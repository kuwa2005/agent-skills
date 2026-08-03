# Skills 一覧

Cursor / OpenCode 向け Agent Skills です。各フォルダの `SKILL.md` が本体になります。

| 区分 | 入れ方 |
|------|--------|
| **デフォルト** | `curl \| bash` または `--all` |
| **オプション** | スキル名を指定してインストール |

```bash
# デフォルト全部
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash

# オプション例
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- frontend-design
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

---

## オプション（`optional.txt`）

### [frontend-design](./frontend-design/) — フロントエンドデザイン

ランディングや Web UI、ダッシュボードなど、見た目のある画面を作る・直すときのデザイン指針。  
印象を残す表現と、管理画面など慣例に寄せる作り分けを行う。

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- frontend-design
```

---

## 補足

| ファイル | 意味 |
|----------|------|
| `catalog.txt` | デフォルトスキル一覧（`--all` 対象） |
| `optional.txt` | オプションスキル一覧（明示指定のみ） |
| `<name>/SKILL.md` | エージェントが読む手順本体 |
