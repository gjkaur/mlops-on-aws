"""
Delete SageMaker artefacts (pipeline, EB rule, monitor, alarms, realtime endpoint configs/models).
Leaves S3 buckets + IAM for `terraform destroy` (matching Lab 7 cleanup philosophy).
"""

from __future__ import annotations

import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from sagemaker.model_monitor import DefaultModelMonitor

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _cw():
    return boto3.client("cloudwatch", region_name=REGION)


def _sm():
    return boto3.client("sagemaker", region_name=REGION)


def _events():
    return boto3.client("events", region_name=REGION)


def _delete_alarm():
    fp = SCRIPT_DIR / "cloudwatch_alarm_name.txt"
    if not fp.is_file():
        return
    name = fp.read_text(encoding="utf-8").strip()
    try:
        _cw().delete_alarms(AlarmNames=[name])
        print(f"Deleted CloudWatch alarm {name}")
    except Exception as exc:
        print(f"Alarm cleanup: {exc}")


def _delete_monitor_schedule(sn: str) -> None:
    try:
        sm_sess = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))
        mon = DefaultModelMonitor.attach(sn, sagemaker_session=sm_sess)
        try:
            mon.stop_monitoring_schedule()
        except Exception as exc:
            print(f"stop_monitoring_schedule ({sn}): {exc}")
        mon.delete_monitoring_schedule()
        print(f"Deleted DQ monitoring schedule {sn}")
    except Exception as exc:
        print(f"Monitor attach/delete failed ({sn}): {exc}; trying API...")
        try:
            _sm().delete_monitoring_schedule(MonitoringScheduleName=sn)
            print(f"Deleted schedule via API ({sn})")
        except Exception as exc2:
            print(f"Schedule cleanup skipped: {exc2}")


def _delete_model(name: str) -> None:
    try:
        _sm().delete_model(ModelName=name)
        print(f"Deleted SageMaker model {name}")
    except Exception as exc:
        print(f"Model delete skipped ({name}): {exc}")


def _delete_endpoint(name: str) -> None:
    sm = _sm()
    try:
        sm.delete_endpoint(EndpointName=name)
        print(f"Deleting endpoint {name}")
        sm.get_waiter("endpoint_deleted").wait(
            EndpointName=name,
            WaiterConfig={"Delay": 15, "MaxAttempts": 40},
        )
    except Exception as exc:
        print(f"Endpoint delete: {exc}")


def _delete_config(cfg: str) -> None:
    try:
        _sm().delete_endpoint_config(EndpointConfigName=cfg)
        print(f"Deleted endpoint config {cfg}")
    except Exception as exc:
        print(f"Endpoint config delete skipped ({cfg}): {exc}")


def _purge_endpoint_related() -> None:
    ef = SCRIPT_DIR / "endpoint_name.txt"
    if not ef.is_file():
        return
    ep_name = ef.read_text(encoding="utf-8").strip()
    sm = _sm()

    extras: set[str] = set()
    jf = SCRIPT_DIR / "canary_models.json"
    if jf.is_file():
        try:
            payload = json.loads(jf.read_text(encoding="utf-8"))
            extras.update(payload.get(k) for k in ("blue_model", "green_model") if payload.get(k))
        except json.JSONDecodeError:
            pass

    try:
        desc = sm.describe_endpoint(EndpointName=ep_name)
        cfg = desc["EndpointConfigName"]
        for v in desc.get("ProductionVariants", []) or []:
            extras.add(v["ModelName"])
        _delete_endpoint(ep_name)
        _delete_config(cfg)
        for mname in sorted({m for m in extras if m}):
            _delete_model(mname)
    except ClientError as exc:
        print(f"SageMaker endpoint purge skipped ({ep_name}): {exc}")


def _delete_pipeline(name: str) -> None:
    sm = _sm()
    try:
        sm.delete_pipeline(PipelineName=name)
        print(f"Deleted pipeline definition {name}")
    except Exception as exc:
        print(f"Pipeline delete skipped ({name}): {exc}")


def _delete_trigger() -> None:
    rf = SCRIPT_DIR / "eventbridge_rule_name.txt"
    rule = rf.read_text(encoding="utf-8").strip() if rf.is_file() else ""
    if not rule:
        return
    evt = _events()
    try:
        evt.remove_targets(Rule=rule, Ids=["SageMakerPipelineTarget"], Force=True)
        evt.delete_rule(Name=rule)
        print(f"Deleted EventBridge rule {rule}")
    except Exception as exc:
        print(f"EventBridge cleanup: {exc}")


def main():
    print("=" * 60)
    print("LAB 8 CAPSTONE CLEANUP (SAGEMAKER + EVENTBRIDGE + CW)")

    _delete_alarm()

    sf = SCRIPT_DIR / "schedule_name.txt"
    if sf.is_file():
        _delete_monitor_schedule(sf.read_text(encoding="utf-8").strip())

    _purge_endpoint_related()

    _delete_trigger()

    pf = SCRIPT_DIR / "pipeline_name.txt"
    if pf.is_file():
        _delete_pipeline(pf.read_text(encoding="utf-8").strip())

    stale = (
        "pipeline_name.txt",
        "model_package_group.txt",
        "endpoint_name.txt",
        "capture_s3_uri.txt",
        "model_data_uri.txt",
        "approved_model_package_arn.txt",
        "canary_models.json",
        "canary_endpoint_config.txt",
        "cloudwatch_alarm_name.txt",
        "schedule_name.txt",
        "eventbridge_rule_name.txt",
        "pipeline_execution_arn.txt",
        "pipeline_terminal_status.txt",
        "preprocess_train_s3_uri.txt",
    )
    for name in stale:
        fp = SCRIPT_DIR / name
        if fp.is_file():
            fp.unlink()

    print("Local breadcrumbs cleared.")
    print("Next: terraform destroy inside infrastructure/")


if __name__ == "__main__":
    main()
