"""Measure local decision overhead only; not a carrier setup-latency benchmark."""
import argparse
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from cvid_ref import (CandidateRequest, CommunicationGrant, EnforcementEngine, FinalityAllocator,
                      FinalityEngine, GrantEnvelope, HMACAuthenticator, InMemoryGrantState)


def percentile(values, p):
    return sorted(values)[max(0, int(len(values) * p) - 1)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--profile", choices=("blocked-path", "pre-routing", "absent-path"), default="pre-routing")
    args = parser.parse_args()
    now = datetime.now(timezone.utc); state = InMemoryGrantState(); state.set_epoch("user:U", 1)
    grant = CommunicationGrant("g", "business:B", "user:U", "enquiry:42", "voice", args.profile, now + timedelta(hours=1), 1, args.iterations + 1)
    engine = EnforcementEngine(state); samples = []
    started = time.perf_counter_ns()
    for i in range(args.iterations):
        request = CandidateRequest(f"call-{i}", "business:B", "user:U", "enquiry:42", "voice", args.profile, "g")
        t0 = time.perf_counter_ns(); decision = engine.evaluate(grant, request, now); samples.append((time.perf_counter_ns() - t0) / 1_000)
        if not decision.allowed: raise RuntimeError(decision.reason)
    total_s = (time.perf_counter_ns() - started) / 1_000_000_000
    print(f"profile={args.profile} iterations={args.iterations} total_s={total_s:.6f}")
    print(f"decision_us p50={statistics.median(samples):.2f} p95={percentile(samples,.95):.2f} p99={percentile(samples,.99):.2f}")
    print(f"throughput_decisions_per_s={args.iterations / total_s:.0f}")
    auth = HMACAuthenticator(b"benchmark-reference-key-at-least-32-bytes")
    state2 = InMemoryGrantState(); state2.set_epoch("user:U", 1)
    signed_grant = CommunicationGrant("signed", "business:B", "user:U", "enquiry:42", "voice", "sbc:west", now + timedelta(hours=1), 1, args.iterations + 1)
    envelope = auth.sign_envelope(GrantEnvelope(signed_grant, "issuer:benchmark", "key:1"))
    finality = FinalityEngine(EnforcementEngine(state2), auth, {"issuer:benchmark"}, "sink:west")
    finality_samples=[]; capabilities=[]; started=time.perf_counter_ns()
    for i in range(args.iterations):
        req=CandidateRequest(f"signed-{i}","business:B","user:U","enquiry:42","voice","sbc:west","signed")
        t0=time.perf_counter_ns(); decision=finality.evaluate(envelope,req,now); finality_samples.append((time.perf_counter_ns()-t0)/1_000); capabilities.append(decision.capability)
    elapsed=(time.perf_counter_ns()-started)/1_000_000_000
    print(f"signed_finality_us p50={statistics.median(finality_samples):.2f} p95={percentile(finality_samples,.95):.2f} p99={percentile(finality_samples,.99):.2f} throughput_per_s={args.iterations/elapsed:.0f}")
    allocator=FinalityAllocator(auth,"sink:west"); allocation_samples=[]; started=time.perf_counter_ns()
    for cap in capabilities:
        t0=time.perf_counter_ns(); result=allocator.allocate(cap,"business:B",cap.resource_id,now); allocation_samples.append((time.perf_counter_ns()-t0)/1_000)
        if not result.allowed: raise RuntimeError(result.reason)
    elapsed=(time.perf_counter_ns()-started)/1_000_000_000
    print(f"allocation_us p50={statistics.median(allocation_samples):.2f} p95={percentile(allocation_samples,.95):.2f} p99={percentile(allocation_samples,.99):.2f} throughput_per_s={args.iterations/elapsed:.0f}")
    print("Scope: CPython, HMAC-SHA256, canonical JSON, in-memory locked state. Excludes SIP/STIR parsing, asymmetric signatures, durable storage, I/O, network, CPaaS and media setup.")

if __name__ == "__main__": main()
