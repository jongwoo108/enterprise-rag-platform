# Enterprise RAG Platform - Terraform 변수 정의
# AWS 클라우드 인프라스트럭처 배포를 위한 변수들

# 프로젝트 기본 정보
variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "enterprise-rag-platform"
}

variable "environment" {
  description = "배포 환경 (dev, staging, prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "환경은 dev, staging, prod 중 하나여야 합니다."
  }
}

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "us-east-1"
}

# availability_zones 변수는 VPC 모듈에서 data source로 동적으로 가져옵니다

# VPC 설정
variable "vpc_cidr" {
  description = "VPC CIDR 블록"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "퍼블릭 서브넷 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "프라이빗 서브넷 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "database_subnet_cidrs" {
  description = "데이터베이스 서브넷 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
}

# EKS 설정
variable "eks_cluster_version" {
  description = "EKS 클러스터 버전"
  type        = string
  default     = "1.28"
}

variable "eks_node_group_instance_types" {
  description = "EKS 노드 그룹 인스턴스 타입"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "eks_node_group_capacity_type" {
  description = "EKS 노드 그룹 용량 타입"
  type        = string
  default     = "ON_DEMAND"
  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.eks_node_group_capacity_type)
    error_message = "용량 타입은 ON_DEMAND 또는 SPOT이어야 합니다."
  }
}

variable "eks_node_group_desired_size" {
  description = "EKS 노드 그룹 원하는 크기"
  type        = number
  default     = 3
}

variable "eks_node_group_min_size" {
  description = "EKS 노드 그룹 최소 크기"
  type        = number
  default     = 1
}

variable "eks_node_group_max_size" {
  description = "EKS 노드 그룹 최대 크기"
  type        = number
  default     = 10
}

# OpenSearch 설정
variable "opensearch_domain_name" {
  description = "OpenSearch 도메인 이름"
  type        = string
  default     = "enterprise-rag-opensearch"
}

variable "opensearch_instance_type" {
  description = "OpenSearch 인스턴스 타입"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "OpenSearch 인스턴스 수"
  type        = number
  default     = 3
}

variable "opensearch_volume_size" {
  description = "OpenSearch 볼륨 크기 (GB)"
  type        = number
  default     = 20
}

variable "opensearch_ebs_enabled" {
  description = "OpenSearch EBS 암호화 활성화"
  type        = bool
  default     = true
}

# ElastiCache (Redis) 설정
variable "redis_node_type" {
  description = "Redis 노드 타입"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Redis 캐시 노드 수"
  type        = number
  default     = 1
}

variable "redis_parameter_group_name" {
  description = "Redis 파라미터 그룹 이름"
  type        = string
  default     = "default.redis7"
}

variable "redis_engine_version" {
  description = "Redis 엔진 버전"
  type        = string
  default     = "7.0"
}

# MSK (Kafka) 설정
variable "kafka_cluster_name" {
  description = "Kafka 클러스터 이름"
  type        = string
  default     = "enterprise-rag-kafka"
}

variable "kafka_instance_type" {
  description = "Kafka 인스턴스 타입"
  type        = string
  default     = "kafka.t3.small"
}

variable "kafka_number_of_broker_nodes" {
  description = "Kafka 브로커 노드 수"
  type        = number
  default     = 3
}

variable "kafka_storage_ebs_volume_size" {
  description = "Kafka EBS 볼륨 크기 (GB)"
  type        = number
  default     = 100
}

variable "kafka_client_subnets" {
  description = "Kafka 클라이언트 서브넷들"
  type        = list(string)
  default     = []
}

# S3 설정
variable "s3_bucket_name" {
  description = "S3 버킷 이름"
  type        = string
  default     = ""
}

variable "s3_versioning_enabled" {
  description = "S3 버전 관리 활성화"
  type        = bool
  default     = true
}

variable "s3_encryption_enabled" {
  description = "S3 암호화 활성화"
  type        = bool
  default     = true
}

variable "s3_lifecycle_enabled" {
  description = "S3 라이프사이클 정책 활성화"
  type        = bool
  default     = true
}

# ALB 설정
variable "alb_name" {
  description = "Application Load Balancer 이름"
  type        = string
  default     = "enterprise-rag-alb"
}

variable "alb_internal" {
  description = "ALB를 내부용으로 설정"
  type        = bool
  default     = false
}

variable "alb_idle_timeout" {
  description = "ALB 유휴 시간 초과 (초)"
  type        = number
  default     = 60
}

# RDS 설정 (메타데이터용)
variable "rds_instance_class" {
  description = "RDS 인스턴스 클래스"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS 할당된 스토리지 (GB)"
  type        = number
  default     = 20
}

variable "rds_engine_version" {
  description = "RDS 엔진 버전"
  type        = string
  default     = "16.1"
}

variable "rds_backup_retention_period" {
  description = "RDS 백업 보존 기간 (일)"
  type        = number
  default     = 7
}

variable "enable_rds" {
  description = "RDS 활성화"
  type        = bool
  default     = false
}

variable "rds_engine" {
  description = "RDS 엔진"
  type        = string
  default     = "postgres"
}

variable "rds_db_name" {
  description = "RDS 데이터베이스 이름"
  type        = string
  default     = "enterprise_rag"
}

variable "rds_username" {
  description = "RDS 사용자명"
  type        = string
  default     = "postgres"
}

variable "rds_password" {
  description = "RDS 비밀번호"
  type        = string
  sensitive   = true
  default     = "changeme123!"
}

# 보안 설정
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

variable "allowed_cidr_blocks" {
  description = "허용된 CIDR 블록들"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# 태그
variable "common_tags" {
  description = "공통 태그"
  type        = map(string)
  default = {
    Project     = "Enterprise RAG Platform"
    Environment = "prod"
    ManagedBy   = "Terraform"
    Owner       = "DevOps Team"
  }
}

# 모니터링 설정
variable "enable_cloudwatch_logs" {
  description = "CloudWatch 로그 활성화"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "로그 보존 기간 (일)"
  type        = number
  default     = 30
}

variable "enable_cloudwatch_alarms" {
  description = "CloudWatch 알람 활성화"
  type        = bool
  default     = true
}

# 비용 최적화
variable "enable_cost_allocation_tags" {
  description = "비용 할당 태그 활성화"
  type        = bool
  default     = true
}

variable "enable_spot_instances" {
  description = "Spot 인스턴스 활성화"
  type        = bool
  default     = false
}

# 백업 설정
variable "backup_retention_days" {
  description = "백업 보존 기간 (일)"
  type        = number
  default     = 30
}

variable "backup_schedule" {
  description = "백업 스케줄 (cron 형식)"
  type        = string
  default     = "cron(0 2 * * ? *)"  # 매일 오전 2시
}