# 문서 인덱싱 가이드

RAG 챗봇에서 문서를 인덱싱하는 방법을 안내합니다.

---

## 빠른 시작

### 1. 문서 준비

```bash
# docker 폴더 내 documents 디렉토리 생성
mkdir -p docker/documents

# 마크다운 문서 복사
cp your-docs/*.md docker/documents/
```

### 2. Docker 실행

```bash
cd docker
docker-compose up -d
```

**끝!** 최초 실행 시 자동으로 인덱싱됩니다.

---

## 지원 문서 형식

| 형식 | 지원 | 비고 |
|------|------|------|
| `.md` (Markdown) | ✅ | 권장 |
| `.txt` | ❌ | 추후 지원 예정 |
| `.pdf` | ❌ | 추후 지원 예정 |

---

## 문서 구조 권장사항

### 폴더 구조

```
docker/documents/
├── 서비스A/
│   ├── 개요.md
│   ├── API가이드.md
│   └── FAQ.md
├── 서비스B/
│   ├── 사용법.md
│   └── 트러블슈팅.md
└── 공통/
    └── 용어정의.md
```

### 문서 작성 팁

```markdown
# 문서 제목

## 개요
문서의 목적과 대상 독자를 명시합니다.

## 주요 내용
- 핵심 내용은 리스트로 정리
- 코드 블록 활용
- 표로 정보 구조화

## 관련 문서
- [다른 문서 링크](./other.md)
```

**권장사항:**
- 하나의 문서는 하나의 주제에 집중
- 제목(H1, H2)을 명확하게 사용
- 1,000~3,000자 내외가 적당

---

## 인덱싱 동작 방식

### 자동 인덱싱 조건

| 조건 | 동작 |
|------|------|
| ChromaDB가 비어있음 (최초 실행) | 자동 인덱싱 |
| `.reindex` 파일 존재 | 자동 재인덱싱 후 파일 삭제 |
| 위 조건 모두 아님 | 기존 인덱스 사용 |

### 처리 흐름

```
문서 파일 (.md)
    │
    ▼
┌─────────────────────┐
│   텍스트 추출       │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│   청킹 (1000자)     │  ← 문단 단위로 분할
│   오버랩 (200자)    │  ← 맥락 유지
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│   임베딩 생성       │  ← OpenAI text-embedding-3-small
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│   ChromaDB 저장     │
└─────────────────────┘
```

---

## 문서 업데이트

### 방법 1: 재인덱싱 플래그 사용 (권장)

```bash
# 1. 문서 추가/수정
cp new-doc.md docker/documents/

# 2. 재인덱싱 플래그 생성
touch docker/documents/.reindex

# 3. 컨테이너 재시작
docker-compose -f docker/docker-compose.yml restart
```

### 방법 2: 수동 인덱싱

```bash
# 실행 중인 컨테이너에서 직접 실행
docker exec -it rag-chatbot-backend python scripts/index_documents.py \
    --source /app/data/documents \
    --reset
```

### 방법 3: 전체 재빌드

```bash
# 볼륨까지 삭제 후 새로 시작
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

---

## CLI 옵션

로컬 환경에서 인덱싱 스크립트 직접 실행:

```bash
python scripts/index_documents.py [OPTIONS]
```

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--source` | 문서 폴더 경로 | (필수) |
| `--collection` | ChromaDB 컬렉션명 | `documents` |
| `--persist-dir` | ChromaDB 저장 경로 | `./data/chroma_db` |
| `--chunk-size` | 청크 크기 (자) | `1000` |
| `--chunk-overlap` | 청크 오버랩 (자) | `200` |
| `--batch-size` | 배치 크기 | `100` |
| `--reset` | 기존 인덱스 삭제 후 재생성 | `false` |
| `--status` | 인덱스 상태 확인 | - |

### 예시

```bash
# 기본 인덱싱
python scripts/index_documents.py --source ./data/documents

# 초기화 후 재인덱싱
python scripts/index_documents.py --source ./data/documents --reset

# 상태 확인
python scripts/index_documents.py --status

# 커스텀 청크 크기
python scripts/index_documents.py --source ./data/documents \
    --chunk-size 500 \
    --chunk-overlap 100
```

---

## 인덱싱 상태 확인

### Docker 로그 확인

```bash
# 인덱서 로그
docker logs rag-chatbot-indexer

# 예상 출력:
# ========================================
# RAG Chatbot - Document Indexer
# ========================================
# 📦 ChromaDB is empty (first run)
#    → Will index documents
# 📄 Found 15 markdown document(s)
# 🔄 Starting document indexing...
# ✅ Indexing completed successfully!
```

### 인덱스 통계 확인

```bash
docker exec -it rag-chatbot-backend python scripts/index_documents.py --status

# 출력:
# 📊 컬렉션 상태
# ==================================================
#   collection_name: rag-documents
#   document_count: 47
#   persist_directory: /app/data/chroma
```

---

## 문제 해결

### 인덱싱이 안 될 때

```bash
# 1. 문서 파일 확인
ls -la docker/documents/*.md

# 2. 환경 변수 확인
echo $OPENAI_API_KEY

# 3. 로그 확인
docker logs rag-chatbot-indexer
```

### "No markdown documents found" 오류

```bash
# documents 폴더가 올바르게 마운트되었는지 확인
docker exec -it rag-chatbot-indexer ls -la /app/data/documents/
```

### API 키 오류

```bash
# .env 파일에 OPENAI_API_KEY가 설정되어 있는지 확인
cat docker/.env | grep OPENAI
```

### 메모리 부족

대용량 문서 인덱싱 시:

```bash
# 배치 크기를 줄여서 실행
docker exec -it rag-chatbot-backend python scripts/index_documents.py \
    --source /app/data/documents \
    --batch-size 20 \
    --reset
```

---

## 성능 최적화

### 청크 크기 조정

| 문서 유형 | 권장 청크 크기 | 이유 |
|-----------|---------------|------|
| 기술 문서 | 800~1000자 | 맥락 유지 |
| FAQ | 300~500자 | 짧은 QA 쌍 |
| 가이드 | 1000~1500자 | 단계별 설명 |

### 대용량 문서 처리

10,000개 이상의 청크:

```bash
# 배치 크기 조정
--batch-size 50

# 메모리 제한 설정 (docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 2G
```

---

## 요약

| 작업 | 명령어 |
|------|--------|
| 최초 실행 | `docker-compose up -d` |
| 재인덱싱 | `touch docker/documents/.reindex && docker-compose restart` |
| 상태 확인 | `docker exec -it rag-chatbot-backend python scripts/index_documents.py --status` |
| 로그 확인 | `docker logs rag-chatbot-indexer` |
