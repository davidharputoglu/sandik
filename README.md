<p align="center"><img src="sandik/editions/sandik/logo.png" alt="sandik" width="420"></p>

<p align="center"><b>CRM · Devis · Factures</b> — logiciel libre pour Windows, Linux, Raspberry Pi et Docker.</p>

---

**sandik** permet de gérer ses clients, son catalogue, ses devis, ses factures et ses avoirs, avec les règles
françaises intégrées (numérotation continue, mentions obligatoires, TVA par taux, franchise en base) et une
interface personnalisable (thèmes, champs, modules métiers).

> Version **0.1** — Créé par **David HARPUTOGLU**, avec l'aide de l'intelligence artificielle —
> contact : <kasparof57@gmail.com> — licence **AGPL-3.0-or-later**.

## Fonctions

- Clients (entreprises et particuliers), catalogue d'articles, champs personnalisés.
- Devis → facture en un clic ; factures et avoirs **figés à l'émission** (numéro définitif, empreinte d'intégrité chaînée).
- Numérotation **continue et sans trou**, format personnalisable (`FAC-{YYYY}-{N:4}`…).
- TVA par taux, autoliquidation, **franchise en base** (art. 293 B du CGI), TVA sur les débits.
- Impression A4 / PDF avec toutes les mentions (pénalités de retard, indemnité de 40 €, assurance…).
- Thèmes **Turquoise**, **Sombre**, **Noir** + éditeur de thèmes personnalisés ; densité d'affichage.
- Langues : français, anglais, turc (arabe, espagnol, portugais, italien et langues turciques en cours).
- **Modules** importables (BTP, commerce, services…) : voir le dépôt des modules.
- Mode **bureau** (un poste, sans connexion) ou **serveur** (Docker, comptes utilisateurs).

## Installation

Les fichiers d'installation sont construits par GitHub à chaque version (onglet *Releases*) :

| Système | Fichier |
|---|---|
| Windows 10 / 11 | `sandik-0.1.0-windows-x64-setup.exe` — installation personnalisée (langue, dossier, données, raccourcis) |
| Linux x86_64 / ARM64 | `.deb`, `.rpm`, `.AppImage` |
| Linux (tous, Raspberry Pi 3+ compris) | `sandik-0.1.0-linux.sh` — installateur interactif |
| Docker / Portainer | `ghcr.io/davidharputoglu/sandik:0.1.0` (amd64, arm64, armv7) |
| Code source | `sandik-0.1.0-source.tar.gz` |

### Docker / Portainer

Dans Portainer : **Stacks → Add stack**, coller [`docker/docker-compose.yml`](docker/docker-compose.yml)
(PostgreSQL) ou [`docker/docker-compose.sqlite.yml`](docker/docker-compose.sqlite.yml) (léger, idéal sur
Raspberry Pi). Puis ouvrir `http://<serveur>:8460` et créer le compte administrateur.

**Choisir le port** : ajouter la variable `PORT` (ex. `PORT=9000`) dans la section *Environment variables*
de la stack Portainer, ou dans un fichier `.env` à côté du fichier compose. Sans compose :

```sh
docker run -d --name sandik -p 9000:9000 -e SANDIK_PORT=9000 -v sandik-data:/data ghcr.io/davidharputoglu/sandik:0.1.0
podman run -d --name sandik -p 9000:9000 -e SANDIK_PORT=9000 -v sandik-data:/data ghcr.io/davidharputoglu/sandik:0.1.0
```

### Un nom plutôt qu'une adresse IP

- **Réseau local** : *Paramètres → Réseau → Nom sur le réseau local* annonce l'application sous
  `http://sandik.local:8460` (mDNS/Bonjour), reconnu par Windows, macOS, Linux et les téléphones.
  Avec Docker, utiliser `network_mode: host` ; avec l'installateur `.sh` en mode service, c'est automatique.
- **Nom gratuit sur Internet (DuckDNS)** : créer un sous-domaine sur [duckdns.org](https://www.duckdns.org), puis
  soit utiliser [`docker/docker-compose.duckdns.yml`](docker/docker-compose.duckdns.yml) (HTTPS automatique,
  variables `DUCKDNS_SUBDOMAIN` et `DUCKDNS_TOKEN`), soit activer *Paramètres → Réseau → DNS dynamique*, qui met
  l'adresse IP à jour depuis l'application elle-même (Windows, Linux, Raspberry Pi, Docker). Autres services :
  deSEC (`.dedyn.io`), FreeDNS, dynv6 (adresse de mise à jour personnalisée), No-IP.
- **Votre propre domaine** (ex. `factures.monentreprise.fr`) : le faire pointer vers le serveur, puis
  [`docker/docker-compose.https.yml`](docker/docker-compose.https.yml) avec la variable `DOMAIN` (certificat
  Let's Encrypt automatique via Caddy, ports 80 et 443 à ouvrir sur la box).
- **Relais web existant** (Nginx Proxy Manager, Traefik…) : le faire pointer vers `sandik:8460` et définir
  `SANDIK_PUBLIC_URL=https://votre.domaine` et `SANDIK_TRUSTED_PROXIES=*`.
- **Sans ouvrir de port** (box « CGNAT ») : Tailscale Funnel (nom `.ts.net`) ou Cloudflare Tunnel.

Avec un port précis (ex. `monentreprise.duckdns.org:5761`), combiner le nom et la variable `PORT`.

### Linux (.sh) et Raspberry Pi

```sh
chmod +x sandik-0.1.0-linux.sh
./sandik-0.1.0-linux.sh            # assistant : langue, dossier, données, menu, démarrage, service
./sandik-0.1.0-linux.sh -- --help  # options pour une installation automatique
```

## Développement

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cd frontend && npm install && npm run build && cd ..
sandik --desktop          # application de bureau
sandik                    # serveur sur http://127.0.0.1:8460 (avec connexion)
pytest                    # tests
```

Interface en développement : `sandik` dans un terminal, `npm run dev` dans `frontend/`.

Variables utiles : `SANDIK_DATA_DIR`, `SANDIK_DATABASE_URL`, `SANDIK_AUTH`, `SANDIK_LANG`, `SANDIK_PORT`,
`SANDIK_PUBLIC_URL`, `SANDIK_TRUSTED_PROXIES`, `SANDIK_LOCAL_NAME`, `SANDIK_MDNS`, `SANDIK_COOKIE_SECURE`, `SANDIK_EDITION`.

## Éditions

sandik est le cœur commun de plusieurs éditions : une édition = un nom, une identité visuelle, des langues,
des thèmes et des modules (dossier `sandik/editions/<id>/edition.toml`).

## Documents

[Licence](LICENSE) · [Avis de droits d'auteur](NOTICE.md) · [Avertissement](DISCLAIMER.md) ·
[Confidentialité](PRIVACY.md) · [Sécurité](SECURITY.md) · [Contribuer](CONTRIBUTING.md) · [CLA](CLA.md) ·
[Composants tiers](THIRD_PARTY_NOTICES.md) · [Auteurs](AUTHORS.md)

---

*sandik is free software (AGPL-3.0-or-later) by David HARPUTOGLU, built with the help of AI. It is provided
without warranty and is not a certified e-invoicing platform. See [DISCLAIMER.md](DISCLAIMER.md).*
