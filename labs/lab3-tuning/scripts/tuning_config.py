"""
Configure and launch a SageMaker hyperparameter tuning job for sklearn RandomForest.
"""

import os
from pathlib import Path

import boto3
import sagemaker
from sagemaker.sklearn import SKLearn
from sagemaker.tuner import HyperparameterTuner, IntegerParameter

SCRIPT_DIR = Path(__file__).resolve().parent


def _metric_definitions():
    return [
        {"Name": "rmse", "Regex": "rmse: ([0-9]+\\.[0-9]+)"},
        {"Name": "r2", "Regex": "r2: ([0-9]+\\.[0-9]+)"},
    ]


def create_tuner():
    bucket_name = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")

    if not bucket_name or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN environment variables")
        return None

    boto_session = boto3.Session(region_name="us-east-1")
    session = sagemaker.Session(boto_session=boto_session)

    print("=" * 60)
    print("HYPERPARAMETER TUNING CONFIGURATION")
    print("=" * 60)

    estimator = SKLearn(
        entry_point="train.py",
        source_dir=str(SCRIPT_DIR),
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.large",
        framework_version="1.2-1",
        py_version="py3",
        output_path=f"s3://{bucket_name}/tuning-output",
        code_location=f"s3://{bucket_name}/code-tuning",
        metric_definitions=_metric_definitions(),
        sagemaker_session=session,
        base_job_name="tuning-diabetes",
    )

    hyperparameter_ranges = {
        "n-estimators": IntegerParameter(50, 200),
        "max-depth": IntegerParameter(3, 15),
        "min-samples-split": IntegerParameter(2, 20),
        "min-samples-leaf": IntegerParameter(1, 10),
    }

    print("\nHyperparameter Search Space:")
    for param, range_obj in hyperparameter_ranges.items():
        print(f"   {param}: {range_obj.min_value} - {range_obj.max_value}")

    tuner = HyperparameterTuner(
        estimator=estimator,
        objective_metric_name="rmse",
        hyperparameter_ranges=hyperparameter_ranges,
        objective_type="Minimize",
        max_jobs=10,
        max_parallel_jobs=2,
        early_stopping_type="Auto",
    )

    print("\nTuner configuration created")
    print(f"   Total jobs: {tuner.max_jobs}")
    print(f"   Parallel jobs: {tuner.max_parallel_jobs}")
    print("   Objective: Minimize rmse")

    return tuner


def start_tuning(tuner):
    print("\nStarting hyperparameter tuning job (10 child jobs; budget ~15–25 min)...")
    tuner.fit(wait=True)

    desc = tuner.describe()
    name = desc["HyperParameterTuningJobName"]
    print("\nTuning job finished")
    print(f"Tuning job name: {name}")

    with open(SCRIPT_DIR / "tuning_job_name.txt", "w", encoding="utf-8") as f:
        f.write(name)

    return name


if __name__ == "__main__":
    t = create_tuner()
    if t:
        start_tuning(t)
