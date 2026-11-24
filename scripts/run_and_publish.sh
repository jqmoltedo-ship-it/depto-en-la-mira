#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"

python3 -m real_estate_scraper run

cp data/report.html docs/index.html
if ! git diff --quiet -- docs/index.html; then
    export GIT_SSH_COMMAND="ssh -o IdentitiesOnly=yes -i $HOME/.ssh/id_ed25519_depto_scraper"
    git add docs/index.html
    git commit -m "Actualiza reporte $(date '+%Y-%m-%d %H:%M')" --quiet
    git push origin main --quiet
fi
