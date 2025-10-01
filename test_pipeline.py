#!/usr/bin/env python3
"""
Enterprise RAG Platform - 전체 파이프라인 테스트
간단한 end-to-end 테스트로 모든 서비스 연동 확인
"""

import requests
import json
import time
import sys

# 서비스 엔드포인트
SERVICES = {
    "text_extraction": "http://localhost:8081",
    "embedding_generator": "http://localhost:8082", 
    "indexing_service": "http://localhost:8083",
    "search_api": "http://localhost:8084"
}

def test_health_checks():
    """모든 서비스 헬스체크"""
    print("🏥 서비스 헬스체크 시작...")
    
    for service_name, base_url in SERVICES.items():
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: 정상")
            else:
                print(f"❌ {service_name}: 비정상 ({response.status_code})")
                return False
        except Exception as e:
            print(f"❌ {service_name}: 연결 실패 - {e}")
            return False
    
    print("🎉 모든 서비스 정상 작동!")
    return True

def test_text_extraction():
    """텍스트 추출 서비스 테스트"""
    print("\n📝 텍스트 추출 테스트...")
    
    test_data = {
        "bucket": "test-bucket",
        "key": "test-document.txt", 
        "content": "이것은 테스트 문서입니다. RAG 시스템이 잘 작동하는지 확인해보겠습니다."
    }
    
    try:
        response = requests.post(
            f"{SERVICES['text_extraction']}/process-document",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 텍스트 추출 성공: {len(result.get('chunks', []))} 청크 생성")
            return True
        else:
            print(f"❌ 텍스트 추출 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 텍스트 추출 오류: {e}")
        return False

def test_embedding_generation():
    """임베딩 생성 서비스 테스트"""
    print("\n🧠 임베딩 생성 테스트...")
    
    test_data = {
        "text": "RAG 시스템 테스트용 텍스트입니다.",
        "chunk_id": "test-chunk-001"
    }
    
    try:
        response = requests.post(
            f"{SERVICES['embedding_generator']}/generate-embedding",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            embedding = result.get('embedding', [])
            print(f"✅ 임베딩 생성 성공: {len(embedding)}차원 벡터")
            return True
        else:
            print(f"❌ 임베딩 생성 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 임베딩 생성 오류: {e}")
        return False

def test_indexing_service():
    """인덱싱 서비스 테스트"""
    print("\n📚 인덱싱 서비스 테스트...")
    
    # 인덱스 상태 확인
    try:
        response = requests.get(f"{SERVICES['indexing_service']}/admin/index-status")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 인덱스 상태: {result.get('status', 'unknown')}")
            print(f"   문서 수: {result.get('document_count', 0)}")
            return True
        else:
            print(f"❌ 인덱스 상태 확인 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 인덱싱 서비스 오류: {e}")
        return False

def test_search_api():
    """검색 API 테스트"""
    print("\n🔍 검색 API 테스트...")
    
    test_queries = [
        "RAG 시스템",
        "테스트 문서", 
        "인공지능"
    ]
    
    for query in test_queries:
        try:
            response = requests.post(
                f"{SERVICES['search_api']}/search",
                json={"query": query, "top_k": 3},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                results = result.get('results', [])
                print(f"✅ 검색 '{query}': {len(results)}개 결과")
            else:
                print(f"❌ 검색 '{query}' 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            return False
    
    return True

def run_full_pipeline_test():
    """전체 파이프라인 통합 테스트"""
    print("\n🚀 전체 파이프라인 통합 테스트...")
    
    # 1. 문서 처리 (텍스트 추출 → 임베딩 → 인덱싱)
    test_doc = {
        "bucket": "integration-test",
        "key": "test-doc.txt",
        "content": """
        Enterprise RAG Platform 통합 테스트 문서입니다.
        이 시스템은 AWS Bedrock, OpenSearch, Kafka, Redis를 활용합니다.
        마이크로서비스 아키텍처로 구성되어 있으며 Docker로 컨테이너화되었습니다.
        """
    }
    
    print("📄 문서 처리 시작...")
    try:
        # 문서 처리 요청
        response = requests.post(
            f"{SERVICES['text_extraction']}/process-document",
            json=test_doc,
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ 문서 처리 완료")
        else:
            print(f"❌ 문서 처리 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 문서 처리 오류: {e}")
        return False
    
    # 2. 잠시 대기 (비동기 처리 완료 대기)
    print("⏳ 처리 완료 대기 중...")
    time.sleep(5)
    
    # 3. 검색 테스트
    print("🔍 검색 테스트...")
    try:
        response = requests.post(
            f"{SERVICES['search_api']}/search",
            json={"query": "Enterprise RAG Platform", "top_k": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            results = result.get('results', [])
            print(f"✅ 통합 검색 성공: {len(results)}개 결과 반환")
            
            # 결과 상세 출력
            for i, doc in enumerate(results[:2], 1):
                score = doc.get('score', 0)
                content = doc.get('content', '')[:100]
                print(f"   {i}. 점수: {score:.4f}, 내용: {content}...")
            
            return True
        else:
            print(f"❌ 통합 검색 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 통합 검색 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🚀 Enterprise RAG Platform 통합 테스트")
    print("=" * 60)
    
    # 개별 서비스 테스트
    tests = [
        ("헬스체크", test_health_checks),
        ("텍스트 추출", test_text_extraction), 
        ("임베딩 생성", test_embedding_generation),
        ("인덱싱 서비스", test_indexing_service),
        ("검색 API", test_search_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 테스트 실패!")
    
    # 통합 테스트
    print(f"\n{'='*20} 통합 테스트 {'='*20}")
    if run_full_pipeline_test():
        passed += 1
    total += 1
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"✅ 통과: {passed}/{total}")
    print(f"❌ 실패: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 시스템이 정상 작동합니다!")
        return True
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패. 문제를 확인해주세요.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
