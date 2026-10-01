# Cross-model Results — IWA (ChatGPT vs Gemini)

This is a descriptive post-hoc comparison of the prespecified project-level analyses. It does not alter the confirmatory or secondary inferential gates.

## Direction classification

Direction is classified with a tolerance of 1e-12: same non-zero direction, both zero, zero-boundary (one estimate is zero), or reversal (opposite non-zero signs). This avoids treating zero-versus-small-nonzero contrasts as substantive sign reversals.

## Confirmatory

Direction classes: {'same_nonzero_direction': 3, 'zero_boundary': 1, 'reversal': 2, 'both_zero': 3}

| Outcome | Contrast | ChatGPT | Gemini | Direction | Significance (C/G) |
|---|---|---:|---:|---|---|
| competence | directness | -0.133 | -0.083 | same_nonzero_direction | False / False |
| competence | interaction | +0.067 | +0.100 | same_nonzero_direction | False / False |
| competence | register | -0.000 | +0.083 | zero_boundary | False / False |
| leadership_potential | directness | -0.283 | -0.367 | same_nonzero_direction | False / False |
| leadership_potential | interaction | -0.033 | +0.267 | reversal | False / False |
| leadership_potential | register | -0.050 | +0.133 | reversal | False / False |
| managerial_intervention_need | directness | +0.000 | +0.000 | both_zero | False / False |
| managerial_intervention_need | interaction | +0.000 | +0.000 | both_zero | False / False |
| managerial_intervention_need | register | +0.000 | +0.000 | both_zero | False / False |

## Secondary

Direction classes: {'same_nonzero_direction': 9}

| Outcome | Contrast | ChatGPT | Gemini | Direction | Significance (C/G) |
|---|---|---:|---:|---|---|
| communicative_appropriateness | directness | -0.283 | -0.517 | same_nonzero_direction | False / False |
| communicative_appropriateness | interaction | +0.100 | +0.233 | same_nonzero_direction | False / False |
| communicative_appropriateness | register | +0.017 | +0.117 | same_nonzero_direction | False / False |
| cooperativeness | directness | -0.900 | -0.283 | same_nonzero_direction | True / False |
| cooperativeness | interaction | +0.067 | +0.033 | same_nonzero_direction | False / False |
| cooperativeness | register | -0.100 | -0.050 | same_nonzero_direction | False / False |
| professionalism | directness | -0.367 | -0.517 | same_nonzero_direction | True / False |
| professionalism | interaction | +0.267 | +0.233 | same_nonzero_direction | False / False |
| professionalism | register | +0.133 | +0.117 | same_nonzero_direction | False / False |

## Categorical recommendation distributions

| Dimension | Level | Category | ChatGPT | Gemini | Gemini − ChatGPT |
|---|---|---|---:|---:|---:|
| directness | direct | acknowledge | 0.283 | 0.200 | -0.083 |
| directness | direct | clarify | 0.133 | 0.200 | +0.067 |
| directness | direct | none | 0.583 | 0.600 | +0.017 |
| directness | mitigated | acknowledge | 0.283 | 0.183 | -0.100 |
| directness | mitigated | clarify | 0.117 | 0.217 | +0.100 |
| directness | mitigated | none | 0.600 | 0.600 | +0.000 |
| register | conversational | acknowledge | 0.317 | 0.183 | -0.133 |
| register | conversational | clarify | 0.083 | 0.217 | +0.133 |
| register | conversational | none | 0.600 | 0.600 | +0.000 |
| register | institutional | acknowledge | 0.250 | 0.200 | -0.050 |
| register | institutional | clarify | 0.167 | 0.200 | +0.033 |
| register | institutional | none | 0.583 | 0.600 | +0.017 |

## Ordinal sensitivity

| Outcome | ChatGPT | Gemini |
|---|---|---|
| communicative_appropriateness | fit_ok (2 levels) | fit_ok (3 levels); numerical warning |
| competence | fit_ok (3 levels) | fit_ok (3 levels) |
| cooperativeness | fit_ok (3 levels) | fit_ok (3 levels) |
| leadership_potential | fit_ok (4 levels) | fit_ok (3 levels) |
| managerial_intervention_need | fit_error (1 levels); not estimable | fit_error (1 levels); not estimable |
| professionalism | fit_ok (2 levels) | fit_ok (3 levels); numerical warning |

Numerical warnings on otherwise fitted ordinal models indicate identifiability/convergence concerns; those fits are not treated as clean inferential sensitivity confirmations. Models marked fit_error are not estimable and are not interpreted.

## Family-level cross-model correlations

These are descriptive Pearson correlations across the 10 scenario families and are not additional inferential tests.

| Outcome | Contrast | Pearson r |
|---|---|---:|
| communicative_appropriateness | directness | 0.798 |
| communicative_appropriateness | register | 0.023 |
| communicative_appropriateness | interaction | -0.243 |
| competence | directness | 0.136 |
| competence | register | -0.000 |
| competence | interaction | 0.429 |
| cooperativeness | directness | 0.651 |
| cooperativeness | register | 0.250 |
| cooperativeness | interaction | -0.186 |
| leadership_potential | directness | 0.106 |
| leadership_potential | register | 0.217 |
| leadership_potential | interaction | 0.514 |
| managerial_intervention_need | directness | NA (constant vector) |
| managerial_intervention_need | register | NA (constant vector) |
| managerial_intervention_need | interaction | NA (constant vector) |
| professionalism | directness | 0.406 |
| professionalism | register | 0.024 |
| professionalism | interaction | 0.024 |

## Manuscript-level synthesis

No secondary effect was significant under BH-FDR in both systems.
ChatGPT-only BH-FDR-significant secondary effects: 2; Gemini-only: 0.
The cross-model comparison is descriptive and should be interpreted as convergence/divergence of effect estimates and significance status, not as a ranking of models.

Family-level correlations are descriptive summaries across 10 scenario families and should not be treated as new inferential tests.
