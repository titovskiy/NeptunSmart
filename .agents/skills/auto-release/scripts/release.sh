#!/usr/bin/env bash
set -euo pipefail

GH_BIN=$(command -v gh || echo "/opt/homebrew/bin/gh")
if [ ! -x "$GH_BIN" ]; then
  echo "Error: gh (GitHub CLI) not found!" >&2
  exit 1
fi

VERSION="${1:-}"
TITLE="${2:-}"
NOTES="${3:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version> [title] [notes]"
  echo "Example: $0 0.7.2 'Neptun Smart v0.7.2' 'Fix sensor state mapping'"
  exit 1
fi

PLAIN_VERSION="${VERSION#v}"
TAG="v${PLAIN_VERSION}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

MANIFEST="custom_components/neptun_smart_local/manifest.json"
HACS_JSON="hacs.json"

# Ensure hacs.json exists
if [ ! -f "$HACS_JSON" ]; then
  echo "Creating missing hacs.json..."
  cat <<'EOF' > "$HACS_JSON"
{
  "name": "Neptun Smart",
  "render_readme": true
}
EOF
  git add "$HACS_JSON"
fi

# Update version in manifest.json
if [ -f "$MANIFEST" ]; then
  sed -i '' -E "s/\"version\": \"[^\"]+\"/\"version\": \"$PLAIN_VERSION\"/" "$MANIFEST"
  git add "$MANIFEST"
fi

# Stage tracked changes
git add -u

# Commit if there are staged changes
if ! git diff --cached --quiet; then
  git commit -m "Release $TAG: ${NOTES:-Bump version to $PLAIN_VERSION}"
fi

# Push main
git push origin main

# Create and push annotated tag
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG already exists, updating tag..."
  git tag -fa "$TAG" -m "Release $TAG: ${NOTES:-$TAG}"
  git push -f origin "$TAG"
else
  git tag -a "$TAG" -m "Release $TAG: ${NOTES:-$TAG}"
  git push origin "$TAG"
fi

# Create or update GitHub release
RELEASE_TITLE="${TITLE:-Neptun Smart $TAG}"
RELEASE_NOTES="${NOTES:-Release $TAG}"

if "$GH_BIN" release view "$TAG" >/dev/null 2>&1; then
  "$GH_BIN" release edit "$TAG" --title "$RELEASE_TITLE" --notes "$RELEASE_NOTES"
else
  "$GH_BIN" release create "$TAG" --title "$RELEASE_TITLE" --notes "$RELEASE_NOTES"
fi

echo "Successfully published $TAG to GitHub!"
