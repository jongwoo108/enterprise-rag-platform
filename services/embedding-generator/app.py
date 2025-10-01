#!/usr/bin/env python3
"""
임베딩 생성 마이크로서비스
텍스트 청크를 받아서 AWS Bedrock으로 임베딩을 생성하는 서비스
"""

import os
import json
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import boto3
import numpy as np
import redis
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from confluent_kafka import Producer, Consumer, KafkaError
from loguru import logger
from asyncio_throttle import Throttler

# 설정
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "ragpassword")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "amazon.titan-embed-text-v1")
SERVICE_NAME = "embedding-generator-service"
SERVICE_VERSION = "1.0.0"

# FastAPI 앱 초기화
app = FastAPI(
    title="임베딩 생성 서비스",
    description="텍스트 청크를 AWS Bedrock으로 임베딩 벡터로 변환하는 마이크로서비스",
    version=SERVICE_VERSION
)

# AWS 클라이언트
bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)

# Redis 클라이언트 (임베딩 캐싱용)
redis_client = redis.Redis(
    host=REDIS_ENDPOINT,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# Kafka Producer
kafka_producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': f'{SERVICE_NAME}-producer'
})

# Bedrock API 스로틀링 (분당 100회 제한)
bedrock_throttler = Throttler(rate_limit=100, period=60)

# 데이터 모델
class EmbeddingRequest(BaseModel):
    chunks: List[str]
    doc_id: str
    metadata: Optional[Dict] = {}

class EmbeddingResponse(BaseModel):
    doc_id: str
    status: str
    embeddings_count: int
    processing_time_ms: int
    message: str

class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    timestamp: str
    bedrock_status: str
    redis_status: str

