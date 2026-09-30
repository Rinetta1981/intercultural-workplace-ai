# Protocol Amendment: Gemini Web UI Replication v0.3

**Date:** 2026-10-01

## Scope

This amendment applies to the second-system replication arm of both:

- Intercultural Workplace AI (IWA)
- Global Team Conflict Lab (GTCL)

## Reason for amendment

The frozen v0.2 protocol specified the Google Gemini Developer API free tier as the second system. Repeated authentication/credential setup problems prevented substantive collection through that interface.

**No substantive Gemini API observations were collected before this amendment.**

To preserve the zero-additional-cost constraint and complete the planned cross-system replication, the second arm is changed from the Gemini Developer API to the Gemini web application.

## What changes

The execution interface changes from:

- `gemini_api_free`

to:

- `gemini_web_ui`

Collection uses the Gemini web application in a fresh **Temporary Chat** for each observation, with a single user-selected Gemini model held constant throughout each project.

The exact model label displayed in the Gemini web interface is recorded in the local run metadata before the first observation.

## What does not change

The following frozen elements remain unchanged:

- 10 scenario families per project
- 4 conditions per family: DC, DI, MC, MI
- 3 replicates per family × condition cell
- 120 Gemini observations per project
- frozen scenario texts
- queue order
- rendered prompts
- prompt fingerprints
- output schema
- substantive scoring rubric
- family-level experimental unit
- confirmatory outcomes
- secondary outcomes
- directness, register, and interaction contrasts
- exact sign-flip inference
- multiplicity corrections
- bootstrap procedure
- categorical-outcome treatment
- exploratory role-relation analysis

The original frozen Gemini API execution-plan rows are used only as the immutable queue/order and rendered-prompt fingerprint source. New collection records are identified as `gemini_web_ui`.

## Web UI collection controls

For every observation:

1. Start a fresh Gemini **Temporary Chat**.
2. Use the same selected Gemini model for the entire run.
3. Use standard text chat only.
4. Do not use Gems, Deep Research, Connected Apps, or manually invoked tools.
5. Paste the frozen prompt unchanged.
6. Copy the full model response.
7. Validate the response locally against the frozen JSON schema before saving.
8. Do not alter substantive score or recommendation values.

Deterministic structural normalization is permitted only when needed to match the frozen schema, using the same principle as the ChatGPT Business collector.

## Interpretation

The cross-system comparison is therefore a comparison between **deployed AI systems/interfaces**, not an API-equivalent provider benchmark.

System differences may reflect model, interface, product configuration, or system-level behavior and will be interpreted as exploratory cross-system evidence rather than as a controlled estimate of model-family effects.

## Analysis firewall

The frozen statistical analysis plan remains unchanged.

Gemini results will be collected and frozen before cross-system interpretation is finalized. The existing ChatGPT Business results were analyzed before this amendment; no Gemini results were available when the amendment was made.
