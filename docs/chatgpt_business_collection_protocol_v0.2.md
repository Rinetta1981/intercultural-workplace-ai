# ChatGPT Business Collection Protocol v0.2

## One observation = one independent Temporary Chat

For each assigned queue row:

1. Confirm you are inside the intended ChatGPT Business workspace.
2. Start a new **Temporary Chat**.
3. Choose **Unpersonalized** before sending the first message.
4. Select **GPT-5.6 Sol** and set reasoning to **Medium**.
5. Confirm web search/tools/connectors are not being used.
6. Paste the fully rendered frozen model prompt for that queue row.
7. Send exactly one research prompt.
8. Copy the complete response verbatim into the raw-results record for that execution ID.
9. Record the visible model/reasoning setting and collection timestamp.
10. Close the Temporary Chat; do not continue it with another stimulus.

## Validity rules

A response is valid only if:

- GPT-5.6 Sol / Medium was selected;
- the chat was Temporary + Unpersonalized;
- there was no prior research stimulus in the conversation;
- no tool, search, file, connector, or plugin was used;
- no visible model fallback occurred;
- the output can be parsed and validated against the frozen project schema.

If any condition fails, mark the attempt as technical/collection failure and do not score it manually.

## Cost rule

Use only included Business Chat usage.

If the included allowance is exhausted:

**stop collection and wait for the allowance to reset.**

Do not purchase credits, enable auto-reload for this study, or move the observations to the OpenAI API.

## Reproducibility note

ChatGPT is a deployed product, so its hidden system layer and product configuration are not under researcher control. Record:

- date and local time;
- workspace type;
- displayed model;
- displayed reasoning level;
- temporary/unpersonalized status;
- any product notice or fallback message.

This limitation must be reported in the paper and README.
