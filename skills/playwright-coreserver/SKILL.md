---
name: playwright-coreserver
description: Install, configure, and troubleshoot Playwright + Chromium on CoreServer (AlmaLinux 8.10) without sudo access. Includes recovery procedures for broken installations.
---

# CoreServer で Playwright を動かすためのガイド

## 概要

CoreServer（AlmaLinux 8.10）は `dnf install` に sudo 権限がなく、Playwright の推奨インストール方法が使えない。  
以下は、その制約を回避して Playwright + Chromium を動かす手順。

---

## 1. Playwright のグローバルインストール

```bash
npm install -g playwright
npx playwright install chromium
```

Chromium バイナリは以下に展開される:

```
~/.cache/ms-playwright/chromium-{ver}/chrome-linux64/chrome
~/.cache/ms-playwright/chromium_headless_shell-{ver}/chrome-headless-shell-linux64/chrome-headless-shell
```

---

## 2. システム依存ライブラリの手動取得

sudo が使えないため、RPM をダウンロードしてユーザー領域に展開する。

### 2-1. 必要な RPM をダウンロード

```bash
mkdir -p ~/.rpm
dnf download \
  nspr nss nss-util nss-softokn nss-softokn-freebl \
  atk at-spi2-atk at-spi2-core \
  alsa-lib libdrm mesa-libgbm \
  libwayland-client libwayland-server \
  --nogpgcheck --destdir=~/.rpm
```

### 2-2. RPM を展開

```bash
mkdir -p ~/.rpm/extract
cd ~/.rpm
for f in *.x86_64.rpm; do
  rpm2cpio "$f" | (cd ~/.rpm/extract && cpio -idm 2>/dev/null)
done
```

展開先の共有ライブラリパス:

```
~/.rpm/extract/usr/lib64/
```

---

## 3. Playwright スクリプトの書き方

### 3-1. LD_LIBRARY_PATH を最初に設定

ESM モジュールでは `import` がホイストされるため、`process.env` を `import` **の前**に設定する必要がある。

```javascript
// 必ずファイルの先頭に置く
process.env.LD_LIBRARY_PATH = '絶対パスで指定';

const { chromium } = await import('playwright');
// ... 以降は通常の Playwright コード
```

グローバルインストールの Playwright を直接指定する場合:

```javascript
process.env.LD_LIBRARY_PATH = '/virtual/pcm/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/../../..';

const { chromium } = await import(
  '/virtual/pcm/.nvm/versions/node/v24.18.0/lib/node_modules/playwright/index.mjs'
);
```

### 3-2. LD_LIBRARY_PATH をシェルから渡す（推奨）

```bash
LD_LIBRARY_PATH=~/.rpm/extract/usr/lib64 node capture.mjs
```

### 3-3. ブラウザ起動オプション

CoreServer ではサンドボックスが効かないため、以下のフラグが必要:

```javascript
const browser = await chromium.launch({
  headless: true,
  args: [
    '--no-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage'
  ]
});
```

---

## 4. 完全なスクリプト例

```javascript
process.env.LD_LIBRARY_PATH = '/virtual/pcm/.rpm/extract/usr/lib64';
const { chromium } = await import('/virtual/pcm/.nvm/versions/node/v24.18.0/lib/node_modules/playwright/index.mjs');

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
});

const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('https://example.com', { waitUntil: 'networkidle', timeout: 15000 });
await page.screenshot({ path: 'screenshot.png', fullPage: false });

await browser.close();
```

実行:

```bash
LD_LIBRARY_PATH=~/.rpm/extract/usr/lib64 node capture.mjs
```

---

## 5. ディレクトリ構成（推奨）

```
~/
├── .rpm/                         # RPM ダウンロード先
│   ├── *.rpm
│   └── extract/
│       └── usr/lib64/            # 展開された共有ライブラリ
├── .cache/ms-playwright/         # Playwright の Chromium バイナリ
│   ├── chromium-{ver}/
│   └── chromium_headless_shell-{ver}/
├── .nvm/versions/node/           # Node.js
└── tmp/                          # 一時ファイル（消してOK）
    └── opencode/                 # スクリプト等
```

---

## 6. トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `libnspr4.so => not found` | NSS/NSPR 未インストール | `dnf download nspr` で取得 |
| `libsoftokn3.so: cannot open` | nss-softokn 未インストール | `dnf download nss-softokn` で取得 |
| `libatspi.so.0 => not found` | AT-SPI2 未インストール | `dnf download at-spi2-core` で取得 |
| `NSS error code: -8023` | NSS DB 未初期化 | `certutil -d sql:~/.rpm/nssdb -N --empty-password` |
| `Target page, context or browser has been closed` | LD_LIBRARY_PATH 未設定 | シェルから `LD_LIBRARY_PATH=...` を渡す |
| `SEC_ERROR_PKCS11_DEVICE_ERROR` | libfreebl3 不足 | `dnf download nss-softokn-freebl` で取得 |

