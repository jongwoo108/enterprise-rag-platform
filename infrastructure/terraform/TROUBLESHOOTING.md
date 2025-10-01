# 🛠️ Enterprise RAG Platform Terraform 전체 트러블슈팅 기록

## 📋 목차
1. [해결된 오류들](#해결된-오류들)
2. [적용된 수정사항](#적용된-수정사항)
3. [현재 상태](#현재-상태)
4. [남은 작업들](#남은-작업들)
5. [권장 다음 단계](#권장-다음-단계)
6. [학습된 교훈](#학습된-교훈)

---

## 🚨 해결된 오류들

### 1. **Helm Repository 중복 정의 오류**
```
Error: Attribute redefined
on modules\helm-charts\main.tf line 45, in resource "helm_release" "aws_load_balancer_controller":
45:   depends_on = [var.alb_controller_service_account]
The argument "depends_on" was already set at modules\helm-charts\main.tf:28,3-13
```

**🔍 원인 분석:**
- `aws_load_balancer_controller` 리소스에서 `depends_on`이 두 번 정의됨
- 28번째 줄과 45번째 줄에 각각 다른 `depends_on` 블록이 존재

**✅ 해결 방법:**
```terraform
# 수정 전
depends_on = [helm_repository.eks]
# ... 중간 코드 ...
depends_on = [var.alb_controller_service_account]

# 수정 후
depends_on = [helm_repository.eks, var.alb_controller_service_account]
```

**📁 수정 파일:** `infrastructure/terraform/modules/helm-charts/main.tf`

---

### 2. **aws_caller_identity 데이터 소스 누락**
```
Error: Reference to undeclared resource
on kms.tf line 15, in resource "aws_kms_key" "kafka":
15: AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
A data resource "aws_caller_identity" "current" has not been declared in the root module
```

**🔍 원인 분석:**
- KMS 정책에서 참조하는 `aws_caller_identity` 데이터 소스가 선언되지 않음
- AWS 계정 ID를 동적으로 가져오기 위해 필요한 데이터 소스 누락

**✅ 해결 방법:**
```terraform
# infrastructure/terraform/main.tf에 추가
data "aws_caller_identity" "current" {}
```

**📁 수정 파일:** `infrastructure/terraform/main.tf`

---

### 3. **Helm Repository 리소스 타입 오류**
```
Error: Invalid resource type
on modules\helm-charts\main.tf line 4, in resource "helm_repository" "eks":
The provider hashicorp/helm does not support resource type "helm_repository"
```

**🔍 원인 분석:**
- `helm_repository` 리소스 타입이 현재 Helm 프로바이더 버전(~> 2.10)에서 지원되지 않음
- 3개의 `helm_repository` 리소스가 모두 동일한 오류 발생

**✅ 해결 방법:**
1. `helm_repository` 리소스들을 모두 제거
2. `helm_release` 리소스에서 직접 repository URL 사용
3. Helm 프로바이더 설정에 repository 관리 옵션 추가

```terraform
# 수정 전
resource "helm_repository" "eks" {
  name = "eks"
  url  = "https://aws.github.io/eks-charts"
}

# 수정 후 (helm_repository 제거)
repository = "https://aws.github.io/eks-charts"
```

**📁 수정 파일:** `infrastructure/terraform/modules/helm-charts/main.tf`

---

### 4. **MSK 클러스터 보안 설정 업데이트 오류**
```
Error: updating MSK Cluster (arn:aws:kafka:ap-northeast-2:348823728620:cluster/enterprise-rag-prod-kafka/0ac1bf13-3ee5-4abb-8d8f-8ffac1b860f4-3) security: 
operation error Kafka: UpdateSecurity, https response error StatusCode: 400, RequestID: 3e9b39a1-c5fe-44e7-83ca-90f4e3ac7ce7, 
BadRequestException: The request does not include any updates to the security setting of the cluster
```

**🔍 원인 분석:**
- Terraform이 MSK 클러스터에 빈 `tls {}` 블록을 추가하려고 시도
- AWS MSK가 유효하지 않은 보안 업데이트를 거부
- `terraform plan`에서 확인: `+ tls {}` 추가 시도

**✅ 해결 방법:**
```terraform
# 수정 전
client_authentication {
  sasl {
    scram = true
  }
  tls {
    # certificate_authority_arns = [aws_acm_certificate.kafka.arn]
  }
}

# 수정 후
client_authentication {
  sasl {
    scram = true
  }
}
```

**📁 수정 파일:** `infrastructure/terraform/modules/msk/main.tf`

---

### 5. **MSK 모듈 보안 그룹 및 KMS 설정 문제**

**🔍 원인 분석:**
- `security_group_id`와 `kms_key_id` 변수가 빈 문자열로 전달됨
- 조건부 로직이 Terraform 상태 드리프트를 일으킴

**✅ 해결 방법:**
```terraform
# 수정 전
security_groups = var.security_group_id != "" ? [var.security_group_id] : [aws_security_group.kafka.id]
encryption_at_rest_kms_key_arn = var.kms_key_id != "" ? var.kms_key_id : null

# 수정 후
security_groups = [aws_security_group.kafka.id]
# encryption_at_rest_kms_key_arn 제거 (TLS 암호화만 사용)
```

**📁 수정 파일:** `infrastructure/terraform/modules/msk/main.tf`

---

### 6. **Helm 차트 다운로드 캐시 오류**
```
Error: could not download chart: no cached repo found. (try 'helm repo update'): 
open .helm\eks-index.yaml: The system cannot find the file specified
```

**🔍 원인 분석:**
- Helm 프로바이더가 저장소 캐시를 찾을 수 없음
- 시스템 레벨 Helm 설정과 Terraform Helm 프로바이더 간의 충돌

**✅ 해결 시도:**
1. Helm 프로바이더 설정에 repository 관리 옵션 추가
2. `.helm/repositories.yaml` 파일 생성
3. Helm 캐시 디렉토리 설정

```terraform
# infrastructure/terraform/main.tf
provider "helm" {
  repository_config_path = "${path.module}/.helm/repositories.yaml"
  repository_cache       = "${path.module}/.helm"
  
  kubernetes {
    # ... Kubernetes 설정
  }
}
```

**📁 생성 파일:** `infrastructure/terraform/.helm/repositories.yaml`

**⚠️ 상태:** 부분적으로 해결됨 (여전히 캐시 오류 발생)

---

## 🔧 적용된 수정사항

### 1. **Helm Charts 모듈 전면 수정**
**파일:** `infrastructure/terraform/modules/helm-charts/main.tf`

**주요 변경사항:**
- `helm_repository` 리소스 3개 제거
- `helm_release` 리소스에서 직접 repository URL 사용
- `depends_on` 중복 정의 문제 해결

### 2. **MSK 모듈 보안 설정 단순화**
**파일:** `infrastructure/terraform/modules/msk/main.tf`

**주요 변경사항:**
- 빈 `tls {}` 블록 제거
- 조건부 보안 그룹 참조 제거
- KMS 암호화 설정 단순화
- Secrets Manager 및 CloudWatch Log Group에서 KMS 참조 제거

### 3. **Helm 프로바이더 설정 개선**
**파일:** `infrastructure/terraform/main.tf`

**주요 변경사항:**
- `repository_config_path` 설정 추가
- `repository_cache` 설정 추가
- 독립적인 Helm 저장소 관리

### 4. **데이터 소스 추가**
**파일:** `infrastructure/terraform/main.tf`

**주요 변경사항:**
- `aws_caller_identity` 데이터 소스 추가
- KMS 정책에서 AWS 계정 ID 동적 참조 가능

### 5. **Helm 저장소 설정 파일 생성**
**파일:** `infrastructure/terraform/.helm/repositories.yaml`

**내용:**
- EKS, Prometheus, Jaeger 저장소 설정
- Helm 프로바이더용 독립적인 저장소 관리

---

## 📊 현재 상태

### ✅ **완전히 해결된 오류들 (6개)**
1. ✅ Helm Repository 중복 정의
2. ✅ aws_caller_identity 데이터 소스 누락
3. ✅ helm_repository 리소스 타입 오류
4. ✅ MSK 클러스터 보안 설정 업데이트
5. ✅ MSK 모듈 보안 그룹 설정 문제
6. ✅ MSK 모듈 KMS 설정 문제

### ⚠️ **부분적으로 해결된 오류들 (1개)**
1. ⚠️ **Helm 차트 다운로드 캐시 오류** - 여전히 발생 중

### 🔄 **진행 중인 작업들**
- Helm 프로바이더 버전 호환성 조사
- 대안적인 Helm 저장소 관리 방법 탐색

---

## 🚧 남은 작업들

### 1. **Helm Repository 캐시 문제 완전 해결**
```bash
# 추가 시도해볼 방법들
- Helm 프로바이더 버전 다운그레이드 (2.8.x 또는 2.9.x)
- system helm 명령어로 사전에 저장소 추가
- Terraform 외부에서 helm repo add 실행
```

### 2. **비활성화된 모듈들 활성화**
```terraform
# 현재 주석 처리된 모듈들
# module "kms" {                    # KMS 키 관리
# module "security_groups" {        # 보안 그룹 관리
```

### 3. **순환 의존성 해결**
- 보안 그룹 모듈과 다른 모듈들 간의 순환 의존성 문제
- 모듈 간 의존성 그래프 재설계 필요

### 4. **전체 인프라 테스트**
- 모든 모듈이 활성화된 상태에서 `terraform plan` 테스트
- `terraform apply` 전체 배포 테스트
- 리소스 간 연결성 확인

### 5. **모니터링 및 로깅 설정**
- CloudWatch 로그 그룹 설정 완료
- Prometheus 및 Grafana 설정 검증
- Jaeger 분산 추적 설정 확인

---

## 🎯 권장 다음 단계

### **단계 1: Helm 문제 해결 (우선순위: 높음)**
```bash
# 1. Helm 프로바이더 버전 변경 시도
# terraform/modules/helm-charts/에서 provider 버전 수정

# 2. 수동으로 Helm 저장소 추가 후 Terraform 실행
helm repo add eks https://aws.github.io/eks-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update
```

### **단계 2: KMS 모듈 구현 (우선순위: 중간)**
```bash
# infrastructure/terraform/modules/kms/ 디렉토리 생성
# main.tf, variables.tf, outputs.tf 파일 구현
# main.tf에서 KMS 모듈 활성화
```

### **단계 3: 보안 그룹 모듈 순환 의존성 해결 (우선순위: 중간)**
```bash
# 모듈 의존성 그래프 재설계
# 보안 그룹을 먼저 생성하고 다른 모듈에서 참조하는 방식으로 변경
```

### **단계 4: 전체 배포 테스트 (우선순위: 높음)**
```bash
terraform plan    # 전체 계획 확인
terraform apply   # 전체 배포 실행
```

---

## 📝 학습된 교훈

### 1. **Terraform 리소스 의존성 관리**
- `depends_on`의 중요성과 중복 정의 시 발생하는 문제
- 모듈 간 의존성 설계 시 순환 참조 방지의 중요성

### 2. **Helm 프로바이더 버전 호환성**
- Terraform 프로바이더 버전과 실제 서비스 버전 간의 호환성 확인 필요
- `helm_repository` 리소스가 지원되지 않는 버전에서의 대안 방법

### 3. **AWS 서비스별 제약사항**
- MSK 클러스터의 보안 설정 업데이트 시 빈 블록 허용하지 않음
- AWS 서비스별로 다른 정책과 제약사항 존재

### 4. **단계별 문제 해결 접근법**
- 한 번에 하나의 오류에 집중하여 해결
- 각 수정사항의 영향을 철저히 검증
- 오류 메시지를 자세히 분석하여 근본 원인 파악

### 5. **상태 관리의 중요성**
- Terraform 상태 파일의 중요성
- `terraform plan`을 통한 변경사항 사전 확인의 필요성

---

## 🔗 관련 파일들

### **수정된 파일들:**
- `infrastructure/terraform/main.tf`
- `infrastructure/terraform/modules/helm-charts/main.tf`
- `infrastructure/terraform/modules/msk/main.tf`

### **생성된 파일들:**
- `infrastructure/terraform/.helm/repositories.yaml`

### **참고 파일들:**
- `infrastructure/terraform/variables.tf`
- `infrastructure/terraform/outputs.tf`
- 각 모듈의 `variables.tf`, `outputs.tf`

---

## 📞 추가 지원

이 문서를 참고하여 남은 문제들을 해결하시고, 추가적인 도움이 필요하시면 다음 정보들을 확인해주세요:

1. **Terraform 버전:** `terraform version`
2. **AWS CLI 버전:** `aws --version`
3. **Helm 버전:** `helm version`
4. **현재 상태:** `terraform show`

**마지막 업데이트:** 2025년 1월 1일
**작성자:** AI Assistant
**프로젝트:** Enterprise RAG Platform
