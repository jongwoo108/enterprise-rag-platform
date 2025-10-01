# IAM 모듈 변수 정의

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

variable "eks_node_role_arn" {
  description = "EKS 노드 역할 ARN"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 버킷 ARN"
  type        = string
}

variable "opensearch_domain_arn" {
  description = "OpenSearch 도메인 ARN"
  type        = string
}

variable "kafka_cluster_arn" {
  description = "Kafka 클러스터 ARN"
  type        = string
}

variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default     = {}
}
