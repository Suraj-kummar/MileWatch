"""
MileWatch — SHAP-Based Explainability & Reason Generation

WHY SHAP (NOT just feature importance):
- Global feature importance tells you "GPS distance matters overall."
- SHAP tells you "for THIS specific attempt, GPS distance contributed -0.15
  to the credibility score because the exec was 3.2km away."
- Per-prediction explanations are what make this product useful:
  an ops manager needs to know WHY a specific attempt is suspicious.

HOW IT WORKS:
1. SHAP (SHapley Additive exPlanations) computes each feature's contribution
   to moving the prediction away from the average.
2. We take the SHAP values and map them to human-readable reason strings.
3. We sort by absolute impact and return the top reasons.

USAGE:
    # As a module (used by Flask service):
    from explainer import ReasonExplainer
    explainer = ReasonExplainer(model, preprocessor)
    reasons = explainer.explain(raw_features)

    # Standalone test:
    python explainer.py
"""

import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

import joblib
import numpy as np
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent))
from features import ALL_FEATURES, CONTINUOUS_FEATURES, PASSTHROUGH_FEATURES, transform_single


@dataclass
class Reason:
    """
    A single human-readable reason explaining a credibility score factor.

    Attributes:
        feature: Raw feature name (e.g., 'gps_distance_m')
        feature_label: Human-readable feature name (e.g., 'GPS Distance')
        direction: 'positive' (increases credibility) or 'negative' (decreases it)
        impact: Absolute SHAP value (magnitude of contribution)
        raw_value: The actual feature value for this attempt
        description: Human-readable explanation string
    """
    feature: str
    feature_label: str
    direction: str
    impact: float
    raw_value: float
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


# ── Human-readable reason templates ────────────────────────────────────

FEATURE_LABELS = {
    "gps_distance_m": "GPS Distance",
    "time_gap_minutes": "Time Gap",
    "call_made": "Call to Customer",
    "is_cod": "Payment Method",
    "exec_historical_fake_rate": "Executive History",
    "minutes_to_shift_end": "Shift Timing",
    "pincode_tier": "Location Tier",
}


def _format_reason(feature: str, raw_value: float, shap_value: float) -> str:
    """
    Generate a human-readable reason string for a specific feature's SHAP contribution.

    Positive SHAP = pushes score UP (more credible)
    Negative SHAP = pushes score DOWN (less credible)
    """
    is_negative = shap_value < 0  # Negative = reduces credibility

    if feature == "gps_distance_m":
        dist_km = raw_value / 1000
        if is_negative:
            if raw_value > 3000:
                return f"Executive was {dist_km:.1f} km away from delivery address (very far)"
            elif raw_value > 1500:
                return f"Executive was {dist_km:.1f} km away from delivery address (suspicious distance)"
            else:
                return f"Executive was {raw_value:.0f}m away from delivery address (moderately far)"
        else:
            return f"Executive was only {raw_value:.0f}m from delivery address (close proximity)"

    elif feature == "time_gap_minutes":
        if is_negative:
            if raw_value < 10:
                return f"Only {raw_value:.0f} min between out-for-delivery and attempt mark (suspiciously fast)"
            elif raw_value > 60:
                return f"{raw_value:.0f} min gap is unusually long"
            else:
                return f"Time gap of {raw_value:.0f} min is outside normal range"
        else:
            return f"Time gap of {raw_value:.0f} min is consistent with a genuine attempt"

    elif feature == "call_made":
        if raw_value == 0:
            return "No call was made to customer before marking attempt"
        else:
            return "Customer was called before marking the attempt"

    elif feature == "is_cod":
        if raw_value == 1 and is_negative:
            return "Cash on Delivery order (higher incentive to skip)"
        elif raw_value == 1:
            return "COD order but other signals suggest genuine attempt"
        else:
            return "Prepaid order (lower incentive to fake attempt)"

    elif feature == "exec_historical_fake_rate":
        pct = raw_value * 100
        if is_negative:
            if raw_value > 0.25:
                return f"Executive has {pct:.0f}% historical suspicious rate (high risk)"
            else:
                return f"Executive has {pct:.0f}% historical suspicious rate (elevated)"
        else:
            return f"Executive has only {pct:.0f}% historical suspicious rate (clean record)"

    elif feature == "minutes_to_shift_end":
        if is_negative:
            if raw_value < 15:
                return f"Attempt marked {raw_value:.0f} min before shift end (end-of-shift pattern)"
            elif raw_value < 30:
                return f"Attempt marked {raw_value:.0f} min before shift end (near shift end)"
            else:
                return f"Shift timing raises minor concern"
        else:
            return f"Attempt marked with {raw_value:.0f} min remaining in shift (no rush)"

    elif feature == "pincode_tier":
        tier_names = {1: "Metro", 2: "Tier-2", 3: "Tier-3"}
        tier_name = tier_names.get(int(raw_value), f"Tier-{int(raw_value)}")
        if is_negative:
            return f"{tier_name} area (limited delivery infrastructure)"
        else:
            return f"{tier_name} area (good delivery infrastructure)"

    return f"{FEATURE_LABELS.get(feature, feature)}: value={raw_value}"


