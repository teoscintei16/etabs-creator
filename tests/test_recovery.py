import unittest

import comtypes

from etabs_creator.connect import GenError
from etabs_creator.server.recovery import build_with_recovery
from etabs_creator.server.state import STATE


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        STATE["builds"] = 0
        self.restarts = 0

    def restart(self):
        self.restarts += 1
        STATE["builds"] = 0

    def test_counts_builds_and_restarts_preventively(self):
        for _ in range(3):
            build_with_recovery(lambda: {}, self.restart, max_builds=3)
        self.assertEqual((self.restarts, STATE["builds"]), (0, 3))
        build_with_recovery(lambda: {}, self.restart, max_builds=3)
        self.assertEqual((self.restarts, STATE["builds"]), (1, 1))

    def test_one_com_error_triggers_a_restart_and_a_retry(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                raise comtypes.COMError(-2147467261, "Invalid pointer", ("x", "ETABS", None, 0, None))
            return {"ok": True}
        self.assertEqual(build_with_recovery(flaky, self.restart), {"ok": True})
        self.assertEqual((len(calls), self.restarts), (2, 1))

    def test_persistent_failure_is_reported_in_romanian(self):
        def broken():
            raise OSError("mort")
        with self.assertRaises(GenError) as cm:
            build_with_recovery(broken, self.restart)
        self.assertIn("nu mai răspunde", str(cm.exception))
        self.assertEqual(self.restarts, 1)

    def test_other_errors_pass_through_without_restart(self):
        with self.assertRaises(GenError):
            build_with_recovery(lambda: (_ for _ in ()).throw(GenError("spec invalid")), self.restart)
        self.assertEqual(self.restarts, 0)


if __name__ == "__main__":
    unittest.main()
