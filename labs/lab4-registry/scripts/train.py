"""
Sklearn training entry for Lab 4 (runs inside SageMaker).
Expects CSV without header: features..., label (last column).
"""

import argparse
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score


def _load_channel_csv(channel: str, filename: str) -> pd.DataFrame:
    base = f"/opt/ml/input/data/{channel}"
    path = os.path.join(base, filename)
    if not os.path.isfile(path):
        # Single file uploaded to channel root
        files = [f for f in os.listdir(base) if f.endswith(".csv")]
        if len(files) == 1:
            path = os.path.join(base, files[0])
        else:
            raise FileNotFoundError(f"No CSV in {base}, expected {filename}")
    return pd.read_csv(path, header=None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    train_df = _load_channel_csv("train", "train.csv")
    test_df = _load_channel_csv("test", "test.csv")

    X_train = train_df.iloc[:, :-1]
    y_train = train_df.iloc[:, -1]
    X_test = test_df.iloc[:, :-1]
    y_test = test_df.iloc[:, -1]

    model = RandomForestClassifier(
        n_estimators=args.n_estimators, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))

    # Lines parsed by metric_definitions in train_model.py
    print(f"accuracy: {accuracy:.4f}")
    print(f"precision: {precision:.4f}")
    print(f"recall: {recall:.4f}")

    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
    }

    os.makedirs("/opt/ml/model", exist_ok=True)
    with open("/opt/ml/model/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f)

    joblib.dump(model, "/opt/ml/model/model.joblib")
    print("Training complete")
