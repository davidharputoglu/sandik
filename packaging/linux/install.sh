#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
# Installateur Linux interactif (PC et Raspberry Pi 3+, 32 et 64 bits).
# Utilise le Python du système (3.10 ou plus récent) et un environnement virtuel.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
. "$HERE/meta.env"   # APP_NAME APP_ID EDITION VERSION LANGS DEFAULT_LANG PORT

# ------------------------------------------------------------------ options
LANG_CODE=""; SCOPE=""; PREFIX=""; DATA_DIR=""; MENU=""; AUTOSTART=""; SERVICE=""; YES=0; UNINSTALL=0
usage() {
  cat <<USAGE
$APP_NAME $VERSION — installation Linux / Linux installer

  --lang CODE        langue de l'application ($LANGS)
  --user | --system  installation pour l'utilisateur (défaut) ou pour tout le système (root)
  --prefix DIR       dossier d'installation
  --data-dir DIR     dossier des données
  --menu / --no-menu raccourci dans le menu des applications (défaut : oui)
  --autostart        lancer à l'ouverture de session
  --service          démarrer comme service (serveur réseau, ex. Raspberry Pi) — port $PORT
  --port N           port du service (défaut : $PORT)
  --yes              sans questions (valeurs par défaut)
  --uninstall        désinstaller
USAGE
}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang) LANG_CODE="$2"; shift ;; --user) SCOPE=user ;; --system) SCOPE=system ;;
    --prefix) PREFIX="$2"; shift ;; --data-dir) DATA_DIR="$2"; shift ;;
    --menu) MENU=1 ;; --no-menu) MENU=0 ;; --autostart) AUTOSTART=1 ;; --service) SERVICE=1 ;;
    --port) PORT="$2"; shift ;; --yes|-y) YES=1 ;; --uninstall) UNINSTALL=1 ;;
    -h|--help) usage; exit 0 ;; *) echo "Option inconnue : $1" >&2; usage; exit 1 ;;
  esac
  shift
done

# ------------------------------------------------------------------ textes (fr / en / tr)
T() { # T clé
  local l="${LANG_CODE:-${DEFAULT_LANG}}"; case "$l" in fr|tr) ;; *) l=en ;; esac
  case "$l:$1" in
    fr:title) echo "Installation de $APP_NAME $VERSION" ;; en:title) echo "$APP_NAME $VERSION setup" ;; tr:title) echo "$APP_NAME $VERSION kurulumu" ;;
    fr:lang) echo "Langue de l'application :" ;; en:lang) echo "Application language:" ;; tr:lang) echo "Uygulama dili:" ;;
    fr:scope) echo "Installer pour :" ;; en:scope) echo "Install for:" ;; tr:scope) echo "Kimin için kurulsun:" ;;
    fr:me) echo "Moi seulement (sans droits administrateur)" ;; en:me) echo "Only me (no administrator rights)" ;; tr:me) echo "Yalnızca ben (yönetici hakkı gerekmez)" ;;
    fr:all) echo "Tous les utilisateurs (/opt, droits administrateur)" ;; en:all) echo "All users (/opt, administrator rights)" ;; tr:all) echo "Tüm kullanıcılar (/opt, yönetici hakkı)" ;;
    fr:prefix) echo "Dossier d'installation :" ;; en:prefix) echo "Installation folder:" ;; tr:prefix) echo "Kurulum klasörü:" ;;
    fr:data) echo "Dossier des données (base et fichiers) :" ;; en:data) echo "Data folder (database and files):" ;; tr:data) echo "Veri klasörü (veritabanı ve dosyalar):" ;;
    fr:menu) echo "Ajouter un raccourci dans le menu des applications ?" ;; en:menu) echo "Add a shortcut to the applications menu?" ;; tr:menu) echo "Uygulama menüsüne kısayol eklensin mi?" ;;
    fr:autostart) echo "Lancer à l'ouverture de session ?" ;; en:autostart) echo "Start when you log in?" ;; tr:autostart) echo "Oturum açılışında başlatılsın mı?" ;;
    fr:service) echo "Démarrer comme service réseau (serveur, accessible depuis les autres appareils, avec connexion) ?" ;; en:service) echo "Run as a network service (server, reachable from other devices, with sign-in)?" ;; tr:service) echo "Ağ hizmeti olarak çalıştırılsın mı (sunucu, diğer cihazlardan erişilebilir, girişli)?" ;;
    fr:python) echo "Python 3.10 ou plus récent (avec venv) est nécessaire." ;; en:python) echo "Python 3.10 or newer (with venv) is required." ;; tr:python) echo "Python 3.10 veya üzeri (venv ile) gereklidir." ;;
    fr:installing) echo "Installation en cours (connexion Internet nécessaire)…" ;; en:installing) echo "Installing (Internet connection required)…" ;; tr:installing) echo "Kuruluyor (İnternet bağlantısı gerekli)…" ;;
    fr:done) echo "Installation terminée." ;; en:done) echo "Installation complete." ;; tr:done) echo "Kurulum tamamlandı." ;;
    fr:run) echo "Lancer :" ;; en:run) echo "Run:" ;; tr:run) echo "Çalıştır:" ;;
    fr:url) echo "Adresse du service :" ;; en:url) echo "Service address:" ;; tr:url) echo "Hizmet adresi:" ;;
    fr:removed) echo "Application désinstallée. Vos données sont conservées dans :" ;; en:removed) echo "Application removed. Your data is kept in:" ;; tr:removed) echo "Uygulama kaldırıldı. Verileriniz şurada korunuyor:" ;;
    fr:root) echo "Cette option nécessite les droits administrateur : relancez avec sudo." ;; en:root) echo "This option requires administrator rights: run again with sudo." ;; tr:root) echo "Bu seçenek yönetici hakkı gerektirir: sudo ile yeniden çalıştırın." ;;
  esac
}

