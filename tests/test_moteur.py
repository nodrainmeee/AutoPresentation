import json
import unittest
from datetime import datetime

from autopresentation import moteur
from autopresentation.gemini import ErreurGemini
from autopresentation.powerpoint import ErreurPowerPoint

PLAN_JSON = json.dumps({"titre": "T", "diapos": [
    {"titre": "A", "puces": ["x"], "notes": "n"}, {"titre": "B", "puces": ["y"], "notes": "m"}]})


class FauxConstructeur:
    def __init__(self, resultat="C:/p.pptx", erreur=None):
        self.resultat, self.erreur, self.appel = resultat, erreur, None

    def construire(self, plan, chemin, **kw):
        self.appel = (plan, chemin, kw)
        if self.erreur:
            raise self.erreur
        kw["sur_progres"](1, 3)
        kw["sur_progres"](3, 3)
        return self.resultat


def parametres(**kw):
    p = {"sujet": "Sujet", "nb_diapos": 5, "theme": "Bleu nuit", "pause": 0, "lancer": True,
         "auto": 0, "cle": "k", "modele": "m", "dossier": "C:/docs"}
    p.update(kw)
    return p


def lancer(generateur, constructeur, **kw):
    m = moteur.MoteurPresentation(generateur, lambda: constructeur)
    assert m.demarrer(parametres(**kw))
    m.attendre(5)
    messages = []
    while not m.file.empty():
        messages.append(m.file.get())
    return m, messages


class TestMoteur(unittest.TestCase):
    def test_nom_fichier(self):
        n = moteur.nom_fichier("D", datetime(2026, 10, 29, 14, 5, 9))
        self.assertTrue(n.endswith("Presentation_2026-10-29_14-05-09.pptx"))

    def test_deroulement_complet(self):
        recu = {}

        def generateur(cle, modele, consigne, sur_attente):
            recu.update(cle=cle, modele=modele, consigne=consigne)
            return PLAN_JSON

        c = FauxConstructeur()
        _, messages = lancer(generateur, c)
        types = [t for t, _ in messages]
        self.assertEqual(messages[-1], ("termine", "C:/p.pptx"))
        self.assertIn(("progres", 100), messages)
        self.assertEqual(recu["cle"], "k")
        self.assertIn("Sujet", recu["consigne"])
        plan, chemin, kw = c.appel
        self.assertEqual(len(plan["diapos"]), 2)
        self.assertEqual(kw["theme"], "Bleu nuit")
        self.assertTrue(kw["lancer_diaporama"])
        self.assertNotIn("erreur", types)

    def test_erreurs_lisibles(self):
        cas = [
            (lambda *a: (_ for _ in ()).throw(ErreurGemini("clé refusée")), FauxConstructeur(), "clé refusée"),
            (lambda *a: "pas du json", FauxConstructeur(), "plan"),
            (lambda *a: PLAN_JSON, FauxConstructeur(erreur=ErreurPowerPoint("PowerPoint introuvable")), "introuvable"),
            (lambda *a: PLAN_JSON, FauxConstructeur(erreur=RuntimeError("boum")), "inattendue"),
        ]
        for generateur, constructeur, attendu in cas:
            _, messages = lancer(generateur, constructeur)
            self.assertEqual(messages[-1][0], "erreur", msg=attendu)
            self.assertIn(attendu, messages[-1][1])

    def test_arret_pendant_la_generation(self):
        m = moteur.MoteurPresentation(lambda *a: PLAN_JSON, lambda: FauxConstructeur())

        def generateur(cle, modele, consigne, sur_attente):
            m.arreter()
            return PLAN_JSON
        m._generateur = generateur
        m.demarrer(parametres())
        m.attendre(5)
        messages = []
        while not m.file.empty():
            messages.append(m.file.get())
        self.assertEqual(messages[-1], ("arrete", ""))

    def test_arret_pendant_la_construction(self):
        _, messages = lancer(lambda *a: PLAN_JSON, FauxConstructeur(resultat=None))
        self.assertEqual(messages[-1], ("arrete", ""))

    def test_pas_de_double_demarrage(self):
        import threading
        bloque = threading.Event()

        def lent(*a):
            bloque.wait(5)
            return PLAN_JSON

        m = moteur.MoteurPresentation(lent, lambda: FauxConstructeur())
        self.assertTrue(m.demarrer(parametres()))
        self.assertFalse(m.demarrer(parametres()))
        bloque.set()
        m.attendre(5)

    def test_le_nombre_de_diapos_est_limite(self):
        gros = json.dumps({"diapos": [{"titre": str(i)} for i in range(30)]})
        c = FauxConstructeur()
        lancer(lambda *a: gros, c, nb_diapos=4)
        self.assertEqual(len(c.appel[0]["diapos"]), 4)


if __name__ == "__main__":
    unittest.main()
