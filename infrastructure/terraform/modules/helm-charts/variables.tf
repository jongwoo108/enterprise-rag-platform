# Helm Charts 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 (production, development)"
  type        = string
}

variable "cluster_name" {
  description = "EKS 클러스터 이름"
  type        = string
}

variable "eks_cluster_name" {
  description = "EKS 클러스터 이름 (별칭)"
  type        = string
  default     = ""
}

variable "opensearch_endpoint" {
  description = "OpenSearch 엔드포인트"
  type        = string
}

variable "redis_endpoint" {
  description = "Redis 엔드포인트"
  type        = string
}

variable "kafka_endpoint" {
  description = "Kafka 엔드포인트"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 버킷 이름"
  type        = string
}

variable "rds_endpoint" {
  description = "RDS 엔드포인트"
  type        = string
}

variable "enable_alb_controller" {
  description = "ALB 컨트롤러 활성화"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "모니터링 활성화"
  type        = bool
  default     = true
}

variable "enable_tracing" {
  description = "분산 추적 활성화"
  type        = bool
  default     = true
}

variable "alb_controller_service_account" {
  description = "ALB 컨트롤러 서비스 계정"
  type        = string
  default     = ""
}

variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default     = {}
}
