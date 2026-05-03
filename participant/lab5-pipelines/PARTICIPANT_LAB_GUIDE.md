# Lab 5: CI/CD pipeline with SageMaker Pipelines

## Participant Lab Guide

**Duration:** 90 minutes  
**Difficulty:** Intermediate  
**Module:** 5 — CI/CD  
**AWS Region:** `us-east-1`

---

## Lab objective

You will automate an ML workflow with **SageMaker Pipelines**:

- Run **processing**, **training**, and **evaluation** as ordered steps (**DAG**)  
- **Register** into **Model Registry** only when **`evaluation.json`** shows **accuracy ≥** your **`AccuracyThreshold`** (quality gate)  
- **Parameterize** instance types and **RandomForest** hyperparameters  
- **Start executions** locally and optionally **automate starts** via **EventBridge** when uploads land under **`new-data/`**  
- Inspect runs and logs in **SageMaker Studio / Console**

---

## What you will build

- A SageMaker Pipeline: **`PreprocessData` → `TrainModel` → `EvaluateModel` → `CheckAccuracy`** (conditional branch)
- Conditional **model package registration** when the gate passes (**`RegisterModelPackage`** step inside the SDK’s register collection)
- Optional **EventBridge** rule (**`lab5-trigger-pipeline-<suffix>`**) targeting **`StartPipelineExecution`**
- **State files** under **`labs/lab5-pipelines/scripts/`**: **`pipeline_name.txt`**, **`pipeline_execution_arn.txt`**

Technical reference: [`labs/lab5-pipelines/LAB_OVERVIEW.md`](../../labs/lab5-pipelines/LAB_OVERVIEW.md).

---

## Why CI/CD-style pipelines matter for ML

Ad-hoc notebooks and one-off CLI runs are hard to replay, observe, or hand off to operations. **Pipelines** give you a repeatable graph, parameterized runs, lineage-friendly artifacts in **S3**, and a visual **DAG** when you need to explain what ran and in what order.

---

## AWS services you will use

| Service | Purpose |
|---------|---------|
| **SageMaker Pipelines** | DAG, parameters, **ConditionStep**, registration step |
| **SageMaker Processing** | **`preprocess.py`** and **`evaluate.py`** |
| **SageMaker Training** | **`SKLearn`** + **`train.py`** |
| **Model Registry** | New package versions when the condition passes (**default:** **`PendingManualApproval`**) |
| **S3** | Data outputs, trained **`model.tar.gz`**, staging for pipeline scripts |
| **EventBridge** (optional) | Object Created under **`new-data/`** triggers a run |
| **CloudWatch Logs** | Processing / training / evaluation logs (via console step drill-down) |

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop / VS Code | Recommended |
| Repo cloned (**`mlops-on-aws`**) | Required |
| [**Lab 00**](../lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) (AWS CLI) | Required |
| From **repo root:** `pip install -r requirements.txt` | Required (`boto3`, `sagemaker`, `pandas`, `scikit-learn`, …) |
| Labs 1–4 | Recommended |

---

## Shell note (bash vs PowerShell)

Examples use **bash** (`export`, `cat`). On Windows use **Git Bash**, or mirror with PowerShell (see infra step).

---

## Lab files overview

| Location | Purpose |
| --- | --- |
| **`labs/lab5-pipelines/infrastructure/`** | Terraform: bucket, SageMaker role, EventBridge role, **S3 → EventBridge** notification |
| **`labs/lab5-pipelines/scripts/preprocess.py`** | Step inside **PreprocessData** |
| **`labs/lab5-pipelines/scripts/train.py`** | Training container entry |
| **`labs/lab5-pipelines/scripts/evaluate.py`** | Loads **`model.tar.gz`**, writes **`evaluation.json`** (metrics for the gate) |
| **`labs/lab5-pipelines/scripts/pipeline_definition.py`** | Builds and **upserts** the pipeline |
| **`labs/lab5-pipelines/scripts/run_pipeline.py`** | **`start_pipeline_execution`** + polls |
| **`labs/lab5-pipelines/scripts/trigger_setup.py`** | Create rule (**`EVENTBRIDGE_ROLE_ARN`**) · **`trigger_setup.py delete`** to tear down |
| **`labs/lab5-pipelines/notebooks/pipeline_analysis.ipynb`** | Optional execution listing |

---

## Naming in this repo (not generic placeholders)

