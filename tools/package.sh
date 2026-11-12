#!/usr/bin/env bash
# Build the site and zip exactly what a web host needs. Usage: tools/package.sh [out.zip]
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/build.py >/dev/null
OUT="${1:-$HOME/Desktop/bluemindmi-site.zip}"
rm -f "$OUT"
zip -qr "$OUT" *.html assets photos robots.txt sitemap.xml .htaccess -x 'photos/README.md' '*.DS_Store'
echo "wrote $OUT ($(du -h "$OUT" | cut -f1)) — upload and extract into public_html"
