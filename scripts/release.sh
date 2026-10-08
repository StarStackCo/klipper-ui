#!/usr/bin/env bash
# Release dev -> stable in both repos and tag the version (klipper-ui D-087).
#   scripts/release.sh v0.2.0 "Short description"
# Versions stay 0.x until the first unit ships (D-088); v1.0.0 needs FIRST_UNIT_SHIPPED=1.
# For each repo with new commits on dev: opens the dev -> stable PR, waits for its checks (stops on
# a failure), merges it, brings dev level with stable. Then tags both stable branches with the
# version (klipper-ui only: the fork already carries upstream KlipperScreen's v0.x tags, so it keeps
# its upstream-based version and the klipper-ui tag records which fork commit belongs to it, D-091).
# Printers get it with "Update everything".
# Needs: gh logged in; both repos clean, on dev and pushed. Run the bench/S1 checklist first.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FORK="${KS_FORK:-$ROOT/../KlipperScreen-starstack}"
GH="$(command -v gh || echo "/c/Program Files/GitHub CLI/gh.exe")"
VER="${1:?usage: release.sh vX.Y.Z \"description\"}"
DESC="${2:?usage: release.sh vX.Y.Z \"description\"}"
[[ "$VER" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "version must look like v1.2.3"; exit 2; }
if [[ ! "$VER" =~ ^v0\. ]] && [ "${FIRST_UNIT_SHIPPED:-}" != 1 ]; then
  echo "versions stay 0.x until the first unit ships (D-088)"; exit 2
fi

REPOS=("$ROOT|StarStackCo/klipper-ui|main" "$FORK|StarStackCo/KlipperScreen-starstack|starstack")

for r in "${REPOS[@]}"; do  # check everything before changing anything
  IFS='|' read -r dir slug stable <<< "$r"
  git -C "$dir" fetch -q --tags origin
  [ -z "$(git -C "$dir" status --porcelain)" ] || { echo "$slug: uncommitted changes"; exit 1; }
  [ "$(git -C "$dir" branch --show-current)" = dev ] || { echo "$slug: not on dev"; exit 1; }
  [ "$(git -C "$dir" rev-parse dev)" = "$(git -C "$dir" rev-parse origin/dev)" ] || { echo "$slug: dev not pushed"; exit 1; }
done
if git -C "$ROOT" rev-parse -q --verify "refs/tags/$VER" >/dev/null; then echo "klipper-ui: $VER already exists"; exit 1; fi

for r in "${REPOS[@]}"; do
  IFS='|' read -r dir slug stable <<< "$r"
  ahead=$(git -C "$dir" rev-list --count "origin/$stable..origin/dev")
  if [ "$ahead" -gt 0 ]; then
    echo "== $slug: $ahead commits dev -> $stable"
    url=$("$GH" pr create -R "$slug" --base "$stable" --head dev --title "$VER: $DESC" \
      --body "$(printf 'Release %s: %s\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)' "$VER" "$DESC")")
    echo "   $url"
    sleep 15
    "$GH" pr checks "$url" -R "$slug" --watch --fail-fast --interval 15 >/dev/null \
      || { echo "   checks failed: fix on dev, then re-run (the PR stays open)"; exit 1; }
    "$GH" pr merge "$url" -R "$slug" --merge
    git -C "$dir" fetch -q origin
    git -C "$dir" push -q origin "origin/$stable:refs/heads/dev"
    git -C "$dir" fetch -q origin && git -C "$dir" merge -q --ff-only origin/dev
  else
    echo "== $slug: nothing new on dev"
  fi
  echo "   $stable is at $(git -C "$dir" describe --tags --always "origin/$stable")"
done
fork_at=$(git -C "$FORK" rev-parse --short origin/starstack)
git -C "$ROOT" tag -a "$VER" origin/main -m "StarStack $VER: $DESC" -m "Touchscreen: KlipperScreen-starstack $fork_at"
git -C "$ROOT" push -q origin "$VER"
echo "   tagged klipper-ui $VER on main ($(git -C "$ROOT" rev-parse --short origin/main)), touchscreen $fork_at"
echo "Released $VER. Add a row to the build/deploy log in docs/DECISIONS.md."
