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
    args = parser.parse_args()

    print("=" * 50)
    print("Starting SageMaker Training Job")
    print("=" * 50)

    # Load data
    diabetes = load_diabetes()
    X = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
    y = pd.Series(diabetes.target, name="target")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training rows: {X_train.shape[0]}")
    print(f"Test rows: {X_test.shape[0]}")

    # Train model
    model = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "mse": float(mse),
        "rmse": float(rmse),
        "r2": float(r2),
    }

    print("Model Performance:")
    print(f"RMSE: {rmse:.2f}")
    print(f"R2 Score: {r2:.4f}")

    # Save model and metrics
    os.makedirs("/opt/ml/model", exist_ok=True)

    with open("/opt/ml/model/metrics.json", "w") as f:
        json.dump(metrics, f)

    joblib.dump(model, "/opt/ml/model/model.joblib")
    print("Training complete")
