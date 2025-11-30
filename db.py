# db.py
import os
import re
import datetime as dt

import psycopg2
from dateutil.relativedelta import relativedelta
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

STOPWORDS = {
    "공지",
    "공지사항",
    "안내",
    "알려줘",
    "알려주세요",
    "문의",
    "학생",
    "모집",
    "참여",
    "참가하고",
    "참가",
    "학기",
    "학부",
    "대학",
    "교내",
    "교외",
    "관련",
    "제출",
    "있어",
    "있는",
    "있나",
    "뭐가",
    "싶은데",
    "최근",
    "또는",
    "개최된",
}


def _split_tokens(q: str):
    """질의어 토큰 분리(소문자)."""
    return re.findall(r"[가-힣a-z0-9]+", q.lower())


def _strong_tokens(q: str):
    """불용어 제외한 강한 토큰만 반환. 전부 불용어면 원토큰 반환."""
    toks = _split_tokens(q)
    strong = [t for t in toks if t not in STOPWORDS]
    return strong or toks


def get_conn():
    """DB 커넥션 생성."""
    return psycopg2.connect(DATABASE_URL)


def upsert_notice(n: dict):
    """공지 UPSERT(요약/본문/날짜 갱신)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO notices (source, url, title, content, posted_at, updated_at, summary, checksum)
        VALUES ('cse', %(url)s, %(title)s, %(content)s, %(posted_at)s, now(), %(summary)s, %(checksum)s)
        ON CONFLICT (url) DO UPDATE SET
          title = EXCLUDED.title,
          content = EXCLUDED.content,
          posted_at = COALESCE(EXCLUDED.posted_at, notices.posted_at),
          updated_at = now(),
          summary = EXCLUDED.summary,
          checksum = EXCLUDED.checksum
        """,
        n,
    )
    conn.commit()
    cur.close()
    conn.close()


def find_by_query(q: str, limit=10, since_years: int = 3, include_past: bool = True):
    """강한 토큰 AND 매칭 + 제목 우선 + 최신순."""
    strong = _strong_tokens(q)
    params = {"limit": limit}

    # AND: 각 강한 토큰이 제목 또는 본문 중 하나에는 반드시 포함
    and_clauses = []
    for i, tok in enumerate(strong):
        and_clauses.append(f"(title ILIKE %(t{i})s OR content ILIKE %(c{i})s)")
        params[f"t{i}"] = f"%{tok}%"
        params[f"c{i}"] = f"%{tok}%"

    # 날짜 필터링
    cutoff = dt.datetime.now() - relativedelta(years=since_years)
    and_clauses.append("posted_at >= %(cutoff)s")
    params["cutoff"] = cutoff

    # 과거 공지 제외 옵션 (미래 또는 최근 공지만)
    if not include_past:
        and_clauses.append("posted_at >= %(now)s")
        params["now"] = dt.datetime.now()

    where_sql = " AND ".join(and_clauses) if and_clauses else "TRUE"

    title_hits = (
        " + ".join(
            [
                f"(CASE WHEN title ILIKE %(t{i})s THEN 1 ELSE 0 END)"
                for i, _ in enumerate(strong)
            ]
        )
        or "0"
    )

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        f"""
        SELECT id, title, url, summary, posted_at, updated_at,
               ({title_hits}) AS in_title_score
        FROM notices
        WHERE {where_sql}
        ORDER BY
          in_title_score DESC,           -- 제목에 강한 토큰 있을수록 우선
          posted_at DESC NULLS LAST,     -- 최신 공지 우선
          updated_at DESC                -- 보조
        LIMIT %(limit)s
    """,
        params,
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_notice_full(id_: int):
    """단건 상세 조회."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM notices WHERE id=%s", (id_,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row
