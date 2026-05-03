# Lab 10: Enterprise MLOps with SageMaker Projects

This module is primarily **experience-based** inside **Amazon SageMaker Studio** and the AWS console—learners create an **AWS-managed MLOps project** from an official template (*model build, train, deploy* lineage), inspect the spawned **CI/CD plane** (**CodePipeline**, **CodeBuild**, optional **CodeCommit**), relate **git-driven** commits to SageMaker executions, and walk the **model package approval** path in **Model Registry**.

Repository assets here (**`project-template/`**) are **teaching companions**: minimal CloudFormation and sample **CodeBuild** spec material—not replacements for AWS Service Catalog provisioning that backs Studio **Projects**.

| Resource | Where to deepen |
|---------|----------------|
| Participant walkthrough | [`participant/lab10-enterprise/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab10-enterprise/PARTICIPANT_LAB_GUIDE.md) |
| Instructor pacing + IAM prerequisites | **`INSTRUCTOR_LAB_GUIDE.md`** |
| Optional companion stack | **`project-template/cloudformation/companion-demonstration.yaml`** |
| CodeBuild/unit-test nib | **`project-template/seed-code/`** |
| Cheatsheet | **`solutions/lab10/LAB10_SOLUTION_REFERENCE.md`** |

**Region:** **`us-east-1`** aligns with AWS console screenshots and other course labs.
