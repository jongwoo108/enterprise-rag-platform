# CloudWatch 모듈 - 모니터링 구성

# CloudWatch 로그 그룹들
# EKS 클러스터가 자동으로 로그 그룹을 생성하므로 주석 처리
# resource "aws_cloudwatch_log_group" "eks_cluster" {
#   count             = var.enable_logs ? 1 : 0
#   name              = "/aws/eks/${var.eks_cluster_name}/cluster"
#   retention_in_days = var.log_retention_days

#   tags = {
#     Name        = "${var.project_name}-${var.environment}-eks-cluster-logs"
#     Environment = var.environment
#     Project     = var.project_name
#   }
# }

resource "aws_cloudwatch_log_group" "application" {
  count             = var.enable_logs ? 1 : 0
  name              = "/aws/eks/${var.eks_cluster_name}/application"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-application-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch 알람
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count               = var.enable_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EKS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors EKS cluster cpu utilization"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    ClusterName = var.eks_cluster_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-high-cpu-alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "low_disk_space" {
  count               = var.enable_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-low-disk-space"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DiskSpaceUtilization"
  namespace           = "AWS/EKS"
  period              = "300"
  statistic           = "Average"
  threshold           = "20"
  alarm_description   = "This metric monitors EKS cluster disk space utilization"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    ClusterName = var.eks_cluster_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-low-disk-space-alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  count               = var.enable_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-${var.environment}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/EKS"
  period              = "120"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors EKS cluster memory utilization"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    ClusterName = var.eks_cluster_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-high-memory-alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}
