# Lab 4: Model registry & governance

Module **4 – Governance** · **`us-east-1`** · about **75 minutes**

## Goals

- Train a sklearn **RandomForest** on synthetic binary data and produce a **model artifact** in S3  
- Create a **Model Package Group** and **register** a version with metrics + metadata (`PendingManualApproval`)  
- Implement a simple **approval gate** (**Approved** / **Rejected**)  
- **Deploy** an **Approved** package to a realtime endpoint via **`ModelPackage`**  
- Discuss **lineage**, metadata, and separation of duties (who trains vs who approves)

## Prerequisites

- [Lab 00](../../participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) (AWS CLI)  
- `pip install -r requirements.txt` at repo root (`boto3`, `sagemaker`, `pandas`, `scikit-learn`, …)

## Participant walkthrough

- **[participant/lab4-registry/PARTICIPANT_LAB_GUIDE.md](../../participant/lab4-registry/PARTICIPANT_LAB_GUIDE.md)** — step-by-step for students  
- **[participant/lab4-registry/LAB4_PARTICIPANT_INDEX.md](../../participant/lab4-registry/LAB4_PARTICIPANT_INDEX.md)** — folder cheat sheet  

## Layout

| Path | Purpose |
|------|---------|
| `infrastructure/` | S3 + SageMaker execution role |
| `scripts/train.py` | Container training entry (reads `train` / `test` channels) |
| `scripts/train_model.py` | Generate CSVs → upload → **SageMaker training** → writes **`training_job_name.txt`**, **`model_data_uri.txt`** |
| `scripts/register_model.py` | Model package group + **create_model_package** (sklearn **inference image** matching training) |
| `scripts/approve_model.py` | List pending → read metrics blob → **`update_model_package`** |
| `scripts/list_models.py` | Inventory groups / versions |
| `scripts/deploy_from_registry.py` | Latest **Approved** package → **`ml.t2.medium`** endpoint (**`endpoint_name.txt`**) |
| `notebooks/registry_explorer.ipynb` | Optional boto3 exploration |

Artifacts written under **`scripts/`** (gitignored locally is optional): `train.csv`, `test.csv`, `*.txt` state files.

Instructor notes: [**`solutions/lab4/LAB4_SOLUTION_REFERENCE.md`**](../../solutions/lab4/LAB4_SOLUTION_REFERENCE.md).

## Script order

1. Terraform apply → export `BUCKET_NAME`, `ROLE_ARN`  
2. **`python train_model.py`**  
3. **`python register_model.py`** (optional env **`MODEL_PACKAGE_GROUP`**)  
4. **`python approve_model.py`** (optional **`ACCURACY_THRESHOLD`**, default `0.85`)  
5. **`python list_models.py`**  
6. **`python deploy_from_registry.py`**  

## Cleanup

```bash
aws sagemaker delete-endpoint --region us-east-1 --endpoint-name "$(cat scripts/endpoint_name.txt)"
cd infrastructure && terraform destroy -auto-approve
```

Also delete **Model Package** versions / group in console if policy requires full teardown (Terraform does not remove registry objects).
