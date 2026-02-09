# 🔧 GitHub Actions 에러 해결 가이드

## ❌ 문제

GitHub Actions가 계속 실패하고 "Process completed with exit code 1" 에러가 발생합니다.

---

## 🔍 가장 흔한 원인: Git 권한 문제

### 원인

GitHub Actions Bot이 Repository에 push할 권한이 없습니다.

### 해결 방법

#### 1단계: Repository Settings 방문

1. **GitHub Repository 방문**
   - https://github.com/taewook486/DashBoard

2. **Settings 탭 클릭**

3. **왼쪽 메뉴에서 "Actions" 클릭**

#### 2단계: Workflow Permissions 설정

1. **"Workflow permissions" 섹션 찾기**

2. **다음 옵션中选择:**
   - ✅ **"Read and write permissions"**
   - ✅ **"Allow GitHub Actions to create and approve pull requests"** (선택사항)

3. **"Save" 버튼 클릭**

```
Settings → Actions → General → Workflow permissions
```

**선택해야 할 옵션:**
- ☑️ Read and write permissions
- ☑️ Allow GitHub Actions to create and approve pull requests (선택사항)

---

## 🐛 다른 가능한 에러들

### 에러 1: ModuleNotFoundError

**에러 메시지:**
```
ModuleNotFoundError: No module named 'seaborn'
```

**해결책:** ✅ 이미 수정 완료 (requirements.txt 사용)

### 에러 2: Script Execution Failed

**에러 메시지:**
```
python: can't open file 'update_all.py'
```

**해결책:** ✅ 이미 수정 완료 (경로 확인 추가)

### 에러 3: Permission Denied (git push)

**에러 메시지:**
```
fatal: could not read Username for 'https://github.com'
```

**해결책:** 위에서 설명한 Workflow permissions 설정 필요

### 에러 4: No changes detected

**에러 메시지:**
```
📊 No changes detected in data files
```

**이것은 에러가 아님!** 데이터에 변경사항이 없는 것으로 정상입니다.

---

## ✅ 설정 확인 체크리스트

### 필수 설정
- [ ] **Repository Settings → Actions → General**
- [ ] **Workflow permissions: "Read and write permissions"** 선택
- [ ] **Save** 클릭

### 테스트
- [ ] Actions 탭에서 수동 실행
- [ ] 실패한 스텝의 로그 확인
- [ ] "Permission denied" 에러가 사라졌는지 확인

---

## 🧪 테스트 방법

### 1. Workflow Permissions 설정 후 테스트

1. **위에서 설명한대로 Workflow permissions 설정**

2. **Actions 탭 방문**
   - https://github.com/taewook486/DashBoard/actions

3. **"Update Market Data" 워크플로우 클릭**

4. **"Run workflow" 버튼 클릭**

5. **실행 모니터링**

### 2. 성공적인 실행의 예

```
✅ Checkout repository
✅ Set up Python 3.10
✅ Install dependencies
✅ Create us_market directory
✅ Update market data (without AI)
✅ Check for changes
✅ Commit and push changes (if data changed)
✅ Summary
```

### 3. 실패할 경우

**가장 마지막 스텝 "Commit and push changes"에서 실패하면:**
- Workflow permissions가 제대로 설정되지 않은 것
- 위 단계 다시 확인

---

## 📊 정상 실행 예시

### 성공 로그

```
Run git push
  git config --local user.email "github-actions[bot]@users.noreply.github.com"
  git config --local user.name "github-actions[bot]"
  git commit -m "📊 Auto-update market data - ..."
  git push
  env:
    PYTHON_VERSION: 3.10.0
    PYTHONPATH: /opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/site-packages

To https://github.com/taewook486/DashBoard.git
   eed48ca..d629dad  main -> main

✅ Changes committed and pushed successfully
```

---

## 🎯 요약

### 가장 중요한 설정

**Repository Settings → Actions → General → Workflow permissions**

**반드시 선택:**
- ✅ **Read and write permissions**

### 왜 이 설정이 필요한가?

GitHub Actions Bot이 변경된 데이터 파일을 Repository에 커밋하고 푸시하려면 **쓰기 권한**이 필요합니다.

기본 설정은 **읽기 전용 (Read-only)**이므로, 반드시 **Read and write permissions**로 변경해야 합니다.

---

## 💡 추가 팁

### GitHub Actions가 성공하면

1. **자동으로 데이터 업데이트**됩니다
2. **Commit 탭**에서 "📊 Auto-update market data" 커밋 확인
3. **Render**가 자동으로 재배포
4. **웹사이트**에서 최신 데이터 확인

### 데이터가 업데이트되지 않으면?

1. **Actions 로그 확인**
2. **실제 데이터 생성 스크립트 실행 여부 확인**
3. **Render Shell에서 수동으로 update_all.py 실행**

---

## 📞 도움이 필요하면

**GitHub Actions 공식 문서:**
- https://docs.github.com/en/actions/security-guides/automatic-token-authentication

**이슈 생성:**
- https://github.com/taewook486/DashBoard/issues

---

**📅 최종 업데이트:** 2026-02-02
**🔄 상태:** Workflow permissions 설정 필요
