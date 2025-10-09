#!/usr/bin/env bash
set -eu -o pipefail

cd tbps-be/Lean_tool && lake build
