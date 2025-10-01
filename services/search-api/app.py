#!/usr/bin/env python3
"""
검색 API 서비스
사용자 질의를 받아 벡터 검색을 수행하고 결과를 반환하는 마이크로서비스
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import boto3
import redis
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from opensearchpy import OpenSearch, RequestsHttpConnection
from loguru import logger

# 설정
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "localhost:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "enterprise-rag")
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "ragpassword")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "amazon.titan-embed-text-v1")
SERVICE_NAME = "search-api-service"
SERVICE_VERSION = "1.0.0"

# FastAPI 앱 초기화
app = FastAPI(
    title="검색 API 서비스",
    description="자연어 질의를 통한 의미 기반 문서 검색 서비스",
    version=SERVICE_VERSION
)

# CORS 설정 (웹 애플리케이션에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경용, 실제 운영에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# AWS Bedrock 클라이언트 (임베딩 생성용)
bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)

# Redis 클라이언트 (검색 결과 캐싱용)
redis_client = redis.Redis(
    host=REDIS_ENDPOINT,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# 데이터 모델
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.5
    include_metadata: Optional[bool] = True

class SearchResult(BaseModel):
    doc_id: str
    chunk_index: int
    chunk_text: str
    score: float
    metadata: Optional[Dict] = {}

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: int
    cached: bool

class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    timestamp: str
    opensearch_status: str
    redis_status: str
    bedrock_status: str
    index_exists: bool
    index_doc_count: int

# 헬스체크 엔드포인트
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서비스 헬스체크"""
    # OpenSearch 연결 및 인덱스 확인
    opensearch_status = "healthy"
    index_exists = False
    index_doc_count = 0
    
    try:
        cluster_health = opensearch_client.cluster.health()
        if cluster_health['status'] in ['green', 'yellow']:
            opensearch_status = "healthy"
        else:
            opensearch_status = "degraded"
            
        # 인덱스 존재 및 문서 수 확인
        if opensearch_client.indices.exists(index=OPENSEARCH_INDEX):
            index_exists = True
            stats = opensearch_client.indices.stats(index=OPENSEARCH_INDEX)
            index_doc_count = stats['indices'][OPENSEARCH_INDEX]['total']['docs']['count']
            
    except Exception as e:
        logger.error(f"OpenSearch 헬스체크 실패: {e}")
        opensearch_status = "unhealthy"
    
    # Redis 연결 확인
    redis_status = "healthy"
    try:
        redis_client.ping()
    except Exception:
        redis_status = "unhealthy"
    
    # Bedrock 연결 확인
    bedrock_status = "healthy"
    try:
        # 간단한 임베딩 테스트
        test_embedding = await generate_embedding("health check")
        if not test_embedding:
            bedrock_status = "unhealthy"
    except Exception:
        bedrock_status = "unhealthy"
    
    overall_status = "healthy"
    if opensearch_status != "healthy" or redis_status != "healthy" or bedrock_status != "healthy":
        overall_status = "degraded"
    
    return HealthResponse(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        opensearch_status=opensearch_status,
        redis_status=redis_status,
        bedrock_status=bedrock_status,
        index_exists=index_exists,
        index_doc_count=index_doc_count
    )

# 메트릭 엔드포인트
@app.get("/metrics")
async def get_metrics():
    """서비스 메트릭"""
    try:
        # Redis에서 통계 정보 가져오기
        total_searches = redis_client.get("total_searches") or 0
        cache_hits = redis_client.get("search_cache_hits") or 0
        cache_misses = redis_client.get("search_cache_misses") or 0
        avg_response_time = redis_client.get("avg_response_time_ms") or 0
        
        cache_hit_rate = 0.0
        total_requests = int(cache_hits) + int(cache_misses)
        if total_requests > 0:
            cache_hit_rate = int(cache_hits) / total_requests * 100
        
        return {
            "total_searches": int(total_searches),
            "cache_hit_rate_percent": f"{cache_hit_rate:.2f}",
            "cache_hits": int(cache_hits),
            "cache_misses": int(cache_misses),
            "avg_response_time_ms": float(avg_response_time)
        }
    except Exception as e:
        logger.error(f"메트릭 조회 오류: {e}")
        return {"error": "메트릭 조회 실패"}

