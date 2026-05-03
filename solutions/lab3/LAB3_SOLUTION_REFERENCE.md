# Lab 3 – Hyperparameter tuning (instructor reference)

Supports **`labs/lab3-tuning/`** artifacts (Terraform + scripted HPO baseline → analyze → deploy).

## Overview

| Attribute | Value |
|-----------|-------|
| Duration | ~90 minutes |
| Module | 3 – experimentation |
| Region | `us-east-1` |

### Learning angles

Baseline before search; tuner objective aligns with **`metric_definitions`** regex on training logs; interpreting **`HyperparameterTuningJobAnalytics`**; realtime hosting with separate **`predict.py`** (artifacts come from trainings that used **`train.py`** only).

### AWS footprint

Amazon SageMaker training + HPO, S3 staging, CloudWatch logs, optional realtime endpoint (**`ml.t2.medium`** in **`deploy_best.py`**).

---

## Sanity sequence

See **`labs/lab3-tuning/LAB_OVERVIEW.md`** for condensed commands.

Notable timings:

| Step | Typical wait |
|------|----------------|
| `baseline.py` | 3–6 minutes |
| `tuning_config.py` | ~15–25 minutes (`max_jobs=10`, `parallel=2`) |

---

## Implementation notes (vs teaching deck)

| Topic | Detail |
|-------|--------|
| Metric capture | **`train.py`** prints `rmse:` / `r2:` strings parsed by estimator **`metric_definitions`** so `FinalObjectiveValue` fills in |
| Analyzer | **`analyze_results.py`** tolerates **`HyperParameters`** cells as dict/str |
| Inference | Hosted model uses **`predict.py`** (**`model_fn`** / **`predict_fn`**) separate from **`train.py`** |
| Glue / Athena | *Not used* — Lab 3 narrows strictly to tuner + Hosting |

Students must **tear down realtime endpoints manually** (`endpoint_name.txt`) plus `terraform destroy`.

---

## Troubleshooting quick hits

| Symptom | Mitigation |
|---------|-------------|
| Tuner never surfaces objective | Inspect CloudWatch log stream → confirm `rmse:` regex matches floats |
| `ResourceLimitExceeded` | Lower parallelism or shrink instance (`ml.m5.large` → `ml.t3.medium`) |
| Hosted endpoint mis-predict shape | Prediction payload must expose **10** diabetes features |

---

Extend with SageMaker Studio Experiments UI once child training jobs populate (optional talking point—not wired in starter scripts).

