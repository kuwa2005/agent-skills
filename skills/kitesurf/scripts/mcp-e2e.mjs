#!/usr/bin/env node
// Kitesurf + chrome-devtools-mcp のエンドツーエンド検証スクリプト
//
// SKILL.md に記載するコマンド（chrome-devtools-mcp を Kitesurf の CDP
// エンドポイントに向けて stdio で起動）を実際に実行し、MCP ハンドシェイク →
// ツール一覧 → 実ツール呼び出しまでを確認する。
//
// 使い方:
//   node scripts/mcp-e2e.mjs
//
// 成功時: exit 0、失敗時: 非ゼロ終了 + stderr に理由
import { spawn } from "node:child_process";

const WS_URL = "wss://kitesurf.cloudflare.app/devtools/browser";
const NAV_URL = process.argv[2] || "https://example.com/";
const INIT_TIMEOUT_MS = 120000; // 初回は npx が chrome-devtools-mcp をダウンロードする

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
  const payload = { jsonrpc: "2.0", id, method, params };
  server.stdin.write(JSON.stringify(payload) + "\n");
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
      console.log(`[server] (非 JSON) ${line}`);
      continue;
    }
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(`${msg.error.message} (code ${msg.error.code})`));
      else resolve(msg.result);
    } else if (msg.method) {
      console.log(`[notification] ${msg.method}`);
    }
  }
});

server.on("error", (err) => {
  console.error(`エラー: chrome-devtools-mcp の起動に失敗 — ${err.message}`);
  process.exit(1);
});
server.on("exit", (code) => {
  if (pending.size > 0 && code !== 0) {
    console.error(`エラー: chrome-devtools-mcp が異常終了 (code ${code})`);
    process.exit(1);
  }
});

async function main() {
  try {
    console.log(`MCP サーバー起動: npx -y chrome-devtools-mcp@latest --wsEndpoint=${WS_URL}`);
    const init = await withTimeout(
      send("initialize", {
        protocolVersion: "2024-11-05",
        capabilities: { roots: { listChanged: false }, sampling: {}, experimental: {} },
        clientInfo: { name: "kitesurf-mcp-e2e", version: "1.0.0" },
      }),
      INIT_TIMEOUT_MS,
      "initialize"
    );
    console.log(`ハンドシェイク OK: protocol ${init?.protocolVersion || "?"}`);
    notify("notifications/initialized");

    const tools = await withTimeout(send("tools/list"), 30000, "tools/list");
    const names = (tools?.tools ?? []).map((t) => t.name);
    console.log(`ツール一覧 (${names.length}):`);
    for (const n of names) console.log(`  - ${n}`);

    // ナビゲーション系ツールを探して実呼び出しする
    const navTool = names.find((n) => /navigat|goto|open/i.test(n)) ?? names.find((n) => /page|url/i.test(n));
    if (!navTool) {
      throw new Error("ナビゲーション系ツールが見つからない（tools/list の内容を確認）");
    }
    console.log(`\nツール呼び出し: ${navTool} url=${NAV_URL}`);
    // Kitesurf のナビゲーション上限は実時間 60 秒のため、クライアント側は余裕を持たせる
    const callResult = await withTimeout(
      send("tools/call", { name: navTool, arguments: { url: NAV_URL } }),
      90000,
      `tools/call ${navTool}`
    );
    const text = JSON.stringify(callResult ?? {}).slice(0, 400);
    console.log(`呼び出し応答 OK: ${text}`);
    console.log("MCP エンドツーエンド検証 成功");
    server.kill();
    process.exit(0);
  } catch (err) {
    console.error(`エラー: ${err.message}`);
    server.kill();
    process.exit(1);
  }
}

main();
