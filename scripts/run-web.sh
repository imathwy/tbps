#!/usr/bin/env bash
set -eu -o pipefail

./scripts/build-lean.sh
uv add -r requirements.txt

uv run main_server.py &
PID_BE=$!

cd tbps-fe || exit 1
pnpm i
pnpm dev &
PID_FE=$!
cd ..

cleanup() {
  kill $PID_BE $PID_FE 2>/dev/null
}

trap cleanup EXIT
wait
