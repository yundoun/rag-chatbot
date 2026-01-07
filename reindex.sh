#!/bin/bash
#
# 문서 재인덱싱 스크립트
#
# 사용법:
#   ./reindex.sh        # 문서 재인덱싱 (Docker 재시작)
#
# 문서 변경 후 이 스크립트를 실행하면:
# 1. .reindex 플래그 생성
# 2. Docker 컨테이너 재시작
# 3. indexer 서비스가 문서 재인덱싱 수행
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
echo "  문서 재인덱싱"
echo "========================================"
echo -e "${NC}"

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 파일이 없습니다.${NC}"
    exit 1
fi

# 문서 폴더 확인
if [ ! -d "data/documents" ]; then
    echo -e "${RED}❌ data/documents 폴더가 없습니다.${NC}"
    exit 1
fi

# 문서 개수 확인
DOC_COUNT=$(find data/documents -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$DOC_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  마크다운 문서가 없습니다.${NC}"
    echo "   data/documents/ 폴더에 .md 파일을 추가하세요."
    exit 1
fi

echo -e "${BLUE}📚 발견된 문서: ${DOC_COUNT}개${NC}"
echo ""

# 문서 목록 출력
echo -e "${BLUE}📄 문서 목록:${NC}"
find data/documents -name "*.md" -type f | while read file; do
    echo "   - $(basename "$file")"
done
echo ""

# 재인덱싱 플래그 생성
echo -e "${YELLOW}📝 재인덱싱 플래그 생성...${NC}"
touch data/documents/.reindex
echo -e "${GREEN}✅ .reindex 플래그 생성됨${NC}"
echo ""

# Docker 재시작
echo -e "${YELLOW}🔄 Docker 컨테이너 재시작 중...${NC}"
echo ""

docker-compose -f docker/docker-compose.yml --env-file .env down
docker-compose -f docker/docker-compose.yml --env-file .env up
