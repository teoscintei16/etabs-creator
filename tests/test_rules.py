import tempfile
import unittest
from pathlib import Path

from etabs_creator.connect import GenError
from etabs_creator.seismic import SeismicParams, sd
from tests.fakes import build


class RulesTests(unittest.TestCase):
    def build(self, **kw):
        return build(stories=3, bays=2, travei=2, **kw)

    def test_cracking_modifiers_reduce_I_and_J(self):
        sap, _ = self.build()
        mods = {a[0]: a[1] for a in sap.calls("PropFrame.SetModifiers")}
        self.assertEqual(mods["C50x50"], [1.0, 1.0, 1.0, 0.1, 0.7, 0.7, 1.0, 1.0])
        self.assertEqual(mods["B30x60"], [1.0, 1.0, 1.0, 0.1, 0.5, 0.5, 1.0, 1.0])
        self.assertEqual(sap.calls("PropArea.SetModifiers")[0][1][3:6], [0.5, 0.5, 0.5])

    def test_rigid_zones_on_every_frame_via_table(self):
        sap, res = self.build(rigid_zone=0.6)
        rows = sap.DatabaseTables.t["Frame Assignments - End Length Offsets"][1]
        self.assertEqual(len(rows), res["objects"]["stalpi"] + res["objects"]["grinzi"])
        self.assertTrue(all(r["RigidFact"] == "0.6" and r["OffsetOpt"] == "Auto" for r in rows))
        self.assertEqual(sap.calls("FrameObj.SetEndLengthOffset"), [])                       # API-ul ignora RZ la offset automat

    def test_mesh_and_mass_source_tables(self):
        sap, _ = self.build(walls=True)
        t = sap.DatabaseTables.t
        fl = t["Analysis Options - Automatic Mesh Settings for Floors"][1][0]
        self.assertEqual((fl["MeshOpt"], fl["Localized"], fl["MergeJoints"], fl["MaxMeshSize"]), ("Rectangular", "Yes", "Yes", "0.5"))
        self.assertEqual(t["Analysis Options - Automatic Rectangular Mesh Options for Walls"][1][0]["MaxMeshSize"], "0.5")
        floor = t["Area Assignments - Floor Auto Mesh Options"][1][0]
        wall = t["Area Assignments - Wall Auto Mesh Options"][1][0]
        self.assertEqual((floor["MeshOption"], floor["Restraints"]), ("Default", "Yes"))
        self.assertEqual((wall["MeshOption"], wall["Restraints"]), ("Auto Rectangular", "Yes"))      # „Default” lasa peretele nemeshat
        ms = t["Mass Source Definition"][1]
        self.assertEqual([(r["LoadPattern"], r["Multiplier"]) for r in ms], [("Permanenta", "1"), ("Live", "0.3")])
        self.assertEqual((ms[0]["SourceSelf"], ms[0]["SourceLoads"]), ("Yes", "Yes"))

    def test_modes_spectrum_cases_patterns_and_combos(self):
        sap, res = self.build()
        self.assertEqual(sap.calls("ModalEigen.SetNumberModes")[0], ("Modal", 9, 1))
        fn = [r for r in sap.DatabaseTables.t["Functions - Response Spectrum - User Defined"][1] if r["Name"] == "SPECTRU_P100"]
        self.assertEqual(float(fn[0]["Value"]), round(0.2 * 9.81, 5))
        self.assertEqual(fn[0]["DampRatio"], "0.05")
        loads = sap.calls("RS.SetLoads")
        self.assertEqual([(a[0], a[2], a[4]) for a in loads], [("SPECX", ["U1", "U2"], [1.0, 0.3]), ("SPECY", ["U2", "U1"], [1.0, 0.3])])
        self.assertEqual([a[1] for a in sap.calls("RS.SetEccentricity")], [0.05, 0.05])
        uc = sap.DatabaseTables.t["Load Pattern Definitions - Auto Seismic - User Coefficient"][1]
        self.assertEqual([r["Name"] for r in uc], ["EXP", "EXN", "EYP", "EYN"])
        self.assertEqual((uc[1]["XDirMinusE"], uc[1]["XDirPlusE"], uc[3]["YDirMinusE"]), ("Yes", "No", "Yes"))
        self.assertEqual((uc[0]["TopStory"], uc[0]["BotStory"], uc[0]["EccRatio"]), ("Story3", "Base", "0.05"))
        self.assertEqual(len(sap.calls("RespCombo.Add")), 47)
        self.assertEqual((res["project"]["ag"], res["project"]["lambda_mfse"]), (0.2, 0.85))

    def test_modes_count_only_stories_above_ground(self):
        sap, _ = build(stories=4, bays=2, travei=2, basement=2)
        self.assertEqual(sap.calls("ModalEigen.SetNumberModes")[0], ("Modal", 12, 1))           # 3 × 4 etaje peste teren, subsolul nu vibreaza
        sap, _ = build(stories=6, bays=4, travei=3, towers="0,0,2,3,3;2,0,2,3,5", modes_per_story=2)
        self.assertEqual(sap.calls("ModalEigen.SetNumberModes")[0], ("Modal", 10, 1))           # turnul cel mai inalt (5 etaje)

    def test_gravity_only_model(self):
        sap, res = self.build(seismic=False)
        self.assertEqual(len(sap.calls("RespCombo.Add")), 3)
        self.assertEqual(res["project"], {})
        self.assertEqual(sap.calls("RS.SetCase"), [])


