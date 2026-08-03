#!/usr/bin/env bash
# agent-skills installer (v1.4.0)
#
# 全部一発 (default catalog only; optional skills excluded):
#   curl -fsSL https://cdn.jsdelivr.net/gh/kuwa2005/agent-skills@main/install.sh | bash
#   curl -fsSL ... | bash -s -- --all
#
# オプションも含めて全部:
#   curl -fsSL ... | bash -s -- --everything
#
# 個別 (default or optional):
#   curl -fsSL ... | bash -s -- prevent-secret-leak
#   curl -fsSL ... | bash -s -- frontend-design
#   curl -fsSL ... | bash -s -- verify,frontend-design
set -euo pipefail

REPO="${AGENT_SKILLS_REPO:-kuwa2005/agent-skills}"
REF="${AGENT_SKILLS_REF:-main}"
RAW_BASE="https://cdn.jsdelivr.net/gh/${REPO}@${REF}"
TARBALL_URL="https://codeload.github.com/${REPO}/tar.gz/${REF}"

CURSOR_SKILLS_DIR="${CURSOR_SKILLS_DIR:-$HOME/.cursor/skills}"
OPENCODE_SKILLS_DIR="${OPENCODE_SKILLS_DIR:-$HOME/.config/opencode/skills}"

MUTED='\033[0;2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

install_cursor=true
install_opencode=true
list_only=false
show_help=false
force_remote=false
install_all=false
install_everything=false
skills_requested=()

SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
LOCAL_ROOT=""
if [[ -n "$SCRIPT_DIR" && -f "${SCRIPT_DIR}/skills/catalog.txt" ]]; then
  LOCAL_ROOT="$SCRIPT_DIR"
fi

# Populated for remote installs (extracted tarball skills/)
REMOTE_SKILLS_ROOT=""
WORKDIR=""

usage() {
  cat <<EOF
agent-skills installer v1.4.0

Install Agent Skills for Cursor (~/.cursor/skills) and OpenCode (~/.config/opencode/skills).
Copies each skill directory in full (SKILL.md + scripts/ and other assets).

全部一発インストール (default skills only; optional excluded):
  curl -fsSL ${RAW_BASE}/install.sh | bash
  curl -fsSL ${RAW_BASE}/install.sh | bash -s -- --all
  ./install.sh --all

オプションも含めて全部インストール:
  curl -fsSL ${RAW_BASE}/install.sh | bash -s -- --everything
  ./install.sh --everything

個別インストール (default or optional skills):
  curl -fsSL ${RAW_BASE}/install.sh | bash -s -- prevent-secret-leak
  curl -fsSL ${RAW_BASE}/install.sh | bash -s -- frontend-design
  curl -fsSL ${RAW_BASE}/install.sh | bash -s -- verify,frontend-design
  ./install.sh frontend-design

Options:
  -h, --help           Show this help
  -l, --list           List default and optional skills, then exit
  -a, --all            Install all DEFAULT skills (not optional)
  --everything         Install default + optional skills
  --cursor-only        Install to Cursor only
  --opencode-only      Install to OpenCode only
  --remote             Force download from GitHub (ignore local checkout)
  --ref <ref>          Git ref (branch/tag/commit). Default: main
                       Implies --remote. Or set AGENT_SKILLS_REF

Notes:
  - No skill names / --all → install catalog.txt only
  - --everything → catalog.txt + optional.txt
  - Optional skills alone still require explicit names (or --everything)
  - Skill names may be space- or comma-separated
EOF
}

log()  { printf '%b\n' "$*" >&2; }
info() { log "${MUTED}$*${NC}"; }
ok()   { log "${GREEN}$*${NC}"; }
err()  { log "${RED}$*${NC}"; }

# User-facing lines that must stay on stdout (list / progress arrows)
out() { printf '%b\n' "$*"; }

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Error: '$1' is required but not installed."
    exit 1
  fi
}

