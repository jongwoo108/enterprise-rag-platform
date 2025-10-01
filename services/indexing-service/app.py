#!/usr/bin/env python3
"""
인덱싱 서비스
임베딩 벡터를 OpenSearch에 저장하고 관리하는 마이크로서비스
"""

import os
import json
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import redis
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from confluent_kafka import Producer, Consumer, KafkaError
from opensearchpy import OpenSearch, RequestsHttpConnection
from loguru import logger

# 설정
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "localhost:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "enterprise-rag")
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "ragpassword")
SERVICE_NAME = "indexing-service"
SERVICE_VERSION = "1.0.0"

# FastAPI 앱 초기화
app = FastAPI(
    title="인덱싱 서비스",
    description="임베딩 벡터를 OpenSearch에 저장하고 관리하는 마이크로서비스",
    version=SERVICE_VERSION
)

# OpenSearch 클라이언트
opensearch_client = OpenSearch(
    hosts=[OPENSEARCH_ENDPOINT],
    http_compress=True,
    connection_class=RequestsHttpConnection,
    use_ssl=False,
    verify_certs=False,
    ssl_show_warn=False,
    timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

# Redis 클라이언트 (인덱싱 상태 관리용)
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

# 데이터 모델
class IndexingRequest(BaseModel):
    doc_id: str
    embeddings: List[Dict[str, Any]]
    metadata: Optional[Dict] = {}

class IndexingResponse(BaseModel):
    doc_id: str
    status: str
    indexed_chunks: int
    processing_time_ms: int
    message: str

class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    timestamp: str
    opensearch_status: str
    redis_status: str
    index_exists: bool

# 헬스체크 엔드포인트
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서비스 헬스체크"""
    # OpenSearch 연결 확인
    opensearch_status = "healthy"
    index_exists = False
    try:
        cluster_health = opensearch_client.cluster.health()
        if cluster_health['status'] in ['green', 'yellow']:
            opensearch_status = "healthy"
        else:
            opensearch_status = "degraded"
            
        # 인덱스 존재 확인
        index_exists = opensearch_client.indices.exists(index=OPENSEARCH_INDEX)
        
    except Exception as e:
        logger.error(f"OpenSearch 헬스체크 실패: {e}")
        opensearch_status = "unhealthy"
    
    # Redis 연결 확인
    redis_status = "healthy"
    try:
        redis_client.ping()
    except Exception:
        redis_status = "unhealthy"
    
    overall_status = "healthy"
    if opensearch_status != "healthy" or redis_status != "healthy":
        overall_status = "degraded"
    
    return HealthResponse(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        opensearch_status=opensearch_status,
        redis_status=redis_status,
        index_exists=index_exists
    )

# 메트릭 엔드포인트
@app.get("/metrics")
async def get_metrics():
    """서비스 메트릭"""
    try:
        # Redis에서 통계 정보 가져오기
        total_indexed = redis_client.get("total_documents_indexed") or 0
        total_chunks = redis_client.get("total_chunks_indexed") or 0
        indexing_errors = redis_client.get("indexing_errors") or 0
        
        # OpenSearch 인덱스 통계
        index_stats = {}
        try:
            if opensearch_client.indices.exists(index=OPENSEARCH_INDEX):
                stats = opensearch_client.indices.stats(index=OPENSEARCH_INDEX)
                index_stats = {
                    "document_count": stats['indices'][OPENSEARCH_INDEX]['total']['docs']['count'],
                    "index_size_bytes": stats['indices'][OPENSEARCH_INDEX]['total']['store']['size_in_bytes']
                }
        except Exception as e:
            logger.warning(f"인덱스 통계 조회 실패: {e}")
        
        return {
            "total_documents_indexed": int(total_indexed),
            "total_chunks_indexed": int(total_chunks),
            "indexing_errors": int(indexing_errors),
            "opensearch_index_stats": index_stats
        }
    except Exception as e:
        logger.error(f"메트릭 조회 오류: {e}")
        return {"error": "메트릭 조회 실패"}

async def ensure_index_exists():
    """OpenSearch 인덱스가 존재하는지 확인하고 없으면 생성"""
    try:
        if not opensearch_client.indices.exists(index=OPENSEARCH_INDEX):
            logger.info(f"인덱스 생성 중: {OPENSEARCH_INDEX}")
            
            # 인덱스 매핑 정의 (1536차원 벡터용)
            index_mapping = {
                "mappings": {
                    "properties": {
                        "doc_id": {
                            "type": "keyword"
                        },
                        "chunk_index": {
                            "type": "integer"
                        },
                        "chunk_text": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536
                        },
                        "metadata": {
                            "type": "object"
                        },
                        "indexed_at": {
                            "type": "date"
                        }
                    }
                },
                "settings": {
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "knn": True
                    }
                }
            }
            
            opensearch_client.indices.create(
                index=OPENSEARCH_INDEX,
                body=index_mapping
            )
            
            logger.info(f"인덱스 생성 완료: {OPENSEARCH_INDEX}")
        else:
            logger.info(f"인덱스 이미 존재: {OPENSEARCH_INDEX}")
            
    except Exception as e:
        logger.error(f"인덱스 생성 실패: {e}")
        raise

async def index_embeddings(doc_id: str, embeddings: List[Dict[str, Any]], metadata: Dict) -> int:
    """임베딩들을 OpenSearch에 인덱싱"""
    indexed_count = 0
    
    try:
        # 인덱스 존재 확인
        await ensure_index_exists()
        
        # 배치로 인덱싱
        bulk_body = []
        
        for embedding_data in embeddings:
            chunk_index = embedding_data.get("chunk_index", 0)
            chunk_text = embedding_data.get("chunk_text", "")
            embedding_vector = embedding_data.get("embedding", [])
            
            if not embedding_vector or len(embedding_vector) != 1536:
                logger.warning(f"잘못된 임베딩 차원: {len(embedding_vector) if embedding_vector else 0}")
                continue
            
            # 문서 ID 생성 (문서ID + 청크 인덱스)
            document_id = f"{doc_id}_chunk_{chunk_index}"
            
            # 인덱스 액션
            bulk_body.append({
                "index": {
                    "_index": OPENSEARCH_INDEX,
                    "_id": document_id
                }
            })
            
            # 문서 데이터
            bulk_body.append({
                "doc_id": doc_id,
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "embedding": embedding_vector,
                "metadata": metadata,
                "indexed_at": datetime.utcnow().isoformat()
            })
        
        if bulk_body:
            # 벌크 인덱싱 실행
            response = opensearch_client.bulk(
                body=bulk_body,
                refresh=True  # 즉시 검색 가능하도록
            )
            
            # 결과 확인
            if response.get("errors"):
                error_count = 0
                for item in response.get("items", []):
                    if "index" in item and item["index"].get("status", 200) >= 400:
                        error_count += 1
                        logger.error(f"인덱싱 오류: {item['index'].get('error')}")
                
                indexed_count = len(embeddings) - error_count
                logger.warning(f"부분 인덱싱 완료: {indexed_count}/{len(embeddings)}")
            else:
                indexed_count = len(embeddings)
                logger.info(f"모든 임베딩 인덱싱 완료: {indexed_count}개")
        
        # 통계 업데이트
        if indexed_count > 0:
            redis_client.incr("total_documents_indexed")
            redis_client.incrby("total_chunks_indexed", indexed_count)
        
        return indexed_count
        
    except Exception as e:
        logger.error(f"인덱싱 실패: {doc_id} - {e}")
        redis_client.incr("indexing_errors")
        return 0

# 메인 인덱싱 엔드포인트
@app.post("/index", response_model=IndexingResponse)
async def index_document(
    request: IndexingRequest,
    background_tasks: BackgroundTasks
):
    """문서의 임베딩들을 인덱싱"""
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"인덱싱 요청: {request.doc_id}, 임베딩 수: {len(request.embeddings)}")
        
        # 백그라운드에서 처리
        background_tasks.add_task(
            process_indexing_async,
            request.doc_id,
            request.embeddings,
            request.metadata
        )
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return IndexingResponse(
            doc_id=request.doc_id,
            status="processing",
            indexed_chunks=0,  # 백그라운드 처리로 인해 아직 알 수 없음
            processing_time_ms=processing_time,
            message="인덱싱이 백그라운드에서 시작되었습니다"
        )
        
    except Exception as e:
        logger.error(f"인덱싱 오류: {request.doc_id} - {str(e)}")
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return IndexingResponse(
            doc_id=request.doc_id,
            status="error",
            indexed_chunks=0,
            processing_time_ms=processing_time,
            message=f"처리 중 오류 발생: {str(e)}"
        )

async def process_indexing_async(
    doc_id: str,
    embeddings: List[Dict[str, Any]],
    metadata: Dict
):
    """비동기 인덱싱 처리"""
    try:
        start_time = time.time()
        
        # 임베딩 인덱싱
        indexed_count = await index_embeddings(doc_id, embeddings, metadata)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        if indexed_count > 0:
            # 성공 메시지를 Kafka로 전송
            success_message = {
                "doc_id": doc_id,
                "status": "indexed",
                "indexed_chunks": indexed_count,
                "total_chunks": len(embeddings),
                "success_rate": indexed_count / len(embeddings) * 100,
                "processing_time_ms": processing_time,
                "metadata": metadata,
                "indexed_at": datetime.utcnow().isoformat(),
                "service": SERVICE_NAME,
                "service_version": SERVICE_VERSION,
                "opensearch_index": OPENSEARCH_INDEX
            }
            
            # index-ready 토픽으로 전송
            kafka_producer.produce(
                topic='index-ready',
                key=doc_id,
                value=json.dumps(success_message, ensure_ascii=False)
            )
            
            kafka_producer.flush()
            
            logger.info(f"인덱싱 완료 및 Kafka 전송: {doc_id} - {indexed_count}개 청크")
            
        else:
            logger.error(f"인덱싱 실패: {doc_id}")
            
            # 에러를 Kafka 에러 토픽으로 전송
            error_message = {
                "doc_id": doc_id,
                "error": "모든 청크의 인덱싱 실패",
                "embeddings_count": len(embeddings),
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
        logger.error(f"인덱싱 비동기 처리 실패: {doc_id} - {str(e)}")

# Kafka 컨슈머 (임베딩 생성 완료 이벤트 수신)
async def kafka_consumer_task():
    """Kafka에서 임베딩 생성 완료 이벤트를 수신하여 인덱싱"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'indexing-service-group',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe(['embeddings-generated'])
    
    logger.info("Kafka 컨슈머 시작: embeddings-generated 토픽 수신 대기")
    
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
                embeddings = event_data.get('embeddings', [])
                metadata = event_data.get('metadata', {})
                
                logger.info(f"임베딩 생성 완료 이벤트 수신: {doc_id}, 임베딩 수: {len(embeddings)}")
                
                if embeddings:
                    # 비동기 인덱싱 처리
                    await process_indexing_async(doc_id, embeddings, metadata)
                else:
                    logger.warning(f"임베딩이 없음: {doc_id}")
                    
            except Exception as e:
                logger.error(f"Kafka 메시지 처리 오류: {str(e)}")
                
    finally:
        consumer.close()

# 인덱스 관리 엔드포인트
@app.post("/admin/recreate-index")
async def recreate_index():
    """인덱스 재생성 (관리자용)"""
    try:
        # 기존 인덱스 삭제
        if opensearch_client.indices.exists(index=OPENSEARCH_INDEX):
            opensearch_client.indices.delete(index=OPENSEARCH_INDEX)
            logger.info(f"기존 인덱스 삭제: {OPENSEARCH_INDEX}")
        
        # 새 인덱스 생성
        await ensure_index_exists()
        
        return {"message": f"인덱스 재생성 완료: {OPENSEARCH_INDEX}"}
        
    except Exception as e:
        logger.error(f"인덱스 재생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"인덱스 재생성 실패: {str(e)}")

@app.get("/admin/index-info")
async def get_index_info():
    """인덱스 정보 조회"""
    try:
        if not opensearch_client.indices.exists(index=OPENSEARCH_INDEX):
            return {"exists": False, "message": "인덱스가 존재하지 않습니다"}
        
        # 인덱스 매핑 및 설정 조회
        mapping = opensearch_client.indices.get_mapping(index=OPENSEARCH_INDEX)
        settings = opensearch_client.indices.get_settings(index=OPENSEARCH_INDEX)
        stats = opensearch_client.indices.stats(index=OPENSEARCH_INDEX)
        
        return {
            "exists": True,
            "mapping": mapping,
            "settings": settings,
            "stats": stats['indices'][OPENSEARCH_INDEX]['total']
        }
        
    except Exception as e:
        logger.error(f"인덱스 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"인덱스 정보 조회 실패: {str(e)}")

# 애플리케이션 시작 시 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} 시작")
    
    # OpenSearch 연결 테스트
    try:
        cluster_info = opensearch_client.info()
        logger.info(f"OpenSearch 연결 성공: {cluster_info['version']['number']}")
    except Exception as e:
        logger.error(f"OpenSearch 연결 실패: {e}")
    
    # Redis 연결 테스트
    try:
        redis_client.ping()
        logger.info("Redis 연결 성공")
    except Exception as e:
        logger.error(f"Redis 연결 실패: {e}")
    
    # 인덱스 생성 확인
    try:
        await ensure_index_exists()
    except Exception as e:
        logger.error(f"인덱스 초기화 실패: {e}")
    
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
