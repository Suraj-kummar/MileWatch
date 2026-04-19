"""
MileWatch — Feature Engineering Pipeline

WHY THIS FILE EXISTS:
Raw features from the dataset need to be preprocessed consistently across
training and inference. This module provides a single pipeline that:

1. Separates features from target variable
2. Scales continuous features (StandardScaler) so XGBoost can converge faster
3. Passes binary/categorical features through untouched
4. Splits into train/test with stratification by credibility bucket
5. Saves the fitted scaler for reuse during inference

CRITICAL: The same pipeline MUST be used at training time and inference time,
otherwise the model receives differently scaled inputs and predictions are garbage.
"""

import sys
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ── Feature configuration ──────────────────────────────────────────────

# Continuous features that need scaling
CONTINUOUS_FEATURES = [
    "gps_distance_m",
    "time_gap_minutes",
    "exec_historical_fake_rate",
    "minutes_to_shift_end",
]

# Binary/categorical features — pass through as-is
PASSTHROUGH_FEATURES = [
    "call_made",
    "is_cod",
    "pincode_tier",
]

# All model features in strict order
ALL_FEATURES = CONTINUOUS_FEATURES + PASSTHROUGH_FEATURES

# Target column
TARGET_COLUMN = "credibility_score"

# Columns that are NOT features (excluded from model input)
NON_FEATURE_COLUMNS = ["attempt_id", "profile", TARGET_COLUMN]


def build_preprocessor() -> ColumnTransformer:
    """
    Build the feature preprocessing pipeline.

    WHY ColumnTransformer:
    - Scales continuous features independently
    - Leaves binary/categorical features unchanged
    - Maintains column order deterministically
    - Can be serialized and reused at inference time
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("continuous", StandardScaler(), CONTINUOUS_FEATURES),
            ("passthrough", "passthrough", PASSTHROUGH_FEATURES),
        ],
        remainder="drop",  # Drop any columns not listed above
        verbose_feature_names_out=False,
    )
    return preprocessor


def load_dataset(data_path: str) -> pd.DataFrame:
    """Load and validate the delivery attempts CSV."""
    df = pd.read_csv(data_path)

    # Validate required columns exist
    required = set(ALL_FEATURES + [TARGET_COLUMN])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")

    # Validate no nulls in feature/target columns
    null_counts = df[ALL_FEATURES + [TARGET_COLUMN]].isnull().sum()
    if null_counts.any():
        raise ValueError(f"Null values found:\n{null_counts[null_counts > 0]}")

    return df


def create_stratification_bins(y: pd.Series, n_bins: int = 5) -> np.ndarray:
    """
    Create stratification bins from continuous credibility scores.

    WHY STRATIFY:
    We want train and test sets to have the same distribution of credibility scores.
    Since the target is continuous, we bin it into quantile buckets for stratification.
    This ensures the test set isn't accidentally dominated by easy (high/low) scores.
    """
    return pd.qcut(y, q=n_bins, labels=False, duplicates="drop").values


def prepare_data(
    data_path: str,
    test_size: float = 0.20,
    random_state: int = 42,
    save_preprocessor: bool = True,
    artifacts_dir: str = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, ColumnTransformer]:
    """
    Full data preparation pipeline: load, split, scale, return.

    Args:
        data_path: Path to delivery_attempts.csv
        test_size: Fraction of data for test set (default 20%)
        random_state: Random seed for reproducibility
        save_preprocessor: Whether to save the fitted scaler to disk
        artifacts_dir: Directory to save model artifacts

    Returns:
        X_train: Scaled training features (numpy array)
        X_test: Scaled test features (numpy array)
        y_train: Training target values (numpy array)
        y_test: Test target values (numpy array)
        preprocessor: Fitted ColumnTransformer (for reuse at inference)
    """
    print("Loading dataset...")
    df = load_dataset(data_path)
    print(f"  Loaded {len(df):,} records")

    # Separate features and target
    X = df[ALL_FEATURES]
    y = df[TARGET_COLUMN]

    # Create stratification bins
    strat_bins = create_stratification_bins(y)

    # Train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=strat_bins,
    )

    print(f"  Train: {len(X_train):,} samples")
    print(f"  Test:  {len(X_test):,} samples")

    # Fit preprocessor on training data ONLY (prevent data leakage)
    print("Fitting preprocessor...")
    preprocessor = build_preprocessor()
    X_train_scaled = preprocessor.fit_transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)

    # Save preprocessor for inference
    if save_preprocessor:
        if artifacts_dir is None:
            artifacts_dir = Path(__file__).parent / "artifacts"
        else:
            artifacts_dir = Path(artifacts_dir)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        scaler_path = artifacts_dir / "feature_scaler.pkl"
        joblib.dump(preprocessor, scaler_path)
        print(f"  Saved preprocessor: {scaler_path}")

    # Convert to numpy arrays
    y_train = y_train.values
    y_test = y_test.values

    print(f"  Feature shape: {X_train_scaled.shape}")
    print(f"  Features: {ALL_FEATURES}")

    return X_train_scaled, X_test_scaled, y_train, y_test, preprocessor


def transform_single(raw_features: dict, preprocessor: ColumnTransformer) -> np.ndarray:
    """
    Transform a single delivery attempt's features for prediction.

    Used at inference time in the Flask service. Takes a raw feature dict
    (as received from the API) and returns a scaled numpy array.

    Args:
        raw_features: Dict with keys matching ALL_FEATURES
        preprocessor: Fitted ColumnTransformer (loaded from feature_scaler.pkl)

    Returns:
        Scaled feature array of shape (1, n_features)
    """
    # Validate all features present
    missing = set(ALL_FEATURES) - set(raw_features.keys())
    if missing:
        raise ValueError(f"Missing features for prediction: {missing}")

    # Create single-row dataframe in correct column order
    df = pd.DataFrame([{col: raw_features[col] for col in ALL_FEATURES}])

    return preprocessor.transform(df)


if __name__ == "__main__":
    # Quick test: load data, prepare, print shapes
    data_path = Path(__file__).parent.parent / "data" / "generated" / "delivery_attempts.csv"

    if not data_path.exists():
        print(f"ERROR: Data not found at {data_path}")
        print("Run data/generator.py first.")
        sys.exit(1)

    X_train, X_test, y_train, y_test, preprocessor = prepare_data(str(data_path))

    print("\nQuick validation:")
    print(f"  X_train shape: {X_train.shape}")
    print(f"  X_test shape:  {X_test.shape}")
    print(f"  y_train range: [{y_train.min():.3f}, {y_train.max():.3f}]")
    print(f"  y_test range:  [{y_test.min():.3f}, {y_test.max():.3f}]")
    print(f"  y_train mean:  {y_train.mean():.3f}")
    print(f"  y_test mean:   {y_test.mean():.3f}")
    print("\nPhase 2A complete.")
