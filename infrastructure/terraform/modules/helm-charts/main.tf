# Helm Charts 모듈 - Kubernetes 차트 구성

# AWS Load Balancer Controller
resource "helm_release" "aws_load_balancer_controller" {
  count = var.enable_alb_controller ? 1 : 0

  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  
  depends_on = [var.alb_controller_service_account]

  set {
    name  = "clusterName"
    value = var.eks_cluster_name != "" ? var.eks_cluster_name : var.cluster_name
  }

  set {
    name  = "serviceAccount.create"
    value = "false"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }
}

# Prometheus (모니터링)
resource "helm_release" "prometheus" {
  count = var.enable_monitoring ? 1 : 0

  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = "monitoring"

  create_namespace = true

  values = [
    file("${path.module}/values/prometheus-values.yaml")
  ]
}

# Jaeger (분산 추적)
resource "helm_release" "jaeger" {
  count = var.enable_tracing ? 1 : 0

  name       = "jaeger"
  repository = "https://jaegertracing.github.io/helm-charts"
  chart      = "jaeger"
  namespace  = "observability"

  create_namespace = true

  values = [
    file("${path.module}/values/jaeger-values.yaml")
  ]
}
