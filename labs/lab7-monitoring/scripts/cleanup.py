"""Remove monitoring schedule, endpoint, model config, optional CloudWatch alarm — Lab 7."""

from __future__ import annotations

from pathlib import Path

import boto3
import sagemaker
from botocore.exceptions import ClientError
from sagemaker.model_monitor import DefaultModelMonitor

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _delete_schedule(name: str) -> None:
    sm_sess = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))
    try:
        mon = DefaultModelMonitor.attach(name, sagemaker_session=sm_sess)
        try:
            mon.stop_monitoring_schedule()
        except Exception as exc:  # noqa: BLE001
            print(f"stop_monitoring_schedule: {exc}")
        mon.delete_monitoring_schedule()
        print(f"Deleted monitoring schedule {name}")
    except Exception as exc:  # noqa: BLE001
        print(f"Schedule cleanup via attach failed ({exc}); trying API delete…")
        sm = boto3.client("sagemaker", region_name=REGION)
        try:
            sm.delete_monitoring_schedule(MonitoringScheduleName=name)
            print(f"Deleted monitoring schedule {name} (API)")
        except Exception as exc2:  # noqa: BLE001
            print(f"Could not delete schedule: {exc2}")


def _delete_endpoint_and_related(sm, endpoint_name: str) -> None:
    try:
        sm.delete_endpoint(EndpointName=endpoint_name)
        print(f"Deleting endpoint {endpoint_name}...")
        waiter = sm.get_waiter("endpoint_deleted")
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={"Delay": 15, "MaxAttempts": 40},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Endpoint delete: {exc}")


def _delete_config(sm, cfg_name: str) -> None:
    try:
        sm.delete_endpoint_config(EndpointConfigName=cfg_name)
        print(f"Deleted EndpointConfig {cfg_name}")
    except Exception as exc:  # noqa: BLE001
        print(f"Endpoint config delete skipped ({cfg_name}): {exc}")


def _delete_model(sm, name: str) -> None:
    try:
        sm.delete_model(ModelName=name)
        print(f"Deleted model {name}")
    except Exception as exc:  # noqa: BLE001
        print(f"Model delete skipped ({name}): {exc}")


def _delete_alarm(name: str) -> None:
    cw = boto3.client("cloudwatch", region_name=REGION)
    try:
        cw.delete_alarms(AlarmNames=[name])
        print(f"Deleted CloudWatch alarm {name}")
    except Exception as exc:  # noqa: BLE001
        print(f"Alarm delete skipped: {exc}")


def main():
    print("=" * 60)
    print("LAB 7 CLEANUP")

    af = SCRIPT_DIR / "cloudwatch_alarm_name.txt"
    if af.is_file():
        _delete_alarm(af.read_text(encoding="utf-8").strip())

    sf = SCRIPT_DIR / "schedule_name.txt"
    if sf.is_file():
        _delete_schedule(sf.read_text(encoding="utf-8").strip())

    ef = SCRIPT_DIR / "endpoint_name.txt"
    if ef.is_file():
        endpoint_name = ef.read_text(encoding="utf-8").strip()
        sm = boto3.client("sagemaker", region_name=REGION)
        try:
            desc = sm.describe_endpoint(EndpointName=endpoint_name)
            cfg = desc["EndpointConfigName"]
            variants = desc.get("ProductionVariants") or []
            variant_models = [v["ModelName"] for v in variants]
            _delete_endpoint_and_related(sm, endpoint_name)
            _delete_config(sm, cfg)
            for m in sorted(set(variant_models)):
                _delete_model(sm, m)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            print(f"SageMaker endpoint cleanup skipped ({code}): {exc}")

    for name in (
        "endpoint_name.txt",
        "endpoint_variant_name.txt",
        "schedule_name.txt",
        "cloudwatch_alarm_name.txt",
        "model_data_uri.txt",
        "training_job_name.txt",
        "statistics_s3_uri.txt",
        "constraints_s3_uri.txt",
        "baseline_output_s3_uri.txt",
        "baseline_features_s3_uri.txt",
        "capture_s3_uri.txt",
    ):
        fp = SCRIPT_DIR / name
        if fp.is_file():
            fp.unlink()

    for fp in SCRIPT_DIR.glob("*.csv"):
        fp.unlink()

    print("Local state cleared. Run terraform destroy from infrastructure/ to drop the sandbox.")


if __name__ == "__main__":
    main()
