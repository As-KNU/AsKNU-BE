# main.py
from dotenv import load_dotenv

load_dotenv()

import os
import asyncio
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from crawler import fetch_html, parse_detail, checksum, collect_all_items
from db import upsert_notice, find_by_query, get_conn
from summarizer import summarize_notice, answer_with_gemini

BASE_BOARD = os.getenv("BASE_BOARD")

app = FastAPI(
    title="AsKNU Backend",
    version="0.2.0",
    description="경북대학교 컴퓨터학부 공지사항 챗봇 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
origins = [
    "https://as-knu-fe.vercel.app",  # 프론트 정식 URL
    "http://localhost:5173",  # 개발용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # "*" 하면 preflight 막힘 → 반드시 리스트로!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    """헬스 체크."""
    return {"ok": True}


@app.get("/db/ping")
def db_ping():
    """DB 연결 확인."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("select 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return {"db": "ok"}
    except Exception as e:
        return {"db": "error", "detail": repr(e)}


@app.post("/refresh")
async def refresh(max_pages: int | None = Query(None, ge=1)):
    """공지 전체/일부 페이지 수집 → 요약 → DB 저장."""
    if not BASE_BOARD:
        raise HTTPException(500, "BASE_BOARD not configured")

    items = await collect_all_items(BASE_BOARD, max_pages=max_pages, delay_sec=0.4)
    saved, skipped, errors = 0, 0, []

    for it in items:
        try:
            detail_html = await fetch_html(it["url"])
            content, posted_at = parse_detail(detail_html)
            if not content or len(content) < 30:
                skipped += 1
                if len(errors) < 5:
                    errors.append({"url": it.get("url"), "error": "content_too_short"})
                continue

            summary = await summarize_notice(it["title"], content)
            upsert_notice(
                {
                    "url": it["url"],
                    "title": it["title"],
                    "content": content,
                    "posted_at": posted_at,
                    "summary": summary,
                    "checksum": checksum(content),
                }
            )
            saved += 1
            await asyncio.sleep(0.2)
        except Exception as e:
            skipped += 1
            if len(errors) < 5:
                errors.append({"url": it.get("url"), "error": repr(e)})

    return {
        "status": "ok",
        "saved": saved,
        "skipped": skipped,
        "count": len(items),
        "sample_errors": errors,
    }


@app.get("/notices/search")
def search(q: str = Query(..., min_length=1), limit: int = 5, years: int = 3):
    """키워드 검색(제목 우선·최신순)."""
    rows = find_by_query(q, limit=limit, since_years=years)
    return {"results": rows}


@app.post("/chat")
async def chat(payload: ChatRequest, years: int = 3):
    """질문 → 검색 상위 N → Gemini로 답변 생성."""
    rows = find_by_query(payload.question, limit=5, since_years=years)
    if not rows:
        return {
            "answer": "관련 공지를 찾지 못했어요. 키워드를 바꿔보거나 담당자에게 문의하세요.",
            "citations": [],
        }

    answer = await answer_with_gemini(payload.question, rows)
    citations = [
        {
            "title": r["title"],
            "url": r["url"],
            "posted_at": r["posted_at"],
            "summary": r.get("summary") or "",
        }
        for r in rows
    ]
    return {"answer": answer, "citations": citations}
