#!/usr/bin/env python3
"""
날짜 데이터 정리 스크립트
- 미래 날짜 (2026년 이후) 삭제
- 너무 오래된 날짜 (2010년 이전) 삭제
"""

from dotenv import load_dotenv

load_dotenv()

import psycopg2
from db import get_conn


def cleanup_invalid_dates():
    """이상한 날짜 데이터 정리"""
    conn = get_conn()
    cur = conn.cursor()

    # 현재 통계 확인
    print("📊 정리 전 통계:")
    cur.execute(
        """
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN EXTRACT(YEAR FROM posted_at) >= 2026 THEN 1 END) as future,
            COUNT(CASE WHEN EXTRACT(YEAR FROM posted_at) < 2010 THEN 1 END) as too_old,
            COUNT(CASE WHEN posted_at IS NULL THEN 1 END) as null_dates
        FROM notices
    """
    )
    stats = cur.fetchone()
    print(f"  총 공지: {stats[0]:,}개")
    print(f"  미래 날짜 (>=2026): {stats[1]:,}개")
    print(f"  너무 오래된 날짜 (<2010): {stats[2]:,}개")
    print(f"  날짜 없음: {stats[3]:,}개")
    print()

    # 미래 날짜 삭제 (2026년 포함)
    print("🗑️  미래 날짜 (2026년 이후) 삭제 중...")
    cur.execute("DELETE FROM notices WHERE EXTRACT(YEAR FROM posted_at) >= 2026")
    deleted_future = cur.rowcount
    print(f"  ✅ {deleted_future}개 삭제됨")

    # 너무 오래된 날짜 삭제
    print("🗑️  너무 오래된 날짜 (2010년 이전) 삭제 중...")
    cur.execute("DELETE FROM notices WHERE EXTRACT(YEAR FROM posted_at) < 2010")
    deleted_old = cur.rowcount
    print(f"  ✅ {deleted_old}개 삭제됨")

    # 날짜 없는 공지 삭제 (선택사항)
    # print("🗑️  날짜 없는 공지 삭제 중...")
    # cur.execute("DELETE FROM notices WHERE posted_at IS NULL")
    # deleted_null = cur.rowcount
    # print(f"  ✅ {deleted_null}개 삭제됨")

    conn.commit()

    # 정리 후 통계
    print()
    print("📊 정리 후 통계:")
    cur.execute(
        """
        SELECT 
            COUNT(*) as total,
            MIN(posted_at) as oldest,
            MAX(posted_at) as newest
        FROM notices
        WHERE posted_at IS NOT NULL
    """
    )
    stats = cur.fetchone()
    print(f"  총 공지: {stats[0]:,}개")
    print(f"  가장 오래된 공지: {stats[1]}")
    print(f"  가장 최근 공지: {stats[2]}")

    # 연도별 분포
    print()
    print("📅 연도별 분포 (2010년 이후):")
    cur.execute(
        """
        SELECT 
            EXTRACT(YEAR FROM posted_at) as year,
            COUNT(*) as count
        FROM notices
        WHERE posted_at IS NOT NULL
          AND EXTRACT(YEAR FROM posted_at) >= 2010
        GROUP BY EXTRACT(YEAR FROM posted_at)
        ORDER BY year DESC
        LIMIT 10
    """
    )
    for row in cur.fetchall():
        print(f"  {int(row[0])}년: {row[1]:,}개")

    cur.close()
    conn.close()

    print()
    print("✅ 데이터 정리 완료!")


if __name__ == "__main__":
    cleanup_invalid_dates()
