from sqlalchemy import Column, String, Integer, Float, Numeric, Date, DateTime, ForeignKey, Text, Index
from sqlalchemy.sql import func
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'sender', 'receiver', 'agent', 'analyst'
    country = Column(String, nullable=True)
    language = Column(String, default="bn")
    is_quarantined = Column(Integer, default=0)
    quarantine_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    district = Column(String, nullable=True)
    cash_on_hand = Column(Float, default=0.0)

class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, index=True)
    sender_id = Column(String, ForeignKey("users.id"))
    receiver_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)  # rent, school, savings
    share_pct = Column(Float, nullable=False)  # 0-100

class RateHistory(Base):
    __tablename__ = "rate_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    corridor = Column(String, index=True)  # AED_BDT, USD_BDT, SAR_BDT, MYR_BDT, EUR_BDT
    rate_date = Column(Date, index=True)
    rate = Column(Float, nullable=False)
    fee_pct = Column(Float, nullable=False)

class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(String, primary_key=True, index=True)
    sender_id = Column(String, ForeignKey("users.id"), index=True)
    receiver_id = Column(String, ForeignKey("users.id"), index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    corridor = Column(String, nullable=False)
    amount_src = Column(Float, nullable=False)
    amount_bdt = Column(Float, nullable=False)
    fee_bdt = Column(Float, nullable=False)
    device_id = Column(String, nullable=True)
    channel = Column(String, default="app")  # app, agent, web
    status = Column(String, default="created")  # created, in_review, completed, held, escalated
    risk_score = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(String, primary_key=True, index=True)
    transfer_id = Column(String, ForeignKey("transfers.id"), unique=True)
    score = Column(Float, nullable=False)
    reason_codes = Column(Text, nullable=False)  # JSON string e.g. ["NEW_RECEIVER","VELOCITY_3X"]
    explanation = Column(Text, nullable=True)
    suggested_action = Column(String, default="hold")
    status = Column(String, default="open")  # open, closed
    model_version = Column(String, default="risk-v1.0")
    created_at = Column(DateTime, server_default=func.now())

class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(String, primary_key=True, index=True)
    alert_id = Column(String, ForeignKey("risk_alerts.id"))
    analyst_id = Column(String, ForeignKey("users.id"))
    decision = Column(String, nullable=False)  # approve, hold, escalate
    note = Column(Text, nullable=True)
    is_fraud_label = Column(Integer, nullable=True)  # feedback label: 0=legit, 1=fraud
    created_at = Column(DateTime, server_default=func.now())

class AgentCashDaily(Base):
    __tablename__ = "agent_cash_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    day = Column(Date, index=True)
    cashout_bdt = Column(Float, nullable=False)
    is_festival = Column(Integer, default=0)

class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    metrics = Column(Text, nullable=True)  # JSON string
    trained_at = Column(DateTime, server_default=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    actor_id = Column(String, nullable=False, index=True)
    details = Column(Text, nullable=True)  # JSON payload
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

# Hot query path performance indexes
Index("ix_transfers_sender_created", Transfer.sender_id, Transfer.created_at)
Index("ix_transfers_receiver_created", Transfer.receiver_id, Transfer.created_at)
Index("ix_risk_alerts_status_score", RiskAlert.status, RiskAlert.score)
Index("ix_audit_events_type_created", AuditEvent.event_type, AuditEvent.created_at)

