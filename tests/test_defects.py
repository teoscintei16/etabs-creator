import unittest

from etabs_creator.connect import GenError
from etabs_creator.defects import DEFECTS, parse
from tests.fakes import build

BASE = dict(stories=3, bays=2, travei=2)


class DefectTests(unittest.TestCase):
    def build(self, names, **kw):
        return build(**BASE, defects=names, **kw)

    def test_registry_and_parsing(self):
        self.assertEqual(len(DEFECTS), 12)
        self.assertEqual(parse(" modes_few , dof_off ,"), ["modes_few", "dof_off"])
        with self.assertRaises(GenError):
            parse("nu_exista")
        with self.assertRaises(GenError):
            self.build("nu_exista")

    def test_defects_are_applied_after_the_rules_and_noted(self):
        sap, res = self.build("modes_few")
        modes = sap.calls("ModalEigen.SetNumberModes")
        self.assertEqual([a[1] for a in modes], [9, 4])                                          # intai regula (3/etaj), apoi defectul
        self.assertTrue(any(n.startswith("DEFECT modes_few") for n in res["notes"]))

    def test_no_defects_by_default(self):
        _sap, res = build(**BASE)
        self.assertFalse(any(n.startswith("DEFECT") for n in res["notes"]))

    def test_analysis_and_load_defects(self):
        sap, _ = self.build("ritz_no_accel,dof_off,selfwt_none,selfwt_double,pattern_type_wrong")
        self.assertEqual(sap.calls("Ritz.SetLoads")[0], ("RitzTest", 1, ["Accel"], ["UZ"], [0], [99.0]))
        self.assertEqual(sap.calls("Analyze.SetActiveDOF")[0][0], [True, True, False, True, True, False])
        self.assertEqual([a for a in sap.calls("LoadPatterns.SetSelfWTMultiplier")], [("Dead", 0.0), ("Permanenta", 1.0)])
        added = {a[0]: a[1] for a in sap.calls("LoadPatterns.Add")}
        self.assertEqual((added["zapada"], added["utila_etaj"]), (1, 1))

    def test_element_defects(self):
        sap, res = self.build("no_rigid_zones,slab_no_diaphragm,parasitic_nodes")
        rows = sap.DatabaseTables.t["Frame Assignments - End Length Offsets"][1]
        self.assertTrue(rows and all(r["RigidFact"] == "0" for r in rows))
        none = [a for a in sap.calls("AreaObj.SetDiaphragm") if a[1] == "None"]
        self.assertEqual(len(none), 3)
        pts = {r["UniqueName"]: r["X"] for r in sap.DatabaseTables.t["Point Object Connectivity"][1]}
        self.assertEqual(pts["p1"], "0.00002")                                                    # nodul aproape de 0
        self.assertAlmostEqual(float(pts["p2"]), 5.00003, 7)
        self.assertEqual(pts["p4"], "1.234")                                                      # punctele automate nu se ating

    def test_secondary_beam_ends_in_the_interior_of_two_beams(self):
        sap, _ = self.build("secondary_beams")
        last = sap.calls("FrameObj.AddByCoord")[-1]
        self.assertEqual((last[0], last[1], last[3], last[4]), (2.5, 0.0, 2.5, 5.0))             # la mijlocul primei deschideri, intre doua grinzi

    def test_mesh_defect_and_pier_defect(self):
        sap, _ = self.build("mesh_nonstandard", walls=True)
        t = sap.DatabaseTables.t
        self.assertEqual(t["Analysis Options - Automatic Mesh Settings for Floors"][1][0]["MeshOpt"], "General")
        self.assertEqual({r["Restraints"] for r in t["Area Assignments - Wall Auto Mesh Options"][1]}, {"No"})
        sap, _ = build(bays=7, travei=3, towers="0,0,3,3,2;4,0,3,3,2", walls=True, wall_lines_x="first", wall_bays_x="middle", wall_lines_y="none",
                       wall_bays_y="none", defects="pier_same_labels")
        piers = {a[1] for a in sap.calls("AreaObj.SetPier")}
        self.assertEqual(piers, {"T1_PX1", "T2_PX1", "PX1"})                                      # etichetele cu prefix, apoi cele fara


if __name__ == "__main__":
    unittest.main()
