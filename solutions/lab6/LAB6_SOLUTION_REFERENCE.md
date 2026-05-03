# Lab 6 — Deployment & serving (instructor reference)

Condensed pitfalls for **`labs/lab6-deployment/`**.

## Resource inventory

Terraform manages **bucket + versioning + PA block + IAM role + standard AWS policy attachments (~8)**. Endpoint / models / scaling policies belong to SageMaker/Application Auto Scaling and require **`cleanup.py`** (or Console).

## Inference contract

Training writes **`model.joblib`**. Inference returns JSON shaped like:

```json
{"prediction": 0, "probability_positive": 0.73}
```

**`Predictor`** path: **`CSVSerializer`** + **`JSONDeserializer`**. Direct **`invoke_endpoint`** should set **`Accept: application/json`**.

## Artifacts (`scripts/`)

| File | Writer |
|------|--------|
| `train.csv`, `test.csv` | train_model.py |
| `model_data_uri.txt`, `training_job_name.txt` | train_model.py (deploy refreshes artifact line) |
| `endpoint_name.txt`, `endpoint_variant_name.txt` | deploy_endpoint (+ canary mutates variant file) |
| `scalable_target_id.txt` | configure_scaling.py |
| `canary_state.txt` | canary_deployment.py apply |

## Canary commands

```bash
python canary_deployment.py apply [--blue-weight 90] [--green-weight 10]
python canary_deployment.py promote-green
```

**`promote-green`** reads **`canary_state.txt`**; rerun **`apply`** if missing.

### True A/B

1. **`python train_model.py`** twice (or tweak hyperparameters)  
2. `export GREEN_MODEL_DATA_URI=s3://.../second/model.tar.gz`  
3. **`apply`**

Without **`GREEN_MODEL_DATA_URI`**, both variants load identical checkpoints—explain explicitly.

## Auto scaling

Policy uses **`PredefinedMetricType = SageMakerVariantInvocationsPerInstance`**. Classroom traffic may fail to oscillate DesiredCapacity—pair with threaded **`test_endpoint.load_test`**.

## Troubleshooting snippets

| Symptom | Check |
|---------|-------|
| **ValidationException** on **`create_model`** | **`prepare_container_def`** keys vs **`describe_training_job`** incomplete artifact URIs |
| **`Endpoint failed`** | Processing container logs (bad **`inference.py`**) |
| **Scaling API denied** | IAM / SCP blocking **`application-autoscaling:*`** |

## Classroom narrative hooks

Contrast **real-time (this lab)** vs **batch transform**, **async inference**, **serverless inference** budgets—Module 7+ can deepen monitoring / drift.
