import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from cvid_ref import *
from fixtures import NOW,request,setup

KEY=b"finality-concurrency-key-at-least-32-bytes"

def make(quota):
    _,core,grant=setup(quota); auth=HMACAuthenticator(KEY); env=auth.sign_envelope(GrantEnvelope(grant,"issuer","key"))
    return env,FinalityEngine(core,auth,{"issuer"},"sink"),FinalityAllocator(auth,"sink")

class FinalityConcurrencyTests(unittest.TestCase):
    def test_fifty_new_acts_yield_one_capability_for_quota_one(self):
        env,engine,_=make(1)
        with ThreadPoolExecutor(max_workers=20) as pool: results=list(pool.map(lambda i:engine.evaluate(env,request(transaction_id=f"t-{i}"),NOW),range(50)))
        self.assertEqual(1,sum(r.allowed for r in results))
    def test_fifty_retransmissions_remain_authorized(self):
        env,engine,_=make(1)
        with ThreadPoolExecutor(max_workers=20) as pool: results=list(pool.map(lambda _:engine.evaluate(env,request(transaction_id="same"),NOW),range(50)))
        self.assertTrue(all(r.allowed for r in results)); self.assertEqual(49,sum(r.idempotent for r in results))
    def test_concurrent_allocator_retransmission_is_idempotent(self):
        env,engine,allocator=make(1); cap=engine.evaluate(env,request(),NOW).capability
        with ThreadPoolExecutor(max_workers=20) as pool: results=list(pool.map(lambda _:allocator.allocate(cap,"business:B",cap.resource_id,NOW),range(50)))
        self.assertTrue(all(r.allowed for r in results)); self.assertEqual(49,sum(r.idempotent for r in results))
    def test_denied_race_creates_no_allocator_effect(self):
        env,engine,allocator=make(1); engine.evaluate(env,request(),NOW)
        denied=engine.evaluate(env,request(transaction_id="other"),NOW)
        self.assertIsNone(denied.capability); self.assertEqual({},allocator.effects)

if __name__=="__main__": unittest.main()
