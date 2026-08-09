#!/usr/bin/env bash
# WSL から Windows 電卓を起動し、Windows Python + pywinauto で GUI 操作する
set -euo pipefail

export PATH="/mnt/c/Windows/System32/WindowsPowerShell/v1.0:/mnt/c/Windows/System32:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_PY="${SCRIPT_DIR}/automate_calc.py"

if ! command -v powershell.exe >/dev/null 2>&1; then
  echo "ERROR: powershell.exe not found. Is WSL interop enabled?" >&2
  exit 1
fi

WIN_HOME_WIN="$(powershell.exe -NoProfile -Command 'Write-Output $env:USERPROFILE' | tr -d '\r')"
if [[ -z "${WIN_HOME_WIN}" ]]; then
  echo "ERROR: failed to resolve Windows USERPROFILE" >&2
  exit 1
fi

# C:\Users\name → /mnt/c/Users/name
WIN_HOME_MNT="$(echo "${WIN_HOME_WIN}" | sed -E 's#^([A-Za-z]):\\#/mnt/\L\1/#; s#\\#/#g')"
WIN_DIR_MNT="${WIN_HOME_MNT}/wsl-win-gui"

mkdir -p "${WIN_DIR_MNT}"
cp "${SRC_PY}" "${WIN_DIR_MNT}/automate_calc.py"

powershell.exe -NoProfile -Command \
  "if (-not (python -c 'import pywinauto' 2>\$null)) { python -m pip install --user pywinauto }; python (Join-Path \$env:USERPROFILE 'wsl-win-gui\\automate_calc.py')"
