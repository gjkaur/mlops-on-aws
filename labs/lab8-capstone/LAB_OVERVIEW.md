# Lab 8 — End-to-End Capstone (Module 8)

| Attribute | Value |
|-----------|-------|
| **Duration** | 120–150 minutes |
| **Difficulty** | Advanced |
| **Region** | `us-east-1` |

Integrated story: synthetic **telco churn** data → SageMaker Pipeline (**Processing → Training → Conditional Register**) → registry approval gate → realtime **capture + duplicated 90/10 canary variants** → **Model Monitor DQ** + **CloudWatch/SNS drift alarm** → **EventBridge-triggered retrains**.

## Narrative pillars

| Track | Artefact folder |
|-------|----------------|
| IaC sandbox | **`infrastructure/`** (four buckets + EventBridge SNS wiring) |
| CI/CD-ish automation | **`scripts/pipeline_definition.py`**, **`run_pipeline.py`** |
| Governance | **`approve_model_package.py`** writes **`approved_model_package_arn.txt`** |
| Serving resilience | **`deploy_canary.py`** (capture-preserving duplicated variant rollout) |
| Observability | **`monitoring_setup.py`** + SNS topic from Terraform |
| Continuous delivery trigger | **`trigger_retraining.py`** (`new-data/*` on **`DATA_BUCKET`**) |

## Prerequisites

Labs **4–7** materially reduce ramp time; newcomers should finish **Lab 00** Terraform hygiene.

## Operational flow (abbreviated)

1. `terraform apply` → export bucket + role ARNs + `SNS_TOPIC_ARN`.
2. `python pipeline_definition.py` → persists **`pipeline_name.txt`** + **`model_package_group.txt`**.
3. `python run_pipeline.py` → persists **`pipeline_execution_arn.txt`** + **`preprocess_train_s3_uri.txt`** on success gate.
4. `python approve_model_package.py`.
5. `python deploy_canary.py` (**requires Approved package**).
6. `python monitoring_setup.py` (**depends on preprocessing train URI + realtime endpoint names**).
7. `python trigger_retraining.py` (after SNS email confirmation!).
8. `python simulate_workflow.py` (**Predictor smoke + seeded `new-data/` upload**).

**Instructor cheatsheet**: [`../../solutions/lab8/LAB8_SOLUTION_REFERENCE.md`](../../solutions/lab8/LAB8_SOLUTION_REFERENCE.md).
