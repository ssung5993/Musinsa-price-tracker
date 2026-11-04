"""무신사 상품 가격 수집 스크립트.

products.txt 의 링크마다 상품 페이지를 열어 판매가·정가·할인율을 읽고,
data/prices.json 에 오늘 날짜(한국 시간)로 기록한다. 같은 날 다시 실행하면
그날 기록을 덮어쓴다. 외부 라이브러리 없이 파이썬 표준 라이브러리만 쓴다.
"""

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = ROOT / "products.txt"
DATA_FILE = ROOT / "data" / "prices.json"
KST = timezone(timedelta(hours=9))
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
PRODUCT_RE = re.compile(r"musinsa\.com/products/(\d+)")


def http_get(url: str) -> tuple[str, str]:
    """페이지를 받아 (최종 URL, 본문) 을 돌려준다. 리다이렉트는 자동으로 따라간다."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read().decode("utf-8", errors="replace")
        return res.geturl(), body


def find_product_id(text: str) -> str | None:
    """링크 문자열(인코딩된 것 포함) 안에서 상품번호를 찾는다."""
    for _ in range(3):  # %252F 처럼 여러 번 인코딩된 경우까지 풀어본다
        m = PRODUCT_RE.search(text)
        if m:
            return m.group(1)
        text = urllib.parse.unquote(text)
    return None


def resolve_product_id(link: str) -> str | None:
    pid = find_product_id(link)
    if pid:
        return pid
    # onelink 짧은 링크: 실제로 열어서 최종 주소나 본문에서 상품번호를 찾는다
    try:
        final_url, body = http_get(link)
    except Exception as e:  # noqa: BLE001
        print(f"  ! 링크 열기 실패: {link} ({e})")
        return None
    return find_product_id(final_url) or find_product_id(body)


def meta(body: str, prop: str) -> str | None:
    pattern = (
        r'<meta[^>]+(?:property|name)=["\']' + re.escape(prop) + r'["\'][^>]*content=["\']([^"\']*)["\']'
        r'|<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']' + re.escape(prop) + r'["\']'
    )
    m = re.search(pattern, body)
    if not m:
        return None
    return html.unescape(m.group(1) or m.group(2) or "").strip()


def to_int(v: str | None) -> int | None:
    if v is None:
        return None
    digits = re.sub(r"[^\d]", "", v)
    return int(digits) if digits else None


def fetch_product(pid: str) -> dict | None:
    url = f"https://www.musinsa.com/products/{pid}"
    try:
        _, body = http_get(url)
    except Exception as e:  # noqa: BLE001
        print(f"  ! 상품 페이지 열기 실패: {pid} ({e})")
        return None

    price = to_int(meta(body, "product:price:amount"))
    if price is None:
        print(f"  ! 가격 정보를 못 찾음: {pid} (페이지 구조 변경 또는 접속 차단 가능)")
        return None

    title = meta(body, "og:title") or ""
    title = re.sub(r"\s*-\s*사이즈 & 후기\s*\|\s*무신사\s*$", "", title)
    brand = meta(body, "product:brand") or ""
    return {
        "id": pid,
        "url": url,
        "title": title,
        "brand": brand,
        "image": meta(body, "og:image") or "",
        "price": price,
        "normal_price": to_int(meta(body, "product:price:normal_price")),
        "sale_rate": to_int(meta(body, "product:price:sale_rate")),
        "available": (meta(body, "product:availability") or "") == "주문가능",
    }


def read_links() -> list[str]:
    links = []
    for line in PRODUCTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            links.append(line)
    return links


def main() -> int:
    data = {"updated_at": None, "products": {}}
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    today = datetime.now(KST).strftime("%Y-%m-%d")
    links = read_links()
    print(f"{today} 가격 수집 시작 (상품 {len(links)}개)")

    ok = 0
    active_ids = []
    for link in links:
        pid = resolve_product_id(link)
        if not pid:
            print(f"  ! 상품번호를 찾지 못함: {link}")
            continue
        active_ids.append(pid)
        info = fetch_product(pid)
        time.sleep(2)  # 사이트에 부담 주지 않게 천천히
        if not info:
            continue

        p = data["products"].setdefault(pid, {"history": []})
        p.update({k: info[k] for k in ("id", "url", "title", "brand", "image")})
        p["history"] = [h for h in p["history"] if h["date"] != today]
        p["history"].append({
            "date": today,
            "price": info["price"],
            "normal_price": info["normal_price"],
            "sale_rate": info["sale_rate"],
            "available": info["available"],
        })
        p["history"].sort(key=lambda h: h["date"])
        ok += 1
        print(f"  ✓ {info['brand']} {info['title']}: {info['price']:,}원")

    # products.txt 에서 지운 상품은 기록은 남기고 '추적 중지'로 표시
    for pid, p in data["products"].items():
        p["active"] = pid in active_ids
    data["order"] = active_ids
    data["updated_at"] = datetime.now(KST).isoformat(timespec="minutes")

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료: {ok}/{len(links)}개 기록")
    # 하나도 못 읽었으면 실패로 끝내서 GitHub에서 알림이 오게 한다
    return 0 if ok > 0 or not links else 1


if __name__ == "__main__":
    sys.exit(main())
