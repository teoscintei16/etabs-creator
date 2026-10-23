import math
import unittest

from etabs_creator.connect import GenError
from etabs_creator.shells import build_mesh, sphere_center
from etabs_creator.shells.layout import build_layout
from etabs_creator.spec import ModelSpec
from tests.fakes import build

OPERA = dict(name="opera", structure="opera", opera=True, stories=2, bays=12, travei=15, span_x=10.0, span_y=12.0, story_height=6.0, basement=1,
             basement_height=6.0, mesh_max=2.0, modes_per_story=10)


def spec(**kw) -> ModelSpec:
    return ModelSpec.from_flat({**OPERA, **kw})


class SphereTests(unittest.TestCase):
    A, B, C = (10, 12, 12), (10, 60, 12), (24, 57, 64)

    def test_all_points_lie_on_the_sphere_through_the_vertices(self):
        o = sphere_center(self.A, self.B, self.C, 75.2)
        for p in (self.A, self.B, self.C):
            self.assertAlmostEqual(math.dist(o, p), 75.2, 6)
        self.assertLess(o[2], self.C[2])                                         # centrul sub creasta: coaja convexa spre cer

    def test_mesh_nodes_on_sphere_base_on_grid_and_ribs_are_great_circles(self):
        m = build_mesh("t", self.A, self.B, self.C, 75.2, 2.0, 10, 12.0)
        for p in m.rim()[1:]:                                                    # muchia frontala exact pe sfera
            self.assertAlmostEqual(math.dist(m.center, p), 75.2, 2)
        for row in m.nodes:                                                      # restul: baza indreptata (deplasare orizontala ≤ 5 m)
            for p in row[1:]:
                self.assertLess(abs(math.dist(m.center, p) - 75.2), 5.0)
        base = m.base_nodes()
        self.assertEqual([p[1] for p in base][:3], [24.0, 26.0, 28.0])           # primul rand la A.y + tip
        self.assertEqual({p[2] for p in base}, {12.0})                           # baza exact la cota podiumului
        self.assertEqual({p[0] for p in base}, {10})
        self.assertEqual(m.rim()[0][1], 60.0)                                    # muchia frontala porneste din B

    def test_aspect_ratio_stays_small(self):
        m = build_mesh("t", self.A, self.B, self.C, 75.2, 2.0, 10, 12.0)
        worst = 0.0
        for f in m.faces():
            e = [math.dist(f[k], f[(k + 1) % 4]) for k in range(4)]
            worst = max(worst, max(e) / min(e))
        self.assertLess(worst, 3.5)

    def test_shell_that_does_not_fit_the_sphere_is_rejected(self):
        with self.assertRaises(GenError):
            sphere_center((0, 0, 0), (200, 0, 0), (100, 10, 30), 75.2)


class LayoutTests(unittest.TestCase):
    def test_default_layout_has_14_shells_and_hall_voids(self):
        lay = build_layout(spec())
        self.assertEqual((lay.z0, len(lay.shells), len(lay.halls)), (12.0, 14, 2))
        self.assertEqual(len(lay.voids), 2 * 4 * 8)                              # 2 sali × 4 deschideri × 8 travei
        self.assertEqual({s.hall for s in lay.shells}, {"CH", "OT", "REST"})
        self.assertEqual(sum(s.on_wall for s in lay.shells), 12)
        w, e = (s for s in lay.shells if s.hall == "CH" and s.row == 1)
        self.assertEqual((w.foot_x, e.foot_x), (10.0, 50.0))
        self.assertEqual(w.c[0] - w.foot_x, e.foot_x - e.c[0])                   # perechea e oglindita fata de axa

    def test_hall_scale_lowers_the_second_hall(self):
        s = spec()
        lay = build_layout(s)
        top = {h: max(sh.mesh(s).max_z() for sh in lay.shells if sh.hall == h) for h in ("CH", "OT")}
        self.assertGreater(top["CH"], top["OT"])

    def test_off_grid_foot_is_rejected(self):
        with self.assertRaises(GenError):
            build_layout(spec(hall_half=19.0))
        with self.assertRaises(GenError):
            build_layout(spec(shell_dy=5.0))

    def test_mismatched_row_lists_are_rejected(self):
        with self.assertRaises(GenError):
            spec(shell_heights="52,42").validate()


class OperaBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sap, cls.res = build(**OPERA)

    def test_shell_stories_added_above_the_podium(self):
        base, names, heights = self.sap.s["stories"]
        self.assertEqual(names, ["S1", "P", "E1", "T1", "T2", "T3", "T4"])
        self.assertEqual((base, heights[3:]), (-6.0, [13.0] * 4))

    def test_every_shell_gets_areas_ribs_foot_rim_and_ties(self):
        c = self.res["objects"]
        self.assertGreater(c["coji"], 14 * 100)
        for k in ("coaste", "grinzi_picior", "grinzi_frontale", "legaturi_coama"):
            self.assertGreater(c[k], 0, k)

    def test_hall_walls_have_pier_labels_and_foot_line_beams_are_replaced(self):
        piers = {a[0] for a in self.sap.calls("PierLabel.SetPier")}
        self.assertTrue({"CH_W", "CH_E", "OT_S", "OT_N", "PX1"} <= piers)                   # peretii salilor + peretele de rigidizare al podiumului
        self.assertEqual(self.res["piers"], sorted(piers))
        self.assertGreater(self.res["objects"]["pereti"], 100)

    def test_wind_patterns_and_combinations(self):
        pats = {a[0] for a in self.sap.calls("LoadPatterns.Add")}
        self.assertTrue({"Vant_X", "Vant_Y", "Permanenta"} <= pats)
        combos = {a[0] for a in self.sap.calls("RespCombo.Add")}
        self.assertTrue({"ULS_Vant_X", "ULS_Vant_X_fav", "SLS_Vant_Y"} <= combos)
        wind = [a for a in self.sap.calls("AreaObj.SetLoadUniform") if a[1] == "Vant_X"]
        self.assertTrue(wind and all(a[3] == 7 and a[5] == "Global" for a in wind))        # proiectat pe X, global

    def test_modes_count_includes_shell_stories(self):
        self.assertEqual(self.sap.calls("ModalEigen.SetNumberModes")[0], ("Modal", 10 * (2 + 4), 1))

    def test_no_columns_or_beams_inside_the_halls(self):
        # nodul (2, 4) e in interiorul salii de vest (x 20, y 48): la P si E1 nu are stalp, la S1 are
        cols = [a for a in self.sap.calls("FrameObj.AddByCoord") if (a[0], a[1]) == (20.0, 48.0) and a[2] != a[5]]
        self.assertEqual({(a[2], a[5]) for a in cols}, {(-6.0, 0.0)})

    def test_ritz_modal_case_replaces_the_eigen_case(self):
        sap, _ = build(**{**OPERA, "modal_type": "ritz"})
        self.assertEqual(sap.calls("Ritz.SetCase"), [("Modal",)])
        self.assertEqual(sap.calls("Ritz.SetLoads")[0], ("Modal", 2, ["Accel"] * 2, ["UX", "UY"], [0, 0], [99.0] * 2))
        self.assertEqual(sap.calls("Ritz.SetNumberModes")[0], ("Modal", 10 * 6, 1))
        self.assertEqual(sap.calls("ModalEigen.SetNumberModes"), [])

    def test_without_wind_no_wind_patterns(self):
        sap, _ = build(**{**OPERA, "wind": 0.0})
        self.assertNotIn("Vant_X", {a[0] for a in sap.calls("LoadPatterns.Add")})


if __name__ == "__main__":
    unittest.main()
