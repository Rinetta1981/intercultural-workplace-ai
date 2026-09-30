#!/usr/bin/env python3
import csv
import itertools
import math
import random
import statistics
from pathlib import Path

BOOTSTRAP_SEED = 2026092803
BOOTSTRAP_RESAMPLES = 10_000
ALPHA = 0.05

PROJECTS = {
    "IWA": {
        "root": Path("intercultural-workplace-ai"),
        "secondary_outcomes": [
            "professionalism",
            "cooperativeness",
            "communicative_appropriateness",
        ],
    },
    "GTCL": {
        "root": Path("global-team-conflict-lab"),
        "secondary_outcomes": [
            "conflict_severity",
            "speaker_aggression",
            "speaker_cooperativeness",
            "addressee_responsibility",
        ],
    },
}

CONTRASTS = [
    ("directness", "directness_contrast"),
    ("register", "register_contrast"),
    ("interaction", "interaction_contrast"),
]


def exact_signflip_p(values):
    observed = abs(statistics.fmean(values))
    extreme = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(values)):
        perm_mean = statistics.fmean(v * s for v, s in zip(values, signs))
        if abs(perm_mean) >= observed - 1e-15:
            extreme += 1
        total += 1
    return extreme / total


def percentile(sorted_values, q):
    if not sorted_values:
        raise ValueError("Cannot compute percentile of empty list")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def bootstrap_mean_ci(values, rng, n_resamples=BOOTSTRAP_RESAMPLES):
    n = len(values)
    draws = []
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        draws.append(statistics.fmean(sample))
    draws.sort()
    return percentile(draws, 0.025), percentile(draws, 0.975)


def bh_adjust(pvalues):
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [None] * m

    running_min = 1.0
    for reverse_rank in range(m - 1, -1, -1):
        idx = order[reverse_rank]
        rank = reverse_rank + 1
        raw_adj = pvalues[idx] * m / rank
        running_min = min(running_min, raw_adj)
        adjusted[idx] = min(1.0, running_min)

    return adjusted


for project_name, cfg in PROJECTS.items():
    root = cfg["root"]
    src = root / "results/analysis_ready/gemini_web_ui_v0.3_family_contrasts.csv"
    if not src.exists():
        raise SystemExit(f"{project_name}: missing input file: {src}")

    with src.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    rng = random.Random(BOOTSTRAP_SEED)
    results = []

    for outcome in cfg["secondary_outcomes"]:
        outcome_rows = [r for r in rows if r["outcome"] == outcome]
        if len(outcome_rows) != 10:
            raise SystemExit(
                f"{project_name}: expected 10 family rows for {outcome}, "
                f"found {len(outcome_rows)}"
            )

        family_ids = [r["family_id"] for r in outcome_rows]
        if len(set(family_ids)) != 10:
            raise SystemExit(f"{project_name}: duplicate family IDs for {outcome}")

        outcome_rows = sorted(outcome_rows, key=lambda r: r["family_id"])

        for contrast_name, column in CONTRASTS:
            values = [float(r[column]) for r in outcome_rows]

            mean_value = statistics.fmean(values)
            median_value = statistics.median(values)
            p_exact = exact_signflip_p(values)
            ci_low, ci_high = bootstrap_mean_ci(values, rng)

            results.append({
                "project": project_name,
                "system_id": outcome_rows[0]["system_id"],
                "model": outcome_rows[0]["model"],
                "reasoning": outcome_rows[0]["reasoning"],
                "outcome": outcome,
                "contrast": contrast_name,
                "n_families": len(values),
                "mean_contrast": mean_value,
                "median_contrast": median_value,
                "bootstrap_ci_low_95": ci_low,
                "bootstrap_ci_high_95": ci_high,
                "exact_signflip_p": p_exact,
            })

    expected_tests = len(cfg["secondary_outcomes"]) * len(CONTRASTS)
    if len(results) != expected_tests:
        raise SystemExit(
            f"{project_name}: expected {expected_tests} secondary tests, "
            f"found {len(results)}"
        )

    raw_ps = [r["exact_signflip_p"] for r in results]
    bh_ps = bh_adjust(raw_ps)

    for row, adj in zip(results, bh_ps):
        row["bh_fdr_p"] = adj
        row["reject_bh_0_05"] = adj <= ALPHA
        row["bootstrap_resamples"] = BOOTSTRAP_RESAMPLES
        row["bootstrap_seed"] = BOOTSTRAP_SEED

    out_dir = root / "results/analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "gemini_web_ui_v0.3_secondary.csv"

    fieldnames = [
        "project",
        "system_id",
        "model",
        "reasoning",
        "outcome",
        "contrast",
        "n_families",
        "mean_contrast",
        "median_contrast",
        "bootstrap_ci_low_95",
        "bootstrap_ci_high_95",
        "exact_signflip_p",
        "bh_fdr_p",
        "reject_bh_0_05",
        "bootstrap_resamples",
        "bootstrap_seed",
    ]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(project_name)
    print("Secondary outcomes:", len(cfg["secondary_outcomes"]))
    print("Secondary tests:", len(results))
    print("Families per test: 10")
    print("Exact sign-flip permutations per test: 1024")
    print("Bootstrap resamples per test:", BOOTSTRAP_RESAMPLES)
    print("Created:", out)
