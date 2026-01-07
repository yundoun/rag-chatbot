#!/bin/bash
#
# RAG 챗봇 중지 스크립트
#
# 사용법:
#   ./stop.sh           # 컨테이너 중지
#   ./stop.sh --clean   # 컨테이너 중지 + 볼륨 삭제
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "========================================"
echo "  RAG 챗봇 중지"
echo "========================================"
echo -e "${NC}"

# 옵션 파싱
CLEAN_FLAG=""

for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN_FLAG="true"
            echo -e "${YELLOW}🗑️  클린 모드 (볼륨 포함 삭제)${NC}"
            ;;
        --help|-h)
            echo "사용법: $0 [옵션]"
            echo ""
            echo "옵션:"
            echo "  --clean   컨테이너와 볼륨 모두 삭제"
            echo "  --help    도움말 표시"
            exit 0
            ;;
    esac
done

if [ "$CLEAN_FLAG" = "true" ]; then
    echo -e "${YELLOW}🛑 컨테이너 및 볼륨 삭제 중...${NC}"
    docker-compose -f docker/docker-compose.yml down -v
    echo -e "${GREEN}✅ 컨테이너와 볼륨이 삭제되었습니다.${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  다음 시작 시 문서가 재인덱싱됩니다.${NC}"
else
    echo -e "${YELLOW}🛑 컨테이너 중지 중...${NC}"
    docker-compose -f docker/docker-compose.yml down
    echo -e "${GREEN}✅ 컨테이너가 중지되었습니다.${NC}"
fi

echo ""
echo -e "${BLUE}다시 시작하려면: ./start.sh${NC}"
