import sys
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from fixtures import NOW, request, setup


class FieldBindingTests(unittest.TestCase):
    def test_unknown_grant_is_denied(self):
        _, engine, _ = setup(); self.assertEqual("unknown grant", engine.evaluate(None, request(), NOW).reason)

    def test_wrong_grant_identifier_is_denied(self):
        _, engine, grant = setup(); self.assertEqual("unknown grant", engine.evaluate(grant, request(grant_id="g-copy"), NOW).reason)

    def test_wrong_authenticated_sender_is_denied(self):
        _, engine, grant = setup(); self.assertEqual("sender mismatch", engine.evaluate(grant, request(authenticated_sender="attacker:X"), NOW).reason)

    def test_wrong_recipient_is_denied(self):
        _, engine, grant = setup(); self.assertEqual("recipient mismatch", engine.evaluate(grant, request(recipient="user:other"), NOW).reason)

    def test_wrong_purpose_is_denied(self):
        _, engine, grant = setup(); self.assertEqual("purpose mismatch", engine.evaluate(grant, request(purpose="marketing"), NOW).reason)

    def test_wrong_channel_is_denied(self):
        _, engine, grant = setup(); self.assertEqual("channel mismatch", engine.evaluate(grant, request(channel="message"), NOW).reason)

    def test_wrong_audience_is_denied(self):
        _, engine, grant = setup(); self.assertEqual("audience mismatch", engine.evaluate(grant, request(audience="sbc:east"), NOW).reason)

    def test_bindings_are_case_sensitive(self):
        _, engine, grant = setup(); self.assertFalse(engine.evaluate(grant, request(purpose="Enquiry:42"), NOW).allowed)

    def test_valid_request_just_before_expiry_is_allowed(self):
        _, engine, grant = setup(); self.assertTrue(engine.evaluate(grant, request(), grant.expires_at - timedelta(microseconds=1)).allowed)

    def test_request_at_exact_expiry_is_denied(self):
        _, engine, grant = setup(); self.assertEqual("grant expired", engine.evaluate(grant, request(), grant.expires_at).reason)

    def test_request_after_expiry_is_denied(self):
        _, engine, grant = setup(); self.assertFalse(engine.evaluate(grant, request(), grant.expires_at + timedelta(seconds=1)).allowed)

    def test_missing_authoritative_epoch_fails_closed(self):
        state, engine, grant = setup(); state._current_epoch.clear()
        self.assertEqual("no authoritative policy epoch", engine.evaluate(grant, request(), NOW).reason)

    def test_higher_current_epoch_revokes_old_grant(self):
        state, engine, grant = setup(); state.set_epoch("user:U", 8)
        self.assertEqual("grant policy epoch is stale or revoked", engine.evaluate(grant, request(), NOW).reason)

    def test_lower_current_epoch_also_rejects_mismatch(self):
        state, engine, grant = setup(); state.set_epoch("user:U", 6)
        self.assertFalse(engine.evaluate(grant, request(), NOW).allowed)

    def test_naive_evaluation_time_is_rejected(self):
        _, engine, grant = setup()
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            engine.evaluate(grant, request(), NOW.replace(tzinfo=None))


if __name__ == "__main__": unittest.main()