async def generate_embedding(text: str) -> Optional[List[float]]:
    """텍스트에 대한 임베딩 생성 (캐싱 포함)"""
    # 캐시 키 생성
    cache_key = f"query_embedding:{hashlib.md5(text.encode()).hexdigest()}"
    
    # 캐시에서 확인
    try:
        cached_embedding = redis_client.get(cache_key)
        if cached_embedding:
            return json.loads(cached_embedding)
    except Exception as e:
        logger.warning(f"임베딩 캐시 조회 실패: {e}")
    
    # 개발 환경에서는 더미 임베딩 생성 (AWS 자격 증명 없이 테스트 가능)
    dev_mode = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    if dev_mode:
        logger.info("개발 모드: 더미 임베딩 생성")
        # 텍스트 기반으로 일관된 더미 임베딩 생성
        import random
        random.seed(hash(text) % (2**32))  # 텍스트 기반 시드로 일관성 보장
        dummy_embedding = [random.uniform(-1, 1) for _ in range(1536)]
        
        # 캐시에 저장
        try:
            redis_client.setex(cache_key, 3600, json.dumps(dummy_embedding))
        except Exception as e:
            logger.warning(f"임베딩 캐시 저장 실패: {e}")
        
        return dummy_embedding
    
    # 프로덕션 환경에서는 Bedrock 사용
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
        
        if not embedding or len(embedding) != 1536:
            logger.error(f"임베딩 생성 실패 또는 잘못된 차원: {len(embedding) if embedding else 0}")
            return None
        
        # 캐시에 저장 (1시간)
        try:
            redis_client.setex(cache_key, 3600, json.dumps(embedding))
        except Exception as e:
            logger.warning(f"임베딩 캐시 저장 실패: {e}")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Bedrock 임베딩 생성 오류: {e}")
        # Bedrock 실패 시에도 더미 임베딩 반환 (개발 환경)
        if dev_mode:
            logger.warning("Bedrock 실패, 더미 임베딩으로 대체")
            import random
            random.seed(hash(text) % (2**32))
            return [random.uniform(-1, 1) for _ in range(1536)]
        return None

async def search_similar_documents(
    query_embedding: List[float],
    top_k: int = 5,
    min_score: float = 0.5
) -> List[Dict[str, Any]]:
    """벡터 유사도 검색"""
    try:
        # KNN 검색 쿼리
        search_body = {
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k * 2  # 더 많이 가져와서 필터링
                    }
                }
            },
            "_source": ["doc_id", "chunk_index", "chunk_text", "metadata", "indexed_at"],
            "size": top_k * 2
        }
        
        # OpenSearch에서 검색 수행
        response = opensearch_client.search(
            index=OPENSEARCH_INDEX,
            body=search_body
        )
        
        # 결과 처리
        results = []
        for hit in response.get("hits", {}).get("hits", []):
            score = hit["_score"]
            
            # 최소 점수 필터링
            if score >= min_score:
                source = hit["_source"]
                results.append({
                    "doc_id": source.get("doc_id", ""),
                    "chunk_index": source.get("chunk_index", 0),
                    "chunk_text": source.get("chunk_text", ""),
                    "score": float(score),
                    "metadata": source.get("metadata", {}),
                    "indexed_at": source.get("indexed_at", "")
                })
        
        # 점수 순으로 정렬하고 상위 k개만 반환
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        logger.error(f"벡터 검색 실패: {e}")
        return []

