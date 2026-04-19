"""
MileWatch — Prediction Service

WHY THIS FILE EXISTS:
This is the core orchestration layer between the Flask API and the ML model.
It handles:
1. Loading the trained model + scaler + explainer at startup (NOT per-request)
2. Running predictions on validated feature inputs
3. Generating SHAP-based reason explanations
4. Determining risk levels from continuous scores
5. Coordinating with the dispute generator for auto-drafted dispute text

DESIGN DECISION: Model loading is done ONCE at startup. If the model files
change, the service must be restarted. This avoids the overhead of loading
a ~1MB model file on every request and ensures consistent predictions within
a deployment.

PERFORMANCE TARGET: < 100ms per single prediction (model + SHAP + reasons).
XGBoost's native tree SHAP is O(TLD) where T=trees, L=leaves, D=depth,
which is ~1-5ms for our model. The bottleneck is SHAP, not prediction.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np

# Add parent dirs to path so we can import model modules
sys.path.insert(0, str(Path(__file__).parent.parent / "model"))

from features import ALL_FEATURES, transform_single
from explainer import ReasonExplainer, load_explainer, Reason

logger = logging.getLogger(__name__)


# ── Risk level thresholds ──────────────────────────────────────────────
# These thresholds are based on Phase 2C threshold analysis.
# LOW = likely fake, MEDIUM = needs review, HIGH = likely genuine

RISK_THRESHOLDS = {
    "HIGH_RISK": (0.0, 0.30),       # Score 0.0 - 0.30 → High risk (likely fake)
    "MEDIUM_RISK": (0.30, 0.60),    # Score 0.30 - 0.60 → Medium risk (needs review)
    "LOW_RISK": (0.60, 1.0),        # Score 0.60 - 1.0 → Low risk (likely genuine)
}


def classify_risk(score: float) -> str:
    """
    Convert continuous credibility score to risk level category.

    WHY RISK LEVELS:
    Continuous scores are precise but hard to act on. An ops manager doesn't
    want to decide what 0.47 means — they want to see "MEDIUM_RISK" and know
    it needs a second look.
    """
    score = np.clip(score, 0.0, 1.0)

    if score < 0.30:
        return "HIGH_RISK"
    elif score < 0.60:
        return "MEDIUM_RISK"
    else:
        return "LOW_RISK"


class PredictionService:
    """
    Central prediction orchestrator.

    Loads model artifacts once at initialization and provides
    predict() and predict_batch() methods for the Flask API.
    """

    def __init__(
        self,
        model_path: str = None,
        scaler_path: str = None,
    ):
        """
        Initialize the prediction service by loading model artifacts.

        Args:
            model_path: Path to xgb_model.json. Defaults to model/artifacts/
            scaler_path: Path to feature_scaler.pkl. Defaults to model/artifacts/
        """
        logger.info("Initializing PredictionService...")
        start = time.time()

        # Load the explainer (which includes the model and preprocessor)
        self.explainer = load_explainer(model_path, scaler_path)
        self.model = self.explainer.model
        self.preprocessor = self.explainer.preprocessor

        elapsed = time.time() - start
        logger.info(f"PredictionService initialized in {elapsed:.2f}s")

    def predict(
        self,
        raw_features: Dict[str, Any],
        top_k_reasons: int = 5,
    ) -> Tuple[float, str, List[Reason]]:
        """
        Run a single prediction: score + risk level + reasons.

        Args:
            raw_features: Dict with keys matching ALL_FEATURES
            top_k_reasons: Number of top SHAP reasons to return

        Returns:
            (credibility_score, risk_level, reasons_list)
        """
        start = time.time()

        # Scale features and predict
        X_scaled = transform_single(raw_features, self.preprocessor)
        score = float(self.model.predict(X_scaled)[0])

        # Clip to valid range (XGBoost can sometimes predict slightly outside [0,1])
        score = float(np.clip(score, 0.0, 1.0))

        # Classify risk
        risk_level = classify_risk(score)

        # Generate SHAP-based reasons
        reasons = self.explainer.explain(raw_features, top_k=top_k_reasons)

        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            f"Prediction complete: score={score:.4f}, risk={risk_level}, "
            f"latency={elapsed_ms:.1f}ms"
        )

        return score, risk_level, reasons

    def predict_batch(
        self,
        raw_features_list: List[Dict[str, Any]],
        top_k_reasons: int = 5,
    ) -> List[Tuple[float, str, List[Reason]]]:
        """
        Run batch predictions.

        Currently iterates sequentially. For production with large batches,
        we'd vectorize the scaling + prediction (but SHAP per-prediction
        is inherently sequential due to how we map reasons).

        Args:
            raw_features_list: List of feature dicts
            top_k_reasons: Number of top SHAP reasons per prediction

        Returns:
            List of (score, risk_level, reasons) tuples
        """
        start = time.time()
        results = []

        for features in raw_features_list:
            result = self.predict(features, top_k_reasons)
            results.append(result)

        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            f"Batch prediction complete: {len(results)} attempts, "
            f"total_latency={elapsed_ms:.1f}ms, "
            f"avg_latency={elapsed_ms / len(results):.1f}ms"
        )

        return results

    @property
    def is_ready(self) -> bool:
        """Check if the service is loaded and ready for predictions."""
        return (
            self.model is not None
            and self.preprocessor is not None
            and self.explainer is not None
        )
