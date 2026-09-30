#!/usr/bin/env python3
import csv
from collections import defaultdict
from pathlib import Path

PROJECTS = [
    Path("intercultural-workplace-ai"),
    Path("global-team-conflict-lab"),
]

ID_COLS = [
    "system_id",
    "model",
    "reasoning",
    "family_id",
    "condition",
    "directness",
    "register",
]

EXCLUDE = {
    "execution_id",
    "replicate",
    "recommended_managerial_response",
    "recommended_strategy",
    *ID_COLS,
}

for root in PROJECTS:
    src = root / "results/analysis_ready/chatgpt_business_v0.2_long.csv"
    if not src.exists():
        raise SystemExit(f"Missing input file: {src}")

    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if len(rows) != 120:
        raise SystemExit(f"{root.name}: expected 120 rows, found {len(rows)}")

    score_cols = [c for c in fieldnames if c not in EXCLUDE]

    grouped = defaultdict(list)
    for row in rows:
        key = tuple(row[c] for c in ID_COLS)
        grouped[key].append(row)

    if len(grouped) != 40:
        raise SystemExit(f"{root.name}: expected 40 cells, found {len(grouped)}")

    replicate_counts = sorted({len(v) for v in grouped.values()})
    if replicate_counts != [3]:
        raise SystemExit(
            f"{root.name}: expected exactly 3 replicates per cell, found {replicate_counts}"
        )

    out = root / "results/analysis_ready/chatgpt_business_v0.2_cell_means.csv"
    out_fields = ID_COLS + score_cols + ["n_replicates"]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()

        for key in sorted(grouped):
            cell_rows = grouped[key]
            out_row = dict(zip(ID_COLS, key))

            for col in score_cols:
                values = [float(r[col]) for r in cell_rows]
                out_row[col] = sum(values) / len(values)

            out_row["n_replicates"] = len(cell_rows)
            writer.writerow(out_row)

    print(root.name)
    print("Cells:", len(grouped))
    print("Replicates per cell:", replicate_counts)
    print("Created:", out)
