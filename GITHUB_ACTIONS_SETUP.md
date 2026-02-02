# 🤖 GitHub Actions로 자동 데이터 업데이트 설정

## 📋 개요

GitHub Actions를 사용하면 **하루 3회, 8시간 간격**으로 자동으로 시장 데이터를 업데이트할 수 있습니다.

**특징:**
- ⏰ 하루 3회 자동 실행 (8시간 간격)
  - 오전 8시 (장 시작 전)
  - 오후 4시 (장 마감 후)
  - 자정 12시 (마감)
- 🚀 yfinance로 최신 데이터 수집
- 📊 Smart Money Picks, Sector Heatmap, ETF Flows 등 업데이트
- 💾 변경된 데이터 자동으로 Git에 커밋
- 🔄 수동으로도 실행 가능

---

## 🚀 설정 방법

### 1단계: GitHub Secrets 추가

1. **GitHub Repository 방문**
   - https://github.com/taewook486/DashBoard

2. **Settings → Secrets and variables → Actions**

3. **"New repository secret" 클릭**

4. **다음 Secret 추가** (선택사항 - AI 기능 시 필요)

| Name | Secret | 필수여부 |
|------|--------|---------|
| `GOOGLE_API_KEY` | Gemini API 키 | ⚠️ 선택 (AI 기능 시) |
| `OPENAI_API_KEY` | OpenAI API 키 | ⚠️ 선택 (AI 기능 시) |
| `FRED_API_KEY` | FRED API 키 | ⚠️ 선택 (매크로 분석 시) |

**💡 참고:** API 키가 없어도 기본적인 데이터 업데이트는 작동합니다.

---

### 2단계: 워크플로우 파일 확인

**파일 위치:** [`.github/workflows/update-data.yml`](.github/workflows/update-data.yml)

이미 생성되어 있어야 합니다. 내용:

```yaml
schedule:
  # 하루 3회, 8시간 간격 (한국 시간 기준)
  - cron: '0 23 * * *'  # KST 08:00 (오전 8시 - 장 시작 전)
  - cron: '0 7 * * *'   # KST 16:00 (오후 4시 - 장 마감 후)
  - cron: '0 15 * * *'  # KST 00:00 (자정 12시)
```

---

### 3단계: 첫 실행 테스트

#### 자동 대기 (다음 예정 시간)

- 워크플로우가 자동으로 실행될 때까지 대기
- Actions 탭에서 실행 상태 모니터링
- **다음 실행:** 오늘 자정 또는 내일 오전 8시

#### 수동 실행 (즉시 테스트)

1. **GitHub Repository → Actions 탭**

2. **왼쪽 메뉴에서 "Update Market Data" 클릭**

3. **오른쪽 "Run workflow" 버튼 클릭**

4. **"Run workflow" 확인**

5. **실행 상태 모니터링**
   - 빌드 진행 상황 실시간 확인
   - 약 30-40분 소요

---

## 📊 실행 과정

### GitHub Actions가 하는 일

```
1. ✅ Checkout 코드 (5초)
2. ✅ Python 3.10 설치 (30초)
3. ✅ 의존성 설치 (2분)
4. ✅ us_market/update_all.py --quick 실행 (30분)
   - create_us_daily_prices.py (yfinance 데이터 수집)
   - smart_money_screener_v2.py (스마트 머니 스크리닝)
   - sector_heatmap.py (섹터 히트맵)
   - options_flow.py (옵션 플로우)
   - economic_calendar.py (경제 캘린더)
5. ✅ 변경사항 확인 (10초)
6. ✅ Git 커밋 및 푸시 (30초)
7. ✅ Render 자동 재배포 (3-5분)
```

**총 소요시간:** 약 40-50분

---

## 🔍 모니터링

### Actions 탭에서 확인

**GitHub Repository → Actions**

### 실행 상태

| 상태 | 아이콘 | 의미 |
|------|--------|------|
| 성공 | ✅ | 데이터 업데이트 완료 |
| 진행중 | 🔄 | 데이터 수집 중 |
| 실패 | ❌ | 에러 발생 (로그 확인 필요) |
| 취소 | ⚠️ | 수동으로 취소됨 |

### Summary 확인

각 실행마다 자동으로 요약이 생성됩니다:

```
📊 Market Data Update Summary

- Status: success
- Changes: true
- Timestamp: 2026-02-03 00:00:00 UTC

✅ Market data updated successfully
```

---

## 🧪 테스트 해보기

### 첫 번째: 수동 실행

