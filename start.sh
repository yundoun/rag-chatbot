#!/bin/bash
#
# RAG 챗봇 시작 스크립트
#
# 사용법:
#   ./start.sh          # 일반 시작
#   ./start.sh --build  # 이미지 재빌드 후 시작
#   ./start.sh --reset  # 문서 재인덱싱 후 시작
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================"
echo "  RAG 챗봇 시작"
echo "========================================"
echo -e "${NC}"

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 파일이 없습니다.${NC}"
    echo ""
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}📝 .env.example을 복사하여 .env를 생성하세요:${NC}"
        echo "   cp .env.example .env"
        echo ""
        echo "그 후 API 키를 설정하세요:"
        echo "   OPENAI_API_KEY=your-key-here"
    fi
    exit 1
fi

# 옵션 파싱
BUILD_FLAG=""
RESET_FLAG=""

for arg in "$@"; do
    case $arg in
        --build)
            BUILD_FLAG="--build"
            echo -e "${YELLOW}🔨 이미지 재빌드 모드${NC}"
            ;;
        --reset)
            RESET_FLAG="true"
            echo -e "${YELLOW}🔄 문서 재인덱싱 모드${NC}"
            ;;
        --help|-h)
            echo "사용법: $0 [옵션]"
            echo ""
            echo "옵션:"
            echo "  --build   Docker 이미지 재빌드"
            echo "  --reset   문서 재인덱싱 (기존 인덱스 삭제)"
            echo "  --help    도움말 표시"
            exit 0
            ;;
    esac
done

# 재인덱싱 플래그 생성
if [ "$RESET_FLAG" = "true" ]; then
    echo -e "${YELLOW}📄 재인덱싱 플래그 생성 중...${NC}"
    mkdir -p data/documents
    touch data/documents/.reindex
    echo -e "${GREEN}✅ .reindex 플래그 생성됨${NC}"
    echo ""
fi

# 문서 폴더 확인
if [ ! -d "data/documents" ]; then
    echo -e "${YELLOW}📁 문서 폴더 생성 중...${NC}"
    mkdir -p data/documents
    echo -e "${GREEN}✅ data/documents 폴더 생성됨${NC}"
    echo ""
fi

# 문서 개수 확인
DOC_COUNT=$(find data/documents -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
echo -e "${BLUE}📚 발견된 문서: ${DOC_COUNT}개${NC}"
echo ""

# Docker Compose 실행 (docker/ 폴더의 docker-compose.yml 사용)
echo -e "${BLUE}🐳 Docker Compose 시작...${NC}"
echo ""

docker-compose -f docker/docker-compose.yml --env-file .env up $BUILD_FLAG
