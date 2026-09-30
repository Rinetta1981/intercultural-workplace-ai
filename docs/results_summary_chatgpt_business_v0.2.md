# ChatGPT Business Results Summary v0.2

## Status

This document summarizes the completed **ChatGPT Business / GPT-5.6 Sol (Medium reasoning)** analysis for Intercultural Workplace AI (IWA). These results are **system-specific**. The planned Gemini replication has not yet been completed and no cross-system claims are made here.

## Research question

Does an AI system evaluate workplace communicators differently when the **factual workplace content is held constant** but the message varies in:

- **directness**: direct vs mitigated
- **register**: conversational vs institutional

The four experimental conditions are DC, DI, MC, and MI. Ten scenario families were evaluated, with three replicates per condition, for **120 ChatGPT Business observations**.

## Confirmatory outcomes

Primary outcomes were:

- competence
- leadership potential
- managerial intervention need

Inference used exact two-sided sign-flip permutation tests over scenario-family contrasts, with Holm correction across the nine preregistered confirmatory tests.

**No primary test survived Holm correction.**

Descriptively, directness reduced competence (mean contrast = -0.133; raw p = .03125; Holm p = .25) and leadership potential (mean contrast = -0.283; raw p = .015625; Holm p = .140625), but these did not meet the confirmatory significance criterion.

Managerial intervention need was completely invariant to directness, register, and their interaction.

## Secondary outcomes

The strongest secondary results concerned interpersonal evaluation.

| Outcome | Contrast | Mean contrast | BH-FDR p | Result |
|---|---|---:|---:|---|
| Cooperativeness | Directness | -0.900 | .0176 | Survived BH-FDR |
| Professionalism | Directness | -0.367 | .0352 | Survived BH-FDR |
| Communicative appropriateness | Directness | -0.283 | .281 | Did not survive BH-FDR |

Register and directness x register interactions did not survive multiplicity correction.

## Categorical managerial recommendations

The categorical recommendation outcome was **recommended managerial response**.

Observed categories were:

- none
- acknowledge
- clarify

Directness produced almost no change in the recommendation distribution:

- acknowledge: 17/60 direct vs 17/60 mitigated
- clarify: 8/60 direct vs 7/60 mitigated
- none: 35/60 direct vs 36/60 mitigated

Register produced a somewhat larger descriptive redistribution between `acknowledge` and `clarify`, but `none` remained essentially stable.

This suggests that style sensitivity in person perception did **not** meaningfully propagate into downstream managerial action recommendations in this system.

## Exploratory role-relation analysis

Role relation was explored descriptively across upward, peer, and downward scenario families.

The directness penalty was largest in **peer scenarios** for several outcomes, including:

- cooperativeness
- professionalism
- leadership potential
- communicative appropriateness

Because role relation is not independently crossed within each scenario family and each subgroup contains only 3-4 families, these patterns are exploratory and should not be interpreted as clean causal moderation effects.

## Ordinal-model sensitivity analysis

A cumulative-link mixed model was preregistered as a sensitivity analysis:

`score ~ directness * register + (1 | family_id)`

Clean ordinal models corroborated negative directness effects for:

- cooperativeness
- professionalism

Leadership potential and communicative appropriateness also showed negative directness signals in the sensitivity model, but these do not override the multiplicity-corrected family-level results.

Two important diagnostics:

- **competence**: ordinal fit was numerically unstable / non-converged and is not interpreted
- **managerial intervention need**: not estimable because the outcome was constant

## Main interpretation

The strongest system-specific pattern is:

> **Directness changes interpersonal evaluation more than downstream managerial action.**

Within GPT-5.6 Sol in ChatGPT Business, more direct workplace wording was consistently judged as less cooperative and less professional even when the substantive workplace content was held constant. However, managerial intervention judgments and categorical managerial responses were substantially more invariant.

This is evidence of **sociopragmatic sensitivity in person perception**, not evidence of national, ethnic, or demographic bias. The stimuli contain no demographic or national identity information.

## Reproducibility

Analysis-ready data:

- `results/analysis_ready/chatgpt_business_v0.2_long.csv`
- `results/analysis_ready/chatgpt_business_v0.2_cell_means.csv`
- `results/analysis_ready/chatgpt_business_v0.2_family_contrasts.csv`

Analysis outputs:

- `results/analysis/chatgpt_business_v0.2_confirmatory.csv`
- `results/analysis/chatgpt_business_v0.2_secondary.csv`
- `results/analysis/chatgpt_business_v0.2_categorical_by_*.csv`
- `results/analysis/chatgpt_business_v0.2_role_relation_exploratory.csv`
- `results/analysis/chatgpt_business_v0.2_ordinal_sensitivity.csv`
- `results/analysis/chatgpt_business_v0.2_ordinal_diagnostics.csv`

Reproducibility scripts are in `scripts/analysis/`.
