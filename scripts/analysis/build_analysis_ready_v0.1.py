#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

PROJECTS = {
    "IWA": {
        "root": Path("intercultural-workplace-ai"),
        "category": "recommended_managerial_response",
    },
    "GTCL": {
        "root": Path("global-team-conflict-lab"),
        "category": "recommended_strategy",
    },
}

FACTOR_MAP = {
    "DC": ("direct", "conversational"),
    "DI": ("direct", "institutional"),
    "MC": ("mitigated", "conversational"),
    "MI": ("mitigated", "institutional"),
}

for name, cfg in PROJECTS.items():
    root = cfg["root"]
    src = root / "results/frozen/chatgpt_business_v0.2/results.jsonl"
    if not src.exists():
        raise SystemExit(f"{name}: missing {src}")

    rows = [
        json.loads(line)
        for line in src.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if len(rows) != 120:
        raise SystemExit(f"{name}: expected 120 rows, found {len(rows)}")

    execution_ids = [r["execution_id"] for r in rows]
    if len(set(execution_ids)) != 120:
        raise SystemExit(f"{name}: duplicate execution IDs detected")

    cells = Counter((r["family_id"], r["condition"]) for r in rows)
    if len(cells) != 40 or set(cells.values()) != {3}:
        raise SystemExit(
            f"{name}: unexpected cell structure: "
            f"{len(cells)} cells, replicate counts {sorted(set(cells.values()))}"
        )

    conditions = {r["condition"] for r in rows}
    if conditions != set(FACTOR_MAP):
        raise SystemExit(f"{name}: unexpected conditions: {sorted(conditions)}")

    score_names = sorted(rows[0]["parsed_response"]["scores"].keys())
    category = cfg["category"]

    out_dir = root / "results/analysis_ready"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "chatgpt_business_v0.2_long.csv"

    fieldnames = [
        "execution_id",
        "system_id",
        "model",
        "reasoning",
        "family_id",
        "condition",
        "directness",
        "register",
        "replicate",
        *score_names,
        category,
    ]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in rows:
            condition = r["condition"]
            directness, register = FACTOR_MAP[condition]

            output_row = {
                "execution_id": r["execution_id"],
                "system_id": r["system_id"],
                "model": r["model"],
                "reasoning": r["reasoning"],
                "family_id": r["family_id"],
                "condition": condition,
                "directness": directness,
                "register": register,
                "replicate": r["replicate"],
                category: r["parsed_response"][category],
            }
            output_row.update(r["parsed_response"]["scores"])
            writer.writerow(output_row)

    print(f"{name}: created {out}")
    print(f"{name}: rows 120 | cells 40 | replicates per cell 3")
