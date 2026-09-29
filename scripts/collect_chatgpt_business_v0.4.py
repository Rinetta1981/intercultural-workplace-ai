#!/usr/bin/env python3
import argparse, csv, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator

SYSTEM_ID = "chatgpt_business_ui"
VERSION = "0.4"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def pbcopy(text: str):
    subprocess.run(["pbcopy"], input=text, text=True, check=True)

def pbpaste() -> str:
    return subprocess.run(["pbpaste"], text=True, capture_output=True, check=True).stdout

def render(template, scenario, condition):
    return (template
            .replace("<<CONTEXT>>", scenario["invariant_facts"]["context"])
            .replace("<<SPEAKER_ROLE>>", scenario["speaker_role"])
            .replace("<<ADDRESSEE_ROLE>>", scenario["addressee_role"])
            .replace("<<MESSAGE>>", scenario["conditions"][condition]["message"]))

def paths(root: Path):
    return {
        "queue": root/"configs/evaluation_queue_v0.1.csv",
        "plan": root/"configs/zero_cost_execution_plan_v0.2.csv",
        "prompt": root/"docs/model_prompt_v0.1.md",
        "schema": root/"schemas/model_output_v0.1.schema.json",
        "frozen": root/"data/frozen/pilot_v0.1",
        "runs": root/"results/runs/chatgpt_business_v0.2",
    }

def verify(root: Path):
    p = paths(root)
    for k,v in p.items():
        if k != "runs" and not v.exists():
            raise SystemExit(f"Missing required file: {v}")
    queue = read_csv(p["queue"])
    plan = [r for r in read_csv(p["plan"]) if r["system_id"] == SYSTEM_ID]
    if len(queue) != 120 or len(plan) != 120:
        raise SystemExit(f"Expected 120 queue + 120 ChatGPT rows; found {len(queue)} + {len(plan)}")
    qmap = {r["queue_row_id"]: r for r in queue}
    schema = load_json(p["schema"])
    Draft202012Validator.check_schema(schema)
    prompt = p["prompt"].read_text(encoding="utf-8")
    return p, plan, qmap, Draft202012Validator(schema), prompt

def completed_ids(results_path: Path):
    out=set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            try:
                r=json.loads(line)
                if r.get("status")=="success": out.add(r["execution_id"])
            except Exception:
                pass
    return out

def next_row(plan, completed):
    for r in plan:
        if r["execution_id"] not in completed:
            return r
    return None

def pending_file(run_dir: Path):
    return run_dir/"pending.json"

def cmd_next(root: Path):
    p, plan, qmap, _, template = verify(root)
    p["runs"].mkdir(parents=True, exist_ok=True)
    completed=completed_ids(p["runs"]/"results.jsonl")
    row=next_row(plan, completed)
    if not row:
        print("DONE: all 120 observations are saved.")
        return
    q=qmap[row["queue_row_id"]]
    scenario=load_json(p["frozen"]/q["scenario_file"])
    prompt=render(template, scenario, q["condition"])
    if sha256_bytes(prompt.encode()) != row["rendered_prompt_sha256"]:
        raise SystemExit("STOP: prompt fingerprint mismatch.")
    pbcopy(prompt)
    pending_file(p["runs"]).write_text(json.dumps({
        "execution_id": row["execution_id"],
        "queue_row_id": row["queue_row_id"],
        "family_id": row["family_id"],
        "condition": row["condition"],
        "replicate": row["replicate"],
        "rendered_prompt_sha256": row["rendered_prompt_sha256"],
    }, indent=2), encoding="utf-8")
    print(f"READY: {row['execution_id']}")
    print(f"Progress: {len(completed)}/120")
    print("Prompt copied to clipboard.")
    print("Now: new Temporary Chat -> GPT-5.6 Sol -> Medium -> paste/send -> copy full response.")

def parse_json(text: str):
    s=text.strip()
    if s.startswith("```") and s.endswith("```"):
        lines=s.splitlines()[1:]
        if lines and lines[-1].strip()=="```": lines=lines[:-1]
        s="\\n".join(lines).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        a,b=s.find("{"),s.rfind("}")
        if a>=0 and b>a:
            return json.loads(s[a:b+1])
        raise