cleanup() {
  if [[ -n "${WORKDIR:-}" && -d "${WORKDIR:-}" ]]; then
    rm -rf "$WORKDIR"
  fi
}
trap cleanup EXIT

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) show_help=true; shift ;;
    -l|--list) list_only=true; shift ;;
    -a|--all) install_all=true; shift ;;
    --everything|--with-optional|--full) install_everything=true; shift ;;
    --cursor-only) install_opencode=false; shift ;;
    --opencode-only) install_cursor=false; shift ;;
    --remote) force_remote=true; shift ;;
    --ref)
      if [[ -z "${2:-}" ]]; then err "Error: --ref requires an argument"; exit 1; fi
      REF="$2"
      RAW_BASE="https://cdn.jsdelivr.net/gh/${REPO}@${REF}"
      TARBALL_URL="https://codeload.github.com/${REPO}/tar.gz/${REF}"
      force_remote=true
      shift 2
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do skills_requested+=("$1"); shift; done
      ;;
    -*)
      err "Error: unknown option '$1'"
      usage
      exit 1
      ;;
    *)
      # Allow comma-separated names in one argv: verify,xlsm2spec
      if [[ "$1" == *,* ]]; then
        IFS=',' read -r -a _parts <<< "$1"
        for _p in "${_parts[@]}"; do
          _p="${_p//[[:space:]]/}"
          [[ -n "$_p" ]] && skills_requested+=("$_p")
        done
      else
        skills_requested+=("$1")
      fi
      shift
      ;;
  esac
done

if [[ "$show_help" == true ]]; then
  usage
  exit 0
fi

need_cmd curl
need_cmd mkdir
need_cmd mktemp
need_cmd cp
need_cmd grep
need_cmd tar

if [[ "$force_remote" == true ]]; then
  LOCAL_ROOT=""
fi

parse_catalog() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    return 0
  fi
  grep -vE '^\s*(#|$)' "$file" | sed 's/[[:space:]]*$//' | grep -v '^$' || true
}

list_default_skills() {
  parse_catalog "$(skills_root)/catalog.txt"
}

list_optional_skills() {
  parse_catalog "$(skills_root)/optional.txt"
}

list_all_known_skills() {
  { list_default_skills; list_optional_skills; } | sort -u
}

ensure_remote_bundle() {
  if [[ -n "$LOCAL_ROOT" ]]; then
    return 0
  fi
  if [[ -n "$REMOTE_SKILLS_ROOT" && -d "$REMOTE_SKILLS_ROOT" ]]; then
    return 0
  fi

  WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/agent-skills.XXXXXX")"
  info "Downloading ${REPO}@${REF} ..."
  if ! curl -fsSL "$TARBALL_URL" -o "${WORKDIR}/src.tar.gz"; then
    err "Error: failed to download ${TARBALL_URL}"
    exit 1
  fi
  mkdir -p "${WORKDIR}/extract"
  tar -xzf "${WORKDIR}/src.tar.gz" -C "${WORKDIR}/extract"
  # Prefer deterministic path: <repo>-<ref>/skills
  if [[ -f "${WORKDIR}/extract/${REPO##*/}-${REF}/skills/catalog.txt" ]]; then
    REMOTE_SKILLS_ROOT="${WORKDIR}/extract/${REPO##*/}-${REF}/skills"
  else
    REMOTE_SKILLS_ROOT="$(find "${WORKDIR}/extract" -mindepth 2 -maxdepth 2 -type d -name skills | head -n 1)"
  fi
  if [[ -z "$REMOTE_SKILLS_ROOT" || ! -f "${REMOTE_SKILLS_ROOT}/catalog.txt" ]]; then
    err "Error: skills/catalog.txt not found in archive"
    exit 1
  fi
}

# Print ONLY the skills root path on stdout (no logs).
# Call ensure_remote_bundle (or rely on LOCAL_ROOT) before using this.
skills_root() {
  if [[ -n "$LOCAL_ROOT" ]]; then
    printf '%s' "${LOCAL_ROOT}/skills"
    return 0
  fi
  printf '%s' "$REMOTE_SKILLS_ROOT"
}

copy_skill_dir() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  mkdir -p "$dest"
  # Copy contents (including hidden files except . and ..)
  cp -a "$src"/. "$dest"/
}

