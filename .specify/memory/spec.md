# TahmPatch Spec — 001: Webhook Poster

## Overview

LoL タグページを定期スクレイピングし、新しいパッチノートを Discord Webhook に Embed 投稿する。
旧 Discord Bot + Railway 方式を廃止し、GitHub Actions + Webhook 方式に移行する。

## Background

**現状:** Discord Bot として Railway 上で常時稼働。patchbot メッセージを監視して日本語 URL を返信。
**課題:** Railway の費用・管理コスト、Bot 権限が必要、patchbot 依存。
**新方式:** GitHub Actions (6h ポーリング) でタグページを直接スクレイピング → Discord Webhook に Embed 投稿。

## Functional Requirements

### FR-1: パッチノート URL 取得
- LoL タグページ（`https://www.leagueoflegends.com/ja-jp/news/tags/patch-notes/`）から最新パッチノート URL を取得する
- Primary: `a[href]` の CSS セレクタでパッチノートリンクを抽出
- Fallback: `<script id="__NEXT_DATA__">` JSON を解析してリンクを取得
- 両方失敗時は `RuntimeError` を発生させる

### FR-2: 二重投稿防止
- `state.json` の `last_posted_slug` と比較して新規パッチのみ投稿する
- 投稿成功後のみ `state.json` を更新・コミットする

### FR-3: Discord Embed 投稿
```
author: {name: "League of Legends", url: latest_ja}
title: og:title（または slug から生成）
url: latest_ja
description: og:description（600字で truncate）
image: og:image
thumbnail: LOL_THUMBNAIL_URL 環境変数（任意）
footer: "TahmPatch • <UTC timestamp>"
```

### FR-4: DRY_RUN モード
- `DRY_RUN=true` の場合、Embed JSON を標準出力に表示するのみで Webhook 投稿しない
- DRY_RUN 時は state.json を更新しない

## Non-Functional Requirements

### NFR-1: スケジュール実行
GitHub Actions schedule で6時間ごとに自動実行。
手動実行（workflow_dispatch）も可能。

### NFR-2: ステートレス設計
state.json 以外の外部状態を持たない。

## Environment Variables

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `DISCORD_WEBHOOK_URL` | 必須 | - | Discord Webhook URL |
| `LOL_THUMBNAIL_URL` | 任意 | - | Embed サムネイル画像 URL |
| `STATE_FILE_PATH` | 任意 | `state.json` | state ファイルパス |
| `DRY_RUN` | 任意 | `false` | true の場合 Webhook 投稿しない |

## Files to Add/Modify/Delete

| ファイル | 操作 | 理由 |
|---------|------|------|
| `patch_poster.py` | 新規 | メインスクリプト |
| `.github/workflows/patch_poster.yml` | 新規 | GitHub Actions ワークフロー |
| `requirements.txt` | 更新 | discord.py/aiohttp → requests/beautifulsoup4 |
| `README.md` | 更新 | 新アーキテクチャ説明 |
| `bot.py` | 削除 | 旧アーキテクチャ廃止 |
| `Procfile` | 削除 | Railway 不要 |
| `railway.json` | 削除 | Railway 不要 |

## Acceptance Criteria

- [ ] `DRY_RUN=true python patch_poster.py` で Embed JSON が標準出力に表示される
- [ ] Webhook URL 設定時に Discord に Embed が投稿される
- [ ] 2回目以降の実行で同じパッチが再投稿されない（state.json チェック）
- [ ] GitHub Actions が6時間ごとに実行される
- [ ] 投稿後に state.json が自動コミットされる
