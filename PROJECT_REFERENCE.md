# 📊 DashBoard 프로젝트 참고 문서

**최종 업데이트:** 2026-02-02
**버전:** 1.0.0
**상태:** 운영 중

---

## 🎯 프로젝트 개요

### 설명
미국 주식 시장 데이터를 분석하고 스마트 머니 추천 종목을 제공하는 AI 기반 대시보드입니다.

### 주요 기능
- **Smart Money Screening** - 6가지 요소 기반 종목 분석 (공급/수요, 기관 매수, 기술적, 펀더멘털, 애널리스트, 상대 강도)
- **실시간 차트** - 기술적 지표와 함께 인터랙티브 캔들 차트 제공
- **섹터 분석** - 11개 섹터 히트맵 시각화
- **ETF/옵션 흐름** - 자금 흐름 및 옵션 포지션 분석
- **AI 분석** - Gemini/GPT 기반 경제/종목 분석
- **다국어 지원** - 한국어/영어 전환

---

## 🔗 연결된 서비스

### 1. GitHub Repository
**URL:** https://github.com/taewook486/DashBoard
- 소스 코드 버전 관리
- 이슈 트래킹
- 문서화

### 2. Render.com (프로덕션 배포)
**URL:** https://dashboard.onrender.com
- Flask 웹 앱 호스팅
- 자동 배포 (GitHub push 시)
- 무료 티어 사용

### 3. GitHub Actions (자동 데이터 업데이트)
**Repository:** https://github.com/taewook486/DashBoard/actions
- 하루 3회 자동 업데이트
- 스케줄: 오전 8시, 오후 4시, 자정 12시 (KST)
- 데이터 자동 커밋

---

## 📁 프로젝트 구조

```
DashBoard/
├── flask_app.py                    # Flask 메인 서버 (738 lines, 13 endpoints)
├── requirements.txt                # Python 의존성
├── vercel.json                     # Vercel 배포 설정 (현재 미사용)
├── render.yaml                    # Render 배포 설정
│
├── templates/
│   └── index.html                 # 프론트엔드 UI (2,356 lines)
│
├── static/
│   ├── js/
│   │   └── app.js                 # 프론트엔드 로직 (1,583 lines)
│   └── css/
│       └── custom.css             # 다크 테마 스타일
│
├── us_market/                     # 데이터 분석 스크립트
│   ├── update_all.py             # 마스터 업데이트 스크립트
│   ├── create_us_daily_prices.py # 가격 데이터 수집
│   ├── smart_money_screener_v2.py # 스마트 머니 스크리닝
│   ├── sector_heatmap.py         # 섹터 히트맵
│   ├── analyze_etf_flows.py      # ETF 흐름 분석
│   ├── options_flow.py           # 옵션 흐름
│   ├── macro_analyzer.py         # 매크로 분석
│   ├── ai_summary_generator.py   # AI 요약 생성
│   └── economic_calendar.py      # 경제 캘린더
│
├── .github/workflows/
│   └── update-data.yml           # GitHub Actions 워크플로우
│
└── docs/                          # 문서
    ├── PART1_Data_Collection.md   # 데이터 수집 설계
    ├── PART2_Analysis_Screening.md # 분석 및 스크리닝 설계
    ├── PART3_AI_Analysis.md       # AI 분석 설계
    ├── PART4_Web_Server.md        # 웹 서버 설계
    ├── PART5_Frontend_UI.md      # 프론트엔드 UI 설계
    └── PART6_Frontend_Logic.md    # 프론트엔드 로직 설계
```

---

## 🌐 배포 환경

### 로컬 개발 환경
```bash
# 서버 시작
cd C:\project\DashBoard
python flask_app.py

# 접속
http://localhost:5001
```

### 프로덕션 환경 (Render)
**URL:** https://dashboard.onrender.com
- **플랫폼:** Render.com
- **인스턴스:** Free tier (512MB RAM, 0.1 CPU)
- **자동 절전:** 15분 무활동 시
- **재시작:** 첫 요청 시 30초 소요

### CI/CD (GitHub Actions)
**Workflow:** Update Market Data
- **트리거:** 매일 3회 (cron 스케줄)
- **작업:** 데이터 수집 → 커밋 → 푸시 → Render 재배포
- **소요 시간:** 30-40분

---

## 🔌 API 엔드포인트

### 메인 페이지
- `GET /` - 메인 대시보드 UI