def normalize_to_frozen_schema(parsed, schema):
    """
    Deterministic structural normalization only:
    - if the frozen schema expects a top-level 'scores' object but the model
      returned those score fields flat at the root, move them under 'scores';
    - if the frozen schema requires schema_version and supplies an unambiguous
      const/single-enum/default, add that schema metadata value.
    No substantive score or categorical value is changed.
    """
    if not isinstance(parsed, dict):
        return parsed, False

    out = dict(parsed)
    changed = False
    props = schema.get("properties", {})

    scores_schema = props.get("scores")
    if isinstance(scores_schema, dict) and "scores" not in out:
        score_props = scores_schema.get("properties", {})
        if isinstance(score_props, dict):
            names = list(score_props.keys())
            present = [name for name in names if name in out]
            if present:
                out["scores"] = {name: out.pop(name) for name in present}
                changed = True

    if "schema_version" in props:
        sv = props.get("schema_version", {})
        value = None
        if isinstance(sv, dict):
            if "const" in sv:
                value = sv["const"]
            elif isinstance(sv.get("enum"), list) and len(sv["enum"]) == 1:
                value = sv["enum"][0]
            elif "default" in sv:
                value = sv["default"]
        if value is not None:
            out["schema_version"] = value
            changed = True

    return out, changed

def cmd_save(root: Path):
    p, plan, qmap, validator, _ = verify(root)
    pf=pending_file(p["runs"])
    if not pf.exists():
        raise SystemExit("No pending observation. Run --next first.")
    meta=load_json(pf)
    raw=pbpaste()
    if not raw.strip():
        raise SystemExit("Clipboard is empty. Copy the FULL ChatGPT response first.")
    try:
        parsed=parse_json(raw)
    except Exception as e:
        raise SystemExit(f"Not saved: clipboard does not contain valid JSON ({e})")

    schema = load_json(p["schema"])
    parsed, normalized = normalize_to_frozen_schema(parsed, schema)
    if normalized:
        print("Format normalized automatically to the frozen schema.")

    errors=sorted(validator.iter_errors(parsed), key=lambda e:list(e.absolute_path))
    if errors:
        print("Not saved: schema validation failed.")
        for e in errors[:8]:
            loc=".".join(map(str,e.absolute_path)) or "<root>"
            print(f"  {loc}: {e.message}")
        return
    ans=input("Confirm: Temporary Chat + unpersonalized + GPT-5.6 Sol + Medium + no tools? [y/N]: ").strip().lower()
    if ans not in {"y","yes"}:
        print("Not saved.")
        return
    rid=meta["execution_id"]
    raw_dir=p["runs"]/"raw"; parsed_dir=p["runs"]/"parsed"
    raw_dir.mkdir(parents=True, exist_ok=True); parsed_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir/f"{rid}.txt").write_text(raw, encoding="utf-8")
    (parsed_dir/f"{rid}.json").write_text(json.dumps(parsed,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    rec={
        "status":"success","execution_id":rid,"system_id":SYSTEM_ID,
        "model":"GPT-5.6 Sol","reasoning":"Medium",
        "queue_row_id":meta["queue_row_id"],"family_id":meta["family_id"],
        "condition":meta["condition"],"replicate":meta["replicate"],
        "rendered_prompt_sha256":meta["rendered_prompt_sha256"],
        "response_sha256":sha256_bytes(raw.encode()),
        "parsed_response":parsed,
        "collected_utc":datetime.now(timezone.utc).isoformat(),
        "temporary_chat":True,"unpersonalized":True,"tools_used":False,
        "visible_fallback":False,"collector_version":VERSION
    }
    with (p["runs"]/"results.jsonl").open("a",encoding="utf-8") as f:
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    pf.unlink(missing_ok=True)
    n=len(completed_ids(p["runs"]/"results.jsonl"))
    print(f"SAVED: {rid}")
    print(f"Progress: {n}/120")

def cmd_status(root: Path):
    p, plan, *_ = verify(root)
    n=len(completed_ids(p["runs"]/"results.jsonl"))
    print(f"Completed: {n}/120")
    print(f"Pending: {120-n}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project-root",type=Path,default=Path(__file__).resolve().parents[1])
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--next",action="store_true")
    g.add_argument("--save",action="store_true")
    g.add_argument("--status",action="store_true")
    args=ap.parse_args()
    root=args.project_root.resolve()
    if args.next: cmd_next(root)
    elif args.save: cmd_save(root)
    else: cmd_status(root)

if __name__=="__main__":
    main()
