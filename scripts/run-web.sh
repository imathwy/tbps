#!/usr/bin/env bash
set -eu -o pipefail

./scripts/build-lean.sh

cd tbps-be || exit 1
uv add -r requirements.txt
uv run main_server.py &
PID_BE=$!
cd ..

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
