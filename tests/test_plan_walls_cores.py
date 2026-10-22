import unittest

from etabs_creator.connect import GenError
from etabs_creator.plan import build_plan
from etabs_creator.plan.cores import core_rect, core_runs
from etabs_creator.plan.indices import groups, parse_indices
from etabs_creator.spec import ModelSpec


def spec(**kw):
    return ModelSpec.from_flat({"calibrate_static": False, **kw})


class IndicesTests(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual(parse_indices("first,last", 4, "x"), [0, 3])
        self.assertEqual(parse_indices("middle", 3, "x"), [1])
        self.assertEqual(parse_indices("all", 3, "x"), [0, 1, 2])
        self.assertEqual(parse_indices("0, 2", 3, "x"), [0, 2])
        self.assertEqual(parse_indices("none", 3, "x", allow_none=True), [])
        for bad in ("5", "abc", "", "-1", "none"):
            with self.assertRaises(GenError):
                parse_indices(bad, 3, "x")

    def test_groups(self):
        self.assertEqual(groups([0, 1, 3]), [[0, 1], [3]])


class RunsTests(unittest.TestCase):
    def test_consecutive_bays_form_one_pier(self):
        runs = build_plan(spec(bays=4, travei=2, walls=True, wall_lines_x="0", wall_bays_x="0,1,3", wall_lines_y="first", wall_bays_y="middle")).runs
        self.assertEqual([(r["axis"], r["line"], r["bays"], r["pier"]) for r in runs],
                         [("X", 0, [0, 1], "PX1"), ("X", 0, [3], "PX2"), ("Y", 0, [0], "PY1")])

    def test_walls_replace_columns_and_beams(self):
        p = build_plan(spec(bays=3, travei=3, walls=True, wall_lines_x="0", wall_bays_x="1", wall_lines_y="0", wall_bays_y="1"))
        idx = len(p.stories) - 1
        self.assertFalse(set(p.columns(idx)) & {(1, 0), (2, 0), (0, 1), (0, 2)})                 # capetele peretilor n-au stalp
        bx, by = p.beams(idx)
        self.assertNotIn((0, 1), bx)
        self.assertNotIn((0, 1), by)


class CoreTests(unittest.TestCase):
    """Nucleu auto-centrat 2×2 intr-un turn 4×4: linii 1..3, deschideri 1 si 2."""

    def runs(self, shape, nx=4, ny=4, cells=""):
        return core_runs(shape, cells, nx, ny)

    def test_default_rect_is_centered_half_plan(self):
        self.assertEqual(core_rect("", 4, 4), (1, 1, 2, 2))
        self.assertEqual(core_rect("", 5, 3), (1, 0, 2, 2))
        self.assertEqual(core_rect("0,1,3,2", 4, 4), (0, 1, 3, 2))

    def test_shapes(self):
        b = [1, 2]
        self.assertEqual(self.runs("L"), [("X", 1, b), ("Y", 1, b)])
        self.assertEqual(self.runs("C"), [("X", 1, b), ("X", 3, b), ("Y", 1, b)])
        self.assertEqual(self.runs("I"), [("X", 1, b), ("X", 3, b), ("Y", 2, b)])
        self.assertEqual(self.runs("H"), [("Y", 1, b), ("Y", 3, b), ("X", 2, b)])
        self.assertEqual(self.runs("T"), [("X", 3, b), ("Y", 2, b)])
        self.assertEqual(self.runs(""), [])

    def test_invalid(self):
        for args in (("I", "0,0,1,2", 4, 4), ("H", "0,0,2,1", 4, 4), ("L", "3,3,2,2", 4, 4), ("L", "a", 4, 4)):
            with self.assertRaises(GenError, msg=str(args)):
                core_runs(*args)

    def test_core_becomes_piers_in_the_plan(self):
        p = build_plan(spec(bays=4, travei=4, walls=True, wall_lines_x="none", wall_bays_x="none", wall_lines_y="none", wall_bays_y="none", core_shape="C"))
        self.assertEqual([(r["axis"], r["line"], r["pier"]) for r in p.runs], [("X", 1, "PX1"), ("X", 3, "PX2"), ("Y", 1, "PY1")])
        idx = len(p.stories) - 1
        self.assertEqual({(w["axis"], w["line"], w["bay"]) for w in p.wall_panels(idx)},
                         {("X", 1, 1), ("X", 1, 2), ("X", 3, 1), ("X", 3, 2), ("Y", 1, 1), ("Y", 1, 2)})

    def test_core_merges_with_configured_walls_on_the_same_line(self):
        p = build_plan(spec(bays=4, travei=4, walls=True, wall_lines_x="1", wall_bays_x="0", wall_lines_y="none", wall_bays_y="none", core_shape="L"))
        x1 = [r for r in p.runs if r["axis"] == "X" and r["line"] == 1]
        self.assertEqual([r["bays"] for r in x1], [[0, 1, 2]])                                    # perete configurat + flansa nucleului = un singur perete
        self.assertEqual(len({r["pier"] for r in p.runs}), len(p.runs))


class CouplingTests(unittest.TestCase):
    SPEC = dict(walls=True, bays=3, travei=3, stories=2, wall_lines_x="first,last", wall_bays_x="0,2", wall_lines_y="none", wall_bays_y="none",
                coupling_bays_x="middle")

    def test_plan(self):
        p = build_plan(spec(**self.SPEC))
        self.assertEqual(p.coupling, {("X", 0, 1), ("X", 3, 1)})
        self.assertEqual([c["spandrel"] for c in p.coupling_beams(0)], ["SPX0_1", "SPX3_1"])
        self.assertNotIn((0, 1), p.beams(0)[0])                                                   # grinda normala din gol lipseste

    def test_all_means_every_non_wall_bay(self):
        p = build_plan(spec(**{**self.SPEC, "coupling_bays_x": "all"}))
        self.assertEqual(p.coupling, {("X", 0, 1), ("X", 3, 1)})


if __name__ == "__main__":
    unittest.main()
