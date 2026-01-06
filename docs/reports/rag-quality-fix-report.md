# RAG 검색 품질 문제 수정 보고서

**Project:** RAG Chatbot
**Task:** RAG Quality Fix
**Date:** 2025-12-12
**Status:** ✅ 완료

---

## 1. 문제 분석

### 관찰된 문제
1. **내부 문서가 있음에도 웹 검색 fallback 발생**
   - 쿼리: "부킹닷컴 연락처 노출 개선건에 대한 기획 설명해줘"
   - 기대: 내부 문서에서 답변
   - 실제: 웹 검색으로 부킹닷컴 고객센터 번호 안내

2. **내부 문서 답변인데 "웹 검색 결과 포함" 배너 표시**
   - 쿼리: "너가 가지고 있는 문서 정보는 어떻게 되지?"
   - 내부 문서에서 정보를 찾았는데도 웹 검색 배너 표시

### 근본 원인

| 영역 | 문제점 | 원래 값 |
|------|--------|---------|
| `relevance_threshold` | 너무 높음 | 0.8 |
| `min_high_relevance_docs` | 문서 수 대비 과도함 | 2 |
| `embedding_threshold` | LLM 평가 스킵 조건 | 0.5 |
| `_score_to_level` | HIGH 기준이 너무 높음 | >= 0.8 |
| `route_after_evaluation` | 충분 조건이 너무 엄격 | high >= 2 OR avg >= 0.8 |
| `evaluate_quality_node` | `needs_disclaimer` 항상 품질 기반 | 웹 검색 여부 무관 |

---

## 2. 수정 내용

### 2.1 settings.py - 임계값 조정

```python
# Before
relevance_threshold: float = 0.8
min_high_relevance_docs: int = 2

# After
relevance_threshold: float = 0.5  # 더 낮은 기준으로 관련 문서 수용
min_high_relevance_docs: int = 1  # 작은 컬렉션에 적합
```

### 2.2 relevance_evaluator.py - 평가 기준 완화

**embedding_threshold 조정:**
```python
# Before: embedding_threshold = 0.5
# After: embedding_threshold = 0.3 (더 많은 문서가 LLM 평가 받음)
```

**_score_to_level 임계값 조정:**
```python
# Before: HIGH >= 0.8, MEDIUM >= 0.5
# After: HIGH >= 0.6, MEDIUM >= 0.3
```

**calculate_metrics 충분 조건 완화:**
```python
# Before
sufficient = high_count >= 2 or avg >= threshold

# After
sufficient = (
    high_count >= 1 or
    (medium_count >= 1 and avg >= threshold) or
    avg >= threshold
)
```

### 2.3 edges.py - 라우팅 조건 완화

```python
# Before: 단순히 high >= min_high_docs OR avg >= threshold

# After: 3가지 조건 중 하나라도 만족하면 generate
# 1. high_count >= min_high_docs
# 2. avg_relevance >= threshold
# 3. medium_count >= 1 AND len(retrieved_docs) > 0 AND avg >= 0.3
```

### 2.4 nodes.py - 소스 표시 로직 수정

```python
# Before: quality evaluator의 needs_disclaimer 그대로 사용

# After: 웹 검색이 실제로 트리거된 경우에만 disclaimer 표시
needs_disclaimer = web_search_triggered  # web_search_triggered가 True일 때만
```

---

## 3. 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `src/config/settings.py` | relevance_threshold, min_high_relevance_docs 조정 |
| `src/rag/relevance_evaluator.py` | embedding_threshold, _score_to_level, calculate_metrics 수정 |
| `src/core/edges.py` | route_after_evaluation 라우팅 조건 완화 |
| `src/core/nodes.py` | evaluate_quality_node의 needs_disclaimer 로직 수정, medium_relevance_count 추가 |

---

## 4. 변경 전후 비교

### 시나리오: 3개 문서, 평균 relevance 0.6

**변경 전:**
```
high_count: 0 (0.6 < 0.8)
avg_relevance: 0.6 < 0.8
→ rewrite 시도 → 실패 → web_search fallback
→ needs_disclaimer: true (품질 평가 기반)
```

**변경 후:**
```
high_count: 1 (0.6 >= 0.6)
avg_relevance: 0.6 >= 0.5
→ generate (조건 1 또는 2 충족)
→ needs_disclaimer: false (웹 검색 미사용)
```

---

## 5. 예상 결과

| 테스트 쿼리 | 변경 전 | 변경 후 |
|------------|---------|---------|
| "부킹닷컴 연락처 노출 개선건 설명" | 웹 검색 fallback | 내부 문서 답변 |
| "친구추천 기능이 뭐야?" | 웹 검색 가능성 | 내부 문서 답변 |
| "문서 목록 알려줘" | 웹 배너 표시 | 배너 없음 |

---

## 6. 임계값 가이드

작은 문서 컬렉션(10개 미만)에 권장되는 설정:

```python
# settings.py
relevance_threshold: 0.5
min_high_relevance_docs: 1

# relevance_evaluator.py
embedding_threshold: 0.3
HIGH_LEVEL: 0.6
MEDIUM_LEVEL: 0.3
```

대규모 문서 컬렉션(100개 이상)에 권장되는 설정:

```python
# settings.py
relevance_threshold: 0.7
min_high_relevance_docs: 2

# relevance_evaluator.py
embedding_threshold: 0.4
HIGH_LEVEL: 0.7
MEDIUM_LEVEL: 0.4
```

---

## 7. 결론

이번 수정으로 작은 문서 컬렉션에서의 RAG 검색 품질이 크게 개선됩니다:

1. **웹 검색 fallback 감소**: 내부 문서에서 어느 정도 관련성이 있으면 웹 검색 없이 답변
2. **정확한 소스 표시**: 웹 검색이 실제로 사용된 경우에만 "웹 검색 결과 포함" 배너 표시
3. **유연한 임계값**: 문서 컬렉션 크기에 맞게 조정 가능

---

**완료 일시:** 2025-12-12
**개발자:** Developer Agent
