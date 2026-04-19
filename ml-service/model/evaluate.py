"""
MileWatch — Model Evaluation

WHY A SEPARATE EVALUATION SCRIPT:
Training and evaluation should be decoupled. You might retrain with different
hyperparameters but want the same evaluation pipeline. This script:
1. Loads test predictions (from training run)
2. Computes comprehensive metrics
3. Generates diagnostic plots
4. Identifies where the model struggles

USAGE:
    python evaluate.py
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)


def load_predictions(artifacts_dir: Path) -> tuple:
    """Load test predictions from training run."""
    pred_path = artifacts_dir / "test_predictions.csv"
    if not pred_path.exists():
        raise FileNotFoundError(f"Run train.py first. Missing: {pred_path}")

    df = pd.read_csv(pred_path)
    return df["y_test"].values, df["y_pred"].values


def compute_metrics(y_test: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute comprehensive evaluation metrics."""
    metrics = {
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(root_mean_squared_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
        "max_error": float(np.max(np.abs(y_test - y_pred))),
        "median_ae": float(np.median(np.abs(y_test - y_pred))),
    }

    # Bucketed accuracy: how well does the model do in each score range?
    buckets = [
        ("LOW (0.0-0.3)", 0.0, 0.3),
        ("MEDIUM (0.3-0.7)", 0.3, 0.7),
        ("HIGH (0.7-1.0)", 0.7, 1.0),
    ]

    metrics["bucketed"] = {}
    for label, low, high in buckets:
        mask = (y_test >= low) & (y_test < high) if high < 1.0 else (y_test >= low) & (y_test <= high)
        if mask.sum() > 0:
            bucket_mae = float(mean_absolute_error(y_test[mask], y_pred[mask]))
            bucket_count = int(mask.sum())
            metrics["bucketed"][label] = {
                "count": bucket_count,
                "mae": bucket_mae,
            }

    # Classification accuracy at threshold 0.5
    # (If we convert to binary: credible (>= 0.5) vs not credible (< 0.5))
    y_test_binary = (y_test >= 0.5).astype(int)
    y_pred_binary = (y_pred >= 0.5).astype(int)
    binary_accuracy = float(np.mean(y_test_binary == y_pred_binary))
    metrics["binary_accuracy_at_0.5"] = binary_accuracy

    return metrics


def plot_residuals(y_test: np.ndarray, y_pred: np.ndarray, output_dir: Path) -> None:
    """
    Residual analysis plots.

    WHAT TO LOOK FOR:
    - Residuals should be centered around 0
    - No systematic pattern (if there's a curve, the model is missing something)
    - Spread should be roughly uniform across predicted values
    """
    residuals = y_test - y_pred

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Residual Analysis", fontsize=14, fontweight="bold")

    # 1. Predicted vs Actual
    axes[0].scatter(y_test, y_pred, alpha=0.3, s=10, c="#3498db")
    axes[0].plot([0, 1], [0, 1], "r--", alpha=0.8, linewidth=2, label="Perfect prediction")
    axes[0].set_xlabel("Actual Credibility Score")
    axes[0].set_ylabel("Predicted Credibility Score")
    axes[0].set_title("Predicted vs Actual")
    axes[0].legend()
    axes[0].set_xlim(-0.05, 1.05)
    axes[0].set_ylim(-0.05, 1.05)

    # 2. Residual distribution
    axes[1].hist(residuals, bins=50, color="#2ecc71", alpha=0.8, edgecolor="white")
    axes[1].axvline(x=0, color="red", linestyle="--", alpha=0.8)
    axes[1].set_xlabel("Residual (Actual - Predicted)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Residual Distribution")

    # 3. Residuals vs Predicted
    axes[2].scatter(y_pred, residuals, alpha=0.3, s=10, c="#9b59b6")
    axes[2].axhline(y=0, color="red", linestyle="--", alpha=0.8)
    axes[2].set_xlabel("Predicted Score")
    axes[2].set_ylabel("Residual")
    axes[2].set_title("Residuals vs Predicted")

    plt.tight_layout()
    plt.savefig(output_dir / "residual_analysis.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: residual_analysis.png")


def plot_error_by_bucket(metrics: dict, output_dir: Path) -> None:
    """Plot MAE by credibility score bucket."""
    bucketed = metrics.get("bucketed", {})
    if not bucketed:
        return

    labels = list(bucketed.keys())
    maes = [bucketed[l]["mae"] for l in labels]
    counts = [bucketed[l]["count"] for l in labels]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color1 = "#e74c3c"
    color2 = "#3498db"

    bars = ax1.bar(labels, maes, color=color1, alpha=0.8, label="MAE")
    ax1.set_ylabel("Mean Absolute Error", color=color1)
    ax1.set_title("Model Performance by Score Bucket", fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=color1)

    # Add count labels on bars
    for bar, count in zip(bars, counts):
        ax1.text(
            bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.002,
            f"n={count}", ha="center", va="bottom", fontsize=9
        )

    ax2 = ax1.twinx()
    ax2.plot(labels, counts, "o-", color=color2, linewidth=2, markersize=8, label="Sample Count")
    ax2.set_ylabel("Sample Count", color=color2)
    ax2.tick_params(axis="y", labelcolor=color2)

    plt.tight_layout()
    plt.savefig(output_dir / "error_by_bucket.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: error_by_bucket.png")


def plot_feature_importance(artifacts_dir: Path, output_dir: Path) -> None:
    """Plot feature importance from saved JSON."""
    importance_path = artifacts_dir / "feature_importance.json"
    if not importance_path.exists():
        return

    with open(importance_path) as f:
        importance = json.load(f)

    features = list(importance.keys())
    values = list(importance.values())

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(features[::-1], values[::-1], color="#3498db", alpha=0.8)
    ax.set_xlabel("Importance (Gain)")
    ax.set_title("Feature Importance Ranking", fontweight="bold")

    # Add value labels
    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2.,
                f"{val:.3f}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: feature_importance.png")


