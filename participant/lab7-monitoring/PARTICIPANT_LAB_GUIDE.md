# Lab 7: Model monitoring & drift detection

## Participant lab guide

**Duration:** 90 minutes  
**Difficulty:** Intermediate  
**Module:** 7 — Monitoring  
**AWS Region:** `us-east-1`

Technical reference: [`labs/lab7-monitoring/LAB_OVERVIEW.md`](../../labs/lab7-monitoring/LAB_OVERVIEW.md).

---

## Lab objective

Learn how production ML teams **capture inference traffic**, build a **data-quality baseline**, run **scheduled Model Monitor comparisons**, and **raise alerts** when live inputs drift away from what the model was trained on.

You will:

- Enable **Data Capture** so requests and responses are written to **S3**
- Run a SageMaker processing job that produces **statistics** and **constraints** from **training-era features**
- Create an **hourly data-quality monitoring schedule** that contrasts captures against that baseline
- Create a **CloudWatch alarm** and route it through **SNS** (email)
- **Stress the endpoint with shifted synthetic data** to make drift observable after the schedule runs

---

## What you will build

By the end of this lab:

- **`lab7-monitored-endpoint-<timestamp>`** (or your **`LAB7_ENDPOINT_NAME`** override) with **`DataCaptureConfig`** → captures under **`s3://<bucket>/lab7/data-capture/`**
- Baseline artefacts **`statistics.json`** / **`constraints.json`** under **`s3://<bucket>/lab7/baseline-output/`** (exact keys come from processing output)
- A **monitoring schedule** emitting CloudWatch metrics in **`/aws/sagemaker/Endpoints/data-metric`**
- Optionally an **alarm** (**`lab7-drift-…`**) wired to **`SNS_TOPIC_ARN`** with **confirmed email subscription**

---

## Why model monitoring matters

**The problem:** Models can degrade silently. Business KPIs slide before anyone opens a notebook.

**The approach:** Persist what the endpoint saw (**capture**), define **“normal”** from an approved baseline, and **schedule** comparisons so operators get **early signal** (**metrics + reports + alarms**).

---

## Types of drift

| Drift type | What changes | Example |
| --- | --- | --- |
| **Data drift** | Input distribution | Population age or spend shifts |
| **Concept drift** | Feature → label relationship changes | Fraud pattern evolves |
| **Quality drift** | Missing/bad payloads | Broken upstream ETL |

**This lab emphasizes data-quality monitoring** against a **tabular feature baseline** (same 10 floats you send at inference).

---

## AWS services you will use

| Service | Purpose |
| --- | --- |
| **SageMaker Training** | Builds **`model.tar.gz`** for the monitored endpoint |
| **SageMaker Model Monitor** | Baseline suggestion + scheduled data-quality checks |
| **SageMaker Endpoints** | Real-time inference subject to capture |
| **CloudWatch** | **`feature_baseline_drift_<column>`** and related metrics |
| **SNS** | Email notifications from alarms |
| **S3** | Captures (`lab7/data-capture/`), baseline outputs, monitoring reports |

---

## How Model Monitor fits together

```
1) Data capture writes CSV/JSON traffic to S3
        │
        ▼
2) Baseline job summarizes “expected” feature stats + constraints from training-era CSV
        │
        ▼
3) Schedule (e.g., hourly cron) aggregates recent captures vs baseline → metrics + violation reports in S3
        │
        ▼
4) CloudWatch alarm (optional) → SNS email when drift metric crosses threshold
```

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop / VS Code | Recommended |
| Repo cloned (**`mlops-on-aws`**) | Required |
| [**Lab 00**](../lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) | Required (CLI, credential hygiene) |
| **`pip install -r requirements.txt`** at repo root | Required |
| **Lab 6** | Recommended (same CSV + JSON inference style) |

This lab is **mostly self-contained** (training + deployment happen here too), but Lab 6 makes the **`CSVSerializer`** / **`Predictor`** story familiar.

---

## Shell note (bash vs PowerShell)

