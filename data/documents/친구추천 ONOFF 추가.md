# 기획서

https://www.figma.com/design/kYgkiTpk67AGSKdSTdjaOO/%EC%83%81%EB%B0%98%EA%B8%B0%EC%84%9C%EB%B9%84%EC%8A%A4?node-id=1062-1486&t=ymIS9kQwmvdPbsgF-1

---

# 기획 배경

## 친구추천 기능이란?

친구추천은 기존 회원이 신규 회원을 유치했을 때 양측 모두에게 혜택을 제공하는 리퍼럴(Referral) 마케팅 기능입니다.

### 동작 방식
1. 기존 회원이 자신의 고유 추천인 코드를 친구에게 공유
2. 신규 회원이 회원가입 시 추천인 코드 입력
3. 추천인(기존 회원)과 피추천인(신규 회원) 모두에게 쿠폰 자동 지급

### 쿠폰 지급 정책 (CMS 설정 기준)
| 대상 | 쿠폰명 | 할인 금액 | 유효기간 | 사용조건 |
|------|--------|-----------|----------|----------|
| 추천인 (기존회원) | 친구추천 감사 쿠폰 | 5,000원 | 발급일로부터 30일 | 30,000원 이상 예약 시 |
| 피추천인 (신규회원) | 신규가입 환영 쿠폰 | 7,000원 | 발급일로부터 14일 | 첫 예약 시 사용 가능 |

## 기획 변경 사유

### 기존 상황
- 친구추천 기능은 **상시 진행**으로 기획되어 배포
- 앱 내 마이페이지, 회원가입 화면 등에 친구추천 관련 UI가 항상 노출

### 변경된 요구사항
- 마케팅팀에서 친구추천을 **간헐적 캠페인**으로 운영 방침 변경
- 특정 시즌(설/추석 연휴, 여름휴가 시즌 등)에만 집중 진행 예정
- 캠페인 미진행 기간에는 앱 내 관련 UI를 숨겨야 함

### 개선 목표
CMS에서 친구추천 기능의 앱 노출 여부를 실시간으로 ON/OFF 제어할 수 있는 토글 기능 추가

---

# 기획 설명

## 기능 개요

CMS 관리자가 친구추천 기능의 앱 노출 상태를 즉시 변경할 수 있는 토글 스위치를 추가합니다.

## 상태별 앱 노출 영역

### ON 상태 (노출)
| 앱 화면 | 노출 요소 | 설명 |
|---------|-----------|------|
| 회원가입 | 추천인 코드 입력 필드 | 가입 폼 하단에 위치 |
| 마이페이지 | 친구추천 배너 | 내 추천코드 확인 및 공유 버튼 |
| 마이페이지 > 쿠폰함 | 친구추천 쿠폰 안내 | 친구 초대하고 쿠폰 받기 배너 |
| 홈 탭 | 이벤트 배너 (선택) | 마케팅 캠페인 기간에만 노출 |

### OFF 상태 (비노출)
| 앱 화면 | 변경 사항 |
|---------|-----------|
| 회원가입 | 추천인 코드 입력 필드 숨김 |
| 마이페이지 | 친구추천 배너 숨김 |
| 마이페이지 > 쿠폰함 | 친구추천 관련 안내 숨김 |
| 홈 탭 | 친구추천 이벤트 배너 숨김 |

> **주의**: OFF 상태에서도 기존에 발급된 쿠폰은 유효기간 내 정상 사용 가능

## 토글 변경 프로세스

```
관리자가 토글 클릭
       ↓
   확인 팝업 노출
  "친구추천을 노출/비노출 하시겠습니까?"
       ↓
    ┌───┴───┐
  [취소]   [확인]
    ↓        ↓
  변경취소   API 호출
             ↓
         성공 여부
        ┌───┴───┐
      실패     성공
       ↓        ↓
    에러팝업   완료팝업
    "잠시 후   "변경이
    다시       완료되었습니다"
    시도해주세요"
```

---

# 작업 범위

- **서비스**: CMS (Content Management System)
- **플랫폼**: Web (PC)

## GNB 메뉴 경로

```
서비스 운영
└── 마케팅 관리
    ├── 쿠폰 관리
    ├── 이벤트 관리
    └── 추천인 관리  ← 수정 대상
```

