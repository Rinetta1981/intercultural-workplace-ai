#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

SYSTEM_ID = "gemini_web_ui"
SOURCE_PLAN_SYSTEM_ID = "gemini_api_free"
RUN_VERSION = "v0.3"
COLLECTOR_VERSION = "0.2"
GEMINI_URL = "https://gemini.google.com/app"


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
    return subprocess.run(
        ["pbpaste"], text=True, capture_output=True, check=True
    ).stdout


def open_gemini():
    subprocess.run(["open", GEMINI_URL], check=False)


def render(template, scenario, condition):
    return (
        template
        .replace("<<CONTEXT>>", scenario["invariant_facts"]["context"])
        .replace("<<SPEAKER_ROLE>>", scenario["speaker_role"])
        .replace("<<ADDRESSEE_ROLE>>", scenario["addressee_role"])
        .replace("<<MESSAGE>>", scenario["conditions"][condition]["message"])
    )


def paths(root: Path):
    return {
        "queue": root / "configs/evaluation_queue_v0.1.csv",
        "plan": root / "configs/zero_cost_execution_plan_v0.2.csv",
        "prompt": root / "docs/model_prompt_v0.1.md",
        "schema": root / "schemas/model_output_v0.1.schema.json",
        "frozen": root / "data/frozen/pilot_v0.1",
        "runs": root / f"results/runs/gemini_web_ui_{RUN_VERSION}",
    }


def derive_execution_id(source_execution_id: str) -> str:
    if SOURCE_PLAN_SYSTEM_ID in source_execution_id:
        return source_execution_id.replace(SOURCE_PLAN_SYSTEM_ID, SYSTEM_ID)
    return f"{SYSTEM_ID}__{source_execution_id}"


def verify(root: Path):
    p = paths(root)
    for key, value in p.items():
        if key != "runs" and not value.exists():
            raise SystemExit(f"Missing required file: {value}")

    queue = read_csv(p["queue"])
    plan = [
        row for row in read_csv(p["plan"])
        if row["system_id"] == SOURCE_PLAN_SYSTEM_ID
    ]
    if len(queue) != 120 or len(plan) != 120:
        raise SystemExit(
            "Expected 120 queue rows + 120 frozen Gemini-plan rows; "
            f"found {len(queue)} + {len(plan)}"
        )

    qmap = {row["queue_row_id"]: row for row in queue}
    schema = load_json(p["schema"])
    Draft202012Validator.check_schema(schema)
    template = p["prompt"].read_text(encoding="utf-8")

    # Verify the complete frozen prompt set before collection.
    for row in plan:
        q = qmap[row["queue_row_id"]]
        scenario = load_json(p["frozen"] / q["scenario_file"])
        rendered = render(template, scenario, q["condition"])
        if sha256_bytes(rendered.encode()) != row["rendered_prompt_sha256"]:
            raise SystemExit(
                "STOP: frozen prompt fingerprint mismatch for "
                f"{row['execution_id']}"
            )

    return p, plan, qmap, Draft202012Validator(schema), template


def completed_ids(results_path: Path):
    out = set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("status") == "success":
                    out.add(rec["execution_id"])
            except Exception:
                pass
    return out


def pending_file(run_dir: Path):
    return run_dir / "pending.json"


def config_file(run_dir: Path):
    return run_dir / "session_config.json"


def ensure_session_config(run_dir: Path):
    run_dir.mkdir(parents=True, exist_ok=True)
    cf = config_file(run_dir)
    if cf.exists():
        return load_json(cf)

    print("\nONE-TIME GEMINI WEB SETUP")
    print("-------------------------")
    model_label = input(
        "Enter the exact Gemini model label shown in the web UI: "
    ).strip()
    if not model_label:
        raise SystemExit("Stopped: model label cannot be empty.")

    print("\nFor every observation:")
    print("  - fresh Temporary Chat")
    print("  - same selected Gemini model")
    print("  - standard text chat only")
    print("  - no Gems, Deep Research, connected apps, or tools")
    print("  - paste the frozen prompt unchanged")
    print("  - copy the FULL Gemini response")
    ans = input("Confirm this collection protocol? [y/N]: ").strip().lower()
    if ans not in {"y", "yes"}:
        raise SystemExit("Stopped: protocol not confirmed.")

    cfg = {
        "system_id": SYSTEM_ID,
        "source_frozen_plan_system_id": SOURCE_PLAN_SYSTEM_ID,
        "run_version": RUN_VERSION,
        "collector_version": COLLECTOR_VERSION,
        "model_label": model_label,
        "interface": "Gemini web app",
        "temporary_chat_required": True,
        "personalization_expected": False,
        "tools_expected": False,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    cf.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"Saved session config: {cf}")
    return cfg


