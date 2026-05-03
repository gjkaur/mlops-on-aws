"""
Lab 8 SageMaker Pipeline: preprocess -> train -> evaluate -> conditional RegisterModel.

Uses JsonGet(PropertyFile) for the accuracy gate (same pattern as Lab 5 — no boto lambdas in graphs).
Upsert consumes ARTIFACTS_BUCKET_NAME + SAGEMAKER_ROLE_ARN environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

from sagemaker.inputs import TrainingInput
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.sklearn import SKLearn
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.functions import Join, JsonGet
from sagemaker.workflow.parameters import ParameterFloat, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.steps import ProcessingStep, TrainingStep

SCRIPT_DIR = Path(__file__).resolve().parent


def _uploadable_code_uri(script: Path) -> str:
    return script.expanduser().resolve().as_uri()


def _bucket_suffix(bucket_name: str) -> str:
    if len(bucket_name) >= 8:
        return bucket_name[-8:]
    return "".join(ch for ch in bucket_name if ch.isalnum())[:8] or "default"


def pipeline_name_for_bucket(bucket_name: str) -> str:
    return f"lab8-capstone-pipeline-{_bucket_suffix(bucket_name)}"


def model_package_group_for_bucket(bucket_name: str) -> str:
    return f"lab8-capstone-group-{_bucket_suffix(bucket_name)}"


def create_pipeline(bucket_name: str, role_arn: str, name: str) -> Pipeline:
    pipeline_session = PipelineSession()

    processing_instance_type = ParameterString(
        name="ProcessingInstanceType",
        default_value="ml.m5.large",
    )
    training_instance_type = ParameterString(
        name="TrainingInstanceType",
        default_value="ml.m5.large",
    )
    n_estimators = ParameterString(name="NEstimators", default_value="150")
    max_depth = ParameterString(name="MaxDepth", default_value="12")
    accuracy_threshold = ParameterFloat(name="AccuracyThreshold", default_value=0.75)

    sklearn_preprocess = SKLearnProcessor(
        framework_version="1.2-1",
        role=role_arn,
        instance_type=processing_instance_type,
        instance_count=1,
        sagemaker_session=pipeline_session,
        base_job_name="lab8-capstone-preprocess",
    )

    process_step = ProcessingStep(
        name="PreprocessData",
        processor=sklearn_preprocess,
        inputs=[],
        outputs=[
            ProcessingOutput(
                output_name="train_data",
                source="/opt/ml/processing/train",
            ),
            ProcessingOutput(
                output_name="test_data",
                source="/opt/ml/processing/test",
            ),
        ],
        code=_uploadable_code_uri(SCRIPT_DIR / "preprocess.py"),
        job_arguments=["--train-test-split-ratio", "0.2"],
    )

    sklearn_train = SKLearn(
        entry_point="train.py",
        source_dir=str(SCRIPT_DIR),
        role=role_arn,
        framework_version="1.2-1",
        py_version="py3",
        instance_type=training_instance_type,
        instance_count=1,
        hyperparameters={
            "n-estimators": n_estimators,
            "max-depth": max_depth,
        },
        output_path=f"s3://{bucket_name}/pipeline-training-output",
        code_location=f"s3://{bucket_name}/pipeline-code",
        sagemaker_session=pipeline_session,
        base_job_name="lab8-capstone-train",
    )

    train_step = TrainingStep(
        name="TrainModel",
        estimator=sklearn_train,
        inputs={
            "train": TrainingInput(
                s3_data=process_step.properties.ProcessingOutputConfig.Outputs[
                    "train_data"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "test": TrainingInput(
                s3_data=process_step.properties.ProcessingOutputConfig.Outputs[
                    "test_data"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
        },
    )

    sklearn_eval = SKLearnProcessor(
        framework_version="1.2-1",
        role=role_arn,
        instance_type=processing_instance_type,
        instance_count=1,
        sagemaker_session=pipeline_session,
        base_job_name="lab8-capstone-evaluate",
    )

    evaluation_report = PropertyFile(
        name="EvaluationReport",
        output_name="evaluation",
        path="evaluation.json",
    )

    evaluation_step = ProcessingStep(
        name="EvaluateModel",
        processor=sklearn_eval,
        inputs=[
            ProcessingInput(
                source=train_step.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model",
            ),
            ProcessingInput(
                source=process_step.properties.ProcessingOutputConfig.Outputs[
                    "test_data"
                ].S3Output.S3Uri,
                destination="/opt/ml/processing/test",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation",
                source="/opt/ml/processing/evaluation",
            ),
        ],
        code=_uploadable_code_uri(SCRIPT_DIR / "evaluate.py"),
        property_files=[evaluation_report],
    )

    group_name = model_package_group_for_bucket(bucket_name)

    eval_metrics_uri = Join(
        on="/",
        values=[
            evaluation_step.properties.ProcessingOutputConfig.Outputs[
                "evaluation"
            ].S3Output.S3Uri,
            "evaluation.json",
        ],
    )

    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri=eval_metrics_uri,
            content_type="application/json",
        ),
    )

    register_step = RegisterModel(
        name="RegisterModelPackage",
        estimator=sklearn_train,
        model_data=train_step.properties.ModelArtifacts.S3ModelArtifacts,
        content_types=["text/csv"],
        response_types=["application/json"],
        inference_instances=["ml.t2.medium", "ml.m5.large"],
        transform_instances=["ml.m5.large"],
        model_package_group_name=group_name,
        approval_status="PendingManualApproval",
        model_metrics=model_metrics,
    )

    gate = ConditionGreaterThanOrEqualTo(
        left=JsonGet(
            step=evaluation_step,
            property_file=evaluation_report,
            json_path="accuracy",
        ),
        right=accuracy_threshold,
    )

    condition_step = ConditionStep(
        name="CheckAccuracy",
        conditions=[gate],
        if_steps=[register_step],
        else_steps=[],
    )

    pipeline = Pipeline(
        name=name,
        parameters=[
            processing_instance_type,
            training_instance_type,
            n_estimators,
            max_depth,
            accuracy_threshold,
        ],
        steps=[process_step, train_step, evaluation_step, condition_step],
        sagemaker_session=pipeline_session,
    )

    return pipeline


if __name__ == "__main__":
    artifacts = os.environ.get("ARTIFACTS_BUCKET_NAME")
    role = os.environ.get("SAGEMAKER_ROLE_ARN")
    if not artifacts or not role:
        print("ERROR: Set ARTIFACTS_BUCKET_NAME and SAGEMAKER_ROLE_ARN (Terraform outputs).")
        raise SystemExit(1)

    pname = pipeline_name_for_bucket(artifacts)
    pl = create_pipeline(artifacts, role, pname)
    pl.upsert(role_arn=role)

    SCRIPT_DIR.joinpath("pipeline_name.txt").write_text(pname, encoding="utf-8")
    SCRIPT_DIR.joinpath("model_package_group.txt").write_text(
        model_package_group_for_bucket(artifacts), encoding="utf-8"
    )
    print(f"Pipeline upsert complete: {pname}")
