# AsKNU 설정 가이드

## ✅ 완료된 작업

Gemini에서 **Upstage Solar Pro** 모델로 성공적으로 전환되었습니다!

## 🔑 필요한 설정

### 1. Upstage API 키 발급

1. [Upstage Console](https://console.upstage.ai/)에 접속
2. 회원가입 및 로그인
3. API Keys 메뉴에서 새 API 키 생성
4. 생성된 API 키 복사

### 2. 환경 변수 설정

`.env` 파일에서 `UPSTAGE_API_KEY`를 실제 키로 변경하세요:

```env
# .env 파일
UPSTAGE_API_KEY=up_xxxxxxxxxxxxxxxxxxxxx  # 여기에 실제 Upstage API 키 입력
UPSTAGE_MODEL=solar-pro
```

### 3. 서버 재시작

환경 변수 변경 후 서버를 재시작하세요:

```bash
# 터미널에서 Ctrl+C로 서버 중지 후
cd /Users/leejeongmin/Python/경진대회
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 변경 사항

### 수정된 파일

1. **summarizer.py**
   - `google.generativeai` → `openai` (Upstage는 OpenAI 호환 API 사용)
   - `GEMINI_API_KEY` → `UPSTAGE_API_KEY`
   - `gemini-1.5-flash` → `solar-pro`
   - API 엔드포인트: `https://api.upstage.ai/v1/solar`

2. **requirements.txt**
   - `google-generativeai` → `openai`

3. **.env**
   - Gemini 설정 → Upstage 설정

## 🚀 Solar Pro 장점

- ✅ **더 정확한 한국어 처리**: Upstage는 한국어에 특화된 모델
- ✅ **안정적인 성능**: 무료 티어 제한이 Gemini보다 관대함
- ✅ **빠른 응답 속도**: 최적화된 추론 엔진
- ✅ **긴 컨텍스트 지원**: 더 많은 공지사항 내용 처리 가능

## 🔍 테스트 방법

서버 실행 후 브라우저에서 테스트:

```
http://localhost:8000/docs
```

1. `/chat` 엔드포인트 선택
2. "Try it out" 클릭
3. Request body에 질문 입력:
   ```json
   {
     "question": "장학금 신청 방법 알려줘"
   }
   ```
4. Execute 클릭

## ⚠️ 주의사항

- Upstage API 키가 설정되지 않으면 `UPSTAGE_API_KEY not set` 에러 발생
- 무료 티어 한도 확인: [Upstage Pricing](https://console.upstage.ai/pricing)
- API 사용량 모니터링: [Upstage Console](https://console.upstage.ai/)

## 📝 백업

이전 Gemini 설정으로 되돌리고 싶다면:
1. `.env`에서 `GEMINI_API_KEY` 복원
2. `summarizer.py`를 git에서 복원
3. `requirements.txt`에 `google-generativeai` 추가
4. `pip install google-generativeai`
