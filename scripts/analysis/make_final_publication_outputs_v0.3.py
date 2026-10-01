from pathlib import Path
import csv
import matplotlib.pyplot as plt

BASE = Path.cwd()
IWA = BASE / 'intercultural-workplace-ai'
GTCL = BASE / 'global-team-conflict-lab'

OUT_ROOT = BASE / 'publication_outputs_v0.1'
TABLES = OUT_ROOT / 'tables'
FIGS = OUT_ROOT / 'figures'
DOCS = OUT_ROOT / 'docs'
for p in (TABLES, FIGS, DOCS):
    p.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def fnum(x):
    return float(x)


def direction_class(a, b, tol=1e-12):
    a0 = abs(a) <= tol
    b0 = abs(b) <= tol
    if a0 and b0:
        return 'both_zero'
    if a0 or b0:
        return 'zero_boundary'
    if a * b > 0:
        return 'same_nonzero_direction'
    return 'reversal'


def merge_models(chat_rows, gem_rows, pkey='outcome', ckey='contrast'):
    gm = {(r[pkey], r[ckey]): r for r in gem_rows}
    out = []
    for c in chat_rows:
        g = gm[(c[pkey], c[ckey])]
        cm = fnum(c['mean_contrast'])
        gmval = fnum(g['mean_contrast'])
        out.append((c, g, direction_class(cm, gmval)))
    return out


