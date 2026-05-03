# Lab 2 – Feature Store pipeline (instructor reference)

Condensed instructor notes for **`labs/lab2-feature-store/`**. Keep synchronized with **`LAB_OVERVIEW.md`** there.

## Lab overview

| Attribute | Value |
|-----------|-------|
| **Duration** | ~90 minutes |
| **Difficulty** | Beginner–intermediate |
| **Module** | 2 – Data management |
| **Region** | `us-east-1` |

### Learning objectives

- Create Feature Groups (online + offline)
- Batch ingest sample features
- Read from Feature Store Runtime (online)
- Athena SQL against offline catalog
- Small training baseline from Athena-exported rows

### AWS services

| Service | Role |
|---------|------|
| SageMaker Feature Store | Canonical feature definitions + stores |
| S3 | Offline exports, Athena spill |
| Glue | Offline metadata / tables |
| Athena | SQL exploration |
| IAM | Execution role for Feature Store operations |

---

## Validation script (dry run order)

From repo root dependencies: `pip install -r requirements.txt`.

```bash
cd labs/lab2-feature-store/infrastructure
terraform init && terraform apply -auto-approve
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw feature_store_role_arn)
cd ../scripts
python create_features.py
python ingest_data.py
python retrieve_features.py
python query_offline.py
python train_model.py
cd ../infrastructure
terraform destroy -auto-approve
```

Artifacts in `scripts/`: **`customer_fg_name.txt`**, **`order_fg_name.txt`**.

---

## Expected outputs (high level)

- **create_features:** Two Feature Groups Created; waiter prints `Created`.
- **ingest:** Row counts echoed per group.
- **retrieve:** Printed feature key/value bundle for cust `101`; batch lookups for `101`,`103`,`105`.
- **query_offline / train_model:** DataFrames printed; churn demo metrics printed (figures vary slightly with stochastic label).

---

## Common issues

| Symptom | Mitigation |
|---------|-------------|
| Feature Group stuck Creating | Typically resolves in under 3 minutes; else delete FG in console & retry scripts |
| Athena empty results | Pause 1–2 min post-ingest; confirm Glue tables / database `sagemaker_featurestore` |
| AccessDenied Feature Store APIs | Sandbox IAM boundary / role trust on `FEATURE_STORE_ROLE_ARN` path |
| Local Athena fails | Participant principal needs Athena + Glue + S3 on lab bucket prefixes |
| Naming drift for FG vs table | Athena table names derive from FG name (`-`→`_`, lowercasing); rerun `query_offline` after inspecting Glue |

---

## Cleanup

Participants must run **`terraform destroy`** in **`infrastructure/`** when finished.
