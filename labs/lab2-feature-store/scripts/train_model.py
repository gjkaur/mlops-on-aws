"""
Train a simple classifier using customer features queried from offline store via Athena.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

# Scripts are run from this directory (`python train_model.py`)
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from query_offline import run_athena_query


def fetch_training_data_from_athena(database, table_name, s3_output):
    """Fetch training data from offline store using Athena."""
    query = f"""
    SELECT
        customer_id,
        age,
        avg_monthly_spend,
        tenure_months,
        support_tickets
    FROM "{database}"."{table_name}"
    """

    df = run_athena_query(query, database, s3_output)

    if df is None:
        print("Failed to fetch data from Athena")
        return None

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


if __name__ == "__main__":
    bucket_name = os.environ.get("BUCKET_NAME")

    if not bucket_name:
        print("ERROR: Set BUCKET_NAME environment variable")
        raise SystemExit(1)

    with open("customer_fg_name.txt", "r", encoding="utf-8") as f:
        customer_fg_name = f.read().strip()

    customer_table = customer_fg_name.lower().replace("-", "_")
    database = "sagemaker_featurestore"
    s3_output = f"s3://{bucket_name}/athena-results/"

    print("=" * 50)
    print("Training Churn Prediction Model (demo)")
    print("=" * 50)

    print("\n1. Fetching training data from Feature Store (Athena)...")
    df = fetch_training_data_from_athena(database, customer_table, s3_output)

    if df is None or len(df) == 0:
        print("No data found. Ensure ingest completed and offline data is cataloged.")
        raise SystemExit(1)

    print(f"   Retrieved {len(df)} records")

    np.random.seed(42)
    df["churn"] = (
        (df["support_tickets"] > 2) * 0.4
        + (df["tenure_months"] < 12) * 0.3
        + (df["avg_monthly_spend"] > 150) * 0.3
    )
    df["churn"] = (df["churn"] > np.random.random(len(df))).astype(int)

    print(f"   Churn rate: {df['churn'].mean():.1%}")

    feature_cols = [
        "age",
        "avg_monthly_spend",
        "tenure_months",
        "support_tickets",
    ]
    X = df[feature_cols]
    y = df["churn"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("\n2. Training Random Forest Classifier...")
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)

    print("\n3. Model Performance:")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")

    print("\n4. Feature Importance:")
    for name, importance in zip(feature_cols, model.feature_importances_):
        print(f"   {name}: {importance:.4f}")

    print("\n✅ Model training complete!")
    print("\nInsight: Offline features surfaced via Athena can feed downstream training.")