---

## 7. 依存ライブラリ一覧（RPM パッケージ名）

| パッケージ | 提供ライブラリ |
|-----------|---------------|
| `nspr` | libnspr4.so, libplc4.so, libplds4.so |
| `nss` | libnss3.so, libsmime3.so, libssl3.so |
| `nss-util` | libnssutil3.so |
| `nss-softokn` | libsoftokn3.so |
| `nss-softokn-freebl` | libfreebl3.so, libfreeblpriv3.so |
| `atk` | libatk-1.0.so.0 |
| `at-spi2-atk` | libatk-bridge-2.0.so.0 |
| `at-spi2-core` | libatspi.so.0 |
| `alsa-lib` | libasound.so.2 |
| `libdrm` | libdrm.so.2 |
| `mesa-libgbm` | libgbm.so.1 |
| `libwayland-client` | libwayland-client.so.0 |
| `libwayland-server` | libwayland-server.so.0 |

---

## 8. 壊れたときの復旧手順

### 8-1. Playwright の再インストール

```bash
npm install -g playwright
npx playwright install chromium
```

### 8-2. RPM の再ダウンロードと展開

```bash
# 既存の RPM を削除
rm -rf ~/.rpm

# 再ダウンロード
mkdir -p ~/.rpm
dnf download \
  nspr nss nss-util nss-softokn nss-softokn-freebl \
  atk at-spi2-atk at-spi2-core \
  alsa-lib libdrm mesa-libgbm \
  libwayland-client libwayland-server \
  --nogpgcheck --destdir=~/.rpm

# 再展開
mkdir -p ~/.rpm/extract
cd ~/.rpm
for f in *.x86_64.rpm; do
  rpm2cpio "$f" | (cd ~/.rpm/extract && cpio -idm 2>/dev/null)
done
```

### 8-3. Chromium バイナリの再ダウンロード

```bash
# 既存の Chromium を削除
rm -rf ~/.cache/ms-playwright

# 再インストール
npx playwright install chromium
```

### 8-4. 完全な初期化

```bash
# 全ての関連ファイルを削除
rm -rf ~/.rpm
rm -rf ~/.cache/ms-playwright
npm uninstall -g playwright

# 再インストール
npm install -g playwright
npx playwright install chromium

# RPM の再ダウンロードと展開
mkdir -p ~/.rpm
dnf download \
  nspr nss nss-util nss-softokn nss-softokn-freebl \
  atk at-spi2-atk at-spi2-core \
  alsa-lib libdrm mesa-libgbm \
  libwayland-client libwayland-server \
  --nogpgcheck --destdir=~/.rpm

mkdir -p ~/.rpm/extract
cd ~/.rpm
for f in *.x86_64.rpm; do
  rpm2cpio "$f" | (cd ~/.rpm/extract && cpio -idm 2>/dev/null)
done
```

### 8-5. 動作確認

```bash
# 簡単なテストスクリプト
cat > ~/tmp/test-playwright.mjs << 'EOF'
process.env.LD_LIBRARY_PATH = '/virtual/pcm/.rpm/extract/usr/lib64';
const { chromium } = await import('/virtual/pcm/.nvm/versions/node/v24.18.0/lib/node_modules/playwright/index.mjs');

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
});

const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('https://example.com', { waitUntil: 'networkidle', timeout: 15000 });
await page.screenshot({ path: '~/tmp/test-screenshot.png', fullPage: false });

await browser.close();
console.log('スクリーンショットを保存しました: ~/tmp/test-screenshot.png');
EOF

LD_LIBRARY_PATH=~/.rpm/extract/usr/lib64 node ~/tmp/test-playwright.mjs
```

---

## 9. メモ

- `LD_LIBRARY_PATH` は **ESM import の前**に設定するか、シェルから渡す
- Chromium ヘッドレスシェル（`chromium_headless_shell`）はフルChrome より依存が少なく、推奨
- RPM ライブラリは `~/.rpm/` に配置（`~/tmp/` は消してOKな一時ファイルのみ）
- `/tmp` にはファイルを置かず、必ず `~/tmp/` を使用する
- RPM のダウンロードには `--nogpgcheck` が必要（署名検証が失敗するため）
- トラブルシューティング時は `ldd` で不足ライブラリを確認する