## 수정 영역 상세

### 추천인 관리 페이지 구조

**현재 화면 구성**:
```
┌─────────────────────────────────────────────────────────────────┐
│  추천인 관리                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  가입현황                                                │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │                                                          │    │
│  │  총 추천 건수        이번 달 추천        지급된 쿠폰     │    │
│  │  ┌─────────┐        ┌─────────┐        ┌─────────┐      │    │
│  │  │  3,542  │        │   127   │        │  7,084  │      │    │
│  │  │   건    │        │   건    │        │   장    │      │    │
│  │  └─────────┘        └─────────┘        └─────────┘      │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  추천인 목록                                  [검색필터] │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  번호 | 추천인 | 피추천인 | 추천일시 | 쿠폰지급 | 상태  │    │
│  │  ───────────────────────────────────────────────────── │    │
│  │  1    | user01 | new123  | 25.04.01 | 완료    | 정상   │    │
│  │  2    | user02 | new456  | 25.04.01 | 완료    | 정상   │    │
│  │  ...                                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**개선 후 화면 (토글 추가)**:
```
┌─────────────────────────────────────────────────────────────────┐
│  추천인 관리                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  가입현황                                                │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │                                                          │    │
│  │  ┌───────────────────────────────────────────────────┐  │    │
│  │  │  친구추천 앱 내 노출                              │  │    │
│  │  │                                                    │  │    │
│  │  │  현재 상태: 노출 중                    [●━━━] ON  │  │    │
│  │  │                                                    │  │    │
│  │  │  마지막 변경: 2025.04.01 14:32 (관리자: 김민서)   │  │    │
│  │  └───────────────────────────────────────────────────┘  │    │
│  │                                                          │    │
│  │  총 추천 건수        이번 달 추천        지급된 쿠폰     │    │
│  │  ┌─────────┐        ┌─────────┐        ┌─────────┐      │    │
│  │  │  3,542  │        │   127   │        │  7,084  │      │    │
│  │  │   건    │        │   건    │        │   장    │      │    │
│  │  └─────────┘        └─────────┘        └─────────┘      │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [이하 동일...]                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# UI/UX 상세 명세

## 토글 컴포넌트

