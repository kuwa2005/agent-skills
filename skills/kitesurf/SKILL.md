---
name: kitesurf
description: Cloudflare Kitesurf（Workers 上のステートレス CDP ブラウザ）を chrome-devtools-mcp 経由で使う手順。Chrome インストール不要でナビゲーション・スクリーンショット・DOM 取得・JS 実行をエージェントに提供する。
---

# Kitesurf（Cloudflare のクラウドブラウザ）をエージェントから使う

## 概要

Kitesurf は Cloudflare が提供する、**Workers 上で完全に動くステートレスなブラウザ**。Chrome DevTools Protocol (CDP) を話すため、`chrome-devtools-mcp` の `--wsEndpoint` を `wss://kitesurf.cloudflare.app/devtools/browser` に向けるだけで、**ローカルに Chrome をインストールせず**にエージェントへ実ブラウザ能力（ナビゲーション・スクリーンショット・DOM 操作・JS 実行）を提供できる。

- プレイグラウンド: https://kitesurf.cloudflare.app/
- CDP エンドポイント: `wss://kitesurf.cloudflare.app/devtools/browser`
- 公式アナウンス: https://blog.cloudflare.com/kitesurf

## 到達点

このスキルに従ったエージェントが以下を**再現**できること:

1. MCP 設定を追加して Kitesurf に接続する
2. `navigate_page` でページを開き、`take_screenshot` / `take_snapshot` / `evaluate_script` で内容を取得する
3. 接続できないとき、制約（スキーム・時間制限）とトラブルシューティングで原因を切り分けられる

「設定を入れたら動いた」で終わらず、制約を踏まえた使い分けまで辿れることが到達条件。

## 接続フロー

```
エージェント (oimo / opencode / Cursor)
   │  MCP プロトコル (stdio)
   ▼
chrome-devtools-mcp  (npx -y chrome-devtools-mcp@latest)
   │  CDP (WebSocket)
   ▼
wss://kitesurf.cloudflare.app/devtools/browser
   │
   ▼
Workers 上のステートレスブラウザ（ページごとに isolate）
```

## セットアップ

### oimo / opencode（`mcp` キー形式）

`opencode.json` / `oimo.jsonc` に追加:

```json
{
  "mcp": {
    "kitesurf": {
      "type": "local",
      "command": [
        "npx",
        "-y",
        "chrome-devtools-mcp@latest",
        "--wsEndpoint=wss://kitesurf.cloudflare.app/devtools/browser"
      ],
      "enabled": true
    }
  }
}
```

### Cursor / その他（標準 `mcpServers` 形式）

```json
{
  "mcpServers": {
    "kitesurf": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--wsEndpoint=wss://kitesurf.cloudflare.app/devtools/browser"
      ]
    }
  }
}
```

### claude code

```bash
claude mcp add kitesurf -- npx -y chrome-devtools-mcp@latest --wsEndpoint=wss://kitesurf.cloudflare.app/devtools/browser
```

## 制約（プレイグラウンド）

| 制約 | 内容 |
|------|------|
| 時間 | ナビゲーションあたり **CPU 20 秒 / 実時間 60 秒**。超過するとページが停止され DevTools に理由が表示される |
| スキーム | **`https://` のみ**。`http:` / `data:` / `javascript:` / `file:` は拒否される |
| ステートレス | ページごとに fresh な isolate で動く。ブラウザ状態・ログインセッションは持続しない |
| 公開性 | Workers 上の共有ブラウザ。機密情報（認証情報・社内システム）の操作には使わない |

## 使い方（chrome-devtools-mcp の主要ツール）

2026-08 時点の `chrome-devtools-mcp@latest` で確認済みのツール。接続直後はページが 1 枚（`about:blank`）あり、`navigate_page` がそのページを遷移させる。

### ページを開く

`navigate_page` ツール（引数 `url`）。成功すると現在のページ一覧が返る:

```
Successfully navigated to https://example.com/.
## Pages
1: Example Domain (https://example.com/) [selected]
```

### 内容を取得する

| ツール | 用途 |
|--------|------|
| `take_screenshot` | ページの PNG 画像を取得 |
| `take_snapshot` | アクセシビリティツリー（DOM 概要）を取得 |
| `evaluate_script` | JS を実行して値を返す（引数 `function` にアロー関数を渡す） |
| `list_pages` / `select_page` | ページ一覧の確認・選択 |
| `new_page` | 新しいページを開く（引数 `url` 必須） |

