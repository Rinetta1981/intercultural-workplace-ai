#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

MODEL_ID = "gemini-3.8-flash"
SYSTEM_ID = "gemini_api_free"
RUNNER_VERSION = "0.2"
MAX_LIVE_BATCH = 20


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def render_prompt(template: str, record: dict, condition: str) -> str:
    return (
        template
        .replace("<<CONTEXT>>", record["invariant_facts"]["context"])
        .replace("<<SPEAKER_ROLE>>", record["speaker_role"])
        .replace("<<ADDRESSEE_ROLE>>", record["addressee_role"])
        .replace("<<MESSAGE>>", record["conditions"][condition]["message"])
    )


def adapt_schema_for_gemini(node: Any) -> Any:
    """Translate unsupported frozen-schema keywords without changing semantics.

    The original frozen schema remains the authoritative local validator.
    This adapter is only for Gemini's provider-side structured-output request.
    """
    if isinstance(node, list):
        return [adapt_schema_for_gemini(x) for x in node]
    if not isinstance(node, dict):
        return node

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key == "$schema":
            continue
        if key == "const":
            out["enum"] = [value]
            continue
        out[key] = adapt_schema_for_gemini(value)
    return out


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def expected_paths(root: Path) -> dict[str, Path]:
    return {
        "queue": root / "configs/evaluation_queue_v0.1.csv",
        "queue_manifest": root / "configs/evaluation_queue_v0.1.manifest.json",
        "plan": root / "configs/zero_cost_execution_plan_v0.2.csv",
        "plan_manifest": root / "configs/zero_cost_execution_plan_v0.2.manifest.json",
        "system_set": root / "configs/zero_cost_system_set_v0.2.json",
        "prompt": root / "docs/model_prompt_v0.1.md",
        "schema": root / "schemas/model_output_v0.1.schema.json",
        "frozen_dir": root / "data/frozen/pilot_v0.1",
        "frozen_manifest": root / "data/frozen/pilot_v0.1/manifest.json",
    }


