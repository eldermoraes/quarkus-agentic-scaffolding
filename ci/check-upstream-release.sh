#!/usr/bin/env bash
# Report whether an upstream project has published a minor line newer than the one this repo
# currently tracks in ci/baseline.env.
#
#   check-upstream-release.sh <owner/repo> <BASELINE_VAR>
#
# Prints `key=value` lines suitable for redirecting into "$GITHUB_OUTPUT". Always prints
# `new_line`, which is empty when the newest upstream minor is the one already tracked — the
# caller gates on that. Patch releases inside the tracked line are deliberately NOT reported:
# Renovate raises those as PRs, and the weekly cron already builds against the live platform.
#
# Requires `gh` authenticated with GH_TOKEN.
set -euo pipefail

repo=${1:?usage: check-upstream-release.sh <owner/repo> <BASELINE_VAR>}
baseline_var=${2:?usage: check-upstream-release.sh <owner/repo> <BASELINE_VAR>}

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
baseline_file="$script_dir/baseline.env"

# Read the tracked version without sourcing the file (it is data, not code).
baseline=$(sed -n "s/^${baseline_var}=\\([^[:space:]]*\\).*/\\1/p" "$baseline_file" | head -n1)
if [ -z "$baseline" ]; then
  echo "No ${baseline_var} entry in ${baseline_file}" >&2
  exit 1
fi

# Newest stable release. Drafts, pre-releases, and anything that is not strictly X.Y.Z
# (candidate builds such as 3.38.0.CR1) are excluded before sorting.
latest=$(gh api "repos/${repo}/releases?per_page=100" \
  --jq '.[] | select(.draft == false and .prerelease == false) | .tag_name' |
  grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' |
  sort -V | tail -n1)

if [ -z "$latest" ]; then
  echo "No stable X.Y.Z release found for ${repo}" >&2
  exit 1
fi

# First two fields only: the platform baseline may be a respin (3.40.1.1), whose minor line is
# still 3.40.
minor_of() { printf '%s' "$1" | cut -d. -f1,2; }
baseline_minor=$(minor_of "$baseline")
latest_minor=$(minor_of "$latest")

echo "tracked=$baseline"
echo "latest=$latest"

# A newer minor line exists only if latest_minor sorts strictly above baseline_minor.
if [ "$baseline_minor" = "$latest_minor" ]; then
  echo 'new_line='
  exit 0
fi
highest=$(printf '%s\n%s\n' "$baseline_minor" "$latest_minor" | sort -V | tail -n1)
if [ "$highest" = "$baseline_minor" ]; then
  # Upstream's newest stable is older than what we track (a re-tag, or a baseline ahead of
  # the release feed). Not something to announce.
  echo 'new_line='
  exit 0
fi

echo "new_line=$latest_minor"
echo "version=$latest"
echo "notes_url=https://github.com/${repo}/releases/tag/${latest}"
