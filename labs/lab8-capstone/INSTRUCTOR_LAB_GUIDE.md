# Lab 8 Instructor Notes — Capstone

## Learning outcomes

Demonstrate stitched storylines previously isolated in Labs **5 (Pipeline + EB)**, **4 (registry approval semantics)**, **6 (traffic shaping)**, **7 (DQ monitoring metrics)** inside one sandbox.

Keep students honest about separation of responsibilities: **Terraform** supplies durable guardrails; Python breadcrumbs (`*.txt`) stitch automation phases the way teams version operational metadata.

## Suggested facilitation arc

| Segment | Guidance |
|---------|----------|
| 0‑20 min | IaC storytelling—why **four buckets** (raw vs artefacts vs telemetry vs DQ reports)? |
| 20‑70 min | Run pipeline execution; dissect **Conditional Register** behaviour + JsonGet limitation |
| 70‑105 min | Approve deliberate package; **`deploy_canary`** emphasises duplication teaching trick |
| 105‑130 min | **Monitoring baseline** derived from preprocessing train split (seven floats, **no labels**) |
| 130‑145 min | **EventBridge latency** realism + double pipeline executions when students mash uploads |
| 145‑150 min | Guided cleanup rehearsal (`simulate_workflow.py` optional second pass) |

## Pitfalls surfaced in smoke tests

| Symptom | Likely culprit |
|---------|----------------|
| Accuracy gate rejects register | Inspect `evaluation.json`; lower **`AccuracyThreshold`** param or widen synthetic churn thresholds |
| `deploy_canary` missing tarball | Forgot approval or describe_model_package denies access |
| Drift telemetry absent | DQ schedule waits until cron window; **`LAB8_MONITOR_NOW`** caveat |
| EventBridge misses uploads | Forgot bucket notification — Terraform snippet must stay applied |
| `cleanup.py` orphaned models | Re-run **`describe_endpoint_config`** referencing variant models outside `canary_models.json` |

## Grading starter rubric

| Component | Approx. weight | Success signal |
|-----------|---------------|----------------|
| Pipeline execution | 25% | `run_pipeline.py` ends `Succeeded` + preprocess train URI persisted |
| Registry approval | 15% | `approve_model_package.py` resolves pending packages |
| Canary deployment | 20% | `deploy_canary.py` publishes weighted variants without dropping capture |
| Monitoring | 15% | `monitoring_setup.py` produces schedule + CloudWatch linkage |
| EventBridge retrains | 10% | `simulate_workflow.py` seeds `new-data/` and executions appear |
| Docs + narration | 15% | Architecture + model card align with deployed stack |
