#!/usr/bin/env bash
set -eu -o pipefail

nix build '.#tbps-be' && docker load -i result
