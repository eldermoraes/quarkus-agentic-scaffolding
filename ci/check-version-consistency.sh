#!/usr/bin/env bash
# Fails unless every file in the canonical inventory carries the same version.
set -euo pipefail
exec python3 "$(dirname "${BASH_SOURCE[0]}")/versioning.py" check "$@"
