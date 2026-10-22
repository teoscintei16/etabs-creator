import unittest

from etabs_creator.connect import GenError
from etabs_creator.plan import build_plan
from etabs_creator.plan.basement import perimeter_edges, perimeter_nodes, wall_panels
from etabs_creator.plan.towers import above_count, towers_of
from etabs_creator.spec import ModelSpec


def spec(**kw):
    return ModelSpec.from_flat({"calibrate_static": False, **kw})


class BasementPlanTests(unittest.TestCase):
    def test_perimeter(self):
        xe, ye = perimeter_edges(2, 3)
        self.assertEqual((len(xe), len(ye)), (2 * 2, 3 * 2))
        self.assertEqual(len(perimeter_nodes(2, 3)), 12 - 2)                                    # 3x4 noduri, 2 interioare
        self.assertEqual(len(wall_panels(2, 3)), 2 * 2 + 3 * 2)

    def test_basement_columns_interior_only_and_beams_without_perimeter(self):
        p = build_plan(spec(bays=3, travei=3, stories=2, basement=1))
        self.assertEqual(len(p.columns(0)), 4)
        bx, by = p.beams(0)
        self.assertEqual((len(bx), len(by)), (2 * 3, 2 * 3))                                    # fara muchiile de perimetru


class TowerTests(unittest.TestCase):
    def test_default_single_tower_covers_the_grid(self):
        t = towers_of(spec(bays=3, travei=2, stories=4))
        self.assertEqual([(x.i0, x.j0, x.nx, x.ny, x.stories, x.prefix) for x in t], [(0, 0, 3, 2, 4, "")])

    def test_multiple_towers_get_prefixes_and_max_height(self):
        s = spec(bays=6, travei=3, towers="0,0,2,3,3;3,0,3,3,5")
        t = towers_of(s)
        self.assertEqual([x.prefix for x in t], ["T1_", "T2_"])
        self.assertEqual(above_count(s), 5)

    def test_invalid_towers(self):
        for bad in ("0,0,9,3,3", "0,0,2,2", "a,b,c,d,e", "0,0,2,2,0", "0,0,3,3,2;2,0,3,3,2"):
            with self.assertRaises(GenError, msg=bad):
                spec(bays=6, travei=3, towers=bad).validate()

    def test_cells_per_story_follow_each_towers_height(self):
        p = build_plan(spec(bays=6, travei=3, towers="0,0,2,3,3;3,0,3,3,5", basement=1))
        self.assertEqual([s.name for s in p.stories], ["S1", "P", "E1", "E2", "E3", "E4"])
        self.assertEqual([len(c) for c in p.cells], [18, 6 + 9, 6 + 9, 6 + 9, 9, 9])         # S1 = grila completa; apoi turnul 1 dispare dupa etajul 3
        self.assertNotIn((0, 0), p.cells[4])

    def test_columns_stop_where_nothing_is_above(self):
        p = build_plan(spec(bays=6, travei=3, towers="0,0,2,3,2;3,0,3,3,4"))
        high = {n for n in p.columns(3)}
        self.assertTrue(all(ix >= 3 for ix, _ in high))

    def test_walls_per_tower_in_local_coordinates_with_prefixed_piers(self):
        p = build_plan(spec(bays=6, travei=3, towers="0,0,3,3,2;3,0,3,3,2", walls=True, wall_lines_x="first", wall_bays_x="middle",
                            wall_lines_y="none", wall_bays_y="none"))
        self.assertEqual([(r["pier"], r["line"], r["bays"]) for r in p.runs], [("T1_PX1", 0, [1]), ("T2_PX1", 0, [4])])

    def test_voids_and_shapes_apply_to_every_tower(self):
        p = build_plan(spec(bays=6, travei=3, towers="0,0,3,3,2;3,0,3,3,2", void_cells="1,1"))
        self.assertEqual(p.voids, {(1, 1), (4, 1)})


if __name__ == "__main__":
    unittest.main()
