#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Create or update the labels listed in .github/labels.yml.
# Not run by CI. Run it by hand from the maintainer's gh login:
#   scripts/sync-labels.sh [owner/repo]     (default ChiefGyk3D/LLMFAO)
# Add --dry-run as the second argument to print what would run.
set -euo pipefail

repo="${1:-ChiefGyk3D/LLMFAO}"
dry="${2:-}"
file="$(dirname "$0")/../.github/labels.yml"

name="" color="" desc=""
flush() {
  [ -n "$name" ] || return 0
  if [ "$dry" = "--dry-run" ]; then
    echo "gh label create $name --color $color --force -R $repo"
  else
    gh label create "$name" --color "$color" --description "$desc" --force -R "$repo"
  fi
  name="" color="" desc=""
}
while IFS= read -r line; do
  case "$line" in
    "- name: "*) flush; name="${line#- name: }" ;;
    "  color: "*) color="${line#  color: }"; color="${color//\"/}" ;;
    "  description: "*) desc="${line#  description: }"; desc="${desc#\"}"; desc="${desc%\"}" ;;
  esac
done < "$file"
flush
