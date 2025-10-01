# ALB 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 (production, development)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "퍼블릭 서브넷 ID 목록"
  type        = list(string)
}

variable "security_group_ids" {
  description = "보안 그룹 ID 목록"
  type        = list(string)
  default     = []
}

variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default     = {}
}
