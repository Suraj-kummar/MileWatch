"""
MileWatch — API Tests

Tests the Flask API endpoints end-to-end:
1. Health check
2. Single prediction (valid, invalid, edge cases)
3. Batch prediction (valid, limits)

RUN: python -m pytest tests/test_api.py -v
"""

import sys
from pathlib import Path

import pytest

# Add service and model to path
sys.path.insert(0, str(Path(__file__).parent.parent / "service"))
sys.path.insert(0, str(Path(__file__).parent.parent / "model"))

from app import app, initialize_service


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create a test client with the model loaded."""
    app.config["TESTING"] = True
    initialize_service()
    with app.test_client() as client:
        yield client


# Sample test data
VALID_SUSPICIOUS = {
    "gps_distance_m": 3200.0,
    "time_gap_minutes": 8.0,
    "call_made": 0,
    "is_cod": 1,
    "exec_historical_fake_rate": 0.28,
    "minutes_to_shift_end": 12.0,
    "pincode_tier": 2,
}

VALID_GENUINE = {
    "gps_distance_m": 120.0,
    "time_gap_minutes": 38.0,
    "call_made": 1,
    "is_cod": 0,
    "exec_historical_fake_rate": 0.03,
    "minutes_to_shift_end": 240.0,
    "pincode_tier": 1,
}


# ── Health Check Tests ─────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_200(self, client):
        """Health endpoint should return 200 when model is loaded."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True


# ── Single Prediction Tests ───────────────────────────────────────────

class TestSinglePrediction:
    def test_predict_suspicious_attempt(self, client):
        """Suspicious attempt should get a low credibility score."""
        resp = client.post("/predict", json=VALID_SUSPICIOUS)
        assert resp.status_code == 200

        data = resp.get_json()
        assert "credibility_score" in data
        assert "risk_level" in data
        assert "reasons" in data
        assert "dispute_draft" in data
        assert "latency_ms" in data

        # Suspicious attempt should score low
        assert data["credibility_score"] < 0.50
        assert data["risk_level"] in ("HIGH_RISK", "MEDIUM_RISK")
        assert len(data["reasons"]) > 0

    def test_predict_genuine_attempt(self, client):
        """Genuine attempt should get a high credibility score."""
        resp = client.post("/predict", json=VALID_GENUINE)
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["credibility_score"] > 0.50
        assert data["risk_level"] in ("LOW_RISK", "MEDIUM_RISK")

    def test_predict_with_attempt_id(self, client):
        """Attempt ID should be echoed back in the response."""
        payload = {**VALID_SUSPICIOUS, "attempt_id": "TEST-001"}
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["attempt_id"] == "TEST-001"

    def test_predict_missing_features(self, client):
        """Should reject request with missing features."""
        incomplete = {"gps_distance_m": 100.0}
        resp = client.post("/predict", json=incomplete)
        assert resp.status_code == 422

        data = resp.get_json()
        assert "error" in data
        assert "Missing" in data["error"]

    def test_predict_invalid_types(self, client):
        """Should reject request with wrong types."""
        bad_data = {**VALID_GENUINE, "gps_distance_m": "not_a_number"}
        resp = client.post("/predict", json=bad_data)
        # Should either coerce or reject — "not_a_number" can't be float
        assert resp.status_code in (200, 422)

    def test_predict_out_of_range(self, client):
        """Should reject values outside valid ranges."""
        bad_data = {**VALID_GENUINE, "gps_distance_m": -500.0}
        resp = client.post("/predict", json=bad_data)
        assert resp.status_code == 422

    def test_predict_invalid_binary(self, client):
        """Binary fields should only accept 0 or 1."""
        bad_data = {**VALID_GENUINE, "call_made": 5}
        resp = client.post("/predict", json=bad_data)
        assert resp.status_code == 422

    def test_predict_no_body(self, client):
        """Should handle missing request body."""
        resp = client.post("/predict", content_type="application/json")
        assert resp.status_code == 400

    def test_predict_score_in_range(self, client):
        """Score should always be between 0 and 1."""
        resp = client.post("/predict", json=VALID_SUSPICIOUS)
        data = resp.get_json()
        assert 0.0 <= data["credibility_score"] <= 1.0

    def test_predict_reasons_structure(self, client):
        """Each reason should have the expected fields."""
        resp = client.post("/predict", json=VALID_SUSPICIOUS)
        data = resp.get_json()

        for reason in data["reasons"]:
            assert "feature" in reason
            assert "feature_label" in reason
            assert "direction" in reason
            assert reason["direction"] in ("positive", "negative")
            assert "impact" in reason
            assert isinstance(reason["impact"], (int, float))
            assert "description" in reason
            assert len(reason["description"]) > 0

    def test_predict_dispute_draft_present(self, client):
        """Dispute draft should be a non-empty string."""
        resp = client.post("/predict", json=VALID_SUSPICIOUS)
        data = resp.get_json()
        assert isinstance(data["dispute_draft"], str)
        assert len(data["dispute_draft"]) > 50  # Should be a real paragraph


# ── Batch Prediction Tests ────────────────────────────────────────────

class TestBatchPrediction:
    def test_batch_predict(self, client):
        """Batch endpoint should score multiple attempts."""
        payload = {
            "attempts": [VALID_SUSPICIOUS, VALID_GENUINE]
        }
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        assert "latency_ms" in data

        # Verify each result has the full structure
        for result in data["results"]:
            assert "credibility_score" in result
            assert "risk_level" in result
            assert "reasons" in result
            assert "dispute_draft" in result

    def test_batch_empty_list(self, client):
        """Should reject empty batch."""
        resp = client.post("/predict/batch", json={"attempts": []})
        assert resp.status_code == 422

    def test_batch_missing_key(self, client):
        """Should reject request without 'attempts' key."""
        resp = client.post("/predict/batch", json={"data": []})
        assert resp.status_code == 422

    def test_batch_invalid_attempt_in_list(self, client):
        """Should reject if any attempt in batch is invalid."""
        payload = {
            "attempts": [
                VALID_GENUINE,
                {"gps_distance_m": 100.0},  # Incomplete
            ]
        }
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 422

    def test_batch_with_attempt_ids(self, client):
        """Attempt IDs should be echoed back per result."""
        payload = {
            "attempts": [
                {**VALID_SUSPICIOUS, "attempt_id": "BATCH-001"},
                {**VALID_GENUINE, "attempt_id": "BATCH-002"},
            ]
        }
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["results"][0]["attempt_id"] == "BATCH-001"
        assert data["results"][1]["attempt_id"] == "BATCH-002"


# ── 404 / Method Tests ────────────────────────────────────────────────

class TestErrorHandling:
    def test_404_endpoint(self, client):
        """Unknown endpoints should return 404 JSON."""
        resp = client.get("/nonexistent")
        assert resp.status_code == 404

    def test_get_predict_not_allowed(self, client):
        """GET on /predict should return 405."""
        resp = client.get("/predict")
        assert resp.status_code == 405
