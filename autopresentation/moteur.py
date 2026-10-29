"""Orchestration : demande à Gemini, valide le plan, construit dans PowerPoint.

Tout se passe dans un fil séparé ; l'interface lit les messages dans `file` :
  ("etat", texte) · ("progres", 0-100) · ("termine", chemin) · ("arrete", "") · ("erreur", texte)
"""

import os
import queue
import threading
from datetime import datetime
from typing import Callable

from . import plan as plan_mod
from .gemini import ErreurGemini
from .powerpoint import ErreurPowerPoint


def nom_fichier(dossier: str, maintenant: datetime = None) -> str:
    maintenant = maintenant or datetime.now()
    return os.path.join(dossier, f"Presentation_{maintenant:%Y-%m-%d_%H-%M-%S}.pptx")


class MoteurPresentation:
    def __init__(self, generateur: Callable, fabrique_constructeur: Callable):
        """generateur(cle, modele, consigne, sur_attente) -> texte JSON ;
        fabrique_constructeur() -> objet avec .construire(...)."""
        self._generateur = generateur
        self._fabrique_constructeur = fabrique_constructeur
        self.file: "queue.Queue[tuple]" = queue.Queue()
        self._arret = threading.Event()
        self._fil = None

    def en_cours(self) -> bool:
        return self._fil is not None and self._fil.is_alive()

    def demarrer(self, parametres: dict) -> bool:
        if self.en_cours():
            return False
        self._arret.clear()
        self._fil = threading.Thread(target=self._executer, args=(parametres,), daemon=True)
        self._fil.start()
        return True

    def arreter(self) -> None:
        self._arret.set()

    def attendre(self, delai: float = 10.0) -> None:
        if self._fil is not None:
            self._fil.join(delai)

    # --- Fil de travail ---

    def _executer(self, p: dict) -> None:
        envoyer = self.file.put
        try:
            envoyer(("progres", 3))
            envoyer(("etat", "Demande envoyée à Gemini…"))
            consigne = plan_mod.construire_consigne(p["sujet"], p["nb_diapos"])
            brut = self._generateur(p["cle"], p["modele"], consigne,
                                    lambda message: envoyer(("etat", message)))
            if self._arret.is_set():
                envoyer(("arrete", ""))
                return
            plan = plan_mod.valider_plan(brut, nb_max=p["nb_diapos"])
            envoyer(("progres", 30))
            envoyer(("etat", f"Plan reçu : {len(plan['diapos'])} diapositives. Construction dans PowerPoint…"))

            def sur_progres(fait: int, total: int) -> None:
                envoyer(("progres", 30 + int(65 * fait / max(total, 1))))
                envoyer(("etat", f"Diapositive {fait} sur {total}…"))

            chemin = nom_fichier(p["dossier"])
            resultat = self._fabrique_constructeur().construire(
                plan, chemin, theme=p["theme"], pause=p["pause"],
                lancer_diaporama=p["lancer"], secondes_auto=p["auto"],
                sur_progres=sur_progres, doit_arreter=self._arret.is_set)
            if resultat is None:
                envoyer(("arrete", ""))
            else:
                envoyer(("progres", 100))
                envoyer(("termine", resultat))
        except (ErreurGemini, ErreurPowerPoint, plan_mod.ErreurPlan) as exc:
            envoyer(("erreur", str(exc)))
        except Exception as exc:  # filet de sécurité : jamais de plantage silencieux
            envoyer(("erreur", f"Erreur inattendue : {exc}"))
