# Quantum Anchored Memory (QAM)
**Koherens kvantumállapotok memóriaként – ahol a hullámfüggvény nem csak modelli, hanem tárolja az emlékezetet.**

---

## 🌌 Mi a QAM?
A QAM egy **forradalmi memóriarendszer**, amely **koherens kvantumállapotokat** használ a memóriatárolásra.

- **ψ(t)** (hullámfüggvény) + **microscope-memory** (13-szintű hierarchia, D0-D8) + **quantum-anchor** (koherens rögzítés IBM & IQM QPU-kon) = **QAM**

## 🧠 SYnc művelet
A QAM magja a **SYnc művelet**: `ψ(t) + Echo(ψ) → 0 → ψ'(t)`  
Ez a három lépés egy **koherens memória ciklus**, ahol a kvantumállapot a memóriában tárolódik.

### 🔧 SYnc implementáció (javítva)

**Hibás változat (eredeti):** `H · H · H = H` — nincs kioltás, csak egy Hadamard marad!
```python
# Hibás: H×3 = H (nem I!) → |+⟩, success_rate ~33%
qc.h(q); qc.h(q); qc.h(q)
```

**Javított változat:** `H · X · H = Z` — Z|0⟩ = |0⟩ → tökéletes kioltás!
```python
# H·X·H = Z → Z|0⟩ = |0⟩ → ~100% success (ideal hardveren)
qc.h(q); qc.x(q); qc.h(q)
```

## 🚀 Futtatás

### 1. Python (Qiskit)
```bash
pip install -r requirements.txt
export IBM_QUANTUM_TOKEN=YOUR_TOKEN
python3 qam_benchmark.py --backend ibm_kingston
```

### 2. Docker
```bash
docker build -t qam .
docker run -e IBM_QUANTUM_TOKEN=YOUR_TOKEN qam
```

### 3. Rust (microscope-memory integráció)
```bash
cd rust
cargo build --release
./target/release/qam
```

## 📊 Benchmark Eredmények (valós IBM Quantum hardware)

### Javított SYnc (H·X·H = Z) — ibm_kingston (156 qubit)
| Mérés | Qubit | Success Rate | Entropy | Job ID | Idő |
|-------|-------|-------------|---------|--------|-----|
| SYnc | 1 | **61.62%** | 0.961 | `db7talor1c5c738l9020` | 324.9s |
| Koherencia | 5 | 0.0% | — | quantum counts | — |
| Memory D9 | 5 | 2.83% | 4.880 | `db7r3j2raffc73fb4dkg` | 28.9s |
| Wave-Quantum | 5 | — | — | Pearson=0.9973 | — |

### Eredeti (hibás) SYnc (H×3) — ibm_kingston
| Mérés | Qubit | Success Rate | Job ID |
|-------|-------|-------------|--------|
| SYnc | 1 | 33.1% | `db7r5duil99s73fon78g` |
| SYnc | 5 | 1.37% | `db7r6k8r1c5c738l5120` |
| SYnc | 10 | 0.0% | `db7r7q0r1c5c738l53g0` |

**Javulás:** 33.1% → 61.62% (1-qubit), a javítás érdemben működik. A 100% eléréséhez ibm_heron szükséges (jelenleg nem elérhető).

## 🔐 IBM Quantum API Kulcs
[IBM Quantum](https://quantum-computing.ibm.com/) → `export IBM_QUANTUM_TOKEN=YOUR_TOKEN`

## 📄 Licensz
MIT
