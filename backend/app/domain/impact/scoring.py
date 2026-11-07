from typing import Dict, Any


class ScoringEngine:
    DEFAULT_WEIGHTS = {
        "path_strength": 0.30,
        "proximity": 0.20,
        "criticality": 0.25,
        "verification_gap": 0.25,
    }

    @staticmethod
    def get_priority_band(score: int) -> str:
        if score >= 75:
            return "CRITICAL"
        elif score >= 55:
            return "HIGH"
        elif score >= 35:
            return "MEDIUM"
        else:
            return "LOW"

    @staticmethod
    def compute_score(
        path_strength: float,
        shortest_distance: int,
        criticality: int,
        test_status: str,  # "NONE", "FAILING", "STALE", "PASSING"
        custom_weights: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """
        Calculates the review-priority score and component breakdowns.
        """
        weights = custom_weights or ScoringEngine.DEFAULT_WEIGHTS
        w_d = weights.get("path_strength", 0.30)
        w_p = weights.get("proximity", 0.20)
        w_c = weights.get("criticality", 0.25)
        w_v = weights.get("verification_gap", 0.25)

        # 1. Proximity factor: 1 / distance
        dist = max(1, shortest_distance)
        p_factor = round(1.0 / dist, 4)

        # 2. Criticality factor: C / 5
        crit = max(1, min(5, criticality))
        c_factor = round(crit / 5.0, 4)

        # 3. Path strength factor: D
        d_factor = max(0.0, min(1.0, round(path_strength, 4)))

        # 4. Verification gap factor: V
        v_map = {
            "NONE": 1.00,
            "FAILING": 0.75,
            "STALE": 0.50,
            "PASSING": 0.10,
        }
        v_factor = v_map.get(test_status.upper(), 1.00)

        # Impact Priority Score
        raw_score = 100.0 * (
            (w_d * d_factor)
            + (w_p * p_factor)
            + (w_c * c_factor)
            + (w_v * v_factor)
        )
        final_score = max(0, min(100, round(raw_score)))
        band = ScoringEngine.get_priority_band(final_score)

        return {
            "path_strength_factor": d_factor,
            "proximity_factor": p_factor,
            "criticality_factor": c_factor,
            "verification_gap_factor": v_factor,
            "final_score": final_score,
            "priority_band": band,
            "weights_used": {
                "path_strength": w_d,
                "proximity": w_p,
                "criticality": w_c,
                "verification_gap": w_v,
            },
        }
