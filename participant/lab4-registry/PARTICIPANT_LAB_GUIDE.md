# Lab 4: Model Registry & Governance

## Participant Lab Guide

**Duration:** 75 minutes  
**Difficulty:** Beginner  
**Module:** 4 - Governance  
**AWS Region:** `us-east-1`

---

## Lab Objective

In this lab you will use **SageMaker Model Registry** to version, review, and publish models. You will:

- Provision **S3 + IAM** with Terraform for training artifacts  
- **Train** a sklearn classifier and capture the artifact location automatically  
- **Register** a model package ( **`PendingManualApproval`** )  
- Run an **approval** step (**`Approved`** / **`Rejected`**) tied to metric quality  
- **Deploy** only from an approved package via **`deploy_from_registry.py`**  
- Relate registry objects to **governance** and **audit**

---

## What You Will Build

By the end of this lab:

- A **Model Package Group** (logical “product”) for churn-style classifier versions  
- A **registered** model version awaiting approval  
- (If metrics pass threshold) version status → **`Approved`**  
- An **inferencing endpoint** provisioned **from** the Registry  
- Confidence reading **approval status**, **metrics**, and **metadata** in code or Console  

---

## Why Model Registry Matters

Without a registry, “what is running in prod?” turns into folklore. Registry gives a **single index** per model line-of-business: versions, approvals, artifact URIs, and metadata for audits.

---

## AWS Services You Will Use

| Service | Purpose |
|---------|---------|
| **SageMaker Model Registry** | Package groups & versioned approvals |
| **SageMaker Training** | Builds `model.tar.gz` stored in **S3** |
| **SageMaker Hosted Endpoints** | Serves Approved packages |
| **IAM** | Sandboxed privileges (extended in real orgs) |

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop / VS Code | ✅ |
| Repo cloned (**`mlops-on-aws`**) | ✅ |
| [**Lab 00**](../lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) (AWS CLI) | ✅ |
| From **repo root:** `pip install -r requirements.txt` | ✅ |
| Lab 3 optional | Helps with SageMaker job intuition |

---

## Shell note (bash vs PowerShell)

Commands default to **bash**. On Windows, use **PowerShell** snippets where indicated or **Git Bash**.

---

## Lab files overview

| File | Purpose |
| --- | --- |
| **`infrastructure/`** | Terraform: bucket + SageMaker execution role |
| **`scripts/train.py`** | Runs **inside SageMaker** (you do not edit for the happy path) |
| **`scripts/train_model.py`** | Local driver: synthesize CSVs → start training → write **`training_job_name.txt`** + **`model_data_uri.txt`** |
| **`scripts/register_model.py`** | Reads those `.txt` files → group + **`create_model_package`** |
| **`scripts/approve_model.py`** | Policy demo: **`ACCURACY_THRESHOLD`** (default **0.85**) |
| **`scripts/list_models.py`** | Inspect groups / versions |
| **`scripts/deploy_from_registry.py`** | Deploy latest **Approved** package |

Abbreviated cheat sheet: [`labs/lab4-registry/LAB_OVERVIEW.md`](../../labs/lab4-registry/LAB_OVERVIEW.md) (technical reference).

---

## Artifact files (written under `scripts/`)

These small text files stitch steps together—you **do not** paste URIs manually into source code:

| File | Created by |
| --- | --- |
| `training_job_name.txt`, `model_data_uri.txt` | `train_model.py` |
| `model_package_group.txt`, `model_package_arn.txt` | `register_model.py` |
| `endpoint_name.txt` | `deploy_from_registry.py` |

---

## Approval workflow

1. Train → artifact in **S3**  
2. Register → **`PendingManualApproval`**  
3. Review metrics → **`approve_model.py`** sets **`Approved`** or **`Rejected`**  
4. Deploy script only picks **Approved** rows  

Manual human approval in regulated orgs replaces or augments the scripted threshold demo.

---

## Step-by-step instructions

### Step 1: Open the lab folder

VS Code → **mlops-on-aws → labs → lab4-registry** → **Open in Integrated Terminal**.

---

### Step 2: Deploy infrastructure

```bash
cd infrastructure
```

Copy tfvars (**PowerShell:** `Copy-Item terraform.tfvars.example terraform.tfvars`), edit **`aws_account_id`**, then:

```bash
terraform init
terraform apply -auto-approve
```

Expect **8** resources added.

Capture outputs (**stay in `infrastructure/`**):

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw sagemaker_role_arn)
```

PowerShell:

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw sagemaker_role_arn
```

---

### Step 3: Train the model (`train_model.py`)

```bash
cd ../scripts
python train_model.py
```

Roughly **3–6 minutes.**

