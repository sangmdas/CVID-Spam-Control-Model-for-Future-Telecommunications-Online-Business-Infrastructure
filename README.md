# CVID Authorization-to-Reach and Communication-Finality Reference Implementation

> **Research and interoperability prototype — not a telephone-network standard, production SBC, or emergency-services implementation.**

This runnable reference implementation accompanies the Internet-Draft **“Authorization-to-Reach for Communication Handles: Separating Identifier Possession from Permission to Contact.”** It demonstrates one architectural rule:

> Possession of a telephone number, SIP URI, messaging handle, relay address, or marketplace contact reference is not, by itself, authority to create a communication effect.

An inbound call, message, notification, WebRTC request, or CPaaS operation is represented as a **Candidate Request**. An enforcement point admits it only when a current grant matches the exact sender, recipient, purpose, channel, audience, nonce, handle, direction, effect, validity window, policy epoch, quota, and logical transaction. The visible handle is a name, not a reusable contact right.

Version 0.2.0 implements the general CVID/Authorization-to-Reach model from `draft-das-6g-query-scoped-communication-handles-04`. It does not implement the separate map-discovery Preview-to-Unlock model.

## What the ZIP / TAR distribution contains

| Path | Contents |
|---|---|
| `src/cvid_ref/models.py` | Strict immutable data models for grants and candidate communication requests. |
| `src/cvid_ref/engine.py` | Fail-closed verifier, policy-epoch check, atomic logical-act consumption, and structured decisions. |
| `src/cvid_ref/crypto.py` | Canonical JSON and dependency-free HMAC-SHA256 grant-envelope integrity. |
| `src/cvid_ref/finality.py` | Signed-grant verification, five-second release capability, and controlled final resource allocator. |
| `tests/` | 108 tests covering scope binding, integrity, finality, failure precedence, concurrency, malformed inputs, profiles and licensing. |
| `tools/benchmark.py` | Reproducible microbenchmark for decision latency and throughput. |
| `configs/*.json` | Ten deployment and protocol-binding variations with explicit claim limits. |
| `docs/` | Performance, test-results, environment and variation documentation. |
| `LICENSE.md` | PolyForm Noncommercial License 1.0.0 notice and patent/IETF-IPR separation. |
| `pyproject.toml` | Standard-library-only Python package and test configuration. |

The archive is deliberately small and auditable. It proves the decision semantics; it does **not** claim to replace a SIP proxy, SBC, carrier IMS, STIR/SHAKEN implementation, PSTN gateway, OAuth server, HSM, or production anti-fraud system.

## Security property demonstrated

The protected effect is denied unless all of the following match:

1. authenticated origin (`sender`);
2. recipient identity or query-scoped descriptor (`recipient`);
3. opaque interaction/purpose identifier;
4. permitted channel (voice, message, notification, etc.);
5. enforcement-point audience;
6. nonce/freshness value;
7. query-scoped handle identifier;
8. direction and requested effect;
9. issuance and expiry times;
10. current policy/revocation epoch;
11. remaining logical-attempt quota; and
12. a stable logical transaction identifier, so a SIP retransmission is not charged as a second act.

The grant is intentionally sender-bound. A copied handle alone cannot authorize contact, and copying the grant should not transfer authority to a different authenticated sender.

## Quick start

```bash
python -m unittest discover -s tests -v
python tools/benchmark.py --iterations 50000 --profile pre-routing
```

No external runtime dependencies are required. Use Python 3.11 or newer.

## Detailed test coverage

The suite is divided by security property, so a passing count cannot hide which boundary was exercised:

