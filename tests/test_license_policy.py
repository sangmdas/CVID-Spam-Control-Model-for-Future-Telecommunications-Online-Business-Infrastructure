import unittest
from pathlib import Path

class LicensePolicyTests(unittest.TestCase):
    TEXT=(Path(__file__).parents[1]/"LICENSE.md").read_text()
    def test_spdx_identifier(self): self.assertIn("PolyForm-Noncommercial-1.0.0",self.TEXT)
    def test_official_url(self): self.assertIn("https://polyformproject.org/licenses/noncommercial/1.0.0",self.TEXT)
    def test_required_notice(self): self.assertIn("Copyright © 2026 Sangam Kumar Das",self.TEXT)
    def test_commercial_license_is_separate(self): self.assertIn("separate commercial license",self.TEXT)
    def test_ietf_ipr_is_separate(self): self.assertIn("IETF IPR disclosure",self.TEXT)

if __name__=="__main__": unittest.main()