class CalibrationTests(unittest.TestCase):
    def test_static_coefficient_follows_each_directions_t1(self):
        with tempfile.TemporaryDirectory() as d:
            sap, res = build(stories=3, bays=2, travei=2, out_path=Path(d) / "m.EDB", calibrate_static=True)
        uc = {r["Name"]: float(r["C"]) for r in sap.DatabaseTables.t["Load Pattern Definitions - Auto Seismic - User Coefficient"][1]}
        p = SeismicParams()
        self.assertEqual(sap.calls("Analyze.RunAnalysis"), [()])
        self.assertAlmostEqual(uc["EXP"], round(0.85 * sd(0.5, p) / 9.81, 5), 5)              # X: modul dominant 0.5 s (platou)
        self.assertAlmostEqual(uc["EYN"], round(0.85 * sd(0.9, p) / 9.81, 5), 5)              # Y: modul dominant 0.9 s (> TC): C mai mic
        self.assertLess(uc["EYN"], uc["EXP"])
        self.assertTrue(any("forțe statice calibrate" in n for n in res["notes"]))
        self.assertEqual(len(sap.calls("File.Save")), 2)                                         # salvat inainte si dupa calibrare

    def test_can_be_disabled_and_needs_a_saved_file(self):
        with tempfile.TemporaryDirectory() as d:
            sap, _ = build(stories=3, bays=2, travei=2, out_path=Path(d) / "m.EDB")
        self.assertEqual(sap.calls("Analyze.RunAnalysis"), [])
        sap, _ = build(stories=3, bays=2, travei=2, calibrate_static=True)                       # fara cale de iesire nu se calibreaza
        self.assertEqual(sap.calls("Analyze.RunAnalysis"), [])

    def test_stale_write_on_a_locked_model_is_detected(self):
        from etabs_creator.rules.calibrate import calibrate_static
        from etabs_creator.spec import ModelSpec
        from tests.fakes import FakeSap
        sap = FakeSap()
        sap.SetModelIsLocked = lambda v: 0                      # ETABS nu deblocheaza: scrierea tabelului ar fi ignorata
        sap.DatabaseTables.ApplyEditedTables = lambda *a: (sap.DatabaseTables.pending.clear(), [0, 0, 0, 0, "", 0])[1]
        sap.s["calls"].append(("Analyze.RunAnalysis", ()))
        sap.DatabaseTables.t["Load Pattern Definitions - Auto Seismic - User Coefficient"] = (
            ["Name", "C"], [dict(Name=n, C="0.1") for n in ("EXP", "EXN", "EYP", "EYN")])
        with self.assertRaises(GenError):
            calibrate_static(sap, ModelSpec.from_flat({}))


if __name__ == "__main__":
    unittest.main()
