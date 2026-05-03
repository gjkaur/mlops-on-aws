# Instructor Setup Guide: MLOps on AWS Course Repository

## Repository Structure

```
mlops-on-aws/
├── README.md
├── requirements.txt
├── participant/
│   ├── PARTICIPANT_DOCUMENTATION_INDEX.md
│   ├── lab0-environment-setup/
│   │   ├── LAB0_PARTICIPANT_INDEX.md
│   │   └── PARTICIPANT_LAB_GUIDE.md
│   ├── lab1-first-training/
│   │   ├── LAB1_PARTICIPANT_INDEX.md
│   │   └── PARTICIPANT_LAB_GUIDE.md
│   ├── lab2-feature-store/
│   │   ├── LAB2_PARTICIPANT_INDEX.md
│   │   └── PARTICIPANT_LAB_GUIDE.md
│   └── lab3-tuning/
│       ├── LAB3_PARTICIPANT_INDEX.md
│       └── PARTICIPANT_LAB_GUIDE.md
├── labs/
│   ├── lab0-environment-setup/
│   │   └── LAB_OVERVIEW.md
│   ├── lab1-first-training/
│   │   ├── LAB_OVERVIEW.md
│   │   ├── infrastructure/
│   │   │   ├── main.tf
│   │   │   ├── providers.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars.example
│   │   ├── scripts/
│   │   │   ├── train.py
│   │   │   └── run_training.py
│   │   └── outputs/
│   │       └── (empty - for student outputs)
│   ├── lab2-feature-store/
│   │   ├── LAB_OVERVIEW.md
│   │   ├── data/
│   │   │   └── sample_customers.csv
│   │   ├── infrastructure/
│   │   │   ├── main.tf
│   │   │   ├── providers.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars.example
│   │   └── scripts/
│   │       ├── create_features.py
│   │       ├── ingest_data.py
│   │       ├── retrieve_features.py
│   │       ├── query_offline.py
│   │       └── train_model.py
│   ├── lab3-tuning/
│   │   ├── LAB_OVERVIEW.md
│   │   ├── infrastructure/
│   │   │   ├── main.tf
│   │   │   ├── providers.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars.example
│   │   ├── notebooks/
│   │   │   └── experiment_analysis.ipynb
│   │   └── scripts/
│   │       ├── analyze_results.py
│   │       ├── baseline.py
│   │       ├── deploy_best.py
│   │       ├── predict.py
│   │       ├── train.py
│   │       └── tuning_config.py
│   ├── lab4-registry/
│   │   └── LAB_OVERVIEW.md
│   ├── lab5-pipelines/
│   │   └── LAB_OVERVIEW.md
│   ├── lab6-deployment/
│   │   └── LAB_OVERVIEW.md
│   ├── lab7-monitoring/
│   │   └── LAB_OVERVIEW.md
│   ├── lab8-capstone/
│   │   └── LAB_OVERVIEW.md
│   ├── lab9-advanced-inference/
│   │   └── LAB_OVERVIEW.md
│   └── lab10-enterprise/
│       └── LAB_OVERVIEW.md
├── shared/
│   ├── modules/
│   │   └── (reusable Terraform modules)
│   └── utils/
│       └── (shared Python utilities)
└── solutions/
    ├── lab1/
    │   └── LAB1_SOLUTION_REFERENCE.md
    ├── lab2/
    │   └── LAB2_SOLUTION_REFERENCE.md
    └── lab3/
        └── LAB3_SOLUTION_REFERENCE.md
```

---

## Step 1: Create the Repository Root Files

### README.md (repository entry page)

```markdown
# MLOps on AWS – Course Labs

This repository contains all code and infrastructure definitions for the Practical MLOps on AWS course.

## Repository Structure

| Folder | Purpose |
|--------|---------|
| `labs/` | Lab-specific code and infrastructure |
| `shared/` | Reusable modules and utilities |
| `solutions/` | Completed solutions (instructors only) |

## Prerequisites

- Python 3.10+
- AWS CLI configured
- Terraform 1.7+
- VS Code (recommended)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/mlops-on-aws.git
cd mlops-on-aws

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Lab Navigation

Each lab folder contains:
- `infrastructure/` – Terraform code for AWS resources
- `scripts/` – Python scripts for training, deployment, monitoring
- `LAB_OVERVIEW.md` – Lab summary and links

Start with [Lab 1](labs/lab1-first-training/LAB_OVERVIEW.md)
```

### requirements.txt

```text
boto3>=1.34.0
sagemaker>=2.200.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
joblib>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
pyyaml>=6.0
```

---

## Step 2: Lab 1 – First SageMaker Training Job

### labs/lab1-first-training/LAB_OVERVIEW.md

