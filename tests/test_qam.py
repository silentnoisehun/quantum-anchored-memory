"""Automated offline & StatevectorSampler test suite for Quantum Anchored Memory."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

import calibration_test
import sync_real_test
import verify_results
from src.qam_benchmark import main as benchmark_main
from src.qam_core import QAM, shannon_entropy, wilson_ci
from src.qam_memory import QAMMemory, compute_merkle_root
from src.qam_quantum import QAMQuantum, build_wave_band_circuit

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_ibm_heron_rejected_as_backend_name() -> None:
    with pytest.raises(ValueError, match="ibm_heron"):
        QAM(backend="ibm_heron", local=True)


def test_seed42_reproduces_published_kingston_angles() -> None:
    _, _, angles = QAM.build_loschmidt_circuits(qubits=1, seed=42)
    published = json.loads((REPO_ROOT / "results" / "qam_sync_real_test.json").read_text(encoding="utf-8"))
    assert math.isclose(angles[0]["theta"], published["angles"]["theta"], rel_tol=1e-12)
    assert math.isclose(angles[0]["phi"], published["angles"]["phi"], rel_tol=1e-12)
    assert math.isclose(angles[0]["lam"], published["angles"]["lam"], rel_tol=1e-12)
    assert math.isclose(
        angles[0]["expected_control_p0"] * 100.0,
        published["expected_control_p0"],
        rel_tol=1e-12,
    )


def test_local_sync_and_control_statevector() -> None:
    qam = QAM(local=True)
    res = qam.sync_operation(qubits=1, shots=2048, seed=42, include_control=True)
    assert res["result_type"] == "simulated"
    assert res["evidence_grade"] == "SIMULATION_ONLY"
    assert res["returned_shots"] == 2048
    # U * U^dagger = I -> ideal statevector gives 100% |0>
    assert res["success_rate"] == 1.0
    assert res["counts"] == {"0": 2048}

    # Control U|0> expected P(0) = cos^2(2.3533 / 2) = 0.14747
    ctrl = res["control"]
    assert abs(ctrl["p0"] - ctrl["expected_p0"]) < 0.03


def test_local_coherence_test_is_physical_not_zero() -> None:
    qam = QAM(local=True)
    coh = qam.coherence_test(qubits=5, shots=512, seed=42)
    assert coh["result_type"] == "simulated"
    assert coh["coherence"] == 1.0
    assert math.isclose(coh["dephased_floor"], 1.0 / 32.0)


def test_memory_d0_to_d8_merkle_and_recall() -> None:
    mem = QAMMemory(local=True)
    with pytest.raises(ValueError, match="D0..D8"):
        mem.store_quantum_memory("invalid_depth", depth=9)

    stored = mem.store_quantum_memory("QuantumAnchoredMemoryPayload", depth=8, shots=128)
    assert stored["zoom_level"] == "D8"
    assert stored["data"] == "QuantumAnchoredMemoryPayload"

    recalled_full = mem.recall_quantum_memory("QuantumAnchoredMemoryPayload", depth=8)
    assert recalled_full["found"] is True
    assert recalled_full["verified"] is True
    assert recalled_full["result"] == "QuantumAnchoredMemoryPayload"

    recalled_coarse = mem.recall_quantum_memory("QuantumAnchoredMemoryPayload", depth=0)
    assert recalled_coarse["found"] is True
    assert len(recalled_coarse["result"]) < len("QuantumAnchoredMemoryPayload")

    missing = mem.recall_quantum_memory("nonexistent_key", depth=0)
    assert missing["found"] is False

    # Tamper detection check
    mem._store["QuantumAnchoredMemoryPayload"]["projections"][3] = "TAMPERED"
    tampered = mem.recall_quantum_memory("QuantumAnchoredMemoryPayload", depth=8)
    assert tampered["verified"] is False


def test_wave_quantum_13band_rabi_parity() -> None:
    qc = build_wave_band_circuit(0, 13)
    assert qc.num_qubits == 2

    wq = QAMQuantum(local=True)
    res = wq.wave_quantum_encoding("QAM_WAVE", shots=2048, seed=42)
    assert res["result_type"] == "simulated"
    assert res["num_bands"] == 13
    assert res["pearson"] > 0.995
    assert res["pearson_partner_marginal"] > 0.995
    assert abs(res["contrast_a"] - 1.0) < 0.04


def test_wilson_ci_and_entropy_math() -> None:
    lo, hi = wilson_ci(1018, 1024)
    assert 0.987 < lo < 0.9941 < hi < 0.998
    assert math.isclose(shannon_entropy({"0": 512, "1": 512}, 1024), 1.0)
    assert compute_merkle_root(["a", "b"]) != compute_merkle_root(["b", "a"])


def test_cli_entrypoints_and_audit_gates(tmp_path: Path) -> None:
    assert calibration_test.main(["--local", "--shots", "256"]) == 0
    assert sync_real_test.main(["--local", "--shots", "256"]) == 0
    assert verify_results.main() == 0

    summary = benchmark_main(["--local", "--shots", "128", "--output-dir", str(tmp_path)])
    assert summary["mode"] == "simulated"

    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_hygiene.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
