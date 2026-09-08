# Test results

Version 0.2.0 result:

```text
Ran 108 tests in 0.105s
OK
```

No tests were skipped or marked as expected failures. The suite uses only the Python standard library.

Coverage includes all bound grant/request fields; exact expiry behavior; missing and stale epoch state; replay and quota exhaustion; SIP-style retransmission idempotency; 50-way concurrent races; signed grant integrity; wrong key and untrusted issuer rejection; bounded release capabilities; allocator actor/resource/audience enforcement; malformed input; deterministic failure precedence; ten deployment/configuration variations; and license packaging checks.

Passing this suite demonstrates the behavior of the local reference model. It does not establish SIP, STIR, OAuth, WebRTC, TURN, CPaaS, carrier, distributed-database, HSM, TEE or standards conformance.
