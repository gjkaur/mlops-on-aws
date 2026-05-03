resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "monitoring_bucket" {
  bucket        = "sagemaker-monitoring-${random_id.suffix.hex}"
  force_destroy = true
  tags          = var.tags
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.monitoring_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket                  = aws_s3_bucket.monitoring_bucket.id
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

resource "aws_iam_role" "monitoring_role" {
  name               = "SageMakerMonitoringRole-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.monitoring_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.monitoring_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.monitoring_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_sns_topic" "monitoring_alerts" {
  name = "sagemaker-monitoring-alerts-${random_id.suffix.hex}"
  tags = var.tags
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.monitoring_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "s3_bucket_name" {
  description = "Bucket for training data, captures, baseline, and monitoring reports"
  value       = aws_s3_bucket.monitoring_bucket.id
}

output "monitoring_role_arn" {
  description = "SageMaker execution role for training, inference, monitoring jobs"
  value       = aws_iam_role.monitoring_role.arn
}

output "monitoring_role_name" {
  value = aws_iam_role.monitoring_role.name
}

output "sns_topic_arn" {
  description = "Subscribe CloudWatch alarms to this SNS topic ARN"
  value       = aws_sns_topic.monitoring_alerts.arn
}