1. **Actions 탭 → "Update Market Data"**
2. **"Run workflow" 클릭**
3. **실행 모니터링**

### 두 번째: 결과 확인

1. **Commits 탭 확인**
   - "📊 Auto-update market data" 커밋이 있어야 함

2. **Render Dashboard 확인**
   - 자동으로 재배포됨 (3-5분 소요)

3. **웹사이트 방문**
   - https://dashboard.onrender.com
   - 최신 데이터가 표시되어야 함

---

## 📅 스케줄

### 자동 실행 시간

| 회차 | 한국 (KST) | UTC | 설명 |
|------|-----------|-----|------|
| 1회 | 오전 8:00 | 23:00 (전날) | 장 시작 전 |
| 2회 | 오후 4:00 | 07:00 | 장 마감 후 |
| 3회 | 자정 12:00 | 15:00 | 마감 후 정리 |

### 캘린더

```
일  월  화  수  목  금  토
 ✅  ✅  ✅  ✅  ✅  ✅  ✅
 0   8   8   8   8   8   8   0시 (오전)
16  16  16  16  16  16  16  16시 (오후)
```

**하루 3회, 매일 8시간 간격으로 실행됩니다.**

---

## ⚙️ 고급 설정

### 실행 시간 변경

**[`.github/workflows/update-data.yml`](.github/workflows/update-data.yml)** 수정:

```yaml
schedule:
  # 예: 한국 시간 오후 2시 (UTC 05:00)
  - cron: '0 5 * * 1-5'

  # 예: 매일 매시간 (테스트용)
  - cron: '0 * * * *'

  # 예: 매주 월요일 오전 9시만
  - cron: '0 0 * * 1'
```

**Cron 형식:** `분 시 일 월 요일`

### AI 기능 활성화

AI 기능을 사용하려면 GitHub Secrets에 API 키를 추가하고, 워크플로우에서 `--quick` 플래그를 제거하세요:

```yaml
# AI 기능 포함 전체 업데이트
python update_all.py
```

---

## 🐛 문제 해결

### 문제 1: 워크플로우가 실행되지 않음

**원인:** 시간대 설정 문제

**해결:**
- UTC 시간으로 설정되어 있음
- 한국 시간 = UTC + 9시간
- 예: 한국 오전 9시 = UTC 00:00

### 문제 2: "No changes detected"

**원인:** 데이터에 변화가 없음

**해결:**
- 장이 열리지 않은 날일 수 있음
- yfinance 데이터가 동일할 수 있음
- 정상적인 상황임

### 문제 3: 실행 시간 초과

**원인:** 데이터 수집이 너무 오래 걸림

**해결:**
```yaml
timeout-minutes: 360  # 6시간으로 증가
```

### 문계 4: Git push 실패

**원인:** 권한 문제

**해결:**
- Repository Settings → Actions → General
- "Workflow permissions" → "Read and write permissions" 선택

---

## 📊 비용

GitHub Actions는 **공개 Repository에서 무료**입니다:

| 계정 유형 | 무료 사용량 |
|----------|-----------|
| Public Repo | 무제한 |
| Private Repo | 월 2,000분 |

**DashBoard은 Public Repo이므로 무료입니다!** ✅

---

## 🎯 체크리스트

### 설정
- [x] .github/workflows/update-data.yml 생성
- [ ] GitHub Secrets 추가 (선택사항)
- [ ] 워크플로우 파일 검토

### 테스트
- [ ] Actions 탭에서 수동 실행
- [ ] 실행 로그 확인
- [ ] 커밋 생성 확인
- [ ] Render 재배포 확인
- [ ] 웹사이트 데이터 확인

### 운영
- [ ] 다음 평일 오전 9시 자동 실행 대기
- [ ] 첫 자동 실행 성공 확인
- [ ] 정기적으로 실행 상태 모니터링

---

## ✅ 완료 후

**설정이 완료되면:**

1. ✅ 매일 평일 오전 9시 자동 업데이트
2. ✅ 최신 시장 데이터 항상 유지
3. ✅ 수동으로도 언제든 실행 가능
4. ✅ Render에서 자동으로 재배포

**더 이상 수동으로 데이터를 업데이트할 필요가 없습니다!** 🎉

---

## 📞 도움말

- **GitHub Actions 문서:** https://docs.github.com/en/actions
- **Cron 표현식:** https://crontab.guru/
- **이슈 생성:** https://github.com/taewook486/DashBoard/issues

---

**📅 생성일:** 2026-02-02
**🔄 마지막 업데이트:** 2026-02-02
