#!/usr/bin/env bash
# Bump the project version and roll the changelog.
#
# Usage: scripts/bump-version.sh <major|minor|patch|X.Y.Z[-prerelease]>
#
# Updates VERSION and CHANGELOG.md only. It does not commit, tag or push.
# See docs/VERSIONING.md for the versioning rules.

set -euo pipefail

REPO_URL="https://github.com/FHTW-AI25/CiteGuard"
SEMVER_RE='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?$'

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version_file="$root/VERSION"
changelog="$root/CHANGELOG.md"

die() { echo "error: $*" >&2; exit 1; }

[ $# -eq 1 ] || die "usage: $0 <major|minor|patch|X.Y.Z[-prerelease]>"
[ -f "$version_file" ] || die "VERSION file not found"
[ -f "$changelog" ] || die "CHANGELOG.md not found"

current="$(tr -d '[:space:]' < "$version_file")"
[[ "$current" =~ $SEMVER_RE ]] || die "VERSION contains '$current', which is not a semantic version"

core="${current%%-*}"
IFS=. read -r major minor patch <<< "$core"

case "$1" in
  major) new="$((major + 1)).0.0" ;;
  minor) new="$major.$((minor + 1)).0" ;;
  patch)
    # Releasing a pre-release (1.2.3-rc.1) as patch gives 1.2.3.
    if [ "$core" != "$current" ]; then new="$core"; else new="$major.$minor.$((patch + 1))"; fi
    ;;
  *)
    new="${1#v}"
    [[ "$new" =~ $SEMVER_RE ]] || die "'$1' is not major, minor, patch or a semantic version"
    ;;
esac

[ "$new" != "$current" ] || die "version is already $current"
grep -q "^## \[$new\]" "$changelog" && die "CHANGELOG.md already has a section for $new"
grep -q '^## \[Unreleased\]' "$changelog" || die "CHANGELOG.md has no '## [Unreleased]' section"

# Require at least one non-blank line between the Unreleased heading and the next one.
unreleased="$(awk '
  /^## \[Unreleased\]/ { on = 1; next }
  on && (/^## \[/ || /^\[[^]]+\]: /) { exit }
  on && NF { print }
' "$changelog")"
[ -n "$unreleased" ] || die "the Unreleased section of CHANGELOG.md is empty; add entries before releasing"

today="$(date +%Y-%m-%d)"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

awk -v new="$new" -v cur="$current" -v today="$today" -v url="$REPO_URL" '
  /^## \[Unreleased\]/ {
    print
    print ""
    print "## [" new "] - " today
    next
  }
  /^\[Unreleased\]: / {
    print "[Unreleased]: " url "/compare/v" new "...HEAD"
    print "[" new "]: " url "/compare/v" cur "...v" new
    next
  }
  { print }
' "$changelog" > "$tmp"

cat "$tmp" > "$changelog"
echo "$new" > "$version_file"

echo "Bumped $current -> $new"
echo
echo "Review the changes, then:"
echo "  git commit -am \"Release v$new\""
echo "  git tag -a v$new -m \"v$new\""
echo "  git push origin main --follow-tags"
