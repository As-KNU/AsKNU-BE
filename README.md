# AsKNU Backend

경북대학교 컴퓨터학부 공지사항 챗봇 백엔드 API 서버

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📌 프로젝트 소개

AsKNU는 경북대학교 컴퓨터학부의 공지사항을 크롤링하고, AI를 활용하여 사용자의 질문에 답변하는 챗봇 서비스입니다.

### 주요 기능
- 🔍 **공지사항 크롤링**: 컴퓨터학부 공지사항 자동 수집
- 🤖 **AI 챗봇**: Upstage Solar Pro를 활용한 한국어 최적화 답변
- 📊 **검색 시스템**: 키워드 기반 공지사항 검색
- 🗄️ **데이터베이스**: PostgreSQL (Supabase) 연동
- 📝 **요약 기능**: 공지사항 자동 요약

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.11+
- PostgreSQL (또는 Supabase)
- Upstage API Key

### 설치 및 실행

1. **저장소 클론**
```bash
git clone https://github.com/your-org/AsKNU-BE.git
cd AsKNU-BE
```

2. **가상환경 생성 및 활성화**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경변수 설정**
```bash
cp .env.example .env
# .env 파일을 열어서 실제 값으로 수정
```

5. **서버 실행**
```bash
uvicorn main:app --reload --port 8000
```

6. **API 문서 확인**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API 엔드포인트

### 기본
- `GET /health` - 헬스체크
- `GET /db/ping` - 데이터베이스 연결 확인

### 공지사항
- `POST /refresh?max_pages={n}` - 공지사항 크롤링 및 저장
- `GET /notices/search?q={keyword}&limit={n}&years={n}` - 공지사항 검색

### 챗봇
- `POST /chat` - AI 챗봇 질문/답변
  ```json
  {
    "question": "최근 경진대회 공지 알려줘"
  }
  ```

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 Python 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증

### AI & NLP
- **Upstage Solar Pro**: 한국어 특화 LLM
- **OpenAI SDK**: API 클라이언트

### Database
- **PostgreSQL**: 관계형 데이터베이스
- **Supabase**: 클라우드 PostgreSQL
- **psycopg2**: PostgreSQL 어댑터

### Crawling
- **httpx**: 비동기 HTTP 클라이언트
- **BeautifulSoup4**: HTML 파싱
- **lxml**: XML/HTML 처리

### Utilities
- **python-dotenv**: 환경변수 관리
- **python-dateutil**: 날짜 처리
- **tenacity**: 재시도 로직

## 📁 프로젝트 구조

```
AsKNU-BE/
├── main.py              # FastAPI 앱 및 라우터
├── crawler.py           # 공지사항 크롤링
├── db.py               # 데이터베이스 연동
├── summarizer.py       # AI 요약 및 답변
├── cleanup_dates.py    # DB 정리 스크립트
├── requirements.txt    # 의존성 목록
├── .env.example        # 환경변수 템플릿
├── .gitignore          # Git 제외 파일
├── SETUP.md           # 개발 환경 설정 가이드
├── DEPLOYMENT.md      # 배포 가이드
└── README.md          # 프로젝트 문서
```

## 🌐 배포

### Render 배포 (추천)
자세한 내용은 [DEPLOYMENT.md](DEPLOYMENT.md) 참조

```bash
# 1. Render.com 계정 생성
# 2. GitHub 리포지토리 연결
# 3. 환경변수 설정
# 4. 자동 배포 시작
```

### 로컬 개발
```bash
# 개발 서버 실행 (핫 리로드)
uvicorn main:app --reload --port 8000

# 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔧 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql://user:pass@host:port/db` |
| `UPSTAGE_API_KEY` | Upstage API 키 | `up_xxxxxxxxxxxxx` |
| `UPSTAGE_MODEL` | 사용할 모델 | `solar-pro` |
| `BASE_BOARD` | 크롤링할 게시판 URL | `https://cse.knu.ac.kr/...` |

## 🧪 테스트

```bash
# 헬스체크
curl http://localhost:8000/health

# DB 연결 확인
curl http://localhost:8000/db/ping

# 챗봇 테스트
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "경진대회 공지 알려줘"}'
```

## 📊 데이터베이스 스키마

```sql
CREATE TABLE notices (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) DEFAULT 'cse',
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    posted_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    summary TEXT,
    checksum VARCHAR(64)
);
```

## 🤝 기여 가이드

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 변경 이력

### v0.2.0 (2025-11-30)
- ✨ Gemini → Upstage Solar Pro 마이그레이션
- 🔧 날짜 검증 로직 추가
- 🔍 검색 기능 개선
- 📚 배포 가이드 추가
- 🌐 CORS 설정 추가

### v0.1.0 (Initial Release)
- 🎉 초기 공지사항 챗봇 기능 구현
- 🔍 크롤링 및 검색 기능
- 🤖 Gemini API 통합

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 팀

- **Backend Team**: AsKNU 백엔드 개발팀
- **Contact**: [이메일 주소]

## 🙏 감사의 말

- 경북대학교 컴퓨터학부
- Upstage Solar API
- FastAPI Community

---

**Made with ❤️ by AsKNU Team**
