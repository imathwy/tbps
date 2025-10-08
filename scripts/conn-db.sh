#!/usr/bin/env bash
set -eu -o pipefail

docker exec -it \
  tbps-postgres \
    psql \
      -U postgres \
      -h 127.0.0.1 \
      -p 5432 \
      -d mathlib_db
