#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path.home() / 'Documents' / 'GitHub' / 'intercultural-org-ai'
PROJECTS = {
    'IWA': ROOT / 'intercultural-workplace-ai',
    'GTCL': ROOT / 'global-team-conflict-lab',
}


def read_csv(path: Path):
    if not path.exists():
        raise SystemExit(f'Missing file: {path}')
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def f(row, key):
    return float(row[key])


def sign(x, tol=1e-12):
    if x > tol:
        return 1
    if x < -tol:
        return -1
    return 0


def merge_by(rows_a, rows_b, keys):
    a = {tuple(r[k] for k in keys): r for r in rows_a}
    b = {tuple(r[k] for k in keys): r for r in rows_b}
    if len(a) != len(rows_a) or len(b) != len(rows_b):
        raise SystemExit(f'Duplicate keys for {keys}')
    if set(a) != set(b):
        only_a = sorted(set(a) - set(b))
        only_b = sorted(set(b) - set(a))
        raise SystemExit(f'Key mismatch for {keys}: only ChatGPT={only_a}; only Gemini={only_b}')
    return [(key, a[key], b[key]) for key in sorted(a)]


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


summary = []
for project, root in PROJECTS.items():
    analysis = root / 'results' / 'analysis'
    out_dir = root / 'results' / 'analysis'
    out_dir.mkdir(parents=True, exist_ok=True)

    chat_confirm = read_csv(analysis / 'chatgpt_business_v0.2_confirmatory.csv')
    gem_confirm = read_csv(analysis / 'gemini_web_ui_v0.3_confirmatory.csv')
    pairs = merge_by(chat_confirm, gem_confirm, ['project', 'outcome', 'contrast'])

    confirm_out = []
    for _, c, g in pairs:
        ce = f(c, 'mean_contrast')
        ge = f(g, 'mean_contrast')
        confirm_out.append({
            'project': project,
            'outcome': c['outcome'],
            'contrast': c['contrast'],
            'chatgpt_mean': ce,
            'gemini_mean': ge,
            'gemini_minus_chatgpt': ge - ce,
            'chatgpt_ci_low_95': f(c, 'bootstrap_ci_low_95'),
            'chatgpt_ci_high_95': f(c, 'bootstrap_ci_high_95'),
            'gemini_ci_low_95': f(g, 'bootstrap_ci_low_95'),
            'gemini_ci_high_95': f(g, 'bootstrap_ci_high_95'),
            'chatgpt_holm_p': f(c, 'holm_p_9tests'),
            'gemini_holm_p': f(g, 'holm_p_9tests'),
            'chatgpt_holm_significant': c['reject_holm_0_05'],
            'gemini_holm_significant': g['reject_holm_0_05'],
            'same_direction': sign(ce) == sign(ge),
        })

    write_csv(
        out_dir / 'gemini_vs_chatgpt_confirmatory_v0.1.csv',
        confirm_out,
        list(confirm_out[0].keys()) if confirm_out else [],
    )

    chat_sec = read_csv(analysis / 'chatgpt_business_v0.2_secondary.csv')
    gem_sec = read_csv(analysis / 'gemini_web_ui_v0.3_secondary.csv')
    pairs = merge_by(chat_sec, gem_sec, ['project', 'outcome', 'contrast'])

    sec_out = []
    for _, c, g in pairs:
        ce = f(c, 'mean_contrast')
        ge = f(g, 'mean_contrast')
        sec_out.append({
            'project': project,
            'outcome': c['outcome'],
            'contrast': c['contrast'],
            'chatgpt_mean': ce,
            'gemini_mean': ge,
            'gemini_minus_chatgpt': ge - ce,
            'chatgpt_ci_low_95': f(c, 'bootstrap_ci_low_95'),
            'chatgpt_ci_high_95': f(c, 'bootstrap_ci_high_95'),
            'gemini_ci_low_95': f(g, 'bootstrap_ci_low_95'),
            'gemini_ci_high_95': f(g, 'bootstrap_ci_high_95'),
            'chatgpt_bh_fdr_p': f(c, 'bh_fdr_p'),
            'gemini_bh_fdr_p': f(g, 'bh_fdr_p'),
            'chatgpt_bh_fdr_significant': c['reject_bh_0_05'],
            'gemini_bh_fdr_significant': g['reject_bh_0_05'],
            'same_direction': sign(ce) == sign(ge),
        })

    write_csv(
        out_dir / 'gemini_vs_chatgpt_secondary_v0.1.csv',
        sec_out,
        list(sec_out[0].keys()) if sec_out else [],
    )

    # Categorical distributions: condition, directness, register.
    for dimension in ['condition', 'directness', 'register']:
        chat = read_csv(analysis / f'chatgpt_business_v0.2_categorical_by_{dimension}.csv')
        gem = read_csv(analysis / f'gemini_web_ui_v0.3_categorical_by_{dimension}.csv')
        pairs = merge_by(chat, gem, ['project', dimension, 'category'])
        rows = []
        for _, c, g in pairs:
            rows.append({
                'project': project,
                dimension: c[dimension],
                'category': c['category'],
                'chatgpt_count': int(c['count']),
                'gemini_count': int(g['count']),
                'chatgpt_proportion': f(c, 'proportion'),
                'gemini_proportion': f(g, 'proportion'),
                'gemini_minus_chatgpt_proportion': f(g, 'proportion') - f(c, 'proportion'),
            })
        write_csv(
            out_dir / f'gemini_vs_chatgpt_categorical_by_{dimension}_v0.1.csv',
            rows,
            list(rows[0].keys()) if rows else [],
        )

    # Ordinal sensitivity status comparison.
    chat_ord = read_csv(analysis / 'chatgpt_business_v0.2_ordinal_sensitivity_status.csv')
    gem_ord = read_csv(analysis / 'gemini_web_ui_v0.3_ordinal_sensitivity_status.csv')
    pairs = merge_by(chat_ord, gem_ord, ['project', 'outcome'])
    ord_rows = []
    for _, c, g in pairs:
        ord_rows.append({
            'project': project,
            'outcome': c['outcome'],
            'chatgpt_status': c['status'],
            'gemini_status': g['status'],
            'chatgpt_levels': c['n_levels_observed'],
            'gemini_levels': g['n_levels_observed'],
            'chatgpt_warning': c.get('warning', ''),
            'gemini_warning': g.get('warning', ''),
        })
    write_csv(
        out_dir / 'gemini_vs_chatgpt_ordinal_status_v0.1.csv',
        ord_rows,
        list(ord_rows[0].keys()) if ord_rows else [],
    )

    both_confirm = sum(r['chatgpt_holm_significant'] == 'True' and r['gemini_holm_significant'] == 'True' for r in confirm_out)
    chat_only_confirm = sum(r['chatgpt_holm_significant'] == 'True' and r['gemini_holm_significant'] == 'False' for r in confirm_out)
    gem_only_confirm = sum(r['chatgpt_holm_significant'] == 'False' and r['gemini_holm_significant'] == 'True' for r in confirm_out)
    neither_confirm = sum(r['chatgpt_holm_significant'] == 'False' and r['gemini_holm_significant'] == 'False' for r in confirm_out)

    both_sec = sum(r['chatgpt_bh_fdr_significant'] == 'True' and r['gemini_bh_fdr_significant'] == 'True' for r in sec_out)
    chat_only_sec = sum(r['chatgpt_bh_fdr_significant'] == 'True' and r['gemini_bh_fdr_significant'] == 'False' for r in sec_out)
    gem_only_sec = sum(r['chatgpt_bh_fdr_significant'] == 'False' and r['gemini_bh_fdr_significant'] == 'True' for r in sec_out)
    neither_sec = sum(r['chatgpt_bh_fdr_significant'] == 'False' and r['gemini_bh_fdr_significant'] == 'False' for r in sec_out)

    summary.append((project, len(confirm_out), both_confirm, chat_only_confirm, gem_only_confirm, neither_confirm,
                    len(sec_out), both_sec, chat_only_sec, gem_only_sec, neither_sec,
                    sum(r['same_direction'] for r in confirm_out), sum(r['same_direction'] for r in sec_out)))

