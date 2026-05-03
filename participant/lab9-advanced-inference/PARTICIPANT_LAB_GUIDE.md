# Lab 9: Advanced Inference Patterns

## Participant Lab Guide

**Duration:** 75 minutes  
**Difficulty:** Intermediate  
**Module:** 9 — Advanced Inference  
**AWS Region:** `us-east-1`

---

## Lab objective

You will practise **four SageMaker inference styles** beyond a single **always-on realtime** host: **serverless** (scale-to-zero metering), **asynchronous** (S3-backed large jobs), **multi-model endpoints** (**MME**) on one **`ml.m5.large`**, and **Batch Transform** for offline CSV scoring.

Technical reference: [`labs/lab9-advanced-inference/LAB_OVERVIEW.md`](../../labs/lab9-advanced-inference/LAB_OVERVIEW.md).

---

## What you will build

| Pattern | What runs | Good for |
| --- | --- | --- |
| **Serverless** | No dedicated instance hours while idle | Sporadic traffic, demos |
| **Asynchronous** | Realtime-capable fleet + S3 **`InputLocation` / async-output** queues | Larger payloads vs sync **`invoke_endpoint`** |
| **Multi-model** | One host, many **`model.tar.gz`** under **`models/`** | Many compact sklearn artefacts |
| **Batch Transform** | One-off transform job over **S3** prefix | Nightly CSV scoring |

Artifacts are sklearn **RandomForest** classifiers (**10** numeric features). Each trained model is **`model.joblib`** inside **`model.tar.gz`** (handled by **`train_models.py`**).

---

## Why different patterns matter

**Realtime-only** stacks (Lab 6) stay **up 24×7** and impose **payload / timeout** limits that do not suit every workload. This lab swaps the **delivery mechanism**—not the maths—so you learn when to meter **requests**, queue **blob** work, multiplex **hosts**, or run **offline** batches.

Teaching numbers in **`compare_costs.py`** are **illustrative stubs**—always reconcile with **[AWS Pricing Calculator](https://calculator.aws)** for real quotes.

---

## Which pattern might you choose?

- Need **steady sub-100 ms** synchronous answers? Prefer a **provisioned realtime** endpoint (Lab 6).
- **Payload or processing** routinely exceeds synchronous **Realtime** limits on your tier? Evaluate **async** ingress to **S3**.
- Traffic is **thin** and interruptions from **cold start** acceptable? Evaluate **Serverless**.
- Millions of CSV rows offline? Prefer **Batch Transform** over flooding an endpoint.

---

## AWS services you will use

| Service | Purpose |
| --- | --- |
| **SageMaker Serverless Inference** | Pay-per-use container without always-on instances |
| **SageMaker Asynchronous Inference** | **`invoke_endpoint_async`** + **S3** staging |
| **SageMaker Multi-Model Endpoints** | **`MultiDataModel`** + **`TargetModel`** routing |
| **SageMaker Batch Transform** | **S3→S3** scoring job |
| **S3** | Model **`models/*/model.tar.gz`**, async IO, batch IO |
| **IAM** | **SageMaker** execution role (**Terraform**) |

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop / VS Code | Recommended |
| Repo cloned (**`mlops-on-aws`**) | Required |
| [**Lab 00**](../lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) | Required (CLI, **`us-east-1`**) |
| **`pip install -r requirements.txt`** (repo root) | Required |
| [**Lab 6**](../lab6-deployment/PARTICIPANT_LAB_GUIDE.md) | Strongly recommended (realtime endpoints, serializers) |

---

## Shell note (bash vs PowerShell)

Steps use **bash**. On Windows, translate **`export`** / **`terraform output -raw`** as shown—or use **Git Bash**.

---

## Lab files overview (`labs/lab9-advanced-inference/`)

| Path | Purpose |
| --- | --- |
| **`infrastructure/`** | **S3** bucket (**versioned**) + SageMaker IAM role (**~eight** Terraform resources) |
| **`scripts/train_models.py`** | Trains **`model-v1..v3`**, uploads **`models/<name>/model.tar.gz`**; writes **`model_uris.txt`** |
| **`scripts/inference.py`** | Shared **`model_fn`** / **`input_fn`** / **`predict_fn`** (**CSV** + **JSON `features`**) |
| **`scripts/deploy_serverless.py`** | **`lab9-serverless-<timestamp>`** (override **`LAB9_SERVERLESS_NAME`**) |
| **`scripts/deploy_async.py`** | Async endpoint → **`async-output/`** prefix |
| **`scripts/deploy_mme.py`** | Sklearn **`MultiDataModel`** on **`models/`** prefix |
| **`scripts/run_batch_transform.py`** | Uploads **`batch-input/data.csv`**, reads **`MODEL_S3_URI`** or **`model-v2`** path |
| **`scripts/test_endpoints.py`** | Exercises **`serverless_endpoint_name.txt`**, **`async_endpoint_name.txt`**, **`mme_endpoint_name.txt`** |
| **`scripts/compare_costs.py`** | Prints **estimate** worksheet (calculator-ready, not authoritative) |
| **`scripts/cleanup.py`** | Deletes SageMaker endpoints / configs / models discovered from **`.txt`** state |
| **`data/sample_batch_data.csv`** | Optional manual CSV (**no header**) with **10** columns |

---

## Step 1 — Open the lab folder

1. Navigate to **`mlops-on-aws` → `labs` → `lab9-advanced-inference`**.
2. Open an integrated terminal rooted at **`lab9-advanced-inference`** (Right-click folder → **Open in Integrated Terminal**).

---

## Step 2 — Deploy infrastructure

### 2.1 Enter **`infrastructure`**

```bash
cd labs/lab9-advanced-inference/infrastructure
```

### 2.2 (**Optional**) variables file

The sample **`terraform.tfvars.example`** only holds optional comments (region/project). Skip **`cp`** if defaults work; customise **`aws_region`** / **`tags`** after copying when your policy requires tagging changes.

### 2.3 Apply Terraform

```bash
terraform init
terraform apply -auto-approve
```

You should see about **eight resources** plus any provider noise (counts may vary slightly with Terraform version **`Apply complete!`**).

### 2.4 Export outputs

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw inference_role_arn)
```

**PowerShell**

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw inference_role_arn
```