| Test module | What it verifies |
|---|---|
| `test_engine.py` | Basic allow path, copied-handle/sender denial, logical replay denial, expiry and epoch revocation. |
| `test_field_binding.py` | Independent binding of grant ID, authenticated sender, recipient, purpose, channel, audience, case sensitivity, exact-expiry behavior, and fail-closed missing policy state. |
| `test_extended_binding.py` | Nonce, CVID handle, direction and requested-effect binding. |
| `test_signed_finality.py` | Signed envelopes, issuer trust, tamper/wrong-key rejection, bounded release and allocator enforcement. |
| `test_finality_concurrency.py` | Concurrent release issuance and allocator idempotency. |
| `test_failure_precedence.py` | Deterministic fail-closed error ordering and proof that denied requests do not consume quota. |
| `test_input_invariants.py` | Individually named rejection tests for every required grant and request field. |
| `test_quota_and_concurrency.py` | Multi-attempt quotas, idempotent SIP retransmission, grant isolation, 50-way concurrent distinct-act race, and 50-way concurrent retransmission race. |
| `test_models.py` | Non-empty required fields, timezone-aware expiry, positive quota, non-negative epoch, immutable grants/candidates, and invalid epoch-store input. |
| `test_profiles.py` | Truthful claim boundaries for blocked-path, pre-routing, and absent-path configurations. |
| `test_protocol_variations.py` | SIP, STIR, CPaaS, WebRTC/TURN, messaging, federation and attested-mode limitations. |
| `test_license_policy.py` | Required notice, official license reference, commercial restriction and IETF-IPR separation. |

Run all 108 tests with:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Reference decision flow

```text
Candidate Request
  → signed grant-envelope verification
  → canonical field comparison
  → expiry / audience / nonce / handle / direction / effect / epoch check
  → atomic logical-act reservation
  → short-lived resource-specific Release Capability
  → allocator re-verification
  → ALLOW: create only the bounded communication resource
  → DENY: no protected ringing, notification, session, or media effect
```

In a SIP binding, the engine belongs at a proxy, SBC, application server, CPaaS gateway, resolver, or another boundary that can prevent the protected effect. STIR/SHAKEN can authenticate origin identity; this prototype uses the supplied authenticated origin as an input and does not implement STIR signing or verification.

## Deployment and protocol variations

| Profile | Enforcement timing | What it can truthfully claim | Typical placement |
|---|---|---|---|
| **A — Blocked path** | After normal address resolution but before ringing/notification/session creation | Unauthorized effects are blocked at the enforcement point; upstream signaling may already occur. | SBC, SIP application server, CPaaS gateway |
| **B — Pre-routing authorization** | Before full destination routing | Unauthorized attempts can avoid downstream destination lookup, wake-up, media reservation, and related work. | Resolver, directory, service-exposure gateway |
| **C — Absent path** | A route is released only after authorization | The visible descriptor alone does not activate the effective path. This claim fails if an alternate routable path bypasses the same check. | Controlled relay / private namespace / mediated marketplace |

Seven additional configuration variations are included:

| Variation | Intended use | Important limitation |
|---|---|---|
| SIP/SBC | Authorization reference at proxy, SBC or application server | No new SIP header is standardized here. |
| STIR/PASSporT input | Verified origin feeds the sender predicate | Origin authenticity is not recipient permission. |
| HTTP/CPaaS | Grant/reference at an API gateway or callback bridge | General API access does not authorize the communication consequence. |
| WebRTC/TURN | Check before room, notification, media or relay allocation | No new WebRTC or TURN field is defined. |
| Messaging/notification | Check before recipient notification or thread creation | Earlier upstream processing may still occur. |
| Federated edge | Cross-provider authority verified near termination | Issuer discovery, trust and revocation semantics remain open. |
| High-assurance/attested | HSM, TEE, enclave or attested verifier | Attestation complements but does not replace communication authority. |

`configs/` makes these operational distinctions explicit. It does not pretend legacy PSTN or an uncontrolled public number can provide absent-path semantics.

## Expected latency and performance

The Internet-Draft intentionally claims **no universal millisecond value**. Results depend on the cryptographic format, cache hit rate, storage choice, topology, SIP stack, and whether an online revocation check is needed. This repository therefore distinguishes targets from measurements.

| Path | Engineering target (same-process prototype) | Why it differs |
|---|---:|---|
| Fully local, in-memory validation and consumption | p99 under **1 ms** | No network or persistent-store round trip. |
| Local verifier with durable/replicated consume-state | p99 under **5 ms** | Atomic state coordination is on the critical path. |
| Near-edge online validation | p99 under **20 ms** | Network and issuer/revocation lookup contribute. |
| Remote cross-region online validation | **Not recommended** as the default voice hot path | Adds tail latency and a new availability dependency. |

