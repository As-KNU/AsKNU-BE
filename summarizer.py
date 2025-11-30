# summarizer.py

import os, re, textwrap
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import anyio

API_KEY = os.getenv("UPSTAGE_API_KEY")
MODEL_NAME = os.getenv("UPSTAGE_MODEL", "solar-pro")

QA_TMPL = """\
당신은 '경북대학교 컴퓨터학부 행정 안내 챗봇 AsKNU'입니다.

아래 '관련 자료'를 참고하여 사용자 질문에 대해
학생이 보기 쉽게 한국어로 안내문을 작성하세요.

### 출력 규칙
- 마크다운 굵기(**) 또는 기울임(*) 절대 사용 금지
- 오직 순수 텍스트만 사용
- 다음 구조로 고정하여 출력:

[요약 안내]
(한 줄로 핵심 요약)

[일정]
- 항목들…

[필요서류]
- 항목들… (있을 때만)

[관련 공지]
- 제목 
(URL)
- 제목 
(URL)

### 주의사항
- 자료에 없는 내용은 추측하지 말고 "자료에서 확인되지 않습니다"라고 답하세요.
- 날짜는 YYYY.MM.DD 형태로 표기하세요.

[사용자 질문]
{question}

[관련 자료]
{contexts}
"""


def _format_contexts(rows):
    blocks = []
    for r in rows:
        blocks.append(
            f"- 제목: {r['title']}\n  요약: {r.get('summary') or ''}\n  링크: {r['url']}"
        )
    return "\n".join(blocks)


def _answer_sync(question: str, rows: list[dict]) -> str:
    client = _ensure_client()
    prompt = QA_TMPL.format(
        question=question.strip(),
        contexts=_format_contexts(rows)[:12000],
    )
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "당신은 대학 학부 행정 안내 전문 챗봇입니다.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


async def answer_with_gemini(question: str, rows: list[dict]) -> str:
    """Solar Pro로 질문 답변 생성 (함수명은 호환성을 위해 유지)"""
    try:
        return await anyio.to_thread.run_sync(_answer_sync, question, rows)
    except Exception:
        bullets = "\n".join([f"- {r['title']} ({r['url']})" for r in rows])
        return f"아래 공지가 도움이 될 수 있어요:\n{bullets}"


def _clean_for_summary(text: str) -> str:
    text = re.sub(r"본문[\s\S]*?댓글목록", "", text)
    bad = ["이전글", "다음글", "댓글목록", "페이지 정보"]
    lines = [ln for ln in text.splitlines() if not any(b in ln for b in bad)]
    text = " ".join(lines)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _ensure_client():
    if not API_KEY:
        raise RuntimeError("UPSTAGE_API_KEY not set")
    return OpenAI(api_key=API_KEY, base_url="https://api.upstage.ai/v1/solar")


PROMPT_TMPL = """\
다음은 대학 공지사항 원문입니다. 한국어로 간결한 요약을 만들어 주세요.

요건:
- 제목의 핵심어를 포함해 2~4문장으로 요약
- 일시/장소/대상/신청방법/마감일 등 실무 핵심만 추림
- 불필요한 머리말(페이지 정보/이전글/다음글/댓글목록/목록)은 절대 포함하지 않음
- 결과는 마크다운 없이 평문

제목: {title}

원문:
{text}
"""


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.8, min=1, max=8),
    retry=retry_if_exception_type(Exception),
)
def _summarize_sync(title: str, content: str) -> str:
    client = _ensure_client()
    cleaned = _clean_for_summary(content)
    if not cleaned:
        cleaned = content[:8000]
    prompt = PROMPT_TMPL.format(title=title.strip(), text=cleaned[:12000])

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "당신은 대학 공지사항을 간결하게 요약하는 전문가입니다.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    text = response.choices[0].message.content.strip()

    text = _clean_for_summary(text)

    if len(text) < 20:
        snippet = cleaned[:300] + ("…" if len(cleaned) > 300 else "")
        text = snippet
    return text


async def summarize_notice(title: str, content: str) -> str:
    """
    동기 SDK를 스레드로 실행.
    """
    try:
        summary = await anyio.to_thread.run_sync(_summarize_sync, title, content)
        return f"[요약] {title}\n- {summary}"
    except Exception:
        cleaned = _clean_for_summary(content)
        snippet = (cleaned[:300] + "…") if len(cleaned) > 300 else cleaned
        return f"[요약] {title}\n- {snippet}"
