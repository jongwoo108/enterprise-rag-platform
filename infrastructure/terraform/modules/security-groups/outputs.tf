# Security Groups 모듈 출력 값들

output "alb_security_group_id" {
  description = "ALB 보안 그룹 ID"
  value       = aws_security_group.alb.id
}

output "eks_cluster_security_group_id" {
  description = "EKS 클러스터 보안 그룹 ID"
  value       = aws_security_group.eks_cluster.id
}

output "eks_nodes_security_group_id" {
  description = "EKS 노드 보안 그룹 ID"
  value       = aws_security_group.eks_nodes.id
}

output "redis_sg_id" {
  description = "Redis 보안 그룹 ID"
  value       = aws_security_group.redis.id
}

output "rds_sg_id" {
  description = "RDS 보안 그룹 ID"
  value       = aws_security_group.rds.id
}

output "opensearch_sg_id" {
  description = "OpenSearch 보안 그룹 ID"
  value       = aws_security_group.opensearch.id
}
