import unittest

from autopresentation import plan


class TestPlan(unittest.TestCase):
    def test_consigne_contient_sujet_et_nombre(self):
        c = plan.construire_consigne("  La microfinance  ", 6)
        self.assertIn("La microfinance", c)
        self.assertIn("6 diapositives", c)

    def test_json_dans_bloc_markdown(self):
        brut = '```json\n{"titre": "T", "diapos": [{"titre": "A", "puces": ["x"], "notes": "n"}]}\n```'
        p = plan.valider_plan(brut)
        self.assertEqual(p["titre"], "T")
        self.assertEqual(p["diapos"][0]["puces"], ["x"])

    def test_json_avec_texte_autour(self):
        brut = 'Voici : {"titre": "T", "diapos": [{"titre": "A", "puces": [], "notes": ""}]} fin'
        self.assertEqual(plan.valider_plan(brut)["diapos"][0]["titre"], "A")

    def test_nettoyage_puces_et_limites(self):
        brut = {"titre": "T", "diapos": [{"titre": "A", "puces": ["- un", "• deux", "", None] + ["x"] * 20}]}
        p = plan.valider_plan(brut)
        self.assertEqual(p["diapos"][0]["puces"][:2], ["un", "deux"])
        self.assertEqual(len(p["diapos"][0]["puces"]), plan.MAX_PUCES)

    def test_titre_par_defaut_et_diapos_sans_titre_ignorees(self):
        p = plan.valider_plan({"diapos": [{"puces": ["a"]}, {"titre": "B"}]})
        self.assertEqual(len(p["diapos"]), 1)
        self.assertEqual(p["titre"], "B")

    def test_nb_max(self):
        brut = {"diapos": [{"titre": str(i)} for i in range(10)]}
        self.assertEqual(len(plan.valider_plan(brut, nb_max=4)["diapos"]), 4)

    def test_erreurs(self):
        for mauvais in ("", "pas de json", '{"titre": "T"', '{"diapos": []}', '{"diapos": "x"}', "[1, 2]"):
            with self.assertRaises(plan.ErreurPlan, msg=mauvais):
                plan.valider_plan(mauvais)


if __name__ == "__main__":
    unittest.main()
