"""
Deploy SageMaker sklearn Multi-Model Endpoint (Lab 9).

Uses MultiDataModel with a bootstrap SKLearnModel (shared inference.py).
Models must live under the same prefix: s3://BUCKET/models/{name}/model.tar.gz
Invocation uses TargetModel = "{name}/model.tar.gz".
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import boto3
import sagemaker
from sagemaker.deserializers import JSONDeserializer
from sagemaker.multidatamodel import MultiDataModel
from sagemaker.serializers import CSVSerializer
from sagemaker.sklearn import SKLearnModel

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"


def _session():
    boto_sess = boto3.Session(region_name=REGION)
    return sagemaker.Session(boto_session=boto_sess)


def deploy_mme(bucket: str, role_arn: str, endpoint_name: str, session) -> MultiDataModel:
    prefix_uri = f"s3://{bucket}/models/"
    bootstrap = f"s3://{bucket}/models/model-v1/model.tar.gz"

    print("=" * 60)
    print("DEPLOYING MULTI-MODEL ENDPOINT (sklearn)")
    print("=" * 60)
    print(f"Endpoint: {endpoint_name}")
    print(f"Artifacts prefix: {prefix_uri}")

    base = SKLearnModel(
        model_data=bootstrap,
        role=role_arn,
        entry_point="inference.py",
        source_dir=str(SCRIPT_DIR),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=session,
    )

    mdm = MultiDataModel(
        name=f"lab9-mme-{int(time.time())}",
        model_data_prefix=prefix_uri,
        model=base,
        sagemaker_session=session,
    )

    mdm.deploy(
        initial_instance_count=1,
        instance_type="ml.m5.large",
        endpoint_name=endpoint_name,
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
        wait=True,
    )
    print("\n✅ Multi-model endpoint ready.")
    return mdm


def main():
    bucket = os.environ.get("BUCKET_NAME", "").strip()
    role = os.environ.get("ROLE_ARN", "").strip()
    if not bucket or not role:
        raise SystemExit("ERROR: export BUCKET_NAME and ROLE_ARN.")

    sess = _session()
    endpoint = os.environ.get("LAB9_MME_NAME", f"lab9-mme-{int(time.time())}")
    deploy_mme(bucket, role, endpoint, sess)
    outfile = SCRIPT_DIR / "mme_endpoint_name.txt"
    outfile.write_text(endpoint, encoding="utf-8")
    print(f"Saved: {outfile}")


if __name__ == "__main__":
    main()
