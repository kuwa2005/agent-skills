#!/usr/bin/env node
// Kitesurf CDP 疎通確認スクリプト
//
// wss://kitesurf.cloudflare.app/devtools/browser に WebSocket 接続し、
// 指定 URL のページを作成してタイトルを取得する。
// MCP 設定の前に、エンドポイント自体が生きているかを確認するために使う。
//
// 使い方:
//   node scripts/check.mjs                    # https://example.com/ を開く
//   node scripts/check.mjs https://example.org # URL 指定
//   node scripts/check.mjs --help
//
// 成功時: exit 0、失敗時: 非ゼロ終了 + stderr に理由
import { setTimeout as sleep } from "node:timers/promises";

const WS_URL = "wss://kitesurf.cloudflare.app/devtools/browser";
const DEFAULT_URL = "https://example.com/";

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log("Kitesurf CDP 疎通確認\n\n  node scripts/check.mjs [https://...]\n\nデフォルト: " + DEFAULT_URL);
  process.exit(0);
}

const TARGET_URL = process.argv[2] || DEFAULT_URL;
if (!/^https:\/\//i.test(TARGET_URL)) {
  console.error(`エラー: https:// スキームのみ許可（Kitesurf プレイグラウンドは http:/data:/javascript:/file: を拒否）: ${TARGET_URL}`);
  process.exit(1);
}

const ws = new WebSocket(WS_URL);
let nextId = 1;
const pending = new Map();

function send(method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, sessionId, method, params }));
  });
}

function withTimeout(p, ms, label) {
  return Promise.race([
    p,
    new Promise((_, rej) => setTimeout(() => rej(new Error(`${label} タイムアウト (${ms}ms)`)), ms)),
  ]);
}

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) reject(new Error(`${msg.error.message} (code ${msg.error.code})`));
    else resolve(msg.result);
  }
};

ws.onerror = () => {
  console.error(`エラー: WebSocket 接続失敗 — ${WS_URL}`);
  process.exit(1);
};

ws.onopen = async () => {
  try {
    const v = await withTimeout(send("Browser.getVersion"), 15000, "Browser.getVersion");
    console.log(`接続 OK: ${v.product || "browser"} (protocol ${v.protocolVersion || "?"})`);

    // Kitesurf は createTarget の url を無視するため about:blank で作り、
    // attach 後に Page.navigate で遷移する
    const { targetId } = await withTimeout(
      send("Target.createTarget", { url: "about:blank" }),
      20000,
      "Target.createTarget"
    );
    console.log("ページ作成 OK (about:blank)");

    const { sessionId } = await withTimeout(
      send("Target.attachToTarget", { targetId, flatten: true }),
      10000,
      "Target.attachToTarget"
    );

    await withTimeout(send("Page.navigate", { url: TARGET_URL }, sessionId), 30000, "Page.navigate");
    console.log(`ナビゲーション OK: ${TARGET_URL}`);

    // 読み込み完了までタイトルをポーリングする
    let title = "";
    for (let i = 0; i < 10; i++) {
      await sleep(2000);
      const ev = await withTimeout(
        send("Runtime.evaluate", { expression: "document.title", returnByValue: true }, sessionId),
        10000,
        "Runtime.evaluate"
      );
      title = ev?.result?.value ?? "";
      if (title) break;
    }
    if (!title) {
      throw new Error("document.title が取得できない（ナビゲーション制限の CPU 20 秒 / 実時間 60 秒を確認）");
    }
    console.log(`タイトル取得 OK: ${title}`);
    console.log("疎通確認 成功");
    ws.close();
    process.exit(0);
  } catch (err) {
    console.error(`エラー: ${err.message}`);
    ws.close();
    process.exit(1);
  }
};
