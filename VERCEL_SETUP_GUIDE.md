# 🚀 Vercel GitHub App 설치 가이드

이 가이드는 DashBoard 프로젝트를 Vercel에 배포하기 위한 GitHub App 설치 및 연결 절차를 안내합니다.

---

## ✅ 사전 준비

### 1단계: Vercel 계정 확인

- ✅ Vercel Dashboard에 로그인되어 있음: https://vercel.com/dashboard
- 계정이 없다면 가입 필요 (GitHub 계정으로 로그인 가능)

### 2단계: GitHub Repository 확인

- ✅ Repository: https://github.com/taewook486/DashBoard
- ✅ GitHub Actions Workflow 생성됨: `.github/workflows/vercel-deploy.yml`

---

## 📋 설치 절차

### 단계 1: Vercel GitHub App 설치 (5분)

**방법 A: Vercel Dashboard에서 직접 설치 (권장)**

1. **Vercel Dashboard 접속**
   - URL: https://vercel.com/dashboard

2. **GitHub Integration 페이지로 이동**
   - 왼쪽 메뉴 → `Projects` → `Settings` → `Git Integration`
   - 또는 직접: https://vercel.com/dashboard/git-integration

3. **GitHub Repository 연결**
   - `Import Git Repository` 섹션에서
   - Repository URL: `https://github.com/taewook486/DashBoard`
   - 또는 `taewook486/DashBoard`로 검색
   - `Import` 버튼 클릭

4. **권한 부여 확인**
   - ✅ Scope: `Production Deployment` 선택
   - ✅ Repository: `taewook486/DashBoard`
   - `Connect` 버튼 클릭

5. **설치 완료 확인**
   - Vercel Dashboard에서 DashBoard 프로젝트가 보여야 함
   - `https://vercel.com/dashboard`에서 확인

---

**방법 B: GitHub 마켓플레이스에서 설치 (대안)**

1. **Vercel GitHub App 접속**
   - URL: https://github.com/apps/vercel
   - GitHub 계정으로 로그인 상태여야 함

2. **App 설치**
   - `Configure` 버튼 클릭
   - 설치할 Repository 선택: `taewook486/DashBoard`
   - 권한 확인 후 `Install` 클릭

---

### 단계 2: Vercel Token 생성 (3분)

**참고**: GitHub App 설치 시 자동으로 생성되는 경우도 있지만, 수동 생성하는 것이 안전합니다.

1. **Vercel Dashboard 접속**
   - URL: https://vercel.com/dashboard

2. **Token 생성 페이지 이동**
   - 왼쪽 메뉴 → `Settings` → `Tokens`
   - 또는 직접: https://vercel.com/dashboard/tokens

3. **토큰 생성**
   - `Create` 버튼 클릭
   - Token name: `DashBoard Deployment Token`
   - Description: `GitHub Actions에서 자동 배포용`
   - Scope: `Full Account` (전체 권한)

4. **토큰 저장 (중요!)**
   - ⚠️ 생성된 토큰을 반드시 안전하게 저장해야 함
   - ⚠️ 이 토큰은 생성 후 다시 표시되지 않습니다
   - 메모장이나 비밀번호 관리자에 복사

---

### 단계 3: GitHub Repository에 Token Secret 추가 (3분)

1. **GitHub Repository Settings 접속**
   - URL: https://github.com/taewook486/DashBoard/settings

2. **Secrets 메뉴 이동**
   - 왼쪽 메뉴 → `Secrets and variables` → `Actions`
   - URL: https://github.com/taewook486/DashBoard/settings/secrets/actions

3. **New Repository Secret 생성**
   - `New repository secret` 버튼 클릭

4. **Secret 정보 입력**
   - **Name**: `VERCEL_TOKEN`
   - **Value**: 2단계에서 생성한 Vercel Token 붙여넣기
   - **Secret 선택**:
     - ✅ Selected repository: `taewook486/DashBoard`
     - ✅ Add secret to: `All workflows` (모든 워크플로우)

5. **Secret 추가**
   - `Add secret` 버튼 클릭

6. **추가 확인**
   - Secrets 페이지에 `VERCEL_TOKEN`이 보이면 성공

---

## 🔄 자동 배포 트리거 방법

설치 완료 후 다음 방법으로 자동 배포를 트리거할 수 있습니다:

### 방법 1: Git Push (권장, 자동)

```bash
# 로컬에서 코드 변경 후
git add .
git commit -m "Update code"
git push origin main
```

→ GitHub Actions `vercel-deploy` workflow가 자동으로 실행됨
→ Vercel Production에 자동 배포됨

---

### 방법 2: GitHub Actions에서 수동 실행

1. **Actions 페이지 접속**
   - URL: https://github.com/taewook486/DashBoard/actions

2. **Workflow 선택**
   - 왼쪽 메뉴 → `Update Market Data` 또는 `Deploy to Vercel`
   - `Update Market Data`는 현재 작동 중

3. **Run workflow 버튼 클릭**
   - `Run workflow` 버튼 오른쪽 상단
   - Branch: `main` 선택
   - `Run workflow` 클릭

4. **실행 모니터링**
   - workflow 실행 상태를 실시간으로 확인
   - 완료되면 초록색 체크 마크가 표시됨

---

## ✅ 설치 완료 확인

