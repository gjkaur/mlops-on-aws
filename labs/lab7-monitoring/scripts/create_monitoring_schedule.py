"""
Create a SageMaker Model Monitor **data-quality** schedule for the deployed endpoint.

Uses statistics/constraints URIs emitted by generate_baseline.py.

Optional: set LAB7_MONITOR_NOW=1 for a one-shot NOW schedule (analysis window defaults
to statistics from roughly the last calendar day).

Default: hourly CloudWatch-aligned cron (`cron(0 * ? * * *)`).
"""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import sagemaker
from sagemaker.model_monitor import CronExpressionGenerator, DefaultModelMonitor, EndpointInput

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def main():
    bucket = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")
    if not bucket or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN.")
        raise SystemExit(1)

    en_f = SCRIPT_DIR / "endpoint_name.txt"
    if not en_f.is_file():
        print("ERROR: Run deploy_with_capture.py first.")
        raise SystemExit(1)
    endpoint_name = en_f.read_text(encoding="utf-8").strip()

    sf = SCRIPT_DIR / "statistics_s3_uri.txt"
    cf = SCRIPT_DIR / "constraints_s3_uri.txt"
    if not sf.is_file() or not cf.is_file():
        print("ERROR: Run generate_baseline.py first.")
        raise SystemExit(1)
    stats_uri = sf.read_text(encoding="utf-8").strip()
    cons_uri = cf.read_text(encoding="utf-8").strip()

    schedule_name = os.environ.get(
        "LAB7_SCHEDULE_NAME", f"lab7-drift-sched-{endpoint_name[-12:]}"
    )
    reports = os.environ.get("LAB7_REPORTS_URI", f"s3://{bucket}/lab7/reports/")
    if not reports.endswith("/"):
        reports += "/"

    boto_sess = boto3.Session(region_name=REGION)
    sm_sess = sagemaker.Session(boto_session=boto_sess)

    monitor = DefaultModelMonitor(
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        volume_size_in_gb=30,
        max_runtime_in_seconds=3600,
        base_job_name="lab7-monitoring-job",
        sagemaker_session=sm_sess,
    )

    cron = CronExpressionGenerator.hourly()
    now_kw: dict = {}
    if os.environ.get("LAB7_MONITOR_NOW"):
        cron = CronExpressionGenerator.now()
        now_kw["data_analysis_start_time"] = os.environ.get("LAB7_NOW_START", "-P1D")
        now_kw["data_analysis_end_time"] = os.environ.get("LAB7_NOW_END", "-PT1S")

    ep_in = EndpointInput(
        endpoint_name=endpoint_name,
        destination="/opt/ml/processing/input/endpoint",
    )

    print("=" * 60)
    print("CREATE DATA QUALITY MONITORING SCHEDULE")
    print(f"schedule={schedule_name}")
    print(f"cron_expression={cron}")
    print(f"reports_s3_uri={reports}")
    print("=" * 60)

    monitor.create_monitoring_schedule(
        endpoint_input=ep_in,
        output_s3_uri=reports,
        statistics=stats_uri,
        constraints=cons_uri,
        monitor_schedule_name=schedule_name,
        schedule_cron_expression=cron,
        enable_cloudwatch_metrics=True,
        **now_kw,
    )

    (SCRIPT_DIR / "schedule_name.txt").write_text(schedule_name, encoding="utf-8")
    print(f"Monitoring schedule active: {schedule_name}")


if __name__ == "__main__":
    main()
