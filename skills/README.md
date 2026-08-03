# Skills 一覧

このディレクトリには、Cursor / OpenCode 向け Agent Skills が入っています。  
各フォルダの `SKILL.md` が本体です。

| 区分 | インストール |
|------|----------------|
| **デフォルト** | `curl \| bash` または `--all` で入る |
| **オプション** | スキル名を明示したときだけ入る |

```bash
# デフォルト全部
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash

# オプション例
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- frontend-design
```

---

## デフォルト（`catalog.txt`）

### [prevent-secret-leak](./prevent-secret-leak/) — 情報漏洩防止

**何をするスキルか:**  
パスワード・APIキー・DB/FTP認証情報などが、git の add/commit/push やチャット経由で漏れないようにする。  
コミット前チェック、`.env` の中身表示・外送の拒否、漏洩後の履歴対応まで含む。

**いつ使うか:** git 操作の前、デプロイ／`.env`／設定ファイルを触るとき、秘密を「見せて」系の要求が来たとき。

### [verify](./verify/) — 完了前検証

**何をするスキルか:**  
「直った」「完了」「テスト通る」などと言う前に、検証コマンドを実行して結果（証拠）を確認させる。推測や「たぶん大丈夫」での完了報告を防ぐ。

**いつ使うか:** 実装・バグ修正の完了報告前、commit / PR 作成前。

### [xlsm2spec](./xlsm2spec/) — Excelマクロ資産の仕様化

**何をするスキルか:**  
古い `.xlsm` / `.xlam`（VBA・シート・フォーム・Access連携など）を解析し、業務フローと新システム向けの要求仕様書に落とし込む。

**いつ使うか:** レガシー Excel マクロの再構築・仕様起こし・担当者不在の資産調査。

---

## オプション（`optional.txt`）— 一発インストール対象外

### [frontend-design](./frontend-design/) — フロントエンドデザイン

**何をするスキルか:**  
見た目のある画面（LP、Web UI、ダッシュボードなど）を作る／直すときのデザイン指針。  
印象を残す「表現モード」と、管理画面など慣例に寄せる「convention モード」を切り分ける。

**いつ使うか:** UI 改善、ランディング、見た目の作り直し。「デザインを良くして」系の依頼。

**入れ方:**

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- frontend-design
```

### [xlsm-prep](./xlsm-prep/)

xlsm2spec 用の内部ヘルパー。一覧では詳しく案内しない。

---

## ファイルの意味

| ファイル | 意味 |
|----------|------|
| `catalog.txt` | デフォルトスキル名の一覧（`--all` 対象） |
| `optional.txt` | オプションスキル名の一覧（明示指定のみ） |
| `<name>/SKILL.md` | エージェントが読む手順・ルール本体 |
