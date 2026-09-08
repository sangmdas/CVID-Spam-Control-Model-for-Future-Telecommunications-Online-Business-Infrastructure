import json
import unittest
from pathlib import Path


class ProfileTests(unittest.TestCase):
    ROOT = Path(__file__).parents[1] / "configs"

    def load(self, name):
        return json.loads((self.ROOT / f"{name}.json").read_text())

    def test_blocked_path_discloses_upstream_signaling_limit(self):
        profile = self.load("blocked-path")
        self.assertEqual("blocked-path", profile["profile"]); self.assertIn("upstream signaling", profile["claim_boundary"])

    def test_pre_routing_profile_identifies_alternate_route_limit(self):
        profile = self.load("pre-routing")
        self.assertEqual("pre-routing", profile["profile"]); self.assertIn("Alternate ordinary routes", profile["claim_boundary"])

    def test_absent_path_requires_bypass_closure(self):
        profile = self.load("absent-path")
        self.assertEqual("absent-path", profile["profile"]); self.assertIn("no equivalent alternate route", profile["claim_boundary"])


if __name__ == "__main__": unittest.main()