### フォーム操作

`click` / `fill` / `fill_form` / `type_text` / `press_key` / `hover` / `drag` / `upload_file` / `wait_for` / `handle_dialog` が使える。対象要素は `take_snapshot` で得た accessibility tree のリファレンスで指定する。

### MCP なしの簡易確認（HTTP エンドポイント）

chrome-devtools-mcp の起動が不要な素早い確認として、プレイグラウンドの HTTP エンドポイントを curl で直接叩ける:

```bash
# スクリーンショット (PNG)
curl -o shot.png "https://kitesurf.cloudflare.app/screenshot?url=https://example.com/"
# PDF
curl -o page.pdf "https://kitesurf.cloudflare.app/pdf?url=https://example.com/"
# レンダリング済み HTML
curl -s "https://kitesurf.cloudflare.app/html?url=https://example.com/"
```

## 具体性の下限（悪い例 / 良い例）

**ページ確認の指示**

悪い例（不十分）:
> ページを開いて確認してください。

良い例（このレベルまで求める）:
> `navigate_page` で `https://example.com/` を開き、`take_snapshot()` で DOM 概要を確認。必要な要素があれば `evaluate_script` で `document.querySelector('h1')?.textContent` を取得する。

**スクリーンショット**

悪い例（不十分）:
> スクリーンショットを撮ってください。

良い例（このレベルまで求める）:
> `navigate_page` で対象 URL を開いた後、`take_screenshot` で PNG を取得。ページが重く 60 秒実時間を超える場合は対象ページを絞る（Kitesurf の制限）。

## 動作確認

同梱のスクリプトで、MCP 設定の**前後**それぞれを検証できる:

```bash
# 1) CDP エンドポイント疎通（MCP 設定前に使う）
node scripts/check.mjs                  # https://example.com/ を開いてタイトル取得
node scripts/check.mjs https://example.org

# 2) MCP エンドツーエンド（設定したコマンドが実動するか）
node scripts/mcp-e2e.mjs

# 3) スクリーンショット取得（URL → PNG）
node scripts/screenshot.mjs https://www.yahoo.co.jp/ yahoo-cojp.png
```

- `check.mjs` … WebSocket で直接 CDP を叩き、`Browser.getVersion` → `Page.navigate` → `document.title` 取得までを検証（Node ≥ 22、グローバル WebSocket を使用）
- `mcp-e2e.mjs` … SKILL.md 記載のコマンドで chrome-devtools-mcp を stdio 起動し、MCP ハンドシェイク → `tools/list` → `navigate_page` 実呼び出しを検証（初回は npx がパッケージをダウンロードするため時間がかかる）
- `screenshot.mjs` … `navigate_page` → `take_screenshot` で URL の PNG を保存（`https://` のみ許可）

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| WebSocket 接続失敗 | エンドポイント URL の typo / ネットワーク不通 | `wss://kitesurf.cloudflare.app/devtools/browser` を再確認。`node scripts/check.mjs` で切り分け |
| ページが読み込まれない | スキームが `https://` でない | URL を `https://` で明示（`http:` / `data:` / `javascript:` / `file:` は拒否） |
| ナビゲーションが停止する | CPU 20 秒 / 実時間 60 秒の制限超過 | 対象ページを軽くする・別 URL で確認 |
| 認証が必要なページが使えない | ステートレスのためログイン状態が持続しない | 認証情報をブラウザ状態に依存させない（URL・リクエスト単位で引き回す設計にしない） |
| MCP ツールが表示されない | 設定変更後にセッションを再起動していない | エージェントセッションを再起動して MCP を再読み込み |
| `navigate_page` が遅い | 初回の npx ダウンロード・コールドスタート | 2 回目以降はキャッシュされる。ナビゲーション上限 60 秒は保持する |

## メモ

- `Target.createTarget` の `url` 引数は Kitesurf では**無視され** `about:blank` のままになる。CDP を直接叩く場合は `Page.navigate` を明示的に呼ぶ（`scripts/check.mjs` が参考実装）
- ページは接続時に 1 枚（`about:blank`）自動生成される。`navigate_page` はそのページを遷移させる
- ツール一覧は 29 件（2026-08 確認）。`tools/list` で最新の一覧を確認できる
