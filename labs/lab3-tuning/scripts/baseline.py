"""
Baseline training job with default hyperparameters.
Run from the scripts/ directory after exporting BUCKET_NAME and ROLE_ARN.
"""

import os
from pathlib import Path

import boto3
import sagemaker
from sagemaker.sklearn import SKLearn

SCRIPT_DIR = Path(__file__).resolve().parent


def _metric_definitions():
    return [
        {"Name": "rmse", "Regex": "rmse: ([0-9]+\\.[0-9]+)"},
        {"Name": "r2", "Regex": "r2: ([0-9]+\\.[0-9]+)"},
    ]


def run_baseline():
    bucket_name = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")

    if not bucket_name or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN environment variables")
        return None

    boto_session = boto3.Session(region_name="us-east-1")
    session = sagemaker.Session(boto_session=boto_session)

    print("=" * 60)
    print("BASELINE TRAINING JOB (Default Hyperparameters)")
    print("=" * 60)

    estimator = SKLearn(
        entry_point="train.py",
        source_dir=str(SCRIPT_DIR),
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.large",
        framework_version="1.2-1",
        py_version="py3",
        hyperparameters={
            "n-estimators": 100,
            "max-depth": 10,
            "min-samples-split": 2,
            "min-samples-leaf": 1,
        },
        output_path=f"s3://{bucket_name}/baseline-output",
        code_location=f"s3://{bucket_name}/code",
        metric_definitions=_metric_definitions(),
        sagemaker_session=session,
        base_job_name="baseline-diabetes",
    )

    print("\nStarting baseline training job...")
    estimator.fit()

    print("\nBaseline training complete!")
    print(f"Model artifact: {estimator.model_data}")

    training_job_name = estimator.latest_training_job.name
    print(f"Training job name: {training_job_name}")

    with open(SCRIPT_DIR / "baseline_job_name.txt", "w", encoding="utf-8") as f:
        f.write(training_job_name)

    return training_job_name


def get_baseline_metrics(job_name):
    sm = boto3.client("sagemaker", region_name="us-east-1")

    response = sm.describe_training_job(TrainingJobName=job_name)
    metrics = response.get("FinalMetricDataList", [])

    print("\nBaseline Performance (from describe_training_job):")
    if not metrics:
        print("   (no FinalMetricDataList yet — check CloudWatch logs or wait briefly)")
        return {}
    for metric in metrics:
        print(f"   {metric['MetricName']}: {metric['Value']:.4f}")

    return {m["MetricName"]: m["Value"] for m in metrics}


if __name__ == "__main__":
    job = run_baseline()
    if job:
        get_baseline_metrics(job)
