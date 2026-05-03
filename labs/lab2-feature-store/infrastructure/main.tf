# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# ============================================
# S3 BUCKET FOR OFFLINE FEATURE STORE OUTPUTS / ATHENA
# ============================================
resource "aws_s3_bucket" "feature_store_bucket" {
  bucket        = "feature-store-${random_id.suffix.hex}"
  force_destroy = true
  tags          = var.tags
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.feature_store_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket                  = aws_s3_bucket.feature_store_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================
# IAM ROLE FOR SAGEMAKER FEATURE STORE
# ============================================
data "aws_iam_policy_document" "feature_store_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "feature_store_role" {
  name               = "FeatureStoreRole-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.feature_store_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.feature_store_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.feature_store_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.feature_store_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_iam_role_policy_attachment" "glue_console" {
  role       = aws_iam_role.feature_store_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess"
}

# ============================================
# GLUE DATABASE FOR ATHENA QUERIES (OFFLINE TABLES)
# ============================================
resource "aws_glue_catalog_database" "feature_store_db" {
  name        = "sagemaker_featurestore"
  description = "Glue catalog DB for querying SageMaker offline feature store exports (LAB 2)"
}

# ============================================
# OUTPUTS
# ============================================
output "s3_bucket_name" {
  description = "Name of the S3 bucket for feature store"
  value       = aws_s3_bucket.feature_store_bucket.id
}

output "feature_store_role_arn" {
  description = "ARN of the Feature Store execution role"
  value       = aws_iam_role.feature_store_role.arn
}

output "glue_database_name" {
  description = "Name of the Glue database for offline store"
  value       = aws_glue_catalog_database.feature_store_db.name
}

output "suffix" {
  description = "Random suffix used for resource names"
  value       = random_id.suffix.hex
}
