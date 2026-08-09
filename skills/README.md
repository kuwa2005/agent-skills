# Skills 一覧

Cursor / OpenCode 向け Agent Skills です。各フォルダの `SKILL.md` が本体になります。

| 区分 | 入れ方 |
|------|--------|
| **デフォルト**（5 件） | `curl \| bash` または `--all` |
| **オプション**（6 件） | スキル名を指定してインストール |
| **全部**（計 11 件） | `--everything` |

```bash
# デフォルト全部（5 件）
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash

# オプションも含めて全部（11 件）
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- --everything

# オプション例
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- frontend-design
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- wsl-windows-gui
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- split-to-prs babysit create-skill
```

---

## デフォルト（`catalog.txt`）

### [prevent-secret-leak](./prevent-secret-leak/) — 情報漏洩防止

コミットやプッシュ、設定ファイル編集のときに、認証情報や秘密ファイルがリポジトリやチャットへ混入しないようチェックする。  
検知時の対応や、すでに漏れた場合の扱いも含む。

### [verify](./verify/) — 完了前検証

「直った」「完了」「通った」と報告する前に、検証コマンドを実行して結果で確認する。  
推測や感覚での完了報告を防ぐ。

### [xlsm2spec](./xlsm2spec/) — Excel マクロ資産の仕様化

`.xlsm` / `.xlam` などのマクロ付き Excel を解析し、業務の流れと新システム向けの要求仕様書にまとめる。  
ドキュメントや担当者がいないレガシー資産の仕様起こし向け。

### [xlsm-prep](./xlsm-prep/) — Excel の前処理

仕様化などの解析に入る前に、Excel ブックを扱いやすい形へ整える内部向け前処理。

### [access2spec](./access2spec/) — Access 資産の仕様化

MS Access（`.mdb/.mde/.accdb`）を静的解析し、設計書13種を Markdown で生成する。XLSM は xlsm2spec と連携。

---

## オプション（`optional.txt`）

### [frontend-design](./frontend-design/) — フロントエンドデザイン

ランディングや Web UI、ダッシュボードなど、見た目のある画面を作る・直すときのデザイン指針。  
印象を残す表現と、管理画面など慣例に寄せる作り分けを行う。

### [split-to-prs](./split-to-prs/) — PR 分割

大きな変更を、レビューしやすい小さな PR に分割する。分割計画の承認前は commit / push / PR 作成を行わない。

### [babysit](./babysit/) — PR 維持

PR をマージ可能な状態まで維持する。コメント整理、コンフリクト解消、CI 修正をループで行う。

### [create-skill](./create-skill/) — スキル作成

新しい Agent Skill の作成手順と SKILL.md の書き方をガイドする。Cursor / OpenCode 両対応。

### [playwright-coreserver](./playwright-coreserver/) — CoreServer 向け Playwright

CoreServer（AlmaLinux 8.10）で sudo なしに Playwright + Chromium を動かす手順。

### [wsl-windows-gui](./wsl-windows-gui/) — WSL から Windows GUI 操作

WSL を司令塔にし、Windows 側の pywinauto / PowerShell / AutoHotkey でデスクトップアプリを操作する。

```bash
# オプション個別
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- frontend-design
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- wsl-windows-gui
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- split-to-prs babysit create-skill

# デフォルト + オプション全部（計 11 件）
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- --everything
```

---

## 補足

| ファイル | 意味 |
|----------|------|
| `catalog.txt` | デフォルトスキル一覧（`--all` 対象） |
| `optional.txt` | オプションスキル一覧（明示指定のみ） |
| `<name>/SKILL.md` | エージェントが読む手順本体 |
