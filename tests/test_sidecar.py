import json
import tempfile
import unittest
from pathlib import Path

from etabs_creator.sidecar import sidecar_path, write_settings


class SidecarTests(unittest.TestCase):
    def test_working_file_maps_to_edb(self):
        self.assertEqual(str(sidecar_path(r"C:\m\model.$et")), r"C:\m\model.EDB.checks.json")

    def test_merges_with_existing_keys(self):
        with tempfile.TemporaryDirectory() as d:
            model = str(Path(d) / "m.EDB")
            Path(model + ".checks.json").write_text(json.dumps({"waivers": [{"key": "x"}], "project": {"q": 9}}), encoding="utf-8")
            path = write_settings(model, {"ag": 0.2, "q": 3.5, "vid": ""}, {"has": True, "sections": ["CENTURA"]})
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual(data["project"], {"q": 3.5, "ag": 0.2})
        self.assertEqual(data["belts"], {"has": True, "sections": ["CENTURA"]})
        self.assertEqual(data["waivers"], [{"key": "x"}])


if __name__ == "__main__":
    unittest.main()
