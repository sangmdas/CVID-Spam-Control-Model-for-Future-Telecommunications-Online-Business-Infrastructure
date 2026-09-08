import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from cvid_ref import CandidateRequest, CommunicationGrant, EnforcementEngine, InMemoryGrantState


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 8, tzinfo=timezone.utc)
        self.state = InMemoryGrantState(); self.state.set_epoch("user:U", 7)
        self.engine = EnforcementEngine(self.state)
        self.grant = CommunicationGrant("g-1", "business:B", "user:U", "enquiry:42", "voice", "sbc:west", self.now + timedelta(minutes=5), 7, 1)

    def request(self, **change):
        fields = dict(transaction_id="sip-call-1", authenticated_sender="business:B", recipient="user:U", purpose="enquiry:42", channel="voice", audience="sbc:west", grant_id="g-1")
        fields.update(change); return CandidateRequest(**fields)

    def test_allow_then_sip_retransmission_is_idempotent(self):
        self.assertTrue(self.engine.evaluate(self.grant, self.request(), self.now).allowed)
        d = self.engine.evaluate(self.grant, self.request(), self.now)
        self.assertTrue(d.allowed); self.assertTrue(d.idempotent)

    def test_new_logical_act_is_replay_denied(self):
        self.engine.evaluate(self.grant, self.request(), self.now)
        self.assertFalse(self.engine.evaluate(self.grant, self.request(transaction_id="sip-call-2"), self.now).allowed)

    def test_copied_handle_does_not_authorize_another_sender(self):
        self.assertEqual("sender mismatch", self.engine.evaluate(self.grant, self.request(authenticated_sender="attacker:X"), self.now).reason)

    def test_purpose_channel_expiry_and_epoch_deny(self):
        self.assertFalse(self.engine.evaluate(self.grant, self.request(purpose="marketing"), self.now).allowed)
        self.assertFalse(self.engine.evaluate(self.grant, self.request(channel="message"), self.now).allowed)
        self.assertFalse(self.engine.evaluate(self.grant, self.request(), self.now + timedelta(minutes=6)).allowed)
        self.state.set_epoch("user:U", 8)
        self.assertFalse(self.engine.evaluate(self.grant, self.request(), self.now).allowed)

if __name__ == "__main__": unittest.main()
