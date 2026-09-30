#!/usr/bin/env python3
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

PROJECTS = {
    "IWA": Path("intercultural-workplace-ai"),
    "GTCL": Path("global-team-conflict-lab"),
}

def find_key(obj, target):
    if isinstance(obj, dict):
        if target in obj:
            return obj[target]
        for value in obj.values():
            found = find_key(value, target)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_key(value, target)
            if found is not None:
                return found
    return None

for project, root in PROJECTS.items():
    frozen_dir = root / "data/frozen/pilot_v0.1"
    contrast_file = root / "results/analysis_ready/chatgpt_business_v0.2_family_contrasts.csv"

    if not frozen_dir.exists():
        raise SystemExit(f"{project}: missing {frozen_dir}")
    if not contrast_file.exists():
        raise SystemExit(f"{project}: missing {contrast_file}")

    role_map = {}
    for path in sorted(frozen_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        obj = json.loads(path.read_text(encoding="utf-8"))
        family_id = find_key(obj, "family_id") or path.stem
        role_relation = find_key(obj, "role_relation")
        if role_relation is None:
            raise SystemExit(
                f"{project}: no 'role_relation' field found in {path.name}. "
                f"Top-level keys: {sorted(obj.keys()) if isinstance(obj, dict) else 'not a dict'}"
            )
        role_map[str(family_id)] = str(role_relation)

    if len(role_map) != 10:
        raise SystemExit(f"{project}: expected 10 family role mappings, found {len(role_map)}")

    with contrast_file.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    missing = sorted({r["family_id"] for r in rows if r["family_id"] not in role_map})
    if missing:
        raise SystemExit(f"{project}: missing role relation for families: {missing}")

    grouped = defaultdict(list)
    for r in rows:
        rr = role_map[r["family_id"]]
        grouped[(rr, r["outcome"])].append(r)

    out_dir = root / "results/analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "chatgpt_business_v0.2_role_relation_exploratory.csv"

    fieldnames = [
        "project",
        "role_relation",
        "outcome",
        "n_families",
        "mean_directness_contrast",
        "median_directness_contrast",
        "mean_register_contrast",
        "median_register_contrast",
        "mean_interaction_contrast",
        "median_interaction_contrast",
    ]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for (role_relation, outcome) in sorted(grouped):
            rs = grouped[(role_relation, outcome)]
            d = [float(r["directness_contrast"]) for r in rs]
            reg = [float(r["register_contrast"]) for r in rs]
            inter = [float(r["interaction_contrast"]) for r in rs]

            writer.writerow({
                "project": project,
                "role_relation": role_relation,
                "outcome": outcome,
                "n_families": len(rs),
                "mean_directness_contrast": statistics.fmean(d),
                "median_directness_contrast": statistics.median(d),
                "mean_register_contrast": statistics.fmean(reg),
                "median_register_contrast": statistics.median(reg),
                "mean_interaction_contrast": statistics.fmean(inter),
                "median_interaction_contrast": statistics.median(inter),
            })

    print(project)
    print("Role relations:", dict(sorted(Counter(role_map.values()).items())))
    print("Families mapped:", len(role_map))
    print("Created:", out)
