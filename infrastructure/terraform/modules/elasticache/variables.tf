# ElastiCache 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 이름"
  type        = string
}

variable "node_type" {
  description = "Redis 노드 타입"
  type        = string
  default     = "cache.t3.micro"
}

variable "num_cache_nodes" {
  description = "Redis 캐시 노드 수"
  type        = number
  default     = 1
}

variable "parameter_group_name" {
  description = "Redis 파라미터 그룹 이름"
  type        = string
  default     = "default.redis7"
}

variable "engine_version" {
  description = "Redis 엔진 버전"
  type        = string
  default     = "6.2"
}

variable "subnet_ids" {
  description = "서브넷 ID들"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "security_group_id" {
  description = "보안 그룹 ID"
  type        = string
  default     = ""
}

variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default     = {}
}