Examples use **`export`** (bash). On Windows PowerShell:

```powershell
cd infrastructure
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw monitoring_role_arn
$env:SNS_TOPIC_ARN = terraform output -raw sns_topic_arn
cd ..\scripts
```

---

## Lab files overview (`labs/lab7-monitoring/`)

| Path | Purpose |
| --- | --- |
| **`infrastructure/`** | Terraform: bucket + versioning + IAM + **SNS topic + email subscription** |
| **`scripts/train.py`** | Container training (**RandomForest**, 11-column CSV incl. label **without header**) |
| **`scripts/train_model.py`** | Uploads **`train.csv`**, **`baseline_features.csv`**, runs **`SKLearn`** job → **`model_data_uri.txt`**, **`baseline_features_s3_uri.txt`** (**must run before deploy**) |
| **`scripts/inference.py`** | Realtime inference (**JSON** with **`prediction`**, **`probability_positive`**) |
| **`scripts/deploy_with_capture.py`** | Deploy with **`DataCaptureConfig`** (**`lab7/data-capture/`**) |
| **`scripts/generate_baseline.py`** | **`DefaultModelMonitor.suggest_baseline`** (**headerless** 10-feature CSV) |
| **`scripts/create_monitoring_schedule.py`** | Hourly default schedule → **`schedule_name.txt`** |
| **`scripts/test_endpoint.py`** | Invoke endpoint + optionally list **`lab7/data-capture/`** keys (**needs `BUCKET_NAME`**) |
| **`scripts/setup_alerts.py`** | CloudWatch drift alarm + optional SNS wiring |
| **`scripts/simulate_drift.py`** | Normal then shifted **`numpy`** traffic |
| **`scripts/cleanup.py`** | Drops schedule/job definition scaffolding, alarm, endpoint, local `*.txt` helpers |
| **`notebooks/monitoring_analysis.ipynb`** | Optional S3 key listing snippet |

Small **`*.txt`** state files (**`endpoint_name.txt`**, **`statistics_s3_uri.txt`**, etc.) are written beside the scripts — **they tie steps together.**

---

## Request / response shape

- **Input:** **`text/csv`** with **exactly ten** floats (matching **`make_classification(..., n_features=10)`**).
- **`inference.py` JSON:**

```json
{"prediction": 0, "probability_positive": 0.712}
```

---

## Step-by-step instructions

---

### Step 1: Open the lab folder

1. **`mlops-on-aws/labs/lab7-monitoring`**
2. **Open in Integrated Terminal**

---

### Step 2: Deploy infrastructure

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars   # Git Bash / macOS / Linux
# Windows (PowerShell): Copy-Item terraform.tfvars.example terraform.tfvars

code terraform.tfvars
```

- Set **`alert_email`** — **required** (**SNS** subscription).
- **`aws_account_id`** may stay empty (`""`) in this Terraform pack; keeping your account ID nearby is optional.

```bash
terraform init
terraform apply -auto-approve
```

Expect **`Apply complete!`** with **about ten** resources (**bucket helpers + IAM + SNS**).

Exports:

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw monitoring_role_arn)
export SNS_TOPIC_ARN=$(terraform output -raw sns_topic_arn)
```

---

### Step 3: Train packaged model **before** deploying

Monitoring depends on **`model.tar.gz`**. **`deploy_with_capture.py`** reads **`model_data_uri.txt`**.

```bash
cd ../scripts
python train_model.py
```

This regenerates **`train.csv`**, uploads **`baseline_features.csv`** (**10 numeric columns**, **no header**), and submits **`lab7-monitoring-train`**. Typical wall clock **five minutes** upstream of capture.

Keep **`export BUCKET_NAME` / `export ROLE_ARN`** alive in **this terminal session**.

---

### Step 4: Deploy realtime endpoint **with capture**

```bash
python deploy_with_capture.py
```

You should see:

- **`DEPLOY REAL-TIME ENDPOINT WITH DATA CAPTURE`**
- **`capture_s3_uri=s3://<bucket>/lab7/data-capture/`**
- Provision **~ 5–10 minutes**

