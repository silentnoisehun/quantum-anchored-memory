#!/usr/bin/env python3
"""
Real Loschmidt Echo (U · U† → |0⟩) + Control (U|0⟩) verification at opt_level=0.
Reads IBM_QUANTUM_TOKEN from the environment for hardware runs, or executes on
local StatevectorSampler with --local (zero quota, no credentials).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.qam_core import QAM, resolve_ibm_token


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QAM Loschmidt Echo Verification")
    parser.add_argument("--backend", type=str, default="ibm_kingston")
    parser.add_argument("--qubit", type=int, default=91, help="Physical qubit index on Heron QPU")
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--local", action="store_true", help="Run on local StatevectorSampler (0 quota)")
    args = parser.parse_args(argv)

    token = None if args.local else resolve_ibm_token()
    is_local = args.local or not token
    qam = QAM(backend=args.backend, local=is_local)

    res = qam.sync_operation(
        qubits=1,
        shots=args.shots,
        opt_level=0,
        initial_layout=None if is_local else [args.qubit],
        seed=args.seed,
        include_control=True,
    )

    ctrl = res["control"]
    p0_sync = res["success_rate"] * 100.0
    p0_ctrl = ctrl["p0"] * 100.0
    exp_ctrl = ctrl["expected_p0"] * 100.0
    ratio = p0_sync / p0_ctrl if p0_ctrl > 0 else float("inf")

    print("=" * 64)
    print(f"QAM Loschmidt Echo Verification ({res['result_type']} — {res['evidence_grade']})")
    print("=" * 64)
    print(f"  Backend           : {res['backend']}")
    print(f"  SYnc (U·U†) P(0)  : {p0_sync:6.2f}%  counts={res['counts']}")
    print(f"  Control (U) P(0)  : {p0_ctrl:6.2f}%  counts={ctrl['counts']} (expected {exp_ctrl:.2f}%)")
    print(f"  Improvement ratio : {ratio:.2f}x")
    print("=" * 64)

    if not is_local:
        out = Path(__file__).resolve().parent / "results" / "qam_sync_latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
        print(f"Saved hardware run: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
