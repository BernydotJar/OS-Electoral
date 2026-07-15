# Antigua Guatemala Participation Baseline — 2023

Program: `C1-ELEC-2023-001`  
Review date: 2026-07-14  
Status: `PARTIAL_RESULTS_AVAILABLE_BALLOT_ACCOUNTING_BLOCKED`

## Current result

No participation percentage or ballot-accounting total is published in this artifact because the required official 2023 registered-electorate, ballots-cast, null-vote, blank-vote, and abstention inputs have not yet been authenticated and ingested.

EV-0112 now provides second-review-confirmed organization vote rows from the legal agreement's result table. These rows support the municipal result table, but they do not by themselves provide a turnout denominator or full ballot accounting.

## Required fields

| Metric | Required numerator | Required denominator | Official source status | Current value |
|---|---|---|---|---|
| Turnout | Ballots cast | Registered electorate for the same election and scope | Not authenticated | Unknown |
| Abstention | Registered electorate minus ballots cast | Registered electorate for the same election and scope | Not authenticated | Unknown |
| Valid-vote share | Valid votes | Ballots cast or total votes, according to official definition | Not authenticated | Unknown |
| Null-vote share | Null votes | Ballots cast or total votes, according to official definition | Not authenticated | Unknown |
| Blank-vote share | Blank votes | Ballots cast or total votes, according to official definition | Not authenticated | Unknown |
| Organization vote share | Verified organization votes | Verified valid votes | Partial: organization vote rows second-review confirmed from EV-0112; no printed valid-vote total captured | Unknown |

## Calculation policy

A calculated metric may be added only when:

1. numerator and denominator come from authenticated official records;
2. both values cover the same election, municipality, and ballot type;
3. the formula is written explicitly;
4. source records and verification status are retained;
5. rounding rules are documented.

## Prohibited substitution

The 2026 electoral-roll value in EV-0111 must not be used as the denominator for the 2023 election.

No media report, campaign claim, encyclopedia, social-media post, or estimated community value may fill the missing fields.

## Next evidence action

Authenticate and ingest the official 2023 municipal ballot-accounting record or dataset for Antigua Guatemala. Until then, this artifact remains blocked for turnout and no participation inference is permitted.
