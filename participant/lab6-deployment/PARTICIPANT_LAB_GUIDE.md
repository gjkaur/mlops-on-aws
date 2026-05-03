# Lab 6: Model deployment & serving

## Participant Lab Guide

**Duration:** 90 minutes  
**Difficulty:** Intermediate  
**Module:** 6 — Deployment  
**AWS Region:** `us-east-1`

---

## Lab objective

You will expose a trained **sklearn** model as a **SageMaker real-time endpoint**, optionally tune **capacity with Application Auto Scaling**, run a short **multi-variant (“canary”) routing** demo, and **stress-test** latency with concurrent calls.

Technical reference: [`labs/lab6-deployment/LAB_OVERVIEW.md`](../../labs/lab6-deployment/LAB_OVERVIEW.md).

---

## What you will build

- **`SKLearn`** training job artifact (**`model.tar.gz`**) in **S3**
- **`lab6-rt-endpoint-<timestamp>`** (or a name you override) **InService** with **`ml.t2.medium`**
- Optional **scaling policy** (**min 1** / **max 3**) on the serving variant
- Optional **90/10-style** routing across **blue/green** variants (same or different tarball)
- **State files** under **`labs/lab6-deployment/scripts/`** (artifact URI, endpoint name, variant name, etc.)

---

## Why deployment matters

A model on disk does not serve users. A **hosted endpoint** provides a stable invocation interface (SDK **`Predictor`** or **`sagemaker-runtime`**) so applications can request predictions without copying your notebook.

---

## AWS services you will use

| Service | Purpose |
|---------|---------|
| **SageMaker Training** | Produces **`model.joblib`** packaged for inference |
| **SageMaker Endpoints** | Real-time **`ml.t2.medium`** inference fleet |
| **Application Auto Scaling** | Target-tracking on **`SageMakerVariantInvocationsPerInstance`** |
| **S3** | Training data uploads + **`lab6-output`** tarball |
| **CloudWatch** | Endpoint metrics / logs |

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop / VS Code | Recommended |
| Repo cloned (**`mlops-on-aws`**) | Required |
| [**Lab 00**](../lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) | Required (AWS CLI, account ID) |
| Repo root **`pip install -r requirements.txt`** | Required |
| Labs 1–5 | Recommended (**Lab 5** reinforces automation context) |

---

## Shell note (bash vs PowerShell)

Commands default to **bash**. On Windows, use PowerShell equivalents for **`cp`/`export`/`cat`** or run **Git Bash**.

---

## Lab files overview (`labs/lab6-deployment/`)

| Path | Purpose |
| --- | --- |
| **`infrastructure/`** | Terraform bucket + SageMaker IAM role (**about eight** managed resources) |
| **`scripts/train.py`** | Container training entry (**RandomForest**, 10-feature CSV) |
| **`scripts/train_model.py`** | Local driver → uploads CSVs → **`lab6-deployment-train`** → **`model_data_uri.txt`** |
| **`scripts/inference.py`** | Container inference (**JSON** response payload) |
| **`scripts/deploy_endpoint.py`** | **`SKLearnModel.deploy`** (**`CSVSerializer`** in, **`JSONDeserializer`** out) |
| **`scripts/configure_scaling.py`** | Registers scalable target + target-tracking policy |
| **`scripts/canary_deployment.py`** | **`apply`** (split traffic) **`promote-green`** (single variant again) |
| **`scripts/test_endpoint.py`** | SDK + **`invoke_endpoint`** + short threaded load test |
| **`scripts/cleanup.py`** | Drops scaling attachments, endpoint, configs, **`lab6-*`** models |
| **`notebooks/endpoint_analysis.ipynb`** | Optional **`describe_endpoint`** |

---

## Request / response shape

- **Realtime input:** **`text/csv`** body with **10** comma-separated floats (matching training **`make_classification`** width).
- **JSON response (from `inference.py`):**

```json
{"prediction": 0, "probability_positive": 0.73}
```

There is **no `label`** field—the lab reports class index and positive-class probability only.

---

## Step-by-step instructions

### Step 1: Open the lab folder

**VS Code → `labs` → `lab6-deployment`**, then **Open in Integrated Terminal**.

---

### Step 2: Provision Terraform

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
code terraform.tfvars
```

Set **`aws_account_id`** per Lab 00. Save.

```bash
terraform init
terraform apply -auto-approve
```

Expect **`Apply complete!`** with **approximately eight** resources added (bucket helpers + IAM role/policy attachments).

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw deployment_role_arn)
```

