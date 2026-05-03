# Lab 10 — Enterprise MLOps with Projects

Participant walkthrough: **[`participant/lab10-enterprise/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab10-enterprise/PARTICIPANT_LAB_GUIDE.md)** · Folder index **[`LAB10_PARTICIPANT_INDEX.md`](../../participant/lab10-enterprise/LAB10_PARTICIPANT_INDEX.md)**.

This lab complements earlier **Pipeline** (**Lab 5**) and **Registry** (**Lab 4**) work by showing how enterprises **stamp out** the same MLOps shape for every team via **SageMaker Projects** (portfolio templates backed by AWS Service Catalog and CloudFormation).

## What learners do

- Create a Studio **Project** from the **“MLOps template for model building, training, and deployment”** (name may vary slightly per AWS revision).
- Map auto-created artefacts (**CodePipeline**, **CodeBuild**, pipelines, registry group, buckets) to governance talking points.
- Push a benign config change (**instance type**, hyperparameter placeholder, or **`buildspec`** tweak) from Studio git client and correlate **pipeline execution**.
- Locate **`PendingManualApproval`** packages and transition to **`Approved`** (if your org policy permits in the sandbox).

No Terraform is required—the teaching stack is whichever template AWS attaches to SageMaker Projects for your account/Studio domain.

## Reference material in this folder

| Path | Purpose |
|------|---------|
| **`INSTRUCTOR_LAB_GUIDE.md`** | Facilitation script, timings, IAM checklist, pitfalls |
| **`LAB_OVERVIEW.md`** | Elevator pitch + sibling links |
| **`project-template/`** | Optional **`companion-demonstration`** CloudFormation + CodeBuild nib |
| **`solutions/lab10/LAB10_SOLUTION_REFERENCE.md`** | One-page cheatsheet |

**Participant guide:** [`participant/lab10-enterprise/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab10-enterprise/PARTICIPANT_LAB_GUIDE.md) (repo root `participant/`).
