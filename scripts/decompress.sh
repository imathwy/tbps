#!/usr/bin/env bash
set -eu -o pipefail

(cd data && fd --no-ignore -e sql -x rm)
(cd data && fd -e xz -x xz --decompress --keep)
