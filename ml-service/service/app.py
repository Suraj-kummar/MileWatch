"""
MileWatch — Flask Application (ML Inference API)

WHY FLASK (not FastAPI, not Django):
- Flask is the thinnest HTTP wrapper possible for a prediction service
- We need exactly 3 endpoints — Flask handles this with zero boilerplate
- The ML service does ONE thing: receive features → return score + reasons
- No ORM, no auth, no sessions, no templates — just JSON in, JSON out

ARCHITECTURE:
- Model/scaler/explainer loaded ONCE at startup (not per-request)
- Request → validate → scale → predict → explain → dispute draft → response
- All predictions logged with latency for monitoring
- Health endpoint for Spring Boot to verify service is alive

ENDPOINTS:
    GET  /health          → { "status": "healthy", "model_loaded": true }
    POST /predict         → Single attempt scoring
    POST /predict/batch   → Batch scoring (up to 50 attempts)
"""

import sys
import time
import logging
from pathlib import Path

from flask import Flask, request, jsonify

# Add service dir to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "model"))

from predictor import PredictionService
from dispute_generator import generate_dispute_draft
from schemas import (
    validate_attempt,
    validate_batch,
    format_prediction_response,
)


# ── Logging setup ──────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("milewatch.api")


# ── Flask app ──────────────────────────────────────────────────────────

app = Flask(__name__)

# Global prediction service — loaded once at startup
prediction_service: PredictionService = None


def initialize_service():
    """Load the ML model and initialize the prediction service."""
    global prediction_service
    try:
        prediction_service = PredictionService()
        logger.info("ML service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ML service: {e}")
        raise


# ── Health Check ───────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.

    Used by Spring Boot's ML service client to verify the Flask service
    is alive and the model is loaded before sending prediction requests.
    """
    if prediction_service is None or not prediction_service.is_ready:
        return jsonify({
            "status": "unhealthy",
            "model_loaded": False,
            "error": "Prediction service not initialized",
        }), 503

    return jsonify({
        "status": "healthy",
        "model_loaded": True,
    }), 200


# ── Single Prediction ─────────────────────────────────────────────────

@app.route("/predict", methods=["POST"])
def predict():
    """
    Score a single delivery attempt.

    Request body:
    {
        "gps_distance_m": 3200.0,
        "time_gap_minutes": 8.0,
        "call_made": 0,
        "is_cod": 1,
        "exec_historical_fake_rate": 0.28,
        "minutes_to_shift_end": 12.0,
        "pincode_tier": 2,
        "attempt_id": "optional-id-for-tracking"
    }

    Response:
    {
        "credibility_score": 0.1842,
        "risk_level": "HIGH_RISK",
        "reasons": [ ... ],
        "dispute_draft": "...",
        "attempt_id": "...",
        "latency_ms": 15.3
    }
    """
    start = time.time()

    # Parse request
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON in request body"}), 400

    # Extract optional attempt_id (not a model feature)
    attempt_id = data.pop("attempt_id", None)

    # Validate features
    validated, error = validate_attempt(data)
    if error:
        return jsonify({"error": error}), 422

    try:
        # Run prediction
        score, risk_level, reasons = prediction_service.predict(validated)

        # Generate dispute draft
        dispute_draft = generate_dispute_draft(
            score=score,
            risk_level=risk_level,
            reasons=reasons,
            attempt_id=attempt_id,
        )

        # Build response
        response = format_prediction_response(
            score=score,
            risk_level=risk_level,
            reasons=reasons,
            dispute_draft=dispute_draft,
            attempt_id=attempt_id,
        )

        elapsed_ms = (time.time() - start) * 1000
        response["latency_ms"] = round(elapsed_ms, 1)

        logger.info(
            f"[PREDICT] attempt_id={attempt_id} score={score:.4f} "
            f"risk={risk_level} latency={elapsed_ms:.1f}ms"
        )

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


# ── Batch Prediction ──────────────────────────────────────────────────

@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    Score multiple delivery attempts in one request.

    Request body:
    {
        "attempts": [
            { features... },
            { features... },
            ...
        ]
    }

    Response:
    {
        "results": [ { prediction_response }, ... ],
        "total": 5,
        "latency_ms": 75.2
    }

    Max batch size: 50 attempts.
    """
    start = time.time()

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON in request body"}), 400

    # Validate batch
    validated_list, error = validate_batch(data)
    if error:
        return jsonify({"error": error}), 422

    try:
        # Run batch predictions
        results = prediction_service.predict_batch(validated_list)

        # Format each result
        response_results = []
        for i, (score, risk_level, reasons) in enumerate(results):
            # Get optional attempt_id from original data
            attempt_id = data["attempts"][i].get("attempt_id")

            dispute_draft = generate_dispute_draft(
                score=score,
                risk_level=risk_level,
                reasons=reasons,
                attempt_id=attempt_id,
            )

            response_results.append(
                format_prediction_response(
                    score=score,
                    risk_level=risk_level,
                    reasons=reasons,
                    dispute_draft=dispute_draft,
                    attempt_id=attempt_id,
                )
            )

        elapsed_ms = (time.time() - start) * 1000

        logger.info(
            f"[BATCH] {len(results)} attempts scored, "
            f"total_latency={elapsed_ms:.1f}ms"
        )

        return jsonify({
            "results": response_results,
            "total": len(response_results),
            "latency_ms": round(elapsed_ms, 1),
        }), 200

    except Exception as e:
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        return jsonify({"error": f"Batch prediction failed: {str(e)}"}), 500


# ── Error handlers ────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── Main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting MileWatch ML Service...")
    initialize_service()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,  # Never debug=True in production (leaks internals)
    )
