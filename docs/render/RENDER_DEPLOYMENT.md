# 🚀 Render.com 배포 가이드

Vercel은 정적 사이트에 최적화되어 있어, Flask 앱은 **Render.com** 배포를 추천합니다.

## 왜 Render.com인가?

| 특징 | Vercel | Render.com |
|------|--------|------------|
| Flask 지원 | ⚠️ 제한적 (250MB 제한) | ✅ 완전 지원 |
| 무료 티어 | ✅ 있음 | ✅ 있음 |
| 데이터 분석 앱 | ❌ 부적합 | ✅ 적합 |
| Python 종속성 | ⚠️ 크기 제한 | ✅ 무제한 |
| 설정 난이도 | ⚠️ 복잡 | ✅ 간단 |

---

## 📋 배포 단계

### 1단계: Render 가입

1. **Render 방문**: https://render.com
2. **GitHub으로 가입**: "Sign up with GitHub" 클릭
3. **Repository 권한 부여**: DashBoard 저장소 접근 허용

### 2단계: New Web Service 생성

1. **Dashboard** → **"New +"** → **"Web Service"** 클릭
2. **GitHub 연동**:
   - "Connect GitHub" 클릭
   - **"DashBoard"** 저장소 선택
3. **설정 입력**:

| 항목 | 값 |
|------|-----|
| **Name** | `DashBoard` |
| **Region** | `Oregon (us-west)` (또는 Seoul 선택 가능) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python flask_app.py` |

### 3단계: 환경변수 설정

**Environment** 탭에서 다음 변수들 추가:

| Key | Value | Required |
|-----|-------|----------|
| `PYTHON_VERSION` | `3.10.0` | ✅ |
| `PORT` | `5001` | ✅ |
| `GOOGLE_API_KEY` | Gemini API 키 | AI 기능 시 |
| `OPENAI_API_KEY` | OpenAI API 키 | AI 기능 시 |
| `FRED_API_KEY` | FRED API 키 | 매크로 분석 시 |

### 4단계: 배포 시작

- **"Create Web Service"** 클릭
- 빌드 자동 시작 (약 3-5분 소요)
- 배포 완료되면 자동 URL 생성: `https://dashboard.onrender.com`

---

## 🌐 배포 완료 후

### Live URL 확인

```
https://dashboard.onrender.com
```

### 테스트

```bash
# API 테스트
curl https://dashboard.onrender.com/api/us/stocks
curl https://dashboard.onrender.com/api/us/heatmap
```

### 무료 티어 제한

- **750시간/월** (충분)
- **512MB RAM**
- **0.1 CPU**
- **자동 절전 모드**: 15분 무활동 시 sleep
- **wake up**: 첫 요청 시 ~30초 소요

---

## 🔧 Vercel과의 차이점

### Vercel (현재 실패)
```bash
❌ Serverless Function 크기 250MB 제한
❌ Flask 전체 앱 배포 불가
❌ 데이터 분석 패키지 용량 초과
```

### Render.com (추천)
```bash
✅ 완전한 Flask 앱 실행 가능
✅ 용량 제한 없음
✅ 데이터 분석 패키지 모두 사용 가능
✅ 무료 티어 제공
```

---

## 📊 배포 비교

| 플랫폼 | 상태 | 추천 |
|--------|------|------|
| **Vercel** | ❌ 실패 (250MB 초과) | 정적 사이트용 |
| **Render.com** | ✅ 권장 | Flask/Python 앱용 |
| **Railway.app** | ✅ 대안 | Docker 지원 |
| **Fly.io** | ✅ 대안 | 전 세계 배포 |

---

## 🎯 빠른 시작 (5분 배포)

1. **Render 방문**: https://render.com
2. **GitHub 연동**: DashBoard 저장소 선택
3. **Web Service 생성**:
   - Name: `DashBoard`
   - Runtime: `Python 3`
   - Build: `pip install -r requirements.txt`
   - Start: `python flask_app.py`
4. **환경변수 추가**: `PORT=5001`
5. **배포 시작**: "Create Web Service"

**5분 뒤**: `https://dashboard.onrender.com` 🚀

---

## 🔄 GitHub 자동 배포

Render는 GitHub와 연동되어 **자동 배포**가 됩니다:

```bash
# 로컬에서 변경
git add .
git commit -m "Add new feature"
git push origin main

# Render에서 자동으로 재배포! ✅
```

---

## 💡 참고

- **Render YAML**: [render.yaml](render.yaml) 파일이 이미 프로젝트에 포함되어 있습니다
- **환경변수**: Render Dashboard → Environment 탭에서 언제든 수정 가능
- **로그**: Dashboard → Logs 탭에서 실시간 로그 확인
- **도메인**: Settings → Custom Domain에서 개인 도메인 연결 가능

---

## ✅ 결론

**Vercel은 정적 사이트용, Render는 동적 앱용!**

Flask + Pandas + 데이터 분석 앱은 **Render.com**이 최적의 선택입니다.

---

**🚀 지금 바로 배포 시작하세요!**

https://render.com
