"""
SageMaker Training entry: train RandomForest, persist model.joblib and metrics.json under /opt/ml/model.
"""

from __future__ import annotations

import argparse
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=10)
    args = parser.parse_args()

    print("=" * 50)
    print("STEP 2: TRAINING MODEL")
    print("=" * 50)
    print(
        f"Hyperparameters: n_estimators={args.n_estimators}, max_depth={args.max_depth}"
    )

    train_df = pd.read_csv("/opt/ml/input/data/train/train.csv", header=None)
    test_df = pd.read_csv("/opt/ml/input/data/test/test.csv", header=None)

    X_train = train_df.iloc[:, :-1]
    y_train = train_df.iloc[:, -1]
    X_test = test_df.iloc[:, :-1]
    y_test = test_df.iloc[:, -1]

    print(f"Training data: {X_train.shape}")
    print(f"Test data (holdout channel): {X_test.shape}")

    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(
            precision_score(y_test, y_pred, zero_division=0)
        ),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "auc": float(roc_auc_score(y_test, y_pred_proba)),
    }

    print("Model performance (test channel):")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

    os.makedirs("/opt/ml/model", exist_ok=True)
    with open("/opt/ml/model/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f)

    joblib.dump(model, "/opt/ml/model/model.joblib")
    print("Training complete.")
