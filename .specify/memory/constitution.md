# TahmPatch Constitution

## Core Principles

### I. Serverless-First
GitHub Actions を唯一の実行基盤とする。常時稼働サーバー（Railway、Bot）は使わない。
スクレイピング・投稿のすべてを単一スクリプト `patch_poster.py` で完結させる。

### II. Idempotency（冪等性）
`state.json` の `last_posted_slug` で二重投稿を防止する。
同じパッチノートが複数回実行されても投稿は1回のみ。
投稿成功後のみ state を更新する（失敗時は次回リトライ可能）。

### III. Robustness（堅牢スクレイピング）
Primary + Fallback の2段階でリンクを取得する。
- Primary: CSS セレクタ（`a[href]`）でパッチノートリンクを抽出
- Fallback: `<script id="__NEXT_DATA__">` の JSON を解析
どちらも失敗した場合のみ RuntimeError を発生させる。

### IV. Simplicity（YAGNI）
必要最小限の依存ライブラリ（requests, beautifulsoup4）のみ使用。
設定は環境変数で完結させ、設定ファイルは作らない。
過剰な抽象化・将来のための設計は行わない。

### V. Observability
標準出力への構造化ログで GitHub Actions のログから動作を追跡可能にする。
DRY_RUN モードで本番投稿なしにローカルで動作確認できること。

## Branch & Commit Rules

- `main` への直接プッシュ禁止
- フィーチャーブランチ → PR → squash merge
- ブランチ番号は仕様書番号と対応（例: `001-webhook-poster`）
- Conventional Commits 形式を必須とする

## Technology Stack

- Runtime: Python 3.11
- Dependencies: requests, beautifulsoup4
- CI/CD: GitHub Actions (schedule: 6時間ごと)
- State: state.json (git管理)
- Notification: Discord Webhook (Embed)

## Governance

この憲法はすべての実装判断に優先する。
変更はドキュメント更新と共に行うこと。

**Version**: 1.0.0 | **Ratified**: 2026-03-18 | **Last Amended**: 2026-03-18
