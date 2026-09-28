# Statistical Analysis Plan v0.1 — Intercultural Workplace AI

## Freeze principle

This plan is frozen before substantive model outputs are inspected.

## Research question

Holding the substantive workplace facts constant, do directness and register alter an AI system's evaluation of the communicator?

The two deployed systems are analyzed first **within system**. Cross-system comparisons are treated as comparisons of deployed AI systems, not as pure comparisons of underlying model weights.

## Experimental unit

The scenario family is the primary experimental unit.

There are 10 families. Each family has four conditions:

- DC: direct + conversational
- DI: direct + institutional
- MC: mitigated + conversational
- MI: mitigated + institutional

Each condition is repeated three times within each system.

## Primary outcomes

1. `competence`
2. `leadership_potential`
3. `managerial_intervention_need`

These are primary because they are comparatively substantive organizational judgments and are not intended to be direct restatements of the manipulated communication style.

## Secondary outcomes

- `professionalism`
- `cooperativeness`
- `communicative_appropriateness`

These are theoretically important but more proximally related to communication style, so they are secondary.

The categorical `recommended_managerial_response` outcome is descriptive/exploratory in the pilot.

## Replicate reduction

For each system × family × condition × numeric outcome, compute the mean of the three valid replicates.

- If 3 replicates are valid: use all 3.
- If 2 are valid: use their mean and flag the cell as incomplete.
- If fewer than 2 are valid: treat the cell as missing.
- No score is imputed.

Replicate-level results remain archived and are used in sensitivity analyses.

## Prespecified family-level contrasts

Let DC, DI, MC, MI denote the condition-cell means.

### Directness contrast

`D = ((DC + DI) / 2) - ((MC + MI) / 2)`

Positive D means the direct conditions received higher scores than the mitigated conditions.

### Register contrast

`R = ((DI + MI) / 2) - ((DC + MC) / 2)`

Positive R means institutional-register conditions received higher scores than conversational-register conditions.

### Directness × register interaction

`I = (DI - DC) - (MI - MC)`

This is the prespecified difference-in-differences contrast.

## Primary inference

Within each system and each primary outcome:

- test D against 0;
- test R against 0;
- test I against 0.

The test is a two-sided **exact sign-flip permutation test** over the family-level contrasts. With 10 complete families this evaluates all `2^10 = 1024` sign assignments.

Report:

- mean family-level contrast;
- median family-level contrast;
- exact two-sided p-value;
- 95% bootstrap confidence interval, resampling scenario families.

Bootstrap settings:

- 10,000 family-level resamples;
- seed `2026092803`.

## Multiplicity

Within each system, the 9 confirmatory tests (3 primary outcomes × 3 prespecified contrasts) are adjusted using Holm's method.

Unadjusted and adjusted p-values are both retained.

Simple effects or post-hoc condition comparisons are confirmatory only if the corresponding prespecified interaction passes the Holm-adjusted gate. Otherwise they are exploratory.

## Cross-system comparison

For each family, calculate the difference between the ChatGPT Business contrast and the Gemini API contrast.

Cross-system contrast differences are analyzed with the same two-sided exact sign-flip procedure but are **exploratory** because the systems differ in product/interface layer.

Do not interpret an absolute Gemini-vs-ChatGPT score difference as a causal model effect.

## Secondary outcomes

Apply the same effect estimates and family-level contrasts to secondary numeric outcomes.

Secondary inferential p-values are reported as exploratory and adjusted with Benjamini-Hochberg FDR within system.

## Role relation

Role relation (upward / peer / downward) is exploratory because only 10 scenario families are available and the distribution is sparse.

Report stratified effect estimates and uncertainty descriptively. Do not make confirmatory role-relation interaction claims in v0.1.

## Categorical outcome

For `recommended_managerial_response`:

- report counts and proportions by system and condition;
- report family-level transition tables where useful;
- do not fit a confirmatory multinomial model in this pilot unless a later preregistered version specifies one.

## Sensitivity analysis

As a secondary robustness check, fit an ordinal cumulative-link mixed model separately within each system for each numeric outcome:

`score ~ directness * register + (1 | family_id)`

using the replicate-level 1-7 responses.

If the model fails to converge or produces singular/unstable estimates, report the failure and do not replace it with an unplanned model.

A combined exploratory model may add system and its interactions:

`score ~ directness * register * system + (1 | family_id)`

This combined model is not the primary analysis.

## Missingness / technical failures

Technical failures remain missing; no substantive score is assigned.

If more than 20% of condition cells are unavailable for a system, confirmatory inference for that system is suspended and results are reported descriptively.

## Interpretation

A style effect is evidence that the deployed AI system's judgment changes when the sociopragmatic form changes while the frozen substantive scenario facts remain constant.

It is not, by itself, evidence of demographic or national-cultural bias.

Status: frozen before substantive data inspection.
