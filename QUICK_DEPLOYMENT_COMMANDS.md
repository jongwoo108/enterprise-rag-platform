# ⚡ 빠른 배포 명령어 모음

## 🧪 **로컬 테스트 (현재 완료됨)**

```bash
# 현재 디렉토리에서 테스트 스크립트 실행
python test_pipeline.py

# 개별 서비스 테스트
curl http://localhost:8081/health  # 텍스트 추출
curl http://localhost:8082/health  # 임베딩 생성  
curl http://localhost:8083/health  # 인덱싱 서비스
curl http://localhost:8084/health  # 검색 API

# 통합 검색 테스트
curl -X POST http://localhost:8084/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Enterprise RAG Platform", "top_k": 5}'
```

## 🚀 **클라우드 배포 (다음 단계)**

### 1단계: 사전 준비

```bash
# enterprise-rag-platform 디렉토리로 이동
cd C:\Users\ACER\enterprise-rag-platform

# 스크립트 실행 권한 부여 (Linux/Mac)
chmod +x deploy/deploy-infrastructure.sh
chmod +x deploy/deploy-services.sh

# AWS 자격 증명 확인
aws sts get-caller-identity
```

### 2단계: 인프라 배포 (15-20분 소요)

```bash
# 전체 AWS 인프라 자동 배포
./deploy/deploy-infrastructure.sh

# 수동 단계별 배포 (선택사항)
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### 3단계: 서비스 배포 (10-15분 소요)

```bash
# 마이크로서비스 자동 배포
./deploy/deploy-services.sh

# 배포 상태 확인
kubectl get pods -n enterprise-rag
kubectl get services -n enterprise-rag
```

### 4단계: 엔드포인트 확인

```bash
# 로드 밸런서 엔드포인트 조회
ALB_ENDPOINT=$(kubectl get ingress rag-platform-ingress -n enterprise-rag -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "배포 완료! 엔드포인트: http://$ALB_ENDPOINT"

# 서비스 헬스체크
curl http://$ALB_ENDPOINT/search/health
```

## 🔧 **주요 설정 변경**

### 비용 최적화 (개발 환경)

```bash
# infrastructure/terraform/variables.tf 수정
opensearch_instance_type = "t3.small.search"
opensearch_instance_count = 1
redis_node_type = "cache.t3.micro"
kafka_instance_type = "kafka.t3.small"
```

### 성능 최적화 (프로덕션 환경)

```bash
# infrastructure/terraform/variables.tf 수정
opensearch_instance_type = "m6g.large.search"
opensearch_instance_count = 3
redis_node_type = "cache.r6g.large"
kafka_instance_type = "kafka.m5.large"
```

## 📊 **모니터링 명령어**

```bash
# 실시간 Pod 상태 모니터링
kubectl get pods -n enterprise-rag -w

# 서비스 로그 확인
kubectl logs -f deployment/search-api-deployment -n enterprise-rag

# 리소스 사용량 확인
kubectl top pods -n enterprise-rag
kubectl top nodes
```

## 🚨 **트러블슈팅 명령어**

```bash
# Pod 문제 진단
kubectl describe pod <pod-name> -n enterprise-rag

# 서비스 연결 테스트
kubectl exec -it <pod-name> -n enterprise-rag -- curl http://service-name:port/health

# 로드 밸런서 상태 확인
kubectl describe ingress rag-platform-ingress -n enterprise-rag
```

## 🧹 **정리 명령어**

```bash
# 서비스만 삭제
kubectl delete namespace enterprise-rag

# 전체 인프라 삭제
cd infrastructure/terraform
terraform destroy

# 로컬 Docker 환경 정리
docker compose down
docker system prune -f
```

## 💡 **팁**

1. **첫 배포시**: 개발 환경으로 작은 인스턴스 타입 사용
2. **비용 절약**: 사용하지 않을 때는 `terraform destroy`로 리소스 삭제
3. **모니터링**: CloudWatch 대시보드에서 실시간 메트릭 확인
4. **보안**: 프로덕션 환경에서는 프라이빗 서브넷 사용

---

**🎯 현재 상태: 로컬 개발 환경 완료 ✅**  
**🚀 다음 단계: `./deploy/deploy-infrastructure.sh` 실행**