### 기본 상태
| 상태 | 토글 모양 | 라벨 | 배경색 |
|------|-----------|------|--------|
| ON (노출) | `[●━━━]` | ON | Primary Blue (#3182F6) |
| OFF (비노출) | `[━━━●]` | OFF | Gray (#E5E8EB) |

### 상태 정보 표시
```
현재 상태: {노출 중 | 비노출 중}
마지막 변경: {YYYY.MM.DD HH:mm} (관리자: {이름})
```

## 확인 팝업

### ON → OFF 변경 시
```
┌─────────────────────────────────────┐
│                                     │
│     친구추천을 비노출 하시겠습니까? │
│                                     │
│     비노출 시 앱 내 친구추천 관련   │
│     모든 영역이 숨김 처리됩니다.    │
│                                     │
│        [취소]      [확인]           │
│                                     │
└─────────────────────────────────────┘
```

### OFF → ON 변경 시
```
┌─────────────────────────────────────┐
│                                     │
│     친구추천을 노출 하시겠습니까?   │
│                                     │
│     노출 시 앱 내 친구추천 관련     │
│     모든 영역이 활성화됩니다.       │
│                                     │
│        [취소]      [확인]           │
│                                     │
└─────────────────────────────────────┘
```

### 변경 완료 팝업
```
┌─────────────────────────────────────┐
│                                     │
│         변경이 완료되었습니다       │
│                                     │
│              [확인]                 │
│                                     │
└─────────────────────────────────────┘
```

### 에러 팝업
```
┌─────────────────────────────────────┐
│                                     │
│     변경에 실패하였습니다.          │
│     잠시 후 다시 시도해 주세요.     │
│                                     │
│              [확인]                 │
│                                     │
└─────────────────────────────────────┘
```

---

# 기술 명세

## API 명세

### 친구추천 노출 상태 조회
```
GET /api/v1/admin/referral/display-status

Response:
{
  "success": true,
  "data": {
    "isDisplayed": true,
    "lastModifiedAt": "2025-04-01T14:32:00+09:00",
    "lastModifiedBy": {
      "id": 123,
      "name": "김민서"
    }
  }
}
```

### 친구추천 노출 상태 변경
```
PUT /api/v1/admin/referral/display-status

Request:
{
  "isDisplayed": false
}

Response (성공):
{
  "success": true,
  "data": {
    "isDisplayed": false,
    "lastModifiedAt": "2025-04-07T10:15:00+09:00",
    "lastModifiedBy": {
      "id": 456,
      "name": "박영희"
    }
  }
}

Response (실패):
{
  "success": false,
  "error": {
    "code": "REFERRAL_001",
    "message": "상태 변경에 실패했습니다."
  }
}
```

## 영향받는 파일 목록

### CMS
| 파일 경로 | 설명 |
|-----------|------|
| `src/pages/marketing/ReferralManagement.tsx` | 추천인 관리 페이지 |
| `src/components/marketing/ReferralStatusCard.tsx` | 가입현황 카드 컴포넌트 (신규) |
| `src/components/marketing/DisplayToggle.tsx` | 노출 토글 컴포넌트 (신규) |
| `src/api/referral.ts` | 추천인 관련 API 호출 |
| `src/hooks/useReferralStatus.ts` | 추천인 상태 관리 훅 (신규) |

### App (API 연동)
| 파일 경로 | 설명 |
|-----------|------|
| `src/api/config.ts` | 앱 설정 API (친구추천 노출 여부 포함) |
| `src/screens/auth/SignUp.tsx` | 회원가입 화면 |
| `src/screens/mypage/MyPage.tsx` | 마이페이지 |
| `src/screens/mypage/CouponList.tsx` | 쿠폰함 |

## 수정 코드 예시

### ReferralStatusCard.tsx (신규)
```tsx
import React from 'react';
import { Switch } from '@/components/ui/Switch';
import { Modal } from '@/components/ui/Modal';
import { useReferralDisplayStatus } from '@/hooks/useReferralStatus';
import { formatDateTime } from '@/utils/dateUtils';

interface ReferralStatusCardProps {
  stats: {
    totalReferrals: number;
    monthlyReferrals: number;
    issuedCoupons: number;
  };
}

export const ReferralStatusCard: React.FC<ReferralStatusCardProps> = ({ stats }) => {
  const { 
    isDisplayed, 
    lastModifiedAt, 
    lastModifiedBy,
    isLoading,
    toggleDisplay 
  } = useReferralDisplayStatus();
  
  const [showConfirmModal, setShowConfirmModal] = React.useState(false);
  const [showResultModal, setShowResultModal] = React.useState(false);
  const [resultMessage, setResultMessage] = React.useState('');

  const handleToggleClick = () => {
    setShowConfirmModal(true);
  };

  const handleConfirm = async () => {
    setShowConfirmModal(false);
    
    try {
      await toggleDisplay(!isDisplayed);
      setResultMessage('변경이 완료되었습니다');
      setShowResultModal(true);
    } catch (error) {
      setResultMessage('변경에 실패하였습니다.\n잠시 후 다시 시도해 주세요.');
      setShowResultModal(true);
    }
  };

  const confirmMessage = isDisplayed
    ? '친구추천을 비노출 하시겠습니까?\n\n비노출 시 앱 내 친구추천 관련 모든 영역이 숨김 처리됩니다.'
    : '친구추천을 노출 하시겠습니까?\n\n노출 시 앱 내 친구추천 관련 모든 영역이 활성화됩니다.';

  return (
    <div className="status-card">
      <h3 className="status-card__title">가입현황</h3>
      
      {/* 노출 토글 영역 */}
      <div className="display-toggle-section">
        <div className="display-toggle-section__header">
          <span className="label">친구추천 앱 내 노출</span>
        </div>
        
        <div className="display-toggle-section__content">
          <span className="status-text">
            현재 상태: {isDisplayed ? '노출 중' : '비노출 중'}
          </span>
          <Switch
            checked={isDisplayed}
            onChange={handleToggleClick}
            disabled={isLoading}
            label={isDisplayed ? 'ON' : 'OFF'}
          />
        </div>
        
        {lastModifiedAt && (
          <div className="display-toggle-section__footer">
            마지막 변경: {formatDateTime(lastModifiedAt)} 
            (관리자: {lastModifiedBy?.name})
          </div>
        )}
      </div>

      {/* 통계 영역 */}
      <div className="stats-grid">
        <div className="stat-item">
          <span className="stat-item__value">{stats.totalReferrals.toLocaleString()}</span>
          <span className="stat-item__label">총 추천 건수</span>
        </div>
        <div className="stat-item">
          <span className="stat-item__value">{stats.monthlyReferrals.toLocaleString()}</span>
          <span className="stat-item__label">이번 달 추천</span>
        </div>
        <div className="stat-item">
          <span className="stat-item__value">{stats.issuedCoupons.toLocaleString()}</span>
          <span className="stat-item__label">지급된 쿠폰</span>
        </div>
      </div>

      {/* 확인 모달 */}
      <Modal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title=""
        message={confirmMessage}
        buttons={[
          { label: '취소', onClick: () => setShowConfirmModal(false), variant: 'secondary' },
          { label: '확인', onClick: handleConfirm, variant: 'primary' }
        ]}
      />

      {/* 결과 모달 */}
      <Modal
        isOpen={showResultModal}
        onClose={() => setShowResultModal(false)}
        title=""
        message={resultMessage}
        buttons={[
          { label: '확인', onClick: () => setShowResultModal(false), variant: 'primary' }
        ]}
      />
    </div>
  );
};
```

### useReferralStatus.ts (신규)
```typescript
import { useState, useEffect, useCallback } from 'react';
import { getReferralDisplayStatus, updateReferralDisplayStatus } from '@/api/referral';

interface DisplayStatus {
  isDisplayed: boolean;
  lastModifiedAt: string | null;
  lastModifiedBy: { id: number; name: string } | null;
}

export const useReferralDisplayStatus = () => {
  const [status, setStatus] = useState<DisplayStatus>({
    isDisplayed: false,
    lastModifiedAt: null,
    lastModifiedBy: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await getReferralDisplayStatus();
      setStatus(response.data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const toggleDisplay = useCallback(async (newValue: boolean) => {
    setIsLoading(true);
    try {
      const response = await updateReferralDisplayStatus({ isDisplayed: newValue });
      setStatus(response.data);
      return response;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    ...status,
    isLoading,
    error,
    toggleDisplay,
    refetch: fetchStatus,
  };
};
```

## 테스트 케이스

### 단위 테스트
```typescript
describe('useReferralDisplayStatus', () => {
  it('초기 로딩 시 API를 호출하여 상태를 가져온다', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useReferralDisplayStatus());
    
    expect(result.current.isLoading).toBe(true);
    await waitForNextUpdate();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isDisplayed).toBeDefined();
  });

  it('toggleDisplay 호출 시 상태가 변경된다', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useReferralDisplayStatus());
    
    await waitForNextUpdate();
    const initialValue = result.current.isDisplayed;
    
    await act(async () => {
      await result.current.toggleDisplay(!initialValue);
    });
    
    expect(result.current.isDisplayed).toBe(!initialValue);
  });
});

describe('ReferralStatusCard', () => {
  it('토글 클릭 시 확인 모달이 노출된다', () => {
    render(<ReferralStatusCard stats={mockStats} />);
    
    fireEvent.click(screen.getByRole('switch'));
    
    expect(screen.getByText(/하시겠습니까/)).toBeInTheDocument();
  });

  it('ON 상태에서 토글 시 비노출 확인 메시지가 노출된다', () => {
    mockUseReferralDisplayStatus.mockReturnValue({ isDisplayed: true, ...otherProps });
    render(<ReferralStatusCard stats={mockStats} />);
    
    fireEvent.click(screen.getByRole('switch'));
    
    expect(screen.getByText(/비노출 하시겠습니까/)).toBeInTheDocument();
  });

  it('OFF 상태에서 토글 시 노출 확인 메시지가 노출된다', () => {
    mockUseReferralDisplayStatus.mockReturnValue({ isDisplayed: false, ...otherProps });
    render(<ReferralStatusCard stats={mockStats} />);
    
    fireEvent.click(screen.getByRole('switch'));
    
    expect(screen.getByText(/노출 하시겠습니까/)).toBeInTheDocument();
  });

  it('변경 성공 시 완료 팝업이 노출된다', async () => {
    render(<ReferralStatusCard stats={mockStats} />);
    
    fireEvent.click(screen.getByRole('switch'));
    fireEvent.click(screen.getByText('확인'));
    
    await waitFor(() => {
      expect(screen.getByText('변경이 완료되었습니다')).toBeInTheDocument();
    });
  });

  it('변경 실패 시 에러 팝업이 노출된다', async () => {
    mockToggleDisplay.mockRejectedValue(new Error('API Error'));
    render(<ReferralStatusCard stats={mockStats} />);
    
    fireEvent.click(screen.getByRole('switch'));
    fireEvent.click(screen.getByText('확인'));
    
    await waitFor(() => {
      expect(screen.getByText(/실패하였습니다/)).toBeInTheDocument();
    });
  });
});
```

### E2E 테스트 시나리오

| 시나리오 | 테스트 단계 | 예상 결과 |
|----------|-------------|-----------|
| ON → OFF 변경 | 1. 추천인 관리 페이지 접속<br>2. ON 상태 토글 클릭<br>3. 확인 팝업에서 [확인] 클릭 | "변경이 완료되었습니다" 팝업 노출 후 토글 OFF 상태로 변경 |
| OFF → ON 변경 | 1. OFF 상태에서 토글 클릭<br>2. 확인 팝업에서 [확인] 클릭 | "변경이 완료되었습니다" 팝업 노출 후 토글 ON 상태로 변경 |
| 변경 취소 | 1. 토글 클릭<br>2. 확인 팝업에서 [취소] 클릭 | 팝업 닫히고 상태 유지 |
| 앱 반영 확인 (OFF) | 1. CMS에서 OFF로 변경<br>2. 앱 회원가입 화면 확인 | 추천인 코드 입력 필드 숨김 |
| 앱 반영 확인 (ON) | 1. CMS에서 ON으로 변경<br>2. 앱 마이페이지 확인 | 친구추천 배너 노출 |

---

# 이슈 트래킹

## 지라 이슈

| 구분 | 이슈 키 | 제목 | 담당자 | 상태 |
|------|---------|------|--------|------|
| 프론트엔드 | [FRONT24-254](https://coolstay.atlassian.net/browse/FRONT24-254) | [CMS] 친구추천 ON/OFF 토글 기능 추가 | 김도운 | Done |
| 백엔드 | BACK24-178 | [API] 친구추천 노출 상태 관리 API | 이상현 | Done |
| QA | [VGQA-2265](https://coolstay.atlassian.net/browse/VGQA-2265) | 친구추천 > On/Off 변경 완료 팝업이 노출되지 않는 문제 | 박지영 | Resolved |
| QA | [VGQA-2267](https://coolstay.atlassian.net/browse/VGQA-2267) | 친구추천 노출/비노출 팝업 문구 띄어쓰기 변경 적용 | 박지영 | Resolved |

## 버그 수정 히스토리

### VGQA-2265: 변경 완료 팝업 미노출

**증상**: 토글 변경 후 완료 팝업이 노출되지 않음

**원인**: API 응답 후 모달 상태 업데이트 로직 누락

**수정 내용**:
```typescript
// Before
const handleConfirm = async () => {
  setShowConfirmModal(false);
  await toggleDisplay(!isDisplayed);
  // 완료 팝업 로직 누락
};

// After
const handleConfirm = async () => {
  setShowConfirmModal(false);
  try {
    await toggleDisplay(!isDisplayed);
    setResultMessage('변경이 완료되었습니다');
    setShowResultModal(true);  // 추가
  } catch (error) {
    setResultMessage('변경에 실패하였습니다.\n잠시 후 다시 시도해 주세요.');
    setShowResultModal(true);  // 추가
  }
};
```

### VGQA-2267: 팝업 문구 띄어쓰기 오류

**증상**: "비노출하시겠습니까?" → "비노출 하시겠습니까?" 띄어쓰기 수정 필요

**수정 내용**:
```typescript
// Before
const confirmMessage = isDisplayed
  ? '친구추천을 비노출하시겠습니까?'
  : '친구추천을 노출하시겠습니까?';

// After
const confirmMessage = isDisplayed
  ? '친구추천을 비노출 하시겠습니까?'
  : '친구추천을 노출 하시겠습니까?';
```

## 타임라인

| 일자 | 마일스톤 |
|------|----------|
| 2025-03-25 | 기획 확정 |
| 2025-03-27 | 백엔드 API 개발 완료 |
| 2025-03-31 | 프론트엔드 개발 완료 |
| 2025-04-02 | QA 테스트 시작 |
| 2025-04-03 | VGQA-2265 버그 발견 |
| 2025-04-04 | 버그 수정 완료 |
| 2025-04-05 | VGQA-2267 문구 수정 |
| 2025-04-07 | 상용 배포 |

---

# QA 체크리스트

## 기능 테스트

- [x] ON → OFF 토글 변경 정상 동작
- [x] OFF → ON 토글 변경 정상 동작
- [x] 확인 팝업 노출 및 문구 확인
- [x] 변경 완료 팝업 노출 확인
- [x] 변경 취소 시 상태 유지 확인
- [x] 마지막 변경 일시/관리자 정보 노출 확인
- [x] 페이지 새로고침 후 상태 유지 확인

## 앱 연동 테스트

- [x] OFF 시 회원가입 화면 추천인 코드 필드 숨김
- [x] OFF 시 마이페이지 친구추천 배너 숨김
- [x] ON 시 모든 친구추천 관련 UI 정상 노출
- [x] 상태 변경 후 앱 즉시 반영 확인 (캐시 확인)

## 예외 케이스

- [x] API 에러 시 에러 팝업 노출
- [x] 네트워크 끊김 시 적절한 에러 처리
- [x] 동시 다발적 토글 클릭 방지 (로딩 중 비활성화)
- [x] 권한 없는 관리자 접근 시 처리

## 크로스 브라우저

- [x] Chrome (최신)
- [x] Safari (최신)
- [x] Edge (최신)
- [x] Firefox (최신)

---

# 특이사항

## 운영 가이드

### 마케팅 캠페인 시 체크리스트
1. 캠페인 시작 전: CMS에서 친구추천 ON으로 변경
2. 쿠폰 관리에서 친구추천 쿠폰 유효기간 확인
3. 캠페인 종료 시: CMS에서 친구추천 OFF로 변경
4. 기존 발급 쿠폰은 유효기간까지 사용 가능함을 CS팀 공유

### 주의사항
- OFF 상태에서도 이미 가입한 회원의 추천 코드는 유지됨
- OFF 기간 중 앱에서 추천 코드를 입력해도 무시됨 (에러 메시지 없이 조용히 처리)
- 캠페인 재개 시 기존 추천 코드 그대로 사용 가능

## 배포 정보

- **상용 배포일**: 2025-04-07 (월)
- **배포 시간**: 10:00
- **배포 방식**: 무중단 배포 (Blue-Green)
- **롤백 계획**: 이전 버전 Docker 이미지로 즉시 롤백 가능

## 향후 개선 계획

| 우선순위 | 개선 항목 | 예상 일정 |
|----------|-----------|-----------|
| 1 | 예약 노출 ON/OFF (특정 일시에 자동 변경) | Q2 2025 |
| 2 | 노출 상태 변경 이력 로그 페이지 추가 | Q3 2025 |
| 3 | A/B 테스트 기능 (일부 유저에게만 노출) | Q4 2025 |

## 관련 문서

- [친구추천 쿠폰 관리 가이드](https://wiki.coolstay.co.kr/cms/referral-coupon)
- [리퍼럴 마케팅 정책](https://wiki.coolstay.co.kr/marketing/referral-policy)
- [CMS 관리자 권한 가이드](https://wiki.coolstay.co.kr/cms/admin-permission)

---

# 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-03-25 | 최유진 (기획) | 최초 작성 |
| 1.1 | 2025-03-31 | 김도운 (개발) | 기술 명세 추가 |
| 1.2 | 2025-04-03 | 박지영 (QA) | QA 체크리스트 추가 |
| 1.3 | 2025-04-05 | 김도운 (개발) | 버그 수정 내역 반영 |
| 1.4 | 2025-04-07 | 최유진 (기획) | 운영 가이드 추가 |