# 헬스체크 엔드포인트
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서비스 헬스체크"""
    # Bedrock 연결 확인
    bedrock_status = "healthy"
    try:
        # 간단한 임베딩 테스트
        test_response = await generate_embedding("health check")
        if not test_response:
            bedrock_status = "unhealthy"
    except Exception:
        bedrock_status = "unhealthy"
    
    # Redis 연결 확인
    redis_status = "healthy"
    try:
        redis_client.ping()
    except Exception:
        redis_status = "unhealthy"
    
    overall_status = "healthy" if bedrock_status == "healthy" and redis_status == "healthy" else "degraded"
    
    return HealthResponse(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        bedrock_status=bedrock_status,
        redis_status=redis_status
    )

# 메트릭 엔드포인트
@app.get("/metrics")
async def get_metrics():
    """서비스 메트릭"""
    try:
        # Redis에서 통계 정보 가져오기
        total_embeddings = redis_client.get("total_embeddings") or 0
        cache_hits = redis_client.get("embedding_cache_hits") or 0
        cache_misses = redis_client.get("embedding_cache_misses") or 0
        
        cache_hit_rate = 0.0
        total_requests = int(cache_hits) + int(cache_misses)
        if total_requests > 0:
            cache_hit_rate = int(cache_hits) / total_requests * 100
        
        return {
            "total_embeddings_generated": int(total_embeddings),
            "cache_hit_rate_percent": f"{cache_hit_rate:.2f}",
            "cache_hits": int(cache_hits),
            "cache_misses": int(cache_misses),
            "bedrock_throttler_remaining": bedrock_throttler.remaining
        }
    except Exception as e:
        logger.error(f"메트릭 조회 오류: {e}")
        return {"error": "메트릭 조회 실패"}

async def generate_embedding(text: str) -> Optional[List[float]]:
    """단일 텍스트에 대한 임베딩 생성 (캐싱 포함)"""
    # 캐시 키 생성
    import hashlib
    cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
    
    # 캐시에서 확인
    try:
        cached_embedding = redis_client.get(cache_key)
        if cached_embedding:
            redis_client.incr("embedding_cache_hits")
            return json.loads(cached_embedding)
    except Exception as e:
        logger.warning(f"캐시 조회 실패: {e}")
    
    redis_client.incr("embedding_cache_misses")
    
    # Bedrock으로 임베딩 생성 (스로틀링 적용)
    async with bedrock_throttler:
        try:
            payload = {"inputText": text[:4000]}  # 토큰 제한
            
            response = bedrock.invoke_model(
                modelId=EMBEDDING_MODEL,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload).encode("utf-8"),
            )
            
            result = json.loads(response["body"].read())
            embedding = result.get("embedding") or result.get("vector")
            
            if not embedding:
                logger.error("임베딩 응답에서 벡터를 찾을 수 없음")
                return None
            
            # 차원 검증
            if len(embedding) != 1536:
                logger.error(f"예상 차원(1536)과 다름: {len(embedding)}")
                return None
            
            # 캐시에 저장 (24시간)
            try:
                redis_client.setex(cache_key, 86400, json.dumps(embedding))
            except Exception as e:
                logger.warning(f"캐시 저장 실패: {e}")
            
            # 통계 업데이트
            redis_client.incr("total_embeddings")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Bedrock 임베딩 생성 오류: {e}")
            return None

async def generate_embeddings_batch(chunks: List[str], doc_id: str) -> List[Dict[str, Any]]:
    """배치 임베딩 생성"""
    embeddings = []
    
    logger.info(f"배치 임베딩 생성 시작: {doc_id}, 청크 수: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        try:
            embedding = await generate_embedding(chunk.strip())
            
            if embedding:
                embeddings.append({
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "embedding": embedding,
                    "embedding_dimension": len(embedding)
                })
                logger.debug(f"임베딩 생성 완료: {doc_id} - 청크 {i+1}/{len(chunks)}")
            else:
                logger.error(f"임베딩 생성 실패: {doc_id} - 청크 {i+1}")
                
        except Exception as e:
            logger.error(f"청크 임베딩 처리 오류: {doc_id} - 청크 {i+1} - {e}")
    
    logger.info(f"배치 임베딩 완료: {doc_id}, 성공: {len(embeddings)}/{len(chunks)}")
    return embeddings

# 메인 임베딩 생성 엔드포인트
@app.post("/generate", response_model=EmbeddingResponse)
async def generate_embeddings_endpoint(
    request: EmbeddingRequest,
    background_tasks: BackgroundTasks
):
    """텍스트 청크들에 대한 임베딩 생성"""
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"임베딩 생성 요청: {request.doc_id}, 청크 수: {len(request.chunks)}")
        
        # 백그라운드에서 처리
        background_tasks.add_task(
            process_embeddings_async,
            request.chunks,
            request.doc_id,
            request.metadata
        )
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return EmbeddingResponse(
            doc_id=request.doc_id,
            status="processing",
            embeddings_count=0,  # 백그라운드 처리로 인해 아직 알 수 없음
            processing_time_ms=processing_time,
            message="임베딩 생성이 백그라운드에서 시작되었습니다"
        )
        
    except Exception as e:
        logger.error(f"임베딩 생성 오류: {request.doc_id} - {str(e)}")
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return EmbeddingResponse(
            doc_id=request.doc_id,
            status="error",
            embeddings_count=0,
            processing_time_ms=processing_time,
            message=f"처리 중 오류 발생: {str(e)}"
        )

async def process_embeddings_async(
    chunks: List[str],
    doc_id: str,
    metadata: Dict
):
    """비동기 임베딩 처리"""
    try:
        start_time = time.time()
        
        # 배치 임베딩 생성
        embeddings = await generate_embeddings_batch(chunks, doc_id)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        if embeddings:
            # Kafka로 결과 전송
            kafka_message = {
                "doc_id": doc_id,
                "embeddings": embeddings,
                "embeddings_count": len(embeddings),
                "total_chunks": len(chunks),
                "success_rate": len(embeddings) / len(chunks) * 100,
                "processing_time_ms": processing_time,
                "metadata": metadata,
                "generated_at": datetime.utcnow().isoformat(),
                "service": SERVICE_NAME,
                "service_version": SERVICE_VERSION,
                "embedding_model": EMBEDDING_MODEL,
                "embedding_dimension": 1536
            }
            
            # embeddings-generated 토픽으로 전송
            kafka_producer.produce(
                topic='embeddings-generated',
                key=doc_id,
                value=json.dumps(kafka_message, ensure_ascii=False)
            )
            
            kafka_producer.flush()
            
            logger.info(f"임베딩 완료 및 Kafka 전송: {doc_id} - {len(embeddings)}개 임베딩")
            
        else:
            logger.error(f"임베딩 생성 실패: {doc_id}")
            
            # 에러를 Kafka 에러 토픽으로 전송
            error_message = {
                "doc_id": doc_id,
                "error": "모든 청크의 임베딩 생성 실패",
                "chunks_count": len(chunks),
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
            
    except Exception as e:
        logger.error(f"임베딩 비동기 처리 실패: {doc_id} - {str(e)}")

# Kafka 컨슈머 (텍스트 추출 완료 이벤트 수신)
async def kafka_consumer_task():
    """Kafka에서 텍스트 추출 완료 이벤트를 수신하여 임베딩 생성"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'embedding-generator-service-group',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe(['text-extracted'])
    
    logger.info("Kafka 컨슈머 시작: text-extracted 토픽 수신 대기")
    
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
                chunks = event_data.get('chunks', [])
                metadata = event_data.get('metadata', {})
                
                logger.info(f"텍스트 추출 완료 이벤트 수신: {doc_id}, 청크 수: {len(chunks)}")
                
                if chunks:
                    # 비동기 임베딩 처리
                    await process_embeddings_async(chunks, doc_id, metadata)
                else:
                    logger.warning(f"청크가 없음: {doc_id}")
                    
            except Exception as e:
                logger.error(f"Kafka 메시지 처리 오류: {str(e)}")
                
    finally:
        consumer.close()

# 애플리케이션 시작 시 Kafka 컨슈머 시작
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} 시작")
    
    # Redis 연결 테스트
    try:
        redis_client.ping()
        logger.info("Redis 연결 성공")
    except Exception as e:
        logger.error(f"Redis 연결 실패: {e}")
    
    # Kafka 컨슈머를 백그라운드 태스크로 실행
    asyncio.create_task(kafka_consumer_task())

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(f"{SERVICE_NAME} 종료")
    kafka_producer.flush()
    try:
        redis_client.close()
    except Exception:
        pass

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )

