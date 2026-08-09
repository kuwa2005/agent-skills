"""Windows Calculator GUI automation via pywinauto (run with Windows Python)."""
from __future__ import annotations

import subprocess
import sys
import time

from pywinauto import Desktop
from pywinauto.application import Application
from pywinauto.keyboard import send_keys


def kill_calculators() -> None:
    for image in ("CalculatorApp.exe", "Calculator.exe", "calc.exe"):
        subprocess.run(["taskkill", "/F", "/IM", image], capture_output=True, check=False)
    time.sleep(1.5)


def list_calc_windows():
    wins = []
    for w in Desktop(backend="uia").windows():
        title = w.window_text() or ""
        if "電卓" in title or "Calculator" in title:
            wins.append(w)
    return wins


def get_calc_dialog(timeout: float = 25.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in list_calc_windows():
            try:
                if w.is_visible() and w.handle:
                    app = Application(backend="uia").connect(handle=w.handle)
                    dlg = app.window(handle=w.handle)
                    if dlg.exists(timeout=1):
                        return dlg, w.handle, w.window_text()
            except Exception:
                continue
        time.sleep(0.4)
    raise RuntimeError(
        f"Calculator window not found (seen={[w.window_text() for w in list_calc_windows()]})"
    )


def click(dlg, auto_id: str) -> None:
    btn = dlg.child_window(auto_id=auto_id, control_type="Button")
    btn.wait("exists enabled visible ready", timeout=8)
    btn.click_input()
    time.sleep(0.2)


def read_result(dlg) -> str:
    for auto_id in ("CalculatorResults", "NormalOutput"):
        try:
            ctrl = dlg.child_window(auto_id=auto_id)
            if ctrl.exists(timeout=1):
                name = ctrl.window_text() or ctrl.element_info.name or ""
                if name.strip():
                    return name.strip()
        except Exception:
            continue

    for ctrl in dlg.descendants(control_type="Text"):
        text = (ctrl.window_text() or "").strip()
        if text and any(ch.isdigit() for ch in text):
            return text
    return "(result not readable)"


def dump_buttons(dlg) -> None:
    print("--- buttons (auto_id / name) ---")
    for btn in dlg.descendants(control_type="Button"):
        info = btn.element_info
        print(f"id={info.automation_id!r} name={info.name!r}")


def operate_with_uia(dlg) -> str:
    for clear_id in ("clearButton", "clearEntryButton"):
        try:
            click(dlg, clear_id)
            break
        except Exception:
            continue

    for auto_id in ("num1Button", "plusButton", "num2Button", "equalButton"):
        click(dlg, auto_id)
    time.sleep(0.5)
    return read_result(dlg)


def operate_with_keys(dlg) -> str:
    dlg.set_focus()
    time.sleep(0.3)
    send_keys("{ESC}")
    time.sleep(0.2)
    send_keys("1{+}2{ENTER}")
    time.sleep(0.5)
    return read_result(dlg)


def main() -> int:
    kill_calculators()

    Application(backend="uia").start("calc.exe")
    time.sleep(3.0)

    if not list_calc_windows():
        subprocess.run(["cmd", "/c", "start", "", "calc.exe"], check=False)
        time.sleep(3.0)

    dlg, handle, title = get_calc_dialog()
    print(f"CONNECTED title={title!r} handle={handle}")
    dlg.set_focus()
    time.sleep(0.4)

    try:
        result = operate_with_uia(dlg)
        method = "uia-buttons"
    except Exception as uia_err:
        print(f"WARN: UIA button click failed: {uia_err}")
        try:
            dump_buttons(dlg)
        except Exception:
            pass
        result = operate_with_keys(dlg)
        method = "send-keys"

    print(f"METHOD={method}")
    print(f"RESULT={result}")
    print("OK: Calculator operated from WSL via Windows pywinauto")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
