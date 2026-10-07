"""
Policy Engine Service
Provides hot-reloadable YAML policy configuration, weight adjustments,
preset transitions, and audit-logging hooks.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "policy.yaml"

DEFAULT_POLICY = {
    "version": "1.0.0",
    "active_preset": "standard",
    "updated_at": "2026-10-07T00:00:00Z",
    "updated_by": "system",
    "weights": {
        "supervised_ml": 0.35,
        "behavioral_anomaly": 0.20,
        "velocity": 0.15,
        "device": 0.15,
        "graph_centrality": 0.10,
        "scamshield_coercion": 0.05
    },
    "thresholds": {
        "review_threshold": 45.0,
        "hold_threshold": 75.0,
        "conformal_alpha": 0.05,
        "cooling_off_seconds": 30
    },
    "presets": {
        "standard": {
            "name": "Standard Balanced Guard",
            "description": "Default calibrated baseline across all remittance corridors and regular daytime activity.",
            "weights": {
                "supervised_ml": 0.35,
                "behavioral_anomaly": 0.20,
                "velocity": 0.15,
                "device": 0.15,
                "graph_centrality": 0.10,
                "scamshield_coercion": 0.05
            },
            "thresholds": {
                "review_threshold": 45.0,
                "hold_threshold": 75.0
            }
        },
        "nocturnal_guard": {
            "name": "Nocturnal Guard (00:00 - 06:00 BST)",
            "description": "Heightened sensitivity for off-hours predawn transactions, device rotations, and rapid velocity.",
            "weights": {
                "supervised_ml": 0.25,
                "behavioral_anomaly": 0.15,
                "velocity": 0.25,
                "device": 0.25,
                "graph_centrality": 0.05,
                "scamshield_coercion": 0.05
            },
            "thresholds": {
                "review_threshold": 35.0,
                "hold_threshold": 65.0
            }
        },
        "mule_syndicate_strike": {
            "name": "Mule Syndicate Strike",
            "description": "Prioritizes community clustering, PageRank centrality, and multi-hop aggregator fan-in detection.",
            "weights": {
                "supervised_ml": 0.20,
                "behavioral_anomaly": 0.05,
                "velocity": 0.25,
                "device": 0.10,
                "graph_centrality": 0.35,
                "scamshield_coercion": 0.05
            },
            "thresholds": {
                "review_threshold": 40.0,
                "hold_threshold": 70.0
            }
        },
        "consumer_scam_alert": {
            "name": "Consumer Scam Alert",
            "description": "Targeted protection against advance-fee lottery traps, hospital emergencies, and regulator impersonation.",
            "weights": {
                "supervised_ml": 0.25,
                "behavioral_anomaly": 0.20,
                "velocity": 0.05,
                "device": 0.10,
                "graph_centrality": 0.10,
                "scamshield_coercion": 0.30
            },
            "thresholds": {
                "review_threshold": 35.0,
                "hold_threshold": 65.0
            }
        },
        "disaster_relief": {
            "name": "Disaster Relief Operational Mode",
            "description": "Relaxed velocity ceilings and heightened false-positive suppression during flood and cyclone emergencies.",
            "weights": {
                "supervised_ml": 0.40,
                "behavioral_anomaly": 0.10,
                "velocity": 0.10,
                "device": 0.10,
                "graph_centrality": 0.15,
                "scamshield_coercion": 0.15
            },
            "thresholds": {
                "review_threshold": 55.0,
                "hold_threshold": 85.0
            }
        }
    }
}

class PolicyEngine:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self._policy_data: Dict[str, Any] = {}
        self._last_mtime: float = 0.0
        self.reload()

    def reload(self) -> None:
        """Loads or reloads configuration from policy.yaml."""
        try:
            if self.config_path.exists():
                mtime = os.path.getmtime(self.config_path)
                if mtime > self._last_mtime or not self._policy_data:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        loaded = yaml.safe_load(f)
                        if isinstance(loaded, dict) and "weights" in loaded:
                            self._policy_data = loaded
                            self._last_mtime = mtime
            else:
                self._policy_data = DEFAULT_POLICY.copy()
        except Exception as e:
            if not self._policy_data:
                self._policy_data = DEFAULT_POLICY.copy()

    def get_policy(self) -> Dict[str, Any]:
        """Returns hot-reloaded active policy configuration."""
        self.reload()
        return self._policy_data

    def get_weights(self) -> Dict[str, float]:
        """Returns normalized active weights."""
        policy = self.get_policy()
        return policy.get("weights", DEFAULT_POLICY["weights"])

    def get_thresholds(self) -> Dict[str, float]:
        """Returns active risk thresholds."""
        policy = self.get_policy()
        return policy.get("thresholds", DEFAULT_POLICY["thresholds"])

    def update_policy(
        self,
        new_weights: Optional[Dict[str, float]] = None,
        preset_name: Optional[str] = None,
        new_thresholds: Optional[Dict[str, float]] = None,
        actor_id: str = "admin"
    ) -> Dict[str, Any]:
        """
        Updates policy configuration, validates normalized weights,
        writes changes back to policy.yaml, and returns diff summary.
        """
        self.reload()
        old_state = {
            "active_preset": self._policy_data.get("active_preset"),
            "weights": dict(self._policy_data.get("weights", {})),
            "thresholds": dict(self._policy_data.get("thresholds", {}))
        }

        presets = self._policy_data.get("presets", DEFAULT_POLICY["presets"])

        if preset_name:
            if preset_name not in presets:
                raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(presets.keys())}")
            preset_cfg = presets[preset_name]
            self._policy_data["active_preset"] = preset_name
            self._policy_data["weights"] = dict(preset_cfg["weights"])
            if "thresholds" in preset_cfg:
                self._policy_data["thresholds"].update(preset_cfg["thresholds"])
        else:
            self._policy_data["active_preset"] = "custom"

        if new_weights:
            # Validate and normalize
            current_w = dict(self._policy_data.get("weights", {}))
            current_w.update(new_weights)
            total = sum(current_w.values())
            if total > 0:
                normalized = {k: round(v / total, 4) for k, v in current_w.items()}
                self._policy_data["weights"] = normalized

        if new_thresholds:
            self._policy_data["thresholds"].update(new_thresholds)

        from datetime import datetime, timezone
        self._policy_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._policy_data["updated_by"] = actor_id

        # Write out to YAML
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._policy_data, f, sort_keys=False)

        self._last_mtime = os.path.getmtime(self.config_path)

        new_state = {
            "active_preset": self._policy_data.get("active_preset"),
            "weights": dict(self._policy_data.get("weights", {})),
            "thresholds": dict(self._policy_data.get("thresholds", {}))
        }

        return {
            "before": old_state,
            "after": new_state,
            "updated_at": self._policy_data["updated_at"],
            "updated_by": actor_id
        }

policy_engine = PolicyEngine()
