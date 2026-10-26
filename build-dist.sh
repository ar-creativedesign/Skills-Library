#!/usr/bin/env bash
# Build one zip per skill in dist/ (also done by CI on tagged releases) for uploading to the Claude app (Settings → Capabilities → Skills).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$REPO/dist"
cd "$REPO/skills"
for s in */; do
  s="${s%/}"
  rm -f "$REPO/dist/$s.zip"
  zip -qr "$REPO/dist/$s.zip" "$s" -x '*.DS_Store'
  echo "dist/$s.zip"
done
