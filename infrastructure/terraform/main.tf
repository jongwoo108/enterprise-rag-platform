# Enterprise RAG Platform - 메인 Terraform 구성
# AWS 클라우드 인프라스트럭처 전체를 정의

# Terraform 및 Provider 설정
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  # 원격 상태 저장소 (선택사항)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "enterprise-rag-platform/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# AWS Provider 설정
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = merge(var.common_tags, {
      Environment = var.environment
      Project     = var.project_name
    })
  }
}

# Kubernetes Provider 설정 (EKS 클러스터 생성 후 사용)
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

# Helm Provider 설정
provider "helm" {
  repository_config_path = "${path.module}/.helm/repositories.yaml"
  repository_cache       = "${path.module}/.helm"
  
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# 데이터 소스
data "aws_caller_identity" "current" {}

# 랜덤 리소스 (고유 ID 생성용)
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# 로컬 값들
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  # S3 버킷 이름 (고유성 보장)
  s3_bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.name_prefix}-storage-${random_string.suffix.result}"
  
  # Kafka 클라이언트 서브넷 (VPC 모듈에서 가져옴)
  kafka_client_subnets = var.kafka_client_subnets != [] ? var.kafka_client_subnets : module.vpc.private_subnet_ids
  
  # 공통 태그
  common_tags = merge(var.common_tags, {
    TerraformManaged = "true"
    CreatedBy        = "terraform"
  })
}

# VPC 모듈
module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_cidr                = var.vpc_cidr
  public_subnet_cidrs     = var.public_subnet_cidrs
  private_subnet_cidrs    = var.private_subnet_cidrs
  database_subnet_cidrs   = var.database_subnet_cidrs
  
  enable_nat_gateway = var.enable_nat_gateway
  enable_vpn_gateway = var.enable_vpn_gateway
  
  common_tags = local.common_tags
}

# KMS 키 모듈 - 임시 비활성화 (모듈 파일 누락)
# module "kms" {
#   source = "./modules/kms"
#   
#   project_name = var.project_name
#   environment  = var.environment
#   
#   common_tags = local.common_tags
# }

# EKS 클러스터 모듈
module "eks" {
  source = "./modules/eks"
  
  project_name = var.project_name
  environment  = var.environment
  
  # VPC 설정
  vpc_id          = module.vpc.vpc_id
  vpc_cidr        = var.vpc_cidr
  subnet_ids      = module.vpc.private_subnet_ids
  
  # EKS 설정
  cluster_version                = var.eks_cluster_version
  node_group_instance_types      = var.eks_node_group_instance_types
  node_group_capacity_type       = var.eks_node_group_capacity_type
  node_group_desired_size        = var.eks_node_group_desired_size
  node_group_min_size            = var.eks_node_group_min_size
  node_group_max_size            = var.eks_node_group_max_size
  
  # 보안 설정
  # kms_key_id = module.kms.eks_key_id  # 임시 비활성화
  
  common_tags = local.common_tags
}

# OpenSearch 모듈
module "opensearch" {
  source = "./modules/opensearch"
  
  project_name = var.project_name
  environment  = var.environment
  
  domain_name       = var.opensearch_domain_name
  instance_type     = var.opensearch_instance_type
  instance_count    = var.opensearch_instance_count
  volume_size       = var.opensearch_volume_size
  ebs_enabled       = var.opensearch_ebs_enabled
  
  # 네트워크 설정
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.database_subnet_ids
  # security_group_id = module.security_groups.opensearch_sg_id  # 임시 비활성화
  
  # 암호화 설정
  # kms_key_id = module.kms.opensearch_key_id  # 임시 비활성화
  
  common_tags = local.common_tags
}

# ElastiCache (Redis) 모듈
module "elasticache" {
  source = "./modules/elasticache"
  
  project_name = var.project_name
  environment  = var.environment
  
  node_type              = var.redis_node_type
  num_cache_nodes        = var.redis_num_cache_nodes
  parameter_group_name   = var.redis_parameter_group_name
  engine_version         = var.redis_engine_version
  
  # 네트워크 설정
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.database_subnet_ids
  # security_group_id = module.security_groups.redis_sg_id  # 임시 비활성화
  
  common_tags = local.common_tags
}

# MSK (Kafka) 모듈
module "msk" {
  source = "./modules/msk"
  
  depends_on = [module.vpc]
  
  project_name = var.project_name
  environment  = var.environment
  
  cluster_name                   = var.kafka_cluster_name
  instance_type                  = var.kafka_instance_type
  number_of_broker_nodes         = var.kafka_number_of_broker_nodes
  storage_ebs_volume_size        = var.kafka_storage_ebs_volume_size
  client_subnets                 = module.vpc.private_subnet_ids
  