**PowerShell:**

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw deployment_role_arn
```

---

### Step 3: Train a deployable tarball

```bash
cd ../scripts
python train_model.py
```

Roughly **3–6 minutes.**

You should see **`TRAINING MODEL FOR DEPLOYMENT`**, **`Training complete`**, and **`Model artifact:`** (**`lab6-output`…** **`model.tar.gz`**). Persisted **`model_data_uri.txt`** + **`training_job_name.txt`**.

Synthetic data uses **`sklearn.datasets.make_classification`** (**binary**, **10 numeric features**)—useful churn-style analogy, but not Telco churn column names.

---

### Step 4: Deploy realtime endpoint

```bash
python deploy_endpoint.py
```

Provisioning commonly **~5–10 minutes**. Default name pattern: **`lab6-rt-endpoint-<unix_seconds>`**. Override with **`LAB6_ENDPOINT_NAME`** if your org needs a fixed pattern.

Writes **`endpoint_name.txt`**, **`endpoint_variant_name.txt`**, and refreshes **`model_data_uri.txt`**.

Monitor **AWS Console → SageMaker → Inference → Endpoints**.

---

### Step 5: Test predictions

**`test_endpoint.py`** reads **`endpoint_name.txt`** automatically. Optionally:

```bash
export ENDPOINT_NAME=$(cat endpoint_name.txt)
python test_endpoint.py
```

Runs **Predictor** (CSV rows shaped **`1×10`**), **`sagemaker-runtime`** **`invoke_endpoint`** with **`Accept: application/json`**, and a short threaded load test (**record your own timing numbers—they vary by account/network**).

---

### Step 6: Auto scaling (recommended)

Requires **`application-autoscaling`** permissions (first-time orgs may need a **service-linked role** established in Console; some SCPs block this API).

```bash
python configure_scaling.py
```

Registers **min 1**, **max 3** capacity with target-tracking on **~50** invocations/minute/instance. Writes **`scalable_target_id.txt`**.

Short demos may **not** show visible scale-out—cooldowns and steady traffic matter. Rerun **`test_endpoint.py`** with higher concurrency if you want more pressure on the metric.

---

### Step 7: Canary routing (bonus)

Subcommands are **required**:

```bash
python canary_deployment.py apply --blue-weight 90 --green-weight 10
python canary_deployment.py promote-green
```

**Default:** blue and green use the **same** tarball unless **`GREEN_MODEL_DATA_URI`** points at a **second** artifact (retrain, then export the new URI before **`apply`**).

**`promote-green`** requires **`canary_state.txt`** from **`apply`**.

If you change variant topology, you may need to **rerun** **`configure_scaling.py`** so **Application Auto Scaling** targets the correct **`endpoint/.../variant/...`** path.

---

### Step 8: Console exploration (optional)

**SageMaker → Endpoints** → choose yours → metrics, configuration, monitoring, logs.

---

### Step 9: Clean up

From **`scripts/`**:

```bash
python cleanup.py
```

Then:

```bash
cd ../infrastructure
terraform destroy -auto-approve
```

**`cleanup.py`** tears down scalable targets/policies, the endpoint/config, **`lab6-`** models from the lab paths, and local **`*.txt`** state trackers.

---

## Lab completion checklist

- [ ] Terraform apply (**~8** resources)
- [ ] **`train_model.py`** → **`model_data_uri.txt`**
- [ ] **`deploy_endpoint.py`** → endpoint **InService**
- [ ] **`test_endpoint.py`** (SDK + runtime + load)
- [ ] **`configure_scaling.py`** (if account allows)
- [ ] Canary **`apply`** / **`promote-green`** (**optional**)
- [ ] **`cleanup.py`** + **`terraform destroy`**

---

## Deployment patterns (context)

| Pattern | Best when |
|---------|-----------|
| **Real-time** | Low latency, interactive apps (**this lab**) |
| **Async inference** | Large payloads / minutes-level latency budgets |
| **Serverless inference** | Spiky traffic / ops minimization posture |
| **Batch transform** | Offline scoring pipelines |

---

## Troubleshooting

| Issue | Guidance |
| --- | --- |
| Endpoint stuck **Creating** | Wait; check quotas + **CloudWatch** logs |
| **`ResourceLimitExceeded`** | Request **`ml.t2.medium`** inference quota lift |
| JSON errors on invoke | **`Accept: application/json`** (**`test_endpoint.py`**) |
| Feature mismatch errors | Exactly **ten** floats per **`text/csv`** row |
| Autoscaling idle | Threshold + cooldown vs **short** load bursts |
| **`promote-green` fails** | Run **`apply`** first; verify **`canary_state.txt`** |

---

## Cost awareness

**`InService`** endpoints bill for provisioned hosting capacity roughly whenever they run, even with low traffic. Always **`cleanup`** in sandboxes after the exercise.

---

## Key takeaways

| Concept | Lesson |
| --- | --- |
| **Artifact contract** | Training tarball + **`inference.py`** define behaviors |
| **Endpoints** | Managed fleet + stable invoke surface |
| **Scaling policies** | Metric-driven capacity vs fixed **1×** fleets |
| **Canary** | Weighted variants before retiring old checkpoints |
| **Hygiene** | Script + **`terraform destroy`** protect shared budgets |
