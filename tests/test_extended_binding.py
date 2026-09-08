import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from fixtures import NOW, request, setup


class ExtendedBindingTests(unittest.TestCase):
    def decide(self, **changes):
        _, engine, grant = setup(); return engine.evaluate(grant, request(**changes), NOW)
    def test_nonce_mismatch_is_denied(self): self.assertEqual("nonce mismatch", self.decide(nonce="nonce:other").reason)
    def test_handle_mismatch_is_denied(self): self.assertEqual("handle mismatch", self.decide(handle_id="handle:copied").reason)
    def test_direction_mismatch_is_denied(self): self.assertEqual("direction mismatch", self.decide(direction="outbound").reason)
    def test_effect_mismatch_is_denied(self): self.assertEqual("effect mismatch", self.decide(effect="unlimited-contact").reason)

if __name__ == "__main__": unittest.main()
