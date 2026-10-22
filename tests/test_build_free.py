import math
import unittest

from etabs_creator.connect import GenError
from tests.fakes import build

BASE = dict(free_edge_max=100.0, free_samples=12, free_rings=2, stories=3)


def circle(**kw):
    return build(free_shape="circle", **{**BASE, **kw})


class FreeBuildTests(unittest.TestCase):
    def test_counts_for_a_circle(self):
        sap, res = circle()
        o = res["objects"]
        self.assertEqual(o["placi"], 3 * (12 + 12 * 1))                                           # 12 triunghiuri + 12 patrulatere pe nivel, 3 etaje
        self.assertEqual(o["stalpi"], 3 * (1 + 2 * 12))                                           # toate nodurile
        self.assertEqual(o["grinzi"], 3 * 48)                                                     # muchii ale retelei, 3 niveluri
        self.assertEqual(res["towers"], 1)
        self.assertEqual(len(sap.calls("PointObj.SetRestraint")), 25)                             # capetele de jos ale stalpilor
        slabs = [a for a in sap.calls("AreaObj.AddByCoord") if a[5].startswith("P")]
        self.assertEqual({len(a[1]) for a in slabs}, {3, 4})
        self.assertEqual(len(sap.calls("AreaObj.SetDiaphragm")), 72)

    def test_slab_polygons_sit_at_the_story_top_level(self):
        sap, _ = circle()
        slabs = [a for a in sap.calls("AreaObj.AddByCoord") if a[5].startswith("P")]
        self.assertEqual(sorted({a[3][0] for a in slabs}), [3.0, 6.0, 9.0])
        self.assertTrue(all(len(set(a[3])) == 1 for a in slabs))                                  # fiecare placa e orizontala

    def test_pyramid_columns_are_inclined_and_continuous(self):
        sap, _ = circle(taper=0.6, free_columns="perimeter")
        cols = [a for a in sap.calls("FrameObj.AddByCoord") if abs(a[2] - a[5]) > 1e-9]
        story1 = [a for a in cols if a[2] == 0.0]
        story2 = [a for a in cols if a[2] == 3.0]
        r_bottom = math.hypot(story1[0][0], story1[0][1])
        r_mid = math.hypot(story1[0][3], story1[0][4])
        self.assertAlmostEqual(r_bottom, 12.0 * 1.0, delta=0.01)
        self.assertAlmostEqual(r_mid, 12.0 * (1 - 0.6 / 3), delta=0.01)
        match = [(a[3], a[4]) for a in story1]
        self.assertEqual({(round(x, 6), round(y, 6)) for x, y, *_ in [(b[0], b[1]) for b in story2]}, {(round(x, 6), round(y, 6)) for x, y in match})

    def test_trapezoidal_wall_panels_when_the_plan_tapers(self):
        sap, res = circle(taper=0.3, free_wall_edges="all", free_columns="perimeter")
        self.assertEqual(res["objects"]["pereti"], 3 * 12)
        walls = [a for a in sap.calls("AreaObj.AddByCoord") if a[5] == "W25"]
        a = walls[0]
        bottom = math.dist((a[1][0], a[2][0]), (a[1][1], a[2][1]))
        top = math.dist((a[1][3], a[2][3]), (a[1][2], a[2][2]))
        self.assertAlmostEqual(top / bottom, 0.9, delta=0.002)                                      # 1 - 0.3 / 3 pe un etaj
        self.assertEqual(res["objects"]["pereti_inclinati"], 36)
        self.assertEqual(sap.calls("AreaObj.SetPier"), [])                                         # panourile inclinate nu pot avea eticheta Pier

    def test_vertical_wall_panels_get_one_pier_label(self):
        sap, res = circle(free_wall_edges="all", free_columns="perimeter")
        self.assertEqual(res["piers"], ["PW1"])
        self.assertEqual(len(sap.calls("AreaObj.SetPier")), 3 * 12)
        self.assertNotIn("pereti_inclinati", res["objects"])

    def test_stepped_pyramid_has_vertical_stories(self):
        sap, _ = circle(step_every=1, step_scale=0.8, free_columns="perimeter")
        cols = [a for a in sap.calls("FrameObj.AddByCoord") if abs(a[2] - a[5]) > 1e-9]
        for a in cols:
            self.assertAlmostEqual(math.hypot(a[0], a[1]), math.hypot(a[3], a[4]), places=6)       # coloana verticala pe fiecare etaj

    def test_basement_under_a_free_plan_continues_the_chosen_walls(self):
        sap, res = circle(basement=1, free_wall_edges="0,1,2")
        o = res["objects"]
        self.assertEqual(o["pereti"], 3 * (3 + 0) + 3)                                             # 3 panouri pe etaj + 3 in subsol
        self.assertEqual(o["pereti_subsol"], 12 - 3)
        self.assertEqual(res["stories"], ["E2", "E1", "P", "S1"])
        loads = [a for a in sap.calls("AreaObj.SetLoadUniform") if a[1] == "Impingere_pamant"]
        self.assertEqual({a[2] for a in loads}, {-25.0})                                           # spre interior = opus axei locale 3 (spre exterior)

    def test_coordinates_are_rounded_to_a_millimetre(self):
        sap, _ = circle(free_radius=12.3456789)
        coords = [v for a in sap.calls("FrameObj.AddByCoord") for v in a[:6]]
        self.assertTrue(all(abs(v * 1000 - round(v * 1000)) < 1e-6 for v in coords))

    def test_twist_with_walls_is_rejected_without_walls_it_builds(self):
        with self.assertRaises(GenError):
            circle(twist_deg=5, free_wall_edges="all")
        sap, res = circle(twist_deg=5)
        self.assertGreater(res["objects"]["stalpi"], 0)

    def test_every_shape_builds(self):
        for shape in ("ellipse", "semicircle", "polygon", "trapezoid", "lobed", "spline"):
            sap, res = build(free_shape=shape, stories=2)
            self.assertGreater(res["objects"]["placi"], 0, shape)
            self.assertGreater(res["objects"]["grinzi"], 0, shape)

    def test_rules_still_apply(self):
        sap, _ = circle()
        self.assertEqual(sap.calls("ModalEigen.SetNumberModes")[0], ("Modal", 9, 1))
        self.assertEqual(len(sap.calls("RespCombo.Add")), 47)


if __name__ == "__main__":
    unittest.main()
