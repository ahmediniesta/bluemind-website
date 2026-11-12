#!/usr/bin/env bash
# Push the built site to GoDaddy Web Hosting over SFTP/FTPS with lftp.
# One-time: brew install lftp. Credentials come from cPanel → FTP Accounts (or SSH access).
#   GODADDY_HOST=ftp.bluemindmi.com GODADDY_USER=... GODADDY_PASS=... tools/deploy_godaddy.sh [--dry-run]
set -euo pipefail
cd "$(dirname "$0")/.."
: "${GODADDY_HOST:?set GODADDY_HOST}"; : "${GODADDY_USER:?set GODADDY_USER}"; : "${GODADDY_PASS:?set GODADDY_PASS}"
REMOTE="${GODADDY_REMOTE_DIR:-public_html}"
DRY=""; [[ "${1:-}" == "--dry-run" ]] && DRY="--dry-run"
python3 tools/build.py >/dev/null
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
cp -R assets photos ./*.html robots.txt sitemap.xml .htaccess "$STAGE"/ && rm -f "$STAGE/photos/README.md"
lftp -u "$GODADDY_USER,$GODADDY_PASS" "sftp://$GODADDY_HOST" -e "set sftp:auto-confirm yes; mirror -R --delete --verbose $DRY '$STAGE' '$REMOTE'; bye" \
  || lftp -u "$GODADDY_USER,$GODADDY_PASS" "ftps://$GODADDY_HOST" -e "set ssl:verify-certificate yes; mirror -R --delete --verbose $DRY '$STAGE' '$REMOTE'; bye"
echo "deployed to $GODADDY_HOST:$REMOTE ${DRY:+(dry run)}"