def parse_json(text: str):
    s = text.strip()
    if s.startswith("```") and s.endswith("```"):
        lines = s.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        a, b = s.find("{"), s.rfind("}")
        if a >= 0 and b > a:
            return json.loads(s[a:b + 1])
        raise


def normalize_to_frozen_schema(parsed, schema):
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
        if value is not None and out.get("schema_version") != value:
            out["schema_version"] = value
            changed = True

    if (
        "recommended_strategy" in props
        and "recommended_strategy" not in out
        and "recommended_conflict_management_strategy" in out
    ):
        out["recommended_strategy"] = out.pop(
            "recommended_conflict_management_strategy"
        )
        changed = True

    return out, changed


def next_row(plan, completed):
    for row in plan:
        rid = derive_execution_id(row["execution_id"])
        if rid not in completed:
            return row
    return None


def prepare_next(root: Path):
    p, plan, qmap, _, template = verify(root)
    p["runs"].mkdir(parents=True, exist_ok=True)
    completed = completed_ids(p["runs"] / "results.jsonl")

    # If a previous session was interrupted while an item was pending,
    # reuse that exact pending item rather than generating a new one.
    pf = pending_file(p["runs"])
    if pf.exists():
        meta = load_json(pf)
        source_id = meta.get("source_execution_id")
        row = next((r for r in plan if r["execution_id"] == source_id), None)
        if row is None:
            raise SystemExit("STOP: pending item is not present in frozen plan.")
        q = qmap[row["queue_row_id"]]
        scenario = load_json(p["frozen"] / q["scenario_file"])
        prompt = render(template, scenario, q["condition"])
        if sha256_bytes(prompt.encode()) != row["rendered_prompt_sha256"]:
            raise SystemExit("STOP: pending prompt fingerprint mismatch.")
        return p, row, meta, prompt, len(completed)

    row = next_row(plan, completed)
    if row is None:
        return None

    q = qmap[row["queue_row_id"]]
    scenario = load_json(p["frozen"] / q["scenario_file"])
    prompt = render(template, scenario, q["condition"])
    if sha256_bytes(prompt.encode()) != row["rendered_prompt_sha256"]:
        raise SystemExit("STOP: prompt fingerprint mismatch.")

    execution_id = derive_execution_id(row["execution_id"])
    meta = {
        "execution_id": execution_id,
        "source_execution_id": row["execution_id"],
        "queue_row_id": row["queue_row_id"],
        "family_id": row["family_id"],
        "condition": row["condition"],
        "replicate": row["replicate"],
        "rendered_prompt_sha256": row["rendered_prompt_sha256"],
    }
    pf.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return p, row, meta, prompt, len(completed)


