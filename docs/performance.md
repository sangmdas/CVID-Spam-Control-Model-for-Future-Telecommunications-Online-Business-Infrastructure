# Performance and latency evaluation

## What can be measured here

`tools/benchmark.py` measures the local Python decision path: canonical grant/request comparison, expiry and epoch checks, and lock-protected logical-act consumption. It is useful for regression testing and comparing code changes. It is **not** a SIP call-setup benchmark and must not be presented as a telecom-network result.

Before publishing any benchmark, run the complete 36-test suite. Performance output is invalid if authorization semantics, concurrent quota enforcement, or fail-closed behavior do not pass.

## Target budgets to validate in a production design

| Validation mode | Suggested p99 budget | Architecture condition |
|---|---:|---|
| local signed grant + in-memory/near-memory state | < 1 ms | co-located with the enforcement boundary |
| local signed grant + durable replicated consume state | < 5 ms | storage operation stays in the same availability zone / edge site |
| online issuer, policy or revocation validation at a nearby edge | < 20 ms | bounded request size, pooled connections, no long-haul dependency |
| remote validation | no default target | measure separately; do not put it on every voice hot path by default |

These are planning budgets, not measured results, standards requirements, or performance promises. A deployment needs its own data for the intended platform and failure mode.

## Test matrix

| Dimension | Variations to report |
|---|---|
| enforcement profile | blocked path, pre-routing, absent path |
| authorization state | valid, expired, revoked epoch, quota exhausted, wrong origin, wrong purpose/channel/audience |
| state operation | no consumption, first logical act, retransmission, concurrent quota race |
| verification | local cached key, cold key/issuer lookup, online revocation, issuer unavailable |
| traffic | voice INVITE, message, notification, HTTP CPaaS request; human-rate and fan-out/retry traffic |
| topology | same process, same host, same edge/zone, cross-zone, cross-region, roaming/failover |

## Report format

Publish the following with each result: hardware/CPU, OS/runtime, commit hash, cryptographic algorithm and key size, storage implementation, number of workers, request size, cache hit ratio, concurrency, decision mix, throughput, p50/p95/p99/p99.9, error rate, and whether SIP parsing/signature verification/network/media were included.

Measure admission decisions separately from full call setup. For end-to-end SIP tests, compare baseline and enforcement-enabled flows using the same traffic mix, and report: INVITE-to-provisional/final response timing, rejected-attempt CPU, signaling bytes, SBC transactions, downstream route lookups, application wake-ups, media reservations, and failure behavior.

## Engineering choices and their cost

| Choice | Benefit | Cost / risk |
|---|---|---|
| short-lived signed grant | mostly local verification | revocation may wait for expiry unless epochs are checked |
| online validation | rapid revocation and centralized policy | added tail latency and availability dependency |
| atomic durable consumption | robust single-use / quota behavior | coordination on hot path |
| idempotent transaction key | SIP retransmission is not double-charged | binding must define logical act and retransmission identity |
| pre-routing placement | avoids downstream work for denied attempts | requires an authoritative early boundary |
| absent-path design | strongest non-reachability property | requires complete alternate-path inventory and control |

## Failure mode

Ordinary protected communication can fail closed when authorization cannot be established, but this is an availability decision. Emergency and legally mandated access must have independently engineered, always-available routing and must not be accidentally gated by the ordinary grant service.
