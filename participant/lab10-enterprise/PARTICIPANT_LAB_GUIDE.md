# Lab 10: Enterprise MLOps with Projects

## Participant Lab Guide

**Duration:** 60 minutes  
**Difficulty:** Intermediate  
**Module:** 10 — Enterprise MLOps  
**AWS Region:** `us-east-1`

---

## Lab objective

You will use **SageMaker Studio** and the AWS console to create a **SageMaker MLOps Project** from AWS’s **standard model build / train / deploy** template, inspect the **automatically provisioned** CI/CD and ML artefacts, make a **small git-backed code change** to trigger automation, and practise the **model approval** path in **Model Registry** (where your organisation allows it).

Technical reference: [`labs/lab10-enterprise/LAB_OVERVIEW.md`](../../labs/lab10-enterprise/LAB_OVERVIEW.md).

Earlier context: **[Lab 4](../lab4-registry/PARTICIPANT_LAB_GUIDE.md)** (**Model Registry**) · **[Lab 5](../lab5-pipelines/PARTICIPANT_LAB_GUIDE.md)** (**SageMaker Pipelines**).

---

## What you will build

| Component | Purpose |
| --- | --- |
| **MLOps Project** | One “factory” instance of the AWS portfolio template |
| **SCM repository** (often **CodeCommit**) | Holds pipeline + training code revisions |
| **CodePipeline** (+ **CodeBuild**) | CI/CD that reacts to commits and updates ML assets |
| **SageMaker Pipeline** | Training / evaluation DAG (template-specific) |
| **Model Registry group** | Versioned models and **approval status** |

Exact resource **names** and **menu paths** depend on your **Studio** experience (Classic vs updated UI) and **template version** — use this guide conceptually and follow what your instructor’s screenshots show.

---

## Why projects matter for enterprises

Teams that **each** reinvent Jenkins, branching models, registry rules, and approval flows burn time and drift from security baseline. **SageMaker Projects** package a **repeatable** pattern (SCM → CI/CD → ML pipeline → registry → promotion) so new models inherit the **same guardrails**.

This lab is mostly **inside AWS** — you typically **do not** author a full pipeline from zero in **`labs/`**; the template’s repo is created for you.

**Optional companion files** (for discussion or offline practice) live under [`labs/lab10-enterprise/project-template/`](../../labs/lab10-enterprise/project-template/), including a tiny **`pytest`** stub and sample **`buildspec`**.

---

## What AWS usually provisions (template-backed)

When the project finishes **Creating**, you should be able to find analogues of:

| Resource | Typical role |
| --- | --- |
| **Repositories** | `…-modelbuild` (training / pipeline code) and often `…-modeldeploy` (promotion artefacts) |
| **CodePipeline** | **Source → Build → …** culminating in SageMaker updates |
| **CodeBuild** | Tests / packaging stages |
| **SageMaker Pipeline** | Executes registered pipeline definition revisions |
| **Model package group** | Collects lineage + approval gate |
| **S3 buckets** | Artefacts and caches (lifecycle rules vary) |
| **CloudFormation stacks** | Underpins the catalogue product |

---

## AWS services you will use

| Service | Purpose |
| --- | --- |
| **SageMaker Studio + Projects** | Launch and manage the MLOps project |
| **CodeCommit** (or connected Git) | Version control for template code |
| **CodePipeline / CodeBuild** | CI/CD automation |
| **SageMaker Pipelines** | ML workflow execution |
| **SageMaker Model Registry** | Versions + **PendingManualApproval** / **Approved** |

---

## Prerequisites

| Requirement | Notes |
| --- | --- |
| **SageMaker Studio** user profile | Provided by instructor / account |
| **IAM** for **`sagemaker:CreateProject`** (and related Service Catalog rights) | Usually pre-provisioned |
| **Git** inside Studio | Clone / commit / push from the template repo |
| [**Lab 00**](../lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) | Account access + region discipline |

