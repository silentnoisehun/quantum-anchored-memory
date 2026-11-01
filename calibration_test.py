#!/usr/bin/env python3
"""
Calibration sanity check: X·X = I and RY(π/2)·RY(-π/2) = I at opt_level=0.
Supports --local (StatevectorSampler, 0 quota) and real IBM QPU execution
via IBM_QUANTUM_TOKEN environment variable.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from qiskit import QuantumCircuit, transpile
from qiskit.primitives import StatevectorSampler

from src.qam_core import QAM, _run_runtime_sampler, resolve_ibm_token, wilson_ci


def build_calibration_circuits() -> dict[str, QuantumCircuit]:
    qc_xx = QuantumCircuit(1)
    qc_xx.x(0)
    qc_xx.barrier()
    qc_xx.x(0)
    qc_xx.barrier()
    qc_xx.measure_all()

    qc_ry = QuantumCircuit(1)
    qc_ry.ry(math.pi / 2.0, 0)
    qc_ry.barrier()
    qc_ry.ry(-math.pi / 2.0, 0)
    qc_ry.barrier()
    qc_ry.measure_all()

    return {"xx_identity": qc_xx, "ry_echo": qc_ry}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QAM Calibration Sanity Check")
    parser.add_argument("--backend", type=str, default="ibm_kingston")
    parser.add_argument("--qubit", type=int, default=91, help="Physical qubit index for opt_level=0")
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--local", action="store_true", help="Run on local StatevectorSampler (0 quota)")
    args = parser.parse_args(argv)

    token = None if args.local else resolve_ibm_token()
    is_local = args.local or not token
    circuits = build_calibration_circuits()
    names = list(circuits.keys())
    qc_list = [circuits[k] for k in names]

    if is_local:
        print("Running calibration sanity check on LOCAL StatevectorSampler (NOT hardware evidence)...")
        sampler = StatevectorSampler(seed=42)
        res = sampler.run(qc_list, shots=args.shots).result()
        job_id = "local-calibration-42"
        mode = "simulated"
    else:
        qam = QAM(backend=args.backend, local=False)
        if qam.backend is None:
            print("Backend unavailable; aborting hardware calibration.")
            return 1
        print(f"Running calibration sanity check on {args.backend} (physical qubit {args.qubit}, opt_level=0)...")
        t_list = [
            transpile(qc, qam.backend, optimization_level=0, seed_transpiler=42, initial_layout=[args.qubit])
            for qc in qc_list
        ]
        res, job_id = _run_runtime_sampler(qam.backend, t_list, shots=args.shots)
        mode = "quantum"

    report: dict[str, object] = {
        "mode": mode,
        "backend": "statevector_simulator" if is_local else args.backend,
        "physical_qubit": None if is_local else args.qubit,
        "job_id": job_id,
        "tests": {},
    }

    for idx, name in enumerate(names):
        counts = QAM._extract_counts(res, pub_index=idx, qubits=1)
        total = sum(counts.values())
        zeros = counts.get("0", 0)
        p0 = zeros / total if total > 0 else 0.0
        ci_lo, ci_hi = wilson_ci(zeros, total)
        report["tests"][name] = {
            "p0": p0,
            "wilson_95_ci": [ci_lo, ci_hi],
            "counts": counts,
        }
        print(f"  {name:<14}: P(0) = {p0 * 100:6.2f}%  CI=[{ci_lo * 100:.2f}%, {ci_hi * 100:.2f}%]  counts={counts}")

    if not is_local:
        out = Path(__file__).resolve().parent / "results" / "qam_calibration_latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved hardware calibration record: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
