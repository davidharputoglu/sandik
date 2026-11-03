# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Réglages enregistrés en base, avec valeurs par défaut issues de l'édition."""

from __future__ import annotations

import copy
from typing import Any

from sqlalchemy.orm import Session

from ..editions import Edition
from ..models import Setting

LATE_PENALTY = (
    "En cas de retard de paiement : pénalités au taux directeur de la BCE majoré de 10 points, "
    "et indemnité forfaitaire de 40 € pour frais de recouvrement (art. L441-10 du Code de commerce)."
)


def defaults(edition: Edition) -> dict[str, Any]:
    d = edition.defaults
    return {
        "company": {
            "name": "", "legal_form": "", "capital": "", "siren": "", "siret": "", "vat_number": "",
            "rcs": "", "ape": "", "address_line1": "", "address_line2": "", "postal_code": "", "city": "",
            "country": "FR", "email": "", "phone": "", "website": "", "iban": "", "bic": "", "bank_name": "",
            "insurance": "",
        },
        "numbering": copy.deepcopy(edition.numbering),
        "documents": {
            "quote_validity_days": d.get("quote_validity_days", 30),
            "payment_terms_days": d.get("payment_terms_days", 30),
            "payment_terms_text": "Paiement à {jours} jours à compter de la date de facture.",
            "late_penalty_text": LATE_PENALTY,
            "early_payment_text": "Pas d'escompte pour paiement anticipé.",
            "quote_intro": "",
            "quote_footer": "Devis valable jusqu'à la date indiquée. Bon pour accord : date, signature et mention « lu et approuvé ».",
            "invoice_footer": "",
            "default_operation_nature": "services",
            "vat_on_debits": False,
        },
        "vat": {
            "regime": "normal",  # normal | franchise (micro-entreprise, art. 293 B du CGI)
            "rates": ["20", "10", "5.5", "2.1", "0"],
            "default_rate": "20",
            "franchise_text": "TVA non applicable, art. 293 B du CGI",
        },
        "units": {"list": ["u", "h", "j", "forfait", "lot", "m", "ml", "m²", "m³", "kg", "t", "L"]},
        "setup": {"done": False, "location_done": False},  # assistant de premier lancement
        "network": {
            "public_url": "",          # ex. https://factures.monentreprise.fr (liens envoyés par e-mail)
            "local_name": edition.id,  # nom sur le réseau local : http://<nom>.local:<port>
            "mdns": False,             # annoncer ce nom sur le réseau local
            # DNS dynamique : met à jour l'adresse IP publique (box à IP changeante)
            "dyndns_enabled": False,
            "dyndns_provider": "duckdns",  # duckdns | custom (deSEC, FreeDNS, dynv6…)
            "duckdns_subdomain": "",
            "duckdns_token": "",
            "dyndns_url": "",
        },
        "modules": {
            "disabled": [],          # modules installés mais désactivés
            "catalog_url": "",       # futur : catalogue des modules (dépôt GitHub)
        },
        "appearance": {
            "theme": "auto",          # thème par défaut : auto | id d'un thème de l'édition | id personnalisé
            "custom_themes": [],      # thèmes créés par l'utilisateur
            "density": "comfortable",  # comfortable | compact
            "document_accent": "",    # couleur des documents imprimés (vide = couleur du thème)
            "show_logo_on_documents": True,
        },
    }


KEYS = {"company", "numbering", "documents", "vat", "units", "appearance", "modules", "setup", "network"}


def get_setting(db: Session, edition: Edition, key: str) -> dict[str, Any]:
    if key not in KEYS:
        raise KeyError(key)
    value = defaults(edition)[key]
    row = db.get(Setting, key)
    if row and isinstance(row.value, dict):
        value.update({k: v for k, v in row.value.items() if k in value})
    return value


def set_setting(db: Session, edition: Edition, key: str, data: dict[str, Any]) -> dict[str, Any]:
    current = get_setting(db, edition, key)
    current.update({k: v for k, v in data.items() if k in current})
    row = db.get(Setting, key)
    if row is None:
        db.add(Setting(key=key, value=current))
    else:
        row.value = current
    db.commit()
    return current
