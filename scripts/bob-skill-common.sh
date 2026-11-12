#!/usr/bin/env bash
# Shared ownership rule for the repository's Bob install/uninstall helpers.
# Source this from the checkout; it is not installed into a user's .bob directory.
# Keep the uninstaller's existing name-reading semantics, including CRLF manifests.
bob_skill_declared_name() {
  if [[ -f "$1" && -r "$1" ]]; then
    awk '/^name:/ {
      sub(/^name:[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); print; exit
    }' "$1" | tr -d '\r'
  fi
}

# The installer must not write through any symlink, including .bob/ or skills/.
# Include broken links (-e alone misses them) and the user-supplied base path.
bob_skill_has_symlink() {
  local path="$1"
  while :; do
    if [[ -L "$path" ]]; then
      return 0
    fi
    case "$path" in /|.) return 1 ;; esac
    path="$(dirname -- "$path")"
  done
}
