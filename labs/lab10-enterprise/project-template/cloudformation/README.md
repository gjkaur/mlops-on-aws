### Companion demonstration stack — read before deploy

Purpose: illustrate **three** orthogonal primitives students will see clustered inside **SageMaker Projects**—not reproduce AWS’s GA MLOps template.

**Creates**

- **`AWS::CodeCommit::Repository`** (HTTP clone URL output)
- **`AWS::S3::Bucket`** (AES256 SSE, versioning on, **DeletionPolicy Delete** — still empty objects cost pennies if forgotten)
- **`AWS::SageMaker::ModelPackageGroup`**

**Does not create**: CodePipeline, CodeBuild IAM, SageMaker pipelines, catalog portfolios.

Deploy only in disposable accounts:

```bash
aws cloudformation deploy \
  --template-file companion-demonstration.yaml \
  --stack-name mlops-l10-companion-demo \
  --parameter-overrides ProjectSlug=accteam \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

Tear down:

```bash
aws cloudformation delete-stack --stack-name mlops-l10-companion-demo --region us-east-1
```

**Model package group naming** collides if you reuse the same **`ProjectSlug`** while an old group remains—pick unique slugs or delete remnants in SageMaker console.
