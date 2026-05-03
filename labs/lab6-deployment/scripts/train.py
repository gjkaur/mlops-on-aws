"""
SageMaker training entry — sklearn RandomForest on CSV channels (Lab 6).
"""

from __future__ import annotations

import argparse
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    print("STEP: TRAINING (Lab 6 deployment)")
    print(f"n_estimators={args.n_estimators}")

    train_df = pd.read_csv("/opt/ml/input/data/train/train.csv", header=None)
    test_df = pd.read_csv("/opt/ml/input/data/test/test.csv", header=None)

    X_train = train_df.iloc[:, :-1]
    y_train = train_df.iloc[:, -1]
    X_test = test_df.iloc[:, :-1]
    y_test = test_df.iloc[:, -1]

    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    os.makedirs("/opt/ml/model", exist_ok=True)
    with open("/opt/ml/model/metrics.json", "w", encoding="utf-8") as fh:
        json.dump({"accuracy": float(acc)}, fh)

    joblib.dump(model, "/opt/ml/model/model.joblib")
    print(f"accuracy: {acc:.4f}")
    print("Training complete.")