install_skill() {
  local name="$1"
  local root src

  root="$(skills_root)"
  src="${root}/${name}"
  if [[ ! -d "$src" || ! -f "${src}/SKILL.md" ]]; then
    err "Error: skill '${name}' not found at ${src}"
    return 1
  fi

  if [[ "$install_cursor" == true ]]; then
    copy_skill_dir "$src" "${CURSOR_SKILLS_DIR}/${name}"
    ok "  cursor:   ${CURSOR_SKILLS_DIR}/${name}/"
  fi

  if [[ "$install_opencode" == true ]]; then
    copy_skill_dir "$src" "${OPENCODE_SKILLS_DIR}/${name}"
    ok "  opencode: ${OPENCODE_SKILLS_DIR}/${name}/"
  fi
}

info "agent-skills installer"
if [[ -n "$LOCAL_ROOT" ]]; then
  info "source: local ${LOCAL_ROOT}"
else
  info "source: ${REPO}@${REF}"
fi
echo >&2

# Prepare source once in this shell (avoid losing state in pipelines/subshells)
if [[ -z "$LOCAL_ROOT" ]]; then
  ensure_remote_bundle
fi

mapfile -t default_skills < <(list_default_skills | sort -u)
mapfile -t optional_skills < <(list_optional_skills | sort -u)
mapfile -t available < <(list_all_known_skills)

if [[ ${#default_skills[@]} -eq 0 ]]; then
  err "Error: no default skills found in catalog.txt"
  exit 1
fi

if [[ "$list_only" == true ]]; then
  out "Default skills (installed by --all / bare curl|bash):"
  for s in "${default_skills[@]}"; do
    out "  - $s"
  done
  out "Optional skills (explicit name, or included by --everything):"
  if [[ ${#optional_skills[@]} -eq 0 ]]; then
    out "  (none)"
  else
    for s in "${optional_skills[@]}"; do
      out "  - $s"
    done
  fi
  exit 0
fi

if [[ "$install_everything" == true && "$install_all" == true ]]; then
  info "--everything specified; --all is redundant"
fi

targets=()
if [[ "$install_everything" == true ]]; then
  if [[ ${#skills_requested[@]} -gt 0 ]]; then
    info "--everything specified; ignoring individual skill names: ${skills_requested[*]}"
  fi
  mapfile -t targets < <(list_all_known_skills)
  info "Mode: EVERYTHING (${#targets[@]} skills; default + optional)"
elif [[ "$install_all" == true || ${#skills_requested[@]} -eq 0 ]]; then
  if [[ "$install_all" == true && ${#skills_requested[@]} -gt 0 ]]; then
    info "--all specified; ignoring individual skill names: ${skills_requested[*]}"
  fi
  targets=("${default_skills[@]}")
  info "Mode: ALL defaults (${#targets[@]} skills; optional excluded)"
else
  # Expand any remaining comma-separated tokens and dedupe while preserving order
  expanded=()
  for req in "${skills_requested[@]}"; do
    if [[ "$req" == *,* ]]; then
      IFS=',' read -r -a _parts <<< "$req"
      for _p in "${_parts[@]}"; do
        _p="${_p//[[:space:]]/}"
        [[ -n "$_p" ]] && expanded+=("$_p")
      done
    else
      expanded+=("$req")
    fi
  done

  for req in "${expanded[@]}"; do
    found=false
    for a in "${available[@]}"; do
      if [[ "$a" == "$req" ]]; then
        found=true
        break
      fi
    done
    if [[ "$found" != true ]]; then
      err "Error: unknown skill '${req}'"
      err "Use --list to see default and optional skills."
      exit 1
    fi
    already=false
    for t in "${targets[@]+"${targets[@]}"}"; do
      if [[ "$t" == "$req" ]]; then
        already=true
        break
      fi
    done
    if [[ "$already" != true ]]; then
      targets+=("$req")
    fi
  done
  info "Mode: SELECTED (${#targets[@]}): ${targets[*]}"
fi

echo >&2
for name in "${targets[@]}"; do
  out "→ ${name}"
  install_skill "$name"
done

echo >&2
ok "Done."
info "Cursor skills dir:   ${CURSOR_SKILLS_DIR}"
info "OpenCode skills dir: ${OPENCODE_SKILLS_DIR}"
info "New agent sessions may be required to pick up skills."
echo >&2
