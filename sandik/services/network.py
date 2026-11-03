# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Adresses de l'application : réseau local (nom .local par mDNS) et adresse publique (nom de domaine)."""

from __future__ import annotations

import logging
import os
import re
import socket
import threading

log = logging.getLogger("sandik.network")
LOCAL_NAME = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
PUBLIC_URL = re.compile(r"^https?://[A-Za-z0-9.-]+(:\d{1,5})?(/[^\s]*)?$")


def in_docker() -> bool:
    return os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")


def mdns_available() -> bool:
    try:
        import zeroconf  # noqa: F401

        return True
    except ImportError:
        return False


def local_ipv4() -> list[str]:
    """Adresses IPv4 de la machine sur le réseau local (hors 127.x)."""
    ips: set[str] = set()
    try:
        import ifaddr  # fourni avec zeroconf

        for adapter in ifaddr.get_adapters():
            for ip in adapter.ips:
                if isinstance(ip.ip, str) and not ip.ip.startswith(("127.", "169.254.")):
                    ips.add(ip.ip)
    except ImportError:
        pass
    try:  # interface de sortie par défaut (aucun paquet n'est envoyé)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))
            ips.add(s.getsockname()[0])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


def validate_local_name(name: str) -> bool:
    return bool(LOCAL_NAME.match(name))


def validate_public_url(url: str) -> bool:
    return url == "" or bool(PUBLIC_URL.match(url))


class LocalAnnouncer:
    """Annonce l'application sur le réseau local : http://<nom>.local:<port> (mDNS / Bonjour / Avahi)."""

    def __init__(self) -> None:
        self._zc = None
        self._info = None
        self._lock = threading.Lock()
        self.name: str | None = None
        self.error: str | None = None

    @property
    def active(self) -> bool:
        return self._zc is not None

    def start(self, name: str, port: int, title: str) -> None:
        with self._lock:
            self._stop()
            self.error = None
            try:
                from zeroconf import IPVersion, ServiceInfo, Zeroconf

                ips = local_ipv4()
                if not ips:
                    raise OSError("aucune adresse réseau locale")
                info = ServiceInfo(
                    "_http._tcp.local.",
                    f"{title}._http._tcp.local.",
                    addresses=[socket.inet_aton(ip) for ip in ips],
                    port=port,
                    server=f"{name}.local.",
                    properties={"path": "/"},
                )
                zc = Zeroconf(ip_version=IPVersion.V4Only)
                zc.register_service(info, allow_name_change=True)
                self._zc, self._info, self.name = zc, info, name
                log.info("Réseau local : http://%s.local:%s", name, port)
            except Exception as exc:  # zeroconf absent, port 5353 occupé, pas de réseau…
                self.error = str(exc) or exc.__class__.__name__
                log.warning("Nom local %s.local indisponible : %s", name, self.error)

    def _stop(self) -> None:
        if self._zc is not None:
            try:
                self._zc.unregister_service(self._info)
                self._zc.close()
            except Exception:
                pass
        self._zc = self._info = self.name = None

    def stop(self) -> None:
        with self._lock:
            self._stop()


# ---------------------------------------------------------------- DNS dynamique (DuckDNS, deSEC, FreeDNS…)
DUCKDNS_NAME = re.compile(r"^[a-z0-9-]{1,63}$")


def dyndns_url(cfg: dict) -> str | None:
    """Adresse de mise à jour du DNS dynamique, ou None si désactivé / incomplet."""
    if not cfg.get("dyndns_enabled"):
        return None
    if cfg.get("dyndns_provider") == "custom":
        url = (cfg.get("dyndns_url") or "").strip()
        return url if url.startswith(("https://", "http://")) else None
    sub, token = (cfg.get("duckdns_subdomain") or "").strip().lower(), (cfg.get("duckdns_token") or "").strip()
    if not (DUCKDNS_NAME.match(sub) and token):
        return None
    return f"https://www.duckdns.org/update?domains={sub}&token={token}&ip="


class DynDnsUpdater:
    """Met à jour l'adresse IP publique auprès du DNS dynamique, toutes les 5 minutes."""

    INTERVAL = 300

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.url: str | None = None
        self.last_result: str | None = None
        self.last_time: float | None = None

    def update_now(self) -> str:
        import time
        import urllib.request

        try:
            with urllib.request.urlopen(self.url, timeout=15) as r:  # noqa: S310 (adresse choisie par l'administrateur)
                body = r.read(200).decode("utf-8", "replace").strip()
            self.last_result = body or "OK"
        except Exception as exc:
            self.last_result = f"erreur : {exc}"
        self.last_time = time.time()
        log.info("DNS dynamique : %s", self.last_result)
        return self.last_result

    def _run(self) -> None:
        while not self._stop.is_set():
            self.update_now()
            self._stop.wait(self.INTERVAL)

    def configure(self, url: str | None) -> None:
        self.stop()
        self.url = url
        if url:
            self._stop = threading.Event()
            self._thread = threading.Thread(target=self._run, name="dyndns", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread = None

    @property
    def active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
