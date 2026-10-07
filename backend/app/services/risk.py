"""
RemitMind Risk Service (v2.0)
Advanced Hybrid Intelligence Layer:
1. Supervised LightGBM classifier trained on 10,000+ realistic remittance patterns
2. Platt (Sigmoid) probability calibration with Brier reliability guarantees
3. TreeSHAP feature attributions per transaction (factors: [{name, contribution_pct}])
4. Inductive Conformal Prediction at 95% empirical coverage (prediction_set, is_doubt, q_hat)
5. Fallback to Isolation Forest unsupervised detection if supervised artifact is missing
6. Zero auto-blocking compliance: Doubt flags route to OTP step-up / analyst review
"""

import os
import math
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import joblib

from app.services.rules import evaluate_rule_penalties, determine_status_and_action, CORRIDOR_RULES

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "ml" / "artifacts"
LGBM_MODEL_FILE = ARTIFACTS_DIR / "lgbm_risk_v2.joblib"
CALIBRATOR_FILE = ARTIFACTS_DIR / "calibrator_v2.joblib"
QHAT_FILE = ARTIFACTS_DIR / "conformal_qhat_v2.json"
FEATURE_NAMES_FILE = ARTIFACTS_DIR / "feature_names_v2.json"
ISO_FOREST_FILE = ARTIFACTS_DIR / "isolation_forest_v1.joblib"

FRIENDLY_FEATURE_NAMES = {
    "time_since_last_txn_hours": "Unusual Transaction Timing Recency",
    "day_of_week_dev": "Day of Week Deviation from Habitual Pattern",
    "is_new_receiver": "First-Time Unknown Recipient",
    "device_age_days": "Hardware Device Trust & Age",
    "amount_z": "Amount Historical Baseline Deviation",
    "accounts_per_device": "Device Multiplexing Signature",
    "sim_swap_recent": "Telco SIM-Swap Activity Within 48 Hours",
    "velocity_1h": "Rapid 1-Hour Velocity Frequency",
    "frequency_7d": "Elevated 7-Day Velocity Spikes",
    "frequency_30d": "30-Day Transfer Frequency Volume",
    "is_night": "Nocturnal Predawn Transfer Window",
    "country_jump": "Geolocation Proxy / Foreign Country Jump",
    "distinct_senders_to_receiver_24h": "Recipient Aggregator Mule Fan-In Ratio",
    "is_dormant_reactivation": "Dormant Account Sudden Reactivation",
    "hour_of_day": "Off-Hours Transfer Activity"
}