# ------------------------------------------------------------------ interface (whiptail / dialog / texte)
UI=text
if [[ $YES -eq 0 && -t 0 ]]; then
  if command -v whiptail >/dev/null 2>&1; then UI=whiptail; elif command -v dialog >/dev/null 2>&1; then UI=dialog; fi
fi
ask_menu() { # titre défaut tag libellé ...
  local title="$1" def="$2"; shift 2
  if [[ $YES -eq 1 || ! -t 0 ]]; then echo "$def"; return; fi
  if [[ $UI != text ]]; then
    $UI --title "$(T title)" --default-item "$def" --menu "$title" 20 72 10 "$@" 3>&1 1>&2 2>&3
  else
    echo "$title" >&2; local i=1 tags=()
    while [[ $# -gt 0 ]]; do echo "  $i) $2" >&2; tags+=("$1"); shift 2; i=$((i+1)); done
    read -r -p "> [$def] " c; if [[ -z "$c" ]]; then echo "$def"; else echo "${tags[$((c-1))]:-$def}"; fi
  fi
}
ask_input() { # titre défaut
  if [[ $YES -eq 1 || ! -t 0 ]]; then echo "$2"; return; fi
  if [[ $UI != text ]]; then $UI --title "$(T title)" --inputbox "$1" 10 72 "$2" 3>&1 1>&2 2>&3
  else read -r -p "$1 [$2] " v; echo "${v:-$2}"; fi
}
ask_yesno() { # titre défaut(1/0)
  if [[ $YES -eq 1 || ! -t 0 ]]; then echo "$2"; return; fi
  if [[ $UI != text ]]; then
    local d=(); [[ "$2" == 0 ]] && d=(--defaultno)
    if $UI --title "$(T title)" "${d[@]}" --yesno "$1" 10 72; then echo 1; else echo 0; fi
  else
    local def=n; [[ "$2" == 1 ]] && def=o
    read -r -p "$1 (o/n) [$def] " v; v="${v:-$def}"; [[ "$v" =~ ^[oOyYeE] ]] && echo 1 || echo 0
  fi
}

LANG_NAME() { case "$1" in fr) echo Français ;; en) echo English ;; ar) echo العربية ;; es) echo Español ;; pt) echo Português ;; it) echo Italiano ;; tr) echo Türkçe ;; az) echo Azərbaycanca ;; kk) echo Қазақша ;; uz) echo Oʻzbekcha ;; tk) echo Türkmençe ;; ky) echo Кыргызча ;; tt) echo Татарча ;; ba) echo Башҡортса ;; ug) echo ئۇيغۇرچە ;; cv) echo Чӑвашла ;; crh) echo Qırımtatarca ;; gag) echo Gagauzca ;; sah) echo "Саха тыла" ;; kaa) echo Qaraqalpaqsha ;; *) echo "$1" ;; esac; }

