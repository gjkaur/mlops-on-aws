# Lab 4 — Model Registry (instructor reference)

Condensed notes for **`labs/lab4-registry/`**.

## Overview

| Attribute | Value |
|-----------|-------|
| Duration | ~75 min |
| Module | 4 – governance |
| Region | `us-east-1` |

## Correctness vs “any model image” teaching draft

Training uses the **SageMaker sklearn** container (**`SKLearn`** estimator, **`framework_version="1.2-1"`**). Registration **must** use the matching **sklearn inference image URI** from **`sagemaker.image_uris.retrieve(..., framework="sklearn", ...)`** — **not** XGBoost — or batch/realtime inference will fail.

## Script outputs (under `scripts/`)

| File | Writer |
|------|--------|
| `training_job_name.txt`, `model_data_uri.txt` | `train_model.py` |
| `model_package_group.txt`, `model_package_arn.txt` | `register_model.py` |
| `endpoint_name.txt` | `deploy_from_registry.py` |

## boto3 details

- **`describe_model_package`** / related calls use **`ModelPackageArn`**.  
- **`update_model_package`** uses **`ModelApprovalStatus`** + **`ApprovalDescription`** (metadata-only updates kept minimal for API compatibility).

## Teaching emphasis

1. Registry is the handoff between **experimentation** and **production**.  
2. Only **Approved** packages should drive automated deploy in real organizations.  
3. **`CustomerMetadataProperties`** + metrics JSON support audit / lineage stories.  
4. Terraform **does not** delete model packages — console or API cleanup if you need a spotless account.

## Common issues

| Symptom | Check |
|---------|--------|
| Register fails on image / container | Sklearn image version matches training |
| Approve always Rejects | **`FinalMetricDataList`** empty → lower **`ACCURACY_THRESHOLD`** or re-run training with metric regex |
| Deploy: no approved model | Run **`approve_model.py`** with passing accuracy |
| Endpoint errors on shape | Input must be **10** numeric features (CSV / default serializer) |
