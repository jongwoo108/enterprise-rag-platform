@echo off
echo =====================================
echo Enterprise RAG Platform 개발 환경 설정
echo =====================================

REM Python 버전 확인
python --version
if %errorlevel% neq 0 (
    echo 오류: Python이 설치되어 있지 않습니다.
    echo Python 3.12+ 를 설치하고 다시 시도해주세요.
    pause
    exit /b 1
)

REM 가상환경 생성
echo.
echo [1/5] Python 가상환경 생성 중...
if not exist "venv" (
    python -m venv venv
    echo ✅ 가상환경이 생성되었습니다.
) else (
    echo ℹ️  가상환경이 이미 존재합니다.
)

REM 가상환경 활성화
echo.
echo [2/5] 가상환경 활성화 중...
call venv\Scripts\activate.bat
echo ✅ 가상환경이 활성화되었습니다.

REM pip 업그레이드
echo.
echo [3/5] pip 업그레이드 중...
python -m pip install --upgrade pip
echo ✅ pip이 업그레이드되었습니다.

REM 의존성 설치
echo.
echo [4/5] Python 의존성 설치 중...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 의존성 설치에 실패했습니다.
    echo 네트워크 연결을 확인하고 다시 시도해주세요.
    pause
    exit /b 1
)
echo ✅ 의존성 설치가 완료되었습니다.

REM 환경변수 설정 파일 생성
echo.
echo [5/5] 환경변수 설정 파일 생성 중...
if not exist ".env" (
    echo # Enterprise RAG Platform 환경변수 > .env
    echo # 개발 환경 설정 >> .env
    echo. >> .env
    echo ENVIRONMENT=development >> .env
    echo. >> .env
    echo # Kafka 설정 >> .env
    echo KAFKA_BOOTSTRAP_SERVERS=localhost:9092 >> .env
    echo. >> .env
    echo # AWS 설정 >> .env
    echo AWS_REGION=us-east-1 >> .env
    echo AWS_DEFAULT_REGION=us-east-1 >> .env
    echo. >> .env
    echo # 서비스 설정 >> .env
    echo SERVICE_NAME=enterprise-rag-platform >> .env
    echo SERVICE_VERSION=1.0.0 >> .env
    echo LOG_LEVEL=DEBUG >> .env
    echo. >> .env
    echo # 처리 설정 >> .env
    echo CHUNK_SIZE=1000 >> .env
    echo CHUNK_OVERLAP=100 >> .env
    echo MAX_FILE_SIZE_MB=50 >> .env
    echo ✅ .env 파일이 생성되었습니다.
) else (
    echo ℹ️  .env 파일이 이미 존재합니다.
)

echo.
echo =====================================
echo 🎉 개발 환경 설정이 완료되었습니다!
echo =====================================
echo.
echo 다음 단계:
echo 1. Docker Desktop 실행 (Kafka, Redis 등을 위해)
echo 2. 첫 번째 마이크로서비스 테스트:
echo    cd services\text-extraction
echo    python app.py
echo.
echo 3. 브라우저에서 확인:
echo    http://localhost:8080/docs
echo.
pause
