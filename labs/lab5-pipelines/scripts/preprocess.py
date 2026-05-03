"""
SageMaker Processing entry: generate synthetic churn-style data and write train/test CSVs.
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-test-split-ratio", type=float, default=0.2)
    args = parser.parse_args()

    print("=" * 50)
    print("STEP 1: PREPROCESSING DATA")
    print("=" * 50)

    np.random.seed(42)
    n_samples = 5000

    data = pd.DataFrame(
        {
            "tenure": np.random.randint(1, 72, n_samples),
            "monthly_charges": np.random.uniform(20, 120, n_samples),
            "support_tickets": np.random.poisson(1, n_samples),
            "payment_delays": np.random.poisson(0.5, n_samples),
            "contract_type": np.random.choice(
                ["Month-to-month", "One year", "Two year"], n_samples
            ),
        }
    )

    data = pd.get_dummies(data, columns=["contract_type"])

    churn_prob = (
        (data["support_tickets"] > 2) * 0.3
        + (data["payment_delays"] > 1) * 0.3
        + (data["contract_type_Month-to-month"] == 1) * 0.4
    )
    data["churn"] = (np.random.random(n_samples) < churn_prob).astype(int)

    print(f"Original data shape: {data.shape}")
    print(f"Churn rate: {data['churn'].mean():.2%}")

    X = data.drop("churn", axis=1)
    y = data["churn"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.train_test_split_ratio, random_state=42
    )

    train_data = pd.concat([X_train, y_train], axis=1)
    test_data = pd.concat([X_test, y_test], axis=1)

    train_output_path = "/opt/ml/processing/train"
    test_output_path = "/opt/ml/processing/test"

    os.makedirs(train_output_path, exist_ok=True)
    os.makedirs(test_output_path, exist_ok=True)

    train_data.to_csv(f"{train_output_path}/train.csv", index=False, header=False)
    test_data.to_csv(f"{test_output_path}/test.csv", index=False, header=False)

    print(f"Training data saved: {train_data.shape}")
    print(f"Test data saved: {test_data.shape}")
    print("Preprocessing complete.")
