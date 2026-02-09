# Render.com에서 데이터 업데이트 방법

## 🔧 방법 1: Render Shell에서 직접 실행 (가장 빠름)

### 단계별 실행

1. **Render Dashboard 방문**
   - https://dashboard.render.com
   - DashBoard 서비스 클릭

2. **Shell 접속**
   - 상단 메뉴에서 **"Shell"** 클릭
   - 터미널이 열릴 때까지 대기 (10-20초)

3. **us_market 폴더로 이동**
   ```bash
   cd /opt/render/project/src/us_market
   ls -la
   ```

4. **데이터 생성 스크립트 실행**

   **옵션 A: 전체 실행 (50-60분 소요)**
   ```bash
   python update_all.py
   ```

   **옵션 B: 빠른 실행 (AI 제외, 30분 소요)**
   ```bash
   python update_all.py --quick
   ```

   **옵션 C: 개별 실행 (원하는 것만)**
   ```bash
   # 1. 가격 데이터 (10분)
   python create_us_daily_prices.py

   # 2. 스마트 머니 스크리닝 (10분)
   python smart_money_screener_v2.py

   # 3. 섹터 히트맵 (5분)
   python sector_heatmap.py

   # 4. 옵션 플로우 (5분)
   python options_flow.py

   # 5. 경제 캘린더 (5분)
   python economic_calendar.py
   ```

5. **완료 후 확인**
   ```bash
   ls -lh *.csv *.json
   ```

6. **웹사이트 새로고침**
   - https://dashboard.onrender.com
   - 데이터가 최신으로 업데이트되어야 함

---

## 🔄 방법 2: GitHub Actions로 자동화 (권장)

### 워크플로우 생성

**.github/workflows/update-data.yml** 파일 생성:

```yaml
name: Update Market Data

on:
  schedule:
    # 매일 한국 시간 오전 9시 (UTC 00:00)
    - cron: '0 0 * * 1-5'
  workflow_dispatch:  # 수동 실행 가능

jobs:
  update-data:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pandas numpy yfinance tqdm requests python-dotenv

      - name: Update market data
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd us_market
          python update_all.py --quick

      - name: Commit and push
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add us_market/*.csv us_market/*.json
          git diff --staged --quiet || git commit -m "Auto-update market data"
          git push
```

### GitHub Secrets 설정

1. GitHub Repository → Settings → Secrets and variables → Actions
2. New repository secret:
   - `GOOGLE_API_KEY`: Gemini API 키
   - `OPENAI_API_KEY`: OpenAI API 키

---

## 🤖 방법 3: API 엔드포인트로 데이터 업데이트

### Flask 엔드포인트 추가

```python
@app.route('/admin/update-data', methods=['POST'])
def update_data():
    """Trigger data update (admin only)"""
    # Security: Add authentication
    from us_market.update_all import main as update_main
    import subprocess

    try:
        result = subprocess.run(
            ['python', 'us_market/update_all.py', '--quick'],
            capture_output=True,
            text=True,
            timeout=1800  # 30분
        )

        return jsonify({
            'success': True,
            'output': result.stdout
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 사용법

```bash
curl -X POST https://dashboard.onrender.com/admin/update-data
```

---

## 📊 방법 4: 로컬에서 실행 후 커밋

### 로컬 실행

```bash
# PowerShell
cd C:\project\DashBoard\us_market
python update_all.py --quick
```

### Git 커밋

```bash
cd C:\project\DashBoard
git add us_market/*.csv us_market/*.json
git commit -m "Update market data"
git push origin main
```

---

## ⚡ 추천 방법

### 개발/테스트 중
**→ 방법 1 (Render Shell)** - 바로 실행 가능

### 프로덕션 운영
**→ 방법 2 (GitHub Actions)** - 매일 자동 업데이트

### 긴급 업데이트
**→ 방법 4 (로컬 실행 후 커밋)** - 빠르고 통제 가능

---

## 📋 체크리스트

### Render Shell 실행
- [ ] Render Dashboard 방문
- [ ] Shell 접속
- [ ] us_market 폴더로 이동
- [ ] update_all.py 실행 (또는 개별 스크립트)
- [ ] 완료 후 파일 확인
- [ ] 웹사이트 새로고침

### GitHub Actions 설정
- [ ] .github/workflows/update-data.yml 생성
- [ ] GitHub Secrets 추가 (API 키)
- [ ] Workflow 테스트 실행
- [ ] 스케줄 확인 (평일 오전 9시)
- [ ] 첫 자동 업데이트 대기

---

## 🎯 오늘 데이터 업데이트 방법

**가장 빠른 방법:**

1. Render Dashboard → Shell 접속
2. `cd /opt/render/project/src/us_market`
3. `python update_all.py --quick` (30분 소요)
4. 완료 후 웹사이트 새로고침

**또는 빠른 업데이트만:**

```bash
# 5분 안에 핵심 데이터만 업데이트
python smart_money_screener_v2.py
python sector_heatmap.py
python options_flow.py
python economic_calendar.py
```

---

**📅 마지막 업데이트:** 2026-02-02
**⏱️  다음 업데이트 권장:** 매일 평일 오전 9시
