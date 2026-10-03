# Database Schema Notes

Full SQL is in 04_DATABASE_SCHEMA.sql.

## Relationships
- users 1-N transfers (as sender and as receiver)
- transfers 1-1 risk_alerts (only when flagged)
- risk_alerts 1-N review_actions
- agents 1-N agent_cash_daily
- users 1-N goals

## Tables
users, agents, goals, rate_history, transfers, risk_alerts, review_actions, agent_cash_daily, model_runs

## Notes
- review_actions.is_fraud_label is the feedback loop: analyst decisions become training labels.
- risk_alerts.model_version and model_runs make every score traceable.
- Use SQLite for the hackathon; the same schema runs on PostgreSQL.
