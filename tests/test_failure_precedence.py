import sys
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from fixtures import NOW,request,setup


class FailurePrecedenceTests(unittest.TestCase):
    def test_unknown_grant_precedes_field_details(self):
        _,engine,grant=setup(); self.assertEqual("unknown grant",engine.evaluate(grant,request(grant_id="other",purpose="marketing"),NOW).reason)
    def test_expiry_precedes_scope_mismatch(self):
        _,engine,grant=setup(); self.assertEqual("grant expired",engine.evaluate(grant,request(purpose="marketing"),grant.expires_at).reason)
    def test_missing_epoch_precedes_scope_mismatch(self):
        state,engine,grant=setup(); state._current_epoch.clear()
        self.assertEqual("no authoritative policy epoch",engine.evaluate(grant,request(purpose="marketing"),NOW).reason)
    def test_stale_epoch_precedes_scope_mismatch(self):
        state,engine,grant=setup(); state.set_epoch(grant.recipient,grant.policy_epoch+1)
        self.assertEqual("grant policy epoch is stale or revoked",engine.evaluate(grant,request(purpose="marketing"),NOW).reason)
    def test_sender_mismatch_precedes_later_fields(self):
        _,engine,grant=setup(); self.assertEqual("sender mismatch",engine.evaluate(grant,request(authenticated_sender="x",purpose="x"),NOW).reason)
    def test_purpose_mismatch_precedes_nonce(self):
        _,engine,grant=setup(); self.assertEqual("purpose mismatch",engine.evaluate(grant,request(purpose="x",nonce="x"),NOW).reason)
    def test_nonce_mismatch_precedes_effect(self):
        _,engine,grant=setup(); self.assertEqual("nonce mismatch",engine.evaluate(grant,request(nonce="x",effect="x"),NOW).reason)
    def test_denial_does_not_consume_quota(self):
        _,engine,grant=setup(); engine.evaluate(grant,request(purpose="x"),NOW)
        self.assertTrue(engine.evaluate(grant,request(),NOW).allowed)

if __name__=="__main__": unittest.main()
