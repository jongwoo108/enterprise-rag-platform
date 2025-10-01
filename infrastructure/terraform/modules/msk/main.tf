# MSK 모듈 - Kafka 클러스터 구성

# MSK 보안 그룹
resource "aws_security_group" "kafka" {
  name_prefix = "${var.project_name}-${var.environment}-kafka-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # VPC 내부에서만 접근
  }

  ingress {
    from_port   = 9094
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # TLS 포트
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-kafka-sg"
  })
}

# MSK Configuration
resource "aws_msk_configuration" "main" {
  kafka_versions = ["3.5.1"]
  name           = "${var.project_name}-${var.environment}-kafka-config"

  server_properties = <<PROPERTIES
auto.create.topics.enable=true
default.replication.factor=3
min.insync.replicas=2
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
log.retention.hours=168
log.segment.bytes=1073741824
log.cleanup.policy=delete
num.partitions=3
default.replication.factor=3
min.insync.replicas=2
unclean.leader.election.enable=false
delete.topic.enable=true
PROPERTIES
}

# MSK Cluster
resource "aws_msk_cluster" "main" {
  cluster_name           = "${var.project_name}-${var.environment}-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = var.number_of_broker_nodes
  configuration_info {
    arn      = aws_msk_configuration.main.arn
    revision = aws_msk_configuration.main.latest_revision
  }

  broker_node_group_info {
    instance_type   = var.instance_type
    client_subnets  = var.client_subnets
    security_groups = [aws_security_group.kafka.id]

    storage_info {
      ebs_storage_info {
        volume_size = var.storage_ebs_volume_size
        # provisioned_throughput은 일부 브로커 타입에서 지원되지 않음
        # provisioned_throughput {
        #   enabled           = true
        #   volume_throughput = 250
        # }
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  client_authentication {
    sasl {
      scram = true
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.kafka.name
      }
      firehose {
        enabled = false
      }
      s3 {
        enabled = false
      }
    }
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-kafka"
  })
}

# MSK SCRAM Secret
resource "aws_secretsmanager_secret" "kafka_sasl" {
  name = "${var.project_name}-${var.environment}-kafka-sasl-${formatdate("YYYYMMDDHHmm", timestamp())}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-kafka-sasl"
  })
}

resource "aws_secretsmanager_secret_version" "kafka_sasl" {
  secret_id = aws_secretsmanager_secret.kafka_sasl.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.kafka_password.result
  })
}

# Kafka Password
resource "random_password" "kafka_password" {
  length  = 32
  special = true
}

# ACM Certificate for Kafka
# resource "aws_acm_certificate" "kafka" {
#   domain_name       = "*.kafka.${var.project_name}-${var.environment}.local"
#   validation_method = "DNS"

#   lifecycle {
#     create_before_destroy = true
#   }

#   tags = merge(var.common_tags, {
#     Name = "${var.project_name}-${var.environment}-kafka-cert"
#   })
# }

# CloudWatch Log Group for Kafka
resource "aws_cloudwatch_log_group" "kafka" {
  name              = "/aws/kafka/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-kafka-logs"
  })
}

# MSK Connect Custom Plugin (선택사항)
# resource "aws_mskconnect_custom_plugin" "example" {
#   count = 0  # 필요시 활성화

#   name         = "${var.project_name}-${var.environment}-kafka-connect-plugin"
#   content_type = "ZIP"
#   location {
#     s3 {
#       bucket_arn = aws_s3_bucket.kafka_connect.arn
#       file_key   = aws_s3_object.kafka_connect_plugin.key
#     }
#   }

#   tags = merge(var.common_tags, {
#     Name = "${var.project_name}-${var.environment}-kafka-connect-plugin"
#   })
# }

# S3 Bucket for Kafka Connect plugins
resource "aws_s3_bucket" "kafka_connect" {
  count = 0  # 필요시 활성화

  bucket = "${var.project_name}-${var.environment}-kafka-connect-plugins"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-kafka-connect-bucket"
  })
}

resource "aws_s3_object" "kafka_connect_plugin" {
  count = 0  # 필요시 활성화

  bucket = aws_s3_bucket.kafka_connect[0].bucket
  key    = "plugins/kafka-connect-plugin.zip"
  source = "plugins/kafka-connect-plugin.zip"
}

# Outputs
output "cluster_arn" {
  description = "Kafka cluster ARN"
  value       = aws_msk_cluster.main.arn
}

output "cluster_name" {
  description = "Kafka cluster name"
  value       = aws_msk_cluster.main.cluster_name
}

output "bootstrap_brokers" {
  description = "Kafka bootstrap brokers"
  value       = aws_msk_cluster.main.bootstrap_brokers
}

output "bootstrap_brokers_tls" {
  description = "Kafka TLS bootstrap brokers"
  value       = aws_msk_cluster.main.bootstrap_brokers_tls
}

output "bootstrap_brokers_sasl_scram" {
  description = "Kafka SASL SCRAM bootstrap brokers"
  value       = aws_msk_cluster.main.bootstrap_brokers_sasl_scram
}

output "sasl_secret_arn" {
  description = "Kafka SASL secret ARN"
  value       = aws_secretsmanager_secret.kafka_sasl.arn
}

output "sasl_password" {
  description = "Kafka SASL password"
  value       = random_password.kafka_password.result
  sensitive   = true
}

output "security_group_id" {
  description = "Kafka 보안 그룹 ID"
  value       = aws_security_group.kafka.id
}
