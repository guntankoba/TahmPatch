# TahmPatch Technical Plan — 001: Webhook Poster

## Architecture

```
GitHub Actions (cron 6h)
    └── python patch_poster.py
            ├── load_state(state.json)        # last_posted_slug 読み込み
            ├── fetch_latest_patch_url(tag)    # LoL タグページスクレイプ
            │       ├── Primary: CSS セレクタ
            │       └── Fallback: __NEXT_DATA__ JSON
            ├── slug 比較 → 同じなら EXIT 0
            ├── fetch_og(ja_url)               # og メタ取得
            ├── post_webhook(webhook_url, embed) # Discord 投稿
            └── save_state(state.json)         # 成功時のみ
```

## Implementation Details

### patch_poster.py の関数設計

```python
def load_state(path: str) -> dict
def save_state(path: str, state: dict) -> None
def to_ja_url(en_url: str) -> str  # /en-us/ → /ja-jp/
def fetch_latest_patch_url_from_tag(tag_url: str) -> str
def fetch_og(url: str) -> dict  # title/desc/image
def post_webhook(webhook_url: str, embed: dict) -> None
def main() -> None
```

### スクレイピング戦略

**Primary セレクタ候補（順に試す）：**
```
a[href*="/news/game-updates/"][href*="-patch-"]
a[href*="/news/game-updates/"][href*="patch-notes"]
a[href*="/news/game-updates/"]
```

**Fallback（__NEXT_DATA__）：**
```python
data = json.loads(soup.find("script", id="__NEXT_DATA__").string)
# data["props"]["pageProps"]["page"]["modules"] を再帰探索
# href に "/news/game-updates/" を含む最初のリンク
```

### state.json 形式

```json
{"last_posted_slug": "league-of-legends-patch-25-6-notes"}
```

## Dependencies

```
requests>=2.32.0        # HTTP リクエスト
beautifulsoup4>=4.12.0  # HTML パース
```

## GitHub Actions ワークフロー設計

- トリガー: `schedule: "0 */6 * * *"` + `workflow_dispatch`
- Python: 3.11
- permissions: `contents: write`（state.json コミット用）
- Secrets: `DISCORD_WEBHOOK_URL`、`LOL_THUMBNAIL_URL`
- state.json 変更時のみ `git commit & push`
