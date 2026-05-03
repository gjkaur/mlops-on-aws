# Lab 5: CI/CD pipeline with SageMaker Pipelines — Instructor guide

## Lab overview

| Attribute | Value |
|-----------|-------|
| **Duration** | 90 minutes |
| **Difficulty** | Intermediate |
| **Module** | 5 — CI/CD |
| **AWS region** | `us-east-1` |

---

## Learning objectives

By the end of the lab learners can:

1. Compose a SageMaker Pipeline with **processing**, **training**, and **evaluation** steps.  
2. Route **successful** evaluations to **Model Registry** using a **`ConditionStep`**.  
3. Parameterize instance types, **RandomForest** hyperparameters, and an **accuracy threshold**.  
4. **Optionally** trigger **`StartPipelineExecution`** from **EventBridge** on **`s3://…/new-data/`** uploads.  
5. Relate the console **DAG** view to the script-defined graph.

---

## AWS services

| Service | Role in this lab |
|---------|------------------|
| **SageMaker Pipelines** | DAG + parameters + conditions |
| **Processing** | Preprocess + evaluate (sklearn container 1.2-1) |
| **Training** | sklearn **`SKLearn`** training job |
| **Model Registry** | **`RegisterModel`** step collection |
| **S3** | Data, artifacts, code staging, optional trigger prefix |
| **EventBridge** | Optional rule targeting the pipeline ARN |
| **IAM** | SageMaker pipeline role + EventBridge invocation role |

---

## Repository layout (implemented)

See [`LAB_OVERVIEW.md`](LAB_OVERVIEW.md). Terraform adds **`eventbridge = true`** on **`aws_s3_bucket_notification`** so **`aws.s3` / Object Created** rules can fire without legacy S3-only notifications mixed in.

---

## Technical notes (critical for facilitation)

### 1. Condition logic must stay inside the Pipeline DSL

Teaching drafts sometimes show **boto3 + S3 reads** `.apply(lambda ...)` inside the graph definition. SageMaker resolves conditions from **workflow expressions**. This lab uses **`JsonGet`** bound to a **`PropertyFile`** over **`evaluation.json`** from **`EvaluateModel`**, compared to **`ParameterFloat AccuracyThreshold`**.

### 2. Evaluation step consumes **`model.tar.gz`**

Training produces a tarball.**`evaluate.py`** extracts **`*.tar.gz`** locally, loads **`model.joblib`**, and writes **`evaluation.json`** (accuracy, precision, recall, auc).

### 3. Windows path caveat

**`ProcessingStep(code=…)`** on Windows must not pass raw **`D:\…`** paths to the urllib-based code uploader (**`pipeline_definition.py`** uses **`Path(...).resolve().as_uri()`**).

### 4. **`RegisterModel` approval**

Default code registers with **`approval_status="PendingManualApproval`** (aligns with governance in module 4). To demo “auto-approved” registry rows, pass **`approval_status="Approved"`** in **`pipeline_definition.py`** and re-**`upsert`**.

### 5. First **`definition()` / `upsert()`** may upload code

**`PipelineSession`** stages local scripts to S3; the destination bucket must **exist** (Terraform) before **`pipeline_definition.py`** succeeds.

---

## Facilitator dry run

```bash
cd labs/lab5-pipelines/infrastructure
cp terraform.tfvars.example terraform.tfvars   # set aws_account_id
terraform init
terraform apply -auto-approve

export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw pipeline_role_arn)
export EVENTBRIDGE_ROLE_ARN=$(terraform output -raw eventbridge_role_arn)

cd ../scripts
python pipeline_definition.py
python run_pipeline.py
# Optional:
python trigger_setup.py
aws s3 cp some-file.txt "s3://$BUCKET_NAME/new-data/hello.txt"

# Tear down triggers then infra
python trigger_setup.py delete
cd ../infrastructure
terraform destroy -auto-approve
```

PowerShell replaces **`export`** with **`$env:NAME = terraform output …`**.

---

## Expected learner-visible outcomes

After **`pipeline_definition.py`:**

- SageMaker Console → **Pipelines** lists **`lab5-churn-pipeline-<suffix>`**  
- **`scripts/pipeline_name.txt`** present  

After **`run_pipeline.py`** (typical synthetic data):

- **`Succeeded`** with branch **RegisterModel** when accuracy ≥ **`AccuracyThreshold`**  
- **`PipelineExecutionSucceeded`** notification in step history  

If **`AccuracyThreshold`** is unrealistically high, the run can **succeed** while the **`else`** branch skips registration—use this deliberately to demo **gates**.

---

## Console DAG (conceptual)

```text
PreprocessData → TrainModel → EvaluateModel → CheckAccuracy
                                                  │
                                                  ├─► RegisterModelPackage (if pass)
                                                  └─► (no register)           (if fail)
```

---

## Common learner issues

| Symptom | Likely fix |
|---------|------------|
| **`NoSuchBucket`** on upsert / run | Forgot Terraform apply before scripts |
| **`code … url scheme d`** (Windows) | Ensure repo uses **`as_uri()`** pattern in **`pipeline_definition.py`** |
| Property file missing | **`EvaluateModel`** must list **`evaluation` output + `property_files=[evaluation_report]`** |
| EventBridge fires but pipeline never starts | Rule target **`RoleArn`**, **`SageMakerPipelineParameters`**, and pipeline ARN; confirm bucket EventBridge forwarding |
| Stuck **`Executing`** | Normal for 15+ minutes; drill into failing step logs |

---

## Cleanup reminder

Terraform **never** deletes **model package** versions created by the pipeline. If sandboxes must be empty, delete those resources in the console or with APIs after **`terraform destroy`**.

---

## Reference

Condensed implementation notes: [`../../solutions/lab5/LAB5_SOLUTION_REFERENCE.md`](../../solutions/lab5/LAB5_SOLUTION_REFERENCE.md).
