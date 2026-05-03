# Lab 10 — Enterprise Projects cheatsheet

## Mind the boundary

**Studio Project** ⇒ **Service Catalog** provisions **nested CloudFormation stacks** (names differ by AWS template vintage). Companion YAML in **`labs/lab10-enterprise/project-template/cloudformation/companion-demonstration.yaml`** is **not** that stack—deploy only when you deliberately want a lean teaching contrast.

## Resource hunt list

| Asset | Typical console path |
|-------|---------------------|
| Project | SageMaker Studio → Projects |
| SCM | Developer Tools → CodeCommit *(or upstream Git linkage)* |
| CI | Developer Tools → CodePipeline |
| Build logs | Developer Tools → CodeBuild → Projects → Logs tab |
| ML DAG | SageMaker → **Pipelines** |
| Versions | SageMaker → **Model Registry** → Model groups |

## Condition + metrics teaching tie-in

Portfolio templates often expose **ModelMetrics** blobs similar to **`evaluation.json`** from Labs **5/8**. If students ask why classroom slides skip dynamic S3 fetching inside **Conditions**, point them to **`JsonGet`** pipelines already authored in-repo—avoid implying **`Lambda`** hacks on **`ProcessingOutput` S3 URIs**.

## Approval cascade vocabulary

- **`PendingManualApproval`** — human gate before downstream deploy product stage activates
- **`Approved`** — releases template-defined promotion (staging endpoint deploy, batch validation, etc.)
- **`Rejected`** — audit failure—discuss retraining loop

## Cleanup commands (when portfolio allows deletes)

```bash
aws sagemaker delete-project \
  --project-name <PROJECT_NAME_FROM_STUDIO> \
  --region us-east-1
```

If orphaned **CloudFormation** stacks linger: **CloudFormation** → delete child stacks depth-first (`DELETE_FAILED` often needs emptying versioned buckets the companion lab warned about).

## Portfolio admin gotchas instructors should voice

1. KMS CMKs on buckets without grant to CodePipeline role → **`AccessDenied`** on artifact promotion.
2. VPC-only egress for CodeBuild → missing interface endpoints ⇒ pip install timeouts.
3. SCP denying **`events:PutRule`** can break orchestration watchers quietly.
