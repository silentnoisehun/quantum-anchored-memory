"""
QAM Core — SYnc Operation: ψ(t) + Echo(ψ) → |0⟩
================================================
Implements the Loschmidt Echo SYnc operation and interferometric coherence
checks for Quantum Anchored Memory (QAM).

Two critical hardware rules (established on ibm_kingston, 156Q Heron r2):
  1. optimization_level=0 — preserves U and U† gates (opt_level=3 cancels
     U·U† = I at compile time and measures only readout floor).
  2. initial_layout — selects calibrated physical qubits (legacy
     backend.properties() returns -1 on Heron backends, causing naive
     opt_level=0 transpilation to pick physical qubit 0 with ~49% readout).

Simulation results (StatevectorSampler) validate circuit mathematics ONLY and
never constitute hardware evidence.
"""

from __future__ import annotations

import dataclasses as _dc
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --- Python 3.14 + pydantic + qiskit-ibm-runtime compatibility shim ---
_orig_fields = _dc.fields


def _patched_fields(cls: Any):
    try:
        return _orig_fields(cls)
    except (AttributeError, TypeError):
        try:
            fields_dict = cls.__dataclass_fields__
            if isinstance(fields_dict, dict):
                return tuple(
                    f
                    for f in fields_dict.values()
                    if getattr(f, "_field_type", _dc._FIELD) is _dc._FIELD
                )
        except Exception:
            pass
        return ()


_dc.fields = _patched_fields
# --- End compatibility shim ---

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.primitives import StatevectorSampler


def wilson_ci(successes: int, total: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    """Compute the Wilson score 95% confidence interval for a binomial proportion."""
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    half_width = (
        z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * total)) / total) / denom
    )
    return (max(0.0, center - half_width), min(1.0, center + half_width))


def shannon_entropy(counts: Dict[str, int], total_shots: int) -> float:
    """Compute Shannon entropy (in bits) of a measurement bitstring distribution."""
    if total_shots <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total_shots
            entropy -= p * math.log2(p)
    return entropy


def resolve_ibm_token(explicit_token: Optional[str] = None) -> Optional[str]:
    """
    Resolve an IBM Quantum API token strictly from safe sources:
      1. Explicit programmatic argument (never pass secrets via CLI flags)
      2. IBM_QUANTUM_TOKEN or IBM_QUANTUM_API_TOKEN environment variable
      3. IBM_TOKEN_PATH environment variable pointing to a JSON file
      4. Untracked local ibm_token.json or apikey.json in the current directory
    """
    if explicit_token:
        return explicit_token.strip()

    for env_name in ("IBM_QUANTUM_TOKEN", "IBM_QUANTUM_API_TOKEN"):
        val = os.environ.get(env_name, "").strip()
        if val:
            return val

    candidate_paths: List[Path] = []
    token_path_env = os.environ.get("IBM_TOKEN_PATH", "").strip()
    if token_path_env:
        candidate_paths.append(Path(token_path_env))
    candidate_paths.extend([Path("ibm_token.json"), Path("apikey.json")])

    for path in candidate_paths:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                tok = (data.get("apikey") or data.get("token") or "").strip()
                if tok:
                    return tok
            except Exception:
                continue
    return None


def _run_runtime_sampler(backend: Any, circuits: Sequence[QuantumCircuit], shots: int) -> Tuple[Any, str]:
    """Submit circuits using SamplerV2 (preferred) with fallback to legacy Sampler."""
    try:
        from qiskit_ibm_runtime import SamplerV2 as RuntimeSampler

        sampler = RuntimeSampler(mode=backend)
        job = sampler.run(list(circuits), shots=shots)
    except ImportError:
        from qiskit_ibm_runtime import Sampler as LegacySampler

        sampler = LegacySampler(backend)
        job = sampler.run(list(circuits), shots=shots)

    result = job.result()
    job_id = job.job_id() if hasattr(job, "job_id") else "unknown"
    return result, str(job_id)


