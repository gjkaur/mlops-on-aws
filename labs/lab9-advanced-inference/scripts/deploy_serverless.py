"""
Deploy SageMaker Serverless Inference (Lab 9).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import boto3
import sagemaker
from sagemaker.deserializers import JSONDeserializer
from sagemaker.serializers import CSVSerializer
from sagemaker.serverless import ServerlessInferenceConfig
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


def deploy_serverless(
    model_uri: str, role_arn: str, endpoint_name: str, session: sagemaker.Session
):
    serverless_cfg = ServerlessInferenceConfig(memory_size_in_mb=2048, max_concurrency=10)

    print("=" * 60)
    print("DEPLOYING SERVERLESS ENDPOINT")
    print("=" * 60)
    print(f"Endpoint: {endpoint_name}")
    print("Memory MB: 2048 | Max concurrency: 10")
    print(model_uri)

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
        serverless_inference_config=serverless_cfg,
        endpoint_name=endpoint_name,
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
    )
    print("\n✅ Serverless endpoint ready (cold start ~5–22s typical).")
    return predictor


def main():
    bucket = os.environ.get("BUCKET_NAME", "").strip()
    role = os.environ.get("ROLE_ARN", "").strip()
    if not bucket or not role:
        raise SystemExit("ERROR: export BUCKET_NAME and ROLE_ARN.")

    uri = _default_model_uri(bucket)
    sess = _session()

    endpoint = os.environ.get(
        "LAB9_SERVERLESS_NAME", f"lab9-serverless-{int(time.time())}"
    )
    pred = deploy_serverless(uri, role, endpoint, sess)
    outfile = SCRIPT_DIR / "serverless_endpoint_name.txt"
    outfile.write_text(pred.endpoint_name, encoding="utf-8")
    print(f"Saved: {outfile}")


if __name__ == "__main__":
    main()
