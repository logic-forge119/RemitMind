-- RemitMind schema. Works on SQLite and PostgreSQL (use TEXT/INTEGER on SQLite).

CREATE TABLE users (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  role       TEXT NOT NULL CHECK (role IN ('sender','receiver','agent','analyst')),
  country    TEXT,
  language   TEXT DEFAULT 'bn',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agents (
  id           TEXT PRIMARY KEY,
  user_id      TEXT REFERENCES users(id),
  district     TEXT,
  cash_on_hand NUMERIC DEFAULT 0
);

CREATE TABLE goals (
  id          TEXT PRIMARY KEY,
  sender_id   TEXT REFERENCES users(id),
  receiver_id TEXT REFERENCES users(id),
  name        TEXT,      -- rent, school, savings
  share_pct   NUMERIC    -- 0-100
);

CREATE TABLE rate_history (
  id        INTEGER PRIMARY KEY,
  corridor  TEXT,        -- AED_BDT, USD_BDT, SAR_BDT
  rate_date DATE,
  rate      NUMERIC,
  fee_pct   NUMERIC
);

CREATE TABLE transfers (
  id          TEXT PRIMARY KEY,
  sender_id   TEXT REFERENCES users(id),
  receiver_id TEXT REFERENCES users(id),
  agent_id    TEXT REFERENCES agents(id),
  corridor    TEXT,
  amount_src  NUMERIC,
  amount_bdt  NUMERIC,
  fee_bdt     NUMERIC,
  device_id   TEXT,
  channel     TEXT,      -- app, agent, web
  status      TEXT,      -- created, in_review, completed, held, escalated
  risk_score  NUMERIC,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_transfers_sender   ON transfers(sender_id, created_at);
CREATE INDEX idx_transfers_receiver ON transfers(receiver_id, created_at);

CREATE TABLE risk_alerts (
  id               TEXT PRIMARY KEY,
  transfer_id      TEXT REFERENCES transfers(id),
  score            NUMERIC,
  reason_codes     TEXT,   -- JSON list e.g. ["NEW_RECEIVER","VELOCITY_3X"]
  explanation      TEXT,   -- LLM or template text
  suggested_action TEXT,
  status           TEXT DEFAULT 'open',
  model_version    TEXT,
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_actions (
  id             TEXT PRIMARY KEY,
  alert_id       TEXT REFERENCES risk_alerts(id),
  analyst_id     TEXT REFERENCES users(id),
  decision       TEXT CHECK (decision IN ('approve','hold','escalate')),
  note           TEXT,
  is_fraud_label INTEGER,  -- feedback label
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_cash_daily (
  id          INTEGER PRIMARY KEY,
  agent_id    TEXT REFERENCES agents(id),
  day         DATE,
  cashout_bdt NUMERIC,
  is_festival INTEGER DEFAULT 0
);

CREATE TABLE model_runs (
  id         INTEGER PRIMARY KEY,
  model_name TEXT,
  version    TEXT,
  metrics    TEXT,         -- JSON
  trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
