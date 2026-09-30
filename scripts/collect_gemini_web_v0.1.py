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
COLLECTOR_VERSION = "0.1"
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


def beep():
    try:
        subprocess.run(
            ["osascript", "-e", "beep 1"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def open_gemini():
    try:
        subprocess.run(["open", GEMINI_URL], check=False)
    except Exception:
        pass


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
    prompt = p["prompt"].read_text(encoding="utf-8")

    # Verify all 120 frozen prompt fingerprints before collection.
    for row in plan:
        q = qmap[row["queue_row_id"]]
        scenario = load_json(p["frozen"] / q["scenario_file"])
        rendered = render(prompt, scenario, q["condition"])
        actual = sha256_bytes(rendered.encode())
        if actual != row["rendered_prompt_sha256"]:
            raise SystemExit(
                "STOP: frozen prompt fingerprint mismatch for "
                f"{row['execution_id']}"
            )

    return p, plan, qmap, Draft202012Validator(schema), prompt


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


def next_row(plan, completed):
    for row in plan:
        execution_id = derive_execution_id(row["execution_id"])
        if execution_id not in completed:
            return row
    return None


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

    print("\nProtocol for every observation:")
    print("  - fresh Temporary Chat")
    print("  - same selected Gemini model")
    print("  - standard text chat only")
    print("  - no Gems, Deep Research, connected apps, or other tools")
    print("  - paste the frozen prompt unchanged")
    print("  - copy the full model response")
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
    """
    Deterministic structural normalization only.
    No substantive score or recommendation value is changed.
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


def prepare_next(root: Path):
    p, plan, qmap, _, template = verify(root)
    p["runs"].mkdir(parents=True, exist_ok=True)

    completed = completed_ids(p["runs"] / "results.jsonl")
    row = next_row(plan, completed)
    if not row:
        return None

    q = qmap[row["queue_row_id"]]
    scenario = load_json(p["frozen"] / q["scenario_file"])
    prompt = render(template, scenario, q["condition"])

    # Fingerprint already globally verified; verify again locally here.
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
    pending_file(p["runs"]).write_text(
        json.dumps(meta, indent=2) + "\n",
        encoding="utf-8",
    )
    pbcopy(prompt)
    return p, meta, prompt, len(completed)


def save_clipboard_response(root: Path, raw: str, auto=False):
    p, _, _, validator, _ = verify(root)
    cfg = ensure_session_config(p["runs"])
    pf = pending_file(p["runs"])

    if not pf.exists():
        raise RuntimeError("No pending observation.")

    meta = load_json(pf)

    if not raw.strip():
        raise ValueError("Clipboard is empty.")

    parsed = parse_json(raw)
    schema = load_json(p["schema"])
    parsed, normalized = normalize_to_frozen_schema(parsed, schema)

    errors = sorted(
        validator.iter_errors(parsed),
        key=lambda e: list(e.absolute_path),
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

    if normalized:
        print("  Structural format normalized to frozen schema.")
    print(f"SAVED: {rid}")
    print(f"Progress: {n}/120")
    if auto:
        beep()
    return n


def cmd_next(root: Path):
    p = paths(root)
    ensure_session_config(p["runs"])
    prepared = prepare_next(root)
    if prepared is None:
        print("DONE: all 120 observations are saved.")
        return

    _, meta, _, completed = prepared
    print(f"READY: {meta['execution_id']}")
    print(f"Progress: {completed}/120")
    print("Prompt copied to clipboard.")
    print(
        "Now: fresh Gemini Temporary Chat -> paste/send -> "
        "copy the FULL response."
    )


def cmd_save(root: Path):
    p = paths(root)
    ensure_session_config(p["runs"])
    raw = pbpaste()
    try:
        save_clipboard_response(root, raw)
    except Exception as exc:
        raise SystemExit(f"Not saved: {exc}")


def cmd_status(root: Path):
    p, _, _, _, _ = verify(root)
    completed = len(completed_ids(p["runs"] / "results.jsonl"))
    print(f"Completed: {completed}/120")
    print(f"Pending: {120 - completed}")
    if config_file(p["runs"]).exists():
        cfg = load_json(config_file(p["runs"]))
        print(f"Model label: {cfg.get('model_label', '<unknown>')}")


def cmd_session(root: Path, no_open=False):
    p = paths(root)
    cfg = ensure_session_config(p["runs"])

    print("\nAUTOMATED GEMINI WEB COLLECTION SESSION")
    print("--------------------------------------")
    print(f"Model: {cfg['model_label']}")
    print("Use a fresh Temporary Chat for EVERY observation.")
    print("The collector will:")
    print("  1. copy the next frozen prompt automatically;")
    print("  2. wait for you to copy Gemini's response;")
    print("  3. validate + save it automatically;")
    print("  4. copy the next prompt automatically.")
    print("\nYour repeated actions are only:")
    print("  Temporary Chat -> paste/send -> copy response")
    print("\nPress Ctrl+C at any time to pause safely.\n")

    if not no_open:
        open_gemini()

    try:
        while True:
            prepared = prepare_next(root)
            if prepared is None:
                print("\nDONE: all 120 observations are saved.")
                beep()
                return

            _, meta, prompt, completed = prepared
            prompt_hash = sha256_bytes(prompt.encode())

            print(
                f"\nREADY {completed + 1}/120: "
                f"{meta['execution_id']}"
            )
            print(
                "Prompt is on clipboard. Open a FRESH Temporary Chat, "
                "paste/send, then copy the full response."
            )
            print("Waiting for valid JSON response on clipboard...")

            last_seen_hash = prompt_hash
            reported_invalid_hashes = set()

            while True:
                time.sleep(0.6)
                raw = pbpaste()
                if not raw.strip():
                    continue

                current_hash = sha256_bytes(raw.encode())
                if current_hash == last_seen_hash:
                    continue

                last_seen_hash = current_hash

                try:
                    # Validate candidate before saving.
                    parsed = parse_json(raw)
                    schema = load_json(p["schema"])
                    parsed, _ = normalize_to_frozen_schema(parsed, schema)
                    validator = Draft202012Validator(schema)
                    errors = list(validator.iter_errors(parsed))
                    if errors:
                        raise ValueError("clipboard JSON does not match schema")
                except Exception:
                    if current_hash not in reported_invalid_hashes:
                        print(
                            "Clipboard changed, but it is not a valid frozen "
                            "response yet. Still waiting..."
                        )
                        reported_invalid_hashes.add(current_hash)
                    continue

                try:
                    save_clipboard_response(root, raw, auto=True)
                except Exception as exc:
                    print(f"Could not save candidate response: {exc}")
                    print("Still waiting for another copied response...")
                    continue

                # The next loop iteration immediately copies the next prompt.
                break

    except KeyboardInterrupt:
        print("\nPAUSED safely. Re-run --session to resume.")


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Semi-automated clipboard collector for Gemini web UI "
            "replication using the frozen v0.2 stimuli/queue."
        )
    )
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

    ap.add_argument(
        "--no-open",
        action="store_true",
        help="Do not automatically open gemini.google.com in --session mode.",
    )

    args = ap.parse_args()
    root = args.project_root.resolve()

    if args.session:
        cmd_session(root, no_open=args.no_open)
    elif args.next:
        cmd_next(root)
    elif args.save:
        cmd_save(root)
    else:
        cmd_status(root)


if __name__ == "__main__":
    main()
