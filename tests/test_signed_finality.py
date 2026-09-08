import sys
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from cvid_ref import *
from fixtures import NOW, request, setup

KEY=b"reference-authentication-key-at-least-32-bytes"

def finality(max_attempts=1):
    state, core, grant=setup(max_attempts); auth=HMACAuthenticator(KEY)
    envelope=auth.sign_envelope(GrantEnvelope(grant,"issuer:trusted","key:1"))
    engine=FinalityEngine(core,auth,{"issuer:trusted"},"sink:west")
    allocator=FinalityAllocator(auth,"sink:west")
    return auth,envelope,engine,allocator


class SignedFinalityTests(unittest.TestCase):
    def test_valid_signed_grant_produces_release(self):
        _,e,engine,_=finality(); self.assertTrue(engine.evaluate(e,request(),NOW).capability)
    def test_missing_envelope_is_denied(self):
        _,_,engine,_=finality(); self.assertEqual("grant envelope required",engine.evaluate(None,request(),NOW).reason)
    def test_unsigned_envelope_is_denied(self):
        _,e,engine,_=finality(); self.assertEqual("grant integrity invalid",engine.evaluate(replace(e,signature=""),request(),NOW).reason)
    def test_tampered_grant_is_denied(self):
        _,e,engine,_=finality(); forged=replace(e,grant=replace(e.grant,purpose="marketing"))
        self.assertFalse(engine.evaluate(forged,request(purpose="marketing"),NOW).allowed)
    def test_untrusted_issuer_is_denied_before_integrity(self):
        auth,e,engine,_=finality(); e=auth.sign_envelope(replace(e,issuer="issuer:other",signature=""))
        self.assertEqual("untrusted issuer",engine.evaluate(e,request(),NOW).reason)
    def test_wrong_key_is_denied(self):
        _,e,engine,_=finality(); other=HMACAuthenticator(b"different-reference-key-at-least-32-bytes!")
        e=other.sign_envelope(replace(e,signature="")); self.assertFalse(engine.evaluate(e,request(),NOW).allowed)
    def test_short_key_is_rejected(self):
        with self.assertRaises(ValueError): HMACAuthenticator(b"short")
    def test_release_lifetime_is_at_most_five_seconds(self):
        _,e,engine,_=finality(); cap=engine.evaluate(e,request(),NOW).capability
        self.assertLessEqual(cap.expires_at-NOW,timedelta(seconds=5))
    def test_no_release_means_no_effect(self):
        *_,allocator=finality(); self.assertFalse(allocator.allocate(None,"business:B","voice:x",NOW).allowed)
    def test_valid_release_allocates_exact_resource(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability
        self.assertTrue(allocator.allocate(cap,"business:B",cap.resource_id,NOW).allowed)
    def test_unsigned_release_is_denied(self):
        _,e,engine,allocator=finality(); cap=replace(engine.evaluate(e,request(),NOW).capability,signature="")
        self.assertEqual("release integrity invalid",allocator.allocate(cap,"business:B",cap.resource_id,NOW).reason)
    def test_tampered_release_is_denied(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability; cap=replace(cap,resource_id="voice:other")
        self.assertFalse(allocator.allocate(cap,"business:B",cap.resource_id,NOW).allowed)
    def test_release_sender_substitution_is_denied(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability
        self.assertEqual("release sender mismatch",allocator.allocate(cap,"attacker:X",cap.resource_id,NOW).reason)
    def test_release_resource_widening_is_denied(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability
        self.assertEqual("release resource mismatch",allocator.allocate(cap,"business:B","voice:unlimited",NOW).reason)
    def test_release_audience_substitution_is_denied(self):
        auth,e,engine,_=finality(); cap=engine.evaluate(e,request(),NOW).capability; other=FinalityAllocator(auth,"sink:east")
        self.assertEqual("release audience mismatch",other.allocate(cap,"business:B",cap.resource_id,NOW).reason)
    def test_release_at_exact_expiry_is_denied(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability
        self.assertEqual("release capability expired",allocator.allocate(cap,"business:B",cap.resource_id,cap.expires_at).reason)
    def test_release_just_before_expiry_is_allowed(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability
        self.assertTrue(allocator.allocate(cap,"business:B",cap.resource_id,cap.expires_at-timedelta(microseconds=1)).allowed)
    def test_same_release_is_idempotent(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability
        allocator.allocate(cap,"business:B",cap.resource_id,NOW); second=allocator.allocate(cap,"business:B",cap.resource_id,NOW)
        self.assertTrue(second.allowed); self.assertTrue(second.idempotent)
    def test_new_logical_act_after_quota_has_no_release(self):
        _,e,engine,_=finality(); engine.evaluate(e,request(),NOW)
        result=engine.evaluate(e,request(transaction_id="new-act"),NOW); self.assertFalse(result.allowed); self.assertIsNone(result.capability)
    def test_naive_allocator_time_is_rejected(self):
        _,e,engine,allocator=finality(); cap=engine.evaluate(e,request(),NOW).capability
        with self.assertRaises(ValueError): allocator.allocate(cap,"business:B",cap.resource_id,NOW.replace(tzinfo=None))

if __name__ == "__main__": unittest.main()
