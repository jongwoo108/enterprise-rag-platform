# 🚀 Enterprise RAG Platform - 클라우드 배포 가이드

## 📋 개요

이 가이드는 Enterprise RAG Platform을 AWS 클라우드에 배포하는 전체 과정을 다룹니다.

## 🏗️ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Application Load Balancer                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    EKS Cluster                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │Text Extract │ │Embedding Gen│ │Indexing Svc │ │Search  ││
│  │   Service   │ │   Service   │ │   Service   │ │API Svc ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Managed Services                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │     MSK     │ │ElastiCache  │ │ OpenSearch  │ │   S3   ││
│  │   (Kafka)   │ │  (Redis)    │ │             │ │        ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 사전 준비

### 1. 필수 도구 설치

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 2. AWS 자격 증명 설정

```bash
aws configure
# AWS Access Key ID: [YOUR_ACCESS_KEY]
# AWS Secret Access Key: [YOUR_SECRET_KEY]
# Default region name: us-east-1
# Default output format: json
```

### 3. 권한 확인

필요한 AWS IAM 권한:
- EC2 관리 권한
- EKS 관리 권한
- VPC 관리 권한
- IAM 역할 생성 권한
- OpenSearch 관리 권한
- ElastiCache 관리 권한
- MSK 관리 권한
- S3 관리 권한
- CloudWatch 관리 권한

## 🚀 배포 과정

### 1단계: 인프라 배포

```bash
# 스크립트 실행 권한 부여
chmod +x deploy/deploy-infrastructure.sh

# 인프라 배포 실행
./deploy/deploy-infrastructure.sh
```

**배포되는 리소스:**
- VPC 및 서브넷
- EKS 클러스터
- OpenSearch 도메인
- ElastiCache Redis 클러스터
- MSK Kafka 클러스터
- S3 버킷
- 보안 그룹
- IAM 역할
- CloudWatch 로그 그룹

### 2단계: 서비스 배포

```bash
# 스크립트 실행 권한 부여
chmod +x deploy/deploy-services.sh

# 서비스 배포 실행
./deploy/deploy-services.sh
```

**배포되는 서비스:**
- Text Extraction Service
- Embedding Generator Service
- Indexing Service
- Search API Service
- Application Load Balancer
- Ingress Controller

## 📊 배포 후 확인

### 1. 클러스터 상태 확인

```bash
# 노드 상태 확인
kubectl get nodes

# Pod 상태 확인
kubectl get pods -n enterprise-rag

# 서비스 상태 확인
kubectl get services -n enterprise-rag

# Ingress 상태 확인
kubectl get ingress -n enterprise-rag
```

### 2. 로드 밸런서 엔드포인트 확인