Terraform creates a globally unique bucket like **`sagemaker-pipeline-<random>`**.

From **the suffix** (typically the **last eight characters** of that bucket id), scripts derive stable names:

| Object | Pattern |
| --- | --- |
| SageMaker pipeline | **`lab5-churn-pipeline-<suffix>`** |
| Model package group | **`lab5-churn-pipeline-group-<suffix>`** |
| EventBridge rule | **`lab5-trigger-pipeline-<suffix>`** |

**`pipeline_definition.py`** writes **`scripts/pipeline_name.txt`** — use this name in Console/API instead of placeholders like **`churn-pipeline-abc123`**.

---

## Pipeline architecture

```text
PreprocessData ──► TrainModel ──► EvaluateModel ──► CheckAccuracy
                                                      │
                                   accuracy ≥ threshold? ──► RegisterModelPackage (+ substeps)
                                   else ──► branch skipped (no new registry version)
```

The condition reads **`accuracy`** from **`evaluation.json`** (output of **EvaluateModel**), **not** from **`metrics.json`** inside the training tarball (those are auxiliary training-time metrics).

Registered packages default to **`PendingManualApproval`** — consistent with [**Lab 4**](../lab4-registry/PARTICIPANT_LAB_GUIDE.md): automation can propose a candidate; humans or a separate approve step enforce production readiness.

---

## Step-by-step instructions

### Step 1: Open the lab folder

In VS Code: **`mlops-on-aws` → `labs` → `lab5-pipelines`**, then **Open in Integrated Terminal**.

---

### Step 2: Deploy infrastructure

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
code terraform.tfvars
```

Edit **`aws_account_id`** (from Lab 00). Save.

```bash
terraform init
terraform apply -auto-approve
```

Expect **Apply complete** with about **eleven** resources (bucket + versioning + blocking + notification + IAM roles/policies/attachments).

Capture outputs (**still inside `infrastructure/`**):

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw pipeline_role_arn)
export EVENTBRIDGE_ROLE_ARN=$(terraform output -raw eventbridge_role_arn)
```

**PowerShell:**

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw pipeline_role_arn
$env:EVENTBRIDGE_ROLE_ARN = terraform output -raw eventbridge_role_arn
```

---

### Step 3: Create (upsert) the pipeline definition

```bash
cd ../scripts
python pipeline_definition.py
```

This uploads local **`preprocess.py`**, **`evaluate.py`**, and training sources to **S3** (requires the Terraform bucket already created) and registers the pipeline DAG in **`us-east-1`**.

**Expected:** `Pipeline upsert complete: lab5-churn-pipeline-<suffix>`

Artifact: **`pipeline_name.txt`**.

---

### Step 4: Run the pipeline

```bash
python run_pipeline.py
```

Default parameters include **`AccuracyThreshold`: `"0.75"`**. Typical wall clock: **about 12–22 minutes**.

**Rough output shape:**

```text
RUNNING SAGEMAKER PIPELINE
Pipeline: lab5-churn-pipeline-...
Parameters: ...
Started: arn:aws:sagemaker:...
  Pipeline status: Executing
  ...
Final status: Succeeded
```

Artifact: **`pipeline_execution_arn.txt`**.

Monitor in **AWS Console → SageMaker → Pipelines** with the exact name from **`pipeline_name.txt`**.

---

### Step 5: Monitor in the Console

Open the pipeline → pick an execution → **Graph** tab. You should recognize:

- **`PreprocessData`**, **`TrainModel`**, **`EvaluateModel`**  
- **`CheckAccuracy`** branching into **`RegisterModelPackage`** (and internal repack/register substeps shown by SDK) **only when** **`accuracy`** meets the threshold  

Click a step → **Logs** / **Outputs** for investigation.

---

### Step 6: Verify Model Registry appearance

Console: **SageMaker → Model registry**. Find **`lab5-churn-pipeline-group-<suffix>`**.

If **`CheckAccuracy`** passed, a **new package version** should appear — usually with approval status **`PendingManualApproval`** (not automatically **Approved**) unless instructors changed **`pipeline_definition.py`**.

CLI example:

```bash
aws sagemaker list-model-package-groups --region us-east-1 \
  --name-contains lab5-churn-pipeline-group