def write_rows(path, header, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


projects = [('IWA', IWA), ('GTCL', GTCL)]
all_confirm = []
all_secondary = []

for project, root in projects:
    chat_c = read_csv(root / 'results/analysis/chatgpt_business_v0.2_confirmatory.csv')
    gem_c = read_csv(root / 'results/analysis/gemini_web_ui_v0.3_confirmatory.csv')
    chat_s = read_csv(root / 'results/analysis/chatgpt_business_v0.2_secondary.csv')
    gem_s = read_csv(root / 'results/analysis/gemini_web_ui_v0.3_secondary.csv')

    for c, g, dc in merge_models(chat_c, gem_c):
        all_confirm.append([
            project, c['outcome'], c['contrast'], c['mean_contrast'],
            c['bootstrap_ci_low_95'], c['bootstrap_ci_high_95'], c['holm_p_9tests'],
            g['mean_contrast'], g['bootstrap_ci_low_95'], g['bootstrap_ci_high_95'],
            g['holm_p_9tests'], dc, c['reject_holm_0_05'], g['reject_holm_0_05']
        ])

    for c, g, dc in merge_models(chat_s, gem_s):
        all_secondary.append([
            project, c['outcome'], c['contrast'], c['mean_contrast'],
            c['bootstrap_ci_low_95'], c['bootstrap_ci_high_95'], c['bh_fdr_p'],
            g['mean_contrast'], g['bootstrap_ci_low_95'], g['bootstrap_ci_high_95'],
            g['bh_fdr_p'], dc, c['reject_bh_0_05'], g['reject_bh_0_05']
        ])

write_rows(TABLES/'table1_confirmatory_cross_model.csv',
           ['project','outcome','contrast','chatgpt_mean','chatgpt_ci_low_95','chatgpt_ci_high_95','chatgpt_holm_p','gemini_mean','gemini_ci_low_95','gemini_ci_high_95','gemini_holm_p','direction_class','chatgpt_significant','gemini_significant'],
           all_confirm)
write_rows(TABLES/'table2_secondary_cross_model.csv',
           ['project','outcome','contrast','chatgpt_mean','chatgpt_ci_low_95','chatgpt_ci_high_95','chatgpt_bh_fdr_p','gemini_mean','gemini_ci_low_95','gemini_ci_high_95','gemini_bh_fdr_p','direction_class','chatgpt_significant','gemini_significant'],
           all_secondary)

# Categorical recommendations: directness only, using the already-generated model comparison files.
cat_rows = []
for project, root in projects:
    path = root / 'results/analysis/gemini_vs_chatgpt_categorical_publication_v0.5.csv'
    for r in read_csv(path):
        if r['dimension'] == 'directness':
            cat_rows.append([project, r['dimension'], r['level'], r['category'], r['chatgpt_proportion'], r['gemini_proportion'], r['gemini_minus_chatgpt']])
write_rows(TABLES/'table3_categorical_recommendations_cross_model.csv',
           ['project','dimension','level','category','chatgpt_proportion','gemini_proportion','gemini_minus_chatgpt'], cat_rows)

# Ordinal sensitivity and family-level correlation outputs are already the final audited v0.5 files.
ord_rows = []
for project, root in projects:
    for r in read_csv(root / 'results/analysis/gemini_vs_chatgpt_ordinal_publication_v0.5.csv'):
        r2 = dict(r); r2['project'] = project; ord_rows.append(r2)
if ord_rows:
    keys = ['project','outcome','chatgpt_status','gemini_status','notes']
    write_rows(TABLES/'table4_ordinal_sensitivity_cross_model.csv', keys, [[r.get(k,'') for k in keys] for r in ord_rows])

corr_rows = []
for project, root in projects:
    for r in read_csv(root / 'results/analysis/gemini_vs_chatgpt_family_correlation_v0.5.csv'):
        r2 = dict(r); r2['project'] = project; corr_rows.append(r2)
if corr_rows:
    keys = ['project','outcome','contrast','pearson_r']
    # v0.5 files use either pearson_r or pearson_r_n10_families depending on generator version.
    corr_out=[]
    for r in corr_rows:
        val=r.get('pearson_r', r.get('pearson_r_n10_families',''))
        corr_out.append([r['project'],r['outcome'],r['contrast'],val])
    write_rows(TABLES/'table5_family_level_cross_model_correlations.csv', ['project','outcome','contrast','pearson_r_n10_families'], corr_out)

# Publication figures: directness contrasts.
def make_forest(project, filename):
    rows=[r for r in all_confirm+all_secondary if r[0]==project and r[2]=='directness']
    labels=[r[1].replace('_',' ') for r in rows]
    y=list(range(len(labels)))[::-1]
    chat=[fnum(r[3]) for r in rows]; chat_lo=[fnum(r[4]) for r in rows]; chat_hi=[fnum(r[5]) for r in rows]
    gem=[fnum(r[7]) for r in rows]; gem_lo=[fnum(r[8]) for r in rows]; gem_hi=[fnum(r[9]) for r in rows]
    fig,ax=plt.subplots(figsize=(9,max(4.5,len(labels)*0.65)))
    ax.errorbar(chat,[v+0.10 for v in y],xerr=[[x-l for x,l in zip(chat,chat_lo)],[h-x for x,h in zip(chat,chat_hi)]],fmt='o',capsize=3,label='ChatGPT')
    ax.errorbar(gem,[v-0.10 for v in y],xerr=[[x-l for x,l in zip(gem,gem_lo)],[h-x for x,h in zip(gem,gem_hi)]],fmt='s',capsize=3,label='Gemini')
    ax.axvline(0,linewidth=1)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlabel('Directness contrast (Direct - Mitigated)')
    ax.set_title(f'{project}: Directness contrasts across models')
    ax.legend(); fig.tight_layout()
    for ext,kw in [('png',{'dpi':300}),('pdf',{}),('svg',{})]:
        fig.savefig(FIGS/(filename+'.'+ext),bbox_inches='tight',**kw)
    plt.close(fig)

make_forest('IWA','figure1_iwa_directness_effects')
make_forest('GTCL','figure2_gtcl_directness_effects')

# Key replicated GTCL effect.
gt=[r for r in all_secondary if r[0]=='GTCL' and r[1]=='speaker_cooperativeness' and r[2]=='directness'][0]
chat_mean=fnum(gt[3]); chat_lo=fnum(gt[4]); chat_hi=fnum(gt[5]); gem_mean=fnum(gt[7]); gem_lo=fnum(gt[8]); gem_hi=fnum(gt[9])
fig,ax=plt.subplots(figsize=(7,5))
ax.errorbar([chat_mean,gem_mean],[1,0],xerr=[[chat_mean-chat_lo,gem_mean-gem_lo],[chat_hi-chat_mean,gem_hi-gem_mean]],fmt='o',capsize=4)
ax.axvline(0,linewidth=1)
ax.set_yticks([1,0]); ax.set_yticklabels(['ChatGPT','Gemini'])
ax.set_xlabel('Directness contrast (Direct - Mitigated)')
ax.set_title('GTCL: Speaker cooperativeness × Directness\nBH-FDR p = .0234 in both systems',pad=12)
fig.tight_layout()
for ext,kw in [('png',{'dpi':300}),('pdf',{}),('svg',{})]: fig.savefig(FIGS/('figure3_gtcl_cooperativeness_replication.'+ext),bbox_inches='tight',**kw)
plt.close(fig)

# Categorical directness figures.
def make_cat(project, filename, title):
    rows=[r for r in cat_rows if r[0]==project]
    levels=[]; cats=[]
    for r in rows:
        if r[2] not in levels: levels.append(r[2])
        if r[3] not in cats: cats.append(r[3])
    groups=[(l,c) for l in levels for c in cats]
    chat=[]; gem=[]
    for l,c in groups:
        r=[x for x in rows if x[2]==l and x[3]==c][0]
        chat.append(fnum(r[4])); gem.append(fnum(r[5]))
    x=list(range(len(groups))); width=0.36
    fig,ax=plt.subplots(figsize=(10,5.5))
    ax.bar([v-width/2 for v in x],chat,width,label='ChatGPT')
    ax.bar([v+width/2 for v in x],gem,width,label='Gemini')
    ax.set_xticks(x); ax.set_xticklabels([f'{l}\n{c.replace("_"," ")}' for l,c in groups])
    ax.set_ylim(0,1); ax.set_ylabel('Proportion of recommendations'); ax.set_title(title); ax.legend(); fig.tight_layout()
    for ext,kw in [('png',{'dpi':300}),('pdf',{}),('svg',{})]: fig.savefig(FIGS/(filename+'.'+ext),bbox_inches='tight',**kw)
    plt.close(fig)

make_cat('IWA','figure4_iwa_categorical_directness','IWA: Managerial recommendations by directness and model')
make_cat('GTCL','figure5_gtcl_categorical_directness','GTCL: Conflict-management recommendations by directness and model')

# Captions and a concise final results note.
(DOCS/'publication_figures_and_tables_v0.1.md').write_text('''# Publication Tables and Figures — Captions and Notes\n\n**Table 1. Confirmatory cross-model results.** Family-level mean contrasts with 95% bootstrap confidence intervals and Holm-adjusted p-values across the nine confirmatory tests within each project.\n\n**Table 2. Secondary cross-model results.** Family-level mean contrasts with 95% bootstrap confidence intervals and BH-FDR-adjusted p-values.\n\n**Table 3. Categorical recommendations.** Observed proportions by directness level and model; descriptive only.\n\n**Table 4. Ordinal sensitivity.** Audited cumulative-link mixed-model status. Warned fits are not treated as clean inferential sensitivity confirmations; one-level outcomes are not estimable.\n\n**Table 5. Family-level cross-model correlations.** Descriptive Pearson correlations across the ten scenario families; not additional inferential tests.\n\n**Figure 1.** IWA Directness contrasts across models; points are family-level means and intervals are 95% bootstrap CIs.\n\n**Figure 2.** GTCL Directness contrasts across models; points are family-level means and intervals are 95% bootstrap CIs.\n\n**Figure 3.** GTCL speaker cooperativeness × Directness, the secondary effect significant under BH-FDR in both systems.\n\n**Figure 4.** IWA managerial recommendation distributions by directness and model.\n\n**Figure 5.** GTCL conflict-management recommendation distributions by directness and model.\n\n**General note.** The ChatGPT–Gemini comparison is descriptive and post-hoc and does not alter the prespecified inferential gates or rank the models.\n''',encoding='utf-8')

(DOCS/'final_cross_model_results_v0.1.md').write_text('''# Final Cross-Model Publication Results\n\nThe final publication package compares the already-generated ChatGPT Business and Gemini web-UI analyses without modifying frozen data or rerunning inferential tests. No confirmatory effect survived Holm correction in either system. The clearest cross-model secondary convergence is the GTCL directness effect on speaker cooperativeness: ChatGPT -0.817 and Gemini -0.750, both BH-FDR p=.0234. IWA secondary directness effects on professionalism and cooperativeness were significant for ChatGPT but not Gemini, although all nine IWA secondary contrasts had the same direction across systems. Categorical recommendations were comparatively stable in IWA and more distributionally different between models in GTCL. Ordinal sensitivity results are reported with explicit numerical-warning and non-estimability qualifications.\n''',encoding='utf-8')


# Deployment instructions for the two repositories.
(DOCS/'deploy_to_repositories.sh').write_text('''#!/bin/sh
set -eu

for repo in intercultural-workplace-ai global-team-conflict-lab; do
  mkdir -p "$repo/results/tables" "$repo/results/figures" "$repo/docs"
done

# Copy the cross-model tables and documentation to both repositories as shared audit outputs.
for repo in intercultural-workplace-ai global-team-conflict-lab; do
  cp publication_outputs_v0.1/tables/table1_confirmatory_cross_model.csv "$repo/results/tables/"
  cp publication_outputs_v0.1/tables/table2_secondary_cross_model.csv "$repo/results/tables/"
  cp publication_outputs_v0.1/tables/table3_categorical_recommendations_cross_model.csv "$repo/results/tables/"
  cp publication_outputs_v0.1/tables/table4_ordinal_sensitivity_cross_model.csv "$repo/results/tables/"
  cp publication_outputs_v0.1/tables/table5_family_level_cross_model_correlations.csv "$repo/results/tables/"
  cp publication_outputs_v0.1/docs/publication_figures_and_tables_v0.1.md "$repo/docs/"
  cp publication_outputs_v0.1/docs/final_cross_model_results_v0.1.md "$repo/docs/"
done

cp publication_outputs_v0.1/figures/figure1_iwa_directness_effects.* intercultural-workplace-ai/results/figures/
cp publication_outputs_v0.1/figures/figure2_gtcl_directness_effects.* global-team-conflict-lab/results/figures/
cp publication_outputs_v0.1/figures/figure3_gtcl_cooperativeness_replication.* global-team-conflict-lab/results/figures/
cp publication_outputs_v0.1/figures/figure4_iwa_categorical_directness.* intercultural-workplace-ai/results/figures/
cp publication_outputs_v0.1/figures/figure5_gtcl_categorical_directness.* global-team-conflict-lab/results/figures/

echo "Publication outputs copied to both repositories. Review git status before committing."
''',encoding='utf-8')
print(f'Created final publication outputs in {OUT_ROOT}')
print('Tables: 5')
print('Figures: 5 x PNG/PDF/SVG')
print('Docs: publication_figures_and_tables_v0.1.md; final_cross_model_results_v0.1.md; deploy_to_repositories.sh')
