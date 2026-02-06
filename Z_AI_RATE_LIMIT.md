# Z.ai Rate Limit (속도 제한) 해결 방법

**날짜:** 2026-02-06
**상태:** ⚠️ Rate Limit 발생 중

## 문제 증상

```
Status: 429
Error: Rate limit exceeded
```

## 원인 분석

Z.ai API에서 일정 시간(분/시간) 동안 너무 많은 요청을 보내면 429 에러가 발생합니다.

**테스트 결과:**
- ✅ API 키: 유효함
- ✅ 인증: 성공
- ✅ 모델(`glm-4-plus`): 사용 가능
- ⚠️ 속도 제한: 활성화됨

## 해결 방법

### 방법 1: 요청 속도 줄이기 (현재 적용됨) ✅

이미 코드에 적용됨:
- 요청 간 2초 대기
- Rate Limit 발생 시 5초 대기 후 재시도

**파일:**
- `us_market/ai_summary_generator.py`
- `us_market/macro_analyzer.py`

### 방법 2: Z.ai 플랫폼에서 제한 확인 및 상향

1. [Z.ai 콘솔](https://open.bigmodel.cn/) 접속
2. **API 관리** 또는 **사용량** 메뉴 확인
3. 현재 속도 제한(QPM/RPM) 확인
4. 필요시 상향 요청

**일반적인 제한:**
- 무료 요금제: 분당 3-10회
- 유료 요금제: 분당 20-100회

### 방법 3: 한 번에 여러 종목 처리하지 않기

**기존 방식:**
```bash
# 20개 종목 한 번에 처리 (빠르지만 제한 초과 가능)
python ai_summary_generator.py
```

**권장 방식:**
```bash
# 5개씩 여러 번 나누어 처리
cd us_market
python -c "
from ai_summary_generator import AIStockAnalyzer
analyzer = AIStockAnalyzer()
analyzer.run(top_n=5)  # First 5
"
# 1-2분 대기 후 다시 실행
```

### 방법 4: 배치 처리 간격 조정

**스크립트 수정:** `ai_summary_generator.py`의 `run()` 메서드에서:

```python
# 기존
time.sleep(1)  # 1초 대기

# 권장
time.sleep(5)  # 5초 대기 (속도 제한 방지)
```

### 방법 5: 요금제 확인

**구독 중인 요금제 확인:**
1. [Z.ai 콘솔](https://open.bigmodel.cn/) 로그인
2. **사용자 정보** 또는 **결제** 메뉴
3. 현재 요금제의 QPM(Queries Per Minute) 제한 확인
4. 필요시 상위 요금제로 업그레이드

## 현재 상태

### 적용된 개선사항

✅ **속도 제한 감지 및 재시도 로직**
```python
elif resp.status_code == 429:
    logger.warning("Z.ai API rate limit reached. Waiting 5 seconds...")
    time.sleep(5)
    # 재시도 로직...
```

✅ **요청 간격 추가**
```python
time.sleep(self.min_request_interval)  # 각 요청 후 2초 대기
```

✅ **폴백 체인 유지**
1. Z.ai (1순위)
2. Gemini (2순위)
3. OpenAI (3순위)

## 테스트 결과

```
✅ 인증 성공
✅ API 키 유효
✅ 모델(glm-4-plus) 사용 가능
⚠️  속도 제한(429) 발생
⚠️  재시도 후에도 제한 지속
```

## 권장사항

### 당장 사용하기 위한 방법

**옵션 1: 속도 제한 해제 대기**
```
1분~5분 정도 기다린 후 다시 시도
```

**옵션 2: 소량씩 나누어 처리**
```bash
# 한 번에 3-5개 종목만 처리
python -c "
from ai_summary_generator import AIStockAnalyzer
AIStockAnalyzer().run(top_n=3)
"
```

**옵션 3: 요금제 확인 및 상향**
```
https://open.bigmodel.cn/ 에서
현재 QPM 제한 확인 및 상향 요청
```

### 장기적 해결책

1. **배치 작업 스케줄링**
   - 한 번에 많은 양 처리하지 않기
   - GitHub Actions으로 분산 처리 (예: 1시간마다 5개씩)

2. **요금제 최적화**
   - 필요한 만큼만 사용하는 요금제 선택
   - 비즈니스 요금제로 업그레이드 고려

3. **캐싱 활용**
   - 이미 생성된 AI 요약 재사용
   - 변경된 종목만 다시 생성

## 추가 도움

### Z.ai 지원
- 플랫폼: https://open.bigmodel.cn/
- 문서: https://open.bigmodel.cn/dev/api
- 지원: 콘솔 내 고객센터

### 일반적인 QPM 제한

**무료/plans:**
- 무료: 3-10 QPM
- 베이직: 10-20 QPM
- 프로: 20-50 QPM
- 엔터프라이즈: 100+ QPM

**참고:** QPM = Queries Per Minute (분당 쿼리 수)

## 요약

✅ **API 통합**: 완료
✅ **인증**: 성공
⚠️ **속도 제한**: 활성화됨
🔧 **해결**: 요금제 확인 또는 속도 조정 필요

---

**다음 단계:**
1. [Z.ai 콘솔](https://open.bigmodel.cn/)에서 현재 요금제 확인
2. QPM 제한 확인
3. 필요시 요금제 상향 또는 요청 속도 조정