# 메인 검색 엔드포인트
@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """문서 검색"""
    start_time = time.time()
    
    try:
        logger.info(f"검색 요청: '{request.query}', top_k: {request.top_k}")
        
        # 캐시 키 생성
        cache_key = f"search_result:{hashlib.md5(f'{request.query}_{request.top_k}_{request.min_score}'.encode()).hexdigest()}"
        
        # 캐시에서 확인
        cached_result = None
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                cached_result = json.loads(cached_data)
                redis_client.incr("search_cache_hits")
                
                processing_time = int((time.time() - start_time) * 1000)
                
                return SearchResponse(
                    query=request.query,
                    results=[SearchResult(**result) for result in cached_result["results"]],
                    total_results=cached_result["total_results"],
                    processing_time_ms=processing_time,
                    cached=True
                )
        except Exception as e:
            logger.warning(f"검색 캐시 조회 실패: {e}")
        
        redis_client.incr("search_cache_misses")
        
        # 1. 질의 임베딩 생성
        query_embedding = await generate_embedding(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="질의 임베딩 생성 실패")
        
        # 2. 벡터 검색 수행
        search_results = await search_similar_documents(
            query_embedding,
            request.top_k,
            request.min_score
        )
        
        # 3. 결과 구성
        results = []
        for result in search_results:
            search_result = SearchResult(
                doc_id=result["doc_id"],
                chunk_index=result["chunk_index"],
                chunk_text=result["chunk_text"],
                score=result["score"],
                metadata=result["metadata"] if request.include_metadata else {}
            )
            results.append(search_result)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # 4. 응답 생성
        response = SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time,
            cached=False
        )
        
        # 5. 결과 캐싱 (성공한 경우만)
        if results:
            try:
                cache_data = {
                    "results": [result.dict() for result in results],
                    "total_results": len(results)
                }
                redis_client.setex(cache_key, 1800, json.dumps(cache_data))  # 30분 캐시
            except Exception as e:
                logger.warning(f"검색 결과 캐시 저장 실패: {e}")
        
        # 6. 통계 업데이트
        redis_client.incr("total_searches")
        
        # 평균 응답 시간 업데이트
        try:
            current_avg = float(redis_client.get("avg_response_time_ms") or 0)
            total_searches = int(redis_client.get("total_searches") or 1)
            new_avg = (current_avg * (total_searches - 1) + processing_time) / total_searches
            redis_client.set("avg_response_time_ms", f"{new_avg:.2f}")
        except Exception as e:
            logger.warning(f"평균 응답 시간 업데이트 실패: {e}")
        
        logger.info(f"검색 완료: '{request.query}' - {len(results)}개 결과, {processing_time}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"검색 오류: '{request.query}' - {str(e)}")
        raise HTTPException(status_code=500, detail=f"검색 처리 중 오류 발생: {str(e)}")

# GET 방식 검색 엔드포인트 (간단한 사용을 위해)
@app.get("/search", response_model=SearchResponse)
async def search_documents_get(
    q: str = Query(..., description="검색 질의"),
    top_k: int = Query(5, description="반환할 결과 수", ge=1, le=20),
    min_score: float = Query(0.5, description="최소 유사도 점수", ge=0.0, le=1.0),
    include_metadata: bool = Query(True, description="메타데이터 포함 여부")
):
    """GET 방식 문서 검색"""
    request = SearchRequest(
        query=q,
        top_k=top_k,
        min_score=min_score,
        include_metadata=include_metadata
    )
    return await search_documents(request)

# 추천 검색어 엔드포인트
@app.get("/suggestions")
async def get_search_suggestions(
    prefix: str = Query(..., description="검색어 접두사", min_length=2)
):
    """검색어 자동완성 제안"""
    try:
        # Redis에서 최근 검색어 조회
        pattern = f"search_result:*{prefix.lower()}*"
        keys = redis_client.keys(pattern)
        
        # 최근 검색어 추출 (간단한 구현)
        suggestions = []
        for key in keys[:10]:  # 최대 10개
            # 실제 구현에서는 더 정교한 로직 필요
            suggestions.append(f"관련 검색어 {len(suggestions) + 1}")
        
        return {
            "prefix": prefix,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"검색어 제안 오류: {e}")
        return {
            "prefix": prefix,
            "suggestions": []
        }

# 인기 검색어 엔드포인트
@app.get("/popular")
async def get_popular_queries():
    """인기 검색어 조회"""
    try:
        # 실제 구현에서는 Redis sorted set 등을 사용하여 검색 빈도 추적
        popular_queries = [
            {"query": "AWS Lambda", "count": 15},
            {"query": "서버리스 아키텍처", "count": 12},
            {"query": "벡터 검색", "count": 8},
            {"query": "임베딩", "count": 6},
            {"query": "OpenSearch", "count": 5}
        ]
        
        return {
            "popular_queries": popular_queries,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"인기 검색어 조회 오류: {e}")
        return {
            "popular_queries": [],
            "updated_at": datetime.utcnow().isoformat()
        }

# 애플리케이션 시작 시 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} 시작")
    
    # OpenSearch 연결 테스트
    try:
        cluster_info = opensearch_client.info()
        logger.info(f"OpenSearch 연결 성공: {cluster_info['version']['number']}")
        
        # 인덱스 존재 확인
        if opensearch_client.indices.exists(index=OPENSEARCH_INDEX):
            stats = opensearch_client.indices.stats(index=OPENSEARCH_INDEX)
            doc_count = stats['indices'][OPENSEARCH_INDEX]['total']['docs']['count']
            logger.info(f"인덱스 '{OPENSEARCH_INDEX}' 확인: {doc_count}개 문서")
        else:
            logger.warning(f"인덱스 '{OPENSEARCH_INDEX}'가 존재하지 않습니다")
            
    except Exception as e:
        logger.error(f"OpenSearch 연결 실패: {e}")
    
    # Redis 연결 테스트
    try:
        redis_client.ping()
        logger.info("Redis 연결 성공")
    except Exception as e:
        logger.error(f"Redis 연결 실패: {e}")
    
    # Bedrock 연결 테스트
    try:
        test_embedding = await generate_embedding("startup test")
        if test_embedding:
            logger.info("Bedrock 연결 성공")
        else:
            logger.warning("Bedrock 연결 실패")
    except Exception as e:
        logger.error(f"Bedrock 연결 실패: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(f"{SERVICE_NAME} 종료")
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
