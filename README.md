# Agent Skills

Cursor / OpenCode 向け Agent Skills の配布リポジトリです。

## 全部一発インストール

`catalog.txt` のデフォルトスキルだけ入ります（**オプションは対象外**）:

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash
```

明示的にデフォルト全部:

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- --all
```

## オプションも含めて全部インストール

デフォルト＋オプションを一括で入れます:

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- --everything
```

（別名: `--with-optional` / `--full`）

## 個別インストール

デフォルト／オプションどちらも名前指定で入れられます:

```bash
# デフォルトから
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- prevent-secret-leak

# オプション
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- frontend-design

# 複数（スペース / カンマ）
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- verify xlsm2spec
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- verify,frontend-design
```

## 一覧・対象の絞り込み

```bash
# 利用可能スキル一覧（default / optional を分けて表示）
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- --list

# Cursor のみ / OpenCode のみ
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- --cursor-only --all
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash -s -- --opencode-only prevent-secret-leak
```

（GitHub raw でも可。CDN キャッシュが残る場合は jsDelivr を推奨）

```bash
curl -fsSL https://raw.githubusercontent.com/kuwa2005/agent-skills/main/install.sh | bash
```

## インストール先

| 対象 | パス |
|------|------|
| Cursor | `~/.cursor/skills/<skill-name>/` |
| OpenCode | `~/.config/opencode/skills/<skill-name>/` |

## 収録スキル

### デフォルト（`--all` / 素の `curl|bash` 対象）

| スキル | 概要 |
|--------|------|
| `prevent-secret-leak` | git add/commit/push 前の秘密情報混入防止、および秘密ファイルの表示・外送防止 |
| `verify` | 完了・修正済み・PR 作成前に、検証コマンドの実行結果（証拠）を必須とする |
| `xlsm2spec` | Excel マクロ資産から業務分析と要求仕様書を生成 |
| `xlsm-prep` | 仕様化などの解析に入る前に、Excel ブックを扱いやすい形へ整える内部向け前処理 |

### オプション（名前指定、または `--everything`）

| スキル | 概要 |
|--------|------|
| `frontend-design` | UI / ランディング等の視覚デザイン指針（表現モードと管理画面の convention モードを区別） |

`xlsm2spec` の抽出スクリプト依存（手動導入時）:

```bash
pip install openpyxl oletools access_parser
```

## リポジトリ構成

```
agent-skills/
├── install.sh
├── README.md
├── LICENSE
└── skills/
    ├── catalog.txt              # デフォルト（--all）
    ├── optional.txt             # オプション（明示指定 / --everything）
    ├── prevent-secret-leak/
    ├── verify/
    ├── xlsm2spec/
    │   └── scripts/
    │       ├── extract.py
    │       └── prepare_workbook.py
    ├── xlsm-prep/
    │   ├── SKILL.md
    │   ├── docs/
    │   └── scripts/prepare.py
    └── frontend-design/         # optional
        ├── SKILL.md
        └── LICENSE.txt
```

## ローカルから実行

```bash
git clone https://github.com/kuwa2005/agent-skills.git
cd agent-skills
./install.sh --list
./install.sh --all
./install.sh --everything
./install.sh frontend-design
./install.sh prevent-secret-leak verify
```

## 環境変数

| 変数 | 意味 | デフォルト |
|------|------|------------|
| `AGENT_SKILLS_REPO` | `owner/repo` | `kuwa2005/agent-skills` |
| `AGENT_SKILLS_REF` | branch/tag/commit | `main` |
| `CURSOR_SKILLS_DIR` | Cursor インストール先 | `~/.cursor/skills` |
| `OPENCODE_SKILLS_DIR` | OpenCode インストール先 | `~/.config/opencode/skills` |

## スキルの追加

1. `skills/<name>/` に `SKILL.md`（と必要なら `scripts/`）を追加
2. デフォルトなら `skills/catalog.txt`、オプションなら `skills/optional.txt` に `<name>` を追記
3. main にマージ

## コントリビューション

- **コミットメッセージは日本語**で書く。詳細は [COMMIT_MESSAGE.md](COMMIT_MESSAGE.md)
- 例: `オプションの frontend-design を追加（--all 対象外）`
- 秘密情報（`.env`、認証情報、鍵）をコミットしない

## 注意

`curl | bash` はスクリプト実行を信頼する方式です。内容を確認してから実行してください:

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | less
```
