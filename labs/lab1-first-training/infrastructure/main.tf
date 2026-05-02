# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# S3 Bucket for training code and model artifacts
resource "aws_s3_bucket" "sagemaker_bucket" {
  bucket        = "sagemaker-lab1-${random_id.suffix.hex}"
  force_destroy = true
  tags          = var.tags
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.sagemaker_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket = aws_s3_bucket.sagemaker_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role for SageMaker
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

resource "aws_iam_role" "sagemaker_execution_role" {
  name               = "SageMakerExecutionRole-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket created for training"
  value       = aws_s3_bucket.sagemaker_bucket.id
}

output "sagemaker_role_arn" {
  description = "ARN of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_execution_role.arn
}

output "sagemaker_role_name" {
  description = "Name of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_execution_role.name
}
