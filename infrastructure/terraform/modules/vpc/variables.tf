# VPC 모듈 변수 정의

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경 이름"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR 블록"
  type        = string
  default     = "10.0.0.0/16"
}

# availability_zones 변수는 data source로 동적으로 가져옵니다

variable "public_subnet_cidrs" {
  description = "퍼블릭 서브넷 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "프라이빗 서브넷 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "database_subnet_cidrs" {
  description = "데이터베이스 서브넷 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24"]
}

variable "enable_nat_gateway" {
  description = "NAT Gateway 활성화"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "VPN Gateway 활성화"
  type        = bool
  default     = false
}

variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default     = {}
}
