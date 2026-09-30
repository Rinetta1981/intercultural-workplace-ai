#!/usr/bin/env python3
import csv
from collections import Counter, defaultdict
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

for project, cfg in PROJECTS.items():
    root = cfg["root"]
    category = cfg["category"]
    src = root / "results/analysis_ready/gemini_web_ui_v0.3_long.csv"

    if not src.exists():
        raise SystemExit(f"{project}: missing input file: {src}")

    with src.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 120:
        raise SystemExit(f"{project}: expected 120 rows, found {len(rows)}")

    condition_counts = Counter(r["condition"] for r in rows)
    if set(condition_counts) != {"DC", "DI", "MC", "MI"} or set(condition_counts.values()) != {30}:
        raise SystemExit(f"{project}: unexpected condition counts: {dict(condition_counts)}")

    directness_counts = Counter(r["directness"] for r in rows)
    register_counts = Counter(r["register"] for r in rows)
    if set(directness_counts.values()) != {60}:
        raise SystemExit(f"{project}: unexpected directness counts: {dict(directness_counts)}")
    if set(register_counts.values()) != {60}:
        raise SystemExit(f"{project}: unexpected register counts: {dict(register_counts)}")

    out_dir = root / "results/analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    categories = sorted({r[category] for r in rows})

    condition_out = out_dir / "gemini_web_ui_v0.3_categorical_by_condition.csv"
    with condition_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["project", "condition", "category", "count", "proportion"],
        )
        writer.writeheader()
        for condition in ["DC", "DI", "MC", "MI"]:
            subset = [r for r in rows if r["condition"] == condition]
            counts = Counter(r[category] for r in subset)
            for cat in categories:
                n = counts.get(cat, 0)
                writer.writerow({
                    "project": project,
                    "condition": condition,
                    "category": cat,
                    "count": n,
                    "proportion": n / len(subset),
                })

    directness_out = out_dir / "gemini_web_ui_v0.3_categorical_by_directness.csv"
    with directness_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["project", "directness", "category", "count", "proportion"],
        )
        writer.writeheader()
        for level in ["direct", "mitigated"]:
            subset = [r for r in rows if r["directness"] == level]
            counts = Counter(r[category] for r in subset)
            for cat in categories:
                n = counts.get(cat, 0)
                writer.writerow({
                    "project": project,
                    "directness": level,
                    "category": cat,
                    "count": n,
                    "proportion": n / len(subset),
                })

    register_out = out_dir / "gemini_web_ui_v0.3_categorical_by_register.csv"
    with register_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["project", "register", "category", "count", "proportion"],
        )
        writer.writeheader()
        for level in ["conversational", "institutional"]:
            subset = [r for r in rows if r["register"] == level]
            counts = Counter(r[category] for r in subset)
            for cat in categories:
                n = counts.get(cat, 0)
                writer.writerow({
                    "project": project,
                    "register": level,
                    "category": cat,
                    "count": n,
                    "proportion": n / len(subset),
                })

    family_out = out_dir / "gemini_web_ui_v0.3_categorical_by_family_condition.csv"
    grouped = defaultdict(Counter)
    for r in rows:
        grouped[(r["family_id"], r["condition"])][r[category]] += 1

    with family_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["project", "family_id", "condition", "category", "count", "proportion"],
        )
        writer.writeheader()
        for family_id, condition in sorted(grouped):
            counts = grouped[(family_id, condition)]
            total = sum(counts.values())
            if total != 3:
                raise SystemExit(
                    f"{project}: {family_id}/{condition} has {total} replicates, expected 3"
                )
            for cat in categories:
                n = counts.get(cat, 0)
                writer.writerow({
                    "project": project,
                    "family_id": family_id,
                    "condition": condition,
                    "category": cat,
                    "count": n,
                    "proportion": n / total,
                })

    print(project)
    print("Rows:", len(rows))
    print("Conditions:", dict(sorted(condition_counts.items())))
    print("Directness:", dict(sorted(directness_counts.items())))
    print("Register:", dict(sorted(register_counts.items())))
    print("Categories observed:", categories)
    print("Created:", condition_out)
    print("Created:", directness_out)
    print("Created:", register_out)
    print("Created:", family_out)
