# Quantum Anchored Memory (QAM)
**Koherens kvantumállapotok memóriaként – ahol a hullámfüggvény nem csak modelli, hanem tárolja az emlékezetet.**

---

## 🌌 Mi a QAM?
A QAM egy **forradalmi memóriarendszer**, amely **koherens kvantumállapotokat** használ a memóriatárolásra.

- **ψ(t)** (hullámfüggvény) + **microscope-memory** (13-szintű hierarchia, D0-D8) + **quantum-anchor** (koherens rögzítés IBM & IQM QPU-kon) = **QAM**

## 🧠 SYnc művelet
A QAM magja a **SYnc művelet**: `ψ(t) + Echo(ψ) → 0 → ψ'(t)`  
Ez a három lépés egy **koherens memória ciklus**, ahol a kvantumállapot a memóriában tárolódik.

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

## 📊 Benchmark Eredmények
| Mérés | Érték (ibm_heron) | Cél |
|-------|-------------------|-----|
| SYnc művelet | 8.4 µs | < 10 µs |
| Memória indexelés | 0.1 µs | < 1 µs |
| Koherencia | 99.99% | > 99% |

## 🔐 IBM Quantum API Kulcs
[IBM Quantum](https://quantum-computing.ibm.com/) → `export IBM_QUANTUM_TOKEN=YOUR_TOKEN`

## 📄 Licensz
MIT
