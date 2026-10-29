import io
import json
import socket
import unittest
import urllib.error

from autopresentation import gemini


class FauxFlux:
    def __init__(self, donnees):
        self._d = json.dumps(donnees).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._d


def reponse(texte):
    return {"candidates": [{"content": {"parts": [{"text": texte}]}}]}


def erreur_http(code, message=""):
    corps = json.dumps({"error": {"message": message}}).encode()
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(corps))


class TestGemini(unittest.TestCase):
    def test_succes_et_requete(self):
        vues = []

        def ouvrir(req, timeout):
            vues.append(req)
            return FauxFlux(reponse('{"a": 1}'))

        texte = gemini.generer_json("CLE-SECRETE", "mon-modele", "bonjour", ouvrir=ouvrir)
        self.assertEqual(texte, '{"a": 1}')
        req = vues[0]
        self.assertIn("mon-modele:generateContent", req.full_url)
        self.assertNotIn("CLE-SECRETE", req.full_url)          # la clé n'est jamais dans l'adresse
        self.assertEqual(req.get_header("X-goog-api-key"), "CLE-SECRETE")
        corps = json.loads(req.data)
        self.assertEqual(corps["contents"][0]["parts"][0]["text"], "bonjour")

    def test_sans_cle(self):
        with self.assertRaises(gemini.ErreurGemini):
            gemini.generer_json("  ", "m", "x", ouvrir=lambda *a, **k: None)

    def test_modele_par_defaut(self):
        vues = []
        gemini.generer_json("k", "", "x", ouvrir=lambda r, timeout: vues.append(r) or FauxFlux(reponse("{}")))
        self.assertIn(gemini.MODELE_DEFAUT, vues[0].full_url)

    def test_cle_invalide_sans_fuite(self):
        def ouvrir(req, timeout):
            raise erreur_http(400, "API key not valid. Please pass a valid API key.")
        with self.assertRaises(gemini.ErreurGemini) as c:
            gemini.generer_json("CLE-SECRETE", "m", "x", ouvrir=ouvrir)
        self.assertIn("Clé Gemini refusée", str(c.exception))
        self.assertNotIn("CLE-SECRETE", str(c.exception))

    def test_modele_introuvable(self):
        def ouvrir(req, timeout):
            raise erreur_http(404)
        with self.assertRaises(gemini.ErreurGemini) as c:
            gemini.generer_json("k", "faux-modele", "x", ouvrir=ouvrir)
        self.assertIn("faux-modele", str(c.exception))

    def test_429_reessaie_puis_reussit(self):
        appels, attentes, messages = [], [], []

        def ouvrir(req, timeout):
            appels.append(1)
            if len(appels) < 3:
                raise erreur_http(429)
            return FauxFlux(reponse("{}"))

        gemini.generer_json("k", "m", "x", ouvrir=ouvrir, attendre=attentes.append, sur_attente=messages.append)
        self.assertEqual(len(appels), 3)
        self.assertEqual(attentes, list(gemini.ATTENTES_429))
        self.assertEqual(len(messages), 2)

    def test_429_abandonne_apres_les_essais(self):
        appels = []

        def ouvrir(req, timeout):
            appels.append(1)
            raise erreur_http(429)

        with self.assertRaises(gemini.ErreurGemini) as c:
            gemini.generer_json("k", "m", "x", ouvrir=ouvrir, attendre=lambda s: None)
        self.assertEqual(len(appels), 1 + len(gemini.ATTENTES_429))
        self.assertIn("Limite", str(c.exception))

    def test_reseau_et_delai(self):
        def hors_ligne(req, timeout):
            raise urllib.error.URLError("pas de réseau")

        def lent(req, timeout):
            raise socket.timeout()

        with self.assertRaises(gemini.ErreurGemini) as c1:
            gemini.generer_json("k", "m", "x", ouvrir=hors_ligne)
        self.assertIn("Internet", str(c1.exception))
        with self.assertRaises(gemini.ErreurGemini) as c2:
            gemini.generer_json("k", "m", "x", ouvrir=lent)
        self.assertIn("trop de temps", str(c2.exception))

    def test_reponses_bloquees_ou_vides(self):
        with self.assertRaises(gemini.ErreurGemini) as c:
            gemini.extraire_texte({"promptFeedback": {"blockReason": "SAFETY"}})
        self.assertIn("SAFETY", str(c.exception))
        with self.assertRaises(gemini.ErreurGemini):
            gemini.extraire_texte({})
        with self.assertRaises(gemini.ErreurGemini):
            gemini.extraire_texte(reponse("   "))

    def test_reponse_non_json(self):
        class Bizarre(FauxFlux):
            def read(self):
                return b"<html>pas du json</html>"
        with self.assertRaises(gemini.ErreurGemini):
            gemini.generer_json("k", "m", "x", ouvrir=lambda r, timeout: Bizarre({}))


if __name__ == "__main__":
    unittest.main()
