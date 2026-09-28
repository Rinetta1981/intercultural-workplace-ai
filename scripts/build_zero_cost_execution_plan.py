import argparse
import csv
import hashlib
import json
from pathlib import Path

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue-csv", type=Path, required=True)
    p.add_argument("--queue-manifest", type=Path, required=True)
    p.add_argument("--system-set", type=Path, required=True)
    p.add_argument("--exec-prefix", required=True)
    p.add_argument("--output-csv", type=Path, required=True)
    p.add_argument("--output-manifest", type=Path, required=True)
    args = p.parse_args()

    if args.output_csv.exists() or args.output_manifest.exists():
        raise SystemExit("Refusing to overwrite an existing v0.2 execution artifact.")

    with args.queue_csv.open(newline="", encoding="utf-8") as f:
        queue = list(csv.DictReader(f))
    qmanifest = json.loads(args.queue_manifest.read_text(encoding="utf-8"))
    systems = json.loads(args.system_set.read_text(encoding="utf-8"))["systems"]

    if len(queue) != 120:
        raise SystemExit(f"Expected 120 queue rows, found {len(queue)}.")
    if len(systems) != 2:
        raise SystemExit(f"Expected 2 systems, found {len(systems)}.")

    rows = []
    execution_number = 1

    # Preserve the identical deterministic queue order within each system.
    for system in systems:
        for within_system_order, q in enumerate(queue, 1):
            rows.append({
                "execution_id": f"{args.exec_prefix}_{execution_number:04d}",
                "system_id": system["system_id"],
                "vendor": system["vendor"],
                "product": system["product"],
                "model": system["model"],
                "access_mode": system["access_mode"],
                "collection_mode": system["collection_mode"],
                "within_system_order": within_system_order,
                "queue_row_id": q["queue_row_id"],
                "family_id": q["family_id"],
                "condition": q["condition"],
                "replicate": q["replicate"],
                "rendered_prompt_sha256": q["rendered_prompt_sha256"],
            })
            execution_number += 1

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    if len(rows) != 240:
        raise SystemExit(f"Expected 240 execution rows, found {len(rows)}.")

    manifest = {
        "execution_design_version": "0.2",
        "row_count": len(rows),
        "observations_per_system": 120,
        "queue_csv_sha256": qmanifest["queue_csv_sha256"],
        "system_set_sha256": sha256_file(args.system_set),
        "execution_plan_csv_sha256": sha256_file(args.output_csv),
        "execution_plan_csv": str(args.output_csv),
        "cost_constraint": "EUR 0 additional project spend",
    }
    args.output_manifest.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Execution rows: {len(rows)}")
    print(f"Queue SHA-256: {manifest['queue_csv_sha256']}")
    print(f"System-set SHA-256: {manifest['system_set_sha256']}")
    print(f"Execution-plan SHA-256: {manifest['execution_plan_csv_sha256']}")
    print(f"Plan: {args.output_csv}")
    print(f"Manifest: {args.output_manifest}")

if __name__ == "__main__":
    main()
