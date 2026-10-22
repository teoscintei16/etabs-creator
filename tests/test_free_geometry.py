import math
import unittest

from etabs_creator.connect import GenError
from etabs_creator.free import build_free_plan, parse_wall_edges
from etabs_creator.free.levels import Level, smooth_level, story_levels
from etabs_creator.free.outline import centroid, is_star_shaped, outline, signed_area
from etabs_creator.free.radial import Radial
from etabs_creator.free.spline import catmull_rom_closed, parse_points
from etabs_creator.spec import ModelSpec


def spec(**kw):
    return ModelSpec.from_flat({"calibrate_static": False, **kw})


class OutlineTests(unittest.TestCase):
    def test_circle_area_centroid_and_orientation(self):
        pts = outline(spec(free_shape="circle", free_radius=10.0, free_samples=48))
        self.assertAlmostEqual(signed_area(pts), math.pi * 100, delta=3.0)                    # poligon inscris: putin sub pi*R^2
        self.assertTrue(signed_area(pts) > 0)
        cx, cy = centroid(pts)
        self.assertAlmostEqual(cx, 0, 6)
        self.assertAlmostEqual(cy, 0, 6)

    def test_every_shape_is_star_shaped_and_centered(self):
        for shape in ("circle", "ellipse", "semicircle", "polygon", "trapezoid", "lobed", "spline"):
            pts = outline(spec(free_shape=shape))
            self.assertTrue(is_star_shaped(pts), shape)
            self.assertAlmostEqual(centroid(pts)[0], 0, 5)
            self.assertGreaterEqual(len(pts), 4)

    def test_semicircle_has_a_straight_diameter_subdivided(self):
        pts = outline(spec(free_shape="semicircle", free_radius=12.0, free_edge_max=5.0))
        ys = sorted(p[1] for p in pts)
        on_diameter = [p for p in pts if abs(p[1] - ys[0]) < 1e-6]                              # laturile drepte au aceeasi cota y
        self.assertGreaterEqual(len(on_diameter), 5)                                            # 24 m impartiti in parti de max 5 m

    def test_trapezoid_corners(self):
        pts = outline(spec(free_shape="trapezoid", trap_bottom=20.0, trap_top=10.0, trap_depth=10.0, free_edge_max=100.0))
        self.assertEqual(len(pts), 4)
        widths = sorted({round(abs(a[0] - b[0]), 3) for a in pts for b in pts if abs(a[1] - b[1]) < 1e-9 and a != b})
        self.assertEqual(widths, [10.0, 20.0])

    def test_spline_passes_through_control_points_and_rejects_non_star_shapes(self):
        ctrl = parse_points("10,0;0,10;-10,0;0,-10")
        curve = catmull_rom_closed(ctrl, 8)
        self.assertEqual(len(curve), 32)
        for c in ctrl:
            self.assertTrue(any(math.dist(c, p) < 1e-9 for p in curve))
        with self.assertRaises(GenError):                                                          # forma de C (nu e stelata fata de centroid)
            outline(spec(free_shape="spline", spline_points="10,10;10,-10;-10,-10;-10,-6;4,-6;4,6;-10,6;-10,10"))
        with self.assertRaises(GenError):
            parse_points("1,1;2,2")
        with self.assertRaises(GenError):
            parse_points("a,b;1,1;2,2;3,3")

    def test_validation(self):
        for bad in (dict(free_shape="cub"), dict(free_shape="circle", free_radius=0), dict(free_shape="circle", atrium=0.95),
                    dict(free_shape="circle", taper=0.95), dict(free_shape="circle", free_wall_edges="all", twist_deg=5),
                    dict(free_shape="circle", free_columns="x"), dict(free_shape="circle", towers="0,0,3,3,4"), dict(free_shape="circle", shape="L")):
            with self.assertRaises(GenError, msg=str(bad)):
                spec(**bad).validate()


class RadialTests(unittest.TestCase):
    B = [(math.cos(2 * math.pi * j / 8), math.sin(2 * math.pi * j / 8)) for j in range(8)]

    def test_counts_without_atrium(self):
        r = Radial(self.B, 3, 0.0)
        self.assertEqual((len(r.nodes()), len(r.faces()), len(r.edges())), (1 + 3 * 8, 24, 24 + 24))
        self.assertEqual(sum(1 for f in r.faces() if len(f) == 3), 8)                              # triunghiuri la centru
        self.assertEqual(r.xy((0, 0)), (0.0, 0.0))
        self.assertAlmostEqual(math.hypot(*r.xy((3, 2))), 1.0)
        self.assertAlmostEqual(math.hypot(*r.xy((1, 2))), 1 / 3)

    def test_atrium_leaves_a_hole(self):
        r = Radial(self.B, 3, 0.4)
        self.assertEqual((len(r.nodes()), len(r.faces())), (4 * 8, 24))
        self.assertTrue(all(len(f) == 4 for f in r.faces()))
        self.assertAlmostEqual(math.hypot(*r.xy((0, 0))), 0.4)

    def test_faces_are_counter_clockwise(self):
        r = Radial(self.B, 2, 0.0)
        for f in r.faces():
            self.assertGreater(signed_area([r.xy(n) for n in f]), 0)