---

## Step 1 — Open SageMaker Studio

1. Sign in to the **AWS console** (`us-east-1` unless your instructor states otherwise).
2. Open **Amazon SageMaker**.
3. Launch **SageMaker Studio** for your **user profile** (wording varies: **Set up for single user**, **Domains**, etc.).
4. Wait until the Studio workspace loads.

If you cannot find **Projects**, use the **search bar** at the top of Studio and type **Projects**.

---

## Step 2 — Create an MLOps project

### 2.1 Open **Projects**

From Studio: go to **Deployments** (or **MLOps** grouping) → **Projects**, or search **Projects**.

### 2.2 **Create project**

1. Choose **Create project**.
2. Select **SageMaker templates** (wording may read **Organization templates** if your org adds custom products — use the instructor-provided one if different).
3. Pick the template labelled like **“MLOps template for model building, training, and deployment”** and continue.

### 2.3 Project details

- **Name:** use something **unique** in the class, e.g. **`mlops-l10-<your-initials>-01`** (avoid everyone using the same name).
- **Description:** short note (e.g. “Course Lab 10”).

Create the project and wait **several minutes** while nested stacks provision repositories, pipelines, and registry objects.

---

## Step 3 — Explore auto-created resources

### 3.1 Repositories

In the **project** detail view, open the **Repositories** (or **Code**) tab.

- **`…-modelbuild`** — training / pipeline source (this is where you edit **`pipeline.py`** in many templates).
- **`…-modeldeploy`** — deployment / promotion configuration (template-specific).

**Clone** the **modelbuild** repo into Studio (HTTPS / git-remote-codecommit — follow the Studio clone wizard). Open the tree in the file browser.

### 3.2 Pipeline definition (typical path)

Many AWS samples place the pipeline under a path similar to:

```text
pipelines/abalone/pipeline.py
```

Your template may use a **different** folder or sample (e.g. churn). Search for **`pipeline.py`** if the path differs.

Skim for:

- **Parameters** (instance types, thresholds)
- **Processing / training / evaluation** steps
- **Conditional** registration against metrics (same *idea* as Labs 5 and 8, implemented in template code)

### 3.3 Model group

In the project view, open **Model groups** / **Model registry** shortcut. You should see a **model package group** created by the template.

The **first** successful execution may take **5–15 minutes**. New versions often appear as **`PendingManualApproval`** until someone approves (if the template registers models that way).

---

## Step 4 — Git change to trigger automation

**Idea:** a **commit** to the **modelbuild** default branch is the **Source** event for **CodePipeline**, which eventually updates the **SageMaker Pipeline** definition and kicks off ML work.

### 4.1 Safe edit (class-friendly)

In **`pipeline.py`** (or the file your instructor names), locate a **parameter default** such as:

```python
training_instance_type = ParameterString(
    name="TrainingInstanceType",
    default_value="ml.m5.xlarge",
)
```

Change **`ml.m5.xlarge`** → **`ml.m5.large`** (or another **allowed** instance type your account supports). **Save** the file.

Do **not** introduce new internet dependencies, giant datasets, or unfamiliar containers without instructor approval.

### 4.2 Commit and push

Use Studio’s **Source Control** / **Git** panel:

1. Stage **`pipeline.py`** (or your changed files).
2. Commit with a clear message (e.g. “Lab10: reduce training instance default”).
3. **Push** to **main** (or the template’s default branch).

### 4.3 Observe the reaction

Back in the **project** UI (or **CodePipeline** in the console), open the **modelbuild** pipeline:

- A **new execution** should start after the **Source** stage sees your commit.
- Follow **Build** logs if a stage fails (common first-time issues: **pytest** failing — ask before disabling tests).

---

## Step 5 — Model approval workflow

### 5.1 Open the latest version

**Model Registry** → your **model package group** → select the **newest** version.

