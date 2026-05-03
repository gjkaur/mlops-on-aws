# Lab 8: End-to-end capstone project

## Participant lab guide

**Duration:** 120–150 minutes  
**Difficulty:** Advanced  
**Module:** 8 — Capstone  
**AWS Region:** `us-east-1`

Technical reference: [`labs/lab8-capstone/LAB_OVERVIEW.md`](../../labs/lab8-capstone/LAB_OVERVIEW.md).

---

## Lab objective

Wire **Labs 4–7** into one story: a **churn-inspired pipeline** that **conditionally registers**, requires **approval**, deploys behind a **duplicated-variant canary (90/10)** **with capture**, attaches **Model Monitor DQ** + **CloudWatch → SNS**, and can be **re-run from S3 uploads** via **EventBridge**.

You will:

- Define and execute a **SageMaker Pipeline** (preprocess → train → evaluate → accuracy gate → register pending)
- **Approve** the package (script + optional console review)
- **Deploy** realtime inference with **Data Capture** retained through a weighted **blue/green** config
- Establish **baseline + monitoring schedule + drift alarm**
- Create an **EventBridge rule** on **`DATA_BUCKET`/new-data/**
- **Simulate traffic + new-batch upload** end-to-end

---

## What you will build

```
NEW CSV under s3://<DATA_BUCKET>/new-data/
        │
        ▼ (EventBridge)
SageMaker Pipeline  →  Pending model package (if accuracy ≥ gate)
        │
        ▼ (you approve)
Deploy (capture preserved) → 90% blue / 10% green (same tarball demo)
        │
        ▼
DQ baseline & hourly schedule → CloudWatch drift metric → SNS email
```

---

## Capstone scenario

**Telco churn** (synthetic). The business wants automation with **safeguards**: registry approvals, observable serving, telemetry for drift, **and** repeatable retrains without manual CLI runs.

Your mission: operate the artefacts in **`labs/lab8-capstone/`**, document the topology, ship simple deliverables listed at the end.

---

## AWS services

| Service | Role here |
|---------|-----------|
| **SageMaker Pipelines** | `PreprocessData` → `TrainModel` → `EvaluateModel` → `CheckAccuracy` → `RegisterModelPackage` |
| **Model Registry** | Group name derived from artefacts bucket (**`lab8-capstone-group-…`**), **PendingManualApproval** by default |
| **Realtime inference** | `SKLearnModel` + local **`inference.py`** (seven-float CSV payload) |
| **Model Monitor (DQ)** | Baseline stripped from preprocessing **`train.csv`**, hourly schedule comparing captures |
| **EventBridge + S3 notifications** | **Data landing bucket only** notifies on **`new-data/`** uploads |
| **CloudWatch / SNS** | Drift **`Sum`** alarms on DQ metrics (**namespace `/aws/sagemaker/Endpoints/data-metric`**) |

---

## Prerequisites

| Requirement | Notes |
| --- | --- |
| [**Lab 00**](../lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) | AWS CLI credibility |
| Root **`pip install -r requirements.txt`** | SageMaker SDK + pandas stack |
| **Labs 1–7 familiarity** | Shortens narration (not hard-blocked — expect longer time if nets new) |

---

## Shell vs PowerShell

Bash excerpts use **`export`**. Windows PowerShell example after **`terraform apply`**:

```powershell
$env:DATA_BUCKET_NAME       = terraform output -raw data_bucket_name
$env:ARTIFACTS_BUCKET_NAME = terraform output -raw artifacts_bucket_name
$env:CAPTURE_BUCKET_NAME    = terraform output -raw capture_bucket_name
$env:REPORTS_BUCKET_NAME    = terraform output -raw reports_bucket_name
$env:SAGEMAKER_ROLE_ARN    = terraform output -raw sagemaker_role_arn
$env:EVENTBRIDGE_ROLE_ARN  = terraform output -raw eventbridge_role_arn
$env:SNS_TOPIC_ARN         = terraform output -raw sns_topic_arn
```

---

## Lab inventory (`labs/lab8-capstone/`)

| Path | Responsibility |
| --- | --- |
| **`infrastructure/`** | Four buckets (**data**/events, **artifacts** + versioning, **capture**, **reports**), SNS + IAM, EventBridge role |
| **`scripts/preprocess.py`** | Builds synthetic churn features → **`train.csv` / `test.csv`** (**no CSV header**) |
| **`scripts/train.py` / `evaluate.py`** | Training + downstream evaluation artefacts |
| **`scripts/pipeline_definition.py`** | **Upserts** pipeline + writes **`pipeline_name.txt`**, **`model_package_group.txt`** |
| **`scripts/run_pipeline.py`** | Starts execution → **`preprocess_train_s3_uri.txt`** helper for monitoring baseline |
| **`scripts/approve_model_package.py`** | Approves (**default**) latest pending registration |
| **`scripts/deploy_canary.py`** | Capture-enabled deploy + duplicated **blue/green** weights |
| **`scripts/monitoring_setup.py`** | Baseline DQ job + hourly schedule + CloudWatch linkage |
| **`scripts/trigger_retraining.py`** | EventBridge **`put_rule`/`put_targets`** (`delete` subcommand removes them) |
| **`scripts/simulate_workflow.py`** | Predict smoke + uploads **`new-data/capstone-simulated-batch.csv`** |
| **`scripts/cleanup.py`** | Drops SageMaker + alarm + EB targets (Terraform still owns buckets/IAM unless destroyed) |

