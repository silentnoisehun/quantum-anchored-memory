#!/usr/bin/env python3
"""
Recover a completed IBM Quantum job by Job ID without consuming QPU quota.
Reads IBM_QUANTUM_TOKEN from the environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.qam_core import QAM, resolve_ibm_token


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieve an IBM Quantum job result (0 quota)")
    parser.add_argument("job_id", help="IBM Quantum Runtime job ID")
    parser.add_argument("--qubits", type=int, default=1, help="Number of measured qubits")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path")
    args = parser.parse_args(argv)

    token = resolve_ibm_token()
    if not token:
        print("Error: set IBM_QUANTUM_TOKEN in the environment first.", file=sys.stderr)
        return 1

    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="auto")
    job = service.job(args.job_id)
    status = str(job.status())
    payload: dict[str, object] = {"job_id": args.job_id, "status": status}

    if "DONE" in status.upper():
        result = job.result()
        counts = QAM._extract_counts(result, pub_index=0, qubits=args.qubits)
        total = sum(counts.values())
        zeros = counts.get("0" * args.qubits, 0)
        payload["returned_shots"] = total
        payload["p_all_zero"] = zeros / total if total > 0 else 0.0
        payload["counts"] = counts

    rendered = json.dumps(payload, indent=2, default=str)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
