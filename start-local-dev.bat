@echo off
echo =====================================
echo 🚀 Enterprise RAG Platform 로컬 개발 환경 시작
echo =====================================

REM Docker 실행 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker가 설치되어 있지 않거나 실행되지 않습니다.
    echo Docker Desktop을 설치하고 실행한 후 다시 시도해주세요.
    pause
    exit /b 1
)

REM Docker Compose 실행 확인
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose가 설치되어 있지 않습니다.
    echo Docker Desktop의 최신 버전을 설치해주세요.
    pause
    exit /b 1
)

echo ✅ Docker 환경 확인 완료

REM 기존 컨테이너 정리 (선택사항)
echo.
echo 🧹 기존 컨테이너 정리 중...
docker compose down -v --remove-orphans

REM 서비스 빌드 및 시작
echo.
echo 🏗️  서비스 빌드 및 시작 중...
docker compose up -d --build

REM 서비스 상태 확인
echo.
echo ⏳ 서비스 시작 대기 중...
timeout /t 30 /nobreak >nul

echo.
echo 📊 서비스 상태 확인:
docker compose ps

echo.
echo =====================================
echo 🎉 로컬 개발 환경이 시작되었습니다!
echo =====================================
echo.
echo 🔗 접속 URL:
echo   - Kafka UI:           http://localhost:8080
echo   - OpenSearch:         http://localhost:9200
echo   - OpenSearch 대시보드: http://localhost:5601  
echo   - MinIO 콘솔:         http://localhost:9001
echo   - Redis:              localhost:6379
echo   - PostgreSQL:         localhost:5432
echo   - 텍스트 추출 서비스:  http://localhost:8081
echo.
echo 📋 접속 정보:
echo   - MinIO: minioadmin / minioadmin123
echo   - PostgreSQL: raguser / ragpassword
echo   - Redis: ragpassword
echo.
echo 🛠️  개발 명령어:
echo   - 로그 확인: docker compose logs -f [서비스명]
echo   - 서비스 재시작: docker compose restart [서비스명]
echo   - 전체 종료: docker compose down
echo.
echo 📖 API 문서: http://localhost:8081/docs
echo.
pause

