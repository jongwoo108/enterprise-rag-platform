# Enterprise RAG Platform

> **Enterprise-grade distributed RAG system with Kubernetes, Kafka, Airflow, and AWS services for large-scale document processing and semantic search**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-1.28+-blue.svg)](https://kubernetes.io/)

---

## 프로젝트 개요

이 프로젝트는 **서버리스 RAG 프로토타입**에서 **엔터프라이즈급 분산 시스템**으로 진화한 대규모 지식 관리 플랫폼입니다.

### 주요 목표
- **100배 처리량 향상**: 1,000 → 100,000+ 문서/시간
- **무제한 확장성**: 수평적 마이크로서비스 아키텍처
- **실시간 스트리밍**: Kafka 기반 연속 데이터 처리
- **엔터프라이즈 안정성**: 99.99% 가용성 목표

### 관련 프로젝트
- **프로토타입**: [bedrock-test](https://github.com/jongwoo108/bedrock-test) - 서버리스 RAG 시스템 (완성)

---

## 아키텍처

### 시스템 다이어그램
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           데이터 수집 레이어                                  │
│  S3 Buckets  │  Database  │  APIs  │  File Systems  │  External Sources    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Apache Kafka (MSK) - 메시징 레이어                       │
│  doc-ingestion → text-extract → embedding → index-ready                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│            Apache Airflow - 워크플로우 오케스트레이션                        │
│  배치 처리 DAG  │  실시간 스트림 DAG  │  인덱스 관리 DAG                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          컴퓨팅 레이어                                        │
│  ┌─────────────────────┐              ┌─────────────────────────────────┐   │
│  │    AWS Batch        │              │         Amazon EKS              │   │
│  │  대용량 배치처리     │              │      마이크로서비스 클러스터      │   │
│  └─────────────────────┘              └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      저장 및 캐싱 레이어                                      │
│  ┌─────────────────────┐              ┌─────────────────────────────────┐   │
│  │  ElastiCache Redis  │              │      OpenSearch Cluster         │   │
│  │    고성능 캐싱       │              │        벡터 검색 엔진            │   │
│  └─────────────────────┘              └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🛠️ 기술 스택
- **컨테이너 오케스트레이션**: Amazon EKS (Kubernetes)
- **메시지 스트리밍**: Amazon MSK (Apache Kafka)
- **워크플로우 관리**: Apache Airflow
- **배치 처리**: AWS Batch
- **캐싱**: Amazon ElastiCache (Redis)
- **벡터 검색**: Amazon OpenSearch
- **AI 모델**: Amazon Bedrock (Titan Embeddings)
- **스토리지**: Amazon S3
- **언어**: Python 3.12+

---

## 프로젝트 구조

```
enterprise-rag-platform/
├── 📁 infrastructure/           # 인프라 코드
│   ├── terraform/              # Terraform IaC
│   ├── helm-charts/            # Kubernetes Helm 차트
│   └── aws-batch/              # AWS Batch 설정
│
├── 📁 services/                # 마이크로서비스들
│   ├── text-extraction/        # 텍스트 추출 서비스
│   ├── embedding-generator/    # 임베딩 생성 서비스
│   ├── indexing-service/       # 인덱싱 서비스
│   ├── search-api/             # 검색 API 서비스
│   └── monitoring/             # 모니터링 서비스
│
├── 📁 workflows/               # Airflow DAGs
│   ├── batch-processing/       # 배치 처리 워크플로우
│   ├── real-time-streaming/    # 실시간 스트림 처리
│   └── maintenance/            # 유지보수 작업
│
├── 📁 kafka/                   # Kafka 설정
│   ├── topics/                 # 토픽 정의
│   ├── schemas/                # 스키마 레지스트리
│   └── connectors/             # Kafka Connect
│
├── 📁 shared/                  # 공통 코드
│   ├── models/                 # 데이터 모델
│   ├── utils/                  # 유틸리티 함수
│   └── config/                 # 설정 관리
│
└── 📁 deployment/              # 배포 관련
    ├── ci-cd/                  # CI/CD 파이프라인
    ├── environments/           # 환경별 설정
    └── scripts/                # 배포 스크립트
```

---

## 빠른 시작

### 전제 조건
- AWS CLI 설정 완료
- kubectl 및 helm 설치
- Docker 및 Docker Compose
- Python 3.12+
- Terraform (선택사항)

### 1. 리포지토리 클론
```bash
git clone https://github.com/jongwoo108/enterprise-rag-platform.git
cd enterprise-rag-platform
```

### 2. 개발 환경 설정
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 인프라 배포 (개발 환경)
```bash
# EKS 클러스터 생성
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# Helm 차트 배포
cd ../helm-charts
helm install rag-platform ./rag-platform
```

---

## 성능 목표

| 지표 | 현재 (서버리스) | 목표 (엔터프라이즈) | 개선율 |
|------|----------------|---------------------|--------|
| **동시 처리량** | 1,000 문서/시간 | 100,000+ 문서/시간 | **100배** |
| **검색 응답** | 200ms | 50ms (캐시 시) | **4배** |
| **가용성** | 99.9% | 99.99% | **10배** |
| **확장성** | 제한적 | 무제한 수평 확장 | **무제한** |

---

## 개발 로드맵

### Phase 1: 인프라 구축 (진행 중)
- [x] 프로젝트 구조 생성
- [ ] EKS 클러스터 설정
- [ ] MSK (Kafka) 클러스터 구성
- [ ] ElastiCache Redis 설정

### Phase 2: 핵심 서비스 개발
- [ ] 텍스트 추출 마이크로서비스
- [ ] 임베딩 생성 서비스
- [ ] 인덱싱 서비스
- [ ] 검색 API 서비스

### Phase 3: 고급 기능
- [ ] Airflow 워크플로우 구성
- [ ] AWS Batch 통합
- [ ] 모니터링 및 알림 시스템
- [ ] CI/CD 파이프라인 구축

---

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 연락처

- **프로젝트 링크**: [https://github.com/jongwoo108/enterprise-rag-platform](https://github.com/jongwoo108/enterprise-rag-platform)
- **관련 프로젝트**: [bedrock-test (서버리스 프로토타입)](https://github.com/jongwoo108/bedrock-test)

---

## 감사의 말

이 프로젝트는 [bedrock-test](https://github.com/jongwoo108/bedrock-test)에서 검증된 서버리스 RAG 시스템을 기반으로 구축되었습니다.
