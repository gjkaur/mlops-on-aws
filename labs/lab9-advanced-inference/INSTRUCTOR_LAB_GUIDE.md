# Lab 9 Instructor Notes — Advanced Inference Patterns

## Learning outcomes

| Objective | Artefact proving it |
|-----------|---------------------|
| Contrast capex-heavy realtime vs serverless metering | Warm vs cold timings from `test_endpoints.py` |
| Explain asynchronous staging | `invoke_endpoint_async` + S3 watcher |
| Operationalise sklearn MME | `MultiDataModel.deploy` + `TargetModel=model-v#/model.tar.gz` |
| Cost intuition | Stub numbers in `compare_costs.py` (replace with Pricing Calculator snapshots if needed) |

## Suggested facilitation arc (≈75 min)

| Minutes | Talking points |
|---------|----------------|
| 0–10 | **Same sklearn artefact**, different control planes (queue vs realtime vs nightly transform) |
| 10–20 | **`train_models.py`** — emphasise **`model.joblib` path inside tarball**, not stray filenames |
| 20–40 | **`deploy_serverless.py`** vs **`deploy_async.py`** billing + SLA trade-offs |
| 40–60 | **`deploy_mme.py`** routing header; latency when models churn on single host |
| 60–70 | **`run_batch_transform.py`** parallelism knobs vs endpoint fleet |
| 70–75 | Cleanup ritual + Terraform destroy reminders |

## Pitfalls from authoring smoke-tests

| Symptom | Root cause |
|---------|------------|
| Serverless 5XX on first invocation | Idle cold-start + container download—retry after success |
| Async never writes output | malformed `async-output/` prefix or missing `Accept` parity |
| MME ValidationException target | **`TargetModel` must match key suffix** under `models/` prefix (`model-v2/model.tar.gz`) |
| Batch job fails parsing | Inputs must omit headers; **`10`** columns strictly |
| `cleanup.py` cannot delete endpoint | Rare partial delete—re-run once endpoint status `Deleting` settles |

## Grading starters

| Checkpoint | Approx. weight |
|------------|----------------|
| Terraform apply + artefacts in S3 | 15% |
| ≥2 inference modes demonstrably answering requests | 40% |
| Written comparison (pricing + WHEN to pick each pattern) | 25% |
| teardown evidence (`cleanup.py` + `destroy`) | 20% |

## Differentiation prompts

1. Which pattern honours **SOC2 change windows** easiest when models update hourly vs nightly?
2. When does **latency SLO <200 ms P99** rule out async even if payloads are giant?
3. How would you retrofit **VPC-only** ingestion into each invocation path?

Keep answers anchored to **`LAB_OVERVIEW.md`** plus official SageMaker quotas for the cohort’s Region.
