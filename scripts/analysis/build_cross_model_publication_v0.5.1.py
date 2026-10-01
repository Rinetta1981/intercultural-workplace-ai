#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path.home() / "Documents" / "GitHub" / "intercultural-org-ai"
PROJECTS = {
    "IWA": ROOT / "intercultural-workplace-ai",
    "GTCL": ROOT / "global-team-conflict-lab",
}
TOL = 1e-12


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    return float(x)


def sign(x):
    if abs(x) <= TOL:
        return 0
    return 1 if x > 0 else -1


def direction_label(a, b):
    sa, sb = sign(a), sign(b)
    if sa == sb:
        if sa == 0:
            return "both_zero"
        return "same_nonzero_direction"
    if sa != 0 and sb != 0:
        return "reversal"
    return "zero_boundary"


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def fmt(x):
    return f"{float(x):+.3f}"


def pct(n, d):
    return 100.0 * n / d if d else 0.0


for project, root in PROJECTS.items():
    analysis = root / "results" / "analysis"
    ready = root / "results" / "analysis_ready"

    confirm = read_csv(analysis / "gemini_vs_chatgpt_confirmatory_v0.1.csv")
    secondary = read_csv(analysis / "gemini_vs_chatgpt_secondary_v0.1.csv")

    for rows, kind in [(confirm, "confirmatory"), (secondary, "secondary")]:
        out = []
        for r in rows:
            c = num(r["chatgpt_mean"])
            g = num(r["gemini_mean"])
            if kind == "confirmatory":
                c_sig = r["chatgpt_holm_significant"]
                g_sig = r["gemini_holm_significant"]
            else:
                c_sig = r["chatgpt_bh_fdr_significant"]
                g_sig = r["gemini_bh_fdr_significant"]
            out.append({
                "project": project,
                "analysis": kind,
                "outcome": r["outcome"],
                "contrast": r["contrast"],
                "chatgpt_mean": c,
                "gemini_mean": g,
                "gemini_minus_chatgpt": g - c,
                "direction_class": direction_label(c, g),
                "chatgpt_significant": c_sig,
                "gemini_significant": g_sig,
                "chatgpt_ci_low_95": r["chatgpt_ci_low_95"],
                "chatgpt_ci_high_95": r["chatgpt_ci_high_95"],
                "gemini_ci_low_95": r["gemini_ci_low_95"],
                "gemini_ci_high_95": r["gemini_ci_high_95"],
                "chatgpt_adjusted_p": r["chatgpt_holm_p"] if kind == "confirmatory" else r["chatgpt_bh_fdr_p"],
                "gemini_adjusted_p": r["gemini_holm_p"] if kind == "confirmatory" else r["gemini_bh_fdr_p"],
            })
        write_csv(analysis / f"gemini_vs_chatgpt_direction_audit_{kind}_v0.5.csv", out)

    # Categorical distributions: compact directness/register comparison.
    cat_rows = []
    for dimension in ["directness", "register"]:
        chat = read_csv(analysis / f"chatgpt_business_v0.2_categorical_by_{dimension}.csv")
        gem = read_csv(analysis / f"gemini_web_ui_v0.3_categorical_by_{dimension}.csv")
        gm = {(r[dimension], r["category"]): r for r in gem}
        for r in chat:
            g = gm[(r[dimension], r["category"])]
            cat_rows.append({
                "project": project,
                "dimension": dimension,
                "level": r[dimension],
                "category": r["category"],
                "chatgpt_count": r["count"],
                "gemini_count": g["count"],
                "chatgpt_proportion": r["proportion"],
                "gemini_proportion": g["proportion"],
                "gemini_minus_chatgpt": num(g["proportion"]) - num(r["proportion"]),
            })
    write_csv(analysis / "gemini_vs_chatgpt_categorical_publication_v0.5.csv", cat_rows)

    # Ordinal status.
    chat_ord = read_csv(analysis / "chatgpt_business_v0.2_ordinal_sensitivity_status.csv")
    gem_ord = read_csv(analysis / "gemini_web_ui_v0.3_ordinal_sensitivity_status.csv")
    gm = {r["outcome"]: r for r in gem_ord}
    ord_rows = []
    for c in chat_ord:
        g = gm[c["outcome"]]
        ord_rows.append({
            "project": project,
            "outcome": c["outcome"],
            "chatgpt_status": c["status"],
            "gemini_status": g["status"],
            "chatgpt_levels": c["n_levels_observed"],
            "gemini_levels": g["n_levels_observed"],
            "chatgpt_warning": " ".join(c.get("warning", "").split()),
            "gemini_warning": " ".join(g.get("warning", "").split()),
        })
    write_csv(analysis / "gemini_vs_chatgpt_ordinal_publication_v0.5.csv", ord_rows)

    # Family-level correlations from already-generated family contrasts.
    chat_f = read_csv(ready / "chatgpt_business_v0.2_family_contrasts.csv")
    gem_f = read_csv(ready / "gemini_web_ui_v0.3_family_contrasts.csv")
    gm = {(r["family_id"], r["outcome"]): r for r in gem_f}
    corr_rows = []
    for outcome in sorted({r["outcome"] for r in chat_f}):
        for contrast in ["directness_contrast", "register_contrast", "interaction_contrast"]:
            pairs = []
            for c in chat_f:
                if c["outcome"] != outcome:
                    continue
                g = gm[(c["family_id"], outcome)]
                pairs.append((num(c[contrast]), num(g[contrast])))
            xs = [x for x, _ in pairs]
            ys = [y for _, y in pairs]
            mx = sum(xs) / len(xs)
            my = sum(ys) / len(ys)
            ssx = sum((x - mx) ** 2 for x in xs)
            ssy = sum((y - my) ** 2 for y in ys)
            if ssx <= TOL or ssy <= TOL:
                corr = "NA (constant vector)"
            else:
                corr = f"{sum((x-mx)*(y-my) for x,y in pairs)/(ssx*ssy)**0.5:.3f}"
            corr_rows.append({
                "project": project,
                "outcome": outcome,
                "contrast": contrast.replace("_contrast", ""),
                "n_families": len(pairs),
                "pearson_r": corr,
            })
    write_csv(analysis / "gemini_vs_chatgpt_family_correlation_v0.5.csv", corr_rows)

    # Publication-facing Markdown report.
    c_audit = read_csv(analysis / "gemini_vs_chatgpt_direction_audit_confirmatory_v0.5.csv")
    s_audit = read_csv(analysis / "gemini_vs_chatgpt_direction_audit_secondary_v0.5.csv")
    cats = cat_rows
    ords = ord_rows
    lines = [
        f"# Cross-model Results — {project} (ChatGPT vs Gemini)",
        "",
        "This is a descriptive post-hoc comparison of the prespecified project-level analyses. It does not alter the confirmatory or secondary inferential gates.",
        "",
        "## Direction classification",
        "",
        "Direction is classified with a tolerance of 1e-12: same non-zero direction, both zero, zero-boundary (one estimate is zero), or reversal (opposite non-zero signs). This avoids treating zero-versus-small-nonzero contrasts as substantive sign reversals.",
        "",
    ]
    for title, rows, sig_col in [("Confirmatory", c_audit, "chatgpt_significant"), ("Secondary", s_audit, "chatgpt_significant")]:
        counts = {}
        for r in rows:
            counts[r["direction_class"]] = counts.get(r["direction_class"], 0) + 1
        lines += [f"## {title}", "", f"Direction classes: {counts}", "", "| Outcome | Contrast | ChatGPT | Gemini | Direction | Significance (C/G) |", "|---|---|---:|---:|---|---|"]
        for r in rows:
            sig = f"{r['chatgpt_significant']} / {r['gemini_significant']}"
            lines.append(f"| {r['outcome']} | {r['contrast']} | {fmt(r['chatgpt_mean'])} | {fmt(r['gemini_mean'])} | {r['direction_class']} | {sig} |")
        lines.append("")

    lines += ["## Categorical recommendation distributions", "", "| Dimension | Level | Category | ChatGPT | Gemini | Gemini − ChatGPT |", "|---|---|---|---:|---:|---:|"]
    for r in cats:
        lines.append(f"| {r['dimension']} | {r['level']} | {r['category']} | {num(r['chatgpt_proportion']):.3f} | {num(r['gemini_proportion']):.3f} | {num(r['gemini_minus_chatgpt']):+.3f} |")
    lines.append("")

    lines += ["## Ordinal sensitivity", "", "| Outcome | ChatGPT | Gemini |", "|---|---|---|"]
    for r in ords:
        c = f"{r['chatgpt_status']} ({r['chatgpt_levels']} levels)"
        g = f"{r['gemini_status']} ({r['gemini_levels']} levels)"
        if r["chatgpt_status"] == "fit_ok" and r["chatgpt_warning"]:
            c += "; numerical warning"
        elif r["chatgpt_status"] != "fit_ok":
            c += "; not estimable"
        if r["gemini_status"] == "fit_ok" and r["gemini_warning"]:
            g += "; numerical warning"
        elif r["gemini_status"] != "fit_ok":
            g += "; not estimable"
        lines.append(f"| {r['outcome']} | {c} | {g} |")
    lines.append("")
    lines.append("Numerical warnings on otherwise fitted ordinal models indicate identifiability/convergence concerns; those fits are not treated as clean inferential sensitivity confirmations. Models marked fit_error are not estimable and are not interpreted.")
    lines.append("")

    corr = read_csv(analysis / "gemini_vs_chatgpt_family_correlation_v0.5.csv")
    lines += ["## Family-level cross-model correlations", "", "These are descriptive Pearson correlations across the 10 scenario families and are not additional inferential tests.", "", "| Outcome | Contrast | Pearson r |", "|---|---|---:|"]
    for r in corr:
        lines.append(f"| {r['outcome']} | {r['contrast']} | {r['pearson_r']} |")
    lines.append("")

    # Highlight inferential findings without creating new tests.
    both_sig = [r for r in s_audit if r["chatgpt_significant"] == "True" and r["gemini_significant"] == "True"]
    chat_only = [r for r in s_audit if r["chatgpt_significant"] == "True" and r["gemini_significant"] == "False"]
    gem_only = [r for r in s_audit if r["chatgpt_significant"] == "False" and r["gemini_significant"] == "True"]
    lines += ["## Manuscript-level synthesis", ""]
    if both_sig:
        labels = "; ".join(f"{r['outcome']} × {r['contrast']} (ChatGPT {fmt(r['chatgpt_mean'])}; Gemini {fmt(r['gemini_mean'])})" for r in both_sig)
        lines.append(f"The secondary effect(s) significant under BH-FDR in both systems were: {labels}.")
    else:
        lines.append("No secondary effect was significant under BH-FDR in both systems.")
    lines.append(f"ChatGPT-only BH-FDR-significant secondary effects: {len(chat_only)}; Gemini-only: {len(gem_only)}.")
    lines.append("The cross-model comparison is descriptive and should be interpreted as convergence/divergence of effect estimates and significance status, not as a ranking of models.")
    lines.append("")
    lines.append("Family-level correlations are descriptive summaries across 10 scenario families and should not be treated as new inferential tests.")

    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "cross_model_results_gemini_vs_chatgpt_v0.5.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{project}: created direction audit, categorical/ordinal comparison tables, and docs/cross_model_results_gemini_vs_chatgpt_v0.5.md")

print("DONE: cross-model publication audit v0.5 created for IWA and GTCL; no frozen data modified.")
