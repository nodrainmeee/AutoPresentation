import unittest

from autopresentation import powerpoint as pp


class Objet:
    """Objet souple qui enregistre les attributs écrits."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def fausse_forme():
    plage = Objet(Text="", Font=Objet(Color=Objet(RGB=None), Size=None, Bold=None))
    return Objet(TextFrame=Objet(TextRange=plage), supprimee=False, Delete=lambda: None)


class FausseDiapo:
    def __init__(self, layout):
        self.layout = layout
        self.formes = {1: fausse_forme(), 2: fausse_forme()}
        self.Shapes = Objet(Placeholders=lambda n: self.formes[n])
        self.notes = fausse_forme()
        self.NotesPage = Objet(Shapes=Objet(Placeholders=lambda n: self.notes))
        self.SlideShowTransition = Objet(AdvanceOnTime=0, AdvanceTime=0)


class FausseListe(list):
    def Add(self, index, layout):
        d = FausseDiapo(layout)
        self.insert(index - 1, d)
        return d


class FausseFill:
    def __init__(self):
        self.plein = False
        self.ForeColor = Objet(RGB=None)

    def Solid(self):
        self.plein = True


class FausseParametres:
    def __init__(self):
        self.lance, self.AdvanceMode = False, None

    def Run(self):
        self.lance = True


class FausseVue:
    def __init__(self):
        self.Slides = FausseListe()
        self.fill = FausseFill()
        self.SlideMaster = Objet(Background=Objet(Fill=self.fill))
        self.SlideShowSettings = FausseParametres()
        self.enregistre = None
        self.echec_enregistrement = False

    def SaveAs(self, chemin):
        if self.echec_enregistrement:
            raise OSError("disque plein")
        self.enregistre = chemin


class FausseApp:
    def __init__(self):
        self.Visible = False
        self.prs = FausseVue()
        self.Presentations = Objet(Add=lambda: self.prs)


PLAN = {"titre": "Mon titre", "sous_titre": "Sous-titre", "diapos": [
    {"titre": "A", "puces": ["a1", "a2"], "notes": "notes A"},
    {"titre": "B", "puces": ["b1", "b2", "b3", "b4", "b5"], "notes": ""},
]}


def constructeur(app):
    return pp.ConstructeurPowerPoint(fabrique=lambda: app, initialiser_com=lambda: True,
                                     liberer_com=lambda: None, attendre=lambda s: None)


class TestPowerPoint(unittest.TestCase):
    def test_construction_complete(self):
        app, progres = FausseApp(), []
        chemin = constructeur(app).construire(
            PLAN, "C:/x.pptx", theme="Clair classique", pause=0,
            sur_progres=lambda f, t: progres.append((f, t)))
        prs = app.prs
        self.assertEqual(chemin, "C:/x.pptx")
        self.assertTrue(app.Visible)
        self.assertEqual(prs.enregistre, "C:/x.pptx")
        self.assertEqual(len(prs.Slides), 3)
        titre, a, b = prs.Slides
        self.assertEqual(titre.layout, pp.PP_LAYOUT_TITRE)
        self.assertEqual(titre.formes[1].TextFrame.TextRange.Text, "Mon titre")
        self.assertEqual(titre.formes[2].TextFrame.TextRange.Text, "Sous-titre")
        self.assertEqual(a.layout, pp.PP_LAYOUT_TEXTE)
        self.assertEqual(a.formes[2].TextFrame.TextRange.Text, "a1\ra2")
        self.assertEqual(a.notes.TextFrame.TextRange.Text, "notes A")
        self.assertEqual(b.formes[2].TextFrame.TextRange.Font.Size, 22)   # 5 puces : texte plus petit
        self.assertEqual(progres, [(1, 3), (2, 3), (3, 3)])
        self.assertTrue(prs.fill.plein)
        self.assertEqual(prs.fill.ForeColor.RGB, pp.rgb(255, 255, 255))
        self.assertFalse(prs.SlideShowSettings.lance)

    def test_rgb_ordre_bgr(self):
        self.assertEqual(pp.rgb(1, 2, 3), 1 + 2 * 256 + 3 * 65536)

    def test_diaporama_automatique(self):
        app = FausseApp()
        constructeur(app).construire(PLAN, "x.pptx", pause=0, lancer_diaporama=True, secondes_auto=7)
        prs = app.prs
        self.assertTrue(prs.SlideShowSettings.lance)
        self.assertEqual(prs.SlideShowSettings.AdvanceMode, pp.PP_DIAPORAMA_MINUTAGE)
        for d in prs.Slides:
            self.assertEqual(d.SlideShowTransition.AdvanceTime, 7)
            self.assertEqual(d.SlideShowTransition.AdvanceOnTime, pp.MSO_VRAI)

    def test_diaporama_manuel(self):
        app = FausseApp()
        constructeur(app).construire(PLAN, "x.pptx", pause=0, lancer_diaporama=True, secondes_auto=0)
        self.assertTrue(app.prs.SlideShowSettings.lance)
        self.assertIsNone(app.prs.SlideShowSettings.AdvanceMode)

    def test_arret_en_cours(self):
        app = FausseApp()
        etat = {"n": 0}

        def doit_arreter():
            etat["n"] += 1
            return etat["n"] > 1       # autorise la 1re diapo de contenu, arrête avant la 2e

        resultat = constructeur(app).construire(PLAN, "x.pptx", pause=0, doit_arreter=doit_arreter)
        self.assertIsNone(resultat)
        self.assertEqual(len(app.prs.Slides), 2)
        self.assertIsNone(app.prs.enregistre)

    def test_powerpoint_absent(self):
        def fabrique():
            raise OSError("Chaîne de classe non valide")
        c = pp.ConstructeurPowerPoint(fabrique=fabrique, initialiser_com=lambda: False, attendre=lambda s: None)
        with self.assertRaises(pp.ErreurPowerPoint) as e:
            c.construire(PLAN, "x.pptx")
        self.assertIn("introuvable", str(e.exception))

    def test_enregistrement_impossible(self):
        app = FausseApp()
        app.prs.echec_enregistrement = True
        with self.assertRaises(pp.ErreurPowerPoint) as e:
            constructeur(app).construire(PLAN, "Z:/x.pptx", pause=0)
        self.assertIn("enregistrer", str(e.exception))

    def test_reglage_esthetique_en_echec_ne_bloque_pas(self):
        app = FausseApp()
        app.prs.SlideMaster = Objet()          # Background absent -> le réglage du fond échoue
        constructeur(app).construire(PLAN, "x.pptx", pause=0)
        self.assertEqual(app.prs.enregistre, "x.pptx")

    def test_com_libere(self):
        etats = []
        c = pp.ConstructeurPowerPoint(fabrique=FausseApp, initialiser_com=lambda: True,
                                      liberer_com=lambda: etats.append("lib"), attendre=lambda s: None)
        c.construire(PLAN, "x.pptx", pause=0)
        self.assertEqual(etats, ["lib"])


if __name__ == "__main__":
    unittest.main()
