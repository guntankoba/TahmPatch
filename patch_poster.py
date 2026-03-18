"""
TahmPatch — patch_poster.py
LoL タグページをスクレイピングし、新しいパッチノートを Discord Webhook に Embed 投稿する。
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

TAG_URL = "https://www.leagueoflegends.com/ja-jp/news/tags/patch-notes/"
LOL_BASE = "https://www.leagueoflegends.com"

PATCH_SELECTORS = [
    'a[href*="/news/game-updates/"][href*="-patch-"]',
    'a[href*="/news/game-updates/"][href*="patch-notes"]',
    'a[href*="/news/game-updates/"]',
]

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
)


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------


def load_state(path: str) -> dict:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_state(path: str, state: dict) -> None:
    Path(path).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# URL utilities
# ---------------------------------------------------------------------------


def to_ja_url(en_url: str) -> str:
    """英語 URL を日本語 URL に変換する。既に ja-jp なら変換不要。"""
    return re.sub(r"/(en-us|en-gb)/", "/ja-jp/", en_url)


def extract_slug(url: str) -> str:
    """URL からパッチノートの slug を取得する。"""
    m = re.search(r"/news/game-updates/([^/]+)/?$", url)
    return m.group(1) if m else url


def _find_patch_href_in_data(data, depth: int = 0) -> str | None:
    """__NEXT_DATA__ を再帰的に探索してパッチノートの href を返す。"""
    if depth > 20:
        return None
    if isinstance(data, dict):
        href = data.get("href", "")
        if isinstance(href, str) and "/news/game-updates/" in href and "patch" in href:
            return href
        for v in data.values():
            found = _find_patch_href_in_data(v, depth + 1)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_patch_href_in_data(item, depth + 1)
            if found:
                return found
    return None


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def fetch_latest_patch_url_from_tag(tag_url: str) -> str:
    """タグページから最新パッチノートの日本語 URL を返す。"""
    print(f"[INFO] タグページ取得: {tag_url}")
    resp = SESSION.get(tag_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Primary: CSS セレクタで探索
    for selector in PATCH_SELECTORS:
        anchors = soup.select(selector)
        if anchors:
            href = anchors[0]["href"]
            if not href.startswith("http"):
                href = LOL_BASE + href
            ja_url = to_ja_url(href)
            print(f"[INFO] Primary セレクタで取得: {ja_url}")
            return ja_url

    # Fallback: __NEXT_DATA__ を解析
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if script_tag and script_tag.string:
        try:
            data = json.loads(script_tag.string)
            href = _find_patch_href_in_data(data)
            if href:
                if not href.startswith("http"):
                    href = LOL_BASE + href
                ja_url = to_ja_url(href)
                print(f"[INFO] Fallback (__NEXT_DATA__) で取得: {ja_url}")
                return ja_url
        except json.JSONDecodeError as e:
            print(f"[WARN] __NEXT_DATA__ JSON パース失敗: {e}", file=sys.stderr)

    raise RuntimeError(f"パッチノート URL を取得できませんでした: {tag_url}")


def fetch_og(url: str) -> dict:
    """URL から OGP メタ情報を取得して返す。"""
    print(f"[INFO] OGP 取得: {url}")
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    def og(prop: str) -> str:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        return (tag.get("content") or "") if tag else ""

    return {
        "title": og("og:title") or og("twitter:title"),
        "description": og("og:description") or og("twitter:description"),
        "image": og("og:image") or og("twitter:image"),
    }


# ---------------------------------------------------------------------------
# Discord Webhook
# ---------------------------------------------------------------------------


def _truncate(text: str, limit: int = 600) -> str:
    if len(text) <= limit:
        return text
    return text[:limit - 1] + "…"


def build_embed(ja_url: str, og: dict) -> dict:
    """Discord Embed オブジェクトを構築する。"""
    slug = extract_slug(ja_url)
    title = og.get("title") or slug.replace("-", " ").title()
    thumbnail_url = os.environ.get("LOL_THUMBNAIL_URL", "")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    embed: dict = {
        "author": {"name": "League of Legends", "url": ja_url},
        "title": title,
        "url": ja_url,
        "description": _truncate(og.get("description") or ""),
        "footer": {"text": f"TahmPatch • {timestamp}"},
        "color": 0xC89B3C,
    }

    image_url = og.get("image", "")
    if image_url:
        embed["image"] = {"url": image_url}

    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}

    return embed


def post_webhook(webhook_url: str, embed: dict) -> None:
    """Discord Webhook に Embed を POST する。"""
    payload = {"embeds": [embed]}
    resp = SESSION.post(webhook_url, json=payload, timeout=30)
    resp.raise_for_status()
    print(f"[INFO] Webhook 投稿成功 (status={resp.status_code})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    state_path = os.environ.get("STATE_FILE_PATH", "state.json")
    dry_run = os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes")

    if not dry_run and not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL が設定されていません。DRY_RUN=true または環境変数を設定してください。")

    state = load_state(state_path)
    last_slug = state.get("last_posted_slug", "")

    latest_url = fetch_latest_patch_url_from_tag(TAG_URL)
    current_slug = extract_slug(latest_url)

    print(f"[INFO] 最新 slug: {current_slug}")
    print(f"[INFO] 前回 slug: {last_slug or '(なし)'}")

    if current_slug == last_slug:
        print("[INFO] 新しいパッチノートはありません。終了します。")
        return

    og = fetch_og(latest_url)
    embed = build_embed(latest_url, og)

    if dry_run:
        print("[DRY_RUN] Embed JSON:")
        print(json.dumps(embed, ensure_ascii=False, indent=2))
        print("[DRY_RUN] Webhook 投稿はスキップされました。state.json も更新しません。")
        return

    post_webhook(webhook_url, embed)

    state["last_posted_slug"] = current_slug
    save_state(state_path, state)
    print(f"[INFO] state.json を更新しました: {current_slug}")


if __name__ == "__main__":
    main()
