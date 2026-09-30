#!/usr/bin/env python3
import csv
from collections import defaultdict
from pathlib import Path

PROJECTS = [
    Path("intercultural-workplace-ai"),
    Path("global-team-conflict-lab"),
]

ID_COLS = {
    "system_id",
    "model",
    "reasoning",
    "family_id",
    "condition",
    "directness",
    "register",
    "n_replicates",
}

EXPECTED_CONDITIONS = {"DC", "DI", "MC", "MI"}

for root in PROJECTS:
    src = root / "results/analysis_ready/chatgpt_business_v0.2_cell_means.csv"
    if not src.exists():
        raise SystemExit(f"Missing input file: {src}")

    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if len(rows) != 40:
        raise SystemExit(f"{root.name}: expected 40 cell rows, found {len(rows)}")

    outcome_cols = [c for c in fieldnames if c not in ID_COLS]

    by_family = defaultdict(dict)
    for row in rows:
        fam = row["family_id"]
        cond = row["condition"]
        if cond in by_family[fam]:
            raise SystemExit(f"{root.name}: duplicate condition {cond} for {fam}")
        by_family[fam][cond] = row

    if len(by_family) != 10:
        raise SystemExit(f"{root.name}: expected 10 families, found {len(by_family)}")

    for fam, conds in by_family.items():
        if set(conds) != EXPECTED_CONDITIONS:
            raise SystemExit(
                f"{root.name}: {fam} has conditions {sorted(conds)}, "
                f"expected {sorted(EXPECTED_CONDITIONS)}"
            )

    out = root / "results/analysis_ready/chatgpt_business_v0.2_family_contrasts.csv"
    out_fields = [
        "system_id",
        "model",
        "reasoning",
        "family_id",
        "outcome",
        "directness_contrast",
        "register_contrast",
        "interaction_contrast",
    ]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()

        for fam in sorted(by_family):
            conds = by_family[fam]
            meta = conds["DC"]

            for outcome in outcome_cols:
                dc = float(conds["DC"][outcome])
                di = float(conds["DI"][outcome])
                mc = float(conds["MC"][outcome])
                mi = float(conds["MI"][outcome])

                d = ((dc + di) / 2.0) - ((mc + mi) / 2.0)
                r = ((di + mi) / 2.0) - ((dc + mc) / 2.0)
                i = (di - dc) - (mi - mc)

                writer.writerow({
                    "system_id": meta["system_id"],
                    "model": meta["model"],
                    "reasoning": meta["reasoning"],
                    "family_id": fam,
                    "outcome": outcome,
                    "directness_contrast": d,
                    "register_contrast": r,
                    "interaction_contrast": i,
                })

    expected_rows = len(by_family) * len(outcome_cols)
    with out.open(newline="", encoding="utf-8") as f:
        actual_rows = sum(1 for _ in csv.DictReader(f))

    if actual_rows != expected_rows:
        raise SystemExit(
            f"{root.name}: expected {expected_rows} contrast rows, found {actual_rows}"
        )

    print(root.name)
    print("Families:", len(by_family))
    print("Outcomes:", len(outcome_cols))
    print("Contrast rows:", actual_rows)
    print("Created:", out)
