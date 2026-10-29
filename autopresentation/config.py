"""Réglages enregistrés sur l'ordinateur de l'utilisateur (jamais dans le projet ni sur GitHub)."""

import json
import os
from typing import Optional

from .gemini import MODELE_DEFAUT


def dossier_config() -> str:
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "AutoPresentation")


def dossier_sortie_defaut() -> str:
    documents = os.path.join(os.path.expanduser("~"), "Documents")
    return documents if os.path.isdir(documents) else os.path.expanduser("~")


def charger(dossier: Optional[str] = None) -> dict:
    reglages = {"cle": "", "modele": MODELE_DEFAUT, "dossier_sortie": ""}
    try:
        with open(os.path.join(dossier or dossier_config(), "reglages.json"), encoding="utf-8") as f:
            lus = json.load(f)
        for nom in reglages:
            if isinstance(lus.get(nom), str):
                reglages[nom] = lus[nom]
    except (OSError, ValueError, AttributeError):
        pass
    return reglages


def enregistrer(reglages: dict, dossier: Optional[str] = None) -> None:
    dossier = dossier or dossier_config()
    os.makedirs(dossier, exist_ok=True)
    with open(os.path.join(dossier, "reglages.json"), "w", encoding="utf-8") as f:
        json.dump({k: reglages.get(k, "") for k in ("cle", "modele", "dossier_sortie")}, f,
                  ensure_ascii=False, indent=2)


def cle_effective(reglages: dict) -> str:
    return (reglages.get("cle") or os.environ.get("GEMINI_API_KEY", "")).strip()
