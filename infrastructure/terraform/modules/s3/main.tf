# S3 모듈 - 객체 스토리지 구성

# S3 버킷
resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${var.environment}-rag-documents"

  tags = {
    Name        = "${var.project_name}-${var.environment}-rag-documents"
    Environment = var.environment
    Project     = var.project_name
  }
}

# S3 버킷 버전 관리
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 버킷 암호화
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 버킷 퍼블릭 액세스 차단
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

