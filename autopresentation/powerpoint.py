"""Construction de la présentation dans Microsoft PowerPoint par automatisation COM.

Comme une macro : PowerPoint s'ouvre, les diapositives apparaissent une à une, puis le
fichier est enregistré et, si demandé, le diaporama est lancé.
Les bibliothèques Windows sont importées à la demande : ce module reste importable
(et testable avec de faux objets) sur n'importe quel système.
"""

import time
from typing import Callable, Optional

PP_LAYOUT_TITRE = 1          # ppLayoutTitle
PP_LAYOUT_TEXTE = 2          # ppLayoutText (titre + contenu)
MSO_VRAI = -1
PP_DIAPORAMA_MINUTAGE = 2    # ppSlideShowUseSlideTimings

# nom -> (couleur de fond, couleur des titres, couleur du texte), en (R, V, B)
THEMES = {
    "Bleu nuit": ((14, 22, 33), (106, 179, 243), (230, 236, 242)),
    "Clair classique": ((255, 255, 255), (31, 56, 100), (40, 40, 40)),
    "Vert profond": ((18, 48, 38), (130, 214, 170), (222, 240, 230)),
    "Orange chaud": ((255, 247, 237), (180, 70, 10), (60, 40, 30)),
}
THEME_DEFAUT = "Bleu nuit"

MSG_ABSENT = ("Microsoft PowerPoint est introuvable. Installez la version de bureau de "
              "PowerPoint (la version web ne peut pas être pilotée).")


class ErreurPowerPoint(Exception):
    """Erreur lisible par l'utilisateur (déjà en français)."""


def rgb(rouge: int, vert: int, bleu: int) -> int:
    """Couleur au format COM (octets dans l'ordre bleu, vert, rouge)."""
    return rouge + vert * 256 + bleu * 65536


def _initialiser_com() -> bool:
    try:
        import pythoncom
        pythoncom.CoInitialize()
        return True
    except ImportError:
        return False


def _liberer_com() -> None:
    try:
        import pythoncom
        pythoncom.CoUninitialize()
    except ImportError:
        pass


def _fabrique_powerpoint():
    import win32com.client  # pywin32
    return win32com.client.Dispatch("PowerPoint.Application")


def _essayer(action: Callable[[], object]) -> None:
    """Réglage esthétique : un échec ne doit jamais interrompre la création."""
    try:
        action()
    except Exception:
        pass


class ConstructeurPowerPoint:
    def __init__(self, fabrique: Optional[Callable[[], object]] = None,
                 initialiser_com: Callable[[], bool] = _initialiser_com,
                 liberer_com: Callable[[], None] = _liberer_com,
                 attendre: Callable[[float], None] = time.sleep):
        self._fabrique = fabrique or _fabrique_powerpoint
        self._init_com, self._lib_com = initialiser_com, liberer_com
        self._attendre = attendre

    def construire(self, plan: dict, chemin: str, *, theme: str = THEME_DEFAUT,
                   pause: float = 1.0, lancer_diaporama: bool = False,
                   secondes_auto: int = 0,
                   sur_progres: Optional[Callable[[int, int], None]] = None,
                   doit_arreter: Callable[[], bool] = lambda: False) -> Optional[str]:
        """Construit la présentation. Retourne le chemin du fichier, ou None si arrêtée."""
        com_actif = bool(self._init_com())
        try:
            try:
                app = self._fabrique()
            except Exception as exc:
                raise ErreurPowerPoint(MSG_ABSENT) from exc
            try:
                return self._construire(app, plan, chemin, theme, pause, lancer_diaporama,
                                        secondes_auto, sur_progres, doit_arreter)
            except ErreurPowerPoint:
                raise
            except Exception as exc:
                raise ErreurPowerPoint(
                    "PowerPoint a signalé une erreur. Fermez les boîtes de dialogue "
                    f"ouvertes dans PowerPoint puis recommencez. Détail : {str(exc)[:250]}") from exc
        finally:
            if com_actif:
                self._lib_com()

    # --- Étapes ---

    def _construire(self, app, plan, chemin, theme, pause, lancer, secondes_auto,
                    sur_progres, doit_arreter):
        fond, c_titre, c_texte = THEMES.get(theme, THEMES[THEME_DEFAUT])
        app.Visible = MSO_VRAI
        prs = app.Presentations.Add()
        _essayer(lambda: self._fond(prs, fond))

        total = 1 + len(plan["diapos"])

        def avancer(fait: int) -> None:
            if sur_progres:
                sur_progres(fait, total)

        # Diapositive de titre
        diapo = prs.Slides.Add(1, PP_LAYOUT_TITRE)
        self._ecrire(diapo.Shapes.Placeholders(1), plan["titre"], c_titre, 44, gras=True)
        sous_titre = plan.get("sous_titre", "")
        if sous_titre:
            self._ecrire(diapo.Shapes.Placeholders(2), sous_titre, c_texte, 24)
        else:
            _essayer(lambda: diapo.Shapes.Placeholders(2).Delete())
        avancer(1)

        # Diapositives de contenu
        for numero, element in enumerate(plan["diapos"], start=2):
            if doit_arreter():
                return None
            self._attendre(max(0.0, pause))
            diapo = prs.Slides.Add(numero, PP_LAYOUT_TEXTE)
            self._ecrire(diapo.Shapes.Placeholders(1), element["titre"], c_titre, 36, gras=True)
            taille = 26 if len(element["puces"]) <= 4 else 22
            self._ecrire(diapo.Shapes.Placeholders(2), "\r".join(element["puces"]), c_texte, taille)
            if element["notes"]:
                _essayer(lambda: setattr(
                    diapo.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange,
                    "Text", element["notes"]))
            avancer(numero)

        try:
            prs.SaveAs(chemin)
        except Exception as exc:
            raise ErreurPowerPoint(
                f"Impossible d'enregistrer le fichier : {chemin}. "
                "Choisissez un autre dossier dans les Paramètres.") from exc

        if lancer:
            self._diaporama(prs, secondes_auto)
        return chemin

    @staticmethod
    def _fond(prs, fond) -> None:
        arriere = prs.SlideMaster.Background.Fill
        arriere.Solid()
        arriere.ForeColor.RGB = rgb(*fond)

    @staticmethod
    def _ecrire(forme, texte: str, couleur, taille: int, gras: bool = False) -> None:
        plage = forme.TextFrame.TextRange
        plage.Text = texte
        _essayer(lambda: setattr(plage.Font.Color, "RGB", rgb(*couleur)))
        _essayer(lambda: setattr(plage.Font, "Size", taille))
        if gras:
            _essayer(lambda: setattr(plage.Font, "Bold", MSO_VRAI))

    @staticmethod
    def _diaporama(prs, secondes_auto: int) -> None:
        reglages = prs.SlideShowSettings
        if secondes_auto and secondes_auto > 0:
            for diapo in prs.Slides:
                _essayer(lambda d=diapo: setattr(d.SlideShowTransition, "AdvanceOnTime", MSO_VRAI))
                _essayer(lambda d=diapo: setattr(d.SlideShowTransition, "AdvanceTime", secondes_auto))
            _essayer(lambda: setattr(reglages, "AdvanceMode", PP_DIAPORAMA_MINUTAGE))
        reglages.Run()