def save_response(root: Path, raw: str):
    p, _, _, validator, _ = verify(root)
    pf = pending_file(p["runs"])
    if not pf.exists():
        raise RuntimeError("No pending observation. Start/resume the session first.")

    cfg = ensure_session_config(p["runs"])
    meta = load_json(pf)
    parsed = parse_json(raw)
    schema = load_json(p["schema"])
    parsed, normalized = normalize_to_frozen_schema(parsed, schema)

    errors = sorted(
        validator.iter_errors(parsed), key=lambda e: list(e.absolute_path)
    )
    if errors:
        messages = []
        for err in errors[:8]:
            loc = ".".join(map(str, err.absolute_path)) or "<root>"
            messages.append(f"{loc}: {err.message}")
        raise ValueError("Schema validation failed: " + " | ".join(messages))

    rid = meta["execution_id"]
    raw_dir = p["runs"] / "raw"
    parsed_dir = p["runs"] / "parsed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)

    (raw_dir / f"{rid}.txt").write_text(raw, encoding="utf-8")
    (parsed_dir / f"{rid}.json").write_text(
        json.dumps(parsed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    rec = {
        "status": "success",
        "execution_id": rid,
        "source_execution_id": meta["source_execution_id"],
        "source_frozen_plan_system_id": SOURCE_PLAN_SYSTEM_ID,
        "system_id": SYSTEM_ID,
        "model": cfg["model_label"],
        "reasoning": "web_ui_selected_model",
        "interface": "Gemini web app",
        "queue_row_id": meta["queue_row_id"],
        "family_id": meta["family_id"],
        "condition": meta["condition"],
        "replicate": meta["replicate"],
        "rendered_prompt_sha256": meta["rendered_prompt_sha256"],
        "response_sha256": sha256_bytes(raw.encode()),
        "parsed_response": parsed,
        "collected_utc": datetime.now(timezone.utc).isoformat(),
        "temporary_chat": True,
        "personalization_expected": False,
        "tools_used": False,
        "protocol_amendment": "gemini_web_ui_v0.3",
        "collector_version": COLLECTOR_VERSION,
        "structural_normalization_applied": normalized,
    }

    with (p["runs"] / "results.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    pf.unlink(missing_ok=True)
    n = len(completed_ids(p["runs"] / "results.jsonl"))
    return n, normalized


def cmd_status(root: Path):
    p, _, _, _, _ = verify(root)
    n = len(completed_ids(p["runs"] / "results.jsonl"))
    print(f"Completed: {n}/120")
    print(f"Pending: {120 - n}")
    cf = config_file(p["runs"])
    if cf.exists():
        cfg = load_json(cf)
        print(f"Model label: {cfg.get('model_label', '<unknown>')}")


def cmd_session(root: Path, no_open=False):
    p = paths(root)
    cfg = ensure_session_config(p["runs"])

    print("\nSAFE GEMINI WEB COLLECTION SESSION")
    print("---------------------------------")
    print(f"Model: {cfg['model_label']}")
    print("The collector will NOT monitor the clipboard automatically.")
    print("This prevents Terminal text from being mistaken for a Gemini response.")
    print("\nFor each observation:")
    print("  1. Paste the prompt into a FRESH Gemini Temporary Chat and send it.")
    print("  2. Copy Gemini's COMPLETE JSON response.")
    print("  3. Return to Terminal and press Enter.")
    print("  4. The collector validates and saves it, then prepares the next prompt.")
    print("\nPress Ctrl+C to pause safely.\n")

    if not no_open:
        open_gemini()

    while True:
        prepared = prepare_next(root)
        if prepared is None:
            print("DONE: all 120 observations are saved.")
            return

        _, row, meta, prompt, completed = prepared
        pbcopy(prompt)
        print(f"\nREADY {completed + 1}/120: {meta['execution_id']}")
        print("Prompt copied to clipboard.")
        print("Gemini: FRESH Temporary Chat -> select the same model -> paste/send.")
        print("Then COPY THE COMPLETE JSON RESPONSE and return here.")

        while True:
            input("When the complete Gemini response is copied, press Enter here...")
            raw = pbpaste()
            try:
                n, normalized = save_response(root, raw)
                if normalized:
                    print("Structural format normalized to frozen schema.")
                print(f"SAVED: {meta['execution_id']}")
                print(f"Progress: {n}/120")
                break
            except Exception as exc:
                print(f"NOT SAVED: {exc}")
                print("Do NOT start a new observation.")
                print("Copy the COMPLETE JSON response from the current Gemini chat, then press Enter again.")


def cmd_next(root: Path):
    p = paths(root)
    ensure_session_config(p["runs"])
    prepared = prepare_next(root)
    if prepared is None:
        print("DONE: all 120 observations are saved.")
        return
    _, _, meta, prompt, completed = prepared
    pbcopy(prompt)
    print(f"READY: {meta['execution_id']}")
    print(f"Progress: {completed}/120")
    print("Prompt copied to clipboard.")
    print("Now: fresh Gemini Temporary Chat -> paste/send -> copy FULL response.")
    print("Then run --save.")


def cmd_save(root: Path):
    raw = pbpaste()
    try:
        n, normalized = save_response(root, raw)
        if normalized:
            print("Structural format normalized to frozen schema.")
        print(f"SAVED. Progress: {n}/120")
    except Exception as exc:
        raise SystemExit(f"Not saved: {exc}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--session", action="store_true")
    group.add_argument("--next", action="store_true")
    group.add_argument("--save", action="store_true")
    group.add_argument("--status", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    root = args.project_root.resolve()

    if args.session:
        try:
            cmd_session(root, no_open=args.no_open)
        except KeyboardInterrupt:
            print("\nPAUSED safely. Re-run --session to resume.")
    elif args.next:
        cmd_next(root)
    elif args.save:
        cmd_save(root)
    else:
        cmd_status(root)


if __name__ == "__main__":
    main()