```bash
# ALB 엔드포인트 조회
kubectl get ingress rag-platform-ingress -n enterprise-rag -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### 3. 서비스 헬스체크

```bash
# 엔드포인트 주소 확인 후 테스트
ALB_ENDPOINT=$(kubectl get ingress rag-platform-ingress -n enterprise-rag -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# 각 서비스 헬스체크
curl http://$ALB_ENDPOINT/text-extraction/health
curl http://$ALB_ENDPOINT/embedding/health
curl http://$ALB_ENDPOINT/indexing/health
curl http://$ALB_ENDPOINT/search/health
```

## 🔧 설정 관리

### 환경별 설정

**Production 환경:**
- Namespace: `enterprise-rag`
- 고가용성 설정
- 자동 스케일링 활성화
- SSL/TLS 적용

**Development 환경:**
- Namespace: `enterprise-rag-dev`
- 내부 로드 밸런서
- 디버그 로깅 활성화

### 스케일링 설정

```bash
# HPA (Horizontal Pod Autoscaler) 설정
kubectl autoscale deployment text-extraction-deployment --cpu-percent=70 --min=2 --max=10 -n enterprise-rag
kubectl autoscale deployment embedding-generator-deployment --cpu-percent=70 --min=2 --max=10 -n enterprise-rag
kubectl autoscale deployment indexing-service-deployment --cpu-percent=70 --min=2 --max=10 -n enterprise-rag
kubectl autoscale deployment search-api-deployment --cpu-percent=70 --min=2 --max=10 -n enterprise-rag
```

## 📈 모니터링 및 로깅

### CloudWatch 대시보드

배포 완료 후 AWS 콘솔에서 확인 가능:
- EKS 클러스터 메트릭
- Redis 성능 메트릭
- Kafka 처리량 메트릭
- OpenSearch 지연 시간 메트릭

### 로그 확인

```bash
# Pod 로그 확인
kubectl logs -f deployment/text-extraction-deployment -n enterprise-rag
kubectl logs -f deployment/embedding-generator-deployment -n enterprise-rag
kubectl logs -f deployment/indexing-service-deployment -n enterprise-rag
kubectl logs -f deployment/search-api-deployment -n enterprise-rag

# CloudWatch 로그 그룹
# - /aws/eks/enterprise-rag-eks/cluster
# - /aws/elasticache/enterprise-rag-redis
# - /aws/msk/enterprise-rag-kafka
```

## 🔒 보안 설정

### 네트워크 보안

- VPC 내 프라이빗 서브넷 배치
- 보안 그룹 최소 권한 원칙
- TLS 암호화 적용

### IAM 보안

- IRSA (IAM Roles for Service Accounts) 사용
- 최소 권한 정책 적용
- 서비스별 역할 분리

### 데이터 보안

- OpenSearch 도메인 암호화
- Redis 전송 중/저장 중 암호화
- S3 버킷 암호화
- Kafka 클러스터 암호화

## 🚨 트러블슈팅

### 일반적인 문제

1. **Pod가 Pending 상태**
   ```bash
   kubectl describe pod <pod-name> -n enterprise-rag
   # 리소스 부족이나 노드 선택 문제 확인
   ```

2. **이미지 Pull 실패**
   ```bash
   # ECR 로그인 확인
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   ```

3. **로드 밸런서 생성 실패**
   ```bash
   # AWS Load Balancer Controller 상태 확인
   kubectl get pods -n kube-system | grep aws-load-balancer-controller
   ```

4. **서비스 간 통신 실패**
   ```bash
   # 보안 그룹 규칙 확인
   # DNS 해결 확인
   kubectl exec -it <pod-name> -n enterprise-rag -- nslookup <service-name>
   ```

## 💰 비용 최적화

### 리소스 최적화

1. **인스턴스 타입 조정**
   - 개발: t3.small, t3.medium
   - 프로덕션: m5.large, c5.xlarge

2. **오토 스케일링 설정**
   - 최소/최대 인스턴스 수 조정
   - 스케일링 정책 최적화

3. **Reserved Instances 활용**
   - 예측 가능한 워크로드에 RI 적용
   - Savings Plans 고려

### 모니터링 도구

- AWS Cost Explorer
- AWS Trusted Advisor
- CloudWatch 비용 모니터링

## 🔄 업데이트 및 롤백

### 서비스 업데이트

```bash
# 이미지 업데이트
kubectl set image deployment/search-api-deployment search-api=<new-image> -n enterprise-rag

# 롤링 업데이트 상태 확인
kubectl rollout status deployment/search-api-deployment -n enterprise-rag
```

### 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/search-api-deployment -n enterprise-rag

# 특정 리비전으로 롤백
kubectl rollout undo deployment/search-api-deployment --to-revision=2 -n enterprise-rag
```

## 📞 지원 및 문의

배포 과정에서 문제가 발생하면:

1. 로그 확인 및 분석
2. AWS 문서 참조
3. Kubernetes 문서 참조
4. 커뮤니티 포럼 활용

---

**🎉 축하합니다! Enterprise RAG Platform이 성공적으로 클라우드에 배포되었습니다!**
