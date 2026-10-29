"""Appel de l'API Gemini (REST, bibliothèque standard uniquement : aucune dépendance).

La clé est envoyée dans l'en-tête de la requête, jamais dans l'adresse, et n'apparaît
dans aucun message d'erreur.
"""

import json
import socket
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

MODELE_DEFAUT = "gemini-2.5-flash"
ADRESSE = "https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
ATTENTES_429 = (15, 30)      # secondes avant chaque nouvel essai (limite de requêtes)
ATTENTES_SERVEUR = (3, 6)    # secondes avant chaque nouvel essai (erreur 5xx)


class ErreurGemini(Exception):
    """Erreur lisible par l'utilisateur (déjà en français)."""


def _message_api(corps: bytes) -> str:
    try:
        return str(json.loads(corps.decode("utf-8", "replace"))["error"]["message"])[:200]
    except Exception:
        return ""


def _erreur_http(code: int, corps: bytes, modele: str) -> ErreurGemini:
    detail = _message_api(corps)
    if code in (400, 401, 403) and ("api key" in detail.lower() or code in (401, 403)):
        return ErreurGemini("Clé Gemini refusée. Vérifiez la clé dans les Paramètres "
                            "(créez-en une nouvelle dans Google AI Studio si besoin).")
    if code == 404:
        return ErreurGemini(f"Modèle Gemini introuvable : « {modele} ». "
                            "Changez le nom du modèle dans les Paramètres.")
    if code == 429:
        return ErreurGemini("Limite de requêtes gratuites atteinte. Attendez une minute "
                            "(ou la fin de la journée si le quota quotidien est épuisé), "
                            "puis recommencez.")
    if code >= 500:
        return ErreurGemini("Le service Gemini est momentanément indisponible. Réessayez dans un instant.")
    return ErreurGemini(f"Requête refusée par Gemini (code {code}). {detail}".strip())


def extraire_texte(reponse: dict) -> str:
    candidats = reponse.get("candidates") or []
    if not candidats:
        raison = (reponse.get("promptFeedback") or {}).get("blockReason")
        if raison:
            raise ErreurGemini(f"Gemini a refusé de traiter ce sujet ({raison}). Reformulez-le.")
        raise ErreurGemini("Gemini n'a renvoyé aucune réponse. Réessayez.")
    parties = (candidats[0].get("content") or {}).get("parts") or []
    texte = "".join(p.get("text", "") for p in parties if isinstance(p, dict))
    if not texte.strip():
        raise ErreurGemini("Gemini a renvoyé une réponse vide. Réessayez.")
    return texte


def generer_json(cle: str, modele: str, consigne: str, *,
                 ouvrir: Callable = urllib.request.urlopen,
                 attendre: Callable[[float], None] = time.sleep,
                 sur_attente: Optional[Callable[[str], None]] = None,
                 delai_max: int = 90) -> str:
    """Envoie la consigne à Gemini et retourne le texte (JSON) de la réponse."""
    cle, modele = (cle or "").strip(), (modele or "").strip() or MODELE_DEFAUT
    if not cle:
        raise ErreurGemini("Aucune clé Gemini : ajoutez-la dans les Paramètres.")
    corps = json.dumps({
        "contents": [{"parts": [{"text": consigne}]}],
        "generationConfig": {"responseMimeType": "application/json",
                             "temperature": 0.7, "maxOutputTokens": 8192},
    }).encode("utf-8")
    requete = urllib.request.Request(
        ADRESSE.format(modele=modele), data=corps, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": cle})

    essai = 0
    while True:
        try:
            with ouvrir(requete, timeout=delai_max) as flux:
                reponse = json.loads(flux.read().decode("utf-8"))
            return extraire_texte(reponse)
        except urllib.error.HTTPError as exc:
            erreur = _erreur_http(exc.code, exc.read() if hasattr(exc, "read") else b"", modele)
            suites = ATTENTES_429 if exc.code == 429 else ATTENTES_SERVEUR if exc.code >= 500 else ()
            if essai < len(suites):
                if sur_attente:
                    sur_attente(f"Gemini est occupé, nouvel essai dans {suites[essai]} s…")
                attendre(suites[essai])
                essai += 1
                continue
            raise erreur from None
        except (socket.timeout, TimeoutError):
            raise ErreurGemini("Gemini met trop de temps à répondre. Réessayez.") from None
        except urllib.error.URLError:
            raise ErreurGemini("Pas de connexion à Internet (ou accès à Gemini bloqué).") from None
        except (ValueError, UnicodeDecodeError):
            raise ErreurGemini("Réponse illisible de Gemini. Réessayez.") from None