```markdown
# Lab 1: First SageMaker Training Job

## What You Will Do

- Deploy pre-written infrastructure code
- Run your first SageMaker training job
- Train a Random Forest model on the diabetes dataset
- Understand model performance metrics

## Files in This Lab

| File | Purpose |
|------|---------|
| `infrastructure/` | Terraform code for S3 bucket and IAM role |
| `scripts/train.py` | Training script (runs inside SageMaker) |
| `scripts/run_training.py` | Launches SageMaker training job |

## Step-by-Step Instructions

Participants: see **`participant/lab1-first-training/PARTICIPANT_LAB_GUIDE.md`** (folder index **`LAB1_PARTICIPANT_INDEX.md`**).

### labs/lab1-first-training/infrastructure/providers.tf

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

### labs/lab1-first-training/infrastructure/variables.tf

```hcl
variable "aws_account_id" {
  description = "Your AWS Account ID"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "training-lab"
    Project     = "mlops-course"
    ManagedBy   = "Terraform"
    Lab         = "module-1"
  }
}
```

### labs/lab1-first-training/infrastructure/main.tf

```hcl
# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# S3 Bucket for training code and model artifacts
resource "aws_s3_bucket" "sagemaker_bucket" {
  bucket        = "sagemaker-lab1-${random_id.suffix.hex}"
  force_destroy = true
  tags          = var.tags
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.sagemaker_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket = aws_s3_bucket.sagemaker_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role for SageMaker
data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "sagemaker_execution_role" {
  name               = "SageMakerExecutionRole-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket created for training"
  value       = aws_s3_bucket.sagemaker_bucket.id
}

output "sagemaker_role_arn" {
  description = "ARN of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_execution_role.arn
}

output "sagemaker_role_name" {
  description = "Name of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_execution_role.name
}
```

### labs/lab1-first-training/infrastructure/terraform.tfvars.example

```hcl
# Copy this file to terraform.tfvars and add your AWS account ID
aws_account_id = "<your-account-id>"
```

### labs/lab1-first-training/scripts/train.py

```python
import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=10)
    args = parser.parse_args()

    print("=" * 50)
    print("Starting SageMaker Training Job")
    print("=" * 50)

    # Load data
    diabetes = load_diabetes()
    X = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
    y = pd.Series(diabetes.target, name="target")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training rows: {X_train.shape[0]}")
    print(f"Test rows: {X_test.shape[0]}")

    # Train model
    model = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "mse": float(mse),
        "rmse": float(rmse),
        "r2": float(r2),
    }

    print("Model Performance:")
    print(f"RMSE: {rmse:.2f}")
    print(f"R2 Score: {r2:.4f}")

    # Save model and metrics
    os.makedirs("/opt/ml/model", exist_ok=True)

    with open("/opt/ml/model/metrics.json", "w") as f:
        json.dump(metrics, f)

    joblib.dump(model, "/opt/ml/model/model.joblib")
    print("Training complete")
```

### labs/lab1-first-training/scripts/run_training.py

```python
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
```

---

## Step 3: Shared Utilities

### shared/utils/aws_helpers.py

```python
"""Shared AWS utilities for all labs."""

import boto3
import json


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
```

---

## Step 4: Solutions Folder (Instructor Only)

### solutions/lab1/LAB1_SOLUTION_REFERENCE.md

```markdown
# Lab 1 Solution (Instructor Reference)

## Expected Outputs

### Terraform Apply
```
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

Outputs:

s3_bucket_name = "sagemaker-lab1-a1b2c3d4"
sagemaker_role_arn = "arn:aws:iam::123456789012:role/SageMakerExecutionRole-a1b2c3d4"
sagemaker_role_name = "SageMakerExecutionRole-a1b2c3d4"
```

### Training Job Metrics
```json
[
  {"MetricName": "rmse", "Value": 54.54},
  {"MetricName": "r2", "Value": 0.44}
]
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| ResourceLimitExceeded | Change instance_type to `ml.t2.medium` in run_training.py |
| AccessDenied | Verify IAM role has required permissions |
| Bucket already exists | Terraform uses random suffix; shouldn't happen |
```

---

## Step 5: Generate Participant Version of Labs

Once the repository is ready, you can generate **participant versions** by:

1. **Removing solution files** from the participant view
2. **Keeping lab `LAB_OVERVIEW.md` files and the root `README.md`** with instructions
3. **Keeping all code files** (students should not write code from scratch)

### Participant Version Script (for your reference)

```bash
#!/bin/bash
# create-participant-repo.sh

# Create a clean copy without solution folders
cp -r mlops-on-aws mlops-on-aws-participant
rm -rf mlops-on-aws-participant/solutions

# Remove any instructor notes from Markdown guides
find mlops-on-aws-participant -name "*.md" -exec sed -i '/INSTRUCTOR NOTE/d' {} \;

# Create archive
zip -r mlops-on-aws-participant.zip mlops-on-aws-participant
```

---

## Summary

| Step | What You've Created |
|------|---------------------|
| 1 | Repository root with README and requirements |
| 2 | Lab 1 complete code (infrastructure + scripts) |
| 3 | Shared utilities for all labs |
| 4 | Solutions folder for instructors |
| 5 | Script to generate participant version |

