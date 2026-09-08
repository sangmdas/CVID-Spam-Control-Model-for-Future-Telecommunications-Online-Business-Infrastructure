# Environment and reproducibility record

The version 0.2.0 test and benchmark results were produced with CPython 3.12.13 on Linux 6.18.35 x86-64 with glibc 2.39. CPython reports Clang 22.1.3 as its compiler. The execution environment exposed nine logical CPUs and reported an Intel Xeon Platinum 8573C processor.

The implementation uses only the Python standard library. It uses HMAC-SHA256, canonical JSON, immutable dataclasses, process-local dictionaries and Python locks. No network, DNS, TLS, SIP, STIR, CPaaS, PSTN, WebRTC, TURN, persistent database, HSM, TEE, secure enclave or remote-attestation service participated in the measured run.

Functional test command:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Benchmark command:

```bash
PYTHONPATH=src python tools/benchmark.py --iterations 50000 --profile pre-routing
```

The host is shared or virtualized. Measurements may include scheduler interference. Reproduction reports should include CPU, OS, runtime, compiler, cryptographic mode, state backend, concurrency, traffic mix, cache state, percentiles, failures and whether protocol/network/media operations were included.
