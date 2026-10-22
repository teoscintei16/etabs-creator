import unittest

from etabs_creator.connect import GenError
from etabs_creator.plan import build_plan
from etabs_creator.plan.cells import parse_cells
from etabs_creator.plan.stories import stories_of
from etabs_creator.spec import ModelSpec


def spec(**kw):
    return ModelSpec.from_flat({"calibrate_static": False, **kw})


class StoriesTests(unittest.TestCase):
    def test_without_basement_default_names(self):
        st = stories_of(spec(stories=3, bottom_height=4.0), 3)
        self.assertEqual([(s.name, s.z_bot, s.z_top) for s in st], [("Story1", 0.0, 4.0), ("Story2", 4.0, 7.0), ("Story3", 7.0, 10.0)])

    def test_basement_names_and_levels(self):
        st = stories_of(spec(stories=3, basement=2, basement_height=3.2), 3)
        self.assertEqual([s.name for s in st], ["S2", "S1", "P", "E1", "E2"])
        self.assertEqual([(s.z_bot, s.z_top) for s in st][:3], [(-6.4, -3.2), (-3.2, 0.0), (0.0, 3.0)])      # S1 are cota superioara ±0.00
        self.assertEqual([s.basement for s in st], [True, True, False, False, False])


class ShapeTests(unittest.TestCase):
    def test_L_and_setback(self):
        p = build_plan(spec(bays=4, travei=3, stories=4, shape="L", cut_bays=2, cut_travei=1))
        c = p.cells[0]
        self.assertEqual(len(c), 12 - 2)
        self.assertNotIn((3, 2), c)
        p = build_plan(spec(bays=4, travei=3, stories=4, shape="setback", setback_story=2, setback_bays=1))
        self.assertEqual((len(p.cells[1]), len(p.cells[2])), (12, 9))

    def test_basement_is_the_full_plan_even_for_an_L_tower(self):
        p = build_plan(spec(bays=4, travei=3, stories=3, shape="L", cut_bays=2, cut_travei=1, basement=1))
        self.assertEqual((len(p.cells[0]), len(p.cells[1])), (12, 10))

    def test_columns_follow_upper_floors_and_beams_follow_cells(self):
        p = build_plan(spec(bays=3, travei=2, stories=3, shape="setback", setback_story=1, setback_bays=1))
        low, top = p.columns(0), p.columns(2)
        self.assertEqual((len(low), len(top)), (4 * 3, 3 * 3))
        self.assertTrue(all(ix < 3 for ix, _ in top))
        bx, by = p.beams(2)
        self.assertTrue(all(i < 2 for _, i in bx))
        self.assertEqual(len(by), 3 * 2)

    def test_voids_remove_slabs_not_beams(self):
        p = build_plan(spec(bays=3, travei=3, stories=2, void_cells="1,1"))
        self.assertEqual(len(p.slab_cells(0)), 8)
        self.assertEqual(len(p.beams(0)[0]), 4 * 3)

    def test_invalid_shapes_and_voids(self):
        for bad in (dict(shape="L", cut_bays=9), dict(shape="setback", setback_story=9), dict(void_cells="9,9"), dict(void_cells="x"), dict(void_cells="1")):
            with self.assertRaises(GenError, msg=str(bad)):
                spec(stories=3, bays=3, travei=3, **bad).validate()
        self.assertEqual(parse_cells("1,1;2,0", 3, 3), {(1, 1), (2, 0)})


if __name__ == "__main__":
    unittest.main()
