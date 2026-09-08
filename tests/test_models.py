import sys
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from cvid_ref import CandidateRequest, CommunicationGrant, InMemoryGrantState
from fixtures import NOW, request, setup


class ModelTests(unittest.TestCase):
    def test_grant_requires_timezone_aware_expiry(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            CommunicationGrant("g", "s", "r", "p", "voice", "a", datetime(2026, 1, 1), 0)

    def test_grant_rejects_zero_attempt_quota(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            CommunicationGrant("g", "s", "r", "p", "voice", "a", NOW + timedelta(seconds=1), 0, 0)

    def test_grant_rejects_negative_epoch(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            CommunicationGrant("g", "s", "r", "p", "voice", "a", NOW + timedelta(seconds=1), -1)

    def test_grant_rejects_every_empty_bound_field(self):
        base = dict(grant_id="g", sender="s", recipient="r", purpose="p", channel="voice", audience="a")
        for field in tuple(base):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "non-empty"):
                CommunicationGrant(**(base | {field: "  "}), expires_at=NOW + timedelta(seconds=1), policy_epoch=0)

    def test_candidate_rejects_every_empty_bound_field(self):
        base = dict(transaction_id="t", authenticated_sender="s", recipient="r", purpose="p", channel="voice", audience="a", grant_id="g")
        for field in tuple(base):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "non-empty"):
                CandidateRequest(**(base | {field: ""}))

    def test_grant_is_immutable_after_construction(self):
        _, _, grant = setup()
        with self.assertRaises(FrozenInstanceError): grant.sender = "attacker"

    def test_candidate_is_immutable_after_construction(self):
        candidate = request()
        with self.assertRaises(FrozenInstanceError): candidate.purpose = "marketing"

    def test_epoch_store_rejects_invalid_values(self):
        state = InMemoryGrantState()
        with self.assertRaises(ValueError): state.set_epoch("", 0)
        with self.assertRaises(ValueError): state.set_epoch("user:U", -1)


if __name__ == "__main__": unittest.main()
