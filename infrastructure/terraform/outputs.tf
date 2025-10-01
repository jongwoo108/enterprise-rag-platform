# Enterprise RAG Platform - Terraform 출력 값들
# 배포 후 필요한 정보들을 출력

# VPC 정보
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "VPC CIDR 블록"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "퍼블릭 서브넷 ID들"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "프라이빗 서브넷 ID들"
  value       = module.vpc.private_subnet_ids
}

output "database_subnet_ids" {
  description = "데이터베이스 서브넷 ID들"
  value       = module.vpc.database_subnet_ids
}

# EKS 클러스터 정보
output "eks_cluster_name" {
  description = "EKS 클러스터 이름"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS 클러스터 엔드포인트"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS 클러스터 CA 인증서 데이터"
  value       = module.eks.cluster_certificate_authority_data
}

output "eks_cluster_security_group_id" {
  description = "EKS 클러스터 보안 그룹 ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_node_security_group_id" {
  description = "EKS 노드 보안 그룹 ID"
  value       = module.eks.node_security_group_id
}

# OpenSearch 정보
output "opensearch_domain_id" {
  description = "OpenSearch 도메인 ID"
  value       = module.opensearch.domain_id
}

output "opensearch_domain_name" {
  description = "OpenSearch 도메인 이름"
  value       = module.opensearch.domain_name
}

output "opensearch_endpoint" {
  description = "OpenSearch 엔드포인트"
  value       = module.opensearch.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "OpenSearch 대시보드 엔드포인트"
  value       = module.opensearch.dashboard_endpoint
}

# ElastiCache (Redis) 정보
output "redis_cluster_id" {
  description = "Redis 클러스터 ID"
  value       = module.elasticache.cluster_id
}

output "redis_endpoint" {
  description = "Redis 엔드포인트"
  value       = module.elasticache.endpoint
}

output "redis_port" {
  description = "Redis 포트"
  value       = module.elasticache.port
}

# MSK (Kafka) 정보
output "kafka_cluster_arn" {
  description = "Kafka 클러스터 ARN"
  value       = module.msk.cluster_arn
}

output "kafka_cluster_name" {
  description = "Kafka 클러스터 이름"
  value       = module.msk.cluster_name
}

output "kafka_bootstrap_brokers" {
  description = "Kafka 부트스트랩 브로커들"
  value       = module.msk.bootstrap_brokers
}

output "kafka_bootstrap_brokers_tls" {
  description = "Kafka TLS 부트스트랩 브로커들"
  value       = module.msk.bootstrap_brokers_tls
}

# S3 정보
output "s3_bucket_name" {
  description = "S3 버킷 이름"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 버킷 ARN"
  value       = module.s3.bucket_arn
}

output "s3_bucket_domain_name" {
  description = "S3 버킷 도메인 이름"
  value       = module.s3.bucket_domain_name
}

# RDS 정보
output "rds_instance_id" {
  description = "RDS 인스턴스 ID"
  value       = module.rds.instance_id
}

output "rds_endpoint" {
  description = "RDS 엔드포인트"
  value       = module.rds.endpoint
}

output "rds_port" {
  description = "RDS 포트"
  value       = module.rds.port
}

# ALB 정보
output "alb_dns_name" {
  description = "ALB DNS 이름"
  value       = module.alb.alb_dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = module.alb.alb_arn
}

# KMS 키 정보 - 임시 비활성화 (KMS 모듈 비활성화로 인해)
# output "kms_key_ids" {
#   description = "KMS 키 ID들"
#   value = {
#     eks         = module.kms.eks_key_id
#     opensearch  = module.kms.opensearch_key_id
#     redis       = module.kms.redis_key_id
#     kafka       = module.kms.kafka_key_id
#     s3          = module.kms.s3_key_id
#     rds         = module.kms.rds_key_id
#   }
# }

# 보안 그룹 정보 - 임시 비활성화 (security_groups 모듈 비활성화로 인해)
# output "security_group_ids" {
#   description = "보안 그룹 ID들"
#   value = {
#     alb         = module.security_groups.alb_sg_id
#     eks_cluster = module.security_groups.eks_cluster_sg_id
#     eks_node    = module.security_groups.eks_node_sg_id
#     opensearch  = module.security_groups.opensearch_sg_id
#     redis       = module.security_groups.redis_sg_id
#     kafka       = module.security_groups.kafka_sg_id
#     rds         = module.security_groups.rds_sg_id
#   }
# }

# IAM 역할 정보
output "iam_role_arns" {
  description = "IAM 역할 ARN들"
  value = {
    eks_cluster_role = module.iam.eks_cluster_role_arn
    eks_node_role    = module.iam.eks_node_role_arn
    service_role     = module.iam.service_role_arn
  }
}

# CloudWatch 정보
output "cloudwatch_log_groups" {
  description = "CloudWatch 로그 그룹들"
  value       = module.cloudwatch.log_groups
}

output "cloudwatch_alarms" {
  description = "CloudWatch 알람들"
  value       = module.cloudwatch.alarms
}

# 환경별 설정 정보
output "environment_config" {
  description = "환경별 설정 정보"
  value = {
    environment     = var.environment
    aws_region      = var.aws_region
    project_name    = var.project_name
    cluster_version = var.eks_cluster_version
  }
}

# 연결 정보 (Kubernetes 설정용)
output "kubeconfig" {
  description = "kubectl 설정 명령어"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# 서비스 엔드포인트 정보 (애플리케이션 설정용)
output "service_endpoints" {
  description = "서비스 엔드포인트 정보"
  value = {
    opensearch = {
      endpoint = module.opensearch.endpoint
      port     = 443
      protocol = "https"
    }
    redis = {
      endpoint = module.elasticache.endpoint
      port     = module.elasticache.port
      protocol = "redis"
    }
    kafka = {
      endpoint = module.msk.bootstrap_brokers
      protocol = "ssl"
    }
    s3 = {
      bucket   = module.s3.bucket_name
      region   = var.aws_region
      protocol = "https"
    }
    postgres = {
      endpoint = module.rds.endpoint
      port     = module.rds.port
      protocol = "postgresql"
    }
  }
}

# 배포 상태 정보
output "deployment_status" {
  description = "배포 상태 정보"
  value = {
    vpc_created         = length(module.vpc.vpc_id) > 0
    eks_created         = length(module.eks.cluster_name) > 0
    opensearch_created  = length(module.opensearch.domain_id) > 0
    redis_created       = length(module.elasticache.cluster_id) > 0
    kafka_created       = length(module.msk.cluster_arn) > 0
    s3_created          = length(module.s3.bucket_name) > 0
    rds_created         = module.rds.instance_id != null ? length(module.rds.instance_id) > 0 : false
    alb_created         = length(module.alb.dns_name) > 0
  }
}

# 비용 정보 (선택사항)
output "estimated_monthly_cost" {
  description = "예상 월 비용 (USD)"
  value = {
    eks_nodes     = "~$50-100 (노드 타입에 따라)"
    opensearch    = "~$30-60 (인스턴스 타입에 따라)"
    redis         = "~$15-30 (노드 타입에 따라)"
    kafka         = "~$60-120 (인스턴스 타입에 따라)"
    rds           = "~$15-30 (인스턴스 타입에 따라)"
    alb           = "~$20-40"
    storage       = "~$10-20"
    total         = "~$200-400 (월 예상 비용)"
  }
}