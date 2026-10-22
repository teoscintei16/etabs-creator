import unittest

from etabs_creator.connect import GenError
from etabs_creator.spec import OWNER, PARTS, ModelSpec


class SpecTests(unittest.TestCase):
    def test_field_names_unique_across_parts(self):
        self.assertEqual(len(OWNER), sum(len(__import__("dataclasses").fields(c)) for c in PARTS.values()))

    def test_flat_roundtrip_and_attribute_access(self):
        s = ModelSpec.from_flat({"name": "x", "stories": 7, "wall_t": 0.3, "basement": 2, "towers": "0,0,2,2,3"})
        self.assertEqual((s.name, s.stories, s.wall_t, s.basement), ("x", 7, 0.3, 2))
        self.assertEqual(s.p_grid.stories, 7)
        flat = s.to_flat()
        self.assertEqual(ModelSpec.from_flat(flat).to_flat(), flat)
        s.stories = 9
        self.assertEqual(s.p_grid.stories, 9)

    def test_unknown_field_rejected(self):
        with self.assertRaises(GenError):
            ModelSpec.from_flat({"stories": 3, "nu_exista": 1})

    def test_each_part_validates_its_own_fields(self):
        bad = [dict(stories=0), dict(bays=0), dict(span_x=-1), dict(concrete="C99"), dict(diaphragm="x"), dict(crack_beam_I=0), dict(crack_slab=1.5),
               dict(mesh_max=0), dict(modes_per_story=0), dict(Tb=1.0, Tc=0.7), dict(q=-1), dict(basement=5), dict(basement=1, basement_height=0),
               dict(shape="x"), dict(live=-1), dict(psi2=2), dict(structure="altceva")]
        for kw in bad:
            with self.assertRaises(GenError, msg=str(kw)):
                ModelSpec.from_flat(kw).validate()

    def test_gravity_only_skips_seismic_validation(self):
        ModelSpec.from_flat({"seismic": False, "q": -5}).validate()

    def test_walls_dependencies(self):
        for kw in (dict(coupling_bays_x="middle"), dict(core_shape="L"), dict(core_shape="Z", walls=True), dict(walls=True, wall_t=0)):
            with self.assertRaises(GenError, msg=str(kw)):
                ModelSpec.from_flat(kw).validate()


if __name__ == "__main__":
    unittest.main()