summary_path = ROOT / 'cross_model_summary_v0.1.md'
with summary_path.open('w', encoding='utf-8') as f:
    f.write('# Gemini vs ChatGPT model comparison v0.1\n\n')
    f.write('This is a post-hoc descriptive comparison of the already-generated, prespecified project-level analyses. It does not alter the primary/secondary inferential gates.\n\n')
    f.write('| Project | Confirmatory tests | Both Holm-significant | ChatGPT only | Gemini only | Neither | Secondary tests | Both BH-FDR-significant | ChatGPT only | Gemini only | Neither | Same direction (confirmatory) | Same direction (secondary) |\n')
    f.write('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n')
    for s in summary:
        f.write('| ' + ' | '.join(str(x) for x in s) + ' |\n')
    f.write('\n## Primary interpretation rule\n\n')
    f.write('The cross-model comparison should be read as convergence/divergence of effect estimates and prespecified significance status, not as a ranking of models.\n')

print('Created cross-model comparison outputs for IWA and GTCL.')
print('Created:', summary_path)
for project, n, both, co, go, neither, ns, boths, cos, gos, neithers, samec, sames in summary:
    print(f'{project}: confirmatory {n}; both significant={both}; ChatGPT-only={co}; Gemini-only={go}; neither={neither}; same direction={samec}/{n}')
    print(f'{project}: secondary {ns}; both significant={boths}; ChatGPT-only={cos}; Gemini-only={gos}; neither={neithers}; same direction={sames}/{ns}')
