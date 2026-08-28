#!/usr/bin/env bash
set -Eeuo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_dir"

python_command="${SAFETEST_PYTHON:-}"
if [[ -z "$python_command" ]]; then
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      python_command="$candidate"
      break
    fi
  done
fi

if [[ -z "$python_command" ]] || ! command -v "$python_command" >/dev/null 2>&1; then
  printf '%s\n' "未找到 Python 3.9+。请安装后重试。" >&2
  exit 1
fi

if ! "$python_command" -c 'import sys; raise SystemExit(sys.version_info < (3, 9))'; then
  printf '%s\n' "Python 版本过低，需要 Python 3.9 或更高版本。" >&2
  exit 1
fi

venv_dir=".venv"
if [[ -e "$venv_dir" ]] && ! "$venv_dir/bin/python" -c 'import sys' >/dev/null 2>&1; then
  platform_tag=$(uname -s | tr '[:upper:]' '[:lower:]')
  architecture_tag=$(uname -m | tr '[:upper:]' '[:lower:]')
  venv_dir=".venv-${platform_tag}-${architecture_tag}"
fi
venv_python="$venv_dir/bin/python"

if [[ ! -x "$venv_python" ]]; then
  printf '%s\n' "首次运行：正在创建独立 Python 环境……"
  "$python_command" -m venv "$venv_dir"
fi

requirements_hash=$(
  "$python_command" -c 'import hashlib, pathlib; print(hashlib.sha256(pathlib.Path("requirements.txt").read_bytes()).hexdigest())'
)
installed_hash=""
marker_path="$venv_dir/.requirements.sha256"
if [[ -f "$marker_path" ]]; then
  installed_hash=$(<"$marker_path")
fi

if [[ "$requirements_hash" != "$installed_hash" ]]; then
  printf '%s\n' "正在安装/更新依赖（仅首次或依赖变化时执行）……"
  "$venv_python" -m pip install --upgrade "pip<26"
  "$venv_python" -m pip install -r requirements.txt
  printf '%s\n' "$requirements_hash" > "$marker_path"
fi

if [[ ! -f "environment.py" ]]; then
  cp environment_template.py environment.py
fi

exec "$venv_python" main.py "$@"
