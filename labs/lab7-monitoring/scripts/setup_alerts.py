"""
Create a CloudWatch alarm on SageMaker Model Monitor **feature baseline drift** for the first
tabular column reported in baseline statistics.json (namespace /aws/sagemaker/Endpoints/data-metric).

Reads schedule_name.txt, statistics_s3_uri.txt, endpoint_name.txt. Optional SNS action when
`SNS_TOPIC_ARN` is set (same value as Terraform output `sns_topic_arn`).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import boto3

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"
CW_NS = "/aws/sagemaker/Endpoints/data-metric"


def _feature_name_first(statistics_uri: str) -> str:
    parsed = urlparse(statistics_uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    s3 = boto3.client("s3", region_name=REGION)
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    blob = json.loads(body)
    features = blob.get("features") or []
    if not features:
        return "0"
    name = features[0].get("name")
    return name if isinstance(name, str) and name else str(features[0])


def put_drift_alarm(
    endpoint_name: str,
    schedule_name: str,
    feature_col: str,
    sns_arn: str | None,
    threshold: float = 0,
) -> str:
    cw = boto3.client("cloudwatch", region_name=REGION)
    safe = "".join(c if c.isalnum() or c == "-" else "-" for c in endpoint_name[-16:])
    alarm_name = f"lab7-drift-{safe}"

    dims = [
        {"Name": "EndpointName", "Value": endpoint_name},
        {"Name": "ScheduleName", "Value": schedule_name},
    ]
    metric = f"feature_baseline_drift_{feature_col}"

    cw.put_metric_alarm(
        AlarmName=alarm_name,
        AlarmDescription="Data-quality baseline drift (first feature vs training baseline).",
        MetricName=metric,
        Namespace=CW_NS,
        Statistic="Sum",
        Period=3600,
        EvaluationPeriods=1,
        Threshold=threshold,
        ComparisonOperator="GreaterThanThreshold",
        TreatMissingData="notBreaching",
        AlarmActions=[sns_arn] if sns_arn else [],
        Dimensions=dims,
    )
    print(f"CloudWatch alarm: {alarm_name}")
    print(f"  Namespace={CW_NS}")
    print(f"  MetricName={metric}")
    print(f"  Dimensions={dims}")
    return alarm_name


def main():
    for name in ("endpoint_name.txt", "schedule_name.txt", "statistics_s3_uri.txt"):
        if not (SCRIPT_DIR / name).is_file():
            print(f"ERROR: Missing {name}. Run prerequisite scripts.")
            raise SystemExit(1)

    endpoint_name = (SCRIPT_DIR / "endpoint_name.txt").read_text(encoding="utf-8").strip()
    schedule_name = (SCRIPT_DIR / "schedule_name.txt").read_text(encoding="utf-8").strip()
    stats_uri = (SCRIPT_DIR / "statistics_s3_uri.txt").read_text(encoding="utf-8").strip()

    sns_arn = (os.environ.get("SNS_TOPIC_ARN") or "").strip() or None

    feat = os.environ.get("LAB7_ALARM_FEATURE_COL") or _feature_name_first(stats_uri)
    print(f"Baseline first feature column name: {feat}")

    thr = float(os.environ.get("LAB7_DRIFT_ALARM_THRESHOLD", "0"))

    print("=" * 60)
    print("SETUP DRIFT CLOUDWATCH ALARM + SNS ACTION")
    print("=" * 60)

    alarm = put_drift_alarm(endpoint_name, schedule_name, feat, sns_arn, threshold=thr)
    (SCRIPT_DIR / "cloudwatch_alarm_name.txt").write_text(alarm, encoding="utf-8")

    print("\nIf you passed SNS_TOPIC_ARN, confirm the Terraform email subscription in your inbox.")
    print("Alarm fires when hourly monitoring publishes Sum(metric) strictly above threshold.")


if __name__ == "__main__":
    main()