class QAM:
    """Quantum Anchored Memory circuit runner (IBM Heron QPU or local StatevectorSampler)."""

    def __init__(
        self,
        token: Optional[str] = None,
        backend: str = "ibm_kingston",
        local: bool = False,
    ) -> None:
        if backend == "ibm_heron":
            raise ValueError(
                "'ibm_heron' is a processor family, not a backend name. "
                "Use 'ibm_kingston', 'ibm_fez', or 'ibm_marrakesh'."
            )
        self.backend_name = backend
        self.local = local
        self.token = None if local else resolve_ibm_token(token)
        self.service = None
        self.backend = None

        if self.token and not self.local:
            try:
                from qiskit_ibm_runtime import QiskitRuntimeService

                try:
                    self.service = QiskitRuntimeService(
                        channel="ibm_quantum_platform",
                        token=self.token,
                        instance="auto",
                    )
                except Exception:
                    self.service = QiskitRuntimeService(token=self.token, instance="auto")
                self.backend = self.service.backend(self.backend_name)
            except Exception as exc:
                print(f"  ⚠️  Backend connection failed ({exc}); falling back to local simulator.", flush=True)
                self.service = None
                self.backend = None

    @staticmethod
    def build_loschmidt_circuits(
        qubits: int = 1,
        seed: int = 42,
    ) -> Tuple[QuantumCircuit, QuantumCircuit, List[Dict[str, float]]]:
        """
        Build paired Loschmidt Echo (U · U†) and Control (U only) circuits.
        Uses an isolated RandomState(seed) so seed=42 reproduces the exact
        ibm_kingston benchmark angles (theta=2.3533, phi=5.9735, lam=4.5993).
        """
        if qubits < 1:
            raise ValueError("qubits must be >= 1")

        rng = np.random.RandomState(seed)
        qc_sync = QuantumCircuit(qubits)
        qc_ctrl = QuantumCircuit(qubits)
        angles: List[Dict[str, float]] = []

        for q in range(qubits):
            theta = float(rng.uniform(0.0, 2.0 * np.pi))
            phi = float(rng.uniform(0.0, 2.0 * np.pi))
            lam = float(rng.uniform(0.0, 2.0 * np.pi))
            angles.append(
                {
                    "qubit": q,
                    "theta": theta,
                    "phi": phi,
                    "lam": lam,
                    "expected_control_p0": float(math.cos(theta / 2.0) ** 2),
                }
            )
            qc_sync.u(theta, phi, lam, q)
            qc_sync.barrier(q)
            qc_sync.u(theta, phi, lam, q).inverse()
            qc_sync.barrier(q)

            qc_ctrl.u(theta, phi, lam, q)
            qc_ctrl.barrier(q)

        qc_sync.measure_all()
        qc_ctrl.measure_all()
        return qc_sync, qc_ctrl, angles

    def select_good_qubits(self, qubits: int) -> Optional[List[int]]:
        """
        Auto-select `qubits` calibrated physical qubits when legacy
        backend.properties() returns -1 on Heron processors.
        """
        if self.backend is None:
            return None

        # 1. Prefer Qiskit 2.x Target error metadata if available
        try:
            target = getattr(self.backend, "target", None)
            if target is not None and getattr(target, "num_qubits", 0) >= qubits:
                scored: List[Tuple[float, int]] = []
                measure_props = target.get("measure", {}) if hasattr(target, "get") else {}
                sx_props = target.get("sx", {}) if hasattr(target, "get") else {}
                for q in range(target.num_qubits):
                    m_prop = measure_props.get((q,))
                    sx_prop = sx_props.get((q,))
                    m_err = getattr(m_prop, "error", None)
                    s_err = getattr(sx_prop, "error", None)
                    if m_err is not None and m_err >= 0:
                        score = float(m_err) + 10.0 * float(s_err if (s_err is not None and s_err >= 0) else 0.0)
                        scored.append((score, q))
                if len(scored) >= qubits:
                    scored.sort(key=lambda item: item[0])
                    return [q for _, q in scored[:qubits]]
        except Exception:
            pass

        # 2. Fallback: probe transpiler layout selection at optimization_level=3
        try:
            qc_probe = QuantumCircuit(qubits)
            for q in range(qubits):
                qc_probe.sx(q)
            qc_probe.measure_all()
            tqc_probe = transpile(
                qc_probe,
                self.backend,
                optimization_level=3,
                seed_transpiler=42,
            )
            if tqc_probe.layout is not None:
                vbits = tqc_probe.layout.initial_layout.get_virtual_bits()
                selected = [
                    int(phys)
                    for virt, phys in vbits.items()
                    if getattr(virt, "_register", None) is None
                    or "ancilla" not in getattr(virt._register, "name", "")
                ]
                if len(selected) >= qubits:
                    return selected[:qubits]
        except Exception:
            pass

        return None

    def sync_operation(
        self,
        qubits: int = 1,
        shots: int = 1024,
        opt_level: int = 0,
        initial_layout: Optional[Sequence[int]] = None,
        seed: int = 42,
        include_control: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute the Loschmidt Echo SYnc operation: U(θ, φ, λ) · U(θ, φ, λ)† |0⟩ → |0⟩.
        Preserves all physical gates at opt_level=0 and measures P(|0...0⟩).
        """
        qc_sync, qc_ctrl, angles = self.build_loschmidt_circuits(qubits=qubits, seed=seed)
        zero_key = "0" * qubits
        expected_ctrl_p0 = 1.0
        for item in angles:
            expected_ctrl_p0 *= item["expected_control_p0"]

        if self.backend is None:
            return self._run_local_sync(
                qc_sync=qc_sync,
                qc_ctrl=qc_ctrl,
                qubits=qubits,
                shots=shots,
                seed=seed,
                expected_ctrl_p0=expected_ctrl_p0,
                include_control=include_control,
            )

        chosen_layout = list(initial_layout) if initial_layout is not None else self.select_good_qubits(qubits)
        transpile_kwargs: Dict[str, Any] = {
            "optimization_level": opt_level,
            "seed_transpiler": seed,
        }
        if chosen_layout is not None:
            transpile_kwargs["initial_layout"] = chosen_layout

        tqc_sync = transpile(qc_sync, self.backend, **transpile_kwargs)
        circuits_to_run = [tqc_sync]
        if include_control:
            tqc_ctrl = transpile(qc_ctrl, self.backend, **transpile_kwargs)
            circuits_to_run.append(tqc_ctrl)

        start = time.perf_counter()
        result, job_id = _run_runtime_sampler(self.backend, circuits_to_run, shots=shots)
        elapsed_s = time.perf_counter() - start

        counts = self._extract_counts(result, pub_index=0, qubits=qubits)
        returned_shots = sum(counts.values())
        zero_hits = counts.get(zero_key, 0)
        success_rate = zero_hits / returned_shots if returned_shots > 0 else 0.0
        ci_low, ci_high = wilson_ci(zero_hits, returned_shots)

        payload: Dict[str, Any] = {
            "qubits": qubits,
            "requested_shots": shots,
            "returned_shots": returned_shots,
            "shots": returned_shots,
            "opt_level": opt_level,
            "initial_layout": chosen_layout,
            "time_us": elapsed_s * 1e6,
            "success_rate": success_rate,
            "wilson_95_ci": [ci_low, ci_high],
            "entropy": shannon_entropy(counts, returned_shots),
            "counts": counts,
            "expected_control_p0": expected_ctrl_p0,
            "job_id": job_id,
            "backend": getattr(self.backend, "name", str(self.backend)),
            "result_type": "quantum",
            "evidence_grade": "HARDWARE_MEASURED",
        }

        if include_control:
            ctrl_counts = self._extract_counts(result, pub_index=1, qubits=qubits)
            ctrl_total = sum(ctrl_counts.values())
            ctrl_zero = ctrl_counts.get(zero_key, 0)
            payload["control"] = {
                "p0": ctrl_zero / ctrl_total if ctrl_total > 0 else 0.0,
                "expected_p0": expected_ctrl_p0,
                "counts": ctrl_counts,
                "returned_shots": ctrl_total,
            }
        return payload

    def coherence_test(
        self,
        qubits: int = 5,
        shots: int = 1024,
        seed: int = 42,
        initial_layout: Optional[Sequence[int]] = None,
    ) -> Dict[str, Any]:
        """
        Interferometric phase-coherence test: H^{⊗n} → barrier → H^{⊗n} → measure.
        At optimization_level=0 all Hadamard gates execute physically; ideal
        constructive/destructive interference returns |0...0⟩ with P = 1.0,
        whereas complete dephasing yields 2^{-n}.
        """
        if qubits < 1:
            raise ValueError("qubits must be >= 1")

        qc = QuantumCircuit(qubits)
        for q in range(qubits):
            qc.h(q)
        qc.barrier()
        for q in range(qubits):
            qc.h(q)
        qc.barrier()
        qc.measure_all()

        zero_key = "0" * qubits

        if self.backend is None:
            sampler = StatevectorSampler(seed=seed)
            start = time.perf_counter()
            res = sampler.run([qc], shots=shots).result()
            elapsed_s = time.perf_counter() - start
            counts = self._extract_counts(res, pub_index=0, qubits=qubits)
            returned_shots = sum(counts.values())
            zero_hits = counts.get(zero_key, 0)
            coherence = zero_hits / returned_shots if returned_shots > 0 else 0.0
            return {
                "qubits": qubits,
                "shots": returned_shots,
                "coherence": coherence,
                "wilson_95_ci": list(wilson_ci(zero_hits, returned_shots)),
                "entropy": shannon_entropy(counts, returned_shots),
                "dephased_floor": 2.0 ** (-qubits),
                "counts_sample": dict(list(counts.items())[:5]),
                "time_us": elapsed_s * 1e6,
                "backend": "statevector_simulator",
                "result_type": "simulated",
                "evidence_grade": "SIMULATION_ONLY",
            }

        chosen_layout = list(initial_layout) if initial_layout is not None else self.select_good_qubits(qubits)
        transpile_kwargs: Dict[str, Any] = {
            "optimization_level": 0,
            "seed_transpiler": seed,
        }
        if chosen_layout is not None:
            transpile_kwargs["initial_layout"] = chosen_layout

        tqc = transpile(qc, self.backend, **transpile_kwargs)
        start = time.perf_counter()
        result, job_id = _run_runtime_sampler(self.backend, [tqc], shots=shots)
        elapsed_s = time.perf_counter() - start
        counts = self._extract_counts(result, pub_index=0, qubits=qubits)
        returned_shots = sum(counts.values())
        zero_hits = counts.get(zero_key, 0)
        coherence = zero_hits / returned_shots if returned_shots > 0 else 0.0

        return {
            "qubits": qubits,
            "shots": returned_shots,
            "initial_layout": chosen_layout,
            "coherence": coherence,
            "wilson_95_ci": list(wilson_ci(zero_hits, returned_shots)),
            "entropy": shannon_entropy(counts, returned_shots),
            "dephased_floor": 2.0 ** (-qubits),
            "counts_sample": dict(list(counts.items())[:5]),
            "time_us": elapsed_s * 1e6,
            "job_id": job_id,
            "backend": getattr(self.backend, "name", str(self.backend)),
            "result_type": "quantum",
            "evidence_grade": "HARDWARE_MEASURED",
        }

    def _run_local_sync(
        self,
        qc_sync: QuantumCircuit,
        qc_ctrl: QuantumCircuit,
        qubits: int,
        shots: int,
        seed: int,
        expected_ctrl_p0: float,
        include_control: bool,
    ) -> Dict[str, Any]:
        """Run actual StatevectorSampler simulation (not hardcoded constants)."""
        sampler = StatevectorSampler(seed=seed)
        circuits = [qc_sync, qc_ctrl] if include_control else [qc_sync]
        start = time.perf_counter()
        res = sampler.run(circuits, shots=shots).result()
        elapsed_s = time.perf_counter() - start

        zero_key = "0" * qubits
        counts = self._extract_counts(res, pub_index=0, qubits=qubits)
        returned_shots = sum(counts.values())
        zero_hits = counts.get(zero_key, 0)
        success_rate = zero_hits / returned_shots if returned_shots > 0 else 0.0
        ci_low, ci_high = wilson_ci(zero_hits, returned_shots)

        payload: Dict[str, Any] = {
            "qubits": qubits,
            "requested_shots": shots,
            "returned_shots": returned_shots,
            "shots": returned_shots,
            "opt_level": 0,
            "initial_layout": None,
            "time_us": elapsed_s * 1e6,
            "success_rate": success_rate,
            "wilson_95_ci": [ci_low, ci_high],
            "entropy": shannon_entropy(counts, returned_shots),
            "counts": counts,
            "expected_control_p0": expected_ctrl_p0,
            "job_id": f"local-statevector-{seed}",
            "backend": "statevector_simulator",
            "result_type": "simulated",
            "evidence_grade": "SIMULATION_ONLY",
        }

        if include_control:
            ctrl_counts = self._extract_counts(res, pub_index=1, qubits=qubits)
            ctrl_total = sum(ctrl_counts.values())
            ctrl_zero = ctrl_counts.get(zero_key, 0)
            payload["control"] = {
                "p0": ctrl_zero / ctrl_total if ctrl_total > 0 else 0.0,
                "expected_p0": expected_ctrl_p0,
                "counts": ctrl_counts,
                "returned_shots": ctrl_total,
            }
        return payload

    @staticmethod
    def _extract_counts(result: Any, pub_index: int = 0, qubits: int = 1) -> Dict[str, int]:
        """Extract bitstring counts across Qiskit 2.x SamplerV2, StatevectorSampler, and legacy APIs."""
        pub = result[pub_index]
        data_bin = getattr(pub, "data", None)
        if data_bin is not None:
            for attr in ("meas", "c"):
                reg = getattr(data_bin, attr, None)
                if reg is not None and hasattr(reg, "get_counts"):
                    return dict(reg.get_counts())
            # Generic DataBin attribute scan (handles renamed classical registers)
            for name in dir(data_bin):
                if name.startswith("_"):
                    continue
                reg = getattr(data_bin, name, None)
                if reg is not None and hasattr(reg, "get_counts"):
                    return dict(reg.get_counts())

        if hasattr(result, "quasi_dists"):
            qd = result.quasi_dists[pub_index]
            return {format(int(k), f"0{qubits}b"): int(round(v * 1024)) for k, v in qd.items()}

        if hasattr(pub, "get_counts"):
            return dict(pub.get_counts())

        raise RuntimeError("Unable to extract bitstring counts from sampler result")


if __name__ == "__main__":
    qam = QAM(local=True)
    out = qam.sync_operation(qubits=1, shots=1024, include_control=True)
    print(json.dumps(out, indent=2))