These are design budgets for a real deployment to test against—not measured claims by this repository, carrier-grade guarantees, or protocol requirements. Run `tools/benchmark.py` on the target host and publish environment details, workload, percentiles, cache state, decision mix, and failure/revocation behavior.

### Measured version 0.2.0 result

Command: `PYTHONPATH=src python tools/benchmark.py --iterations 50000 --profile pre-routing`

| Local operation | Throughput | p50 | p95 | p99 |
|---|---:|---:|---:|---:|
| Core in-memory authorization decision | 187,340/s | 1.96 µs | 2.43 µs | 3.38 µs |
| Signed-envelope finality decision and capability issuance | 14,164/s | 50.35 µs | 87.60 µs | 298.24 µs |
| Capability verification and resource allocation | 41,114/s | 19.67 µs | 31.58 µs | 90.12 µs |

These results include CPython object processing, canonical JSON, HMAC-SHA256, exact field comparison, process-local locking and in-memory state. They exclude SIP/STIR parsing, asymmetric signatures, durable or replicated storage, TLS/network latency, CPaaS processing, PSTN/WebRTC setup, HSM/TEE transitions and media allocation.

## Recorded test environment

| Parameter | Value |
|---|---|
| Language | Python |
| Runtime | CPython 3.12.13 |
| Supported project version | Python 3.11 or later |
| Compiler used for CPython | Clang 22.1.3 |
| Operating system | Linux 6.18.35, x86-64 |
| C library | glibc 2.39 |
| CPU reported by environment | Intel Xeon Platinum 8573C |
| Logical CPUs available | 9 |
| External packages | None |
| Integrity mode | HMAC-SHA256, minimum 32-byte reference key |
| Serialization | Canonical JSON, sorted keys, compact separators, UTF-8 |
| State | Process-local Python dictionaries protected by locks |
| Benchmark iterations | 50,000 per reported path |

The environment is shared or virtualized. Results are reproducibility measurements, not service-level guarantees. See `docs/ENVIRONMENT.md` and `docs/performance.md` for reporting requirements.

## Benchmarking correctly

Benchmark at least four cases separately:

- local valid grant, first logical act;
- repeated SIP retransmission of the *same* transaction (idempotent allow, not re-consumption);
- rejected request (wrong sender, epoch, expiry, or purpose);
- cache miss / online issuer or revocation validation.

For system tests, also report invite-to-180/183/200 setup deltas, rejected-attempt CPU, signaling bytes, application wake-ups, downstream route lookups, media allocations, and decision latency at p50/p95/p99. A single average latency figure hides the primary operational risks.

## Important limitations and production hardening

- The prototype trusts its `authenticated_sender` input. A production binding must derive it from a protected source such as a verified SIP identity, mTLS workload identity, DPoP-bound token, or carrier-authenticated context.
- Its in-memory store is process-local. Use a transactional store, a single authoritative shard, or a carefully designed reservation protocol for multi-node quota enforcement.
- It demonstrates HMAC-signed grant envelopes but does not implement production issuer discovery, asymmetric certificates, managed key rotation, HSM custody or cross-provider federation.
- The `purpose` field is opaque. Free text is not mechanically enforceable; use an application-defined transaction or enquiry identifier.
- Emergency and legally required paths must be separately designed and must not be disabled by ordinary grant-service failure.
- A deployment may claim absent-path behavior only after mapping and closing equivalent alternate paths: ordinary PSTN number, SIP URI, CPaaS API, messaging service, relay, notification service, forwarding, and other identifiers.

## Relationship to existing technology

- **STIR/SHAKEN**: authenticates/attests origin identity; it does not itself express recipient-specific current authority to contact.
- **Virtual numbers and relays**: hide an endpoint but may remain routable while active. They can be a transport façade for this model.
- **OAuth / RAR / ACE**: may carry or issue a grant, but do not by themselves define telephone/messaging reachability or logical SIP-act consumption.
- **SIP/IMS/PSTN**: remain transports. This reference implementation is an authorization decision at a communication-bearing boundary.

## License and status

The repository is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE.md). Subject to its official terms, the code may be studied, tested, modified and distributed for permitted non-commercial purposes. Commercial use requires prior written permission or a separate commercial license. The limited repository license does not replace an applicable IETF IPR disclosure or independently grant commercial patent implementation rights. This is source-available, not OSI-approved open source.
