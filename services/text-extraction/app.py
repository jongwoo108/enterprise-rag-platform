#!/usr/bin/env python3
"""
텍스트 추출 마이크로서비스
S3 문서에서 텍스트를 추출하여 Kafka로 전송하는 서비스
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

import boto3
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from confluent_kafka import Producer, Consumer, KafkaError
from loguru import logger

# 기존 bedrock-test의 텍스트 추출 로직을 마이크로서비스로 재구성
from text_extractors import (
    extract_from_txt,
    extract_from_md, 
    extract_from_pdf,
    extract_from_docx,
    chunk_text
)

# 설정
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SERVICE_NAME = "text-extraction-service"
SERVICE_VERSION = "1.0.0"

# FastAPI 앱 초기화
app = FastAPI(
    title="텍스트 추출 서비스",
    description="S3 문서에서 텍스트를 추출하고 청킹하는 마이크로서비스",
    version=SERVICE_VERSION
)

# AWS 클라이언트
s3_client = boto3.client('s3', region_name=AWS_REGION)

# Kafka Producer
kafka_producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': f'{SERVICE_NAME}-producer'
})

# 데이터 모델
class DocumentProcessRequest(BaseModel):
    s3_bucket: str
    s3_key: str
    doc_id: str
    metadata: Optional[Dict] = {}

class TextExtractionResponse(BaseModel):
    doc_id: str
    status: str
    chunks_count: int
    processing_time_ms: int
    message: str

class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    timestamp: str

# 헬스체크 엔드포인트
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서비스 헬스체크"""
    return HealthResponse(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

# 메트릭 엔드포인트
@app.get("/metrics")
async def get_metrics():
    """서비스 메트릭 (Prometheus 형식)"""
    # TODO: 실제 메트릭 구현
    return {
        "processed_documents_total": 0,
        "processing_time_seconds": 0.0,
        "errors_total": 0
    }

# 메인 텍스트 추출 엔드포인트
@app.post("/extract", response_model=TextExtractionResponse)
async def extract_text(
    request: DocumentProcessRequest,
    background_tasks: BackgroundTasks
):
    """문서에서 텍스트 추출 및 Kafka 전송"""
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"텍스트 추출 시작: {request.doc_id}")
        
        # 백그라운드에서 처리
        background_tasks.add_task(
            process_document_async,
            request.s3_bucket,
            request.s3_key,
            request.doc_id,
            request.metadata
        )
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return TextExtractionResponse(
            doc_id=request.doc_id,
            status="processing",
            chunks_count=0,  # 백그라운드 처리로 인해 아직 알 수 없음
            processing_time_ms=processing_time,
            message="문서 처리가 백그라운드에서 시작되었습니다"
        )
        
    except Exception as e:
        logger.error(f"텍스트 추출 오류: {request.doc_id} - {str(e)}")
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return TextExtractionResponse(
            doc_id=request.doc_id,
            status="error",
            chunks_count=0,
            processing_time_ms=processing_time,
            message=f"처리 중 오류 발생: {str(e)}"
        )

async def process_document_async(
    s3_bucket: str,
    s3_key: str, 
    doc_id: str,
    metadata: Dict
):
    """비동기 문서 처리"""
    try:
        # 1. S3에서 문서 다운로드
        logger.info(f"S3에서 문서 다운로드: {s3_bucket}/{s3_key}")
        
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        file_content = response['Body'].read()
        
        # 2. 파일 확장자에 따른 텍스트 추출
        file_extension = s3_key.lower().split('.')[-1]
        
        if file_extension == 'txt':
            text = extract_from_txt(file_content)
        elif file_extension == 'md':
            text = extract_from_md(file_content)
        elif file_extension == 'pdf':
            text = extract_from_pdf(file_content)
        elif file_extension in ['docx', 'doc']:
            text = extract_from_docx(file_content)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_extension}")
        
        if not text.strip():
            raise ValueError("추출된 텍스트가 비어있습니다")
        
        # 3. 텍스트 청킹
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        
        logger.info(f"텍스트 추출 완료: {doc_id}, 청크 수: {len(chunks)}")
        
        # 4. Kafka로 결과 전송
        kafka_message = {
            "doc_id": doc_id,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "original_text": text,
            "chunks": chunks,
            "chunks_count": len(chunks),
            "metadata": metadata,
            "extracted_at": datetime.utcnow().isoformat(),
            "service": SERVICE_NAME,
            "service_version": SERVICE_VERSION
        }
        
        # text-extracted 토픽으로 전송
        kafka_producer.produce(
            topic='text-extracted',
            key=doc_id,
            value=json.dumps(kafka_message, ensure_ascii=False)
        )
        
        kafka_producer.flush()  # 즉시 전송 보장
        
        logger.info(f"Kafka 전송 완료: {doc_id}")
        
    except Exception as e:
        logger.error(f"문서 처리 실패: {doc_id} - {str(e)}")
        
        # 에러를 Kafka 에러 토픽으로 전송
        error_message = {
            "doc_id": doc_id,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "error": str(e),
            "error_at": datetime.utcnow().isoformat(),
            "service": SERVICE_NAME,
            "service_version": SERVICE_VERSION
        }
        
        kafka_producer.produce(
            topic='processing-errors',
            key=doc_id,
            value=json.dumps(error_message, ensure_ascii=False)
        )
        
        kafka_producer.flush()

# Kafka 이벤트 리스너 (S3 업로드 이벤트 수신)
async def kafka_consumer_task():
    """Kafka에서 문서 업로드 이벤트를 수신하여 처리"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'text-extraction-service-group',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe(['doc-ingestion'])
    
    logger.info("Kafka 컨슈머 시작: doc-ingestion 토픽 수신 대기")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                await asyncio.sleep(0.1)
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka 오류: {msg.error()}")
                    continue
            
            try:
                event_data = json.loads(msg.value().decode('utf-8'))
                doc_id = event_data.get('doc_id')
                s3_bucket = event_data.get('s3_bucket')
                s3_key = event_data.get('s3_key')
                metadata = event_data.get('metadata', {})
                
                logger.info(f"새 문서 처리 요청 수신: {doc_id}")
                
                # 비동기 처리
                await process_document_async(s3_bucket, s3_key, doc_id, metadata)
                
            except Exception as e:
                logger.error(f"Kafka 메시지 처리 오류: {str(e)}")
                
    finally:
        consumer.close()

# 애플리케이션 시작 시 Kafka 컨슈머 시작
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} 시작")
    
    # Kafka 컨슈머를 백그라운드 태스크로 실행
    asyncio.create_task(kafka_consumer_task())

@app.on_event("shutdown") 
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(f"{SERVICE_NAME} 종료")
    kafka_producer.close()

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