```

---

### Step 7: Run again with different parameters

Edit **`run_pipeline.py`** — structure **`DEFAULT_PARAMETERS`** — e.g. raise **`AccuracyThreshold`** to **`"0.90"`**, or shrink **`MaxDepth`** / **`NEstimators`**. Save, then **`python run_pipeline.py`**.

**Reflection:** Could the workflow **still show `Succeeded`** while **no registration** occurs? *(Yes — the overall execution can succeed when the branch simply skips **`RegisterModelPackage`**.)*

---

### Step 8: Automatic trigger (optional)

Requires **`EVENTBRIDGE_ROLE_ARN`** set (**Step 2**).

```bash
python trigger_setup.py
```

Creates **`lab5-trigger-pipeline-<suffix>`** observing **`s3://$BUCKET_NAME/new-data/`** (Terraform enables **S3 → EventBridge** for that bucket).

Test:

```bash
echo hello > dummy.txt
aws s3 cp dummy.txt "s3://${BUCKET_NAME}/new-data/hello.txt"
```

List runs:

```bash
PIPELINE=$(cat labs/lab5-pipelines/scripts/pipeline_name.txt)
aws sagemaker list-pipeline-executions --region us-east-1 --pipeline-name "$PIPELINE" --max-results 5
```

If your shell’s cwd is already **`labs/lab5-pipelines/scripts/`**, shorten paths to **`pipeline_name.txt`**.

**PowerShell:** `(Get-Content pipeline_name.txt -Raw).Trim()`.

---

### Step 9: Clean up

1. **If you ran Step 8**, from **`scripts/`**:

```bash
python trigger_setup.py delete
```

2. **Delete the pipeline definition** (finish or stop active executions first if blocked):

```bash
PIPE=$(cat labs/lab5-pipelines/scripts/pipeline_name.txt)
aws sagemaker delete-pipeline --region us-east-1 --pipeline-name "$PIPELINE"
```

3. **Terraform destroy** from **`labs/lab5-pipelines/infrastructure/`**:

```bash
cd labs/lab5-pipelines/infrastructure
terraform destroy -auto-approve
```

Terraform **does not delete** SageMaker Model Package versions or groups created during runs — resolve those in-console if your sandbox rules require.

---

## Lab completion checklist

- [ ] Terraform apply succeeded (**about 11** resources)  
- [ ] **`pipeline_definition.py`** completed; **`pipeline_name.txt`** exists  
- [ ] **`run_pipeline.py`** reached a terminal **`PipelineExecutionStatus`**  
- [ ] Console graph shows preprocess → train → evaluate → condition + conditional register  
- [ ] Registry shows a new package only when **`accuracy`** met **`AccuracyThreshold`**  
- [ ] (Optional) EventBridge-triggered execution observed  
- [ ] **`trigger_setup.py delete`**, **`delete-pipeline`**, **`terraform destroy`** completed  

---

## Concepts recap

| Concept | Meaning | In this lab |
| --- | --- | --- |
| **DAG** | Ordered acyclic workflow | preprocess → train → evaluate → gate |
| **Parameter** | Run-time knobs | Instances, **`NEstimators`**, **`MaxDepth`**, **`AccuracyThreshold`** |
| **Property file / JsonGet** | Read JSON metrics for conditions | **`evaluation.json`** **`accuracy`** |
| **ConditionStep** | Branch without cycles | Registers only if threshold met |
| **Model package** | Registry candidate | **`PendingManualApproval`** after register |

---

## Troubleshooting

| Issue | Guidance |
| --- | --- |
| **`NoSuchBucket`** during **`pipeline_definition.py`** | Run **`terraform apply`** before upsert (code uploads to the bucket). |
| Windows path / code URI quirks | Repo uses **`Path.as_uri()`** for processing scripts; sync to latest **`pipeline_definition.py`**. |
| Gate never rejects | Synthetic data tends to exceed **0.75**; raise **`AccuracyThreshold`** sharply to demo skip. |
| **`trigger_setup.py`** errors | Export **`EVENTBRIDGE_ROLE_ARN`** from **`terraform output`**. |
| Rule never invokes pipeline | Confirm **`new-data/`** prefix, bucket EventBridge forwarding (Terraform **`eventbridge = true`**). |

---

## Key takeaways

| Idea | Lesson |
| --- | --- |
| **Automation & reuse** | One DAG, many runs via parameters. |
| **Quality gates** | Registry intake becomes policy-driven. |
| **Observability** | Each step has logs and S3-linked outputs. |
| **Event-driven retrains** | Optional **`new-data/`** ingestion hook. |
