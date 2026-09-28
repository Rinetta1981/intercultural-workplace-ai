# Model Execution Protocol v0.1

## Scope

This protocol governs the first model-evaluation runs for the frozen pilot dataset.

## Frozen model set

The primary cross-provider model set is defined in `configs/model_set_v0.1.json` and must not be changed after substantive outputs have been inspected without creating a new version.

## Core design

- Every condition message is evaluated in an independent, stateless API call.
- No conversation history is carried between items.
- Family IDs and condition labels are hidden from the model.
- The same project-specific prompt template and output schema are used for every item within a project.
- Frozen stimuli are read only from `data/frozen/pilot_v0.1/`.
- Raw model outputs are retained unchanged alongside parsed outputs.
- Tools, browsing, retrieval, and external grounding are disabled.

## Reasoning and sampling configuration

Cross-provider sampling parameters are not forced to a common non-default value.

- Sampling parameters such as `temperature`, `top_p`, and `top_k` are left at provider defaults.
- A comparable low reasoning/effort setting is requested where the provider supports it.
- Provider-specific effective settings are recorded for every call.
- Three independent replicates per condition are used to quantify residual stochasticity.

Frozen primary reasoning settings:

- OpenAI GPT-5.6 Sol: `reasoning.effort = low`
- Anthropic Claude Sonnet 5: `output_config.effort = low`
- Google Gemini 3.8 Flash: `generation_config.thinking_level = low`

If an API rejects a frozen setting at execution time, do not silently substitute another value. Record the incompatibility and create a versioned protocol amendment before substantive execution.

## Replication

Primary pilot runs use three independent replicates per condition per model.

Per project:

- 10 families
- 4 conditions per family
- 40 unique condition messages
- 3 replicates
- 120 queue rows per model
- 3 primary models
- 360 planned calls

Across both projects: 720 planned substantive calls.

## Ordering and counterbalancing

The condition/replicate queue is generated before execution using master randomization seed:

`20260928`

A full model x queue execution plan is then generated using seed:

`2026092801`

Both CSV files and their SHA-256 fingerprints are frozen before model execution.

Because each item is a stateless call, order is not treated as a substantive experimental factor. Deterministic shuffling prevents systematic batching by family, condition, replicate, or provider.

## Model-facing information

The model receives only:

- the invariant workplace context field;
- speaker role;
- addressee role;
- one condition-specific message;
- the fixed project scoring rubric.

The model does not receive:

- family ID;
- condition code;
- directness label;
- register label;
- hypothesis;
- requested-action metadata;
- deadline metadata outside what is naturally present in the context/message;
- organizational-stakes metadata outside what is naturally present in the context/message;
- another model's outputs;
- another condition from the same family.

## Structured outputs

Each provider is requested to return output constrained by the project-specific schema in `schemas/model_output_v0.1.schema.json`.

Provider-native structured-output mechanisms should be used when supported. The exact request parameters and API/SDK versions must be logged.

## Output handling

For every call retain:

- project;
- frozen dataset fingerprint;
- prompt-template fingerprint;
- queue fingerprint;
- execution-plan fingerprint;
- queue row ID;
- execution ID;
- family ID;
- hidden condition code;
- replicate;
- provider;
- model identifier;
- requested reasoning/effort configuration;
- effective configuration when reported;
- timestamp;
- latency;
- raw response;
- parsed response;
- schema-validation status;
- technical error status;
- retry count.

## Failure policy

A technical failure is not converted into a substantive score.

Technical failures include:

- network/API failure;
- timeout;
- empty response;
- invalid JSON;
- output that cannot be validated against the frozen response schema;
- refusal or provider-side block that prevents the requested structured judgment.

A failed call may be retried up to two times using the same prompt and frozen configuration.

If all attempts fail:

- preserve all failure metadata;
- mark the execution item as technical failure;
- do not impute scores;
- do not silently replace the item with a different model, condition, prompt, or parameter setting.

## Contamination firewall

No stimulus wording, output schema, scoring anchor, model-facing prompt, model set, queue order, retry rule, or primary configuration may be changed after substantive pilot outputs have been inspected without creating a new version.

Exploratory changes after inspection must use a new version and remain analytically separate.

## Status

Protocol v0.1 is frozen before substantive model data collection.
