---
name: wsl-windows-gui
description: >-
  Automate Windows GUI apps from WSL by orchestrating Windows-side engines
  (pywinauto, PowerShell UI Automation, AutoHotkey). Use when the user asks to
  control Windows apps from WSL/Bash, click buttons, send keys, drive Calculator
  / Notepad / desktop software, or mentions WSL interop GUI automation,
  pywinauto, or Windows UI Automation.
---

# WSL から Windows GUI を操作する

## 概要

WSL 自体は HWND / UIA を直接扱えない。**WSL（Bash）を司令塔**にし、Windows 側の自動化エンジンへ指示を飛ばす。

## 到達点

従った人が、**(1) Windows Python + pywinauto の有無確認 → (2) スクリプトを Windows パスへ置く → (3) WSL から `powershell.exe` / `python.exe` で起動 → (4) ハンドル接続でボタン操作 → (5) 結果テキスト取得**まで再現できること。  
「Interop でできる」だけで止まったら失敗。

## 具体性の下限（悪い例 / 良い例）

**構成説明**

悪い例（不十分）:
> WSL から Windows アプリも操作できます。Python を使ってください。

良い例（このレベルまで求める）:
> WSL では `export PATH="/mnt/c/Windows/System32/WindowsPowerShell/v1.0:/mnt/c/Windows/System32:$PATH"` のうえ、`powershell.exe -NoProfile -Command "python C:\\Users\\<User>\\wsl-win-gui\\automate_calc.py"` を実行。スクリプトは `/mnt/c/Users/<User>/...` に置き、Windows Python（`pywinauto`）が UIA で `電卓` を操作する。

**ウィンドウ接続**

悪い例（不十分）:
> `Application(...).connect(title_re=".*電卓.*")` で繋げばよい。

良い例（このレベルまで求める）:
> UWP 電卓は同名ウィンドウが複数になり `ElementAmbiguousError` になる。`Desktop(backend="uia").windows()` で可視ウィンドウを列挙し、`Application(backend="uia").connect(handle=w.handle)` → `app.window(handle=w.handle)` で接続する。`Desktop(...).windows()` の戻り値（wrapper）には `child_window` が無い点に注意。

## 図必須（オーケストレーション）

```
[WSL Bash]
    │  powershell.exe / python.exe / AutoHotkey64.exe
    v
[Windows 自動化エンジン]
    ├─ pywinauto (推奨・UIA)
    ├─ PowerShell + System.Windows.Automation / SendKeys
    └─ AutoHotkey
    │
    v
[Windows GUI アプリ] 例: CalculatorApp / notepad
```

分岐（接続失敗時）:

```
[calc.exe 起動] → [Desktop.windows で「電卓」探索]
        │
        ├─ 0件 → cmd /c start calc.exe → 再探索
        ├─ 複数 → handle で connect（title_re 単体禁止）
        └─ UIA ボタン失敗 → send_keys フォールバック
```

---

## 前提チェック（最初に実行）

```bash
export PATH="/mnt/c/Windows/System32/WindowsPowerShell/v1.0:/mnt/c/Windows/System32:${PATH:-}"

# Windows 側 Python
powershell.exe -NoProfile -Command "python -c \"import sys; print(sys.executable)\""

# pywinauto
powershell.exe -NoProfile -Command "python -c \"import pywinauto; print(pywinauto.__version__)\""
```

未導入なら **Windows 側**で:

```powershell
python -m pip install pywinauto
```

Windows ホーム（スクリプト置き場）:

```bash
WIN_HOME_WIN=$(powershell.exe -NoProfile -Command 'Write-Output $env:USERPROFILE' | tr -d '\r')
WIN_HOME_MNT=$(echo "$WIN_HOME_WIN" | sed -E 's#^([A-Za-z]):\\#/mnt/\L\1/#; s#\\#/#g')
echo "WIN_HOME_WIN=$WIN_HOME_WIN"
echo "WIN_HOME_MNT=$WIN_HOME_MNT"
```

---

## 推奨手順（方法1: pywinauto）

1. 自動化スクリプトを **Windows パス**（例: `%USERPROFILE%\wsl-win-gui\`）に置く  
   - `\\wsl$\...` 直実行より `/mnt/c/Users/...` 経由が安定
2. WSL から Windows Python で実行する
3. ウィンドウは **handle 接続**（title_re 単独は曖昧エラーになりやすい）
4. 操作は `child_window(auto_id=...).click_input()`、失敗時は `send_keys`

サンプル: [scripts/automate_calc.py](scripts/automate_calc.py)  
ランチャ: [scripts/run_from_wsl.sh](scripts/run_from_wsl.sh)

```bash
# スキル同梱スクリプトを使う例
SKILL_DIR="$(dirname "$0")"   # または skills/wsl-windows-gui
bash "$SKILL_DIR/scripts/run_from_wsl.sh"
```

電卓サンプルの成功出力例:

```
CONNECTED title='電卓' handle=659522
METHOD=uia-buttons
RESULT=表示は 3 です
OK: Calculator operated from WSL via Windows pywinauto
```

---

## 方法2: PowerShell（追加インストールなし）

キー送信程度なら PowerShell で足りる。

```bash
powershell.exe -NoProfile -Command \
  "Start-Process notepad; Start-Sleep -Seconds 1; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('Hello from WSL!')"
```

複雑なコントロール操作は pywinauto を優先。

---

## 方法3: AutoHotkey

Windows に AutoHotkey v2 がある場合:

```bash
"/mnt/c/Program Files/AutoHotkey/v2/AutoHotkey64.exe" "C:\path\to\control_app.ahk"
```

---

## よくある失敗と対処

| 症状 | 原因 | 対処 |
|------|------|------|
| `powershell.exe: command not found` | PATH 未設定 | `System32` と `WindowsPowerShell\v1.0` を PATH へ |
| `ModuleNotFoundError: pywinauto` | WSL の Python を使っている | **Windows** の `python.exe` で `pip install` / 実行 |
| `ElementAmbiguousError` | 同名ウィンドウ複数 | handle で connect。必要なら対象プロセスを一度終了 |
| `UIAWrapper` に `child_window` が無い | `windows()` の wrapper を直接使っている | `Application.connect(handle=...)` 経由の WindowSpecification を使う |
| プロセスはあるが窓が無い | UWP 起動の取りこぼし | `cmd /c start calc.exe` で再起動し数秒待つ |
| クリック効かない | フォーカスなし / 言語別 auto_id | `set_focus()`、`dump_buttons` で auto_id 確認、`send_keys` へフォールバック |

---

## エージェント向けチェックリスト

```
Task Progress:
- [ ] PATH に Windows System32 / PowerShell を追加
- [ ] Windows Python と pywinauto を確認（無ければ Windows 側へ導入）
- [ ] スクリプトを %USERPROFILE% 配下など Windows パスへ配置
- [ ] 対象アプリ起動 → Desktop で窓列挙 → handle 接続
- [ ] UIA クリック（失敗時 send_keys）
- [ ] 結果テキストまたはスクリーンショットで成功を証拠提示
```

## 注意

- GUI 自動化はユーザーデスクトップセッションが必要（ヘッドレスのみの環境では窓が出ないことがある）
- 本番 UI の破壊的操作・認証画面の自動入力は、ユーザ確認なしで行わない
- スクリプトやログにパスワード・API キーを埋め込まない
