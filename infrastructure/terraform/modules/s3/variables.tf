# S3 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 (production, development)"
  type        = string
}

variable "bucket_name" {
  description = "S3 버킷 이름"
  type        = string
  default     = ""
}

variable "versioning_enabled" {
  description = "S3 버킷 버전 관리 활성화"
  type        = bool
  default     = true
}

variable "encryption_enabled" {
  description = "S3 버킷 암호화 활성화"
  type        = bool
  default     = true
}

variable "lifecycle_enabled" {
  description = "S3 버킷 라이프사이클 활성화"
  type        = bool
  default     = true
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
