"""
QAM Quantum — Wave-Quantum 13-Band Rabi Parity Encoding
=======================================================
Replaces the earlier random placeholder with the actual 2-qubit wave-quantum v3
encoding across N = 13 frequency bands:

  Circuit (2-qubit core of wave-quantum v3 `build_v3` at A=0.5, φ=0, θ_k = 2π·k/13):
    1. Encode:      RY(π/2) on q0 (readout -> |+⟩), RX(θ_k) on q1 (partner)
    2. Bell-bridge: H(q1) → CX(q1 → q0)
    3. X-readout:   H(q0), H(q1) → measure

  Analytical expectation (Heisenberg back-propagation):
    (H_1 ⊗ H_0):      Z_1 ⊗ Z_0  →  X_1 ⊗ X_0
    CX(q1 → q0):      X_1 ⊗ X_0  →  X_1 ⊗ I_0
    H_1 (Bell-bridge): X_1        →  Z_1
    RX(θ_k)|0⟩:       ⟨Z_1⟩ = cos(θ_k) = cos(2π·k/13) = ⟨Z_0 Z_1⟩
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.primitives import StatevectorSampler

from src.qam_core import QAM, _run_runtime_sampler

NUM_BANDS = 13


def build_wave_band_circuit(
    band_k: int,
    num_bands: int = NUM_BANDS,
    amplitude: float = 0.5,
    phase: float = 0.0,
) -> QuantumCircuit:
    """Build the 2-qubit wave-quantum v3 circuit (`build_v3`) for frequency band `band_k`."""
    theta_a = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, amplitude))))
    theta_k = 2.0 * math.pi * float(band_k) / float(num_bands)

    qc = QuantumCircuit(2)
    qc.ry(theta_a, 0)
    qc.rx(theta_k, 1)
    if phase != 0.0:
        qc.rz(2.0 * phase, 0)

    # Bell-bridge
    qc.h(1)
    qc.cx(1, 0)

    # X-basis readout
    qc.h(0)
    qc.h(1)
    qc.measure_all()
    return qc


def _parity_and_partner_expectation(counts: Dict[str, int]) -> Dict[str, float]:
    """
    Compute ⟨Z_0 Z_1⟩ and partner marginal ⟨Z_1⟩ from Qiskit 2-qubit bitstrings
    (Qiskit little-endian convention: bitstring is 'c1 c0' -> idx 0 is q1, idx 1 is q0).
    """
    total = sum(counts.values())
    if total <= 0:
        return {"zz": 0.0, "z1": 0.0}

    zz_acc = 0.0
    z1_acc = 0.0
    for bits, count in counts.items():
        b = bits.replace(" ", "").zfill(2)
        z1 = 1.0 if b[-2] == "0" else -1.0
        z0 = 1.0 if b[-1] == "0" else -1.0
        zz_acc += (z0 * z1) * count
        z1_acc += z1 * count
    return {"zz": zz_acc / total, "z1": z1_acc / total}


def _pearson_r(xs: Sequence[float], ys: Sequence[float]) -> float:
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    x_diff = x - np.mean(x)
    y_diff = y - np.mean(y)
    denom = float(np.sqrt(np.sum(x_diff ** 2) * np.sum(y_diff ** 2)))
    if denom == 0.0:
        return 0.0
    return float(np.sum(x_diff * y_diff) / denom)


class QAMQuantum:
    """13-band wave-quantum Rabi parity encoder/evaluator."""

    def __init__(
        self,
        token: Optional[str] = None,
        backend: str = "ibm_kingston",
        local: bool = False,
    ) -> None:
        self.qam = QAM(token=token, backend=backend, local=local)

    def wave_quantum_encoding(
        self,
        data: str = "",
        shots: int = 1024,
        seed: int = 42,
        initial_layout: Optional[Sequence[int]] = None,
    ) -> Dict[str, Any]:
        """
        Sweep all 13 frequency bands and compute the real Pearson correlation `r`
        and fitted Rabi contrast `A` against cos(2π·k/13).
        """
        circuits = [build_wave_band_circuit(k, NUM_BANDS) for k in range(NUM_BANDS)]
        ideal = [math.cos(2.0 * math.pi * k / NUM_BANDS) for k in range(NUM_BANDS)]

        if self.qam.backend is None:
            sampler = StatevectorSampler(seed=seed)
            res = sampler.run(circuits, shots=shots).result()
            job_id = f"local-wave-{seed}"
            backend_name = "statevector_simulator"
            result_type = "simulated"
            evidence_grade = "SIMULATION_ONLY"
        else:
            chosen_layout = (
                list(initial_layout)
                if initial_layout is not None
                else self.qam.select_good_qubits(2)
            )
            transpile_kwargs: Dict[str, Any] = {
                "optimization_level": 1,
                "seed_transpiler": seed,
            }
            if chosen_layout is not None:
                transpile_kwargs["initial_layout"] = chosen_layout
            t_circuits = [transpile(qc, self.qam.backend, **transpile_kwargs) for qc in circuits]
            res, job_id = _run_runtime_sampler(self.qam.backend, t_circuits, shots=shots)
            backend_name = getattr(self.qam.backend, "name", str(self.qam.backend))
            result_type = "quantum"
            evidence_grade = "HARDWARE_MEASURED"

        measured_zz: List[float] = []
        measured_z1: List[float] = []
        for idx in range(NUM_BANDS):
            counts = self.qam._extract_counts(res, pub_index=idx, qubits=2)
            obs = _parity_and_partner_expectation(counts)
            measured_zz.append(obs["zz"])
            measured_z1.append(obs["z1"])

        pearson_zz = _pearson_r(ideal, measured_zz)
        pearson_z1 = _pearson_r(ideal, measured_z1)
        ideal_norm = float(np.dot(ideal, ideal))
        contrast_a = float(np.dot(ideal, measured_zz) / ideal_norm) if ideal_norm > 0 else 0.0

        return {
            "data": data,
            "qubits": 2,
            "num_bands": NUM_BANDS,
            "shots": shots,
            "pearson": pearson_zz,
            "pearson_partner_marginal": pearson_z1,
            "contrast_a": contrast_a,
            "ideal_zz": ideal,
            "measured_zz": measured_zz,
            "measured_z1": measured_z1,
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backend": backend_name,
            "result_type": result_type,
            "evidence_grade": evidence_grade,
            "operation": "wave_quantum_encoding",
        }


if __name__ == "__main__":
    wq = QAMQuantum(local=True)
    out = wq.wave_quantum_encoding("QAM_WAVE_DATA", shots=1024)
    print(f"Pearson r = {out['pearson']:.4f}, contrast A = {out['contrast_a']:.4f} ({out['result_type']})")
