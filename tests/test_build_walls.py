import unittest

from etabs_creator.connect import GenError
from tests.fakes import build

DEFAULT_WALLS = dict(stories=2, bays=3, travei=3, walls=True)


class WallModelTests(unittest.TestCase):
    def test_counts_default_layout(self):
        sap, res = build(**DEFAULT_WALLS)
        o = res["objects"]
        self.assertEqual(o["pereti"], 4 * 1 * 2)                        # 4 pereti (2 pe X, 2 pe Y) x 1 deschidere x 2 etaje
        self.assertEqual(o["centuri"], 8)
        self.assertEqual(o["stalpi"], (16 - 8) * 2)                     # nodurile de capat ale peretilor n-au stalp
        self.assertEqual(o["grinzi"], (24 - 4) * 2)                     # grinzile de sub pereti lipsesc
        self.assertEqual(res["piers"], ["PX1", "PX2", "PY1", "PY2"])
        self.assertEqual(res["belts"], {"has": True, "sections": ["CENTURA"]})
        self.assertEqual(res["project"]["tip_cladire"], "rezidential_pereti")

    def test_wall_geometry_and_piers(self):
        sap, _ = build(**DEFAULT_WALLS)
        walls = [a for a in sap.calls("AreaObj.AddByCoord") if a[5] == "W25"]
        self.assertEqual(len(walls), 8)
        self.assertEqual((walls[0][1], walls[0][2], walls[0][3]), ([5.0, 10.0, 10.0, 5.0], [0.0] * 4, [0.0, 0.0, 3.0, 3.0]))
        self.assertEqual([a[1] for a in sap.calls("AreaObj.SetPier")], ["PX1", "PX2", "PY1", "PY2"] * 2)      # aceeasi eticheta la toate etajele
        self.assertEqual(len(sap.calls("PierLabel.SetPier")), 4)

    def test_base_restraints_include_wall_corners(self):
        sap, _ = build(**DEFAULT_WALLS)
        self.assertEqual(len({a[0] for a in sap.calls("PointObj.SetRestraint")}), 8 + 4 * 2)                   # 8 stalpi + 4 pereti x 2 colturi

    def test_wall_and_belt_sections_and_modifiers(self):
        sap, _ = build(**DEFAULT_WALLS, wall_t=0.3)
        self.assertEqual(sap.calls("PropArea.SetWall")[0], ("W30", 0, 1, "C25/30", 0.3))
        self.assertEqual({a[0]: a[1] for a in sap.calls("PropArea.SetModifiers")}["W30"], [0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual({a[0]: a[1] for a in sap.calls("PropFrame.SetModifiers")}["CENTURA"][-2:], [0.0, 0.0])        # fara masa si greutate
        rigid = sap.DatabaseTables.t["Frame Assignments - End Length Offsets"][1]
        self.assertEqual(sum(1 for r in rigid if r["RigidFact"] == "0.75"), 8 * 2 + 20 * 2)
        self.assertEqual(sum(1 for r in rigid if r["RigidFact"] == "0"), 8)                                     # centurile nu primesc zone rigide

    def test_beams_and_belts_top_center(self):
        sap, res = build(**DEFAULT_WALLS)
        ins = sap.DatabaseTables.t["Frame Assignments - Insertion Point"][1]
        self.assertEqual(sum(1 for r in ins if r["CardinalPt"] == "8 (Top Center)"), res["objects"]["grinzi"] + res["objects"]["centuri"])

    def test_walls_without_frame_or_belts(self):
        sap, res = build(**DEFAULT_WALLS, gravity_frame=False, belts=False)
        self.assertEqual((res["objects"]["stalpi"], res["objects"]["grinzi"], res["objects"].get("centuri", 0)), (0, 0, 0))
        self.assertIsNone(res["belts"])

    def test_invalid_layout(self):
        for bad in (dict(wall_bays_x="9"), dict(wall_lines_y="x"), dict(wall_t=0), dict(crack_wall_f=2), dict(core_shape="I", core_cells="0,0,1,2")):
            with self.assertRaises(GenError, msg=str(bad)):
                build(walls=True, **bad)


class CoupledTests(unittest.TestCase):
    KW = dict(walls=True, bays=3, travei=3, stories=2, wall_lines_x="first,last", wall_bays_x="0,2", wall_lines_y="none", wall_bays_y="none",
              coupling_bays_x="middle")

    def test_model(self):
        sap, res = build(**self.KW)
        self.assertEqual(res["objects"]["grinzi_cuplare"], 2 * 2)
        self.assertEqual(res["objects"]["pereti"], 4 * 2)                                         # 2 linii x 2 picioare x 2 etaje
        self.assertEqual(len(sap.calls("FrameObj.SetSpandrel")), 4)
        self.assertEqual(len(sap.calls("SpandrelLabel.SetSpandrel")), 2)                          # eticheta multi-etaj, definita o singura data
        self.assertEqual(sap.calls("PropFrame.SetRectangle")[-1][0], "CB25x90")
        self.assertEqual({a[0]: a[1] for a in sap.calls("PropFrame.SetModifiers")}["CB25x90"][4], 0.5)


class CoreModelTests(unittest.TestCase):
    def test_each_core_shape_builds_its_panels(self):
        expected = {"L": 4, "C": 6, "I": 6, "H": 6, "T": 4}                  # panouri pe etaj intr-un nucleu 2x2 celule, cu 1 etaj
        for shape, n in expected.items():
            sap, res = build(walls=True, bays=4, travei=4, stories=1, wall_lines_x="none", wall_bays_x="none", wall_lines_y="none",
                             wall_bays_y="none", core_shape=shape)
            self.assertEqual(res["objects"]["pereti"], n, shape)
            self.assertEqual(len(sap.calls("PierLabel.SetPier")), len(res["piers"]), shape)

    def test_core_columns_removed_at_wall_nodes(self):
        _, res = build(walls=True, bays=4, travei=4, stories=1, wall_lines_x="none", wall_bays_x="none", wall_lines_y="none", wall_bays_y="none", core_shape="I")
        self.assertEqual(res["objects"]["stalpi"], 25 - 7)                    # I: (1..3, 1), (1..3, 3) si (2, 2) = 7 noduri de capat de perete


if __name__ == "__main__":
    unittest.main()
