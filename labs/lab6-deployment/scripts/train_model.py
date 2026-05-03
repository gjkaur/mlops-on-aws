"""
Generate binary data, upload to S3, run SageMaker sklearn training — writes artifact URIs for deploy (Lab 6).
"""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import pandas as pd
import sagemaker
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sagemaker.sklearn import SKLearn

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def main():
    bucket = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")
    if not bucket or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN (Terraform outputs).")
        raise SystemExit(1)

    boto_sess = boto3.Session(region_name=REGION)
    session = sagemaker.Session(boto_session=boto_sess)

    print("Generating synthetic data...")
    X, y = make_classification(
        n_samples=2000,
        n_features=10,
        n_informative=8,
        n_redundant=2,
        random_state=42,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    train_df = pd.DataFrame(X_train)
    train_df["target"] = y_train
    test_df = pd.DataFrame(X_test)
    test_df["target"] = y_test

    train_path = SCRIPT_DIR / "train.csv"
    test_path = SCRIPT_DIR / "test.csv"
    train_df.to_csv(train_path, index=False, header=False)
    test_df.to_csv(test_path, index=False, header=False)

    train_s3 = session.upload_data(
        str(train_path),
        bucket=bucket,
        key_prefix="lab6/training-data",
    )
    test_s3 = session.upload_data(
        str(test_path),
        bucket=bucket,
        key_prefix="lab6/testing-data",
    )
    print(f"Training CSV: {train_s3}")
    print(f"Test CSV: {test_s3}")

    print("=" * 60)
    print("TRAINING MODEL FOR DEPLOYMENT")
    print("=" * 60)

    estimator = SKLearn(
        entry_point="train.py",
        source_dir=str(SCRIPT_DIR),
        role=role_arn,
        framework_version="1.2-1",
        py_version="py3",
        instance_count=1,
        instance_type="ml.m5.large",
        hyperparameters={"n-estimators": 100},
        output_path=f"s3://{bucket}/lab6-output",
        code_location=f"s3://{bucket}/lab6-code",
        sagemaker_session=session,
        base_job_name="lab6-deployment-train",
    )

    estimator.fit({"train": train_s3, "test": test_s3})

    model_data = estimator.model_data
    job_name = estimator.latest_training_job.name
    print("Training complete")
    print(f"Model artifact: {model_data}")
    print(f"Training job name: {job_name}")

    (SCRIPT_DIR / "model_data_uri.txt").write_text(model_data, encoding="utf-8")
    (SCRIPT_DIR / "training_job_name.txt").write_text(job_name, encoding="utf-8")


if __name__ == "__main__":
    main()
