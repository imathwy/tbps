#!/usr/bin/env bash
set -eu -o pipefail

./scripts/build-lean.sh
uv add -r requirements.txt
uv run search_app/main_new.py