> **Created:** **`mlops-lab9-inference-<suffix>`** bucket (versioned) + **`MLOpsLab9InferenceRole-<suffix>`**.

---

## Step 3 — Train three model variants

```bash
cd ../scripts
python train_models.py
```

Creates **`model-v1`** (50 trees), **`model-v2`** (100 trees), **`model-v3`** (150 trees)—each mirrored to **`s3://<BUCKET_NAME>/models/<variant>/model.tar.gz`**—and writes **`model_uris.txt`**.

Accuracy lines differ slightly between runs (**~0.85** region typical).

---

## Step 4 — Deploy serverless endpoint

```bash
python deploy_serverless.py
```

- Default endpoint name **`lab9-serverless-<unix_ts>`**.
- Persisted into **`serverless_endpoint_name.txt`**.

Cold path after idle can take **many seconds**. Warm calls should settle faster.

Optional: **`MODEL_S3_URI`** to point deployments at non-default artefacts; **`LAB9_SERVERLESS_NAME`** pins a deterministic name.

---

## Step 5 — Deploy asynchronous endpoint

```bash
python deploy_async.py
```

- Default **`lab9-async-<unix_ts>`** → **`async_endpoint_name.txt`**.
- Responses land under **`s3://<BUCKET>/async-output/`** configured in code.

Requires **`ROLE_ARN`**, **`BUCKET_NAME`** (same **`export`** discipline).

Optional: **`LAB9_ASYNC_NAME`** for a fixed AWS name inside your quotas.

---

## Step 6 — Deploy multi-model endpoint

```bash
python deploy_mme.py
```

Bootstraps **`MultiDataModel`** with **`models/model-v1/model.tar.gz`**, **`model_data_prefix` = `s3://<bucket>/models/`**. **`mme_endpoint_name.txt`** captures the **`lab9-mme-<ts>`** name.

Invocations specify **`TargetModel = "<folder>/model.tar.gz"`**, e.g. **`model-v2/model.tar.gz`**.

