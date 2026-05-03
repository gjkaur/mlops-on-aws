"""
Build a DQ baseline from preprocessing train.csv (drops label column), register monitoring schedule + drift alarm.

Env: REPORTS_BUCKET_NAME (baseline + schedule outputs), preprocess_train via preprocess_train_s3_uri.txt from run_pipeline.py.
Also: CAPTURE_BUCKET_NAME unused here (captures configured at deploy_canary deploy time).
"""

from __future__ import annotations

import io
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import boto3
import pandas as pd
import sagemaker
from sagemaker.model_monitor import (
    CronExpressionGenerator,
    DefaultModelMonitor,
    EndpointInput,
)
from sagemaker.model_monitor.dataset_format import DatasetFormat

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"
CW_NS = "/aws/sagemaker/Endpoints/data-metric"


def _put_feature_baseline(s3_client, bucket: str, train_uri: str, key_out: str) -> str:
    parsed = urlparse(train_uri)
    body = s3_client.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))["Body"].read()
    df = pd.read_csv(io.BytesIO(body), header=None)
    feats = df.iloc[:, :-1]
    buf = io.StringIO()
    feats.to_csv(buf, index=False, header=False)
    s3_client.put_object(
        Bucket=bucket,
        Key=key_out,
        Body=buf.getvalue().encode("utf-8"),
    )
    return f"s3://{bucket}/{key_out}"


def _first_stat_feature(statistics_uri: str) -> str:
    parsed = urlparse(statistics_uri)
    s3 = boto3.client("s3", region_name=REGION)
    raw = s3.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))["Body"].read().decode("utf-8")
    blob = json.loads(raw)
    feats = blob.get("features") or []
    if not feats:
        return "0"
    name = feats[0].get("name")
    return name if isinstance(name, str) and name else str(feats[0])


def main():
    reports = os.environ.get("REPORTS_BUCKET_NAME", "").strip()
    role = (os.environ.get("SAGEMAKER_ROLE_ARN") or os.environ.get("ROLE_ARN") or "").strip()
    if not reports or not role:
        print("ERROR: REPORTS_BUCKET_NAME and SAGEMAKER_ROLE_ARN required.")
        raise SystemExit(1)

    trf = SCRIPT_DIR / "preprocess_train_s3_uri.txt"
    if not trf.is_file():
        print("ERROR: preprocess_train_s3_uri.txt missing (run run_pipeline.py to completion first).")
        raise SystemExit(1)
    train_uri = trf.read_text(encoding="utf-8").strip()

    en_f = SCRIPT_DIR / "endpoint_name.txt"
    if not en_f.is_file():
        print("ERROR: endpoint_name.txt missing (deploy_canary.py).")
        raise SystemExit(1)
    endpoint_name = en_f.read_text(encoding="utf-8").strip()

    sns = os.environ.get("SNS_TOPIC_ARN", "").strip() or None
    key_feat = os.environ.get("CAPSTONE_ALARM_FEATURE_COL", "").strip()

    s3_cli = boto3.client("s3", region_name=REGION)
    feat_uri = _put_feature_baseline(s3_cli, reports, train_uri, "lab8/baseline/feature_only.csv")
    baseline_out = f"s3://{reports}/lab8/baseline-job-output/"
    print(f"Feature-only baseline input: {feat_uri}")

    sm_sess = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))

    base_mon = DefaultModelMonitor(
        role=role,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        volume_size_in_gb=30,
        max_runtime_in_seconds=3600,
        base_job_name="lab8-capstone-baseline",
        sagemaker_session=sm_sess,
    )
    base_mon.suggest_baseline(
        baseline_dataset=feat_uri,
        dataset_format=DatasetFormat.csv(header=False),
        output_s3_uri=baseline_out,
        wait=True,
        logs=True,
    )
    stats_uri = base_mon.baseline_statistics().file_s3_uri
    cons_uri = base_mon.suggested_constraints().file_s3_uri

    feat_name = key_feat or _first_stat_feature(stats_uri)
    print(f"Drift telemetry feature column baseline[0]={feat_name}")

    sched_mon = DefaultModelMonitor(
        role=role,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        volume_size_in_gb=30,
        max_runtime_in_seconds=3600,
        base_job_name="lab8-capstone-monitor",
        sagemaker_session=sm_sess,
    )

    cron = CronExpressionGenerator.hourly()
    now_kw: dict = {}
    if os.environ.get("LAB8_MONITOR_NOW"):
        cron = CronExpressionGenerator.now()
        now_kw["data_analysis_start_time"] = os.environ.get("LAB8_NOW_START", "-P1D")
        now_kw["data_analysis_end_time"] = os.environ.get("LAB8_NOW_END", "-PT1S")

    sfx = endpoint_name.replace("_", "")[-16:] if len(endpoint_name) >= 8 else "capstone"
    schedule_name = os.environ.get("CAPSTONE_SCHEDULE_NAME") or f"lab8-dq-{sfx}-{int(time.time())}"
    reports_out = f"s3://{reports}/lab8/monitoring-reports/"
    schedule_name = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in schedule_name)[:59]

    ep_in = EndpointInput(
        endpoint_name=endpoint_name,
        destination="/opt/ml/processing/input/endpoint",
    )

    sched_mon.create_monitoring_schedule(
        endpoint_input=ep_in,
        output_s3_uri=reports_out,
        statistics=stats_uri,
        constraints=cons_uri,
        monitor_schedule_name=schedule_name,
        schedule_cron_expression=cron,
        enable_cloudwatch_metrics=True,
        **now_kw,
    )

    cw = boto3.client("cloudwatch", region_name=REGION)
    alarm_name_raw = f"lab8-drift-{endpoint_name[-24:]}-{int(time.time())}"
    alarm_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in alarm_name_raw)[:255]
    cw.put_metric_alarm(
        AlarmName=alarm_name,
        AlarmDescription="Capstone DQ baseline drift (Sum > threshold).",
        MetricName=f"feature_baseline_drift_{feat_name}",
        Namespace=CW_NS,
        Statistic="Sum",
        Period=3600,
        EvaluationPeriods=1,
        Threshold=float(os.environ.get("LAB8_DRIFT_ALARM_THRESHOLD", "0")),
        ComparisonOperator="GreaterThanThreshold",
        TreatMissingData="notBreaching",
        AlarmActions=[sns] if sns else [],
        Dimensions=[
            {"Name": "EndpointName", "Value": endpoint_name},
            {"Name": "ScheduleName", "Value": schedule_name},
        ],
    )

    (SCRIPT_DIR / "schedule_name.txt").write_text(schedule_name, encoding="utf-8")
    (SCRIPT_DIR / "cloudwatch_alarm_name.txt").write_text(alarm_name, encoding="utf-8")
    print(f"Monitoring schedule: {schedule_name}")
    print(f"CloudWatch alarm: {alarm_name}")


if __name__ == "__main__":
    main()
