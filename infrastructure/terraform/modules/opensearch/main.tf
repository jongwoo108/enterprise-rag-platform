# OpenSearch 모듈 - 검색 엔진 구성

# OpenSearch 보안 그룹
resource "aws_security_group" "opensearch" {
  name_prefix = "${var.project_name}-${var.environment}-opensearch-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # VPC 내부에서만 접근
  }

  ingress {
    from_port   = 9200
    to_port     = 9200
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # HTTP 포트 (내부용)
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-opensearch-sg"
  })
}

# OpenSearch Domain
resource "aws_opensearch_domain" "main" {
  domain_name    = "rag-${var.environment}-search"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type            = var.instance_type
    instance_count           = var.instance_count
    dedicated_master_enabled = var.instance_count > 3
    zone_awareness_enabled   = var.instance_count > 1

    dynamic "zone_awareness_config" {
      for_each = var.instance_count > 1 ? [1] : []
      content {
        availability_zone_count = 3
      }
    }
  }

  ebs_options {
    ebs_enabled = var.ebs_enabled
    volume_type = "gp3"
    volume_size = var.volume_size
  }

  vpc_options {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_id != "" ? [var.security_group_id] : [aws_security_group.opensearch.id]
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  encrypt_at_rest {
    enabled    = true
    kms_key_id = var.kms_key_id != "" ? var.kms_key_id : null
  }

  node_to_node_encryption {
    enabled = true
  }


  advanced_security_options {
    enabled                        = true
    anonymous_auth_enabled         = false
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = "admin"
      master_user_password = random_password.opensearch_password.result
    }
  }

  advanced_options = {
    "rest.action.multi.allow_explicit_index" = "true"
    "indices.fielddata.cache.size"          = "20"
    "indices.query.bool.max_clause_count"   = "1024"
  }

  # CloudWatch 로그를 비활성화하여 권한 문제 해결
  # log_publishing_options {
  #   cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
  #   log_type                 = "INDEX_SLOW_LOGS"
  # }

  # log_publishing_options {
  #   cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
  #   log_type                 = "SEARCH_SLOW_LOGS"
  # }

  # log_publishing_options {
  #   cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
  #   log_type                 = "ES_APPLICATION_LOGS"
  # }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-opensearch"
  })

  depends_on = [aws_iam_service_linked_role.opensearch]
}

# OpenSearch Password
resource "random_password" "opensearch_password" {
  length  = 16
  special = true
}

# CloudWatch 로그를 비활성화하여 권한 문제 해결
# resource "aws_cloudwatch_log_group" "opensearch" {
#   name              = "/aws/opensearch/${var.project_name}-${var.environment}"
#   retention_in_days = 7
#   kms_key_id        = var.kms_key_id != "" ? var.kms_key_id : null

#   tags = merge(var.common_tags, {
#     Name = "${var.project_name}-${var.environment}-opensearch-logs"
#   })
# }

# IAM Service Linked Role for OpenSearch
resource "aws_iam_service_linked_role" "opensearch" {
  aws_service_name = "es.amazonaws.com"
}

# OpenSearch Access Policy - VPC 엔드포인트에서는 IP 기반 정책 사용 불가
# resource "aws_opensearch_domain_policy" "main" {
#   domain_name = aws_opensearch_domain.main.domain_name

#   access_policies = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Principal = {
#           AWS = "*"
#         }
#         Action   = "es:*"
#         Resource = "${aws_opensearch_domain.main.arn}/*"
#         Condition = {
#           IpAddress = {
#             "aws:SourceIp" = ["10.0.0.0/8"]
#           }
#         }
#       }
#     ]
#   })
# }

# OpenSearch Index Template - curl 오류로 인해 주석 처리
# resource "null_resource" "opensearch_index_template" {
#   depends_on = [aws_opensearch_domain.main]

#   provisioner "local-exec" {
#     command = <<-EOT
#       curl -X PUT "${aws_opensearch_domain.main.endpoint}/_index_template/enterprise-rag-template" \
#         -H "Content-Type: application/json" \
#         -u admin:${random_password.opensearch_password.result} \
#         -d '{
#           "index_patterns": ["${var.project_name}-*"],
#           "template": {
#             "settings": {
#               "number_of_shards": 1,
#               "number_of_replicas": 1,
#               "index": {
#                 "knn": true,
#                 "knn.algo_param.ef_search": 100
#               }
#             },
#             "mappings": {
#               "properties": {
#                 "content": {
#                   "type": "text",
#                   "analyzer": "korean"
#                 },
#                 "content_vector": {
#                   "type": "knn_vector",
#                   "dimension": 1536,
#                   "method": {
#                     "name": "hnsw",
#                     "space_type": "cosinesimil",
#                     "engine": "nmslib",
#                     "parameters": {
#                       "ef_construction": 128,
#                       "m": 24
#                     }
#                   }
#                 },
#                 "doc_id": {
#                   "type": "keyword"
#                 },
#                 "chunk_id": {
#                   "type": "keyword"
#                 },
#                 "metadata": {
#                   "type": "object"
#                 },
#                 "created_at": {
#                   "type": "date"
#                 },
#                 "updated_at": {
#                   "type": "date"
#                 }
#               }
#             }
#           }
#         }'
#     EOT
#   }

#   triggers = {
#     domain_endpoint = aws_opensearch_domain.main.endpoint
#   }
# }

# Outputs
output "domain_id" {
  description = "OpenSearch domain ID"
  value       = aws_opensearch_domain.main.domain_id
}

output "domain_name" {
  description = "OpenSearch domain name"
  value       = aws_opensearch_domain.main.domain_name
}

output "domain_arn" {
  description = "OpenSearch domain ARN"
  value       = aws_opensearch_domain.main.arn
}

output "endpoint" {
  description = "OpenSearch endpoint"
  value       = aws_opensearch_domain.main.endpoint
}

output "dashboard_endpoint" {
  description = "OpenSearch dashboard endpoint"
  value       = aws_opensearch_domain.main.dashboard_endpoint
}

output "kibana_endpoint" {
  description = "OpenSearch Dashboard endpoint"
  value       = aws_opensearch_domain.main.dashboard_endpoint
}

output "master_password" {
  description = "OpenSearch master password"
  value       = random_password.opensearch_password.result
  sensitive   = true
}

output "security_group_id" {
  description = "OpenSearch 보안 그룹 ID"
  value       = aws_security_group.opensearch.id
}
