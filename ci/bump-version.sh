#!/usr/bin/env bash
# Update the canonical release inventory and re-copy convention seeds.
set -euo pipefail
exec python3 "$(dirname "${BASH_SOURCE[0]}")/versioning.py" bump "$@"
