locals {
  tags = merge(var.tags, { Project = var.project_name })
}

resource "random_id" "suffix" {
  byte_length = 4
}

# Raw / landing data + EventBridge "new-data/" triggers live here only.
resource "aws_s3_bucket" "data_bucket" {
  bucket        = "mlops-capstone-data-${random_id.suffix.hex}"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_public_access_block" "data_pab" {
  bucket                  = aws_s3_bucket.data_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_notification" "data_eventbridge" {
  bucket      = aws_s3_bucket.data_bucket.id
  eventbridge = true
}

resource "aws_s3_bucket" "artifacts_bucket" {
  bucket        = "mlops-capstone-artifacts-${random_id.suffix.hex}"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_versioning" "artifacts_versioning" {
  bucket = aws_s3_bucket.artifacts_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts_pab" {
  bucket                  = aws_s3_bucket.artifacts_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "capture_bucket" {
  bucket        = "mlops-capstone-capture-${random_id.suffix.hex}"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_public_access_block" "capture_pab" {
  bucket                  = aws_s3_bucket.capture_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "reports_bucket" {
  bucket        = "mlops-capstone-reports-${random_id.suffix.hex}"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_public_access_block" "reports_pab" {
  bucket                  = aws_s3_bucket.reports_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
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

resource "aws_iam_role" "sagemaker_role" {
  name               = "MLOpsCapstoneRole-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
  tags               = local.tags
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_iam_role" "eventbridge_role" {
  name = "MLOpsCapstoneEventBridgeRole-${random_id.suffix.hex}"

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

  tags = local.tags
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

resource "aws_sns_topic" "alert_topic" {
  name = "mlops-capstone-alerts-${random_id.suffix.hex}"
  tags = local.tags
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.alert_topic.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "data_bucket_name" {
  description = "Landing bucket; EventBridge emits on new-data/*"
  value       = aws_s3_bucket.data_bucket.id
}

output "artifacts_bucket_name" {
  description = "Pipeline preprocessing outputs + training artefacts + SageMaker uploads"
  value       = aws_s3_bucket.artifacts_bucket.id
}

output "capture_bucket_name" {
  description = "Realtime endpoint DataCapture destination"
  value       = aws_s3_bucket.capture_bucket.id
}

output "reports_bucket_name" {
  description = "Model Monitor reports + derived baseline CSV helpers"
  value       = aws_s3_bucket.reports_bucket.id
}

output "sagemaker_role_arn" {
  value = aws_iam_role.sagemaker_role.arn
}

output "eventbridge_role_arn" {
  value = aws_iam_role.eventbridge_role.arn
}

output "sns_topic_arn" {
  value = aws_sns_topic.alert_topic.arn
}
