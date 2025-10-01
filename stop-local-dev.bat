@echo off
echo =====================================
echo 🛑 Enterprise RAG Platform 로컬 개발 환경 종료
echo =====================================

echo 📊 현재 실행 중인 서비스:
docker compose ps

echo.
echo 🛑 서비스 종료 중...
docker compose down

echo.
echo 🧹 볼륨 및 네트워크 정리 (데이터 삭제됨):
set /p cleanup="데이터를 모두 삭제하고 정리하시겠습니까? (y/N): "
if /i "%cleanup%"=="y" (
    docker compose down -v --remove-orphans
    echo ✅ 모든 데이터가 정리되었습니다.
) else (
    echo ℹ️  데이터는 보존되었습니다. 다음 실행 시 복원됩니다.
)

echo.
echo 🎯 필요 시 Docker 리소스 정리:
echo   - 사용하지 않는 이미지: docker image prune
echo   - 사용하지 않는 볼륨: docker volume prune
echo   - 전체 정리: docker system prune -a
echo.
echo ✅ 로컬 개발 환경이 종료되었습니다.
pause

