"""
MileWatch — Behavioral Profile Definitions

WHY THIS FILE EXISTS:
In real delivery systems, fake attempts show CORRELATED signal patterns — not random noise.
An exec faking a delivery is far away, didn't call, near shift end, on a COD order — simultaneously.
If we simulate features independently, the model learns to separate random distributions, not fraud.

These profiles encode real-world delivery behavior archetypes derived from:
- Consumer complaint patterns (Twitter, Reddit r/india, consumer forums)
- Delivery industry domain knowledge
- Logical fraud incentive structures (COD avoidance, shift-end behavior)

Each profile defines distributions for every feature, ensuring cross-feature correlations
are realistic. The model should DISCOVER these patterns, not memorize them.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class FeatureDistribution:
    """
    Defines how a single feature is sampled within a profile.

    Attributes:
        dist_type: 'normal', 'uniform', 'binary', 'categorical'
        params: Parameters for the distribution.
            - normal: {'mean': float, 'std': float, 'min': float, 'max': float}
            - uniform: {'low': float, 'high': float}
            - binary: {'probability': float}  (probability of 1)
            - categorical: {'weights': {value: probability}}
    """
    dist_type: str
    params: Dict


@dataclass(frozen=True)
class BehavioralProfile:
    """
    A behavioral archetype representing a class of delivery attempt behavior.

    Each profile models a real-world scenario: genuine attempts, lazy skips,
    shift-end dumps, or systematic fraud. Features within a profile are defined
    as distributions, ensuring correlated sampling.
    """
    name: str
    description: str
    proportion: float  # Fraction of total dataset this profile represents
    credibility_range: Tuple[float, float]  # (min, max) credibility score range

    # ── Feature distributions ──────────────────────────────────────────
    gps_distance_m: FeatureDistribution
    time_gap_minutes: FeatureDistribution
    call_made: FeatureDistribution
    is_cod: FeatureDistribution
    exec_historical_fake_rate: FeatureDistribution
    minutes_to_shift_end: FeatureDistribution
    pincode_tier: FeatureDistribution

    # ── Credibility score construction weights ─────────────────────────
    # These weights define how much each feature contributes to the
    # credibility score for THIS profile. They model the intuition:
    # "for a lazy skip, GPS distance matters more than pincode tier."
    score_weights: Dict[str, float] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════
# PROFILE DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════

GENUINE_ATTEMPT = BehavioralProfile(
    name="GENUINE_ATTEMPT",
    description=(
        "Executive genuinely went to the address, customer was actually unavailable. "
        "GPS is close, call was likely made, timing is normal within the shift."
    ),
    proportion=0.55,
    credibility_range=(0.75, 1.0),

    gps_distance_m=FeatureDistribution(
        dist_type="normal",
        params={"mean": 150.0, "std": 120.0, "min": 10.0, "max": 600.0}
    ),
    time_gap_minutes=FeatureDistribution(
        dist_type="normal",
        params={"mean": 35.0, "std": 12.0, "min": 10.0, "max": 90.0}
    ),
    call_made=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.85}
    ),
    is_cod=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.40}  # Matches real-world COD ratio
    ),
    exec_historical_fake_rate=FeatureDistribution(
        dist_type="normal",
        params={"mean": 0.05, "std": 0.03, "min": 0.0, "max": 0.15}
    ),
    minutes_to_shift_end=FeatureDistribution(
        dist_type="uniform",
        params={"low": 30.0, "high": 480.0}  # Spread across shift
    ),
    pincode_tier=FeatureDistribution(
        dist_type="categorical",
        params={"weights": {1: 0.45, 2: 0.35, 3: 0.20}}
    ),
    score_weights={
        "gps_distance_m": 0.30,
        "call_made": 0.20,
        "time_gap_minutes": 0.15,
        "is_cod": 0.05,
        "exec_historical_fake_rate": 0.15,
        "minutes_to_shift_end": 0.10,
        "pincode_tier": 0.05,
    },
)

GENUINE_BORDERLINE = BehavioralProfile(
    name="GENUINE_BORDERLINE",
    description=(
        "Executive went nearby but not exactly to the door — GPS shows medium distance. "
        "Could be GPS drift, parked on the street, or building access issue. "
        "Call was sometimes made. Slightly suspicious but likely genuine."
    ),
    proportion=0.15,
    credibility_range=(0.50, 0.75),

    gps_distance_m=FeatureDistribution(
        dist_type="normal",
        params={"mean": 700.0, "std": 350.0, "min": 200.0, "max": 1800.0}
    ),
    time_gap_minutes=FeatureDistribution(
        dist_type="normal",
        params={"mean": 45.0, "std": 18.0, "min": 15.0, "max": 120.0}
    ),
    call_made=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.60}
    ),
    is_cod=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.42}
    ),
    exec_historical_fake_rate=FeatureDistribution(
        dist_type="normal",
        params={"mean": 0.10, "std": 0.05, "min": 0.0, "max": 0.25}
    ),
    minutes_to_shift_end=FeatureDistribution(
        dist_type="uniform",
        params={"low": 20.0, "high": 400.0}
    ),
    pincode_tier=FeatureDistribution(
        dist_type="categorical",
        params={"weights": {1: 0.40, 2: 0.35, 3: 0.25}}
    ),
    score_weights={
        "gps_distance_m": 0.25,
        "call_made": 0.25,
        "time_gap_minutes": 0.15,
        "is_cod": 0.05,
        "exec_historical_fake_rate": 0.15,
        "minutes_to_shift_end": 0.10,
        "pincode_tier": 0.05,
    },
)

LAZY_SKIP = BehavioralProfile(
    name="LAZY_SKIP",
    description=(
        "Executive didn't want to deliver this order — typically COD, far away, "
        "or inconvenient. Marked as attempted without actually going. "
        "GPS is far, no call made, time gap is suspiciously short."
    ),
    proportion=0.13,
    credibility_range=(0.15, 0.45),

    gps_distance_m=FeatureDistribution(
        dist_type="normal",
        params={"mean": 2200.0, "std": 900.0, "min": 800.0, "max": 5000.0}
    ),
    time_gap_minutes=FeatureDistribution(
        dist_type="normal",
        params={"mean": 12.0, "std": 6.0, "min": 2.0, "max": 30.0}
    ),
    call_made=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.15}
    ),
    is_cod=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.70}  # COD avoidance bias
    ),
    exec_historical_fake_rate=FeatureDistribution(
        dist_type="normal",
        params={"mean": 0.18, "std": 0.08, "min": 0.05, "max": 0.40}
    ),
    minutes_to_shift_end=FeatureDistribution(
        dist_type="normal",
        params={"mean": 120.0, "std": 90.0, "min": 10.0, "max": 400.0}
    ),
    pincode_tier=FeatureDistribution(
        dist_type="categorical",
        params={"weights": {1: 0.35, 2: 0.40, 3: 0.25}}
    ),
    score_weights={
        "gps_distance_m": 0.30,
        "call_made": 0.25,
        "time_gap_minutes": 0.20,
        "is_cod": 0.10,
        "exec_historical_fake_rate": 0.10,
        "minutes_to_shift_end": 0.03,
        "pincode_tier": 0.02,
    },
)

SHIFT_END_DUMP = BehavioralProfile(
    name="SHIFT_END_DUMP",
    description=(
        "Executive is near shift end and bulk-marks remaining deliveries as attempted. "
        "GPS shows they're nowhere near the addresses. Time gaps are very short "
        "(multiple fake attempts in quick succession). Classic end-of-shift fraud."
    ),
    proportion=0.10,
    credibility_range=(0.05, 0.30),

    gps_distance_m=FeatureDistribution(
        dist_type="normal",
        params={"mean": 3500.0, "std": 1500.0, "min": 1000.0, "max": 8000.0}
    ),
    time_gap_minutes=FeatureDistribution(
        dist_type="normal",
        params={"mean": 6.0, "std": 4.0, "min": 1.0, "max": 15.0}
    ),
    call_made=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.10}
    ),
    is_cod=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.50}
    ),
    exec_historical_fake_rate=FeatureDistribution(
        dist_type="normal",
        params={"mean": 0.22, "std": 0.10, "min": 0.05, "max": 0.45}
    ),
    minutes_to_shift_end=FeatureDistribution(
        dist_type="normal",
        params={"mean": 15.0, "std": 10.0, "min": 1.0, "max": 40.0}
    ),
    pincode_tier=FeatureDistribution(
        dist_type="categorical",
        params={"weights": {1: 0.40, 2: 0.35, 3: 0.25}}
    ),
    score_weights={
        "gps_distance_m": 0.20,
        "call_made": 0.15,
        "time_gap_minutes": 0.15,
        "is_cod": 0.05,
        "exec_historical_fake_rate": 0.10,
        "minutes_to_shift_end": 0.30,  # Shift-end is the dominant signal
        "pincode_tier": 0.05,
    },
)

SYSTEMATIC_FRAUD = BehavioralProfile(
    name="SYSTEMATIC_FRAUD",
    description=(
        "Executive has a pattern of faking attempts — high historical fake rate, "
        "consistently far GPS, rarely calls, heavily skewed toward COD orders. "
        "Some may attempt GPS spoofing (close GPS but no call, short time gap). "
        "Hardest to catch individually but pattern is clear over time."
    ),
    proportion=0.07,
    credibility_range=(0.0, 0.20),

    gps_distance_m=FeatureDistribution(
        dist_type="normal",
        params={"mean": 2800.0, "std": 1800.0, "min": 50.0, "max": 7000.0}
        # NOTE: min is 50m because some fraudsters spoof GPS
    ),
    time_gap_minutes=FeatureDistribution(
        dist_type="normal",
        params={"mean": 8.0, "std": 5.0, "min": 1.0, "max": 25.0}
    ),
    call_made=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.20}  # Some make fake calls to cover tracks
    ),
    is_cod=FeatureDistribution(
        dist_type="binary",
        params={"probability": 0.80}  # Heavily COD-biased
    ),
    exec_historical_fake_rate=FeatureDistribution(
        dist_type="normal",
        params={"mean": 0.30, "std": 0.10, "min": 0.15, "max": 0.50}
    ),
    minutes_to_shift_end=FeatureDistribution(
        dist_type="uniform",
        params={"low": 5.0, "high": 300.0}  # Happens anytime
    ),
    pincode_tier=FeatureDistribution(
        dist_type="categorical",
        params={"weights": {1: 0.30, 2: 0.40, 3: 0.30}}
    ),
    score_weights={
        "gps_distance_m": 0.20,
        "call_made": 0.15,
        "time_gap_minutes": 0.15,
        "is_cod": 0.10,
        "exec_historical_fake_rate": 0.30,  # History is the dominant signal
        "minutes_to_shift_end": 0.05,
        "pincode_tier": 0.05,
    },
)

# ══════════════════════════════════════════════════════════════════════════
# PROFILE REGISTRY
# ══════════════════════════════════════════════════════════════════════════

ALL_PROFILES = [
    GENUINE_ATTEMPT,
    GENUINE_BORDERLINE,
    LAZY_SKIP,
    SHIFT_END_DUMP,
    SYSTEMATIC_FRAUD,
]

# Feature names used in the dataset (order matters for consistency)
FEATURE_COLUMNS = [
    "gps_distance_m",
    "time_gap_minutes",
    "call_made",
    "is_cod",
    "exec_historical_fake_rate",
    "minutes_to_shift_end",
    "pincode_tier",
]

# Sanity check: profile proportions must sum to 1.0
_total_proportion = sum(p.proportion for p in ALL_PROFILES)
assert abs(_total_proportion - 1.0) < 1e-6, (
    f"Profile proportions sum to {_total_proportion}, expected 1.0. "
    f"Fix the proportions before generating data."
)