  # 네트워크 설정
  vpc_id            = module.vpc.vpc_id
  # security_group_id = module.security_groups.kafka_sg_id  # 임시 비활성화
  
  # 암호화 설정
  # kms_key_id = module.kms.kafka_key_id  # 임시 비활성화
  
  common_tags = local.common_tags
}

# S3 모듈
module "s3" {
  source = "./modules/s3"
  
  project_name = var.project_name
  environment  = var.environment
  
  bucket_name           = local.s3_bucket_name
  versioning_enabled    = var.s3_versioning_enabled
  encryption_enabled    = var.s3_encryption_enabled
  lifecycle_enabled     = var.s3_lifecycle_enabled
  
  # 암호화 설정
  # kms_key_id = module.kms.s3_key_id  # 임시 비활성화
  
  common_tags = local.common_tags
}

# RDS 모듈 (메타데이터용 PostgreSQL)
module "rds" {
  source = "./modules/rds"
  
  project_name = var.project_name
  environment  = var.environment
  
  # RDS 설정
  enable_rds = var.enable_rds
  
  # 데이터베이스 설정
  db_engine               = var.rds_engine
  db_engine_version       = var.rds_engine_version
  db_instance_class       = var.rds_instance_class
  db_allocated_storage    = var.rds_allocated_storage
  db_name                 = var.rds_db_name
  db_username             = var.rds_username
  db_password             = var.rds_password
  db_backup_retention_period = var.rds_backup_retention_period
  
  # 네트워크 설정
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.database_subnet_ids
  # db_security_group_id = module.security_groups.rds_sg_id  # 임시 비활성화
  
  # 암호화 설정
  # kms_key_id = module.kms.rds_key_id  # 임시 비활성화
  
  common_tags = local.common_tags
}

# ALB 모듈
module "alb" {
  source = "./modules/alb"
  
  project_name = var.project_name
  environment  = var.environment
  
  # 네트워크 설정
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  # security_group_ids    = [module.security_groups.alb_security_group_id]  # 임시 비활성화
  
  common_tags = local.common_tags
}

# 보안 그룹 모듈 (임시 비활성화 - 순환 의존성 해결을 위해)
# module "security_groups" {
#   source = "./modules/security-groups"
#   
#   project_name = var.project_name
#   environment  = var.environment
#   
#   vpc_id = module.vpc.vpc_id
#   vpc_cidr = var.vpc_cidr
#   
#   # 허용된 CIDR 블록들
#   allowed_cidr_blocks = var.allowed_cidr_blocks
#   
#   common_tags = local.common_tags
# }

# CloudWatch 모니터링 모듈
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  project_name = var.project_name
  environment  = var.environment
  
  # 모니터링 설정
  enable_logs   = var.enable_cloudwatch_logs
  enable_alarms = var.enable_cloudwatch_alarms
  
  log_retention_days = var.log_retention_days
  
  # 리소스 ARN들
  eks_cluster_name     = module.eks.cluster_name
  opensearch_domain_id = module.opensearch.domain_id
  redis_cluster_id     = module.elasticache.cluster_id
  kafka_cluster_arn    = module.msk.cluster_arn
  rds_instance_id      = module.rds.db_instance_id
  
  common_tags = local.common_tags
}

# IAM 역할 및 정책 모듈
module "iam" {
  source = "./modules/iam"
  
  project_name = var.project_name
  environment  = var.environment
  
  # 리소스 ARN들
  s3_bucket_arn           = module.s3.bucket_arn
  opensearch_domain_arn   = module.opensearch.domain_arn
  kafka_cluster_arn       = module.msk.cluster_arn
  
  # EKS 설정
  eks_cluster_name = module.eks.cluster_name
  eks_node_role_arn = module.eks.node_role_arn
  
  common_tags = local.common_tags
}

# Helm 차트 배포
module "helm_charts" {
  source = "./modules/helm-charts"
  
  project_name = var.project_name
  environment  = var.environment
  
  # EKS 설정
  cluster_name = module.eks.cluster_name
  
  # 서비스 엔드포인트들
  opensearch_endpoint = module.opensearch.endpoint
  redis_endpoint      = module.elasticache.endpoint
  kafka_endpoint      = module.msk.bootstrap_brokers
  s3_bucket_name      = module.s3.bucket_name
  rds_endpoint        = module.rds.db_instance_endpoint
  
  common_tags = local.common_tags
  
  depends_on = [
    module.eks,
    module.opensearch,
    module.elasticache,
    module.msk,
    module.s3,
    module.rds
  ]
}