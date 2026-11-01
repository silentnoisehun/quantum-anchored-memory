# Quantum Anchored Memory (QAM)

> **🔬 Researcher Note & Evidence Summary**
> *Author:* Máté Róbert ([ORCID: 0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))
> *Repository:* [`silentnoisehun/quantum-anchored-memory`](https://github.com/silentnoisehun/quantum-anchored-memory)
> *Hardware:* IBM Quantum `ibm_kingston` (156-qubit Heron r2 superconducting QPU)
> *Primary Hardware Result:* **1-qubit `U·U†` Loschmidt Echo (`opt_level=0`, physical qubit 91) = 99.41% (1018/1024, Wilson 95% CI [98.73%, 99.73%])** vs. `U|0⟩` control **15.33%** (157/1024; analytical `cos²(θ/2) = 14.75%`).
>
> Every project in the [Quantum Memory Research Series](#-quantum-memory-research-series) follows the same evidence standard: **calibration → execution → diagnosis → verification**, strictly separating classical/simulator checks from real QPU measurements.

---

## 🌌 Overview & Evidence Boundary

**Quantum Anchored Memory (QAM)** explores pairing coherent quantum state verification (`SYnc` / Loschmidt Echo) with a deterministic 9-level hierarchical memory architecture (`D0–D8` zoom levels with Merkle integrity) and 13-band wave-packet encoding.

### What is hardware-proven here — and what is classical/architectural

| Component | Status | Evidence Grade | Source |
|---|---|---|---|
| **1Q `U·U†` Loschmidt Echo (`opt_level=0`, `q91`)** | **99.41%** (1018/1024) vs **15.33%** control | 📬 **HARDWARE MEASURED** | `ibm_kingston`, Jobs `db7viu8r1c5c738ldhi0` & `db7vj1gr1c5c738ldhng` |
| **1Q `X·X = I` layout diagnosis (`opt_level=0`)** | `q0` (auto): **49.32%** → `q91` (forced): **99.32%** | 📬 **HARDWARE MEASURED** | `results/qam_diagnosis.json`, `results/qam_real_results.json` |
| **1Q / 5Q / 10Q `H·X·H → RZ(π)` (`opt_level=3`)** | **99.80%** (1Q), **98.93%** (5Q), **98.34%** (10Q) | 📬 **HARDWARE MEASURED** *(virtual Z readout floor)* | `ibm_kingston`, Jobs `db7tthor1c5c738la3ig`, `db7ufs6il99s73fotfcg`, `db7ugt0r1c5c738lb9a0` |
| **D0–D8 zoom memory + Merkle verification (`src/qam_memory.py`, `rust/`)** | Deterministic 9-level projections + tamper check | ✅ **PROVEN (classical)** | Unit-tested in `tests/test_qam.py` & `rust/src/lib.rs` |
| **13-band Wave-Quantum Rabi parity (`src/qam_quantum.py`)** | `⟨Z₀Z₁⟩ = cos(2πk/13)` sweep (`r > 0.995` in sim) | ✅ **PROVEN (simulation here; QPU-validated in [`wave-quantum`](https://github.com/silentnoisehun/wave-quantum))** | `src/qam_quantum.py` |
| **Time-delayed `U–delay(τ)–U†` echo sweep** | Evaluated in dedicated follow-up repo (`T₂_eff = 89.6 ± 17.5 µs`) | 📬 **MEASURED IN [`quantum-delayed-sync`](https://github.com/silentnoisehun/quantum-delayed-sync)** | 5 runs on `ibm_kingston` `q91` |

> **⚠️ Methodological note on earlier v0.1 benchmark rows:** In the initial prototype (`results/qam_real_results.json`), `coherence_test` evaluated `1 - len(counts)/32` on `H^{⊗5}|0⟩` (which trivially yields `0.0%` for an ideal uniform superposition), `Memory D9` ran 5-qubit `opt_level=0` without `initial_layout` (`2.83%` due to uncalibrated qubit 0), and `qam_quantum.py` returned a synthetic random placeholder. In v0.2.0, all three modules have been replaced with real circuit/Merkle implementations and explicit `HARDWARE_MEASURED` vs `SIMULATION_ONLY` tags, while keeping all original `results/*.json` artifacts untouched for auditability.

---

## 🧠 The SYnc Operation & Calibration Diagnosis

The `SYnc` verification prepares `ψ = U(θ, φ, λ)|0⟩` and applies the time-reversed inverse `U†`:

```
U(θ, φ, λ) · U(θ, φ, λ)† |0⟩ = |0⟩
```

### Phase 1–3 Progression (`H·X·H` prototype on `ibm_kingston`)

| Phase | Circuit | Qubits | `P(0^n)` | Counts | Job ID | Notes |
|---|---|---|---|---|---|---|
| ❌ Broken v0 | `H·H·H = H` | 1 | 33.11% | 339/1024 | `db7r5duil99s73fon78g` | Leaves qubit in `\|+⟩`, no echo |
| ⚠️ Unoptimized | `H·X·H = Z` | 1 | 61.62% | 631/1024 | `db7talor1c5c738l9020` | Uncalibrated default qubit |
| ✅ Virtual-Z (`opt=3`) | `H·X·H → RZ(π)` | 1 | **99.80%** | 1022/1024 | `db7tthor1c5c738la3ig` | Transpiler compiles to virtual `RZ` (readout floor) |
| ✅ Virtual-Z (`opt=3`) | `H·X·H → RZ(π)` | 5 | **98.93%** | 1013/1024 | `db7ufs6il99s73fotfcg` | 5-qubit readout floor |
| ✅ Virtual-Z (`opt=3`) | `H·X·H → RZ(π)` | 10 | **98.34%** | 1007/1024 | `db7ugt0r1c5c738lb9a0` | 10-qubit readout floor |

### Real Gate-Preserving Loschmidt Echo (`opt_level=0`, 10 physical native gates)

At `optimization_level=3`, Qiskit algebraically cancels `U·U† = I` before execution. A genuine hardware test requires **`optimization_level=0`** (preserving all `6 rz + 4 sx` physical native gates) **plus explicit `initial_layout` selection**:

| Test | Physical Qubit | Native Gates | `P(0)` | Wilson 95% CI | Counts | Job ID |
|---|---|---|---|---|---|---|
| `X·X = I` (Statevector) | sim | 2 `x` | 100.00% | — | 1024×`0` | local |
| `X·X = I` (`opt=0`, auto) | **0** (bad) | 2 `x` | 49.32% | [46.26%, 52.38%] | 505×`0`, 519×`1` | diagnosis |
| `X·X = I` (`opt=0`, forced) | **91** (good) | 2 `x` | **99.32%** | [98.60%, 99.67%] | 1017×`0`, 7×`1` | diagnosis |
| `U·U†` Echo (`opt=0`, auto) | **0** (bad) | `6 rz + 4 sx` | 45.31% | [42.29%, 48.37%] | 464×`0`, 560×`1` | `db7uus8r1c5c738lc8i0` |
| **Control `U\|0⟩` (`opt=0`)** | **91** | `3 rz + 2 sx` | **15.33%** | [13.26%, 17.67%] | 157×`0`, 867×`1` | `db7vj1gr1c5c738ldhng` |
| **Real SYnc `U·U†` (`opt=0`)** | **91** | `6 rz + 4 sx` | **99.41%** | **[98.73%, 99.73%]** | **1018×`0`, 6×`1`** | `db7viu8r1c5c738ldhi0` |

**Root cause discovered:** Legacy `backend.properties()` returns `-1` on Heron backends (`ibm_kingston`), causing `transpile(..., optimization_level=0)` without `initial_layout` to default to physical qubit `0`. Selecting calibrated physical qubits via Qiskit's `Target` error map (or `opt_level=3` layout probing) restores **99.41%** fidelity (`6.48×` over the `15.33%` `U|0⟩` control, which matches `cos²(2.3533/2) = 14.75%` within `0.53σ`).

---

## ⚙️ Quick Start & Verification

### 1. Offline Audit & Test Suite (0 quota, no API token needed)

```bash
pip install -r requirements.txt pytest

# Verify committed IBM Heron hardware JSON records & Wilson 95% CIs
python verify_results.py

# Check repository hygiene (no personal paths, no leaked secrets, no --token CLI flags)
python scripts/check_hygiene.py

# Run unit & StatevectorSampler test suite
pytest -v

# Run local StatevectorSampler benchmark (explicitly tagged SIMULATION_ONLY)
python -m src.qam_benchmark --local
```

### 2. Real IBM Quantum QPU Execution

Never pass API tokens on the command line (they persist in shell history and process tables). Export `IBM_QUANTUM_TOKEN` in the environment:

```bash
export IBM_QUANTUM_TOKEN="<YOUR_IBM_QUANTUM_TOKEN>"

# 1. Calibration sanity check (X·X=I and RY·RY†=I on physical qubit 91)
python calibration_test.py --backend ibm_kingston --qubit 91

# 2. Gate-preserving Loschmidt Echo + Control verification
python sync_real_test.py --backend ibm_kingston --qubit 91

# 3. Full QAM benchmark suite
python -m src.qam_benchmark --backend ibm_kingston
```

> **Note:** `ibm_heron` refers to the processor architecture, not a backend name. Valid Heron backends include `ibm_kingston`, `ibm_fez`, and `ibm_marrakesh`.

### 3. Rust Core (`WavePacket` + `D0–D8` Merkle Hierarchy + Hardware Audit)

```bash
cargo test --manifest-path rust/Cargo.toml
cargo run --release --manifest-path rust/Cargo.toml
```

### 4. Docker

```bash
docker build -t qam .
# Local simulation mode (no token):
docker run --rm qam --local
# Real QPU mode:
docker run --rm -e IBM_QUANTUM_TOKEN="$IBM_QUANTUM_TOKEN" qam --backend ibm_kingston
```

---

## 🔗 Quantum Memory Research Series

This repository is part of a six-repository research series investigating wave-packet encoding, coherent state anchoring, decoherence drift, and quantum-classical feedback loops on superconducting QPUs:

| # | Repository | Role in Series | Key Hardware Result |
|---|---|---|---|
| 1 | **[`scs-quantum`](https://github.com/silentnoisehun/scs-quantum)** | Foundational 2-qubit `(A, f, φ)` wave-packet bridge (`RY` + `CNOT`) & 4 measurement rules | `ibm_marrakesh` Bell balance **87.7–99.3%** across 7 runs (median **94.9%**), GHZ **89.3–96.7%** |
| 2 | **[`quantum-anchored-memory`](https://github.com/silentnoisehun/quantum-anchored-memory)** *(this repo)* | Gate-preserving `U·U†` Loschmidt Echo diagnosis (`opt_level=0` + layout calibration) & `D0–D8` Merkle memory | `ibm_kingston` (`q91`) `U·U†` **99.41%** vs `U\|0⟩` control **15.33%** (`q0` uncalibrated: 45.31%) |
| 3 | **[`quantum-anchor`](https://github.com/silentnoisehun/quantum-anchor)** | Post-pulse anchoring protocol & Tesseract V1–V3 interferometric audit (`ibm_marrakesh` & `IQM Garnet 20Q`) | Tesseract-V2 8Q GHZ **83.01%**; V3 5-phase sweep **0.20–1.37%** (Grade C: below hardware noise floor; weak-drive T1/T2 compensation **not proven**) |
| 4 | **[`wave-quantum`](https://github.com/silentnoisehun/wave-quantum)** | 13-band Rabi parity curves across 1Q / 2Q / 14Q chains (`ibm_fez`, `ibm_marrakesh`, `ibm_kingston`) + Heisenberg reduction proof | `⟨Z₀Z₁⟩ → ⟨Z₁⟩ = cos(2πk/13)`, Pearson **r = 0.873–0.9998**, 2Q `χ²_red = 0.82` |
| 5 | **[`quantum-delayed-sync`](https://github.com/silentnoisehun/quantum-delayed-sync)** | Time-delayed `U–delay(τ)–U†` vs `T₁` control-arm timescale arbitration (0–800 µs) | `ibm_kingston` (`q91`, 5 runs): `T₂_eff = 89.6 ± 17.5 µs` (SD `39.2 µs` < calibrated `121.3 µs`); cross-repo drift falsified on `wave-quantum` (`r = 0.9994 ± 0.00013`) |
| 6 | **[`quantum-organic-intelligence`](https://github.com/silentnoisehun/quantum-organic-intelligence)** | Closed-loop 2D Gross–Pitaevskii (`fluid-stratos` FFT) + 2-qubit quantum bridge on `ibm_fez` | 91 hardware loop iterations (68+20+3): live `c` tracks drift (`0.917–0.953`), raw `A` MAE `0.026`, 7/16 modes visited vs 1 classical mode, 16-mode argmax `0/6` (shot-noise limited) |

---

## 📁 Project Structure

```text
quantum-anchored-memory/
├── src/
│   ├── qam_core.py          # Loschmidt Echo (U·U†), Target/layout selection, Wilson CI, SamplerV2
│   ├── qam_memory.py        # 9-level (D0–D8) zoom projections + SHA-256 Merkle integrity
│   ├── qam_quantum.py       # 13-band 2-qubit Wave-Quantum Rabi parity sweep
│   ├── qam_benchmark.py     # Unified CLI benchmark (--local or real IBM Heron QPU)
│   └── qam_test.py          # Smoke runner
├── rust/                    # Rust library + CLI (WavePacket, D0–D8 Merkle tree, SyncAudit)
├── scripts/
│   ├── check_hygiene.py     # Scans tracked files for personal paths, leaked keys & --token flags
│   └── retrieve_job.py      # Zero-quota IBM Quantum job recovery utility
├── tests/
│   └── test_qam.py          # Automated pytest suite (math, circuits, tamper check, hygiene)
├── results/                 # Committed IBM Heron (ibm_kingston) raw & diagnostic JSON records
├── calibration_test.py      # X·X=I and RY·RY†=I sanity check (--local or QPU)
├── sync_real_test.py        # Paired Loschmidt Echo + Control verification
├── verify_results.py        # Stdlib-only verifier for committed hardware JSON records
├── CITATION.cff             # Citation metadata
├── .zenodo.json             # Zenodo archive metadata
└── Dockerfile               # Reproducible Python 3.12 + Rust container
```

## 📄 License

MIT — see [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff).
