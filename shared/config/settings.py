#!/usr/bin/env python3
"""
공통 설정 관리 모듈
모든 마이크로서비스에서 사용하는 설정을 중앙 관리
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field

class KafkaSettings(BaseSettings):
    """Kafka 관련 설정"""
    bootstrap_servers: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    
    # 토픽 이름들
    doc_ingestion_topic: str = "doc-ingestion"
    text_extracted_topic: str = "text-extracted"
    embeddings_generated_topic: str = "embeddings-generated"
    index_ready_topic: str = "index-ready"
    search_queries_topic: str = "search-queries"
    search_results_topic: str = "search-results"
    processing_errors_topic: str = "processing-errors"
    
    # Consumer 설정
    consumer_group_id_prefix: str = "enterprise-rag"
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    
    class Config:
        env_prefix = "KAFKA_"

class AWSSettings(BaseSettings):
    """AWS 관련 설정"""
    region: str = Field(default="us-east-1", env="AWS_REGION")
    
    # S3 설정
    s3_bucket_name: Optional[str] = Field(default=None, env="S3_BUCKET_NAME")
    
    # Bedrock 설정
    bedrock_region: str = Field(default="us-east-1", env="BEDROCK_REGION")
    embedding_model: str = Field(default="amazon.titan-embed-text-v1", env="EMBEDDING_MODEL")
    
    # OpenSearch 설정
    opensearch_endpoint: Optional[str] = Field(default=None, env="OPENSEARCH_ENDPOINT")
    opensearch_index: str = Field(default="enterprise-rag", env="OPENSEARCH_INDEX")
    
    # ElastiCache 설정
    redis_endpoint: Optional[str] = Field(default=None, env="REDIS_ENDPOINT")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    
    class Config:
        env_prefix = "AWS_"

class ProcessingSettings(BaseSettings):
    """문서 처리 관련 설정"""
    # 텍스트 청킹 설정
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    min_chunk_size: int = Field(default=50, env="MIN_CHUNK_SIZE")
    
    # 파일 크기 제한 (MB)
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    
    # 지원하는 파일 형식
    supported_extensions: List[str] = [
        "txt", "md", "markdown", 
        "pdf", "docx", "doc", 
        "html", "htm"
    ]
    
    # 임베딩 설정
    embedding_dimension: int = Field(default=1536, env="EMBEDDING_DIMENSION")
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    
    class Config:
        env_prefix = "PROCESSING_"

class ServiceSettings(BaseSettings):
    """마이크로서비스 공통 설정"""
    service_name: str = Field(default="unknown-service", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8080, env="PORT")
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        env="LOG_FORMAT"
    )
    
    # 헬스체크 설정
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # 메트릭 설정
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    
    class Config:
        env_prefix = "SERVICE_"

class MonitoringSettings(BaseSettings):
    """모니터링 및 관찰성 설정"""
    # Prometheus 설정
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # Jaeger 트레이싱 설정
    jaeger_enabled: bool = Field(default=False, env="JAEGER_ENABLED")
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    
    # 알림 설정
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    alert_threshold_error_rate: float = Field(default=0.05, env="ALERT_THRESHOLD_ERROR_RATE")
    alert_threshold_latency_ms: int = Field(default=5000, env="ALERT_THRESHOLD_LATENCY_MS")
    
    class Config:
        env_prefix = "MONITORING_"

class GlobalSettings:
    """전체 설정을 통합하는 클래스"""
    
    def __init__(self):
        self.kafka = KafkaSettings()
        self.aws = AWSSettings()
        self.processing = ProcessingSettings()
        self.service = ServiceSettings()
        self.monitoring = MonitoringSettings()
    
    def get_kafka_config(self) -> dict:
        """Kafka 클라이언트 설정 반환"""
        return {
            'bootstrap_servers': [self.kafka.bootstrap_servers],
            'auto_offset_reset': self.kafka.auto_offset_reset,
            'enable_auto_commit': self.kafka.enable_auto_commit,
        }
    
    def get_consumer_config(self, service_name: str) -> dict:
        """Kafka Consumer 설정 반환"""
        config = self.get_kafka_config()
        config['group_id'] = f"{self.kafka.consumer_group_id_prefix}-{service_name}"
        return config
    
    def get_producer_config(self) -> dict:
        """Kafka Producer 설정 반환"""
        return {
            'bootstrap_servers': [self.kafka.bootstrap_servers],
            'acks': 'all',  # 모든 복제본에서 확인
            'retries': 3,
            'batch_size': 16384,
            'linger_ms': 10,
            'buffer_memory': 33554432,
        }
    
    def is_file_supported(self, filename: str) -> bool:
        """파일이 지원되는 형식인지 확인"""
        extension = filename.lower().split('.')[-1]
        return extension in self.processing.supported_extensions
    
    def validate_file_size(self, size_bytes: int) -> bool:
        """파일 크기가 허용 범위인지 확인"""
        max_size_bytes = self.processing.max_file_size_mb * 1024 * 1024
        return size_bytes <= max_size_bytes

# 전역 설정 인스턴스
settings = GlobalSettings()

# 환경별 설정 오버라이드
def load_environment_config():
    """환경별 설정 로드"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        # 프로덕션 환경 설정
        settings.service.log_level = "WARNING"
        settings.monitoring.prometheus_enabled = True
        settings.monitoring.jaeger_enabled = True
        
    elif env == "staging":
        # 스테이징 환경 설정
        settings.service.log_level = "INFO"
        settings.monitoring.prometheus_enabled = True
        
    elif env == "development":
        # 개발 환경 설정
        settings.service.log_level = "DEBUG"
        settings.monitoring.prometheus_enabled = False
        
    return settings

# 설정 로드
settings = load_environment_config()

if __name__ == "__main__":
    # 설정 테스트
    print("=== Enterprise RAG Platform 설정 ===")
    print(f"환경: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Kafka 서버: {settings.kafka.bootstrap_servers}")
    print(f"AWS 리전: {settings.aws.region}")
    print(f"청크 크기: {settings.processing.chunk_size}")
    print(f"로그 레벨: {settings.service.log_level}")
    print(f"지원 파일 형식: {', '.join(settings.processing.supported_extensions)}")
