# GETS Logistics Assistant - Conversation Starters

> **Usage**: Copy 4 starters to ChatGPT GPT "Conversation starters" field

---

## 📋 추천 세트 (기본)

ChatGPT GPT 설정의 "Conversation starters"에 아래 4개 문장을 입력하세요:

```
1. 📊 현재 병목(bottleneck) 상황을 요약해줘

2. 🚢 SCT-0143 선적 상태를 자세히 보여줘

3. ⏰ D-5 또는 초과된 승인 건이 있어?

4. 📈 오늘의 KPI 대시보드를 보여줘
```

---

## 🎯 대안 세트 (사용 시나리오별)

### Option A: 균형잡힌 세트 (기본 권장)
```
1. 📊 현재 병목 상황을 요약해줘
2. 🚢 SCT-0143 선적 상태를 자세히 보여줘
3. ⏰ D-5 또는 초과된 승인 건이 있어?
4. 📈 오늘의 KPI 대시보드를 보여줘
```

### Option B: 운영팀 중심
```
1. 📊 72시간 이상 지연된 병목이 있어?
2. 🔴 HIGH risk 선적과 다음 액션 알려줘
3. ⏰ FANR 승인 중 긴급한 건 있어?
4. 📋 HE-0538 상태 확인 및 업데이트
```

### Option C: 관리자용
```
1. 📊 전체 병목 요약 (카테고리별)
2. 📈 이번주 문서 완료율과 KPI
3. 🔴 Critical/High risk 선적 현황
4. ⏱️ 승인 SLA 준수율은?
```

### Option D: 영문 버전
```
1. 📊 Show me current bottleneck summary
2. 🚢 What's the status of shipment SCT-0143?
3. ⏰ Any critical or overdue approvals?
4. 📈 Give me today's KPI dashboard
```

---

## 🧪 고급 세트 (구체적 쿼리)

### Option E: 분석 중심
```
1. 📊 24시간 이상 지연된 병목 건수와 원인 분석
2. 🔴 HIGH/CRITICAL risk 선적 목록과 다음 액션
3. ⏰ FANR/MOEI 승인 중 D-5 이내 긴급 건
4. 📈 BOE/DO/COO 문서 완료율과 상위 3개 병목
```

### Option F: 데모/프레젠테이션용
```
1. 📊 병목 요약 + 에이징 분포 보여줘 (GETS API 데모)
2. 🗄️ Shipments 테이블에서 HIGH risk 조회 (Airtable 직접)
3. 🔄 SCT-0143의 이벤트 히스토리 보여줘 (감사 추적)
4. ⚠️ HE-0538 리스크 레벨을 LOW로 변경 (업데이트 워크플로우)
```

---

## 📊 각 스타터가 트리거하는 API

| 대화 스타터 | API 호출 | 응답 속도 | API 타입 |
|------------|---------|---------|---------|
| 현재 병목 상황 | `getsGetBottleneckSummary` | ~1-2초 | 🔵 GETS |
| SCT-0143 상태 | `getsGetDocumentStatus` | ~1초 | 🔵 GETS |
| D-5 초과 승인 | `getsGetApprovalSummary` | ~2초 | 🔵 GETS |
| KPI 대시보드 | `getsGetStatusSummary` | ~1-2초 | 🔵 GETS |
| HIGH risk 조회 | `airtableGetRecords` | ~1초 | 🟠 Airtable |
| 상태 업데이트 | `airtableGetRecords` + `airtableUpdateRecord` | ~2-3초 | 🟠 Airtable |

---

## 🎨 이모지 가이드

사용 가능한 이모지와 의미:

```
📊 - 요약, 통계, 분석
🚢 - 선적, 화물
⏰ - 승인, 기한, SLA
📈 - KPI, 대시보드, 트렌드
🔴 - 위험, 긴급
⚠️ - 경고, 주의
✅ - 완료, 승인
📋 - 상세, 목록
🔍 - 조회, 검색
⚙️ - 설정, 업데이트
🗄️ - 데이터베이스, 테이블
🔄 - 히스토리, 추적
```

---

## 📝 ChatGPT GPT 설정 방법

### Step 1: GPT Configure 페이지 열기
1. ChatGPT 접속
2. 왼쪽 메뉴에서 "Your GPTs" 클릭
3. "GETS Logistics GPT" 선택
4. "Configure" 탭 클릭

### Step 2: Conversation starters 섹션 찾기
- 페이지를 아래로 스크롤
- "Conversation starters" 섹션 찾기 (Name, Description 아래)
- 4개의 입력란이 있음

### Step 3: 4개 문장 입력
위에서 선택한 세트(Option A 권장)의 4개 문장을 각 입력란에 복사:

```
[Input 1] 📊 현재 병목(bottleneck) 상황을 요약해줘
[Input 2] 🚢 SCT-0143 선적 상태를 자세히 보여줘
[Input 3] ⏰ D-5 또는 초과된 승인 건이 있어?
[Input 4] 📈 오늘의 KPI 대시보드를 보여줘
```

### Step 4: Save & Publish
- 페이지 상단의 "Update" 또는 "Save" 버튼 클릭
- 변경사항이 즉시 적용됨

---

## 💡 커스터마이징 팁

### 실제 선적번호로 변경
```
Before: 🚢 SCT-0143 선적 상태를 자세히 보여줘
After:  🚢 [자주 조회하는 선적번호] 상태를 자세히 보여줘
```

### 특정 테이블 조회 추가
```
📋 Vendors 테이블에서 활성 공급업체 목록 보여줘
```

### 특정 승인 타입 강조
```
⏰ FANR 승인 중 D-5 이내 긴급 건은?
```

### 시간대 맞춤
```
📈 오늘 오전 회의용 KPI 리포트 (06:00 GST 기준)
```

---

## ✅ 테스트 체크리스트

Conversation starters 설정 후 테스트:

- [ ] 각 스타터 클릭 시 즉시 응답 생성
- [ ] 올바른 API 호출 (🔵 GETS 또는 🟠 Airtable)
- [ ] 응답에 데이터 포함 (에러 없음)
- [ ] 응답 시간 2초 이내
- [ ] 이모지가 정상 표시됨

---

## 🎯 최종 추천

**Option A (균형잡힌 세트)** 를 사용하세요!

이유:
- ✅ 4개 문장이 각각 다른 주요 기능 커버
- ✅ 조회(Read) 3개 + 업데이트 힌트 1개로 균형
- ✅ GETS API 위주 (빠르고 안전)
- ✅ 자연스러운 한글 표현
- ✅ 이모지로 시각적 구분 명확

---

## 📞 문의 및 피드백

Conversation starters가 작동하지 않으면:
1. GPT Actions가 올바르게 설정되었는지 확인
2. GETS API와 Airtable API 모두 연결되었는지 확인
3. 각 스타터를 개별적으로 테스트
4. 에러 메시지를 확인하고 API 상태 점검

---

**Updated**: 2025-12-25  
**Version**: 1.0.0  
**For**: GETS Logistics GPT (Dual-Action Architecture)

