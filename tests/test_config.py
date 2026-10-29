import os
import tempfile
import unittest
from unittest import mock

from autopresentation import config, gemini


class TestConfig(unittest.TestCase):
    def test_valeurs_par_defaut(self):
        with tempfile.TemporaryDirectory() as d:
            r = config.charger(d)
        self.assertEqual(r["cle"], "")
        self.assertEqual(r["modele"], gemini.MODELE_DEFAUT)

    def test_aller_retour(self):
        with tempfile.TemporaryDirectory() as d:
            config.enregistrer({"cle": "abc", "modele": "m", "dossier_sortie": "é"}, d)
            r = config.charger(d)
        self.assertEqual((r["cle"], r["modele"], r["dossier_sortie"]), ("abc", "m", "é"))

    def test_fichier_corrompu(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "reglages.json"), "w") as f:
                f.write("{pas du json")
            self.assertEqual(config.charger(d)["cle"], "")

    def test_cle_variable_environnement(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": " env "}):
            self.assertEqual(config.cle_effective({"cle": ""}), "env")
            self.assertEqual(config.cle_effective({"cle": "saisie"}), "saisie")


if __name__ == "__main__":
    unittest.main()
