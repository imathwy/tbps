#!/usr/bin/env bash
set -eu -o pipefail

(docker compose up --wait)
sleep 10

echo "SELECT 'CREATE DATABASE mathlib_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mathlib_db')\gexec" | \
docker exec -i \
  tbps-postgres \
    psql \
      -U postgres \
      -h 127.0.0.1 \
      -p 5432
