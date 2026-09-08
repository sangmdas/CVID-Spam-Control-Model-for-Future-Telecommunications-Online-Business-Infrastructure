#!/usr/bin/env sh
set -eu
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python tools/benchmark.py --iterations "${1:-50000}" --profile "${2:-pre-routing}"
