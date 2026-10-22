import tempfile
import unittest
from pathlib import Path

from etabs_creator.build.sections import section_names
from etabs_creator.connect import GenError
from etabs_creator.spec import ModelSpec
from tests.fakes import FakeSap, build


class FrameModelTests(unittest.TestCase):
    def test_counts_and_geometry(self):
        with tempfile.TemporaryDirectory() as d:
            sap, r = build(stories=2, bays=2, travei=3, story_height=3.0, span_x=5.0, span_y=4.0, out_path=Path(d) / "m.EDB")
        self.assertEqual(r["objects"], {"stalpi": 24, "grinzi": 34, "placi": 12})
        self.assertEqual(r["base_nodes"], 12)
        self.assertEqual(sap.calls("File.NewGridOnly")[0], (2, 3.0, 3.0, 3, 4, 5.0, 4.0))
        cols = [a for a in sap.calls("FrameObj.AddByCoord") if a[2] != a[5]]
        self.assertEqual(len(cols), 24)
        self.assertEqual(sorted({a[5] for a in cols}), [3.0, 6.0])                                # varfurile stalpilor la cotele etajelor
        slabs = sap.calls("AreaObj.AddByCoord")
        self.assertEqual(slabs[0][1:4], ([0.0, 5.0, 5.0, 0.0], [0.0, 0.0, 4.0, 4.0], [3.0] * 4))
        self.assertEqual(len(sap.calls("PointObj.SetRestraint")), 12)
        self.assertEqual(len(sap.calls("AreaObj.SetDiaphragm")), 12)
        self.assertTrue(all(isinstance(a[0], str) for a in sap.calls("AreaObj.SetDiaphragm")))
        self.assertEqual(len(sap.calls("AreaObj.SetLoadUniform")), 24)                           # permanent + utila pe fiecare placa

    def test_sections_and_materials(self):
        sap, _ = build(stories=1, bays=1, travei=1, column_b=0.4, column_h=0.6, beam_b=0.25, beam_h=0.5, concrete="C30/37")
        self.assertEqual(section_names(ModelSpec.from_flat({"column_b": 0.4, "column_h": 0.6}))["column"], "C40x60")
        self.assertEqual(sap.calls("PropFrame.SetRectangle")[0], ("C40x60", "C30/37", 0.6, 0.4))     # T3 = inaltime, T2 = latime
        self.assertEqual(sap.calls("PropMaterial.SetMPIsotropic")[0][1], 33e6)
        self.assertTrue(sap.calls("Diaphragm.SetDiaphragm")[0][1])                                # semirigid implicit

    def test_beams_top_center_columns_untouched(self):
        sap, res = build(stories=2, bays=2, travei=2)
        ins = sap.DatabaseTables.t["Frame Assignments - Insertion Point"][1]
        self.assertEqual(sum(1 for r in ins if r["CardinalPt"] == "8 (Top Center)"), res["objects"]["grinzi"])
        self.assertEqual(sum(1 for r in ins if r["CardinalPt"] == "10 (Centroid)"), res["objects"]["stalpi"])

    def test_invalid_spec_does_not_touch_etabs(self):
        sap = FakeSap()
        from etabs_creator.build import build_model
        with self.assertRaises(GenError):
            build_model(sap, ModelSpec.from_flat({"stories": 0}))
        self.assertEqual(sap.s["calls"], [])

    def test_never_replaces_a_users_model(self):
        from etabs_creator.build import build_model
        with self.assertRaises(GenError):
            build_model(FakeSap(r"C:\Users\x\Documents\modelul_meu.EDB"), ModelSpec.from_flat({"stories": 1, "bays": 1, "travei": 1}))


if __name__ == "__main__":
    unittest.main()
