"""
Deploy the Approved model package as a realtime sklearn endpoint with DataCapture enabled,
then update to duplicated blue/green variants (defaults 90/10) mirroring Lab 6’s teaching demo.

Requires: approve_model_package.py wrote approved_model_package_arn.txt.
Needs: CAPTURE_BUCKET_NAME + SAGEMAKER_ROLE_ARN.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import boto3
import sagemaker
from sagemaker.deserializers import JSONDeserializer
from sagemaker.model_monitor import DataCaptureConfig
from sagemaker.serializers import CSVSerializer
from sagemaker.sklearn import SKLearnModel

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _approved_package_arn(sm) -> str:
    gf = SCRIPT_DIR / "approved_model_package_arn.txt"
    if gf.is_file():
        return gf.read_text(encoding="utf-8").strip()
    mpg = SCRIPT_DIR / "model_package_group.txt"
    if not mpg.is_file():
        print("ERROR: Approve workflow missing (approve_model_package.py).")
        raise SystemExit(1)
    group = mpg.read_text(encoding="utf-8").strip()
    resp = sm.list_model_packages(
        ModelPackageGroupName=group,
        ModelApprovalStatus="Approved",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=1,
    )
    rows = resp.get("ModelPackageSummaryList") or []
    if not rows:
        print("ERROR: No Approved model package.")
        raise SystemExit(1)
    return rows[0]["ModelPackageArn"]


def main():
    role = (os.environ.get("SAGEMAKER_ROLE_ARN") or os.environ.get("ROLE_ARN") or "").strip()
    cap_bucket = (os.environ.get("CAPTURE_BUCKET_NAME") or "").strip()
    if not role or not cap_bucket:
        print("ERROR: Set SAGEMAKER_ROLE_ARN (or ROLE_ARN) and CAPTURE_BUCKET_NAME.")
        raise SystemExit(1)

    sm = boto3.client("sagemaker", region_name=REGION)
    pkg_arn = _approved_package_arn(sm)
    ctr = sm.describe_model_package(ModelPackageArn=pkg_arn)["InferenceSpecification"][
        "Containers"
    ][0]
    model_uri = ctr["ModelDataUrl"]
    print(f"Model tarball: {model_uri}")

    session = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))

    capture_uri = os.environ.get("CAPSTONE_CAPTURE_PREFIX", f"s3://{cap_bucket}/lab8/data-capture/")
    if not capture_uri.endswith("/"):
        capture_uri += "/"

    endpoint_name = os.environ.get(
        "CAPSTONE_ENDPOINT_NAME", f"lab8-capstone-rt-{int(time.time())}"
    )

    sk = SKLearnModel(
        model_data=model_uri,
        role=role,
        entry_point="inference.py",
        source_dir=str(SCRIPT_DIR),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=session,
    )
    print("Deploying baseline single-variant endpoint with capture (often several minutes)...")
    predictor = sk.deploy(
        initial_instance_count=1,
        instance_type="ml.t2.medium",
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
        endpoint_name=endpoint_name,
        data_capture_config=DataCaptureConfig(
            enable_capture=True,
            sampling_percentage=100,
            destination_s3_uri=capture_uri,
            capture_options=["Input", "Output"],
            csv_content_types=["text/csv"],
            json_content_types=["application/json"],
        ),
    )

    ep_name = predictor.endpoint_name
    cfg_name = sm.describe_endpoint(EndpointName=ep_name)["EndpointConfigName"]
    cfg = sm.describe_endpoint_config(EndpointConfigName=cfg_name)
    base_variant = cfg["ProductionVariants"][0]["ModelName"]
    container = sm.describe_model(ModelName=base_variant)["PrimaryContainer"]

    ts = int(time.time())
    blue_model = f"lab8-canary-blue-{ts}"
    green_model = f"lab8-canary-green-{ts}"
    for name in (blue_model, green_model):
        sm.create_model(
            ModelName=name,
            ExecutionRoleArn=role,
            PrimaryContainer=container,
        )

    canary_cfg = f"lab8-canary-cfg-{ts}"
    bw = float(os.environ.get("CAPSTONE_BLUE_WEIGHT", "90"))
    gw = float(os.environ.get("CAPSTONE_GREEN_WEIGHT", "10"))
    eb_kwargs: dict = {
        "EndpointConfigName": canary_cfg,
        "ProductionVariants": [
            {
                "VariantName": "blue",
                "ModelName": blue_model,
                "InstanceType": "ml.t2.medium",
                "InitialInstanceCount": 1,
                "InitialVariantWeight": bw,
            },
            {
                "VariantName": "green",
                "ModelName": green_model,
                "InstanceType": "ml.t2.medium",
                "InitialInstanceCount": 1,
                "InitialVariantWeight": gw,
            },
        ],
    }
    dcc = cfg.get("DataCaptureConfig")
    if dcc:
        eb_kwargs["DataCaptureConfig"] = dcc

    sm.create_endpoint_config(**eb_kwargs)
    print(f"Applying canary config {canary_cfg} weights blue={bw} green={gw}...")
    sm.update_endpoint(EndpointName=ep_name, EndpointConfigName=canary_cfg)
    sm.get_waiter("endpoint_in_service").wait(
        EndpointName=ep_name,
        WaiterConfig={"Delay": 15, "MaxAttempts": 60},
    )

    (SCRIPT_DIR / "endpoint_name.txt").write_text(ep_name, encoding="utf-8")
    (SCRIPT_DIR / "capture_s3_uri.txt").write_text(capture_uri, encoding="utf-8")
    (SCRIPT_DIR / "model_data_uri.txt").write_text(model_uri, encoding="utf-8")
    (SCRIPT_DIR / "canary_endpoint_config.txt").write_text(canary_cfg, encoding="utf-8")
    (SCRIPT_DIR / "canary_models.json").write_text(
        json.dumps({"blue_model": blue_model, "green_model": green_model}, indent=2),
        encoding="utf-8",
    )
    print("Canary realtime endpoint ready:")
    print(ep_name)


if __name__ == "__main__":
    main()