### 시장 데이터
- `GET /api/us/indices` - 주요 지수 데이터
- `GET /api/us/smart-money` - 스마트 머니 TOP 20 추천
- `GET /api/us/stock-chart/<ticker>` - 종목 차트 데이터
- `GET /api/us/technical-indicators/<ticker>` - 기술적 지표 (RSI, MACD, BB, S/R)
- `GET /api/us/sector-heatmap` - 섹터 히트맵 데이터
- `GET /api/us/etf-flows` - ETF 자금 흐름
- `GET /api/us/options-flow` - 옵션 흐름
- `GET /api/us/calendar` - 경제 캘린더
- `GET /api/us/history-dates` - 이용 가능한 과거 데이터 날짜
- `GET /api/us/history/<date>` - 특정 날짜의 스냅샷

### AI 분석
- `GET /api/us/macro-analysis` - 매크로 경제 분석
- `GET /api/us/ai-summary/<ticker>` - 종목 AI 요약

### 포트폴리오
- `GET /api/us/portfolio` - 포트폴리오 관리 (미구현)

### 관리자
- `POST /api/us/update-data` - 데이터 업데이트 트리거

---

## 📊 데이터 파일

### 필수 데이터 파일 (Git에 포함)
| 파일 | 크기 | 용도 | 위치 |
|------|------|------|------|
| smart_money_current.json | 7.5KB | TOP 20 추천 종목 | us_market/ |
| sector_heatmap.json | 2.8KB | 섹터 성과 | us_market/ |
| options_flow.json | 2.8KB | 옵션 흐름 | us_market/ |
| ai_summaries.json | 2.6KB | AI 종목 분석 | us_market/ |
| macro_analysis.json | 1.2KB | 매크로 분석 (KO) | us_market/ |
| macro_analysis_en.json | 1.2KB | 매크로 분석 (EN) | us_market/ |
| weekly_calendar.json | 0.4KB | 경제 캘린더 | us_market/ |
| smart_money_picks_v2.csv | 32KB | 스마트 머니 데이터 | us_market/data/ |
| us_etf_flows.csv | 2KB | ETF 흐름 데이터 | us_market/data/ |
| us_stocks_list.csv | 12KB | 종목 리스트 | us_market/data/ |

### 대용량 데이터 파일 (Git 제외)
- `us_daily_prices.csv` (120MB) - 너무 커서 Git에 올리지 않음

---

## 🔄 데이터 업데이트 방법

### 방법 1: GitHub Actions (권장)
- **자동:** 매일 3회 실행
- **설정:** [.github/workflows/update-data.yml](.github/workflows/update-data.yml)
- **수동:** Actions 탭 → "Run workflow"

### 방법 2: Render Shell
```bash
# Render Dashboard → Shell 접속
cd /opt/render/project/src/us_market
python update_all.py --quick
```

### 방법 3: 로컬 실행
```bash
cd C:\project\DashBoard\us_market
python update_all.py --quick
```

### 방법 4: Create Report 버튼
- 웹사이트 헤더의 "Create Report" 버튼 클릭
- `POST /api/us/update-data` API 호출
- 백그라운드에서 업데이트 실행

---

## ⚙️ 환경 설정

### 필수 환경 변수
```env
PORT=5001                    # Flask 서버 포트
PYTHON_VERSION=3.10.0       # Python 버전
```

### 선택적 환경 변수 (AI 기능)
```env
GOOGLE_API_KEY=xxx          # Gemini API 키
OPENAI_API_KEY=xxx          # OpenAI API 키
FRED_API_KEY=xxx            # FRED 경제 데이터 API 키
```

### 로컬 .env 파일
```bash
# .env 예시
GOOGLE_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
FRED_API_KEY=your_fred_key_here
```

---

## 🧪 테스트

### 로컬 테스트
```bash
# 1. 서버 시작
python flask_app.py

# 2. API 테스트
curl http://localhost:5001/api/us/smart-money
curl http://localhost:5001/api/us/sector-heatmap

# 3. 브라우저 테스트
start http://localhost:5001
```

### API 테스트 스크립트
```bash
# test_api.sh (자동 생성됨)
bash test_api.sh
```

상세 테스트 보고서: [TESTING_REPORT.md](TESTING_REPORT.md)

---

## 🐛 문제 해결

### GitHub Actions 에러
**증상:** "Process completed with exit code 1"

**해결:**
1. GitHub Repository → Settings → Actions → General
2. Workflow permissions: **"Read and write permissions"** 선택
3. Save

상세 가이드: [GITHUB_ACTIONS_TROUBLESHOOTING.md](GITHUB_ACTIONS_TROUBLESHOOTING.md)

### Vercel 배포 실패
**증상:** Serverless Function 250MB 초과

**해결:** Render.com으로 변경 (이미 완료)

### 데이터가 표시 안됨
**증상:** API는 200인데 데이터 없음