class ReasonExplainer:
    """
    Generates per-prediction SHAP-based explanations.

    Uses XGBoost's built-in predict method with output_margin for tree-based
    SHAP computation, which is exact (not approximate) and fast.
    """

    def __init__(self, model: xgb.XGBRegressor, preprocessor=None):
        """
        Args:
            model: Trained XGBoost model
            preprocessor: Fitted ColumnTransformer for feature scaling
        """
        self.model = model
        self.preprocessor = preprocessor
        # Get the underlying Booster for SHAP predictions
        self.booster = model.get_booster()

    def _get_shap_values(self, X_scaled: np.ndarray) -> np.ndarray:
        """
        Compute SHAP values using XGBoost's native tree SHAP implementation.

        Returns array of shape (n_samples, n_features) with SHAP values.
        """
        dmatrix = xgb.DMatrix(X_scaled, feature_names=ALL_FEATURES)
        # XGBoost's native predict with pred_contribs returns SHAP values
        # Shape: (n_samples, n_features + 1) where last column is bias term
        shap_values = self.booster.predict(dmatrix, pred_contribs=True)
        # Drop the bias column
        return shap_values[:, :-1]

    def explain(
        self,
        raw_features: dict,
        top_k: int = 5,
    ) -> List[Reason]:
        """
        Generate human-readable reasons for a single prediction.

        Args:
            raw_features: Dict with keys matching ALL_FEATURES
            top_k: Number of top reasons to return (sorted by impact)

        Returns:
            List of Reason objects, sorted by absolute impact (highest first)
        """
        # Scale features
        X_scaled = transform_single(raw_features, self.preprocessor)

        # Get SHAP values
        shap_values = self._get_shap_values(X_scaled)
        shap_row = shap_values[0]  # Single prediction

        # Build reasons
        reasons = []
        for i, feature in enumerate(ALL_FEATURES):
            shap_val = float(shap_row[i])
            raw_val = float(raw_features[feature])

            reason = Reason(
                feature=feature,
                feature_label=FEATURE_LABELS.get(feature, feature),
                direction="positive" if shap_val >= 0 else "negative",
                impact=abs(shap_val),
                raw_value=raw_val,
                description=_format_reason(feature, raw_val, shap_val),
            )
            reasons.append(reason)

        # Sort by absolute impact, return top_k
        reasons.sort(key=lambda r: r.impact, reverse=True)
        return reasons[:top_k]

    def explain_batch(
        self,
        raw_features_list: list,
        top_k: int = 5,
    ) -> List[List[Reason]]:
        """Explain multiple predictions at once."""
        return [self.explain(feat, top_k) for feat in raw_features_list]


def load_explainer(
    model_path: str = None,
    scaler_path: str = None,
) -> ReasonExplainer:
    """
    Load a ReasonExplainer from saved model artifacts.

    Used by the Flask service at startup.
    """
    artifacts_dir = Path(__file__).parent / "artifacts"

    if model_path is None:
        model_path = str(artifacts_dir / "xgb_model.json")
    if scaler_path is None:
        scaler_path = str(artifacts_dir / "feature_scaler.pkl")

    model = xgb.XGBRegressor()
    model.load_model(model_path)

    preprocessor = joblib.load(scaler_path)

    return ReasonExplainer(model, preprocessor)


if __name__ == "__main__":
    # Quick test: load model and explain a sample prediction
    print("=" * 60)
    print("MileWatch - Explainability Test")
    print("=" * 60)

    try:
        explainer = load_explainer()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Run train.py first to generate model artifacts.")
        sys.exit(1)

    # Test with a suspicious-looking attempt
    suspicious_attempt = {
        "gps_distance_m": 3200.0,
        "time_gap_minutes": 8.0,
        "call_made": 0,
        "is_cod": 1,
        "exec_historical_fake_rate": 0.28,
        "minutes_to_shift_end": 12.0,
        "pincode_tier": 2,
    }

    print("\nTest Case 1: Suspicious Attempt")
    print(f"  Input: {suspicious_attempt}")

    # Get prediction
    X_scaled = transform_single(suspicious_attempt, explainer.preprocessor)
    score = float(explainer.model.predict(X_scaled)[0])
    print(f"  Credibility Score: {score:.4f}")

    reasons = explainer.explain(suspicious_attempt, top_k=5)
    print("\n  Top Reasons:")
    for i, reason in enumerate(reasons, 1):
        arrow = "^" if reason.direction == "positive" else "v"
        print(f"    {i}. [{arrow}] {reason.description} (impact: {reason.impact:.4f})")

    # Test with a genuine-looking attempt
    genuine_attempt = {
        "gps_distance_m": 120.0,
        "time_gap_minutes": 38.0,
        "call_made": 1,
        "is_cod": 0,
        "exec_historical_fake_rate": 0.03,
        "minutes_to_shift_end": 240.0,
        "pincode_tier": 1,
    }

    print("\n\nTest Case 2: Genuine Attempt")
    print(f"  Input: {genuine_attempt}")

    X_scaled = transform_single(genuine_attempt, explainer.preprocessor)
    score = float(explainer.model.predict(X_scaled)[0])
    print(f"  Credibility Score: {score:.4f}")

    reasons = explainer.explain(genuine_attempt, top_k=5)
    print("\n  Top Reasons:")
    for i, reason in enumerate(reasons, 1):
        arrow = "^" if reason.direction == "positive" else "v"
        print(f"    {i}. [{arrow}] {reason.description} (impact: {reason.impact:.4f})")

    print("\n" + "=" * 60)
    print("Phase 2D: Explainability test complete.")
    print("=" * 60)
