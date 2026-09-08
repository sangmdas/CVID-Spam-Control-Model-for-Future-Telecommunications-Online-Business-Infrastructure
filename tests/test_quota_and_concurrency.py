import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from fixtures import NOW, request, setup


class QuotaAndConcurrencyTests(unittest.TestCase):
    def test_two_attempt_grant_allows_two_distinct_acts(self):
        _, engine, grant = setup(max_attempts=2)
        self.assertTrue(engine.evaluate(grant, request(transaction_id="call-1"), NOW).allowed)
        self.assertTrue(engine.evaluate(grant, request(transaction_id="call-2"), NOW).allowed)

    def test_two_attempt_grant_denies_third_distinct_act(self):
        _, engine, grant = setup(max_attempts=2)
        for i in (1, 2): engine.evaluate(grant, request(transaction_id=f"call-{i}"), NOW)
        self.assertEqual("attempt quota exhausted", engine.evaluate(grant, request(transaction_id="call-3"), NOW).reason)

    def test_retransmission_does_not_consume_second_attempt(self):
        _, engine, grant = setup(max_attempts=2)
        engine.evaluate(grant, request(transaction_id="call-1"), NOW)
        retransmit = engine.evaluate(grant, request(transaction_id="call-1"), NOW)
        second = engine.evaluate(grant, request(transaction_id="call-2"), NOW)
        self.assertTrue(retransmit.idempotent); self.assertTrue(second.allowed)

    def test_concurrent_distinct_acts_cannot_exceed_single_quota(self):
        _, engine, grant = setup(max_attempts=1)
        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(lambda i: engine.evaluate(grant, request(transaction_id=f"call-{i}"), NOW), range(50)))
        self.assertEqual(1, sum(d.allowed for d in results))
        self.assertEqual(49, sum(d.reason == "attempt quota exhausted" for d in results))

    def test_concurrent_retransmissions_are_all_idempotently_accepted(self):
        _, engine, grant = setup(max_attempts=1)
        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(lambda _: engine.evaluate(grant, request(transaction_id="same-call"), NOW), range(50)))
        self.assertTrue(all(d.allowed for d in results))
        self.assertEqual(49, sum(d.idempotent for d in results))
        self.assertFalse(engine.evaluate(grant, request(transaction_id="new-call"), NOW).allowed)

    def test_quota_is_isolated_between_grants(self):
        _, engine1, grant1 = setup(max_attempts=1)
        state2, engine2, grant2 = setup(max_attempts=1)
        grant2 = type(grant2)("g-2", grant2.sender, grant2.recipient, grant2.purpose, grant2.channel, grant2.audience, grant2.expires_at, grant2.policy_epoch, 1)
        engine1.evaluate(grant1, request(), NOW)
        self.assertTrue(engine2.evaluate(grant2, request(grant_id="g-2"), NOW).allowed)


if __name__ == "__main__": unittest.main()