---

### Step 5: Confirm SNS email subscription

1. Email from **AWS Notifications**
2. **Confirm subscription** before expecting alarm emails.

(Re-run Terraform SNS resource if email was wrong.)

---

### Step 6: Generate baseline

```bash
python generate_baseline.py
```

- Uses **`lab7/baseline-input/baseline_features.csv`** (already uploaded by **`train_model.py`**)
- Saves **`statistics_s3_uri.txt`** + **`constraints_s3_uri.txt`**
- Baseline processor ~ **5–15 minutes**

Baseline answers: *what did the monitored 10-vector look like when we trusted the dataset?*

---

### Step 7: Create hourly monitoring schedule

```bash
python create_monitoring_schedule.py
```

- Schedule name saved as **`schedule_name.txt`**
- Default cron **hourly top-of-hour** (**`cron(0 * ? * * *)`** pattern from the SDK helper)
- First execution **might not coincide with class time** — plan to revisit results after **`+60 min`** unless your instructor demonstrates **`LAB7_MONITOR_NOW=1`**

<details>
<summary>Optional: one-shot “NOW” demo (narrow windows can miss buffered captures—instructor-guided)</summary>

```bash
export LAB7_MONITOR_NOW=1 LAB7_NOW_START=-P1D LAB7_NOW_END=-PT1S
python create_monitoring_schedule.py
```

Discuss with your facilitator before overwriting an existing schedule (**delete first**).

</details>

---

### Step 8: Smoke-test invokes + skim captures

Ensure **`export BUCKET_NAME=...`** is still set:

```bash
python test_endpoint.py
```

Listing uses prefix **`lab7/data-capture/`**. If counts are **`0`**, wait **two minutes** — capture delivery is asynchronous.

---

### Step 9: Wire CloudWatch → SNS drift alarm

```bash
python setup_alerts.py
```

- Requires **`schedule_name.txt`**, **`statistics_s3_uri.txt`**, **`endpoint_name.txt`**
- Alarm targets **`feature_baseline_drift_<firstBaselineFeature>`** namespace **`/aws/sagemaker/Endpoints/data-metric`**
- **`AlarmActions`** include **`SNS_TOPIC_ARN`** when exported

Customize threshold if directed:

```bash
export LAB7_DRIFT_ALARM_THRESHOLD=0    # strictly positive Sum trips > 0
python setup_alerts.py
```

---

### Step 10: Simulate drifting traffic

```bash
python simulate_drift.py
```

Sequences **in-distribution** Gaussian pulls then **strongly shifted** pulls to stress empirical differences.

Interpretation caveat: hourly automation — **immediate email is not guaranteed** until the cron processes enough captured records.

---

### Step 11: Review artefacts

**A. CloudWatch → Metrics → All metrics**

Filter for the namespace **`/aws/sagemaker/Endpoints/data-metric`**. Use dimension **`EndpointName`** (matches **`endpoint_name.txt`**) and **`ScheduleName`** (matches **`schedule_name.txt`**). Example metric: **`feature_baseline_drift_<column>`**. See [**Interpreting CloudWatch metrics**](https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor-interpreting-cloudwatch.html).

**B. S3 reports**

Browse **`lab7/reports/`** for execution folders (violations CSV/JSON artefacts depend on scheduler output).

**C. SageMaker console**

Monitoring schedules → executions — deep link from your facilitator if enabled.

Optional notebook: **`notebooks/monitoring_analysis.ipynb`** (set **`PREFIX_REPORTS`** to **`lab7/reports/`**).

---

### Step 12: Cleanup

Always tear down SageMaker artefacts before dropping Terraform when possible:

```bash
python cleanup.py
cd ../infrastructure
terraform destroy -auto-approve
```

Unset environment variables tied to sandbox ARNs afterward.

---

## Lab completion checklist

