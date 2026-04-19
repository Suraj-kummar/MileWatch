"""
MileWatch — Request/Response Validation Schemas

WHY THIS FILE EXISTS:
The Flask API must reject bad inputs before they reach the model. An unscaled
GPS distance of -500 or a pincode_tier of 99 would produce meaningless scores.

This module validates:
1. All required fields are present
2. Types are correct (float, int, bool)
3. Values are within physically plausible ranges
4. Batch size limits are enforced

DESIGN DECISION: We use plain validation functions instead of a library like
marshmallow/pydantic because the schema is small (7 fields) and adding a
dependency for this would be over-engineering.
"""

from typing import Dict, List, Tuple, Any, Optional


# ── Feature constraints ────────────────────────────────────────────────
# Each feature: (type, min_value, max_value)
# None means no bound

FEATURE_CONSTRAINTS = {
    "gps_distance_m": (float, 0.0, 50_000.0),        # 0m to 50km max
    "time_gap_minutes": (float, 0.0, 1440.0),         # 0 to 24 hours
    "call_made": (int, 0, 1),                          # Binary
    "is_cod": (int, 0, 1),                             # Binary
    "exec_historical_fake_rate": (float, 0.0, 1.0),   # Percentage as decimal
    "minutes_to_shift_end": (float, 0.0, 720.0),      # 0 to 12 hours
    "pincode_tier": (int, 1, 3),                       # Metro(1), Tier-2(2), Tier-3(3)
}

REQUIRED_FEATURES = list(FEATURE_CONSTRAINTS.keys())

# Batch prediction limits
MAX_BATCH_SIZE = 50


def validate_attempt(data: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate a single delivery attempt's feature data.

    Args:
        data: Raw request body dict

    Returns:
        Tuple of (validated_features_dict, error_message)
        If valid: (features, None)
        If invalid: (None, error_string)
    """
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    # Check required fields
    missing = [f for f in REQUIRED_FEATURES if f not in data]
    if missing:
        return None, f"Missing required features: {missing}"

    validated = {}
    errors = []

    for feature, (expected_type, min_val, max_val) in FEATURE_CONSTRAINTS.items():
        value = data[feature]

        # Type coercion + validation
        try:
            if expected_type == float:
                value = float(value)
            elif expected_type == int:
                value = int(value)
                # Ensure binary fields are actually 0 or 1
                if feature in ("call_made", "is_cod") and value not in (0, 1):
                    errors.append(f"{feature} must be 0 or 1, got {value}")
                    continue
        except (ValueError, TypeError):
            errors.append(f"{feature} must be {expected_type.__name__}, got {type(value).__name__}")
            continue

        # Range validation
        if min_val is not None and value < min_val:
            errors.append(f"{feature} must be >= {min_val}, got {value}")
            continue
        if max_val is not None and value > max_val:
            errors.append(f"{feature} must be <= {max_val}, got {value}")
            continue

        validated[feature] = value

    if errors:
        return None, "; ".join(errors)

    return validated, None


def validate_batch(data: dict) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Validate a batch prediction request.

    Expected format:
    {
        "attempts": [
            { features... },
            { features... },
            ...
        ]
    }

    Returns:
        Tuple of (list_of_validated_features, error_message)
    """
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    if "attempts" not in data:
        return None, "Missing 'attempts' key in request body"

    attempts = data["attempts"]
    if not isinstance(attempts, list):
        return None, "'attempts' must be a list"

    if len(attempts) == 0:
        return None, "'attempts' list cannot be empty"

    if len(attempts) > MAX_BATCH_SIZE:
        return None, f"Batch size {len(attempts)} exceeds maximum of {MAX_BATCH_SIZE}"

    validated_list = []
    for i, attempt in enumerate(attempts):
        validated, error = validate_attempt(attempt)
        if error:
            return None, f"Attempt [{i}]: {error}"
        validated_list.append(validated)

    return validated_list, None


def format_prediction_response(
    score: float,
    risk_level: str,
    reasons: list,
    dispute_draft: str,
    attempt_id: str = None,
) -> dict:
    """
    Format a single prediction result into the API response schema.

    Returns:
        {
            "attempt_id": "...",  (if provided)
            "credibility_score": 0.23,
            "risk_level": "HIGH_RISK",
            "reasons": [ { reason_dict }, ... ],
            "dispute_draft": "On ..."
        }
    """
    response = {
        "credibility_score": round(score, 4),
        "risk_level": risk_level,
        "reasons": [r.to_dict() if hasattr(r, 'to_dict') else r for r in reasons],
        "dispute_draft": dispute_draft,
    }

    if attempt_id:
        response["attempt_id"] = attempt_id

    return response
