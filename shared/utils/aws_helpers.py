"""Shared AWS utilities for all labs."""

import boto3


def get_training_job_metrics(job_name, region="us-east-1"):
    """Get final metrics from a SageMaker training job."""
    sm = boto3.client("sagemaker", region_name=region)
    response = sm.describe_training_job(TrainingJobName=job_name)
    return response.get("FinalMetricDataList", [])


def get_model_artifact_uri(job_name, region="us-east-1"):
    """Get S3 URI of the model artifact."""
    sm = boto3.client("sagemaker", region_name=region)
    response = sm.describe_training_job(TrainingJobName=job_name)
    return response.get("ModelArtifacts", {}).get("S3ModelArtifacts")


def download_model(uri, local_path="./model.tar.gz", region="us-east-1"):
    """Download model artifact from S3."""
    s3 = boto3.client("s3", region_name=region)
    # Parse s3://bucket/key from URI
    parts = uri.replace("s3://", "").split("/")
    bucket = parts[0]
    key = "/".join(parts[1:])
    s3.download_file(bucket, key, local_path)
    return local_path