State crumbs (`*.txt`, `*.json`) land beside **`scripts/`** — keep that folder your working directory once Terraform finishes.

---

## CSV / inference contract

**Seven numeric features** matching preprocessing column order (**label is not sent at inference time**):

1. **`tenure`**
2. **`monthly_charges`**
3. **`support_tickets`**
4. **`payment_delays`**
5. **`contract_type_Month-to-month`** (one-hot **0** or **1**)
6. **`contract_type_One year`**
7. **`contract_type_Two year`** (exactly one contract column **`1`** per row)

**JSON response:**

```json
{"prediction": 0, "probability_positive": 0.72}
```

Reference row: **`data/sample_churn_data.csv`**.

---

## Step-by-step instructions

### Step 1 — Open **`labs/lab8-capstone`**

Use **Integrated Terminal** at repo root conventions (same pattern as Labs 6–7).

---

### Step 2 — Terraform

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars   # Windows: Copy-Item …
code terraform.tfvars                          # Provide alert_email; aws_account_id optional
terraform init
terraform apply -auto-approve
```

Expect **`Apply complete!`** with roughly **two dozen** manageable objects (four buckets & policies + IAM + SNS, etc.—exact tally drifts slightly with AWS provider bumps).

Persist outputs (**bash** excerpt earlier; PowerShell snippet above mirrors it).

Buckets created:

| Output env | Responsibility |
|-----------|----------------|
| **`DATA_BUCKET_NAME`** | **`new-data/`** landing + EventBridge |
| **`ARTIFACTS_BUCKET_NAME`** | Pipeline upload roots / training outputs |
| **`CAPTURE_BUCKET_NAME`** | Inference capture prefix **`lab8/data-capture/`** |
| **`REPORTS_BUCKET_NAME`** | Baseline + monitoring artefacts published by DQ jobs |

---

### Step 3 — Confirm SNS inbox

Approve the **`mlops-capstone-alerts-*`** subscription message before expecting drift emails.

---

### Step 4 — Pipeline upsert & execution

```bash
cd ../scripts
python pipeline_definition.py      # emits pipeline_name + model package group
```

Pipeline names look like **`lab8-capstone-pipeline-<8-char-suffix>`** (suffix comes from artefacts bucket spelling).

(Optional) Export **`CAPSTONE_ACC_GATE`** before **`run_pipeline.py`** to raise/lower **`AccuracyThreshold`** (defaults **`0.75`** when omitted):

```bash
export CAPSTONE_ACC_GATE=0.80        # example: gate registration at ≥ 80% accuracy
python run_pipeline.py
```

Stages you should recognise in SageMaker Console: **Preprocess → Train → Evaluate → CheckAccuracy**. When accuracy ≥ threshold, **`RegisterModelPackage`** runs and you see **`PendingManualApproval`**.

Artifacts:

- **`pipeline_execution_arn.txt`**, **`pipeline_terminal_status.txt`**
- **`preprocess_train_s3_uri.txt`** (**needed by monitoring** once present)

Budget **10–20 minutes wall clock** typical classroom SKLearn workers.

---

### Step 5 — Approve pending package (**script-first**)

Preferred path (automates approvals at the keyboard):

```bash
python approve_model_package.py
```

Produces **`approved_model_package_arn.txt`** when **`CAPSTONE_APPROVAL`** (default **`Approved`**) resolves the newest pending artifact.

Alternative / supplement: SageMaker Console → Model registry → **`lab8-capstone-group-…`** manual review referencing metrics surfaced in **`evaluation.json`**.

Evaluate metrics surfaced in-registry are **accuracy, precision, recall, AUC** (no separate **F1** column in shipped evaluate step).

---

### Step 6 — Canary realtime endpoint

Requirements: prior approval + **`SAGEMAKER_ROLE_ARN`**, **`CAPTURE_BUCKET_NAME`**.

```bash
python deploy_canary.py
```

This **already enables capture** (`lab8/data-capture/…`) **before** rewriting the endpoint configuration for **weighted routing** while cloning the existing **`DataCaptureConfig`**.

Writes **`endpoint_name.txt`**, **`capture_s3_uri.txt`**, **`canary_models.json`**, **`canary_endpoint_config.txt`**.

---

### Step 7 — Monitoring + alarm

Expose **`REPORTS_BUCKET_NAME`**, **`SNS_TOPIC_ARN`**, and ensure **`endpoint_name.txt` + preprocess train URI breadcrumbs exist**:

```bash
python monitoring_setup.py
```

Produces baseline objects under **`s3://<REPORTS>/lab8/...`**, a **data-quality monitoring schedule**, and a CloudWatch alarm whose name resembles **`lab8-drift-<endpoint-suffix>-<unix>`**.

