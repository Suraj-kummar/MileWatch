"""
MileWatch — Exploratory Data Analysis

WHY THIS STEP:
Before training a model, we MUST verify:
1. Feature distributions per profile look realistic
2. Cross-feature correlations exist (not independent)
3. Credibility score distributions overlap between profiles (no trivial separation)
4. No data quality issues (nulls, outliers, impossible values)

If any of these fail, we fix the generator — NOT the model.

USAGE:
    python eda.py                           # Runs all analyses, saves plots
    python eda.py --data ./generated/delivery_attempts.csv
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/CI environments

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# ── Plot configuration ─────────────────────────────────────────────────
PROFILE_COLORS = {
    "GENUINE_ATTEMPT": "#2ecc71",
    "GENUINE_BORDERLINE": "#f39c12",
    "LAZY_SKIP": "#e74c3c",
    "SHIFT_END_DUMP": "#9b59b6",
    "SYSTEMATIC_FRAUD": "#1a1a2e",
}

FEATURE_COLUMNS = [
    "gps_distance_m",
    "time_gap_minutes",
    "call_made",
    "is_cod",
    "exec_historical_fake_rate",
    "minutes_to_shift_end",
    "pincode_tier",
]

FEATURE_LABELS = {
    "gps_distance_m": "GPS Distance (m)",
    "time_gap_minutes": "Time Gap (min)",
    "call_made": "Call Made",
    "is_cod": "COD Order",
    "exec_historical_fake_rate": "Historical Fake Rate",
    "minutes_to_shift_end": "Min to Shift End",
    "pincode_tier": "Pincode Tier",
}


def setup_plot_style():
    """Configure matplotlib for clean, professional plots."""
    plt.style.use("seaborn-v0_8-darkgrid")
    plt.rcParams.update({
        "figure.facecolor": "#f8f9fa",
        "axes.facecolor": "#ffffff",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "figure.dpi": 120,
    })


def plot_feature_distributions(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Plot distribution of each feature, colored by profile.

    WHAT TO LOOK FOR:
    - GPS distance: GENUINE should cluster < 500m, FRAUD should be 2000m+
    - Time gap: GENUINE ~35min, SHIFT_END_DUMP < 10min
    - Call made: GENUINE ~85% yes, FRAUD < 20% yes
    - COD: FRAUD profiles should have higher COD ratio
    """
    continuous_features = [
        "gps_distance_m", "time_gap_minutes",
        "exec_historical_fake_rate", "minutes_to_shift_end"
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Feature Distributions by Profile", fontsize=14, fontweight="bold")

    for ax, feature in zip(axes.flatten(), continuous_features):
        for profile_name, color in PROFILE_COLORS.items():
            subset = df[df["profile"] == profile_name][feature]
            if len(subset) > 0:
                ax.hist(
                    subset, bins=40, alpha=0.5, label=profile_name,
                    color=color, density=True, edgecolor="none"
                )
        ax.set_xlabel(FEATURE_LABELS[feature])
        ax.set_ylabel("Density")
        ax.legend(fontsize=7)

    plt.tight_layout()
    plt.savefig(output_dir / "feature_distributions_continuous.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: feature_distributions_continuous.png")

    # Binary / categorical features
    binary_features = ["call_made", "is_cod", "pincode_tier"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Binary/Categorical Features by Profile", fontsize=14, fontweight="bold")

    for ax, feature in zip(axes, binary_features):
        pivot = df.groupby(["profile", feature]).size().unstack(fill_value=0)
        pivot_pct = pivot.div(pivot.sum(axis=1), axis=0)
        pivot_pct.plot(kind="bar", ax=ax, color=["#3498db", "#e74c3c", "#2ecc71"][:len(pivot_pct.columns)])
        ax.set_title(FEATURE_LABELS[feature])
        ax.set_xlabel("")
        ax.set_ylabel("Proportion")
        ax.tick_params(axis="x", rotation=30)
        ax.legend(title=feature, fontsize=7)

    plt.tight_layout()
    plt.savefig(output_dir / "feature_distributions_categorical.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: feature_distributions_categorical.png")


def plot_correlation_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Plot correlation matrix for all features + credibility score.

    WHAT TO LOOK FOR:
    - GPS distance should be NEGATIVELY correlated with credibility
    - Call made should be POSITIVELY correlated with credibility
    - Historical fake rate should be NEGATIVELY correlated with credibility
    - Features should NOT be independent — we need cross-correlations
    """
    corr_cols = FEATURE_COLUMNS + ["credibility_score"]
    corr_matrix = df[corr_cols].corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

    sns.heatmap(
        corr_matrix,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        vmin=-1, vmax=1,
        square=True,
        ax=ax,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8, "label": "Correlation"},
    )
    ax.set_title("Feature Correlation Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "correlation_heatmap.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: correlation_heatmap.png")


def plot_score_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Plot credibility score distribution, overall and per profile.

    WHAT TO LOOK FOR:
    - Overall distribution should NOT be bimodal with clear separation
    - Profiles should OVERLAP in the 0.3-0.7 range (realistic ambiguity)
    - GENUINE: mostly 0.7-1.0
    - FRAUD: mostly 0.0-0.3
    - BORDERLINE/LAZY: spread across 0.2-0.7
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Overall distribution
    axes[0].hist(df["credibility_score"], bins=50, color="#3498db", alpha=0.8, edgecolor="white")
    axes[0].set_xlabel("Credibility Score")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Overall Score Distribution", fontweight="bold")
    axes[0].axvline(x=0.3, color="#e74c3c", linestyle="--", alpha=0.7, label="Low/Med threshold")
    axes[0].axvline(x=0.7, color="#2ecc71", linestyle="--", alpha=0.7, label="Med/High threshold")
    axes[0].legend()

    # Per profile
    for profile_name, color in PROFILE_COLORS.items():
        subset = df[df["profile"] == profile_name]["credibility_score"]
        axes[1].hist(
            subset, bins=30, alpha=0.5, label=profile_name,
            color=color, density=True, edgecolor="none"
        )
    axes[1].set_xlabel("Credibility Score")
    axes[1].set_ylabel("Density")
    axes[1].set_title("Score Distribution by Profile", fontweight="bold")
    axes[1].legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_dir / "score_distribution.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: score_distribution.png")


def plot_feature_vs_score(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Scatter plots: each feature vs credibility score.

    WHAT TO LOOK FOR:
    - Clear trends (GPS ↑ → score ↓, call_made = 1 → score ↑)
    - But with enough scatter that the relationship isn't trivial
    """
    continuous_features = [
        "gps_distance_m", "time_gap_minutes",
        "exec_historical_fake_rate", "minutes_to_shift_end"
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Feature vs Credibility Score", fontsize=14, fontweight="bold")

    for ax, feature in zip(axes.flatten(), continuous_features):
        # Sample for performance (plotting 15K points is slow)
        sample = df.sample(n=min(3000, len(df)), random_state=42)

        for profile_name, color in PROFILE_COLORS.items():
            subset = sample[sample["profile"] == profile_name]
            ax.scatter(
                subset[feature], subset["credibility_score"],
                alpha=0.3, s=8, c=color, label=profile_name
            )
        ax.set_xlabel(FEATURE_LABELS[feature])
        ax.set_ylabel("Credibility Score")
        ax.legend(fontsize=6, markerscale=3)

    plt.tight_layout()
    plt.savefig(output_dir / "feature_vs_score.png", bbox_inches="tight")
    plt.close()
    print("  [OK] Saved: feature_vs_score.png")


def run_sanity_checks(df: pd.DataFrame) -> bool:
    """
    Automated sanity checks on the generated data.
    Returns True if all checks pass.
    """
    print("\n" + "=" * 60)
    print("SANITY CHECKS")
    print("=" * 60)

    all_passed = True

    # Check 1: No nulls
    null_count = df.isnull().sum().sum()
    status = "PASS" if null_count == 0 else "FAIL"
    print(f"  [{status}] No null values: {null_count} nulls found")
    if null_count > 0:
        all_passed = False

    # Check 2: Score in [0, 1]
    score_valid = df["credibility_score"].between(0.0, 1.0).all()
    status = "PASS" if score_valid else "FAIL"
    print(f"  [{status}] Credibility scores in [0, 1]")
    if not score_valid:
        all_passed = False

    # Check 3: GPS distance positive
    gps_valid = (df["gps_distance_m"] >= 0).all()
    status = "PASS" if gps_valid else "FAIL"
    print(f"  [{status}] GPS distance >= 0")
    if not gps_valid:
        all_passed = False

    # Check 4: Binary features are actually binary
    for col in ["call_made", "is_cod"]:
        is_binary = df[col].isin([0, 1]).all()
        status = "PASS" if is_binary else "FAIL"
        print(f"  [{status}] {col} is binary (0/1)")
        if not is_binary:
            all_passed = False

    # Check 5: Pincode tier in {1, 2, 3}
    tier_valid = df["pincode_tier"].isin([1, 2, 3]).all()
    status = "PASS" if tier_valid else "FAIL"
    print(f"  [{status}] Pincode tier in {{1, 2, 3}}")
    if not tier_valid:
        all_passed = False

    # Check 6: GENUINE_ATTEMPT avg score > LAZY_SKIP avg score
    genuine_mean = df[df["profile"] == "GENUINE_ATTEMPT"]["credibility_score"].mean()
    lazy_mean = df[df["profile"] == "LAZY_SKIP"]["credibility_score"].mean()
    order_valid = genuine_mean > lazy_mean
    status = "PASS" if order_valid else "FAIL"
    print(f"  [{status}] GENUINE mean ({genuine_mean:.3f}) > LAZY_SKIP mean ({lazy_mean:.3f})")
    if not order_valid:
        all_passed = False

    # Check 7: GENUINE avg GPS < SHIFT_END_DUMP avg GPS
    genuine_gps = df[df["profile"] == "GENUINE_ATTEMPT"]["gps_distance_m"].mean()
    dump_gps = df[df["profile"] == "SHIFT_END_DUMP"]["gps_distance_m"].mean()
    gps_order = genuine_gps < dump_gps
    status = "PASS" if gps_order else "FAIL"
    print(f"  [{status}] GENUINE avg GPS ({genuine_gps:.0f}m) < SHIFT_END avg GPS ({dump_gps:.0f}m)")
    if not gps_order:
        all_passed = False

    # Check 8: LAZY_SKIP has higher COD ratio than GENUINE
    genuine_cod = df[df["profile"] == "GENUINE_ATTEMPT"]["is_cod"].mean()
    lazy_cod = df[df["profile"] == "LAZY_SKIP"]["is_cod"].mean()
    cod_valid = lazy_cod > genuine_cod
    status = "PASS" if cod_valid else "FAIL"
    print(f"  [{status}] LAZY_SKIP COD ratio ({lazy_cod:.2f}) > GENUINE COD ratio ({genuine_cod:.2f})")
    if not cod_valid:
        all_passed = False

    # Check 9: Feature correlations with score have expected signs
    corr_with_score = df[FEATURE_COLUMNS + ["credibility_score"]].corr()["credibility_score"]
    expected_signs = {
        "gps_distance_m": "negative",
        "call_made": "positive",
        "exec_historical_fake_rate": "negative",
        "minutes_to_shift_end": "positive",
    }
    for feat, expected in expected_signs.items():
        actual_corr = corr_with_score[feat]
        sign_correct = (actual_corr < 0) if expected == "negative" else (actual_corr > 0)
        status = "PASS" if sign_correct else "FAIL"
        print(f"  [{status}] {feat} correlation with score is {expected} ({actual_corr:.3f})")
        if not sign_correct:
            all_passed = False

    print("=" * 60)
    final = "ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED"
    print(f"  Result: {final}")
    print("=" * 60)

    return all_passed


def print_profile_summary(df: pd.DataFrame) -> None:
    """Print detailed per-profile statistics."""
    print("\n" + "=" * 60)
    print("PER-PROFILE STATISTICS")
    print("=" * 60)

    for profile_name in df["profile"].unique():
        subset = df[df["profile"] == profile_name]
        print(f"\n  -- {profile_name} ({len(subset):,} records) --")
        print(f"     Score:     mean={subset['credibility_score'].mean():.3f}  "
              f"std={subset['credibility_score'].std():.3f}  "
              f"range=[{subset['credibility_score'].min():.3f}, {subset['credibility_score'].max():.3f}]")
        print(f"     GPS:       mean={subset['gps_distance_m'].mean():.0f}m  "
              f"std={subset['gps_distance_m'].std():.0f}m")
        print(f"     Time gap:  mean={subset['time_gap_minutes'].mean():.1f}min")
        print(f"     Call made: {subset['call_made'].mean():.1%}")
        print(f"     COD:       {subset['is_cod'].mean():.1%}")
        print(f"     Fake rate: mean={subset['exec_historical_fake_rate'].mean():.3f}")
        print(f"     Shift end: mean={subset['minutes_to_shift_end'].mean():.0f}min")


def main():
    parser = argparse.ArgumentParser(description="MileWatch EDA")
    parser.add_argument(
        "--data", type=str,
        default=str(Path(__file__).parent / "generated" / "delivery_attempts.csv"),
        help="Path to delivery attempts CSV"
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        print("Run generator.py first.")
        return 1

    print(f"MileWatch EDA")
    print(f"  Data: {data_path}")

    df = pd.read_csv(data_path)
    print(f"  Loaded {len(df):,} records\n")

    # Output directory for plots
    output_dir = data_path.parent / "plots"
    output_dir.mkdir(exist_ok=True)

    setup_plot_style()

    # Run all analyses
    print("Generating plots...")
    plot_feature_distributions(df, output_dir)
    plot_correlation_heatmap(df, output_dir)
    plot_score_distribution(df, output_dir)
    plot_feature_vs_score(df, output_dir)

    # Profile summary
    print_profile_summary(df)

    # Sanity checks
    passed = run_sanity_checks(df)

    print(f"\nPlots saved to: {output_dir}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
