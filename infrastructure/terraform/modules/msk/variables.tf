# MSK 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 이름"
  type        = string
}

variable "cluster_name" {
  description = "Kafka 클러스터 이름"
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "Kafka 인스턴스 타입"
  type        = string
  default     = "kafka.t3.small"
}

variable "number_of_broker_nodes" {
  description = "Kafka 브로커 노드 수"
  type        = number
  default     = 3
}

variable "storage_ebs_volume_size" {
  description = "Kafka EBS 볼륨 크기 (GB)"
  type        = number
  default     = 100
}

variable "client_subnets" {
  description = "Kafka 클라이언트 서브넷들"
  type        = list(string)
  default     = []
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
