#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
# Paquets Linux à partir de dist/<nom>/ (PyInstaller) : .deb, .rpm (fpm) et .AppImage (appimagetool).
# Usage : packaging/linux/build_packages.sh <nom> <id> <version> <icône.png> <licence> "<description>" [formats]
set -euo pipefail
NAME="$1"; ID="$2"; VERSION="$3"; ICON="$4"; LICENSE_ID="$5"; DESC="$6"; FORMATS="${7:-deb rpm appimage}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/dist"; OUT="$DIST/release"; mkdir -p "$OUT"
MACHINE="$(uname -m)"
case "$MACHINE" in
  x86_64) DEB_ARCH=amd64; RPM_ARCH=x86_64; AI_ARCH=x86_64 ;;
  aarch64|arm64) DEB_ARCH=arm64; RPM_ARCH=aarch64; AI_ARCH=aarch64 ;;
  *) echo "Architecture non prise en charge : $MACHINE" >&2; exit 1 ;;
esac
MAINTAINER="David HARPUTOGLU <kasparof57@gmail.com>"

desktop_file() { # $1 = commande, $2 = icône
  sed -e "s|@NAME@|$NAME|" -e "s|@COMMENT@|$DESC|" -e "s|@EXEC@|$1|" -e "s|@ICON@|$2|" "$ROOT/packaging/linux/app.desktop.in"
}

if [[ " $FORMATS " == *" deb "* || " $FORMATS " == *" rpm "* ]]; then
  PKG="$DIST/pkgroot"; rm -rf "$PKG"
  mkdir -p "$PKG/opt/$ID" "$PKG/usr/bin" "$PKG/usr/share/applications" "$PKG/usr/share/icons/hicolor/512x512/apps" "$PKG/usr/share/doc/$ID"
  cp -a "$DIST/$NAME/." "$PKG/opt/$ID/"
  ln -s "/opt/$ID/$NAME" "$PKG/usr/bin/$ID"
  desktop_file "/opt/$ID/$NAME" "$ID" > "$PKG/usr/share/applications/$ID.desktop"
  cp "$ICON" "$PKG/usr/share/icons/hicolor/512x512/apps/$ID.png"
  cp "$ROOT"/LICENSE* "$ROOT"/NOTICE.md "$ROOT"/DISCLAIMER.md "$PKG/usr/share/doc/$ID/" 2>/dev/null || true
  COMMON=(-s dir -n "$ID" -v "$VERSION" --license "$LICENSE_ID" --maintainer "$MAINTAINER" --vendor "David HARPUTOGLU"
          --description "$DESC" --url "https://github.com/davidharputoglu/$ID" -C "$PKG")
  [[ " $FORMATS " == *" deb "* ]] && fpm "${COMMON[@]}" -t deb -a "$DEB_ARCH" -p "$OUT/${ID}_${VERSION}_${DEB_ARCH}.deb" .
  [[ " $FORMATS " == *" rpm "* ]] && fpm "${COMMON[@]}" -t rpm -a "$RPM_ARCH" -p "$OUT/${ID}-${VERSION}.${RPM_ARCH}.rpm" .
fi

if [[ " $FORMATS " == *" appimage "* ]]; then
  APP="$DIST/AppDir"; rm -rf "$APP"; mkdir -p "$APP/usr/lib/$ID"
  cp -a "$DIST/$NAME/." "$APP/usr/lib/$ID/"
  cat > "$APP/AppRun" <<RUN
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\$0")")"
exec "\$HERE/usr/lib/$ID/$NAME" "\$@"
RUN
  chmod +x "$APP/AppRun"
  desktop_file "$NAME" "$ID" > "$APP/$ID.desktop"
  cp "$ICON" "$APP/$ID.png"
  TOOL="$DIST/appimagetool-$AI_ARCH.AppImage"
  [[ -f "$TOOL" ]] || curl -fsSL -o "$TOOL" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$AI_ARCH.AppImage"
  chmod +x "$TOOL"
  ARCH="$AI_ARCH" "$TOOL" --appimage-extract-and-run "$APP" "$OUT/${NAME}-${VERSION}-${AI_ARCH}.AppImage"
fi
ls -la "$OUT"
