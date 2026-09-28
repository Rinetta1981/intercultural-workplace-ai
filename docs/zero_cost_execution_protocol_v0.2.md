# Zero-Cost Execution Protocol v0.2

## Purpose

This protocol supersedes the *execution* portion of v0.1 for actual data collection while preserving v0.1 unchanged for provenance.

The hard constraint is:

**Additional project expenditure = EUR 0.**

No paid API usage, purchased workspace credits, paid cloud compute, or automatic paid fallback is permitted.

## Systems

### 1. Gemini API Free Tier

- Vendor: Google
- Model: `gemini-3.8-flash`
- Interface: Gemini Developer API
- Tier: Free
- Thinking level: `low`
- Structured output: provider-native structured output
- Grounding/search/tools: disabled
- Replicates: 3 independent calls per condition

Before the first substantive call, the researcher must verify in Google AI Studio that the project is on the **Free** usage tier. Do not enable billing or upgrade the project for this study.

If a free-tier quota is exhausted, stop. Resume after the quota resets. Never switch the project to a paid tier to continue the study.

### 2. ChatGPT Business product replication

- Vendor: OpenAI
- Product: ChatGPT Business
- Model: GPT-5.6 Sol
- Reasoning setting: Medium
- Interface: ChatGPT web/desktop product, not OpenAI API
- Replicates: 3 independent chats per condition

Every observation must use a new **Temporary Chat** configured as **Unpersonalized**. This prevents use of memory, custom instructions, and plugins for personalization and prevents creation of new memories.

No web search, files, connectors, plugins, apps, GPTs, Projects, or other tools are used.

If the Business included allowance is exhausted, stop and wait for reset. Do not purchase or consume additional workspace credits for this study. If the product visibly falls back to another model, do not accept that response as a valid GPT-5.6 Sol observation.

## Comparability

The two conditions are intentionally described as **AI systems**, not as a controlled comparison of underlying model weights.

Gemini is observed through a developer API. GPT-5.6 Sol is observed through the ChatGPT Business product. Therefore:

- within-system directness and register effects are the primary target;
- replication of an effect across both systems strengthens generality;
- absolute system-level score differences are descriptive;
- cross-system differences must not be interpreted as pure model differences.

## Frozen stimuli and prompts

The existing frozen `pilot_v0.1` stimuli, evaluation rubrics, output schemas, and deterministic `evaluation_queue_v0.1.csv` remain unchanged.

No condition wording is altered for v0.2.

The same queue order is used within each system so that the systems encounter the same deterministically shuffled sequence.

## Planned observations

Per project:

- 10 scenario families
- 4 conditions per family
- 3 replicates
- 120 observations per system
- 2 systems
- 240 planned observations

Across both projects:

- 240 Gemini API calls
- 240 ChatGPT Business messages
- 480 total planned observations

## Technical failures

A technical failure includes:

- API/network error;
- free-tier quota error;
- invalid or empty output;
- schema-validation failure;
- visible model fallback;
- inability to verify the intended model/system configuration.

A technical failure is never assigned a substantive score.

Up to two retries are permitted using the same frozen prompt and configuration. Quota failures are not retried immediately; collection pauses until the quota resets.

## Zero-cost firewall

Execution must stop rather than spend money.

Specifically:

- do not enable paid Gemini API billing for this project;
- do not purchase ChatGPT workspace credits for this study;
- do not use paid OpenAI API access;
- do not use paid cloud compute;
- do not use a paid fallback model or endpoint;
- do not relax this rule to complete the dataset faster.

## Versioning

Any change to the systems, access mode, reasoning setting, replicate count, cost rule, prompt, rubric, or failure policy requires a new version.

Status: v0.2 is to be frozen before substantive data collection.
