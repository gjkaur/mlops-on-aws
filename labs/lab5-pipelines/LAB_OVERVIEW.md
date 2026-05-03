# Lab 5: CI/CD orchestration — SageMaker Pipelines

Module **5 – CI/CD** · **`us-east-1`** · about **90 minutes** · intermediate

## Goals

- Build a SageMaker Pipeline **DAG**: processing → training → evaluation → **conditional** model registry registration  
- Use **pipeline parameters** (instance types, hyperparameters, **accuracy gate**)  
- Understand **quality gates**: only register when **`JsonGet`** on **`evaluation.json`** meets **`AccuracyThreshold`**  
- Optionally wire **EventBridge** → **`StartPipelineExecution`** when objects land under **`new-data/`**  
- Inspect runs in console or **`notebooks/pipeline_analysis.ipynb`**

## Prerequisites

- [Lab 00](../../participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) (AWS CLI configured)  
- Repo root **`pip install -r requirements.txt`**

## Layout

| Path | Purpose |
|------|---------|
| `infrastructure/` | S3 bucket, SageMaker execution role, EventBridge role, **S3 → EventBridge** notification |
| `scripts/preprocess.py` | Synthetic churn-style dataset → **`train.csv` / `test.csv`** |
| `scripts/train.py` | Sklearn **`RandomForest`**, **`model.joblib`** + **`metrics.json`** |
| `scripts/evaluate.py` | Unpack **`model.tar.gz`**, evaluate on **`test.csv`**, write **`evaluation.json`** |
| `scripts/pipeline_definition.py` | **`Pipeline`** with **`ConditionStep`** + **`RegisterModel`** |
| `scripts/run_pipeline.py` | **`start_pipeline_execution`**, poll to terminal state |
| `scripts/trigger_setup.py` | EventBridge rule + SageMaker Pipeline target (**`delete`** subcommand) |
| `notebooks/pipeline_analysis.ipynb` | Optional boto3 listings |

Naming (stable per learner bucket suffix): pipeline **`lab5-churn-pipeline-<suffix>`**, model package group **`lab5-churn-pipeline-group-<suffix>`**.

## Script order

1. Terraform **`apply`** → export outputs  
2. **`python pipeline_definition.py`** (**`pipeline_name.txt`**)  
3. **`python run_pipeline.py`** (**`pipeline_execution_arn.txt`**)  
4. Optional **`python trigger_setup.py`** (requires **`EVENTBRIDGE_ROLE_ARN`**)  

## Instructor / solution notes

[`INSTRUCTOR_LAB_GUIDE.md`](INSTRUCTOR_LAB_GUIDE.md) · [`../../solutions/lab5/LAB5_SOLUTION_REFERENCE.md`](../../solutions/lab5/LAB5_SOLUTION_REFERENCE.md)

## Cleanup

Destroy EventBridge targeting first (**`python trigger_setup.py delete`**).

```bash
cd infrastructure && terraform destroy -auto-approve
```

SageMaker **Model Package** entities are **not** removed by Terraform; delete in SageMaker Studio / console if policies require empty accounts.
