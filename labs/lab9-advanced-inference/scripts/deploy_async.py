"""
Deploy SageMaker Asynchronous Inference (Lab 9).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import boto3
import sagemaker
from sagemaker.async_inference import AsyncInferenceConfig
from sagemaker.deserializers import JSONDeserializer
from sagemaker.serializers import CSVSerializer
from sagemaker.sklearn import SKLearnModel

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"


def _session():
    boto_sess = boto3.Session(region_name=REGION)
    return sagemaker.Session(boto_session=boto_sess)


def _default_model_uri(bucket: str) -> str:
    env = os.environ.get("MODEL_S3_URI", "").strip()
    if env:
        return env
    return f"s3://{bucket}/models/model-v2/model.tar.gz"


def deploy_async(model_uri: str, role_arn: str, bucket: str, endpoint_name: str, session):
    out_prefix = f"s3://{bucket}/async-output/"
    async_cfg = AsyncInferenceConfig(
        output_path=out_prefix,
        max_concurrent_invocations_per_instance=4,
    )

    print("=" * 60)
    print("DEPLOYING ASYNCHRONOUS ENDPOINT")
    print("=" * 60)
    print(f"Endpoint: {endpoint_name}")
    print(f"Results: {out_prefix}")

    model = SKLearnModel(
        model_data=model_uri,
        role=role_arn,
        entry_point="inference.py",
        source_dir=str(SCRIPT_DIR),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=session,
    )

    predictor = model.deploy(
        async_inference_config=async_cfg,
        instance_count=1,
        instance_type="ml.m5.large",
        endpoint_name=endpoint_name,
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
    )
    print("\n✅ Asynchronous endpoint ready.")
    return predictor


def main():
    bucket = os.environ.get("BUCKET_NAME", "").strip()
    role = os.environ.get("ROLE_ARN", "").strip()
    if not bucket or not role:
        raise SystemExit("ERROR: export BUCKET_NAME and ROLE_ARN.")

    uri = _default_model_uri(bucket)
    sess = _session()
    endpoint = os.environ.get(
        "LAB9_ASYNC_NAME", f"lab9-async-{int(time.time())}"
    )
    pred = deploy_async(uri, role, bucket, endpoint, sess)
    outfile = SCRIPT_DIR / "async_endpoint_name.txt"
    outfile.write_text(pred.endpoint_name, encoding="utf-8")
    print(f"Saved: {outfile}")


if __name__ == "__main__":
    main()