- [ ] Terraform applied (**bucket + SNS + IAM** confirmed)
- [ ] **`train_model.py`** finished (**baseline features + tarball** paths exist)
- [ ] **`deploy_with_capture.py`** reached **InService** + **`lab7/data-capture`** prefix reachable
- [ ] SNS inbox **Confirmed**
- [ ] **`generate_baseline.py`** produced **`statistics_s3_uri.txt`**
- [ ] **`create_monitoring_schedule.py`** persisted **`schedule_name.txt`**
- [ ] **`test_endpoint.py`** generated traffic + **`setup_alerts.py`** built alarm (**optional SNS test** confirmed by facilitator)
- [ ] **`simulate_drift.py`** executed
- [ ] At least **one inspection path** exercised (**CloudWatch**, **S3 reports**, or **console execution** view)
- [ ] **`cleanup.py`** + **`terraform destroy`**

---

## Monitoring concepts recap

| Concept | Meaning | Location this lab |
| --- | --- | --- |
| **Data capture** | Stores serialized requests/responses | **`lab7/data-capture/`** |
| **Baseline** | Training-era reference stats/constraints | **`lab7/baseline-output`** processing outputs |
| **Monitoring schedule** | Recurring DQ job vs baseline | **`schedule_name.txt`** identity |
| **Drift metric (example)** | **`feature_baseline_drift_<col>` Sum** vs threshold | **`/aws/sagemaker/Endpoints/data-metric`** |
| **Remediation** | Investigate ingestion, approvals, **rebaseline**, or **retrain** | Out of scope but discuss |

Constraint-violation **reports** complement CloudWatch aggregates — read both once available.

---

## Example alert email (**illustrative**)

Exact wording depends on SNS + alarm configuration. Typical pattern:

```
Subject: ALARM ... lab7-drift-...

Cause: Threshold Crossed ...
```

Treat any sample body as pedagogical—not a guaranteed template.

---

## Troubleshooting

| Issue | Resolution |
| --- | --- |
| **`deploy_with_capture.py`** errors **`model_data_uri.txt`** | Run **`train_model.py`** first in same shell with **`ROLE_ARN`**, **`BUCKET_NAME`**. |
| Baseline **`AccessDenied`** / missing object | Bucket policy / wrong prefix — confirm uploads under **`lab7/baseline-input/baseline_features.csv`**. |
| Baseline rejects CSV | Expected **headerless**, **exactly ten** numeric columns (**no label column here**). |
| Zero capture listings | Wait **2–3 min** post-invoke; ensure **`SamplingPercentage=100`** (script default); verify prefix **`lab7/data-capture/`**. |
| No drift observation yet | Cron is **hourly** — revisit after **`Top of hour`**; confirm shifted traffic preceded window. |
| Alarm never transitions | Inspect dimensions (**`EndpointName`**, **`ScheduleName`**) and metric **`feature_baseline_drift_<...>`**. |
| No email | Spam + **Confirmed subscription** + alarm **`AlarmActions`** includes topic ARN (**`setup_alerts.py`** needs **`SNS_TOPIC_ARN`**). |

---

## Interpreting drift signals (primer)

| Signal | Typical reading |
| --- | --- |
| **`feature_baseline_drift_<name>`** | Built-in DQ drift indicator per monitored column *(see AWS Model Monitor interpreting CloudWatch docs)* |
| **`constraint_violations.json`** (reports) | Human-readable deltas vs thresholds |
| **PSI-style analytics** *(external)* | PSI **> ~0.25** often flagged in finance-style monitoring — SageMaker DQ focuses on distributions + thresholds here |

Consult facilitator for domain-specific alerting standards.

---

## Key takeaways

| Idea | Lesson |
| --- | --- |
| **Capture-first** | You cannot retrospectively analyse traffic you never stored |
| **Shape discipline** | Baseline CSV rows must mirror production encodes (**10 floats**, **no stray header**) |
| **Operational cadence** | Schedules amortise monitoring cost vs ad-hoc audits |
| **Alert wiring** | CloudWatch thresholds operationalise reports into wake-up calls (**SNS**) |
| **Human follow-up** | Drift telemetry starts investigation — it rarely auto-fixes pipelines |
