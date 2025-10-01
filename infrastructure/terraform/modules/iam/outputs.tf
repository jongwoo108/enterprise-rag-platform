# IAM 모듈 출력 값들

output "eks_cluster_role_arn" {
  description = "EKS 클러스터 역할 ARN"
  value       = aws_iam_role.eks_cluster.arn
}

output "eks_node_group_role_arn" {
  description = "EKS 노드 그룹 역할 ARN"
  value       = aws_iam_role.eks_node_group.arn
}

output "eks_node_role_arn" {
  description = "EKS 노드 역할 ARN"
  value       = aws_iam_role.eks_node_group.arn
}

output "service_role_arn" {
  description = "서비스 역할 ARN"
  value       = aws_iam_role.eks_cluster.arn
}