# ------------------------------------------------------------------ désinstallation
if [[ $UNINSTALL -eq 1 ]]; then
  for f in "$HOME/.local/share/$APP_ID/install.env" "/opt/$APP_ID/install.env"; do
    if [[ -f "$f" ]]; then exec bash "$(dirname "$f")/uninstall.sh"; fi
  done
  echo "Aucune installation trouvée / nothing installed."; exit 1
fi

# ------------------------------------------------------------------ questions
if [[ -z "$LANG_CODE" ]]; then
  items=(); for l in $LANGS; do items+=("$l" "$(LANG_NAME "$l")"); done
  LANG_CODE="$(ask_menu "$(T lang)" "$DEFAULT_LANG" "${items[@]}")"
fi
[[ -n "$SCOPE" ]] || SCOPE="$(ask_menu "$(T scope)" user user "$(T me)" system "$(T all)")"
if [[ "$SCOPE" == system && $EUID -ne 0 ]]; then echo "$(T root)" >&2; exit 1; fi
if [[ "$SCOPE" == system ]]; then DEF_PREFIX="/opt/$APP_ID"; DEF_DATA="/var/lib/$APP_ID"
else DEF_PREFIX="$HOME/.local/share/$APP_ID"; DEF_DATA="${XDG_DATA_HOME:-$HOME/.local/share}/$APP_ID-data"; fi
[[ -n "$PREFIX" ]] || PREFIX="$(ask_input "$(T prefix)" "$DEF_PREFIX")"
[[ -n "$DATA_DIR" ]] || DATA_DIR="$(ask_input "$(T data)" "$DEF_DATA")"
[[ -n "$MENU" ]] || MENU="$(ask_yesno "$(T menu)" 1)"
[[ -n "$SERVICE" ]] || SERVICE="$(ask_yesno "$(T service)" 0)"
if [[ "$SERVICE" == 1 ]]; then AUTOSTART=0; else [[ -n "$AUTOSTART" ]] || AUTOSTART="$(ask_yesno "$(T autostart)" 0)"; fi

