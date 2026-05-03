# Lab 6 — Model deployment & serving (Instructor guide)

## Lab overview

| Attribute | Value |
|-----------|-------|
| Duration | ~90 minutes |
| Difficulty | Intermediate |
| Module | 6 – Deployment |
| Region | `us-east-1` |

## Learning objectives

Learners operationalize **`SKLearn`** training artifacts onto **real-time endpoints**, attach **optional auto-scaling**, practice **traffic-splitting demos**, observe **latency** characteristics, then **clean up** cloud resources cleanly.

Implementation reference: **`LAB_OVERVIEW.md`**, condensed notes **`../../solutions/lab6/LAB6_SOLUTION_REFERENCE.md`**.

## Facilitator dry run checklist

```bash
cd labs/lab6-deployment/infrastructure
cp terraform.tfvars.example terraform.tfvars  # aws_account_id
terraform init && terraform apply -auto-approve

export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw deployment_role_arn)

cd ../scripts
python train_model.py
python deploy_endpoint.py               # generates endpoint_name + variant artifact
python configure_scaling.py             # Application Auto Scaling
python test_endpoint.py
python canary_deployment.py apply --blue-weight 90 --green-weight 10   # GREEN_MODEL_DATA_URI optional
python canary_deployment.py promote-green                               # collapses variants
python cleanup.py

cd ../infrastructure
terraform destroy -auto-approve
```

PowerShell mirrors **`export`** with **`$env:`** assigns.

## Design choices vs naive teaching drafts

1. **`train.py` + `train_model.py` split** – keeps container code immutable and reviewable.  
2. **`inference.py` checked in** – avoids writing huge strings mid-import; clarifies **`input_fn` / `predict_fn` / `output_fn`**.  
3. **`model_data_uri.txt`** persists artifacts so **`deploy_endpoint.py`** need not loosely scan jobs.  
4. **`deploy_endpoint`** uses **`JSONDeserializer`** paired with **`inference.output_fn`** JSON payload.  
5. **`cleanup.py`** enumerates **`application-autoscaling`** targets prefixed with **`endpoint/<name>/`** so scaling policies don’t linger.  
6. **`canary_deployment`** uses **`SKLearn.prepare_container_def`** twice (blue/green) so containers match estimator packaging without hand-pasted ECR digests.

## Canary lab story

Default **`GREEN_MODEL_DATA_URI` unset ⇒ both variants share tarball** → traffic split is **non-functional differentiation** yet still teaches **routing**, **metrics**, **`update_endpoint`**. For a truthful A/B rerun training with tweaked hyperparameters and export **`GREEN_MODEL_DATA_URI`** before **`apply`**.

## Auto scaling caveats

- First-time **`register_scalable_target`** may prompt learners to approve **service-linked roles** (“**AWSServiceRoleForApplicationAutoScaling_SageMakerEndpoint**”) depending on account guardrails—document in Slack if corporate SCPs deny **`application-autoscaling`**.  
- Cooldown timers + sparse classroom traffic ⇒ **scaling events may not visibly fire** despite policies—use **`test_endpoint`** load spike or artificially lower **`TargetValue`** for demos.

## Common learner errors

| Symptom | Fix |
|---------|-----|
| **JSON parse error** invoking endpoint | **`Accept application/json`** (see **`test_endpoint`**) |
| **Feature mismatch** validation | Inference expects **10** CSV fields |
| **Scaling policy conflict** duplicate name | Scripts timestamp policy names |
| **`delete_endpoint` hangs** rare capacity issues | lengthen waiter or console manual stop |

## Post-lab housekeeping

Terraform bucket removal **does not** delete SageMaker models still referenced—or dangling models if learners skip **`cleanup.py`**. **`cleanup`** removes locally tracked endpoints & **`lab6-*`** canary twins; escalate stragglers in shared accounts via tags.
