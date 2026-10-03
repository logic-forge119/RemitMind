# App Flow

## Main flow (Rahim to Amina)
1. Sender screen: Rahim enters amount (AED), receiver, goal.
2. App calls POST /plans/recommend: best send day, fee, expected BDT, goal split.
3. Rahim taps Send: POST /transfers.
4. Backend runs rules, then the risk model, then saves the score.
5. Branch: score under 40 -> status completed; 40 or more -> status in_review and an alert is created.
6. Analyst screen: Nusrat sees the alert with reasons and explanation, picks approve / hold / escalate.
7. On approve the transfer becomes completed; the decision is saved as a feedback label.
8. Receiver screen: Amina sees the plain-language summary and split suggestion.
9. Agent panel: Karim sees 7-day demand forecast and top-up flag.

## Screens
| Screen | Key elements |
|---|---|
| Sender | Amount, currency, receiver picker, goal dropdown, plan card (best day, fee saved, split bar), Send button, status tracker |
| Receiver | BN/EN toggle, received amount, plain summary, split suggestion, cash-out tips |
| Agent panel | 7-day demand chart, cash-on-hand input, top-up warning |
| Analyst | Alert table by score, detail drawer (reason codes, explanation, linked wallets if time), approve/hold/escalate |

## Transfer states
created -> scored -> completed
created -> scored -> in_review -> completed | held | escalated
