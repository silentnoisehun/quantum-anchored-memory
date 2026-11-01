#!/usr/bin/env python3
"""Root wrapper for the QAM Benchmark Suite."""

from __future__ import annotations

import sys

from src.qam_benchmark import main


if __name__ == "__main__":
    main(sys.argv[1:])
