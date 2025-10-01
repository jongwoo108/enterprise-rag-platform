# CloudWatch 모듈 출력 값들

# EKS 클러스터는 자동으로 로그 그룹을 생성하므로 제거
# output "eks_cluster_log_group_name" {
#   description = "EKS 클러스터 로그 그룹 이름"
#   value       = var.enable_logs ? aws_cloudwatch_log_group.eks_cluster[0].name : null
# }

output "application_log_group_name" {
  description = "애플리케이션 로그 그룹 이름"
  value       = var.enable_logs ? aws_cloudwatch_log_group.application[0].name : null
}

output "log_groups" {
  description = "모든 로그 그룹 정보"
  value = {
    application = var.enable_logs ? aws_cloudwatch_log_group.application[0].name : null
  }
}

output "alarms" {
  description = "모든 알람 정보"
  value = var.enable_alarms ? {
    high_cpu    = aws_cloudwatch_metric_alarm.high_cpu[0].alarm_name
    low_disk    = aws_cloudwatch_metric_alarm.low_disk_space[0].alarm_name
    high_memory = aws_cloudwatch_metric_alarm.high_memory[0].alarm_name
  } : {}
}
