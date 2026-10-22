import unittest

from etabs_creator.build.context import SOIL_PATTERN
from etabs_creator.connect import GenError
from tests.fakes import build


class BasementTests(unittest.TestCase):
    def build(self, **kw):
        return build(stories=2, bays=2, travei=2, basement=2, **kw)

    def test_stories_and_base_story(self):
        sap, res = self.build()
        base, names, _h = sap.s["stories"]
        self.assertEqual((base, names), (-6.0, ["S2", "S1", "P", "E1"]))
        self.assertEqual(res["stories"], ["E1", "P", "S1", "S2"])
        uc = sap.DatabaseTables.t["Load Pattern Definitions - Auto Seismic - User Coefficient"][1]
        self.assertEqual({r["BotStory"] for r in uc}, {"S1"})                                      # fortele seismice incep deasupra ±0.00
        self.assertEqual(uc[0]["TopStory"], "E1")

    def test_perimeter_walls_and_interior_columns(self):
        sap, res = self.build()
        o = res["objects"]
        self.assertEqual(o["pereti_subsol"], 8 * 2)                                                # perimetru: 2 deschideri x 4 laturi, 2 niveluri
        self.assertEqual(o["stalpi"], 1 * 2 + 9 * 2)                                               # subsol: doar nodul interior; deasupra: toate 9 noduri
        self.assertEqual(sap.calls("PropArea.SetWall")[0][0], "WB30")
        self.assertEqual(o["centuri"], 16)                                                         # centura dummy deasupra fiecarui panou de subsol

    def test_soil_pressure_is_inward_on_every_side(self):
        sap, _ = self.build(soil_pressure=20.0)
        loads = [a for a in sap.calls("AreaObj.SetLoadUniform") if a[1] == SOIL_PATTERN]
        self.assertEqual(len(loads), 16)
        self.assertEqual({a[2] for a in loads}, {-20.0, 20.0})
        self.assertTrue(all(a[3] == 3 and a[5] == "Local" for a in loads))

    def test_combinations_include_pressure_only_in_uls_and_sls(self):
        sap, _ = self.build()
        self.assertEqual({a[0] for a in sap.calls("RespCombo.SetCaseList") if a[2] == SOIL_PATTERN}, {"ULS", "SLS_CAR", "SLS_QP"})

    def test_project_params_declare_basement(self):
        _, res = self.build()
        p = res["project"]
        self.assertEqual((p["basement"], p["basement_stories"], p["ground_story"]), ("da", ["S1", "S2"], "P"))

    def test_modes_ignore_the_basement(self):
        sap, _ = self.build()
        self.assertEqual(sap.calls("ModalEigen.SetNumberModes")[0], ("Modal", 6, 1))


class TowerWallsContinueBelowTests(unittest.TestCase):
    def test_tower_walls_run_through_the_basement_with_the_same_piers(self):
        sap, res = build(bays=4, travei=3, stories=2, towers="1,0,2,3,2", basement=1, walls=True, wall_lines_x="first,last", wall_bays_x="middle",
                         wall_lines_y="none", wall_bays_y="none")
        self.assertEqual(res["objects"]["pereti"], 2 * (2 + 1))                                    # 2 pereti x (2 etaje + 1 subsol)
        piers = [a[1] for a in sap.calls("AreaObj.SetPier")]
        self.assertEqual(sorted(piers), ["PX1"] * 3 + ["PX2"] * 3)


    def test_defect_switch_leaves_tower_walls_on_the_ground_slab(self):
        sap, res = build(bays=4, travei=3, stories=2, towers="1,0,2,3,2", basement=1, walls=True, wall_lines_x="first,last", wall_bays_x="middle",
                         wall_lines_y="none", wall_bays_y="none", walls_through_basement=False)
        self.assertEqual(res["objects"]["pereti"], 2 * 2)                                          # doar peste teren: reazema pe placa subsolului

    def test_no_duplicate_panel_where_a_tower_wall_meets_the_perimeter(self):
        sap, res = build(bays=3, travei=3, stories=1, basement=1, walls=True, wall_lines_x="first,last", wall_bays_x="middle", wall_lines_y="none", wall_bays_y="none")
        self.assertEqual(res["objects"]["pereti_subsol"], 12 - 2)                                  # 12 panouri de perimetru, 2 ocupate de peretii turnului
        coords = [(tuple(a[1]), tuple(a[2]), tuple(a[3])) for a in sap.calls("AreaObj.AddByCoord") if a[5] in ("W25", "WB30")]
        self.assertEqual(len(coords), len(set(coords)))                                            # niciun panou dublat


class LargerBasementTests(unittest.TestCase):
    """Subsol sub un plan mai mare decat turnul."""
    KW = dict(bays=5, travei=3, towers="1,0,3,3,4", basement=2, calibrate_static=False)

    def test_basement_covers_the_full_grid_tower_only_its_rectangle(self):
        sap, res = build(**self.KW)
        slabs = sap.calls("AreaObj.AddByCoord")
        self.assertEqual(res["objects"]["placi"], 2 * 15 + 4 * 9)                                  # 2 subsoluri pe 15 celule + 4 etaje pe 9
        self.assertEqual(res["objects"]["pereti_subsol"], (5 * 2 + 3 * 2) * 2)                      # perimetrul grilei complete
        self.assertEqual(res["stories"], ["E3", "E2", "E1", "P", "S1", "S2"])

    def test_tower_columns_start_at_ground_floor_not_below_the_tower(self):
        sap, res = build(**self.KW)
        self.assertEqual(res["objects"]["stalpi"], 2 * ((6 - 2) * (4 - 2)) + 4 * 16)                # subsol: noduri interioare 4x2; turn: 4x4 noduri


class MultiTowerTests(unittest.TestCase):
    KW = dict(bays=7, travei=3, towers="0,0,3,3,3;4,0,3,3,5", calibrate_static=False)

    def test_two_towers_of_different_heights(self):
        sap, res = build(**self.KW)
        self.assertEqual(res["towers"], 2)
        self.assertEqual(res["objects"]["placi"], 9 * 3 + 9 * 5)
        self.assertEqual(len(res["stories"]), 5)

    def test_walls_per_tower_with_prefixed_piers(self):
        sap, res = build(**self.KW, walls=True, wall_lines_x="first,last", wall_bays_x="middle", wall_lines_y="none", wall_bays_y="none")
        self.assertEqual(res["piers"], ["T1_PX1", "T1_PX2", "T2_PX1", "T2_PX2"])
        t1 = sum(1 for a in sap.calls("AreaObj.SetPier") if a[1].startswith("T1_"))
        t2 = sum(1 for a in sap.calls("AreaObj.SetPier") if a[1].startswith("T2_"))
        self.assertEqual((t1, t2), (2 * 3, 2 * 5))                                                  # panouri = linii x etaje ale fiecarui turn

    def test_towers_must_fit_and_not_overlap(self):
        for bad in ("0,0,9,3,3", "0,0,4,3,3;3,0,4,3,3"):
            with self.assertRaises(GenError):
                build(bays=7, travei=3, towers=bad)


if __name__ == "__main__":
    unittest.main()
