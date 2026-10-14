"""
Diagnosztikai teszt: Statevector szimulátor + layout-átadás
1. Statevector: X·X=I szimuláció (exaktan 100% P(0) kell legyen)
2. Layout átadás: opt_level=3 → layout → opt_level=0 (kapuk megőrzve)
"""
import json, os, sys, numpy as np

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'
from src.qam_core import QAM  # monkeypatch FIRST

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')
qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend

from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import Sampler

# --- DIAGNOSIS 1: Statevector szimuláció ---
print(f'{"="*60}', flush=True)
print('DIAGNOSIS 1: Statevector szimulátor (X·X=I → exaktan 100%)', flush=True)

qc = QuantumCircuit(1)
qc.x(0); qc.x(0)
qc.measure_all()

try:
    from qiskit.quantum_info import Statevector
    sv = Statevector(qc)
    p0_sv = abs(sv.amplitudes[0])**2 * 100
    print(f'  Statevector P(0) = {p0_sv:.2f}% (expected 100%)', flush=True)
except Exception as e:
    print(f'  Statevector error: {e}', flush=True)
    p0_sv = -1

try:
    from qiskit_aer import AerSimulator
    sim = AerSimulator()
    tqc_sim = transpile(qc, sim)
    result = sim.run(tqc_sim, shots=1024).result()
    counts_sim = result.get_counts()
    p0_sim = counts_sim.get('0', 0) / sum(counts_sim.values()) * 100
    print(f'  AerSimulator P(0) = {p0_sim:.2f}% (expected ~100%)', flush=True)
    print(f'  Counts: {counts_sim}', flush=True)
except Exception as e:
    print(f'  AerSimulator error: {e}', flush=True)
    p0_sim = -1

# --- DIAGNOSIS 2: Layout átadás (opt=3 → opt=0) ---
print(f'\n{"="*60}', flush=True)
print('DIAGNOSIS 2: Layout átadás (opt=3 → opt=0)', flush=True)

# Step 1: Find good qubit via opt_level=3
tqc_opt3 = transpile(qc, backend, optimization_level=3, seed_transpiler=42)
layout_opt3 = tqc_opt3.layout
vbits_opt3 = layout_opt3.initial_layout.get_virtual_bits()
used_qubits_opt3 = [v for q, v in vbits_opt3.items() if 'ancilla' not in repr(q)]
good_qubit = used_qubits_opt3[0] if used_qubits_opt3 else 0
print(f'opt_level=3 → physical qubit: {good_qubit}', flush=True)
print(f'  gates: {dict(tqc_opt3.count_ops())}', flush=True)

# Step 2: Apply same qubit to opt_level=0
tqc_opt0 = transpile(qc, backend, optimization_level=0, seed_transpiler=42,
                     initial_layout=[good_qubit])
vbits_opt0 = tqc_opt0.layout.initial_layout.get_virtual_bits()
phys_opt0 = [v for q, v in vbits_opt0.items() if 'ancilla' not in repr(q)]
print(f'opt_level=0 forced qubit {good_qubit}: physical qubits = {phys_opt0}', flush=True)
print(f'  gates: {dict(tqc_opt0.count_ops())}', flush=True)

try:
    from qiskit.qasm2 import dumps
    qasm_str = dumps(tqc_opt0)
    print(f'\n  QASM:\n{qasm_str}', flush=True)
except Exception:
    try:
        qasm_str = tqc_opt0.qasm()
        print(f'\n  QASM:\n{qasm_str}', flush=True)
    except Exception:
        qasm_str = 'QASM not available'
        print(f'\n  QASM: not available', flush=True)

# Run on the good qubit
sampler = Sampler(backend)
job = sampler.run([tqc_opt0], shots=1024)
result = job.result()
counts2 = result[0].data.meas.get_counts()
p0_good = counts2.get('0', 0) / sum(counts2.values()) * 100
print(f'\n✅ X·X=I on good qubit {good_qubit}: P(0) = {p0_good:.2f}%', flush=True)
print(f'  Counts: {counts2}', flush=True)

# --- DIAGNOSIS 3: Compare qbit 0 vs good qubit ---
print(f'\n{"="*60}', flush=True)
print('DIAGNOSIS 3: qbit 0 vs good qubit (X·X=I, opt_level=0)', flush=True)

# qbit 0
tqc_q0 = transpile(qc, backend, optimization_level=0, seed_transpiler=42)
job_q0 = sampler.run([tqc_q0], shots=1024)
result_q0 = job_q0.result()
counts_q0 = result_q0[0].data.meas.get_counts()
p0_q0 = counts_q0.get('0', 0) / sum(counts_q0.values()) * 100
print(f'qbit 0 (auto): P(0) = {p0_q0:.2f}%  counts={counts_q0}', flush=True)

# good qubit
print(f'good qubit ({good_qubit}): P(0) = {p0_good:.2f}%  counts={counts2}', flush=True)

# --- SUMMARY ---
print(f'\n{"="*60}', flush=True)
print('DIAGNOSIS ÖSSZEFOGLALÓ:', flush=True)
print(f'  Statevector:     P(0) = {p0_sv:.2f}%  (szimulátor, exaktan 100%)', flush=True)
print(f'  AerSimulator:    P(0) = {p0_sim:.2f}%  (szimulátor)', flush=True)
print(f'  qbit 0 (hardware): P(0) = {p0_q0:.2f}%  (hardware)', flush=True)
print(f'  qbit {good_qubit} (hardware): P(0) = {p0_good:.2f}%  (hardware)', flush=True)

if p0_sv > 99 and p0_good > 95:
    diagnosis = 'HARDWARE ISSUE: qbit 0 bad, good qubit ({good_qubit}) gives ~99%. Fix: use initial_layout to force good qubit.'
elif p0_sv > 99 and p0_good < 50:
    diagnosis = 'PIPELINE ISSUE: even good qubit gives ~50%. monkeypatch or sampler bug.'
else:
    diagnosis = f'UNKNOWN: statevector={p0_sv}%, good_qubit={p0_good}%'

print(f'\n  Diagnózis: {diagnosis}', flush=True)

results = {
    'diagnosis': diagnosis,
    'statevector_p0': p0_sv,
    'aer_simulator_p0': p0_sim,
    'qbit0_hardware_p0': p0_q0,
    'good_qubit_hardware_p0': p0_good,
    'good_qubit': good_qubit,
    'good_qubit_gates': dict(tqc_opt0.count_ops()),
    'qbit0_gates': dict(tqc_q0.count_ops()),
    'qbit0_qubits': phys_opt0 if 'phys_opt0' in dir() else None,
}
with open('results/qam_diagnosis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f'\n✅ Mentve: results/qam_diagnosis.json', flush=True)
