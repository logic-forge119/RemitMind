# Synthetic Data Specification

| Entity | Volume | Notes |
|---|---|---|
| Senders | 200 | Corridors: UAE, Saudi, Malaysia, Italy |
| Receivers | 300 | Linked to 1-3 senders |
| Agents | 20 | Different districts |
| Transfers | 5,000 over 90 days | Monthly rhythm, bigger before Eid |
| Rate history | 90 days per corridor | Random walk with drift |
| Agent cash-outs | 90 days per agent | Weekly cycle plus festival spike |

## Injected patterns
- 3 mule rings: several senders to the same new receivers, short bursts, new devices.
- 2% account-takeover style transfers: new device, odd hour, large amount.
- Eid spike: cash-out demand about 2.5x for the 5 days before the festival.
- Rate trends so the forecaster can show savings.

## Rules
- Fixed random seed for reproducibility.
- Document every assumption in docs/data_assumptions.md.
- Never use real PII.
- Keep a clean test split that is never used for training.
