# AsKNU Backend Deployment Guide

## 🚀 Render 배포 가이드

### 1. 사전 준비
- [Render.com](https://render.com) 계정 생성 (GitHub 연동 추천)
- GitHub 리포지토리에 코드 푸시 완료
- Supabase 데이터베이스 준비 완료
- Upstage API 키 준비

### 2. Render에서 새 Web Service 생성

#### Step 1: Repository 연결
1. Render 대시보드 접속
2. "New +" 버튼 클릭 → "Web Service" 선택
3. GitHub 리포지토리 연결
4. 배포할 리포지토리 선택

#### Step 2: 기본 설정
```
Name: asknu-backend (또는 원하는 이름)
Region: Singapore (한국과 가장 가까움)
Branch: main (또는 배포할 브랜치)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### Step 3: 환경 변수 설정
Render 대시보드의 "Environment" 탭에서 다음 환경 변수 추가:

```bash
# 필수 환경 변수
DATABASE_URL=postgresql://postgres.czkbauhkrpgpawacaonv:YOUR_PASSWORD@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require
UPSTAGE_API_KEY=up_YOUR_API_KEY
UPSTAGE_MODEL=solar-pro
BASE_BOARD=https://cse.knu.ac.kr/bbs/board.php?bo_table=sub5_1&lang=kor

# 선택 환경 변수
PYTHON_VERSION=3.11
```

#### Step 4: 플랜 선택
- **Free Plan**: 무료 (15분 비활동시 슬립 모드)
- **Starter Plan**: $7/월 (항상 활성, 더 나은 성능)

### 3. 배포 및 확인

#### 자동 배포
- `main` 브랜치에 푸시하면 자동으로 배포됩니다
- 배포 로그는 Render 대시보드에서 실시간 확인 가능

#### 헬스체크
배포 완료 후 다음 URL로 확인:
```
https://your-app-name.onrender.com/health
```

예상 응답:
```json
{"ok": true}
```

#### API 테스트
```bash
# 챗봇 테스트
curl -X POST https://your-app-name.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "경진대회 공지 알려줘"}'

# DB 연결 확인
curl https://your-app-name.onrender.com/db/ping
```

### 4. 배포 후 설정

#### Custom Domain 설정 (선택)
1. Render 대시보드 → Settings → Custom Domain
2. 도메인 추가 및 DNS 설정
3. HTTPS 자동 적용

#### 로그 모니터링
- Render 대시보드 → Logs 탭
- 실시간 로그 확인 가능
- 에러 발생시 즉시 확인

### 5. 주의사항

#### 무료 플랜 제약사항
- 15분 동안 요청이 없으면 슬립 모드
- 첫 요청시 콜드 스타트 (~30초 소요)
- 매월 750시간 무료 (약 31일)

#### 슬립 모드 방지 (선택)
무료 플랜에서 슬립 모드를 방지하려면 외부 크론 서비스 사용:
- [Cron-job.org](https://cron-job.org)
- [UptimeRobot](https://uptimerobot.com)

설정: 매 10분마다 `/health` 엔드포인트 호출

### 6. 환경별 배포

#### Development (개발)
```bash
# 로컬에서 테스트
uvicorn main:app --reload --port 8000
```

#### Staging (스테이징)
```bash
# staging 브랜치 생성 후 별도 Render 서비스 생성
git checkout -b staging
git push origin staging
```

#### Production (프로덕션)
```bash
# main 브랜치에 머지
git checkout main
git merge feature/upstage-solar-migration
git push origin main
```

### 7. 트러블슈팅

#### 배포 실패시
1. 빌드 로그 확인
2. `requirements.txt` 의존성 확인
3. Python 버전 확인 (3.11 권장)

#### DB 연결 오류
1. DATABASE_URL 환경변수 확인
2. Supabase 프로젝트가 활성화되어 있는지 확인
3. 비밀번호 특수문자 URL 인코딩 확인

#### API 응답 느림
1. 무료 플랜 콜드 스타트 문제
2. Starter 플랜으로 업그레이드 고려
3. 또는 크론잡으로 슬립 모드 방지

### 8. 팀원과 협업

#### 환경 변수 공유
`.env.example` 파일을 참고하여 각자 설정:
```bash
cp .env.example .env
# .env 파일 수정 (개인 키 입력)
```

#### 배포 권한 관리
Render 대시보드 → Settings → Team 에서 팀원 초대 가능

### 9. 비용 최적화

#### 무료로 운영
- Render Free Plan (Web Service)
- Supabase Free Plan (PostgreSQL)
- Upstage API Free Tier
- **총 비용: $0/월** ✅

#### 프로덕션 운영
- Render Starter: $7/월
- Supabase Pro: $25/월
- Upstage API: 종량제
- **총 예상 비용: ~$35/월**

### 10. 다음 단계

배포 완료 후:
- [ ] 프론트엔드와 API 연동
- [ ] CORS 설정 (필요시)
- [ ] Rate Limiting 추가
- [ ] 로깅/모니터링 개선
- [ ] API 문서 자동 생성 (FastAPI Swagger)

---

## 📚 추가 자료

- [Render 공식 문서](https://render.com/docs)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Supabase 연결 가이드](https://supabase.com/docs/guides/database/connecting-to-postgres)

## 🆘 문제 발생시

1. Render 대시보드의 Logs 확인
2. `/db/ping` 엔드포인트로 DB 연결 테스트
3. `/health` 엔드포인트로 서버 상태 확인
4. 팀원과 환경 변수 설정 비교

---

**배포 성공을 기원합니다! 🚀**
