#!/usr/bin/env bash
set -euo pipefail
make lint
make test
bash scripts/check_repo_hygiene.sh
