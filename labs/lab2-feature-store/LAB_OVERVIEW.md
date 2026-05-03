# Lab 2: Feature Store pipeline

Module **2 – Data Management** · Region **`us-east-1`** · approx. **90 minutes**

## What this lab covers

Work with SageMaker Feature Store:

- Provision S3 bucket, Glue catalog DB, and execution role (**Terraform**)
- Create customer + order **Feature Groups** (online + offline)
- **Ingest** batch features
- **Read** features from the **online store** (low latency)
- **Query** the **offline store** with Amazon **Athena**
- Fit a simple **training** baseline from offline features (**scikit-learn**)

## Prerequisites

Complete [Lab 00](../../participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md). Your IAM identity needs permissions for SageMaker Feature Store APIs, Athena, Glue, and S3 (your instructor configures the sandbox).

## Participant lab guide

- **[PARTICIPANT_LAB_GUIDE.md](../../participant/lab2-feature-store/PARTICIPANT_LAB_GUIDE.md)** — step-by-step (Terraform, scripts, cleanup)  
- **[LAB2_PARTICIPANT_INDEX.md](../../participant/lab2-feature-store/LAB2_PARTICIPANT_INDEX.md)** — folder index  

## Repo layout

| Path | Purpose |
|------|---------|
| `infrastructure/` | Terraform (`main.tf`, `providers.tf`, `variables.tf`) |
| `scripts/` | `create_features.py` → `ingest_data.py` → `retrieve_features.py` → `query_offline.py` → `train_model.py` |
| `data/sample_customers.csv` | Sample rows (CSV); scripts use synthesized DataFrames for consistency |

Full instructor notes and expected outputs: [`solutions/lab2/LAB2_SOLUTION_REFERENCE.md`](../../solutions/lab2/LAB2_SOLUTION_REFERENCE.md).

## Quick run (high level)

```bash
cd infrastructure
terraform init && terraform apply -auto-approve
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw feature_store_role_arn)
cd ../scripts
pip install -r ../../requirements.txt   # once, from repo root
python create_features.py
python ingest_data.py
python retrieve_features.py
python query_offline.py    # optional wait ~1–2 min after ingest for Athena
python train_model.py
```

**Cleanup:**

```bash
cd ../infrastructure
terraform destroy -auto-approve
```

## Athena / Glue note

**Terraform** creates Glue database **`sagemaker_featurestore`**. Offline tables are typically named after your Feature Group (normalized). If queries return no rows, wait briefly after ingest and verify table names under that database in the Glue console.