Optional **`LAB9_MME_NAME`** to fix endpoint naming.

---

## Step 7 — Run batch transform

```bash
python run_batch_transform.py
```

Automatically stages **100** **headerless** rows (**10 floats**) to **`batch-input/`** and writes scores under **`batch-output/`** (inspect **S3** for **`.out`** artefacts).

Runs **minutes** typical for classroom accounts.

---

## Step 8 — Test endpoints

Ensure **`BUCKET_NAME`** stays exported (**async branch** uploads probe CSV to **`async-requests/`**):

```bash
python test_endpoints.py
```

You should see **`TEST SERVERLESS`** latency lines, **`TEST ASYNCHRONOUS`** queue + **`OutputLocation`** poll status, plus **`TEST MULTI-MODEL ENDPOINT`** lines with **`prediction`** + **`probability`**.

---

## Step 9 — Compare costs (**illustrative**)

```bash
python compare_costs.py
```

Script prints bullet estimates—**numbers are teaching aids**, **not invoices**. Replace assumptions with Pricing Calculator snapshots for stakeholder decks.

---

## Step 10 — Clean up (**avoid surprise bills**)

```bash
python cleanup.py
cd ../infrastructure
terraform destroy -auto-approve
```

Terraform destroy tears down bucket + IAM. Confirm **CloudWatch Logs** retained policy if mandated by organisation.

---

## Lab completion checklist

- [ ] Terraform applied (**bucket + IAM**).
- [ ] **`train_models.py`** seeded **three** S3 artefacts + **`model_uris.txt`**.
- [ ] **`deploy_serverless.py`** / **`deploy_async.py`** / **`deploy_mme.py`** emitted **`.txt`** endpoint names & remained **InService** through tests.
- [ ] **`run_batch_transform.py`** finished without **`Failed`** transform status.
- [ ] **`test_endpoints.py`** proved **cold vs warm**, **async S3 acknowledgement**, **`TargetModel`** routing.
- [ ] **`compare_costs.py`** discussed with instructor (stub vs reality).
- [ ] **`cleanup.py`** + **`terraform destroy`** succeeded.

---

## Pattern comparison (**rules of thumb**)

| Aspect | Provisioned realtime (Lab 6) | Serverless | Async realtime host | Batch |
| --- | --- | --- | --- | --- |
| Idle cost | Instances bill | Minimal | Instances bill until scaled | Pays per job duration |
| First-byte behaviour | Warm fleet | Potential **cold starts** | Similar to realtime + queue delay | Deferred by design |
| Large payloads | **Realtime** quotas | Same HTTP path limits typically | **`InputLocation` S3** pattern | Naturally **S3** native |
| When to revisit choice | SLA-sensitive UX | intermittent traffic | heavyweight ingress | nightly scoring decks |

Limits evolve—pair this table with current **Regional** quotas when designing production.

---

## Troubleshooting

| Symptom | Likely remedy |
| --- | --- |
| Serverless first call **times out / slow** | Expected **cold boot** — retry once healthy |
| **`test_endpoints`** async section skipped | **`BUCKET_NAME`** unset (`export` drift) |
| Async never materialises **`OutputLocation`** | Inspect **IAM** (**SageMaker reads input / writes outputs**) + **`async-output/`** prefixes |
| MME **`ValidationException`** on **`invoke_endpoint`** | Confirm **`TargetModel`** matches **`model-vN/model.tar.gz`** under bucket **`models/`** |
| Batch transform fails CSV parse | Rows must contain **exactly ten** floats, **no header** |
| **`cleanup.py`** cannot delete endpoint | Wait for **`Deleting`** / **`InService`→`Deleting`** propagation; rerun |

---

## Key takeaways

- **Operational choices** dominate unit economics — **pick** the delivery path (**serverless** / **async** / **MME** / **batch**) deliberately.
- **Packaging parity** (**`model.joblib`**) keeps every pattern sharing **one inference contract**.
- **Always** pair demo math with **`compare_costs.py`-style disclaimers**: verify with Pricing Calculator **before** stakeholder promises.
