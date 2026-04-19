"""
MileWatch — XGBoost Model Training

WHY XGBoost REGRESSOR (not classifier):
- Our target is a CONTINUOUS credibility score (0.0 to 1.0), not a binary label.
- Regression preserves the granularity: 0.15 is worse than 0.40, which matters.
- Binary classification would lose the "how bad" information.
- XGBoost handles tabular data extremely well with built-in regularization.

WHY THESE HYPERPARAMETERS:
- n_estimators=300: Enough trees to capture complex patterns without overfitting
- max_depth=5: Controls tree complexity. Deeper = more overfitting risk on 15K samples
- learning_rate=0.05: Small steps → better generalization (compensated by more trees)
- reg_alpha/reg_lambda: L1/L2 regularization to prevent overfitting
- subsample=0.8: Each tree sees 80% of data → reduces overfitting
- colsample_bytree=0.8: Each tree uses 80% of features → reduces feature co-dependence

USAGE:
    python train.py                                  # Default config
    python train.py --data ../data/generated/delivery_attempts.csv
    python train.py --n-estimators 500 --max-depth 6  # Custom hyperparams
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.model_selection import cross_val_score

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from features import ALL_FEATURES, prepare_data


def get_default_params() -> dict:
    """
    Return default XGBoost hyperparameters.

    These are tuned for our dataset characteristics:
    - 15K samples, 7 features
    - Continuous target in [0, 1]
    - Need interpretable feature importances
    """
    return {
        "n_estimators": 300,
        "max_depth": 5,
        "learning_rate": 0.05,
        "reg_alpha": 0.1,         # L1 regularization
        "reg_lambda": 1.0,        # L2 regularization
        "subsample": 0.8,         # Row sampling
        "colsample_bytree": 0.8,  # Feature sampling per tree
        "min_child_weight": 3,    # Minimum samples in leaf
        "objective": "reg:squarederror",
        "random_state": 42,
        "n_jobs": -1,             # Use all CPU cores
    }


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    params: dict = None,
    run_cv: bool = True,
) -> xgb.XGBRegressor:
    """
    Train an XGBoost regressor with optional cross-validation.

    Args:
        X_train: Scaled training features
        y_train: Training target values
        params: XGBoost hyperparameters (defaults used if None)
        run_cv: Whether to run 5-fold cross-validation

    Returns:
        Trained XGBRegressor model
    """
    if params is None:
        params = get_default_params()

    print("\nModel Configuration:")
    for key, value in params.items():
        print(f"  {key}: {value}")

    # ── Cross-validation ───────────────────────────────────────────────
    if run_cv:
        print("\nRunning 5-fold cross-validation...")
        cv_model = xgb.XGBRegressor(**params)

        # MAE (negative because sklearn convention is higher = better)
        mae_scores = cross_val_score(
            cv_model, X_train, y_train,
            cv=5, scoring="neg_mean_absolute_error", n_jobs=-1
        )
        mae_scores = -mae_scores  # Convert to positive

        rmse_scores = cross_val_score(
            cv_model, X_train, y_train,
            cv=5, scoring="neg_root_mean_squared_error", n_jobs=-1
        )
        rmse_scores = -rmse_scores

        r2_scores = cross_val_score(
            cv_model, X_train, y_train,
            cv=5, scoring="r2", n_jobs=-1
        )

        print(f"\n  Cross-Validation Results (5-fold):")
        print(f"  -----------------------------------------")
        print(f"  MAE:   {mae_scores.mean():.4f} (+/- {mae_scores.std():.4f})")
        print(f"  RMSE:  {rmse_scores.mean():.4f} (+/- {rmse_scores.std():.4f})")
        print(f"  R2:    {r2_scores.mean():.4f} (+/- {r2_scores.std():.4f})")
        print(f"  -----------------------------------------")

        # Store CV results for evaluation report
        cv_results = {
            "mae_mean": float(mae_scores.mean()),
            "mae_std": float(mae_scores.std()),
            "rmse_mean": float(rmse_scores.mean()),
            "rmse_std": float(rmse_scores.std()),
            "r2_mean": float(r2_scores.mean()),
            "r2_std": float(r2_scores.std()),
        }
    else:
        cv_results = None

    # ── Final training on full training set ─────────────────────────────
    print("\nTraining final model on full training set...")
    start_time = time.time()

    model = xgb.XGBRegressor(**params)
    model.fit(
        X_train, y_train,
        verbose=False,
    )

    train_time = time.time() - start_time
    print(f"  Training time: {train_time:.2f}s")

    # Store CV results as attribute for later access
    model.cv_results_ = cv_results

    return model


def save_model(model: xgb.XGBRegressor, artifacts_dir: str = None) -> Path:
    """
    Save the trained model to disk in XGBoost's native JSON format.

    WHY JSON (not pickle):
    - JSON is human-readable and inspectable
    - XGBoost can load JSON natively without sklearn dependency
    - More portable across Python versions
    - Smaller file size than pickle for tree models
    """
    if artifacts_dir is None:
        artifacts_dir = Path(__file__).parent / "artifacts"
    else:
        artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifacts_dir / "xgb_model.json"
    model.save_model(str(model_path))
    print(f"  Saved model: {model_path}")

    # Also save feature importance
    importance = model.feature_importances_
    importance_dict = {
        feat: float(imp) for feat, imp in zip(ALL_FEATURES, importance)
    }
    # Sort by importance descending
    importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

    importance_path = artifacts_dir / "feature_importance.json"
    with open(importance_path, "w") as f:
        json.dump(importance_dict, f, indent=2)
    print(f"  Saved feature importance: {importance_path}")

    # Save CV results if available
    if hasattr(model, "cv_results_") and model.cv_results_:
        cv_path = artifacts_dir / "cv_results.json"
        with open(cv_path, "w") as f:
            json.dump(model.cv_results_, f, indent=2)
        print(f"  Saved CV results: {cv_path}")

    # Save hyperparameters for reproducibility
    params_path = artifacts_dir / "hyperparameters.json"
    params = model.get_params()
    # Convert non-serializable values
    serializable_params = {k: v for k, v in params.items() if isinstance(v, (int, float, str, bool, type(None)))}
    with open(params_path, "w") as f:
        json.dump(serializable_params, f, indent=2)
    print(f"  Saved hyperparameters: {params_path}")

    return model_path


def print_feature_importance(model: xgb.XGBRegressor) -> None:
    """Print feature importance ranking."""
    importance = model.feature_importances_
    pairs = sorted(zip(ALL_FEATURES, importance), key=lambda x: x[1], reverse=True)

    print("\nFeature Importance (Gain-based):")
    print("  -----------------------------------------")
    for feat, imp in pairs:
        bar = "#" * int(imp * 50)
        print(f"  {feat:<30} {imp:.4f}  {bar}")
    print("  -----------------------------------------")


def main():
    parser = argparse.ArgumentParser(description="MileWatch - Train XGBoost Model")
    parser.add_argument(
        "--data", type=str,
        default=str(Path(__file__).parent.parent / "data" / "generated" / "delivery_attempts.csv"),
        help="Path to delivery attempts CSV"
    )
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--no-cv", action="store_true", help="Skip cross-validation")

    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: Data not found at {data_path}")
        return 1

    print("=" * 60)
    print("MileWatch - XGBoost Model Training")
    print("=" * 60)

    # Phase 2A: Prepare data
    X_train, X_test, y_train, y_test, preprocessor = prepare_data(str(data_path))

    # Phase 2B: Train model
    params = get_default_params()
    params.update({
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "learning_rate": args.learning_rate,
    })

    model = train_model(X_train, y_train, params, run_cv=not args.no_cv)

    # Print feature importance
    print_feature_importance(model)

    # Quick test set evaluation
    y_pred = model.predict(X_test)
    from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

    print("\nTest Set Performance:")
    print(f"  MAE:  {mean_absolute_error(y_test, y_pred):.4f}")
    print(f"  RMSE: {root_mean_squared_error(y_test, y_pred):.4f}")
    print(f"  R2:   {r2_score(y_test, y_pred):.4f}")

    # Save model and artifacts
    print("\nSaving artifacts...")
    save_model(model)

    # Save test data for evaluation script
    import pandas as pd
    artifacts_dir = Path(__file__).parent / "artifacts"
    test_data = pd.DataFrame({
        "y_test": y_test,
        "y_pred": y_pred,
    })
    test_data.to_csv(artifacts_dir / "test_predictions.csv", index=False)
    print(f"  Saved test predictions: {artifacts_dir / 'test_predictions.csv'}")

    print("\n" + "=" * 60)
    print("Training complete. Phase 2B done.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
