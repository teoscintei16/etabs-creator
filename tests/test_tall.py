import math
import unittest

from etabs_creator.connect import GenError
from etabs_creator.spec import ModelSpec
from etabs_creator.tall.geometry import TowerGeom
from etabs_creator.tall.levels import build_levels, typical_height
from etabs_creator.tall.occupancy import check_sets, parse_occupancy, set_of
from etabs_creator.tall.setbacks import bays_at, setback_levels
from etabs_creator.tall.storyplan import story_plan
from etabs_creator.tall.wind import pressure, story_force
from etabs_creator.tall.zones import parse_zones, zone_of
from tests.fakes import build

BURJ = dict(name="burj", structure="turn_inalt", tall=True, basement=2, basement_height=4.5, diaphragm="rigid", modal_type="ritz", modes_total=120, mesh_max=3.0)
SMALL = dict(name="mini", structure="turn_inalt", tall=True, basement=1, basement_height=4.0, tall_levels=12, tall_spire_levels=2, tall_top_concrete=48.0,
             tall_top=60.0, lobby_height=6.0, mech_levels="6,12", mech_height=4.0, setback_start=3, setback_every=2, wing_bays=3,
             zones="1-6:C60/75:0.8:1.0:0.3;7-12:C50/60:0.5:0.8:0.25", occupancy="1-2:MALL;3-5:HOTEL;7-11:BIROU", diaphragm="rigid", modal_type="ritz", modes_total=30, tall_stage_every=4)


