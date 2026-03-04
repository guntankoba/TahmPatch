# TahmPatch

Discord の patch bot が投稿した LoL パッチノートリンクを検出し、
**日本語版（ja-jp）** の URL を返信するボットです。

## できること
- `League of Legends Patch 26.5 Notes` のようなタイトルから日本語リンクを生成
- メッセージ/Embed に含まれる URL を検出
- patchbot 特有のリンク（リダイレクト）も追跡して、最終到達先が英語版なら日本語版へ変換
- patchbot の投稿のみをトリガーにして返信（`PATCHBOT_USER_IDS` 未設定時は名前に `patchbot` を含むBotを対象）

## セットアップ
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 環境変数
- `DISCORD_BOT_TOKEN` : Discord Bot トークン（必須）
- `TARGET_CHANNEL_IDS` : 監視対象チャンネル ID（任意、カンマ区切り）
  - 未指定なら全チャンネルで反応
- `PATCHBOT_USER_IDS` : patchbot のユーザー ID（任意、カンマ区切り）
  - 指定時はこの ID の Bot 投稿のみを処理
  - 未指定時は Bot の表示名/名前に `patchbot` を含む投稿を処理

## 実行
```bash
python bot.py
```


## Railway デプロイ
1. Railway で GitHub リポジトリを新規プロジェクトとして作成
2. Variables に以下を設定
   - `DISCORD_BOT_TOKEN`（必須）
   - `PATCHBOT_USER_IDS`（推奨: patchbot のユーザーID）
   - `TARGET_CHANNEL_IDS`（任意）
3. 本リポジトリには `Procfile` と `railway.json` を同梱しているため、
   Railway は `python bot.py` を Worker として起動します
4. デプロイ後、ログに `ログイン完了:` が表示されれば起動成功です

> 注意: `PATCHBOT_USER_IDS` を設定しない場合は、Bot名に `patchbot` を含む投稿を対象にします。
> 本番運用では誤検知防止のため、ID指定を推奨します。

## 動作イメージ
英語リンク:
`https://www.leagueoflegends.com/en-us/news/game-updates/league-of-legends-patch-26-5-notes/`

返信:
`https://www.leagueoflegends.com/ja-jp/news/game-updates/league-of-legends-patch-26-5-notes/`