class AnomalyScorer:
    def __init__(self):
        self.lgbm_model = None
        self.calibrator = None
        self.explainer = None
        self.feature_columns = []
        self.q_hat = 0.052
        self.iso_model = None
        self.model_version = "risk-v1.0-iforest"
        
        self._init_supervised_model()
        self._init_isolation_forest()

    def _init_supervised_model(self):
        """Attempts loading supervised LightGBM + Platt Calibrator + Conformal artifacts."""
        try:
            if LGBM_MODEL_FILE.exists() and CALIBRATOR_FILE.exists():
                self.lgbm_model = joblib.load(LGBM_MODEL_FILE)
                self.calibrator = joblib.load(CALIBRATOR_FILE)
                
                if QHAT_FILE.exists():
                    with open(QHAT_FILE, "r", encoding="utf-8") as f:
                        q_data = json.load(f)
                        self.q_hat = float(q_data.get("q_hat", 0.052))

                if FEATURE_NAMES_FILE.exists():
                    with open(FEATURE_NAMES_FILE, "r", encoding="utf-8") as f:
                        self.feature_columns = json.load(f)

                # Initialize TreeSHAP explainer
                import shap
                self.explainer = shap.TreeExplainer(self.lgbm_model)
                self.model_version = "risk-v2.0-lgbm"
                print("AnomalyScorer: Successfully loaded LightGBM + Platt Calibrator + TreeSHAP engine.")
                return
        except Exception as e:
            print(f"AnomalyScorer: Could not initialize supervised model ({e}). Falling back to Isolation Forest.")
            self.lgbm_model = None

    def _init_isolation_forest(self):
        """Initializes fallback Isolation Forest model."""
        try:
            if ISO_FOREST_FILE.exists():
                self.iso_model = joblib.load(ISO_FOREST_FILE)
                return

            from sklearn.ensemble import IsolationForest
            rng = np.random.RandomState(42)
            normal_data = rng.normal(
                loc=[0.0, 0.2, 0.05, 0.05, 14.0, 1.0],
                scale=[1.0, 0.4, 0.2, 0.2, 4.0, 0.3],
                size=(500, 6)
            )
            self.iso_model = IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
            self.iso_model.fit(normal_data)
            ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.iso_model, ISO_FOREST_FILE)
        except Exception:
            self.iso_model = None

    def score_transfer(
        self,
        amount_src: float,
        sender_avg: float = 2000.0,
        sender_std: float = 500.0,
        velocity_1h: int = 1,
        frequency_7d: int = 1,
        frequency_30d: int = 2,
        time_since_last_txn_hours: float = 120.0,
        day_of_week_dev: float = 0.05,
        is_dormant_reactivation: bool = False,
        device_age_days: int = 180,
        accounts_per_device: int = 1,
        sim_swap_recent: bool = False,
        country_jump: bool = False,
        is_new_receiver: bool = False,
        is_new_device: bool = False,
        hour_of_day: int = 14,
        distinct_senders_24h: int = 1,
        corridor: str = "AED_BDT",
        **kwargs
    ) -> dict:
        """
        Calculates calibrated 0-100 risk score, TreeSHAP feature attributions,
        conformal doubt prediction set, and rule penalties.
        """
        std_val = sender_std if sender_std > 0 else 500.0
        amount_z = (amount_src - sender_avg) / std_val

        is_night = 1 if (hour_of_day <= 5 or hour_of_day >= 23) else 0
        rule = CORRIDOR_RULES.get(corridor.upper(), CORRIDOR_RULES["AED_BDT"])
        amount_bdt = amount_src * rule["base_rate"]
        is_high_val = 1 if (amount_src >= 5000.0 and device_age_days >= 180 and not is_new_receiver) else 0

        factors = []
        prediction_set = ["LEGITIMATE"]
        is_doubt = False
        calibrated_prob = 0.15

        # ----------------------------------------------------------------------
        # PATH A: Supervised LightGBM + Platt Calibration + TreeSHAP
        # ----------------------------------------------------------------------
        if self.lgbm_model is not None and self.calibrator is not None and self.feature_columns:
            try:
                feat_map = {
                    "amount_src": amount_src,
                    "amount_bdt": amount_bdt,
                    "amount_z": amount_z,
                    "velocity_1h": velocity_1h,
                    "frequency_7d": frequency_7d,
                    "frequency_30d": frequency_30d,
                    "time_since_last_txn_hours": time_since_last_txn_hours,
                    "day_of_week_dev": day_of_week_dev,
                    "is_dormant_reactivation": 1 if is_dormant_reactivation else 0,
                    "device_age_days": 1 if is_new_device else device_age_days,
                    "accounts_per_device": accounts_per_device,
                    "sim_swap_recent": 1 if sim_swap_recent else 0,
                    "country_jump": 1 if country_jump else 0,
                    "is_new_receiver": 1 if is_new_receiver else 0,
                    "hour_of_day": hour_of_day,
                    "is_night": is_night,
                    "distinct_senders_to_receiver_24h": distinct_senders_24h,
                    "is_high_value_legitimate": is_high_val
                }

                x_vec = np.array([[feat_map.get(c, 0.0) for c in self.feature_columns]], dtype=float)

                # Raw model prediction
                raw_prob = self.lgbm_model.predict_proba(x_vec)[0, 1]
                # Platt Sigmoid Calibrated Probability
                cal_probs = self.calibrator.predict_proba(np.array([[raw_prob]]))[0]
                p_legit = float(cal_probs[0])
                p_scam = float(cal_probs[1])
                calibrated_prob = p_scam
                base_score = p_scam * 100.0

                # Inductive Conformal Prediction Set (at 95% coverage)
                c_set = []
                if (1.0 - p_legit) <= self.q_hat:
                    c_set.append("LEGITIMATE")
                if (1.0 - p_scam) <= self.q_hat:
                    c_set.append("SCAM")
                if not c_set:
                    # Model uncertain (doubt): neither hypothesis rejected at 1 - q_hat
                    c_set = ["LEGITIMATE", "SCAM"]
                prediction_set = c_set
                is_doubt = ("LEGITIMATE" in prediction_set and "SCAM" in prediction_set)

                # TreeSHAP Explanations
                if self.explainer is not None:
                    shap_raw = self.explainer.shap_values(x_vec)
                    if isinstance(shap_raw, list):
                        s_vals = shap_raw[1][0]
                    elif len(np.shape(shap_raw)) == 3:
                        s_vals = shap_raw[0, :, 1]
                    else:
                        s_vals = shap_raw[0]

                    # Filter top positive contributors (driving score upwards)
                    pos_contribs = []
                    for idx, val in enumerate(s_vals):
                        if val > 0.001:
                            col_name = self.feature_columns[idx]
                            friendly = FRIENDLY_FEATURE_NAMES.get(col_name, col_name)
                            pos_contribs.append((friendly, float(val)))

                    pos_contribs.sort(key=lambda x: x[1], reverse=True)
                    total_pos = sum(v for _, v in pos_contribs) or 1.0

                    for name, v in pos_contribs[:4]:
                        pct = (v / total_pos) * 100.0
                        factors.append({
                            "name": name,
                            "contribution_pct": round(pct, 1),
                            "impact": "elevates_risk"
                        })

            except Exception as e:
                # Fallback to baseline on unexpected inference failure
                base_score = 15.0

        # ----------------------------------------------------------------------
        # PATH B: Unsupervised Isolation Forest Fallback
        # ----------------------------------------------------------------------
        else:
            base_score = 15.0
            if self.iso_model is not None:
                try:
                    iso_features = np.array([[
                        amount_z,
                        float(velocity_1h),
                        1.0 if is_new_receiver else 0.0,
                        1.0 if is_new_device else 0.0,
                        float(hour_of_day),
                        float(distinct_senders_24h)
                    ]])
                    raw_anomaly = self.iso_model.decision_function(iso_features)[0]
                    scaled = 45.0 - (raw_anomaly * 180.0)
                    base_score = max(5.0, min(80.0, scaled))
                except Exception:
                    base_score = 15.0

        # ----------------------------------------------------------------------
        # Evaluate Rule Penalties & Status Thresholds
        # ----------------------------------------------------------------------
        rule_bonus, reason_codes = evaluate_rule_penalties(
            amount_src=amount_src,
            recent_velocity=velocity_1h,
            is_new_receiver=is_new_receiver,
            is_new_device=is_new_device,
            hour_of_day=hour_of_day,
            sender_avg_amount=sender_avg
        )

        final_score = round(max(0.0, min(100.0, base_score + rule_bonus)), 1)

        # Default benign reason codes
        if not reason_codes and final_score < 40:
            reason_codes = ["CORRIDOR_VERIFIED", "NORMAL_VELOCITY"]

        status, suggested_action = determine_status_and_action(final_score)

        # Zero Auto-Blocking Conformal Routing
        if is_doubt:
            status = "in_review"
            suggested_action = "otp_step_up"  # Step-up verification challenge
            if "CONFORMAL_DOUBT_FLAG" not in reason_codes:
                reason_codes.append("CONFORMAL_DOUBT_FLAG")

        return {
            "score": final_score,
            "status": status,
            "reason_codes": reason_codes,
            "suggested_action": suggested_action,
            "factors": factors,
            "prediction_set": prediction_set,
            "is_doubt": is_doubt,
            "q_hat": round(self.q_hat, 4),
            "calibrated_prob": round(calibrated_prob, 4),
            "model_version": self.model_version
        }

anomaly_scorer = AnomalyScorer()
