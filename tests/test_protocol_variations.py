import json
import unittest
from pathlib import Path


class ProtocolVariationTests(unittest.TestCase):
    ROOT=Path(__file__).parents[1]/"configs"
    def load(self,name): return json.loads((self.ROOT/f"{name}.json").read_text())
    def test_ten_configuration_variations_are_packaged(self): self.assertEqual(10,len(list(self.ROOT.glob("*.json"))))
    def test_blocked_path_profile_is_present(self): self.assertEqual("blocked-path",self.load("blocked-path")["profile"])
    def test_pre_routing_profile_is_present(self): self.assertEqual("pre-routing",self.load("pre-routing")["profile"])
    def test_absent_path_profile_is_present(self): self.assertEqual("absent-path",self.load("absent-path")["profile"])
    def test_sip_profile_disclaims_standardized_header(self): self.assertIn("No SIP header",self.load("sip-sbc")["claim_limit"])
    def test_stir_profile_separates_identity_from_permission(self): self.assertIn("not recipient-issued permission",self.load("stir-passport-input")["claim_limit"])
    def test_http_cpaas_profile_separates_api_access_from_effect(self): self.assertIn("does not automatically authorize",self.load("http-cpaas")["claim_limit"])
    def test_webrtc_profile_disclaims_new_fields(self): self.assertIn("no new WebRTC",self.load("webrtc-turn")["claim_limit"])
    def test_federation_profile_lists_open_semantics(self): self.assertIn("not standardized",self.load("federated-edge")["claim_limit"])
    def test_attestation_profile_does_not_replace_authority(self): self.assertIn("does not replace",self.load("high-assurance-attested")["claim_limit"])

if __name__=="__main__": unittest.main()
