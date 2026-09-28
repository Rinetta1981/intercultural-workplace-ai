import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue-csv", type=Path, required=True)
    p.add_argument("--queue-manifest", type=Path, required=True)
    p.add_argument("--model-set", type=Path, required=True)
    p.add_argument("--exec-prefix", required=True)
    p.add_argument("--output-csv", type=Path, required=True)
    p.add_argument("--output-manifest", type=Path, required=True)
    p.add_argument("--seed", type=int, default=2026092801)
    args = p.parse_args()

    if args.output_csv.exists() or args.output_manifest.exists():
        raise SystemExit("Refusing to overwrite an existing frozen execution-plan artifact.")

    with args.queue_csv.open(newline="", encoding="utf-8") as f:
        queue_rows = list(csv.DictReader(f))
    queue_manifest = json.loads(args.queue_manifest.read_text(encoding="utf-8"))
    model_set = json.loads(args.model_set.read_text(encoding="utf-8"))

    if len(queue_rows) != 120:
        raise SystemExit(f"Expected 120 queue rows, found {len(queue_rows)}.")
    if len(model_set["models"]) != 3:
        raise SystemExit(f"Expected 3 models, found {len(model_set['models'])}.")

    rows = []
    for q in queue_rows:
        for model in model_set["models"]:
            rows.append({
                "provider": model["provider"],
                "model_id": model["model_id"],
                "queue_row_id": q["queue_row_id"],
                "family_id": q["family_id"],
                "condition": q["condition"],
                "replicate": q["replicate"],
                "rendered_prompt_sha256": q["rendered_prompt_sha256"],
            })

    rng = random.Random(args.seed)
    rng.shuffle(rows)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "execution_id","provider","model_id","queue_row_id",
        "family_id","condition","replicate","rendered_prompt_sha256"
    ]
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, row in enumerate(rows, 1):
            w.writerow({"execution_id": f"{args.exec_prefix}_{i:04d}", **row})

    if len(rows) != 360:
        raise SystemExit(f"Expected 360 execution rows, found {len(rows)}.")

    plan_hash = sha256_file(args.output_csv)
    manifest = {
        "execution_plan_version": "0.1",
        "seed": args.seed,
        "row_count": len(rows),
        "queue_csv_sha256": queue_manifest["queue_csv_sha256"],
        "model_set_sha256": sha256_file(args.model_set),
        "execution_plan_csv_sha256": plan_hash,
        "execution_plan_csv": str(args.output_csv),
    }
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Execution rows: {len(rows)}")
    print(f"Queue SHA-256: {manifest['queue_csv_sha256']}")
    print(f"Model-set SHA-256: {manifest['model_set_sha256']}")
    print(f"Execution-plan SHA-256: {plan_hash}")
    print(f"Plan: {args.output_csv}")
    print(f"Manifest: {args.output_manifest}")

if __name__ == "__main__":
    main()
