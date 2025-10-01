# S3 모듈 출력 값들

output "bucket_name" {
  description = "S3 버킷 이름"
  value       = aws_s3_bucket.main.bucket
}

output "bucket_arn" {
  description = "S3 버킷 ARN"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "S3 버킷 도메인 이름"
  value       = aws_s3_bucket.main.bucket_domain_name
}
