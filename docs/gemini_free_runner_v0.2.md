# Gemini Free-Tier Runner v0.2

This runner executes only the frozen `gemini_api_free` arm of the zero-cost v0.2 plan.

## Safety properties

- Dry run is the default behavior.
- Live execution requires both `--confirm-free-tier` and `GEMINI_FREE_TIER_CONFIRMED=YES`.
- The API key is read only from `GEMINI_API_KEY`; it is never written to the repository.
- The runner never enables billing, upgrades a project, or falls back to another model.
- A 429 / `RESOURCE_EXHAUSTED` response stops execution immediately.
- Substantive runs require an explicit `--max-items` between 1 and 20.
- Existing successful execution IDs are skipped, so collection is resumable.
- Frozen prompt, queue, dataset, system-set, and execution-plan fingerprints are checked before any call.
- Returned JSON is validated against the original frozen Draft 2020-12 schema.

## Provider schema adapter

Gemini structured output supports a subset of JSON Schema. The frozen research schema is **not modified**.
For the provider request only, the runner:

- removes the top-level `$schema` declaration;
- translates each `const: X` to `enum: [X]`.

The model response is then validated locally against the untouched frozen schema.

## Installation

Inside the active `intercultural-ai` Conda environment:

```bash
pip install -r requirements-gemini-free.txt
```

## Dry run

From either repository root:

```bash
python scripts/run_gemini_free_v0.2.py --dry-run
```

A passing dry run makes **zero API calls**.

## Live-use firewall

Before any live call, verify in Google AI Studio that the API key's project is on the **Free** tier.
Do not click **Set up billing** for this study.

Then, in the shell session only:

```bash
export GEMINI_API_KEY="YOUR_KEY_HERE"
export GEMINI_FREE_TIER_CONFIRMED=YES
```

Never commit the API key or put it into a tracked file.

## Synthetic smoke test

This makes one non-study structured-output request:

```bash
python scripts/run_gemini_free_v0.2.py \
  --smoke-test \
  --confirm-free-tier
```

## Substantive collection

Do not begin until the smoke test passes and the research freeze is confirmed.
Run in small resumable batches, for example:

```bash
python scripts/run_gemini_free_v0.2.py \
  --run \
  --confirm-free-tier \
  --max-items 10
```

The runner stores outputs under `results/runs/gemini_free_v0.2/`, which is already ignored by the repository's `results/runs/` Git rule.

## Pinned dependency

`google-genai==2.25.0` is pinned for the execution environment.
