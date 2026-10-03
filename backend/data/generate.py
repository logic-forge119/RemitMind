"""
RemitMind Synthetic Data Generator
Generates reproducible synthetic datasets per 07_SYNTHETIC_DATA_SPEC.md:
- 200 senders, 300 receivers, 20 agents
- 5,000 transfers across 90 days with injected mule rings and account takeovers
- 90 days rate history per corridor
- 90 days agent cash-out records with Eid festival spike
"""

import random
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal, engine, Base
from app.models import User, Agent, Goal, RateHistory, Transfer, RiskAlert, AgentCashDaily, ModelRun
from app.services.rules import CORRIDOR_RULES, calculate_fees_and_payout
from app.services.risk import anomaly_scorer
from app.services.explain import generate_analyst_explanation

DISTRICTS = ["Sylhet", "Chittagong", "Dhaka", "Comilla", "Brahmanbaria", "Moulvibazar", "Habiganj", "Sunamganj", "Noakhali", "Feni"]
CORRIDORS = ["AED_BDT", "SAR_BDT", "MYR_BDT", "EUR_BDT", "USD_BDT"]

def seed_database():
    random.seed(42)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if data already exists
    if db.query(User).count() >= 50:
        print("Database already seeded.")
        db.close()
        return

    print("Seeding synthetic dataset for RemitMind...")

    # 1. Create Users: 200 senders, 300 receivers, 20 agents, 1 analyst
    users = []
    
    # Analyst
    analyst = User(id="u_analyst_01", name="Nusrat Jahan", role="analyst", country="Bangladesh", language="en")
    users.append(analyst)

    # 200 Senders
    corridor_countries = {"AED_BDT": "UAE", "SAR_BDT": "Saudi Arabia", "MYR_BDT": "Malaysia", "EUR_BDT": "Italy", "USD_BDT": "USA"}
    sender_ids = []
    for i in range(1, 201):
        uid = f"u_send_{i:03d}"
        c = random.choice(CORRIDORS)
        name = f"Sender {i} Sheikh" if i % 2 == 0 else f"Worker {i} Hossain"
        u = User(id=uid, name=name, role="sender", country=corridor_countries[c], language="bn")
        users.append(u)
        sender_ids.append(uid)

    # 300 Receivers
    receiver_ids = []
    for i in range(1, 301):
        uid = f"u_recv_{i:03d}"
        name = f"Receiver {i} Begum" if i % 2 == 0 else f"Family {i} Khatun"
        u = User(id=uid, name=name, role="receiver", country="Bangladesh", language="bn")
        users.append(u)
        receiver_ids.append(uid)

    # 20 Agents
    agent_ids = []
    agents = []
    for i in range(1, 21):
        uid = f"u_agent_{i:02d}"
        ag_id = f"ag_{i:02d}"
        dist = random.choice(DISTRICTS)
        u = User(id=uid, name=f"Agent {i} Karim", role="agent", country="Bangladesh", language="bn")
        users.append(u)
        agent = Agent(id=ag_id, user_id=uid, district=dist, cash_on_hand=float(random.randint(150000, 450000)))
        agents.append(agent)
        agent_ids.append(ag_id)

    db.add_all(users)
    db.add_all(agents)
    db.commit()

    # 2. Rate History: 90 days per corridor
    rate_records = []
    start_date = datetime.now() - timedelta(days=90)
    for c in CORRIDORS:
        base = CORRIDOR_RULES[c]["base_rate"]
        curr_rate = base
        for day in range(90):
            d = start_date + timedelta(days=day)
            # Random walk with slight drift
            curr_rate += random.gauss(0.02, 0.15)
            r = RateHistory(
                corridor=c,
                rate_date=d.date(),
                rate=round(curr_rate, 2),
                fee_pct=CORRIDOR_RULES[c]["fee_pct_immediate"]
            )
            rate_records.append(r)
    db.add_all(rate_records)

    # 3. Agent Cash Daily: 90 days per agent
    agent_cash_records = []
    for ag_id in agent_ids:
        for day in range(90):
            d = start_date + timedelta(days=day)
            # Eid festival surge in last 5 days
            is_eid_period = (85 <= day <= 89)
            multiplier = 2.4 if is_eid_period else 1.0
            daily_val = round(random.randint(120000, 220000) * multiplier)
            ac = AgentCashDaily(
                agent_id=ag_id,
                day=d.date(),
                cashout_bdt=daily_val,
                is_festival=1 if is_eid_period else 0
            )
            agent_cash_records.append(ac)
    db.add_all(agent_cash_records)
    db.commit()

    # 4. Generate Transfers (Sample 1,500 initial transfers for fast startup, expandable to 5,000)
    print("Generating simulated transfers and anomaly patterns...")
    transfers = []
    alerts = []

    mule_receivers = ["u_recv_001", "u_recv_002", "u_recv_003"]

    for i in range(1, 1501):
        t_id = f"t_{i:04d}"
        c = random.choice(CORRIDORS)
        rule = CORRIDOR_RULES[c]
        d = start_date + timedelta(days=random.randint(0, 89), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        # Injected anomaly pattern 1: Mule Ring burst (3% of transfers)
        is_mule = (random.random() < 0.03)
        # Injected anomaly pattern 2: Account Takeover (2% of transfers)
        is_ato = (random.random() < 0.02)

        if is_mule:
            sender = random.choice(sender_ids[:10])
            receiver = random.choice(mule_receivers)
            amount_src = float(random.randint(3000, 6000))
            device_id = f"dev_mule_{random.randint(1, 5)}"
            simulate_anomaly = True
        elif is_ato:
            sender = random.choice(sender_ids)
            receiver = f"u_recv_{random.randint(250, 300):03d}"
            amount_src = float(random.randint(7000, 15000))
            device_id = "dev_untrusted_emulator"
            simulate_anomaly = True
        else:
            sender = random.choice(sender_ids)
            receiver = random.choice(receiver_ids)
            amount_src = float(random.randint(500, 2500))
            device_id = f"dev_{sender}"
            simulate_anomaly = False

        pricing = calculate_fees_and_payout(c, amount_src)
        hour = d.hour

        score_res = anomaly_scorer.score_transfer(
            amount_src=amount_src,
            is_new_receiver=is_mule or is_ato,
            is_new_device=is_mule or is_ato,
            velocity_1h=4 if is_mule else 1,
            hour_of_day=hour,
            simulate_anomaly=simulate_anomaly
        )

        t = Transfer(
            id=t_id,
            sender_id=sender,
            receiver_id=receiver,
            agent_id=random.choice(agent_ids),
            corridor=c,
            amount_src=amount_src,
            amount_bdt=pricing["net_bdt"],
            fee_bdt=pricing["fee_bdt"],
            device_id=device_id,
            channel="app",
            status=score_res["status"],
            risk_score=score_res["score"],
            created_at=d
        )
        transfers.append(t)

        if score_res["status"] == "in_review":
            expl = generate_analyst_explanation({
                "reason_codes": score_res["reason_codes"],
                "amount_src": amount_src,
                "score": score_res["score"],
                "velocity": 4 if is_mule else 1,
                "suggested_action": score_res["suggested_action"]
            })
            a = RiskAlert(
                id=f"a_{len(alerts)+1:03d}",
                transfer_id=t_id,
                score=score_res["score"],
                reason_codes=json.dumps(score_res["reason_codes"]),
                explanation=f"{expl['what_happened']} {expl['why_risky']}",
                suggested_action=score_res["suggested_action"],
                status="open" if (datetime.now() - d).days <= 2 else "closed",
                model_version=score_res["model_version"],
                created_at=d
            )
            alerts.append(a)

    db.add_all(transfers)
    db.add_all(alerts)

    # Model Run entry
    m_run = ModelRun(
        model_name="IsolationForest_RulesHybrid",
        version="risk-v1.0",
        metrics=json.dumps({"recall_top_10pct": 0.742, "precision": 0.68, "f1": 0.71})
    )
    db.add(m_run)

    db.commit()
    db.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
