# Lab 10 Instructor Notes — Enterprise MLOps with Projects

## Lab overview

| Attribute | Value |
|-----------|-------|
| **Duration** | ~60 minutes |
| **Difficulty** | Intermediate |
| **Module** | 10 — Enterprise MLOps |
| **AWS Region** | **`us-east-1`** |

## Learning objectives

By session end learners can:

- Provision a SageMaker **Studio Project** using the standard **model build/train/deploy** AWS template vocabulary.
- Name the CI/CD scaffolding AWS typically attaches (**pipelines**, **build projects**, SCM integration, artefacts bucket, **Model Registry** linkage).
- Drive a harmless **git-visible** edit that triggers downstream automation without derailing classmates.
- Walk **Model Registry** approval semantics echoing Lab 4/8 (without conflating *project delete* vs *model approval*).

## AWS services surfaced

| Service | Teaching angle |
|---------|----------------|
| SageMaker Projects / Service Catalog | Standardised “golden path” provisioning |
| CodeCommit *(or upstream Git connector)* | Source of truth for pipeline code revisions |
| CodePipeline | Stage orchestration (Source→Build→…→Pipeline deploy) |
| CodeBuild | Test/lint/smoke gates before SageMaker artefacts refresh |
| SageMaker Pipelines | ML DAG distinct from—but triggered by—CodePipeline |
| Model Registry | Versioning + **PendingManualApproval** governance |
| CloudFormation | Under-the-hood template execution (students rarely edit day one) |

## Architectural truth check (tell students explicitly)

Production **SageMaker MLOps Projects** instantiate **portfolio templates**. The **CloudFormation excerpt** circulated in syllabi—and the simplified **`project-template/`** snippets in **this repo**—are **pedagogical**; they **omit** KMS networking, SCP guardrails, cross-account portfolios, VPC-only CodeBuild fleets, Secrets Manager SCM tokens, approval gates, Slack hooks, etc. Use them to **diagram roles**, **not** to clone AWS’s GA template verbatim.

Companion stack **`project-template/cloudformation/companion-demonstration.yaml`** creates **only** a toy **CodeCommit** repo, encrypted **S3** bucket, and **Model Package Group** so you can whiteboard deltas vs the full Projects blast radius—deploy **only** when you intentionally want stray resources beside the AWS template.

### Why we do not vend a “full Projects” YAML here

A drop-in YAML that binds **CodePipeline** + **CodeBuild** demands **purpose-built IAM trusts** (**`codepipeline.amazonaws.com`**, **`codebuild.amazonaws.com`**) with least-privilege S3/CodeCommit/KMS grants. Instructor samples that mistakenly `RoleArn` the **Studio execution role** confuse novices (**see earlier draft warning**—fixed in this curriculum note, not recreated as infra).

## Suggested facilitation arc (~60 minutes)

| Segment | Minutes | Facilitator cues |
|---------|---------|------------------|
| Framing Projects vs lone pipelines | 5 | Tie back to Labs **4** (**registry**) and **5** (**Pipeline SDK**)—“factory vs bespoke script.” |
| Prereqs + Studio domain sanity | 5 | Roles: **`sagemaker:CreateProject`**, Studio execution role trusts, Service Catalog launches. |
| Live create Project | 10 | Pick template name explicitly; slower accounts may stall on **Creating** status—narrate. |
| Inventory auto resources | 10 | Split class: cohort A timelines **CodePipeline**, cohort B **Model Registry**. |
| Git micro-change drill | 15 | Prefer **`buildspec.yml`** tweak or benign pipeline parameter—not dataset size explosions. |
| Approval + downstream | 15 | Pause if sandbox forbids approvals—simulate read-only narrative. |

## Lab walkthrough (Console / Studio checklist)

### Part A — Create project (~10 minutes)

