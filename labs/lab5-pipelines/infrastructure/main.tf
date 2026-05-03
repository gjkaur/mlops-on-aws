resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "pipeline_bucket" {
  bucket        = "sagemaker-pipeline-${random_id.suffix.hex}"
  force_destroy = true
  tags          = var.tags
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.pipeline_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket                  = aws_s3_bucket.pipeline_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Forward S3 object events to EventBridge (needed for aws.s3 Object Created rules).
resource "aws_s3_bucket_notification" "pipeline_eventbridge" {
  bucket      = aws_s3_bucket.pipeline_bucket.id
  eventbridge = true
}

data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "pipeline_role" {
  name               = "SageMakerPipelineRole-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "pipeline_sagemaker_full" {
  role       = aws_iam_role.pipeline_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "pipeline_s3_full" {
  role       = aws_iam_role.pipeline_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "pipeline_cloudwatch_logs" {
  role       = aws_iam_role.pipeline_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# EventBridge invokes StartPipelineExecution on behalf of rules.
resource "aws_iam_role" "eventbridge_role" {
  name = "EventBridgePipelineRole-${random_id.suffix.hex}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "eventbridge_start_pipeline" {
  name = "EventBridgeStartSageMakerPipeline"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sagemaker:StartPipelineExecution"
      Resource = "*"
    }]
  })
}

output "s3_bucket_name" {
  description = "Data + artifact bucket for SageMaker pipelines"
  value       = aws_s3_bucket.pipeline_bucket.id
}

output "pipeline_role_arn" {
  description = "SageMaker execution role for Pipeline / Processing / Training"
  value       = aws_iam_role.pipeline_role.arn
}

output "pipeline_role_name" {
  value = aws_iam_role.pipeline_role.name
}

output "eventbridge_role_arn" {
  description = "Role assumed by EventBridge when targeting SageMaker Pipelines"
  value       = aws_iam_role.eventbridge_role.arn
}
