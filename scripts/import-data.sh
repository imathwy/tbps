#!/usr/bin/env bash
set -eu -o pipefail

./scripts/init-db.sh
./scripts/decompress.sh
fd --no-ignore -e sql -x ./scripts/exec-sql-file.sh
