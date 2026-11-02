#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
# Construit l'installateur .sh auto-extractible (makeself) à partir des paquets wheel.
# Usage : packaging/linux/make_sh.sh <nom> <id> <édition> <version> "<langues>" <langue_défaut> <icône.png> <wheel>...
set -euo pipefail
NAME="$1"; ID="$2"; EDITION="$3"; VERSION="$4"; LANGS="$5"; DEF="$6"; ICON="$7"; shift 7
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="$ROOT/dist/sh-$ID"; OUT="$ROOT/dist/release"; rm -rf "$STAGE"; mkdir -p "$STAGE/wheels" "$OUT"
cp "$@" "$STAGE/wheels/"
cp "$ROOT/packaging/linux/install.sh" "$STAGE/install.sh"; chmod +x "$STAGE/install.sh"
cp "$ICON" "$STAGE/icon.png"
LEGAL="${LEGAL_DIR:-$ROOT}"   # BatiPilot : ses propres mentions légales
for f in LICENSE LICENSE.md NOTICE.md DISCLAIMER.md THIRD_PARTY_NOTICES.md; do [[ -f "$LEGAL/$f" ]] && cp "$LEGAL/$f" "$STAGE/"; done
cat > "$STAGE/meta.env" <<META
APP_NAME="$NAME"
APP_ID="$ID"
EDITION="$EDITION"
VERSION="$VERSION"
LANGS="$LANGS"
DEFAULT_LANG="$DEF"
PORT=8460
META
makeself --gzip --nox11 "$STAGE" "$OUT/${ID}-${VERSION}-linux.sh" "$NAME $VERSION" ./install.sh
