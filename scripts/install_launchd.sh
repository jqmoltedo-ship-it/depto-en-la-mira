#!/bin/sh
set -eu

days="${1:-2}"
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
agent_dir="$HOME/Library/LaunchAgents"
plist="$agent_dir/com.local.departamentos.plist"
mkdir -p "$agent_dir"
python_dir=$(dirname "$(command -v python3)")
git_dir=$(dirname "$(command -v git)")
interval_seconds=$((days * 24 * 60 * 60))
job_path="$python_dir:$git_dir:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"

sed -e "s|__PROJECT__|$project_dir|g" -e "s|__PATH__|$job_path|g" \
    -e "s|__INTERVAL_SECONDS__|$interval_seconds|g" \
    "$project_dir/scripts/launchd.plist.template" > "$plist"
launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"
echo "Instalado: ejecucion cada $days dia(s) (corre ahora y luego cada $interval_seconds segundos)"

