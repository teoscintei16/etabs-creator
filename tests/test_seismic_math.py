import unittest

from etabs_creator.seismic import SeismicParams, coefficient_for_period, combos, sd, seismic_coefficient, spectrum_points


class SpectrumTests(unittest.TestCase):
    P = SeismicParams(ag=0.2, gamma_I=1.0, beta0=2.5, Tb=0.07, Tc=0.7, Td=3.0, q=3.5)

    def test_corners_and_floor(self):
        self.assertAlmostEqual(sd(0, self.P), 0.2 * 9.81, 6)                                      # Sd(0) = ag·g
        self.assertAlmostEqual(sd(0.4, self.P), 0.2 * 9.81 * 2.5 / 3.5, 6)                        # platou β0/q
        self.assertAlmostEqual(sd(6.0, self.P), 0.2 * 9.81 * 0.2, 6)                              # minim 0.2·ag·g
        pts = dict(spectrum_points(self.P))
        for t in (0.0, 0.07, 0.7, 3.0, 6.0):
            self.assertIn(t, pts)

    def test_coefficients(self):
        self.assertAlmostEqual(seismic_coefficient(self.P), 0.85 * 0.2 * 2.5 / 3.5, 5)
        self.assertEqual(coefficient_for_period(0.5, self.P), seismic_coefficient(self.P))        # pe platou coincide
        self.assertLess(coefficient_for_period(0.9, self.P), seismic_coefficient(self.P))         # peste TC scade


class ComboTests(unittest.TestCase):
    P = SeismicParams()

    def test_counts_and_structure(self):
        cs = dict(combos(True, ["EXP", "EXN", "EYP", "EYN"], ["SPECX", "SPECY"], self.P))
        self.assertEqual(len(cs), 3 + 8 + 32 + 4)                                                 # ULS/SLS + pure + ortogonale + spectru
        self.assertEqual(cs["ULS"], [("Dead", 1.35), ("Permanenta", 1.35), ("Live", 1.5)])
        self.assertEqual(cs["SLS_QP"][-1], ("Live", 0.3))
        self.assertEqual(cs["S_+EXP_-0.3EYN"][-2:], [("EXP", 1.0), ("EYN", -0.3)])
        self.assertTrue(all(c[:3] == [("Dead", 1.0), ("Permanenta", 1.0), ("Live", 0.3)] for n, c in cs.items() if n.startswith("S_")))

    def test_extra_permanent_only_in_gravity_combinations(self):
        cs = dict(combos(True, ["EXP", "EXN", "EYP", "EYN"], [], self.P, extra_perm=["Pamant"]))
        self.assertEqual({n for n, c in cs.items() if any(l == "Pamant" for l, _ in c)}, {"ULS", "SLS_CAR", "SLS_QP"})

    def test_without_permanent_pattern(self):
        cs = dict(combos(False, [], [], self.P))
        self.assertEqual(cs["ULS"], [("Dead", 1.35), ("Live", 1.5)])


if __name__ == "__main__":
    unittest.main()
