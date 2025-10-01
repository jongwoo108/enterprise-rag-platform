# CloudWatch 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 (production, development)"
  type        = string
}

variable "eks_cluster_name" {
  description = "EKS 클러스터 이름"
  type        = string
}

variable "enable_logs" {
  description = "CloudWatch 로그 활성화"
  type        = bool
  default     = true
}

variable "enable_alarms" {
  description = "CloudWatch 알람 활성화"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "로그 보존 기간 (일)"
  type        = number
  default     = 7
}

variable "sns_topic_arn" {
  description = "SNS 토픽 ARN (알람용)"
  type        = string
  default     = ""
}

variable "opensearch_domain_id" {
  description = "OpenSearch 도메인 ID"
  type        = string
  default     = ""
}

variable "redis_cluster_id" {
  description = "Redis 클러스터 ID"
  type        = string
  default     = ""
}

variable "kafka_cluster_arn" {
  description = "Kafka 클러스터 ARN"
  type        = string
  default     = ""
}

variable "rds_instance_id" {
  description = "RDS 인스턴스 ID"
  type        = string
  default     = ""
}

variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default     = {}
}
