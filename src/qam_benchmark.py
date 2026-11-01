"""
QAM Full Benchmark Suite
========================
Usage:
  # Local StatevectorSampler verification (0 quota, no token required):
  python -m src.qam_benchmark --local

  # Real IBM Quantum hardware (reads IBM_QUANTUM_TOKEN from environment):
  export IBM_QUANTUM_TOKEN="..."
  python -m src.qam_benchmark --backend ibm_kingston
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.qam_core import QAM, resolve_ibm_token
from src.qam_memory import QAMMemory
from src.qam_quantum import QAMQuantum


def main(argv: List[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="QAM Benchmark Suite")
    parser.add_argument(
        "--backend",
        type=str,
        default="ibm_kingston",
        help="IBM Quantum Heron backend (e.g., ibm_kingston, ibm_fez, ibm_marrakesh)",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Shots per circuit (default: 1024)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Force local StatevectorSampler mode (NOT hardware evidence)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for saving the benchmark JSON output",
    )
    args = parser.parse_args(argv)

    token = None if args.local else resolve_ibm_token()
    is_local = args.local or not token

    print("=" * 68)
    print("QAM Benchmark Suite — Quantum Anchored Memory")
    print("=" * 68)
    print(f"  Target backend : {args.backend}")
    print(
        f"  Execution mode : "
        f"{'LOCAL SIMULATION (StatevectorSampler — NOT hardware proof)' if is_local else 'REAL QPU HARDWARE'}"
    )
    print("=" * 68)

    qam = QAM(backend=args.backend, local=is_local)
    results: List[Dict[str, Any]] = []

    print("\n[1/4] Loschmidt Echo SYnc benchmark (U · U† |0⟩ → |0⟩, opt_level=0)...")
    for qubits in (1, 5):
        res = qam.sync_operation(qubits=qubits, shots=args.shots, include_control=(qubits == 1))
        results.append(res)
        print(
            f"  qubits={qubits:2d} | P(0^n)={res['success_rate'] * 100:6.2f}% "
            f"| H={res['entropy']:.4f} bits | mode={res['result_type']}"
        )

    print("\n[2/4] Interferometric phase-coherence benchmark (H → H, opt_level=0)...")
    coh = qam.coherence_test(qubits=5, shots=args.shots)
    results.append(coh)
    print(
        f"  qubits= 5 | P(0^5)={coh['coherence'] * 100:6.2f}% "
        f"(dephased floor {coh['dephased_floor'] * 100:.2f}%) | mode={coh['result_type']}"
    )

    print("\n[3/4] Hierarchical memory store/recall (D0–D8 Merkle + SYnc)...")
    qam_mem = QAMMemory(backend=args.backend, local=is_local)
    stored = qam_mem.store_quantum_memory("QAM_TEST_DATA", depth=8, shots=args.shots)
    recalled = qam_mem.recall_quantum_memory("QAM_TEST_DATA", depth=8)
    results.extend([stored, recalled])
    print(
        f"  level={stored['zoom_level']} | verified={recalled['verified']} "
        f"| merkle={stored['merkle_root'][:16]}..."
    )

    print("\n[4/4] 13-band Wave-Quantum Rabi parity sweep...")
    qam_q = QAMQuantum(backend=args.backend, local=is_local)
    wq = qam_q.wave_quantum_encoding("QAM_WAVE_DATA", shots=args.shots)
    results.append(wq)
    print(
        f"  bands={wq['num_bands']} | Pearson r={wq['pearson']:.4f} "
        f"| contrast A={wq['contrast_a']:.4f} | mode={wq['result_type']}"
    )

    repo_root = Path(__file__).resolve().parent.parent
    results_dir = args.output_dir if args.output_dir is not None else (repo_root / "results")
    os.makedirs(results_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = results_dir / f"qam_results_{ts}.json"
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "simulated" if is_local else "quantum",
        "backend": "statevector_simulator" if is_local else args.backend,
        "results": results,
    }
    filepath.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 68)
    print(f"Saved benchmark output: {filepath}")
    print("=" * 68)
    return summary


if __name__ == "__main__":
    main()
