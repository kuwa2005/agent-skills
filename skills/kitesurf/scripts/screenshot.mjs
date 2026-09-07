#!/usr/bin/env node
// Kitesurf スクリーンショット取得スクリプト
//
// chrome-devtools-mcp を Kitesurf の CDP エンドポイントに向けて stdio 起動し、
// navigate_page → take_screenshot で URL の PNG を保存する。
// Kitesurf の制約どおり https:// のみ許可（http:/data:/javascript:/file: は拒否）。
//
// 使い方:
//   node scripts/screenshot.mjs https://www.yahoo.co.jp/ yahoo-cojp.png
//   node scripts/screenshot.mjs https://example.com/          # <ホスト名>.png に保存
//
// 成功時: exit 0、失敗時: 非ゼロ終了 + stderr に理由
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";

const WS_URL = "wss://kitesurf.cloudflare.app/devtools/browser";
const NAV_TIMEOUT_MS = 90000; // Kitesurf のナビゲーション実時間上限 60 秒 + 余裕
const SHOT_TIMEOUT_MS = 60000;

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log("Kitesurf スクリーンショット取得\n\n  node scripts/screenshot.mjs <https://...> [出力パス]\n\n出力パス省略時は <ホスト名>.png");
  process.exit(0);
}

const URL_ARG = process.argv[2];
const OUTPUT = process.argv[3] || (URL_ARG ? new URL(URL_ARG).hostname + ".png" : "");

if (!URL_ARG || !OUTPUT) {
  console.error("エラー: 引数が不足 — node scripts/screenshot.mjs <https://...> [出力パス]");
  process.exit(1);
}
if (!/^https:\/\//i.test(URL_ARG)) {
  console.error(`エラー: https:// スキームのみ許可（Kitesurf プレイグラウンドは http:/data:/javascript:/file: を拒否）: ${URL_ARG}`);
  process.exit(1);
}

const server = spawn(
  "npx",
  ["-y", "chrome-devtools-mcp@latest", `--wsEndpoint=${WS_URL}`],
  { stdio: ["pipe", "pipe", "inherit"] }
);

let nextId = 1;
const pending = new Map();
let buffer = "";

function send(method, params = {}) {
  const id = nextId++;
  server.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

function notify(method, params = {}) {
  server.stdin.write(JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n");
}

function withTimeout(p, ms, label) {
  return Promise.race([
    p,
    new Promise((_, rej) => setTimeout(() => rej(new Error(`${label} タイムアウト (${ms}ms)`)), ms)),
  ]);
}

server.stdout.on("data", (chunk) => {
  buffer += chunk.toString();
  let idx;
  while ((idx = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, idx);
    buffer = buffer.slice(idx + 1);
    if (!line.trim()) continue;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      continue;
    }
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(`${msg.error.message} (code ${msg.error.code})`));
      else resolve(msg.result);
    }
  }
});

server.on("error", (err) => {
  console.error(`エラー: chrome-devtools-mcp の起動に失敗 — ${err.message}`);
  process.exit(1);
});

async function main() {
  try {
    console.log(`ナビゲーション: ${URL_ARG}`);
    await withTimeout(
      send("initialize", {
        protocolVersion: "2024-11-05",
        capabilities: { roots: { listChanged: false }, sampling: {}, experimental: {} },
        clientInfo: { name: "kitesurf-screenshot", version: "1.0.0" },
      }),
      120000,
      "initialize"
    );
    notify("notifications/initialized");

    await withTimeout(send("tools/call", { name: "navigate_page", arguments: { url: URL_ARG } }), NAV_TIMEOUT_MS, "navigate_page");
    console.log("ナビゲーション完了");

    const result = await withTimeout(send("tools/call", { name: "take_screenshot", arguments: {} }), SHOT_TIMEOUT_MS, "take_screenshot");
    const image = (result?.content ?? []).find((c) => c.type === "image" && c.mimeType === "image/png");
    if (!image?.data) {
      throw new Error("take_screenshot の応答に PNG 画像が含まれていない");
    }
    writeFileSync(OUTPUT, Buffer.from(image.data, "base64"));
    const size = Buffer.byteLength(image.data, "base64");
    console.log(`保存 OK: ${OUTPUT} (${size} bytes)`);
    server.kill();
    process.exit(0);
  } catch (err) {
    console.error(`エラー: ${err.message}`);
    server.kill();
    process.exit(1);
  }
}

main();