Metrics (**RMSE**, accuracy, custom JSON, etc.) **depend on the template** — read what the UI shows; do not assume a single metric name.

### 5.2 Update status (if permitted)

If policy allows:

1. Choose **Update model package status** / **Update status**.
2. Set status to **`Approved`** (add a short note if requested).

Some sandboxes are **view-only** for approvals — in that case, narrate with your instructor what would happen next.

### 5.3 Deployment pipeline

Many templates include a separate **`-modeldeploy`** pipeline that progresses toward **staging** / **production** checks after approval. Open that pipeline and map **stages** to your course’s deployment story (**Lab 6**).

---

## Step 6 — Clean up

**Important:** projects **incur** storage, pipeline, and compute charges while resources exist.

**Studio / console**

1. **SageMaker Studio** → **Projects**.
2. Select your project → **Delete** / **Actions → Delete** (confirm prompts).

**CLI (optional)**

```bash
aws sagemaker delete-project --project-name <YOUR_PROJECT_NAME> --region us-east-1
```

If **CloudFormation** stacks remain in `DELETE_FAILED`, ask the instructor — versioned buckets or retained roles sometimes need manual cleanup.

---

## Lab completion checklist

- [ ] Studio opened and **Projects** located.
- [ ] MLOps project created from the **model build / train / deploy** template.
- [ ] **modelbuild** repo cloned; **`pipeline.py`** (or equivalent) reviewed.
- [ ] Benign **instance-type** (or instructor-approved) edit committed and **pushed**.
- [ ] **CodePipeline** / **SageMaker Pipeline** showed a **new** run tied to the commit.
- [ ] **Model package group** located; latest version and **metrics** reviewed.
- [ ] **Approval** attempted or discussed (per sandbox policy).
- [ ] **Deployment** pipeline stage identified (if present).
- [ ] **Project deleted** (or deletion ticket raised).

---

## Architecture (conceptual)

```text
Code (SCM) → CodePipeline → CodeBuild (tests/glue) → SageMaker Pipeline (ML steps)
                                                      → Model Registry (versions + approval)
                                                      → Deploy stages (template-specific endpoints / tests)
```

---

## Key concepts

| Concept | Meaning |
| --- | --- |
| **Standard template** | Same starting shape for every team in the org portfolio |
| **Git-driven ML** | Commits trigger automation — not one-off console clicks |
| **Approval gate** | Human or policy step before production promotion |
| **Separation of duties** | Engineers change code; approvers attest model risk |
| **Audit trail** | SCM history + pipeline executions + registry status |

---

## Troubleshooting

| Issue | What to try |
| --- | --- |
| **Create project** disabled | Domain not associated with the Service Catalog portfolio — **instructor / admin**. |
| Project stuck **Creating** | Open **CloudFormation** → earliest **FAILED** event (IAM capability, quota). |
| **Clone** fails | Renew **git-remote-codecommit** credentials or use Studio’s **Clone** button. |
| **Build** fails on **pytest** | Read **CodeBuild** logs; ask before deleting tests. |
| No **model version** yet | ML pipeline still running or failed earlier — open **SageMaker Pipeline** execution. |
| Cannot **approve** | Missing **`sagemaker:UpdateModelPackage`** — instructor escalation. |

---

## Course completion (core lab track)

| Lab | Topic |
| --- | --- |
| 00 | Environment setup (AWS CLI) |
| 1 | First SageMaker training |
| 2 | Feature Store pipeline |
| 3 | Hyperparameter tuning |
| 4 | Model registry & governance |
| 5 | CI/CD with SageMaker Pipelines |
| 6 | Model deployment & serving |
| 7 | Model monitoring & drift |
| 8 | End-to-end capstone |
| 9 | Advanced inference patterns |
| **10** | **Enterprise MLOps with Projects** |

You have reached the end of the **numbered hands-on sequence** in this repository; keep using **Lab 00** and your organisation’s playbooks for production work.