**해결:**
1. Render Shell에서 `update_all.py` 실행
2. 또는 GitHub Actions 수동 실행

상세 가이드: [RENDER_DATA_UPDATE.md](RENDER_DATA_UPDATE.md)

---

## 📖 문서

### 사용자 가이드
- [README.md](README.md) - 프로젝트 개요 및 설치
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) - Render 배포 가이드
- [RENDER_DATA_UPDATE.md](RENDER_DATA_UPDATE.md) - 데이터 업데이트 방법
- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) - GitHub Actions 설정
- [GITHUB_ACTIONS_TROUBLESHOOTING.md](GITHUB_ACTIONS_TROUBLESHOOTING.md) - 에러 해결

### 개발자 문서
- [PART1-6](docs/) - 시스템 설계 문서
- [TESTING_REPORT.md](TESTING_REPORT.md) - 테스트 보고서

### 배포 가이드
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Vercel/Render 배포

---

## 🛠️ 기술 스택

### 백엔드
- **Flask** 3.x - 웹 프레임워크
- **Python** 3.10+ - 프로그래밍 언어
- **pandas** - 데이터 처리
- **numpy** - 수치 계산
- **yfinance** - 주가 데이터 수집
- **ta** - 기술적 지표 계산

### 프론트엔드
- **Tailwind CSS** - 스타일링
- **Lightweight Charts** - 캔들 차트
- **Chart.js** - 데이터 시각화
- **ApexCharts** - 히트맵
- **jQuery** - DOM 조작

### AI/ML
- **Google Gemini 3.0** - 매크로 분석
- **OpenAI GPT-5.2** - 종목 분석

### 인프라
- **Render.com** - 호스팅
- **GitHub Actions** - CI/CD
- **Git** - 버전 관리

---

## 📈 성과 지표

### 데이터 커버리지
- **종목 수:** 500개 (S&P 500)
- **가격 데이터:** 746,233 레코드
- **분석 완료:** 492/503 종목 (97.8%)
- **섹터:** 11개
- **ETF:** 24개

### Smart Money Picks (현재 TOP 5)
1. FITB (Fifth Third) - 78.8점
2. FDX (FedEx) - 78.0점
3. PPG (PPG Industries) - 76.6점
4. NOC (Northrop) - 76.6점
5. CMCSA (Comcast) - 76.5점

### 코드 베이스
- **총 라인 수:** ~5,000+ lines
- **파일 수:** 40개
- **언어:** Python, JavaScript, HTML, CSS
- **문서:** 10개 Markdown 파일

---

## 🎯 향후 개선 계획

### 단기 (1주일)
- [ ] GitHub Actions 안정화 (권한 설정)
- [ ] 모든 API 엔드포인트 테스트
- [ ] UI 버그 수정

### 중기 (1개월)
- [ ] 사용자 인증 추가
- [ ] 포트폴리오 추적 기능
- [ ] 알림 시스템 (이메일/Slack)
- [ ] 백테스팅 기능

### 장기 (3개월)
- [ ] 한국 시장 추가
- [ ] 앱 모바일 버전
- [ ] 실시간 WebSocket 업데이트
- [ ] 머신러닝 예측 모델

---

## 📞 지원 및 연락

### 이슈 트래킹
**GitHub Issues:** https://github.com/taewook486/DashBoard/issues

### 문서
**GitHub Wiki:** https://github.com/taewook486/DashBoard/wiki (예정)

---

## 📝 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2026-02-02 | 초기 릴리스 |
| - | - | Flask API 완성 |
| - | - | 프론트엔드 구현 완료 |
| - | - | GitHub Actions 구축 |
| - | - | Render 배포 완료 |

---

## 🏷️ 라이선스

MIT License

---

## 👥 기여자

- **개발:** taewook486
- **AI 지원:** Claude (Anthropic)

---

**문서 생성:** 2026-02-02
**마지막 업데이트:** 2026-02-02
**버전:** 1.0.0

---

## 📎 빠른 링크

- **🌐 Live Site:** https://dashboard.onrender.com
- **📦 GitHub:** https://github.com/taewook486/DashBoard
- **📖 README:** [README.md](README.md)
- **🧪 Testing:** [TESTING_REPORT.md](TESTING_REPORT.md)
- **🚀 Deploy:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **🔧 Actions Setup:** [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
- **💡 Data Update:** [RENDER_DATA_UPDATE.md](RENDER_DATA_UPDATE.md)
- **🐛 Troubleshooting:** [GITHUB_ACTIONS_TROUBLESHOOTING.md](GITHUB_ACTIONS_TROUBLESHOOTING.md)