class LevelTests(unittest.TestCase):
    def test_smooth_taper_scales_linearly_and_story_levels_chain(self):
        s = spec(free_shape="circle", stories=4, taper=0.6)
        self.assertEqual([round(smooth_level(s, k, 4).scale, 3) for k in range(5)], [1.0, 0.85, 0.7, 0.55, 0.4])
        lo, hi = story_levels(s, 2, 4)
        self.assertEqual((lo.scale, hi.scale), (smooth_level(s, 1, 4).scale, smooth_level(s, 2, 4).scale))     # sus-ul unui etaj = josul urmatorului

    def test_steps_keep_each_story_vertical(self):
        s = spec(free_shape="circle", stories=6, step_every=2, step_scale=0.8)
        scales = [story_levels(s, k, 6)[0].scale for k in range(1, 7)]
        self.assertEqual([round(x, 3) for x in scales], [1.0, 1.0, 0.8, 0.8, 0.64, 0.64])
        for k in range(1, 7):
            lo, hi = story_levels(s, k, 6)
            self.assertEqual(lo, hi)

    def test_twist_and_lean(self):
        s = spec(free_shape="circle", stories=3, twist_deg=10, lean_x=0.5)
        lv = smooth_level(s, 2, 3)
        self.assertAlmostEqual(math.degrees(lv.angle), 20)
        x, _y = lv.apply((1.0, 0.0))
        self.assertAlmostEqual(x, math.cos(math.radians(20)) * lv.scale + 1.0, 6)
        self.assertEqual(Level().apply((2.0, 3.0)), (2.0, 3.0))


class FreePlanTests(unittest.TestCase):
    def plan(self, **kw):
        return build_free_plan(spec(free_shape="circle", free_samples=12, free_rings=2, free_edge_max=100.0, **kw))

    def test_wall_edge_syntax_and_pier_groups(self):
        self.assertEqual(parse_wall_edges("alternate", 6), [0, 2, 4])
        self.assertEqual(parse_wall_edges("all", 3), [0, 1, 2])
        self.assertEqual(parse_wall_edges("none", 3), [])
        with self.assertRaises(GenError):
            parse_wall_edges("9", 3)
        p = self.plan(free_wall_edges="0,1,2,6,7")
        self.assertEqual(p.piers, {0: "PW1", 1: "PW1", 2: "PW1", 6: "PW2", 7: "PW2"})

    def test_columns_modes_and_wall_nodes_are_skipped(self):
        p = self.plan()
        top = len(p.stories) - 1
        self.assertEqual(len(p.columns(top)), 1 + 2 * 12)                                          # implicit: toate nodurile
        self.assertEqual(len(self.plan(free_columns="perimeter").columns(top)), 12)
        self.assertEqual(self.plan(free_columns="none").columns(top), [])
        w = self.plan(free_wall_edges="0,1", free_columns="perimeter")
        self.assertEqual(len(w.columns(top)), 12 - 3)                                              # nodurile 0, 1, 2 sunt capete de perete

    def test_beams_exclude_replaced_boundary_edges(self):
        p = self.plan(free_wall_edges="0,1,2")
        self.assertEqual(len(p.beams(0)), len(p.radial.edges()) - 3)
        b = self.plan(basement=1)
        self.assertEqual(len(b.beams(0)), len(b.radial.edges()) - 12)                              # tot conturul e perete in subsol

    def test_basement_continues_selected_walls_and_adds_perimeter_walls_elsewhere(self):
        p = self.plan(basement=1, free_wall_edges="0,1")
        self.assertEqual([w["edge"] for w in p.wall_panels(0)], [0, 1])
        self.assertEqual([w["edge"] for w in p.basement_walls(0)], list(range(2, 12)))
        self.assertEqual(p.basement_walls(1), [])                                                  # peste teren nu exista pereti de subsol
        off = self.plan(basement=1, free_wall_edges="0,1", walls_through_basement=False)
        self.assertEqual(off.wall_panels(0), [])
        self.assertEqual(len(off.basement_walls(0)), 12)

    def test_levels_are_identity_in_the_basement(self):
        p = self.plan(basement=1, taper=0.5, stories=3)
        self.assertEqual(p.levels(0), (Level(), Level()))
        self.assertEqual(p.above_number(1), 1)
        self.assertEqual(p.levels(3)[1].scale, 0.5)


if __name__ == "__main__":
    unittest.main()
