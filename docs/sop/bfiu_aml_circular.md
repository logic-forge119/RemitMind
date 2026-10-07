# BFIU and AML Regulatory Standard Operating Procedures (SOP)
*Source Document for RemitMind Compliance Engine, BM25 Retrieval, and STR Evidence Grounding*
*Status: Repository Grounding Source per BFIU Circular & AML Directives*

---

## Section 1: Legal Mandate & Suspicious Transaction Reporting
### BFIU-SOP-SEC-25.1: Mandatory Suspicious Transaction Reporting (STR)
- **Reference**: Money Laundering Prevention Act (MLPA) 2012, Section 25(1)(c) & BFIU Circular No. 26.
- **Requirement**: Every Mobile Financial Services (MFS) provider, payment system operator, and scheduled bank must immediately furnish a Suspicious Transaction Report (STR / SAR) to the Bangladesh Financial Intelligence Unit (BFIU) upon detecting transactions that deviate unreasonably from customer economic profile, or where there is reasonable suspicion of involvement in illicit proceeds.
- **Evidence Standard**: The STR narrative must include specific unique transaction identifiers, detected deviation reason codes, and quantitative risk contribution factors.

---

## Section 2: Smurfing, Structuring & Threshold Evasion
### BFIU-SOP-STRUC-4.2: Smurfing and Cash Transaction Reporting (CTR) Evasion
- **Reference**: BFIU Master Circular on MFS Anti-Money Laundering Guidelines, Clause 4.2.
- **Indicator**: Multiple fund transfers conducted in rapid succession, or structured just below mandatory reporting thresholds (specifically clustering between BDT 45,000 and BDT 49,999 to circumvent the BDT 50,000 single-transaction scrutiny or daily aggregate limits).
- **Enforcement Action**: Any account exhibiting high near-threshold frequency (>15% of total inflow volume within the BDT 45,000-49,999 band) must be flagged for agent structuring investigation and temporary float disbursement holds.

---

## Section 3: Mule Account Networks & Rapid Velocity Pass-Through
### BFIU-SOP-MULE-5.1: Rapid Transit Accounts & Pass-Through Mule Velocity
- **Reference**: BFIU Directive on Digital Mule Syndicate Containment, Guideline 5.1.
- **Indicator**: Accounts characterized by immediate dispersal of inbound remittances within 15 minutes of receipt, high fan-in ratio (more than 4 distinct international senders remitting to a single domestic beneficiary within 24 hours), or high fan-out dispersal to cash-out agents.
- **Enforcement Action**: Place immediate administrative freeze on outbound liquidity; isolate linked cluster graph nodes; issue formal quarantine alert to BFIU within 24 hours.

---

## Section 4: Consumer Fraud, Coercion & Social Engineering Protection
### BFIU-SOP-COERCE-6.3: Victim Coercion, Impersonation and Advance-Fee Scams
- **Reference**: BFIU Consumer Protection & Fraud Mitigation Framework, Guideline 6.3.
- **Indicator**: Transactions accompanied by memos or communication strings referencing official regulatory clearance ("Bangladesh Bank fine", "BFIU clearance", "Tax penalty"), lottery disbursements, or urgent hostage/bail emergencies.
- **Enforcement Action**: Engage mandatory cooling-off delay (minimum 30 seconds) with bilingual advisories; require step-up authentication (OTP / biometric); prevent automated debit execution while consumer caution flags remain unresolved.

---

## Section 5: Agent Float Integrity & Nocturnal Liquidity Anomaly
### BFIU-SOP-AGENT-7.4: Agent Off-Hours Cash-Out & Liquidity Hoarding
- **Reference**: Payment Systems Department (PSD) Circular No. 04/2021 on MFS Agent Governance.
- **Indicator**: Cash-out to cash-in turnover ratio exceeding 4.0; nocturnal transaction concentration (>25% of turnover occurring between 00:00 and 06:00 BST); significant volume z-score deviation (>2.5 standard deviations) relative to district peer medians.
- **Enforcement Action**: Agent liquidity rebalancing audit; district territory officer dispatch inspection; restriction of nocturnal credit limits.
