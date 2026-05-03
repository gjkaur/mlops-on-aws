"""
SageMaker Processing entry: load trained model artifact (tar.gz), score test set, write evaluation.json.
"""

from __future__ import annotations

import json
import os
import tarfile
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

if __name__ == "__main__":
    print("=" * 50)
    print("STEP 3: EVALUATING MODEL")
    print("=" * 50)

    model_dir = Path("/opt/ml/processing/model")
    for path in model_dir.glob("*.tar.gz"):
        with tarfile.open(path, "r:gz") as tar:
            tar.extractall(model_dir)

    model_path = model_dir / "model.joblib"
    if not model_path.is_file():
        raise FileNotFoundError(f"Expected {model_path} after extracting model.tar.gz")

    model = joblib.load(model_path)

    test_df = pd.read_csv("/opt/ml/processing/test/test.csv", header=None)
    X_test = test_df.iloc[:, :-1]
    y_test = test_df.iloc[:, -1]

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

    print("Final evaluation metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

    out_dir = Path("/opt/ml/processing/evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    eval_path = out_dir / "evaluation.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f)

    print("Evaluation complete.")