def verify_project(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    p = expected_paths(root)
    missing = [str(v) for v in p.values() if not v.exists()]
    if missing:
        raise SystemExit("Missing required frozen files:\n  " + "\n  ".join(missing))

    queue = read_csv(p["queue"])
    plan = read_csv(p["plan"])
    queue_manifest = load_json(p["queue_manifest"])
    plan_manifest = load_json(p["plan_manifest"])
    system_set = load_json(p["system_set"])
    schema = load_json(p["schema"])
    frozen_manifest = load_json(p["frozen_manifest"])
    prompt_template = p["prompt"].read_text(encoding="utf-8")

    if len(queue) != 120:
        raise SystemExit(f"Expected 120 queue rows, found {len(queue)}.")
    gemini_plan = [r for r in plan if r["system_id"] == SYSTEM_ID]
    if len(gemini_plan) != 120:
        raise SystemExit(f"Expected 120 Gemini plan rows, found {len(gemini_plan)}.")

    if sha256_file(p["queue"]) != queue_manifest["queue_csv_sha256"]:
        raise SystemExit("Queue CSV fingerprint mismatch.")
    if sha256_file(p["plan"]) != plan_manifest["execution_plan_csv_sha256"]:
        raise SystemExit("Zero-cost execution-plan fingerprint mismatch.")
    if sha256_file(p["system_set"]) != plan_manifest["system_set_sha256"]:
        raise SystemExit("Zero-cost system-set fingerprint mismatch.")
    if frozen_manifest["dataset_sha256"] != queue_manifest["frozen_dataset_sha256"]:
        raise SystemExit("Frozen dataset fingerprint mismatch between dataset and queue manifest.")
    if sha256_bytes(prompt_template.encode("utf-8")) != queue_manifest["prompt_template_sha256"]:
        raise SystemExit("Prompt template fingerprint mismatch.")

    model_entries = [s for s in system_set["systems"] if s["system_id"] == SYSTEM_ID]
    if len(model_entries) != 1:
        raise SystemExit("Expected exactly one gemini_api_free system entry.")
    model_entry = model_entries[0]
    if model_entry["model"] != MODEL_ID:
        raise SystemExit(f"Frozen Gemini model mismatch: {model_entry['model']} != {MODEL_ID}")
    if model_entry["access_mode"] != "free_tier_api":
        raise SystemExit("Gemini access mode is not frozen as free_tier_api.")

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    gemini_schema = adapt_schema_for_gemini(schema)

    queue_by_id = {r["queue_row_id"]: r for r in queue}
    if len(queue_by_id) != 120:
        raise SystemExit("Duplicate queue_row_id values detected.")

    seen_exec = set()
    for plan_row in gemini_plan:
        exec_id = plan_row["execution_id"]
        if exec_id in seen_exec:
            raise SystemExit(f"Duplicate execution_id: {exec_id}")
        seen_exec.add(exec_id)

        qid = plan_row["queue_row_id"]
        if qid not in queue_by_id:
            raise SystemExit(f"Plan references unknown queue row: {qid}")
        q = queue_by_id[qid]
        if plan_row["family_id"] != q["family_id"]:
            raise SystemExit(f"Family mismatch for {exec_id}")
        if plan_row["condition"] != q["condition"]:
            raise SystemExit(f"Condition mismatch for {exec_id}")
        if plan_row["replicate"] != q["replicate"]:
            raise SystemExit(f"Replicate mismatch for {exec_id}")
        if plan_row["rendered_prompt_sha256"] != q["rendered_prompt_sha256"]:
            raise SystemExit(f"Prompt-hash mismatch for {exec_id}")

        scenario = load_json(p["frozen_dir"] / q["scenario_file"])
        rendered = render_prompt(prompt_template, scenario, q["condition"])
        if sha256_bytes(rendered.encode("utf-8")) != q["rendered_prompt_sha256"]:
            raise SystemExit(f"Rendered prompt does not match frozen hash for {exec_id}")

    meta = {
        "paths": {k: str(v) for k, v in p.items()},
        "queue_sha256": queue_manifest["queue_csv_sha256"],
        "plan_sha256": plan_manifest["execution_plan_csv_sha256"],
        "system_set_sha256": plan_manifest["system_set_sha256"],
        "dataset_sha256": frozen_manifest["dataset_sha256"],
        "prompt_sha256": queue_manifest["prompt_template_sha256"],
        "frozen_schema_sha256": sha256_file(p["schema"]),
        "gemini_request_schema_sha256": sha256_bytes(
            (json.dumps(gemini_schema, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        ),
        "model": MODEL_ID,
        "thinking_level": "low",
        "runner_version": RUNNER_VERSION,
        "validator": validator,
        "gemini_schema": gemini_schema,
        "prompt_template": prompt_template,
        "queue_by_id": queue_by_id,
    }
    return queue, gemini_plan, meta


def load_completed(results_jsonl: Path) -> set[str]:
    completed: set[str] = set()
    if not results_jsonl.exists():
        return completed
    with results_jsonl.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") == "success" and rec.get("execution_id"):
                completed.add(rec["execution_id"])
    return completed


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def is_quota_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    status = getattr(exc, "status_code", None)
    text = str(exc).lower()
    return code == 429 or status == 429 or "resource_exhausted" in text or "429" in text


def import_genai():
    try:
        from google import genai
    except Exception as exc:
        raise SystemExit(
            "google-genai is not installed. Install the pinned runner requirements first.\n"
            f"Import error: {exc}"
        )
    return genai


def interaction_metadata(interaction: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": getattr(interaction, "id", None),
        "status": getattr(interaction, "status", None),
        "model": getattr(interaction, "model", None),
    }
    for attr in ("usage", "usage_metadata"):
        obj = getattr(interaction, attr, None)
        if obj is None:
            continue
        try:
            if hasattr(obj, "model_dump"):
                data[attr] = obj.model_dump(mode="json")
            else:
                data[attr] = str(obj)
        except Exception:
            data[attr] = str(obj)
    return data


def run_smoke_test(meta: dict[str, Any]) -> None:
    genai = import_genai()
    client = genai.Client()
    smoke_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"type": "string", "enum": ["ok"]},
            "value": {"type": "integer", "minimum": 1, "maximum": 1},
        },
        "required": ["status", "value"],
    }
    interaction = client.interactions.create(
        model=MODEL_ID,
        input=(
            "Connectivity and structured-output smoke test. Return the requested JSON object "
            "with status set to ok and value set to 1."
        ),
        generation_config={"thinking_level": "low"},
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": smoke_schema,
        },
    )
    parsed = json.loads(interaction.output_text)
    if parsed != {"status": "ok", "value": 1}:
        raise SystemExit(f"Smoke-test response failed validation: {parsed}")
    print("SMOKE TEST: PASS")
    print(f"Model: {getattr(interaction, 'model', MODEL_ID)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Zero-cost Gemini Free-Tier runner for frozen v0.2 evaluation plans."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of scripts/.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate everything; make zero API calls.")
    mode.add_argument("--smoke-test", action="store_true", help="Make one synthetic connectivity test call.")
    mode.add_argument("--run", action="store_true", help="Run substantive frozen Gemini observations.")
    parser.add_argument("--confirm-free-tier", action="store_true")
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--sleep-seconds", type=float, default=6.0)
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()

    root = args.project_root.resolve()
    _, gemini_plan, meta = verify_project(root)

    print("GEMINI FREE-TIER RUNNER PREFLIGHT: PASS")
    print(f"Project root: {root}")
    print(f"Model: {MODEL_ID}")
    print("Thinking level: low")
    print(f"Frozen Gemini executions: {len(gemini_plan)}")
    print(f"Dataset SHA-256: {meta['dataset_sha256']}")
    print(f"Queue SHA-256: {meta['queue_sha256']}")
    print(f"Execution-plan SHA-256: {meta['plan_sha256']}")
    print(f"System-set SHA-256: {meta['system_set_sha256']}")
    print(f"Prompt SHA-256: {meta['prompt_sha256']}")
    print(f"Frozen schema SHA-256: {meta['frozen_schema_sha256']}")
    print(f"Gemini request-schema SHA-256: {meta['gemini_request_schema_sha256']}")

    if not (args.dry_run or args.smoke_test or args.run):
        print("No mode supplied; defaulting to dry-run behavior. No API calls were made.")
        return
    if args.dry_run:
        print("DRY RUN: PASS — zero API calls made.")
        return

    # Hard live-use firewall. The runner cannot independently query AI Studio billing tier.
    if not args.confirm_free_tier or os.environ.get("GEMINI_FREE_TIER_CONFIRMED") != "YES":
        raise SystemExit(
            "LIVE EXECUTION BLOCKED. First verify the project is Free Tier in Google AI Studio, then set:\n"
            "  export GEMINI_FREE_TIER_CONFIRMED=YES\n"
            "and include --confirm-free-tier. The runner will not enable billing or upgrade a project."
        )
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("LIVE EXECUTION BLOCKED: GEMINI_API_KEY is not set.")

    if args.smoke_test:
        run_smoke_test(meta)
        return

    if args.max_items is None:
        raise SystemExit("For --run, --max-items is required. Use 1-20 per invocation.")
    if not 1 <= args.max_items <= MAX_LIVE_BATCH:
        raise SystemExit(f"--max-items must be between 1 and {MAX_LIVE_BATCH}.")
    if args.max_retries < 0 or args.max_retries > 2:
        raise SystemExit("--max-retries must be 0, 1, or 2 under the frozen protocol.")

    genai = import_genai()
    client = genai.Client()
    p = expected_paths(root)
    queue_by_id = meta["queue_by_id"]
    prompt_template = meta["prompt_template"]
    validator: Draft202012Validator = meta["validator"]

    run_dir = root / "results/runs/gemini_free_v0.2"
    raw_dir = run_dir / "raw"
    parsed_dir = run_dir / "parsed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    results_jsonl = run_dir / "results.jsonl"
    completed = load_completed(results_jsonl)

    run_meta_path = run_dir / "run_metadata.json"
    if not run_meta_path.exists():
        public_meta = {k: v for k, v in meta.items() if k not in {"validator", "gemini_schema", "prompt_template", "queue_by_id", "paths"}}
        public_meta.update({
            "created_utc": utc_now(),
            "sdk_expected": "google-genai==2.25.0",
            "cost_constraint": "EUR 0 additional project spend",
            "free_tier_confirmation_required": True,
        })
        run_meta_path.write_text(json.dumps(public_meta, indent=2) + "\n", encoding="utf-8")

    pending = [r for r in gemini_plan if r["execution_id"] not in completed]
    selected = pending[: args.max_items]
    if not selected:
        print("No pending Gemini executions remain.")
        return

    print(f"Pending before this run: {len(pending)}")
    print(f"Planned this invocation: {len(selected)}")

    successes = 0
    for idx, plan_row in enumerate(selected, 1):
        exec_id = plan_row["execution_id"]
        q = queue_by_id[plan_row["queue_row_id"]]
        scenario = load_json(p["frozen_dir"] / q["scenario_file"])
        prompt = render_prompt(prompt_template, scenario, q["condition"])
        prompt_hash = sha256_bytes(prompt.encode("utf-8"))
        if prompt_hash != plan_row["rendered_prompt_sha256"]:
            raise SystemExit(f"Frozen prompt hash changed before execution {exec_id}.")

        print(f"[{idx}/{len(selected)}] {exec_id} {q['family_id']} {q['condition']} rep={q['replicate']}")
        last_error: Exception | None = None
        attempt_records = []

        for retry in range(args.max_retries + 1):
            started = time.monotonic()
            attempt_utc = utc_now()
            try:
                interaction = client.interactions.create(
                    model=MODEL_ID,
                    input=prompt,
                    generation_config={"thinking_level": "low"},
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": meta["gemini_schema"],
                    },
                )
                latency = time.monotonic() - started
                raw_text = interaction.output_text
                parsed = json.loads(raw_text)
                errors = sorted(validator.iter_errors(parsed), key=lambda e: list(e.path))
                if errors:
                    message = "; ".join(err.message for err in errors[:5])
                    raise ValueError(f"Frozen-schema validation failed: {message}")

                raw_record = {
                    "execution_id": exec_id,
                    "attempt": retry + 1,
                    "timestamp_utc": attempt_utc,
                    "latency_seconds": latency,
                    "model_requested": MODEL_ID,
                    "thinking_level_requested": "low",
                    "interaction_metadata": interaction_metadata(interaction),
                    "raw_output_text": raw_text,
                }
                (raw_dir / f"{exec_id}.json").write_text(
                    json.dumps(raw_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                (parsed_dir / f"{exec_id}.json").write_text(
                    json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )

                result = {
                    "status": "success",
                    "execution_id": exec_id,
                    "queue_row_id": plan_row["queue_row_id"],
                    "family_id": q["family_id"],
                    "condition": q["condition"],
                    "replicate": int(q["replicate"]),
                    "system_id": SYSTEM_ID,
                    "provider": "Google",
                    "model": MODEL_ID,
                    "thinking_level": "low",
                    "timestamp_utc": attempt_utc,
                    "latency_seconds": latency,
                    "retry_count": retry,
                    "rendered_prompt_sha256": prompt_hash,
                    "schema_valid": True,
                    "parsed": parsed,
                }
                append_jsonl(results_jsonl, result)
                successes += 1
                last_error = None
                break
            except Exception as exc:
                latency = time.monotonic() - started
                last_error = exc
                attempt_records.append({
                    "attempt": retry + 1,
                    "timestamp_utc": attempt_utc,
                    "latency_seconds": latency,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
                if is_quota_error(exc):
                    fail = {
                        "status": "quota_stop",
                        "execution_id": exec_id,
                        "queue_row_id": plan_row["queue_row_id"],
                        "family_id": q["family_id"],
                        "condition": q["condition"],
                        "replicate": int(q["replicate"]),
                        "system_id": SYSTEM_ID,
                        "provider": "Google",
                        "model": MODEL_ID,
                        "timestamp_utc": attempt_utc,
                        "attempts": attempt_records,
                    }
                    append_jsonl(results_jsonl, fail)
                    print("FREE-TIER QUOTA/RATE LIMIT HIT. Stopping without retrying or upgrading.")
                    return
                if retry < args.max_retries:
                    time.sleep(min(2 ** (retry + 1), 5))

        if last_error is not None:
            fail = {
                "status": "technical_failure",
                "execution_id": exec_id,
                "queue_row_id": plan_row["queue_row_id"],
                "family_id": q["family_id"],
                "condition": q["condition"],
                "replicate": int(q["replicate"]),
                "system_id": SYSTEM_ID,
                "provider": "Google",
                "model": MODEL_ID,
                "timestamp_utc": utc_now(),
                "attempts": attempt_records,
            }
            append_jsonl(results_jsonl, fail)
            print(f"Technical failure recorded for {exec_id}; no score imputed.")

        if idx < len(selected):
            time.sleep(max(0.0, args.sleep_seconds))

    print(f"Successful observations this invocation: {successes}/{len(selected)}")
    print(f"Results: {results_jsonl}")


if __name__ == "__main__":
    main()
