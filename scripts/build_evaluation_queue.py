import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

CONDITIONS = ("DC", "DI", "MC", "MI")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def render_prompt(template: str, record: dict, condition: str) -> str:
    return (
        template
        .replace("<<CONTEXT>>", record["invariant_facts"]["context"])
        .replace("<<SPEAKER_ROLE>>", record["speaker_role"])
        .replace("<<ADDRESSEE_ROLE>>", record["addressee_role"])
        .replace("<<MESSAGE>>", record["conditions"][condition]["message"])
    )

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frozen-dir", type=Path, required=True)
    p.add_argument("--prompt-template", type=Path, required=True)
    p.add_argument("--prefix", required=True)
    p.add_argument("--queue-prefix", required=True)
    p.add_argument("--output-csv", type=Path, required=True)
    p.add_argument("--output-manifest", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20260928)
    p.add_argument("--replicates", type=int, default=3)
    args = p.parse_args()

    if args.output_csv.exists() or args.output_manifest.exists():
        raise SystemExit("Refusing to overwrite an existing frozen queue artifact.")

    frozen_manifest = json.loads((args.frozen_dir / "manifest.json").read_text(encoding="utf-8"))
    template = args.prompt_template.read_text(encoding="utf-8")
    template_hash = sha256_bytes(template.encode("utf-8"))

    files = sorted(args.frozen_dir.glob(f"{args.prefix}_*.json"))
    if len(files) != 10:
        raise SystemExit(f"Expected 10 frozen scenario files, found {len(files)}.")

    rows = []
    for file in files:
        record = json.loads(file.read_text(encoding="utf-8"))
        for condition in CONDITIONS:
            c = record["conditions"][condition]
            prompt = render_prompt(template, record, condition)
            for replicate in range(1, args.replicates + 1):
                rows.append({
                    "family_id": record["family_id"],
                    "domain": record["domain"],
                    "role_relation": record["role_relation"],
                    "condition": condition,
                    "directness": c["directness"],
                    "register": c["register"],
                    "replicate": replicate,
                    "scenario_file": file.name,
                    "message_sha256": sha256_bytes(c["message"].encode("utf-8")),
                    "rendered_prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                })

    rng = random.Random(args.seed)
    rng.shuffle(rows)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "queue_row_id","family_id","domain","role_relation","condition",
        "directness","register","replicate","scenario_file",
        "message_sha256","rendered_prompt_sha256"
    ]
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, row in enumerate(rows, 1):
            w.writerow({"queue_row_id": f"{args.queue_prefix}_{i:04d}", **row})

    if len(rows) != 120:
        raise SystemExit(f"Expected 120 queue rows, found {len(rows)}.")

    queue_hash = sha256_file(args.output_csv)
    manifest = {
        "queue_version": "0.1",
        "seed": args.seed,
        "replicates": args.replicates,
        "family_count": 10,
        "conditions_per_family": 4,
        "row_count": len(rows),
        "frozen_dataset_sha256": frozen_manifest["dataset_sha256"],
        "prompt_template_sha256": template_hash,
        "queue_csv_sha256": queue_hash,
        "queue_csv": str(args.output_csv),
    }
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Queue rows: {len(rows)}")
    print(f"Dataset SHA-256: {manifest['frozen_dataset_sha256']}")
    print(f"Prompt SHA-256: {template_hash}")
    print(f"Queue SHA-256: {queue_hash}")
    print(f"Queue: {args.output_csv}")
    print(f"Manifest: {args.output_manifest}")

if __name__ == "__main__":
    main()
