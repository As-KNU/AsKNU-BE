# crawler.py
import asyncio
import hashlib
import re, datetime as dt
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import httpx
from bs4 import BeautifulSoup

LIST_URL = "https://cse.knu.ac.kr/bbs/board.php?bo_table=sub5_1&lang=kor"
HEADERS = {
    "User-Agent": "AsKNUCrawler/1.0 (+https://asknu.local)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko,en;q=0.8",
    "Connection": "keep-alive",
}

NAV_SELECTORS = [
    "#bo_v_nb", ".bo_v_nb", ".prev_next", ".btn_nextprv",
    ".bo_v_info", "#bo_v_info", ".bo_v_category",
    "#bo_vc", ".bo_vc", ".cmt", "#comment", ".bo_vc_w",
]
CONTENT_SELECTORS = [
    "#bo_v_con", ".bo_v_con", "#bo_v_atc", ".bo_v_atc",
    ".view_content", ".bo_view", "article#bo_v",
]


def checksum(text: str) -> str:
    """본문 체크섬(SHA1)."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


async def fetch_html(url: str) -> str:
    """URL GET(리다이렉트 허용)."""
    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


def _normalize_spaces(s: str) -> str:
    """공백/줄바꿈 정규화."""
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\n+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def _strip_between_markers(text: str, start_mark="본문", end_mark="댓글목록") -> str:
    """마커 구간(본문~댓글목록) 제거."""
    pattern = re.compile(rf"{re.escape(start_mark)}[\s\S]*?{re.escape(end_mark)}", re.M)
    return pattern.sub("", text)


def parse_list(html: str):
    """목록 페이지에서 게시글 링크 추출."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    candidates = [
        "table.bo_list td.td_subject a",
        ".bo_list .td_subject a",
        ".bo_list .wr_subject a",
        ".list_subject a",
        ".bo_tit a",
        ".list td.subject a",
        ".tbl_head01 tbody tr .subject a",
    ]
    for sel in candidates:
        for a in soup.select(sel):
            href = a.get("href") or ""
            title = a.get_text(strip=True)
            if "wr_id=" in href and title:
                links.append({"title": title, "url": urljoin(LIST_URL, href)})
        if links:
            break

    if not links:  # 백업 경로
        for a in soup.find_all("a", href=True):
            href = a["href"]; title = a.get_text(strip=True)
            if "wr_id=" in href and title:
                links.append({"title": title, "url": urljoin(LIST_URL, href)})

    uniq = {x["url"]: x for x in links}
    return list(uniq.values())


def _with_page(url: str, page: int) -> str:
    """LIST_URL에 page 파라미터 설정."""
    u = urlparse(url)
    qs = parse_qs(u.query, keep_blank_values=True)
    qs["page"] = [str(page)]
    return urlunparse((u.scheme, u.netloc, u.path, u.params, urlencode(qs, doseq=True), u.fragment))


def parse_last_page(html: str) -> int | None:
    """페이지네이션의 최대 페이지 추정."""
    soup = BeautifulSoup(html, "lxml")
    for sel in [".pg_page", ".pagination", ".pg", ".pg_wrap", ".page"]:
        nums = [int(a.get_text(strip=True)) for a in soup.select(f"{sel} a") if a.get_text(strip=True).isdigit()]
        if nums:
            return max(nums)
    return None


async def collect_all_items(base_url: str, max_pages: int | None = None, delay_sec: float = 0.4):
    """전체/일부 페이지 순회하여 링크 수집."""
    items_map = {}
    first_html = await fetch_html(base_url)
    for it in parse_list(first_html):
        items_map[it["url"]] = it

    last_page = parse_last_page(first_html)
    target_last = (1 + max(0, (max_pages or 1) - 1)) if max_pages else (last_page or 999_999)

    page = 2
    while page <= target_last:
        html = await fetch_html(_with_page(base_url, page))
        page_items = parse_list(html)
        if not page_items:
            break
        added = 0
        for it in page_items:
            if it["url"] not in items_map:
                items_map[it["url"]] = it
                added += 1
        if added == 0:
            break  # 고정글 중복 방지
        page += 1
        if delay_sec:
            await asyncio.sleep(delay_sec)

    return list(items_map.values())


def parse_detail(html: str, return_meta: bool = False):
    """상세 페이지에서 본문/게시일 추출 및 클린업."""
    soup = BeautifulSoup(html, "lxml")

    used_selector, content_el = None, None
    for sel in CONTENT_SELECTORS:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            content_el, used_selector = el, sel
            break
    if not content_el:
        content_el = soup.select_one("main") or soup.select_one("article") or soup.select_one("section") or soup
        used_selector = used_selector or "(fallback)"

    for bad_sel in NAV_SELECTORS:
        for tag in content_el.select(bad_sel):
            tag.decompose()

    for sib in content_el.find_all_next():
        if sib.name in ("div", "ul"):
            sid = sib.get("id", "")
            cls = " ".join(sib.get("class", []))
            if any(k in sid for k in ["bo_v_nb", "bo_vc", "comment"]) or any(k in cls for k in ["bo_v_nb", "prev_next", "btn_nextprv", "bo_vc"]):
                sib.decompose()

    raw_text = content_el.get_text("\n", strip=True)
    lines = [ln for ln in raw_text.splitlines() if not any(b in ln for b in ["이전글", "다음글", "댓글목록", "페이지 정보"])]
    text = _normalize_spaces(_strip_between_markers("\n".join(lines), "본문", "댓글목록"))
    if len(text) < 80 and len(raw_text) > len(text):
        text = _normalize_spaces(raw_text)

    page_text = soup.get_text(" ", strip=True)
    m = re.search(r"(20\d{2})[.\-/년 ]\s?(\d{1,2})[.\-/월 ]\s?(\d{1,2})", page_text)
    posted_at = None
    if m:
        y, mo, d = map(int, m.groups())
        try:
            posted_at = dt.datetime(y, mo, d)
        except:
            posted_at = None

    return (text, posted_at, {"selector": used_selector}) if return_meta else (text, posted_at)