### 단계별 체크리스트

- [ ] **1단계**: Vercel GitHub App 설치 완료
  - [ ] Vercel Dashboard 접속
  - [ ] Git Integration 페이지 이동
  - [ ] DashBoard Repository 연결
  - [ ] Production Deployment 권한 확인
  - [ ] 프로젝트가 Vercel Dashboard에 보임

- [ ] **2단계**: Vercel Token 생성 완료
  - [ ] Vercel Dashboard 접속
  - [ ] Tokens 페이지 이동
  - [ ] "DashBoard Deployment Token" 생성
  - [ ] 토큰 안전하게 저장

- [ ] **3단계**: GitHub Secret 추가 완료
  - [ ] GitHub Repository Settings 접속
  - [ ] Secrets and variables → Actions 페이지 이동
  - [ ] New repository secret 생성
  - [ ] Name: `VERCEL_TOKEN`
  - [ ] Token 값 입력
  - [ ] Secret 추가 및 확인

---

## 🧪 배포 테스트

### 배포 완료 후 테스트 방법

1. **Vercel Dashboard에서 배포 확인**
   - URL: https://vercel.com/dashboard
   - `DashBoard` 프로젝트의 `Deployments` 탭 확인
   - 최신 배포 상태 확인

2. **배포된 URL 확인**
   - Vercel Dashboard에서 `Domains` 탭 확인
   - 기본 도메인: `https://dashboard-[random].vercel.app`
   - 또는 커스텀 도메인이 설정된 경우

3. **API 테스트**
   ```bash
   # test_api.sh 수정
   BASE_URL="https://your-vercel-url.vercel.app"
   
   # 모든 엔드포인트 테스트
   curl -s "$BASE_URL/api/us/portfolio"
   curl -s "$BASE_URL/api/us/smart-money"
   curl -s "$BASE_URL/api/us/indices"
   # ... 기타 엔드포인트
   ```

4. **브라우저에서 접속 테스트**
   - 배포된 URL로 직접 접속
   - 모든 메뉴 기능 테스트
   - Smart Money, 섹터 히트맵, ETF 플로우 등

---

## 📊 문제 해결

### Vercel Token이 작동하지 않을 때

**증상**: GitHub Actions가 VERCEL_TOKEN을 찾지 못함

**해결 방법**:
1. Secret Name 확인: 정확히 `VERCEL_TOKEN`인지 확인
2. 대소문자 구분: `VERCEL_TOKEN` (모두 대문자)
3. Secret 유효성 확인: GitHub Actions에서 Secrets 목록 재확인
4. Workflow 파일 확인: `.github/workflows/vercel-deploy.yml`에서 `${{ secrets.VERCEL_TOKEN }}` 사용 확인

---

### 배포 시간 초과

**증상**: Vercel CLI가 배포 중 타임아웃

**해결 방법**:
1. `.gitignore` 확인: 큰 파일이 제외되어 있는지 확인
2. `vercel.json` 확인: `functions` 설정 확인
3. 배포 크기 최적화: 불필요한 파일 제외

---

## 📞 지원 및 도움말

### 공식 문서
- **Vercel 문서**: https://vercel.com/docs
- **GitHub Actions 문서**: https://docs.github.com/en/actions
- **Git Integration 가이드**: https://vercel.com/docs/concepts/git

### 문제 신고
- **Vercel 커뮤니티**: https://vercel.com/feedback
- **GitHub 지원**: https://support.github.com/contact

---

## 📌 빠른 참조

### 주요 링크
- **Vercel Dashboard**: https://vercel.com/dashboard
- **GitHub Repository**: https://github.com/taewook486/DashBoard
- **GitHub Actions**: https://github.com/taewook486/DashBoard/actions
- **GitHub Secrets**: https://github.com/taewook486/DashBoard/settings/secrets/actions

### GitHub Secrets 명령어 (CLI 사용 시)
```bash
# CLI로 Secret 추가 방법 (gh CLI 설치 필요)
gh secret set VERCEL_TOKEN "your-vercel-token-here" --repo taewook486/DashBoard
```

---

## ⚠️ 보안 주의사항

1. **토큰 보안**
   - ⚠️ 토큰을 절대 코드에 하드코딩하지 마십시오
   - ⚠️ 토큰을 공개하지 마십시오 (GitHub 공개 repo지만 보안 유의)
   - ⚠️ 토큰을 주기적으로 갱신하는 것을 권장합니다

2. **권한 관리**
   - ✅ 필요한 최소 권한만 부여하세요
   - ✅ 토큰 만료 시 자동 갱신 설정을 고려하세요

3. **배포 환경**
   - ✅ 배포 전 코드를 로컬에서 테스트하세요
   - ✅ 개발 환경과 프로덕션 환경을 분리하세요

---

## ✅ 설치 완료 후

### 다음 단계

1. **설치 완료 알리기**: 이 가이드의 모든 단계를 완료하면 "✅ 작업 완료"라고 알려주세요

2. **자동 배포 테스트**: 설치 후 첫 번째 push로 배포 테스트

3. **모니터링 시작**: Vercel Dashboard와 GitHub Actions에서 상태 모니터링

---

**📅 생성일**: 2026년 2월 4일
**🔄 마지막 업데이트**: 2026년 2월 4일

**버전**: 1.0
