"""
Training script that accepts hyperparameters.
Runs inside the SageMaker sklearn container.
"""

import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=10)
    parser.add_argument("--min-samples-split", type=int, default=2)
    parser.add_argument("--min-samples-leaf", type=int, default=1)
    args = parser.parse_args()

    print("=" * 60)
    print("HYPERPARAMETER TUNING TRAINING JOB")
    print("=" * 60)
    print(f"n_estimators: {args.n_estimators}")
    print(f"max_depth: {args.max_depth}")
    print(f"min_samples_split: {args.min_samples_split}")
    print(f"min_samples_leaf: {args.min_samples_leaf}")

    diabetes = load_diabetes()
    X = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
    y = pd.Series(diabetes.target, name="target")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    model = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_split=args.min_samples_split,
        min_samples_leaf=args.min_samples_leaf,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    # Lines parsed by SageMaker metric_definitions / tuning objective
    print(f"rmse: {rmse:.4f}")
    print(f"r2: {r2:.4f}")

    metrics = {"rmse": rmse, "r2": r2}
    os.makedirs("/opt/ml/model", exist_ok=True)

    with open("/opt/ml/model/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f)

    joblib.dump(model, "/opt/ml/model/model.joblib")
    print("Training complete")
