#!/usr/bin/env bash
set -eu -o pipefail

cd Lean_tool && lake build
