# Lab 9 — Advanced Inference cheatsheet

## IaC tally

Minimal footprint: versioning-enabled bucket, IAM role wired to **`AmazonSageMakerFullAccess`**, **`AmazonS3FullAccess`**, **`CloudWatchLogsFullAccess`**.

## Artefact convention

Tarballs must unzip to **`model.joblib`** (`train_models.py` does this deliberately). Inference entrypoint **`scripts/inference.py`** mirrors Lab 6 contract with **`probability`** key for student-facing JSON examples.

## Multi-model nuances

Bootstrap model **`models/model-v1/model.tar.gz`** seeds **`MultiDataModel`**. **`TargetModel`** is the **suffix after the shared prefix**:

```
s3://BUCKET/models/ + model-v2/model.tar.gz → TargetModel = "model-v2/model.tar.gz"
```

Cold requests per model incur download + load—call that out live.

## Asynchronous checklist

Outputs land under **`s3://…/async-output/`** (configured in **`AsyncInferenceConfig`**). Demonstrate SNS/Lambda escalation if cohort time allows — not wired in scaffold.

## Batch transform knobs

Scripts use **`SingleRecord`/`Line`** for transparent JSON-per-row outputs. Mention **`MaxPayloadInMB`** for wide rows when students graduate to parquet manifests.

## Breadcrumb files (`scripts/`)

| File | Writer |
|------|--------|
| `model_uris.txt` | `train_models.py` |
| `serverless_endpoint_name.txt` | `deploy_serverless.py` |
| `async_endpoint_name.txt` | `deploy_async.py` |
| `mme_endpoint_name.txt` | `deploy_mme.py` |

## Cleanup order

Always run **`cleanup.py`** (deletes endpoint + discovers models) prior to **`terraform destroy`** unless you purposely retain artefacts for auditing.
