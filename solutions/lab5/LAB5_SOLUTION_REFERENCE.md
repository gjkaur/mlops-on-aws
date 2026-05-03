# Lab 5 — SageMaker Pipelines (instructor reference)

Condensed notes for **`labs/lab5-pipelines/`**.

## Overview

| Attribute | Value |
|-----------|-------|
| Duration | ~90 min |
| Module | 5 — CI/CD |
| Region | `us-east-1` |

## Correctness vs naive teaching drafts

1. **`ConditionStep`** must compare workflow expressions (e.g. **`JsonGet`**) to parameters or literals — not **`boto3.get_object`** inside **`.apply`**.  
2. **`evaluation.json`** drives both **`JsonGet`** and **`ModelMetrics`** (**`MetricsSource`** with **`Join`** to the keyed output prefix + **`evaluation.json`**).  
3. **`EvaluateModel`** ingests **`S3ModelArtifacts`** (tarball); **`evaluate.py`** **extracts** then loads **`joblib`**.  
4. **`approval_status`** defaults to **`PendingManualApproval`**; switch to **`Approved`** only when you intentionally skip manual approval demos.  
5. Terraform **`aws_s3_bucket_notification`** with **`eventbridge = true`** matches modern **Object Created → EventBridge** patterns.

## Naming

| Artefact | Pattern |
|---------|---------|
| Pipeline | **`lab5-churn-pipeline-` + last 8 chars of bucket** |
| Model package group | **`lab5-churn-pipeline-group-` + same suffix** |
| Optional EventBridge rule | **`lab5-trigger-pipeline-<suffix>`** |

## Artifacts (`scripts/`)

| File | Writer |
|------|--------|
| `pipeline_name.txt` | `pipeline_definition.py` |
| `pipeline_execution_arn.txt` | `run_pipeline.py` |

## EventBridge target shape

**`put_targets`** includes **`SageMakerPipelineParameters.PipelineParameterList`** with **string** values for every pipeline parameter.

## Common issues

| Symptom | Check |
|---------|-------|
| Windows code upload error | **`as_uri()`** for **`ProcessingStep` `code=`** paths |
| No registration despite “success” | **`AccuracyThreshold`** too high vs **`evaluation.json`** |
| Trigger never runs | EventBridge notification on bucket; **prefix **`new-data/`**; **`EVENTBRIDGE_ROLE_ARN`** |

## Teaching emphasis

1. **DAG + parameters** reuse the same codebase across environments and schedule-driven retrains.  
2. **Conditional registration** is the minimal “promotion gate” inside automation.  
3. **Manual approval** in the registry (module 4) still applies after **`PendingManualApproval`** registration unless you deliberately set **`Approved`**.