You should see headings like **`TRAINING MODEL FOR MODEL REGISTRY`**, uploads, **`Training complete`**, plus **S3 `Model artifact`** and **training job name**. The script persists both to **`training_job_name.txt`** and **`model_data_uri.txt`** in **`scripts/`**.

> Synthetic **binary churn-style** CSVs (**`train.csv` / `test.csv`**) also appear locally for debugging—they are regenerated each run.

---

### Step 4: Register the model (**no manual code edits**)

Still in **`scripts/`** with both env vars populated:

```bash
python register_model.py
```

This:

- Optionally honors **`MODEL_PACKAGE_GROUP`** env (otherwise builds `lab4-churn-group-<timestamp>`).  
- Creates / reuses group.  
- Pulls metrics from **`describe_training_job`** (falls back gracefully if CW still syncing).  
- Registers **sklearn-aligned** inference container image (matches **`train.py`** container family).  

Outputs **`PendingManualApproval`**. Persisted names: **`model_package_group.txt`**, **`model_package_arn.txt`**.

> **Important:** Older lab drafts asked you to paste S3 URIs into Python by hand—in **this repo** that is obsolete; the `.txt` state files automate wiring.

---

### Step 5: Approve / reject gate

```bash
python approve_model.py
```

Script lists pending packages, parses embedded metric JSON created at registration time, compares **accuracy** to **`ACCURACY_THRESHOLD`** (**default 0.85**). Override threshold if instructor asks:

```bash
ACCURACY_THRESHOLD=0.80 python approve_model.py
```

PowerShell:

```powershell
$env:ACCURACY_THRESHOLD = "0.80"
python approve_model.py
```

---

### Step 6: Inspect registry listings

```bash
python list_models.py
```

If **`model_package_group.txt`** exists, that group opens first—otherwise script defaults to alphabetically earliest group shown.

Console walkthrough (**optional**): SageMaker → **Register / Model Registry** mirrors the same lineage.

---

### Step 7: Deploy Approved package

Ensure previous step yielded **Approved**:

```bash
python deploy_from_registry.py
```

Endpoint name pattern: **`lab4-registry-<timestamp>`** stored in **`endpoint_name.txt`** (inside **`scripts/`**). Sample inference uses random **10-feature** vectors consistent with synthetic training columns.

Hosted responses look like **`[0.]`** / **`[1.]`** array text from sklearn serializers—formats differ from JSON fantasies sometimes shown in marketing slides.

---

### Step 8: Clean up (avoid ongoing charges)

From **`scripts/`** (endpoint file locality):

```bash
aws sagemaker delete-endpoint --region us-east-1 --endpoint-name "$(cat endpoint_name.txt)"
```

PowerShell:

```powershell
$name = Get-Content endpoint_name.txt -Raw
$name = $name.Trim()
aws sagemaker delete-endpoint --region us-east-1 --endpoint-name $name
```

Then:

```bash
cd ../infrastructure
terraform destroy -auto-approve
```

Terraform **does not delete** SageMaker Registry packages—you may prune them in-console if sandbox policy mandates a blank slate.

---

## Lab completion checklist

- [ ] Terraform apply succeeded  
- [ ] **`train_model.py`** finished → `.txt` files exist  
- [ ] **`register_model.py`** created pending package  
- [ ] **`approve_model.py`** produced decision message  
- [ ] **`list_models.py`** corroborates **Approved** state  
- [ ] **`deploy_from_registry.py`** returned prediction output  
- [ ] Endpoint delete + **`terraform destroy`** executed  

---

## Concepts recap

| Concept | Meaning / lab tie-in |
| --- | --- |
| **Package group** | Namespace for lineage ( churn-style demo ) |
| **Model package** | Concrete version with artifact + approvals |
| **Approval status** | Gating prod deployment readiness |
| **Metadata + metrics blobs** | Auditors reconstruct *why* promoted |
| **Separation** | Training automation vs governance role |

---

## Troubleshooting

| Issue | Guidance |
| --- | --- |
| Register says run **`train_model.py` first** | Missing `.txt` outputs—rerun Step 3 in same cwd |
| Approve rejects unexpectedly | Accuracy under threshold—or metrics still propagating (**lower threshold** transiently ) |
| Deploy: no Approved package | Retry approval script or inspect pending list (`list_models.py`) |
| Delete endpoint denied | IAM path / wrong region (**`us-east-1`**) |

---

## Key takeaways

| Idea | Lesson |
| --- | --- |
| Registry centralizes lineage | Artefact + approvals + searchable metadata |
| Approvals mitigate risk | Default script automates thresholds—prod uses humans + policy |
| Only Approved rows deploy | `deploy_from_registry.py` intentionally filters |

---

## Next steps

Continue with subsequent modules indexed under [`labs/`](../../labs/).
