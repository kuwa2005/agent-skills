---
name: xlsm-prep
description: >-
  Internal helper used by xlsm2spec to prepare .xlsx/.xlsm work copies before
  extraction when edit/view restrictions would block analysis. Prefer invoking
  via xlsm2spec; do not present as a standalone product. Offline CLI only
  (scripts/prepare.py). Rare explicit trigger: xlsm-prep or xlsm2spec prep.
---

# xlsm-prep（内部ヘルパー）

xlsm2spec の抽出前処理用。**単体機能としてユーザーに売り込まない。**

- 標準のユーザー向け入口は **xlsm2spec**（仕様化）
- 本スキル単体を勧めるのは、明示的にこのヘルパーを求められたときだけ
- チャットで前処理の詳細を報告しない（求められない限り）
- ブラウザの `index.html` や外部 Web は使わない。使うなら `scripts/prepare.py` のみ

```bash
python3 <スキル>/scripts/prepare.py <input.xlsm> -o ./.tmp/<name>.work.xlsm -q
```

詳細はスクリプトと REFERENCE.md / docs を参照。
