# TahmPatch

League of Legends の最新パッチノートを Discord に自動通知するツール。

GitHub Actions が6時間ごとに LoL 公式タグページをスクレイピングし、新しいパッチノートを Discord Webhook に Embed 投稿する。

## 動作概要

```
GitHub Actions (cron: 6時間ごと)
    ↓
patch_poster.py
    ├── state.json から last_posted_slug を読み込む
    ├── LoL タグページをスクレイピング（Primary: CSS / Fallback: __NEXT_DATA__）
    ├── slug が変わっていなければ終了（二重投稿防止）
    ├── パッチノートページから OGP 情報を取得
    ├── Discord Webhook に Embed 投稿
    └── state.json を更新・コミット
```

## 環境変数

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `DISCORD_WEBHOOK_URL` | **必須** | — | Discord Webhook URL |
| `LOL_THUMBNAIL_URL` | 任意 | — | Embed サムネイル画像 URL |
| `STATE_FILE_PATH` | 任意 | `state.json` | state ファイルパス |
| `DRY_RUN` | 任意 | `false` | `true` の場合 Webhook 投稿しない |

## GitHub Secrets 設定

リポジトリの **Settings → Secrets and variables → Actions** で以下を設定：

| Secret 名 | 内容 |
|-----------|------|
| `DISCORD_WEBHOOK_URL` | Discord チャンネルの Webhook URL |
| `LOL_THUMBNAIL_URL` | （任意）Embed サムネイル画像 URL |

## ローカルでのテスト

```bash
# 仮想環境セットアップ
uv venv
uv pip sync requirements.txt
source .venv/bin/activate

# DRY_RUN で Embed JSON を確認（Webhook 投稿なし）
DRY_RUN=true python patch_poster.py

# 実投稿テスト
DISCORD_WEBHOOK_URL=<your_webhook_url> python patch_poster.py
```

## 手動実行

GitHub Actions の **Actions タブ → Patch Poster → Run workflow** から手動実行可能。

## アーキテクチャ詳細

- **スクレイピング戦略:** Primary（CSS セレクタ）→ Fallback（`__NEXT_DATA__` JSON）の2段階
- **二重投稿防止:** `state.json` の `last_posted_slug` と比較
- **投稿成功後のみ** `state.json` を更新（失敗時は次回自動リトライ）
- **依存ライブラリ:** `requests`, `beautifulsoup4` のみ
