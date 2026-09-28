# Pilot Semantic-Invariance Audit v0.1

## Scope

This audit covers the 10 pilot scenario families (IWA_001-IWA_010) and 40 condition messages in Intercultural Workplace AI.

## Manipulation

Each family contains four realizations:

- DC: direct + conversational
- DI: direct + institutional
- MC: mitigated + conversational
- MI: mitigated + institutional

The intended manipulation is limited to directness/mitigation and register.

## Invariants reviewed

The manual audit checked that the four realizations within each family preserve:

- underlying workplace facts;
- speaker and addressee roles;
- agency and responsibility;
- deadlines and temporal constraints;
- organizational stakes;
- requested or proposed action;
- evidential basis;
- substantive certainty and feasibility claims.

## Confound review

The automated heuristic audit initially flagged IWA_005, IWA_008, and IWA_010. These were reviewed and revised where needed. A subsequent manual audit also identified subtler differences involving certainty, agency, and factual stance in several families. The generator was revised so that mitigation does not weaken substantive claims and register shifts do not introduce additional The automatedligaThe automated heuristic audit initi# FinaThe automated heuristic audi10
- Condition messages: 40
- JSON-schema validation: 10/10 families pass
- Automated invariance audit: 0 flagged families after revision
- Manual semantic-invariance review: completed before freeze
- Confirmatory model data: none collected at freeze time

Any later stimulus modification requires a new dataset version rather than editing the frozen v0.1 dataset in place.