Optional facilitator shortcut (narrow windows):

```bash
export LAB8_MONITOR_NOW=1 LAB8_NOW_START=-P1D LAB8_NOW_END=-PT1S
python monitoring_setup.py     # rerun only if schedule deleted beforehand
```

---

### Step 8 — Automated retraining trigger

```bash
python trigger_retraining.py
echo $DATA_BUCKET_NAME         # uploads must land ONLY under DATA bucket new-data prefix
```

`python trigger_retraining.py delete` deletes the persisted rule/target when rehearsing teardown.

---

### Step 9 — Full-path simulation

```bash
python simulate_workflow.py
```

Issues a handful of **seven-float** payloads to the realtime endpoint plus drops **`new-data/capstone-simulated-batch.csv`** into **`DATA_BUCKET_NAME`**. Expect eventual **duplicate pipeline executions** if you spam uploads—coordinate with facilitator.

---

### Step 10 — Observe artefacts

**Pipelines**: SageMaker Console → **Pipelines → Executions**.

**Endpoints**: Inference → **`endpoint_name`** + variant weights.

**Model registry**: **`lab8-capstone-group-<suffix>`**.

**Monitoring**: DQ schedule executions + **`lab8/monitoring-reports/`** prefixes on reports bucket.

**CloudWatch Metrics**: **`/aws/sagemaker/Endpoints/data-metric`**, dims **`EndpointName` + ScheduleName**.

**Alarm state**: **`lab8-drift-*`**.

Captures accumulate under **`s3://<CAPTURE_BUCKET>/lab8/data-capture/`**.

---

### Step 11 — Cleanup discipline

Always delete orchestrated artefacts before Terraform when possible:

```bash
python cleanup.py                      # wipes EB targets, DQ schedule, CW alarm hints, realtime stack, pipeline defs
python trigger_retraining.py delete    # if rule survived cleanup edge cases
cd ../infrastructure
terraform destroy -auto-approve
```

---

## Capstone deliverables

| Deliverable | Guidance |
| --- | --- |
| **Architecture diagram** | Sketch **four buckets**, EventBridge on **DATA** lane, SageMaker primitives, DQ + SNS path |
| **Pipeline evidence** | Point reviewers at repo **`scripts/`** + execution IDs / screenshots |
| **Model Card** | Short Markdown/PDF tying metrics + limitations + lineage |
| **5-minute narration** | Emphasise *what automates*, *what human gate still oversees*, *how drift surfaces* |

### Model Card starter (adapt numbers from **Console / `evaluation.json`**)

```markdown
# Model Card — Lab 8 Churn surrogate

## Model type
RandomForestClassifier (sklearn container 1.2-1) serving JSON probability payload.

## Training data synopsis
Synthetic **5 000-row** preprocessing job (inside pipeline).

## Inputs (seven CSV floats)
Tenure-like numeric stream + categorical **month-to-month / one-year / two-year** one-hot triplet (**exact order** mandated).

## Reported offline metrics bundle
Accuracy • Precision • Recall • ROC-AUC (see pipeline evaluation artefact).

## Limitations / operational caveats
- Canary variants currently clone identical containers (teaching stress test).
- EventBridge-triggered executions may backlog if students spam uploads concurrently.
```

---

## Troubleshooting

| Symptom | Guidance |
|---------|----------|
| Pipeline stuck / failed **`CheckAccuracy`** | Lower **`CAPSTONE_ACC_GATE`** or widen synthetic churn RNG (ask instructor — avoid editing container code blindly) |
| **No Pending package** after run | Accuracy below threshold OR register step aborted — revisit pipeline graph |
| **deploy_canary denied** | Approve artifact first; inspect **`Approved` status** in registry |
| **monitoring baseline missing preprocess URI** | Rerun **`run_pipeline.py`** to completion; inspect **`PreprocessData` ProcessingJob outputs** manually if needed |
| **No SNS email** | Confirm subscription **and** that alarm ARN lists topic as action |
| **EventBridge silence** | Ensure object lands on **DATA bucket** **`new-data/`** prefix |

---

## Success criteria checklist

Check each before declaring completion:

- [ ] Terraform sandbox created + SNS subscription confirmed  
- [ ] Pipeline execution **Succeeded**  
- [ ] Accuracy gate behaviour understood (raised / lowered consciously)  
- [ ] Approved package artifact exists  
- [ ] Canary endpoint **InService**, capture prefix receiving objects after simulation  
- [ ] DQ baseline + hourly schedule **`Scheduled`** (+ optional NOW demo)  
- [ ] Uploaded **`new-data/** object produced at least one new execution trace** OR instructor validated rule  
- [ ] **`cleanup.py` + terraform destroy`** executed in teaching account policy window  

---

## Congratulations

Completing Lab 8 means you can articulate how **training automation**, **governance choke points**, **serving ergonomics**, and **telemetry** braid together—not just run isolated widgets.
