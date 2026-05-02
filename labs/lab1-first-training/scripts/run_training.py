import os

import boto3
import sagemaker
from sagemaker.sklearn import SKLearn

# Get configuration from environment
bucket_name = os.environ.get("BUCKET_NAME")
role_arn = os.environ.get("ROLE_ARN")

if not bucket_name or not role_arn:
    print("ERROR: BUCKET_NAME and ROLE_ARN must be set.")
    print("Run the following commands after terraform apply:")
    print("  export BUCKET_NAME=$(terraform output -raw s3_bucket_name)")
    print("  export ROLE_ARN=$(terraform output -raw sagemaker_role_arn)")
    raise SystemExit(1)

print(f"Using bucket: {bucket_name}")
print(f"Using role: {role_arn}")

# SageMaker session
boto_session = boto3.Session(region_name="us-east-1")
session = sagemaker.Session(boto_session=boto_session)

# Training job configuration
estimator = SKLearn(
    entry_point="train.py",
    role=role_arn,
    instance_count=1,
    instance_type="ml.m5.large",
    framework_version="1.2-1",
    py_version="py3",
    hyperparameters={
        "n-estimators": 100,
        "max-depth": 10,
    },
    output_path=f"s3://{bucket_name}/output",
    code_location=f"s3://{bucket_name}/code",
    base_job_name="diabetes-training",
    sagemaker_session=session,
)

print("Starting training job. This usually takes 3-5 minutes.")
estimator.fit()

print("Training complete")
print(f"Model artifact: {estimator.model_data}")

training_job_name = estimator._current_job_name
print(f"Training job name: {training_job_name}")

with open("training_job_name.txt", "w") as f:
    f.write(training_job_name)
