"""
Deploy SageMaker realtime endpoint from sklearn model artifact (Lab 6).
Reads model_data_uri.txt written by train_model.py.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import boto3
import sagemaker
from sagemaker.deserializers import JSONDeserializer
from sagemaker.serializers import CSVSerializer
from sagemaker.sklearn import SKLearnModel

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _model_data_uri() -> str:
    state = SCRIPT_DIR / "model_data_uri.txt"
    if state.is_file():
        return state.read_text(encoding="utf-8").strip()

    print("WARN: model_data_uri.txt missing; discovering latest lab6-deployment training job...")
    sm = boto3.client("sagemaker", region_name=REGION)
    resp = sm.list_training_jobs(
        NameContains="lab6-deployment-train",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=1,
    )
    rows = resp.get("TrainingJobSummaries") or []
    if not rows:
        return ""
    name = rows[0]["TrainingJobName"]
    detail = sm.describe_training_job(TrainingJobName=name)
    return detail["ModelArtifacts"]["S3ModelArtifacts"]


def main():
    bucket = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")
    if not bucket or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN.")
        raise SystemExit(1)

    artifact = _model_data_uri()
    if not artifact:
        print("ERROR: Run train_model.py first (no artifact).")
        raise SystemExit(1)
    print(f"Model artifact: {artifact}")

    boto_sess = boto3.Session(region_name=REGION)
    session = sagemaker.Session(boto_session=boto_sess)

    endpoint_name = os.environ.get(
        "LAB6_ENDPOINT_NAME", f"lab6-rt-endpoint-{int(time.time())}"
    )

    model = SKLearnModel(
        model_data=artifact,
        role=role_arn,
        entry_point="inference.py",
        source_dir=str(SCRIPT_DIR),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=session,
    )

    print("=" * 60)
    print("DEPLOY REAL-TIME ENDPOINT")
    print(f"endpoint_name={endpoint_name}")
    print("Provisioning often takes ~5–10 minutes...")
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type="ml.t2.medium",
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
        endpoint_name=endpoint_name,
    )

    print("Endpoint deployed")
    print("Realtime client sends CSV feature rows with length matching training (10).")
    (SCRIPT_DIR / "endpoint_name.txt").write_text(predictor.endpoint_name, encoding="utf-8")
    (SCRIPT_DIR / "model_data_uri.txt").write_text(artifact, encoding="utf-8")

    # Store variant name for Application Auto Scaling (SDK default)
    sm = boto3.client("sagemaker", region_name=REGION)
    ep = sm.describe_endpoint(EndpointName=predictor.endpoint_name)
    variant = ep["ProductionVariants"][0]["VariantName"]
    (SCRIPT_DIR / "endpoint_variant_name.txt").write_text(variant, encoding="utf-8")
    print(f"VariantName (for scaling): {variant}")


if __name__ == "__main__":
    main()
