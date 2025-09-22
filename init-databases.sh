#!/bin/bash
# 初始化多个数据库
psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE mathlib_db;"
psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE wl_encodings_db;"
psql -U "$POSTGRES_USER" -d mathlib_db -f /docker-entrypoint-initdb.d/mathlib_filtered_backup0515.sql
psql -U "$POSTGRES_USER" -d wl_encodings_db -f /docker-entrypoint-initdb.d/wl_encodings_new_backup0515.sql