# ------------------------------------------------------------------ Python
PY="$(command -v python3 || true)"
ok_py() { [[ -n "$PY" ]] && "$PY" -c 'import sys, venv, ensurepip; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; }
if ! ok_py; then
  echo "$(T python)" >&2
  if command -v apt-get >/dev/null; then echo "  sudo apt-get install -y python3 python3-venv python3-pip" >&2
  elif command -v dnf >/dev/null; then echo "  sudo dnf install -y python3 python3-pip" >&2
  elif command -v pacman >/dev/null; then echo "  sudo pacman -S python python-pip" >&2
  elif command -v zypper >/dev/null; then echo "  sudo zypper install python3 python3-pip" >&2; fi
  exit 1
fi

# ------------------------------------------------------------------ installation
echo "$(T installing)"
mkdir -p "$PREFIX" "$DATA_DIR"
"$PY" -m venv --clear "$PREFIX/venv"
"$PREFIX/venv/bin/python" -m pip install --quiet --upgrade pip
"$PREFIX/venv/bin/python" -m pip install --quiet "$HERE"/wheels/*.whl
cp "$HERE/icon.png" "$PREFIX/icon.png"
cp "$HERE"/LICENSE* "$HERE"/*.md "$PREFIX/" 2>/dev/null || true
cat > "$PREFIX/install.env" <<ENV
SANDIK_EDITION=$EDITION
SANDIK_DATA_DIR=$DATA_DIR
SANDIK_LANG=$LANG_CODE
ENV
mkdir -p "$PREFIX/bin"
cat > "$PREFIX/bin/$APP_ID" <<RUN
#!/usr/bin/env bash
set -a; . "$PREFIX/install.env"; set +a
exec "$PREFIX/venv/bin/sandik" --desktop "\$@"
RUN
chmod +x "$PREFIX/bin/$APP_ID"

if [[ "$SCOPE" == system ]]; then BIN_DIR=/usr/local/bin; APPS=/usr/share/applications; else BIN_DIR="$HOME/.local/bin"; APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"; fi
mkdir -p "$BIN_DIR"; ln -sf "$PREFIX/bin/$APP_ID" "$BIN_DIR/$APP_ID"
DESKTOP="[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=CRM · Devis · Factures
Exec=$PREFIX/bin/$APP_ID
Icon=$PREFIX/icon.png
Terminal=false
Categories=Office;Finance;"
if [[ "$MENU" == 1 ]]; then mkdir -p "$APPS"; echo "$DESKTOP" > "$APPS/$APP_ID.desktop"; fi
if [[ "$AUTOSTART" == 1 ]]; then mkdir -p "$HOME/.config/autostart"; echo "$DESKTOP" > "$HOME/.config/autostart/$APP_ID.desktop"; fi

UNIT=""
if [[ "$SERVICE" == 1 ]]; then
  if [[ "$SCOPE" == system ]]; then UNIT="/etc/systemd/system/$APP_ID.service"; USER_OPT="User=${SUDO_USER:-root}"; CTL="systemctl"; TARGET=multi-user.target
  else UNIT="$HOME/.config/systemd/user/$APP_ID.service"; USER_OPT=""; CTL="systemctl --user"; TARGET=default.target; fi
  mkdir -p "$(dirname "$UNIT")"
  [[ "$SCOPE" == system && -n "${SUDO_USER:-}" ]] && chown -R "$SUDO_USER" "$DATA_DIR"
  cat > "$UNIT" <<UNITFILE
[Unit]
Description=$APP_NAME (serveur)
After=network-online.target

[Service]
$USER_OPT
EnvironmentFile=$PREFIX/install.env
Environment=SANDIK_AUTH=1
ExecStart=$PREFIX/venv/bin/sandik --host 0.0.0.0 --port $PORT
Restart=on-failure

[Install]
WantedBy=$TARGET
UNITFILE
  $CTL daemon-reload && $CTL enable --now "$APP_ID.service" || true
  [[ "$SCOPE" == user ]] && command -v loginctl >/dev/null && loginctl enable-linger "$USER" 2>/dev/null || true
fi

cat > "$PREFIX/uninstall.sh" <<UNINST
#!/usr/bin/env bash
# Désinstallation de $APP_NAME (les données sont conservées : $DATA_DIR)
[[ -n "$UNIT" && -f "$UNIT" ]] && { ${CTL:-systemctl} disable --now "$APP_ID.service" 2>/dev/null; rm -f "$UNIT"; }
rm -f "$BIN_DIR/$APP_ID" "$APPS/$APP_ID.desktop" "$HOME/.config/autostart/$APP_ID.desktop"
rm -rf "$PREFIX"
echo "$(T removed) $DATA_DIR"
UNINST
chmod +x "$PREFIX/uninstall.sh"

echo
echo "✔ $(T done)"
echo "  $(T run) $APP_ID   (${BIN_DIR}/$APP_ID)"
[[ "$SERVICE" == 1 ]] && echo "  $(T url) http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PORT"
echo "  Désinstaller / uninstall : $PREFIX/uninstall.sh"
