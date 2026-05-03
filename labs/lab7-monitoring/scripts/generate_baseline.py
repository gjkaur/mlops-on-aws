"""
Run a data-quality baselining job on feature-only CSV (matches captured endpoint inputs).
Persists statistics and constraint S3 URIs for create_monitoring_schedule.py.
"""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import sagemaker
from sagemaker.model_monitor import DefaultModelMonitor
from sagemaker.model_monitor.dataset_format import DatasetFormat

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _baseline_dataset_uri_s3(bucket: str) -> str:
    bf = SCRIPT_DIR / "baseline_features_s3_uri.txt"
    if bf.is_file():
        return bf.read_text(encoding="utf-8").strip()
    return f"s3://{bucket}/lab7/baseline-input/baseline_features.csv"


def main():
    bucket = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")
    if not bucket or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN.")
        raise SystemExit(1)

    baseline_ds = _baseline_dataset_uri_s3(bucket)
    print(f"Baseline dataset (CSV, no header, 10 feature columns): {baseline_ds}")

    boto_sess = boto3.Session(region_name=REGION)
    sm_sess = sagemaker.Session(boto_session=boto_sess)

    out_prefix = os.environ.get(
        "LAB7_BASELINE_OUTPUT_URI", f"s3://{bucket}/lab7/baseline-output/"
    )
    if not out_prefix.endswith("/"):
        out_prefix += "/"

    monitor = DefaultModelMonitor(
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        volume_size_in_gb=30,
        max_runtime_in_seconds=3600,
        base_job_name="lab7-data-quality-baseline",
        sagemaker_session=sm_sess,
    )

    print("=" * 60)
    print("BASELINE JOB (typically 5–15 minutes)")
    print("=" * 60)

    monitor.suggest_baseline(
        baseline_dataset=baseline_ds,
        dataset_format=DatasetFormat.csv(header=False),
        output_s3_uri=out_prefix,
        wait=True,
        logs=True,
    )

    stats_uri = monitor.baseline_statistics().file_s3_uri
    cons_uri = monitor.suggested_constraints().file_s3_uri

    (SCRIPT_DIR / "statistics_s3_uri.txt").write_text(stats_uri, encoding="utf-8")
    (SCRIPT_DIR / "constraints_s3_uri.txt").write_text(cons_uri, encoding="utf-8")
    (SCRIPT_DIR / "baseline_output_s3_uri.txt").write_text(out_prefix, encoding="utf-8")

    print("Baseline complete.")
    print(f"statistics: {stats_uri}")
    print(f"constraints: {cons_uri}")


if __name__ == "__main__":
    main()
