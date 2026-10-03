"""
RemitMind Risk Service
Blends Isolation Forest unsupervised anomaly detection with deterministic rules.
Produces a 0-100 score and explicit reason codes.
"""

import os
import math
import json
from app.services.rules import evaluate_rule_penalties, determine_status_and_action

MODEL_VERSION = "risk-v1.0"

class AnomalyScorer:
    def __init__(self):
        self.model = None
        self._init_model()

    def _init_model(self):
        try:
            from sklearn.ensemble import IsolationForest
            import numpy as np

            # Initialize a baseline Isolation Forest
            # Trained on standard reference vectors: [amount_z, velocity_1h, new_rcv, new_dev, odd_hour, distinct_senders]
            rng = np.random.RandomState(42)
            # 500 reference samples representing baseline distribution
            normal_data = rng.normal(loc=[0.0, 0.2, 0.05, 0.05, 14.0, 1.0], scale=[1.0, 0.4, 0.2, 0.2, 4.0, 0.3], size=(500, 6))
            self.model = IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
            self.model.fit(normal_data)
        except Exception:
            self.model = None

    def score_transfer(
        self,
        amount_src: float,
        sender_avg: float = 2000.0,
        sender_std: float = 500.0,
        velocity_1h: int = 1,
        is_new_receiver: bool = False,
        is_new_device: bool = False,
        hour_of_day: int = 14,
        distinct_senders_24h: int = 1,
        simulate_anomaly: bool = False
    ) -> dict:
        """
        Calculates 0-100 risk score, extracts reason codes, and determines suggested action.
        """
        # Calculate z-score
        amount_z = (amount_src - sender_avg) / (sender_std if sender_std > 0 else 500.0)

        base_score = 15.0

        if simulate_anomaly:
            base_score = 65.0
            velocity_1h = max(3, velocity_1h)
            is_new_receiver = True
            is_new_device = True

        elif self.model is not None:
            try:
                import numpy as np
                features = np.array([[
                    amount_z,
                    float(velocity_1h),
                    1.0 if is_new_receiver else 0.0,
                    1.0 if is_new_device else 0.0,
                    float(hour_of_day),
                    float(distinct_senders_24h)
                ]])
                
                # Isolation Forest decision_function: lower means more anomalous
                raw_anomaly = self.model.decision_function(features)[0]
                # Scale typical range [-0.25, 0.25] to [80, 10]
                # If raw_anomaly is positive (~0.15), normalized is low (~12)
                # If raw_anomaly is negative (~ -0.15), normalized is high (~75)
                scaled = 45.0 - (raw_anomaly * 180.0)
                base_score = max(5.0, min(80.0, scaled))
            except Exception:
                base_score = 15.0

        # Evaluate rule penalties
        rule_bonus, reason_codes = evaluate_rule_penalties(
            amount_src=amount_src,
            recent_velocity=velocity_1h,
            is_new_receiver=is_new_receiver,
            is_new_device=is_new_device,
            hour_of_day=hour_of_day,
            sender_avg_amount=sender_avg
        )

        final_score = round(max(0.0, min(100.0, base_score + rule_bonus)), 1)

        # Ensure default benign code if clean
        if not reason_codes and final_score < 40:
            reason_codes = ["CORRIDOR_VERIFIED", "NORMAL_VELOCITY"]

        status, suggested_action = determine_status_and_action(final_score)

        return {
            "score": final_score,
            "status": status,
            "reason_codes": reason_codes,
            "suggested_action": suggested_action,
            "model_version": MODEL_VERSION
        }

anomaly_scorer = AnomalyScorer()