1. **SageMaker Studio** → **Deployments**/**MLOps** groupings vary by UX generation → **Projects** → **Create project**.
2. Choose **Organization templates** portfolio item labelled like **“MLOps template for model building, training, and deployment”**.
3. Name example: **`student-mlops-l10-<initials>`** (avoid collisions).

### Part B — Resource safari (~10 minutes)

Ask students to record **five** artefacts with ARNs/screenshots:

| Expected artefact | Where to click |
|-------------------|----------------|
| SCM repository | AWS CodeCommit (or connector target) matched to project readme |
| CodePipeline | **`{project}-...`** pipelines with Source stage |
| CodeBuild projects | Logs linked from failed/success executions |
| SageMaker Pipeline | **Pipelines** list created/updated during deploy stage |
| Model package group | **Model Registry → Model groups** with project tag |

Template generations differ—**explicitly allow** mismatched suffixes versus slide deck screenshots.

### Part C — Controlled code change (~10 minutes)

Recommended low-risk edits (pick one cohort-wide):

- Swap default **training instance type** **`ml.m5.xlarge → ml.m5.large`** inside template-provided estimator config *where the sample documents it*.
- Bump a comment-only change in **`buildspec`** to prove **pytest** invocation path.
- Add **`tests/test_truth.py`** asserting trivial constant (**see `project-template/seed-code/`**) if template repo empty.

Reject edits that widen external network calls or enlarge datasets without quota checks.

Push via Studio **Git** tooling or **`git-remote-codecommit`** assisted flow from lab desktop.

### Part D — Approval narrative (~10 minutes)

1. After ML pipeline registers a version, locate **`PendingManualApproval`**.
2. Discuss who may approve in regulated org (**second party**, **risk committee**).
3. If allowed, approve and narrate whichever **deploy/testing** stage activates (staging endpoint, QA lambda, batch transform)—template dependent.

Cleanup discussion: **`aws sagemaker delete-project --project-name <name>`** (and dependent stacks from Service Catalog)—see **`solutions/lab10`**.

## Required / recommended IAM posture (staging)

Broad strokes—adapt to least privilege workshops:

| Need | Typical permission surface |
|------|----------------------------|
| Create project | `sagemaker:CreateProject`, `servicecatalog:List*`, `servicecatalog:ProvisionProduct` (portfolio bindings) |
| Studio user | SageMaker Studio domain execution role augmented with provisioning **passrole** scoped to templated CFN IAM patterns |
| Git push | Repo-level **Contributor** privileges |
| Approval lab | Conditional `sagemaker:UpdateModelPackage`, registry group resource scope |

Provide **sandbox OU** SCP exceptions list before day-of.

## Student failure modes

| Symptom | Guidance |
|---------|----------|
| **Create disabled** | Domain lacks portfolio association—admin task. |
| **Project stuck Creating** | Open **CloudFormation** events for earliest `FAIL` (`CAPABILITY_IAM`, nested stack). |
| **Clone rejected** | Git-remote helper / temporary HTTPS credentials expiry. |
| **Build fails pytest** | Template ships failing sample tests—substitute **`seed-code`** placeholder or skip tests with instructor approval. |
| **No registry version** | ML pipeline gated earlier—trace **Processing** step CloudWatch logs. |
| **`delete-project` orphaned stacks** | Re-delete nested stacks manually if Service Catalog teardown partially failed. |

## Grading anchors (starter rubric)

| Evidence | Points idea |
|---------|-------------|
| Screenshot/map of spawned CI/CD artefacts | /25 |
| Git commit SHA tied to Pipeline execution URL | /25 |
| Written paragraph on approvals & separation of duties | /25 |
| Cleanup proof (screens or CLI snippet) | /25 |

## Stretch prompts

1. Sketch **dual-account** hub-spoke Projects (central registry vs spoke training).
2. Compare **native CodeCommit** vs **GitHub** enterprise connector approvals.
3. Where would **model card** artefacts land in AWS-native vs custom template?