def area(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2


class LevelsTests(unittest.TestCase):
    def test_default_tower_levels_heights_and_names(self):
        s = ModelSpec.from_flat(BURJ)
        lv = build_levels(s)
        self.assertEqual((len(lv), lv[0].name, lv[2].name, lv[-1].name), (165, "S2", "P", "E162"))
        self.assertAlmostEqual(lv[-1].z_top, 828.0)
        concrete_top = [x for x in lv if x.number == 156][0].z_top
        self.assertAlmostEqual(concrete_top, 601.0, 2)
        self.assertEqual([x.name for x in lv if x.kind == "mech"], ["E16", "E39", "E72", "E108", "E135", "E155"])
        self.assertAlmostEqual(typical_height(s), 3.74, 2)
        self.assertEqual(lv[2].z_top - lv[2].z_bot, 8.0)                                # lobby

    def test_all_level_elevations_are_on_the_millimetre_grid(self):
        for lv in build_levels(ModelSpec.from_flat(BURJ)):
            self.assertAlmostEqual(lv.z_bot, round(lv.z_bot, 3), 9)
            self.assertAlmostEqual(lv.z_top, round(lv.z_top, 3), 9)

    def test_unreachable_heights_are_rejected(self):
        with self.assertRaises(GenError):
            typical_height(ModelSpec.from_flat({**BURJ, "tall_top_concrete": 100.0}))


class ZonesAndOccupancyTests(unittest.TestCase):
    def test_zones_cover_all_levels_and_grades_are_known(self):
        s = ModelSpec.from_flat(BURJ)
        z = parse_zones(s)
        self.assertEqual((len(z), z[0].grade, zone_of(z, 41).grade, zone_of(z, 156).wall_t), (5, "C80/95", "C70/85", 0.5))
        with self.assertRaises(GenError):
            parse_zones(ModelSpec.from_flat({**BURJ, "zones": "1-100:C80/95:1:1:0.3"}))
        with self.assertRaises(GenError):
            parse_zones(ModelSpec.from_flat({**BURJ, "zones": "1-156:C99/99:1:1:0.3"}))

    def test_every_level_has_a_defined_load_set(self):
        s = ModelSpec.from_flat(BURJ)
        lv = build_levels(s)
        sets = check_sets(s, lv)
        occ = parse_occupancy(s.occupancy)
        self.assertEqual(set_of(lv[0], occ), "PARCARE")
        self.assertEqual(set_of([x for x in lv if x.number == 17][0], occ), "TEHNIC")
        self.assertEqual(set_of([x for x in lv if x.number == 124][0], occ), "OBSERV")
        self.assertEqual(sets["MALL"], (2.5, 5.0))
        with self.assertRaises(GenError):
            check_sets(ModelSpec.from_flat({**BURJ, "occupancy": "1-3:MALL"}), lv)


class SetbackTests(unittest.TestCase):
    def test_spiral_removes_one_bay_per_step_cyclically_until_the_hub(self):
        s = ModelSpec.from_flat(BURJ)
        self.assertEqual(bays_at(s, 25), (7, 7, 7))
        self.assertEqual(bays_at(s, 26), (6, 7, 7))
        self.assertEqual(bays_at(s, 32), (6, 6, 7))
        self.assertEqual(bays_at(s, 38), (6, 6, 6))
        self.assertEqual(bays_at(s, 156), (0, 0, 0))
        changes = setback_levels(s, 156)
        self.assertEqual(len(changes), 1 + 21)                                       # starea initiala + 21 retrageri
        self.assertTrue(all(sum(b2) < sum(b1) for (_, b1), (_, b2) in zip(changes, changes[1:])))

    def test_bays_never_grow_with_height(self):
        s = ModelSpec.from_flat(BURJ)
        seq = [bays_at(s, n) for n in range(1, 157)]
        self.assertTrue(all(all(b <= a for a, b in zip(x, y)) for x, y in zip(seq, seq[1:])))


class PlanTests(unittest.TestCase):
    g = TowerGeom(6.0, 12.0, 1.8, 4.5)

    def test_slabs_plus_core_fill_the_outline_exactly(self):
        hexa = area([self.g.hex_vertex(i) for i in range(6)])
        for bays in ((7, 7, 7), (3, 5, 0), (0, 0, 0)):
            sp = story_plan(self.g, bays)
            outline = [e[0] for e in sp.outline]
            self.assertTrue(all(sp.outline[i][1] == sp.outline[(i + 1) % len(sp.outline)][0] for i in range(len(sp.outline))))     # contur inchis
            self.assertAlmostEqual(sum(area(list(s)) for s in sp.slabs) + hexa, area(outline), 3)
            self.assertTrue(all(area(list(s)) > 0 for s in sp.slabs))                                                            # toate antiorare

    def test_full_plan_counts_and_notch_columns_are_shared(self):
        sp = story_plan(self.g, (7, 7, 7))
        self.assertEqual((len(sp.columns), len(sp.slabs)), (3 * 16 - 3, 3 * (7 * 3 + 3)))
        w, h = sp.extents()
        self.assertTrue(60 < w < 80 and 70 < h < 85)                                  # ca la turnul real (~70 m)

    def test_walls_stay_inside_the_outline_and_corridor_walls_reach_the_tip(self):
        sp = story_plan(self.g, (7, 7, 7))
        tip = self.g.glob(0, self.g.station(7), 1.8)
        self.assertIn(tip, {w.b for w in sp.walls if w.pier == "SP0L"})
        self.assertEqual({w.pier for w in sp.walls if w.pier.startswith("CORE")}, {"CORE0L", "CORE0R", "CORE2L", "CORE2R", "CORE4L", "CORE4R", "CORE1", "CORE3", "CORE5"})


class WindTests(unittest.TestCase):
    def test_pressure_grows_with_height_and_force_scales_with_width(self):
        self.assertAlmostEqual(pressure(10, 0.8, 0.16), 0.8)
        self.assertGreater(pressure(600, 0.8, 0.16), 2.9)
        self.assertAlmostEqual(story_force(100, 4, 50, 0.8, 0.16, 1.2) / story_force(100, 4, 25, 0.8, 0.16, 1.2), 2.0)


class TallBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sap, cls.res = build(**SMALL)

    def test_levels_zones_sections_and_steel_spire(self):
        base, names, heights = self.sap.s["stories"]
        self.assertEqual((names[0], names[1], names[-1], len(names)), ("S1", "P", "E13", 1 + 14))
        self.assertEqual(base, -4.0)
        self.assertAlmostEqual(sum(heights[1:13]), 48.0, 2)
        pipes = [a[0] for a in self.sap.calls("PropFrame.SetPipe")]
        self.assertEqual(len([p for p in pipes if p.startswith("SPIRE")]), 2)
        self.assertEqual({a[0] for a in self.sap.calls("PropMaterial.SetMaterial")}, {"C60/75", "C50/60", "S355"})

    def test_walls_have_pier_labels_and_every_story_has_objects(self):
        piers = {a[0] for a in self.sap.calls("PierLabel.SetPier")}
        self.assertTrue({"SP0L", "SP2R", "CORE1", "CORE4L"} <= piers)
        for k in ("stalpi", "grinzi", "placi", "pereti", "pereti_subsol", "centuri", "spite", "catarg"):
            self.assertGreater(self.res["objects"][k], 0, k)
        self.assertEqual(self.res["objects"]["catarg"], 2)

    def test_load_sets_are_defined_and_assigned_to_every_slab(self):
        t = self.sap.DatabaseTables.t
        sets = t["Shell Uniform Load Sets"][1]
        self.assertIn(("MALL", "Live", "5"), {(r["Name"], r["LoadPattern"], r["LoadValue"]) for r in sets})
        assigned = t["Area Load Assignments - Uniform Load Sets"][1]
        self.assertEqual(len(assigned), self.res["objects"]["placi"])
        self.assertEqual({r["LoadSet"] for r in assigned}, {"PARCARE", "MALL", "HOTEL", "TEHNIC", "BIROU"})

    def test_facade_loads_wind_forces_and_combinations(self):
        self.assertGreater(len(self.sap.calls("FrameObj.SetLoadDistributed")), 0)
        forces = self.sap.calls("PointObj.SetLoadForce")
        self.assertEqual({a[1] for a in forces}, {"Vant_X", "Vant_Y"})
        self.assertEqual(self.res["objects"]["forte_vant"], 2 * (12 + 2))                         # pe fiecare nivel peste teren (inclusiv spire)
        combos = {a[0] for a in self.sap.calls("RespCombo.Add")}
        self.assertTrue({"ULS_Vant_X", "ULS_Vant_X_neg", "ULS_Vant_Y_fav_neg", "SLS_Vant_Y"} <= combos)

    def test_ritz_with_total_modes_and_verifier_params(self):
        self.assertEqual(self.sap.calls("Ritz.SetNumberModes")[0], ("Modal", 30, 1))
        self.assertEqual(self.res["params"]["r10_moduri.moduri_per_etaj"], math.floor(30 / 14 * 100) / 100)
        self.assertEqual(self.res["params"]["r5_mesh.mesh_max"], 0.5)

    def test_staged_construction_groups_stages_and_combinations(self):
        t = self.sap.DatabaseTables.t["Group Assignments"][1]
        groups = {r["GroupName"] for r in t}
        self.assertEqual(groups, {"ETAPA01", "ETAPA02", "ETAPA03", "ETAPA04"})
        self.assertEqual({r["ObjectType"] for r in t}, {"Line", "Area"})
        stage_calls = self.sap.calls("Staged.SetStageData_2")
        self.assertEqual([a[1] for a in stage_calls], [1, 2, 3, 4])
        self.assertEqual(stage_calls[0][3], [1, 3, 3])                                    # Add Structure + Load Objects if Added × 2 tipare
        self.assertEqual(stage_calls[0][8], ["", "Dead", "Permanenta"])
        self.assertEqual(self.sap.calls("Staged.SetCase"), [("CONSTR",)])
        self.assertTrue({"ULS_CONSTR", "SLS_CONSTR"} <= {a[0] for a in self.sap.calls("RespCombo.Add")})
        self.assertEqual(len(t), sum(self.res["objects"][k] for k in ("stalpi", "grinzi", "placi", "pereti", "pereti_subsol", "centuri", "spite", "catarg")))

    def test_the_masts_transfer_support_is_a_documented_expected_finding(self):
        keys = [k for k, _note in self.res["waivers"]]
        self.assertEqual(len(keys), 1)
        self.assertTrue(keys[0].startswith("r2_continuitate_verticala|frame:"))

    def test_cracking_modifiers_cover_every_zone_section(self):
        mods = {a[0] for a in self.sap.calls("PropFrame.SetModifiers")} | {a[0] for a in self.sap.calls("PropArea.SetModifiers")}
        self.assertTrue({"TC100_C60", "TC80_C50", "TW80_C60", "TW50_C50", "TP30_C60", "TP25_C50"} <= mods)


if __name__ == "__main__":
    unittest.main()