def main():
    artifacts_dir = Path(__file__).parent / "artifacts"
    output_dir = artifacts_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MileWatch - Model Evaluation")
    print("=" * 60)

    # Load predictions
    y_test, y_pred = load_predictions(artifacts_dir)
    print(f"\nLoaded {len(y_test):,} test predictions")

    # Compute metrics
    metrics = compute_metrics(y_test, y_pred)

    print("\n  Overall Metrics:")
    print(f"  -----------------------------------------")
    print(f"  MAE:              {metrics['mae']:.4f}")
    print(f"  RMSE:             {metrics['rmse']:.4f}")
    print(f"  R2:               {metrics['r2']:.4f}")
    print(f"  Max Error:        {metrics['max_error']:.4f}")
    print(f"  Median AE:        {metrics['median_ae']:.4f}")
    print(f"  Binary Acc @0.5:  {metrics['binary_accuracy_at_0.5']:.4f}")
    print(f"  -----------------------------------------")

    print("\n  Performance by Bucket:")
    for label, data in metrics["bucketed"].items():
        print(f"  {label:<20}  MAE={data['mae']:.4f}  (n={data['count']})")

    # Load CV results if available
    cv_path = artifacts_dir / "cv_results.json"
    if cv_path.exists():
        with open(cv_path) as f:
            cv = json.load(f)
        print(f"\n  Cross-Validation (from training):")
        print(f"  MAE:  {cv['mae_mean']:.4f} +/- {cv['mae_std']:.4f}")
        print(f"  RMSE: {cv['rmse_mean']:.4f} +/- {cv['rmse_std']:.4f}")
        print(f"  R2:   {cv['r2_mean']:.4f} +/- {cv['r2_std']:.4f}")

    # Check targets
    print("\n  Target Check:")
    mae_target = 0.10
    r2_target = 0.85
    mae_pass = metrics["mae"] < mae_target
    r2_pass = metrics["r2"] > r2_target
    print(f"  MAE < {mae_target}:  {'PASS' if mae_pass else 'FAIL'} ({metrics['mae']:.4f})")
    print(f"  R2 > {r2_target}:   {'PASS' if r2_pass else 'FAIL'} ({metrics['r2']:.4f})")

    # Generate plots
    print("\nGenerating evaluation plots...")
    plot_residuals(y_test, y_pred, output_dir)
    plot_error_by_bucket(metrics, output_dir)
    plot_feature_importance(artifacts_dir, output_dir)

    # Save metrics JSON
    metrics_path = artifacts_dir / "evaluation_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n  Saved metrics: {metrics_path}")

    print(f"  Plots saved to: {output_dir}")

    print("\n" + "=" * 60)
    overall = "PASS" if (mae_pass and r2_pass) else "NEEDS ATTENTION"
    print(f"  Evaluation Result: {overall}")
    print("=" * 60)

    return 0 if (mae_pass and r2_pass) else 1


if __name__ == "__main__":
    sys.exit(main())
