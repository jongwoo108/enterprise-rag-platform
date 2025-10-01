# OpenSearch 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 이름"
  type        = string
}

variable "domain_name" {
  description = "OpenSearch 도메인 이름"
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "OpenSearch 인스턴스 타입"
  type        = string
  default     = "t3.small.search"
}

variable "instance_count" {
  description = "OpenSearch 인스턴스 수"
  type        = number
  default     = 3
}

variable "volume_size" {
  description = "OpenSearch 볼륨 크기 (GB)"
  type        = number
  default     = 20
}

variable "ebs_enabled" {
  description = "OpenSearch EBS 활성화"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "서브넷 ID들"
  type        = list(string)
}

variable "security_group_id" {
  description = "보안 그룹 ID"
  type        = string
  default     = ""
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
