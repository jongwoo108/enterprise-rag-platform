# EKS 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 이름"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR 블록"
  type        = string
}

variable "subnet_ids" {
  description = "서브넷 ID들"
  type        = list(string)
}

variable "cluster_version" {
  description = "EKS 클러스터 버전"
  type        = string
  default     = "1.28"
}

variable "node_group_instance_types" {
  description = "EKS 노드 그룹 인스턴스 타입"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "node_group_capacity_type" {
  description = "EKS 노드 그룹 용량 타입"
  type        = string
  default     = "ON_DEMAND"
}

variable "node_group_desired_size" {
  description = "EKS 노드 그룹 원하는 크기"
  type        = number
  default     = 3
}

variable "node_group_min_size" {
  description = "EKS 노드 그룹 최소 크기"
  type        = number
  default     = 1
}

variable "node_group_max_size" {
  description = "EKS 노드 그룹 최대 크기"
  type        = number
  default     = 10
}

variable "kms_key_id" {
  description = "KMS 키 ID (암호화용)"
  type        = string
  default     = ""
}

variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default     = {}
}
