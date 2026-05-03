"""
Analyze hyperparameter tuning job results and emit simple plots.
"""

import ast
import json
import os
from pathlib import Path

import boto3
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd
from sagemaker.analytics import HyperparameterTuningJobAnalytics

SCRIPT_DIR = Path(__file__).resolve().parent


def _hp_row(hp_value):
    """Normalize HyperParameters cell from analytics DataFrame."""
    if hp_value is None:
        return {}
    if isinstance(hp_value, dict):
        return hp_value
    if isinstance(hp_value, str):
        try:
            return json.loads(hp_value)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(hp_value)
            except (ValueError, SyntaxError):
                return {}
    return {}


def get_tuning_results(tuning_job_name):
    analytics = HyperparameterTuningJobAnalytics(tuning_job_name)
    df = analytics.dataframe()
    if df.empty:
        return df
    if "FinalObjectiveValue" in df.columns:
        df = df.sort_values("FinalObjectiveValue", ascending=True)
    return df


def print_best_models(df, top_n=5):
    print("\nTOP MODELS (by validation objective):")
    print("-" * 70)

    subset = df.head(top_n).reset_index(drop=True)
    for rank, row in subset.iterrows():
        rmse = row.get("FinalObjectiveValue")
        hp = _hp_row(row.get("HyperParameters"))

        rank_display = rank + 1
        print(f"\nRank {rank_display}: RMSE = {rmse}")
        print("   Parameters:")
        print(f"     n_estimators: {hp.get('n-estimators', 'N/A')}")
        print(f"     max_depth: {hp.get('max-depth', 'N/A')}")
        print(f"     min_samples_split: {hp.get('min-samples-split', 'N/A')}")
        print(f"     min_samples_leaf: {hp.get('min-samples-leaf', 'N/A')}")


def plot_tuning_progress(df, baseline_rmse=None, out_path="tuning_progress.png"):
    if df.empty:
        print("Nothing to plot (empty dataframe).")
        return

    time_col = None
    for candidate in ("TrainingStartTime", "TrainingEndTime"):
        if candidate in df.columns:
            time_col = candidate
            break

    plt.figure(figsize=(12, 6))

    if time_col:
        plot_df = df.copy()
        plot_df[time_col] = pd.to_datetime(plot_df[time_col])
        plot_df = plot_df.sort_values(time_col)
        xs = plot_df[time_col]
    else:
        plot_df = df.reset_index()
        xs = plot_df.index

    plt.plot(xs, plot_df["FinalObjectiveValue"], "o-", alpha=0.7, markersize=8)

    if baseline_rmse:
        plt.axhline(
            y=baseline_rmse,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Baseline RMSE: {baseline_rmse:.4f}",
        )

    plt.xlabel(time_col or "Trial order")
    plt.ylabel("RMSE (lower is better)")
    plt.title("Hyperparameter Tuning Progress")
    if baseline_rmse:
        plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    outp = SCRIPT_DIR / out_path
    plt.savefig(outp)
    plt.close()
    print(f"\nPlot saved to {outp}")


def plot_hyperparameter_impact(df, out_path="hyperparameter_impact.png"):
    working = df.copy()
    working["n_estimators"] = working["HyperParameters"].apply(
        lambda x: int(_hp_row(x).get("n-estimators", 0) or 0)
    )
    working["max_depth"] = working["HyperParameters"].apply(
        lambda x: int(_hp_row(x).get("max-depth", 0) or 0)
    )
    working["min_samples_split"] = working["HyperParameters"].apply(
        lambda x: int(_hp_row(x).get("min-samples-split", 0) or 0)
    )
    working["min_samples_leaf"] = working["HyperParameters"].apply(
        lambda x: int(_hp_row(x).get("min-samples-leaf", 0) or 0)
    )

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    plots = [
        ("n_estimators", "Number of trees", axes[0, 0]),
        ("max_depth", "Max depth", axes[0, 1]),
        ("min_samples_split", "Min samples split", axes[1, 0]),
        ("min_samples_leaf", "Min samples leaf", axes[1, 1]),
    ]
    for key, title, ax in plots:
        ax.scatter(working[key], working["FinalObjectiveValue"], alpha=0.6, s=50)
        ax.set_xlabel(title)
        ax.set_ylabel("RMSE")
        ax.set_title(title + " vs RMSE")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    outp = SCRIPT_DIR / out_path
    plt.savefig(outp)
    plt.close()
    print(f"Hyperparameter plots saved to {outp}")


def main():
    if not os.path.exists(SCRIPT_DIR / "tuning_job_name.txt"):
        print("No tuning job found. Run tuning_config.py first.")
        raise SystemExit(1)

    with open(SCRIPT_DIR / "tuning_job_name.txt", encoding="utf-8") as f:
        tuning_job_name = f.read().strip()

    print("=" * 60)
    print("ANALYZING TUNING RESULTS")
    print("=" * 60)

    df = get_tuning_results(tuning_job_name)
    if df.empty:
        print("Analytics returned zero rows.")
        raise SystemExit(1)

    print(f"\nTotal training jobs listed: {len(df)}")
    print(f"Best RMSE: {df['FinalObjectiveValue'].min():.4f}")
    print(f"Worst RMSE: {df['FinalObjectiveValue'].max():.4f}")

    print_best_models(df)

    baseline_rmse = None
    baseline_path = SCRIPT_DIR / "baseline_job_name.txt"
    if baseline_path.exists():
        with open(baseline_path, encoding="utf-8") as f:
            baseline_job = f.read().strip()
        sm = boto3.client("sagemaker", region_name="us-east-1")
        resp = sm.describe_training_job(TrainingJobName=baseline_job)
        for m in resp.get("FinalMetricDataList", []) or []:
            if m.get("MetricName") == "rmse":
                baseline_rmse = m["Value"]
                print(f"\nBaseline RMSE: {baseline_rmse:.4f}")
                impr = (
                    (baseline_rmse - df["FinalObjectiveValue"].min())
                    / baseline_rmse
                    * 100
                )
                print(f"Improvement vs best tuned: {impr:.1f}%")

    plot_tuning_progress(df, baseline_rmse)
    plot_hyperparameter_impact(df)

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
