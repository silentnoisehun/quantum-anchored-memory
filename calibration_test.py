"""
Kalibrációs teszt: egyszerű U·U† = I circuit.
Ha ez is ~50% lesz, a pipeline (monkeypatch / backend / sampler) hibás.
"""
import json, os, sys, numpy as np

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'
from src.qam_core import QAM  # applies monkeypatch FIRST

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')
qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend

from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import Sampler

print(f'✅ Backend: {backend.name}, {backend.num_qubits} qubits', flush=True)

# --- TEST 1: RY(pi/2) → RY(-pi/2) → measure (should be |0⟩ with ~98%) ---
print(f'\n{"="*50}', flush=True)
print('TEST 1: RY(π/2)·RY(-π/2) = I → |0⟩', flush=True)
qc1 = QuantumCircuit(1)
qc1.ry(np.pi/2, 0)
qc1.ry(-np.pi/2, 0)  # inverse, should cancel
qc1.measure_all()

tqc1 = transpile(qc1, backend, optimization_level=0, seed_transpiler=42)
print(f'QASM:\n{tqc1.qasm() if hasattr(tqc1, "qasm") else "[qiskit 2.x — no qasm()]"}', flush=True)
try:
    from qiskit.qasm2 import dumps
    print(f'QASM2:\n{dumps(tqc1)}', flush=True)
except:
    pass

# Get the physical qubit from the layout
try:
    vbits = tqc1.layout.initial_layout.get_virtual_bits()
    phys_qubits = [v for q, v in vbits.items() if 'ancilla' not in repr(q)]
    print(f'Physical qubit: {phys_qubits[:1]}', flush=True)
    # Check backend properties for that qubit
    props = backend.properties()
    if props and phys_qubits:
        pq = phys_qubits[0]
        print(f'T1[{pq}]: {props.t1(pq)}', flush=True)
        print(f'T2[{pq}]: {props.t2(pq)}', flush=True)
        print(f'Readout err[{pq}]: {props.readout_error(pq)}', flush=True)
        # Check gate errors
        for ginfo in props.gate_errors():
            if ginfo.gate_name in ('rz', 'sx') and pq in ginfo.qubits:
                if ginfo.gate_name == 'sx':
                    print(f'{ginfo.gate_name} error on {ginfo.qubits}: {ginfo.error}', flush=True)
except Exception as e:
    print(f'Layout/properties error: {e}', flush=True)

# Run it
sampler = Sampler(backend)
job1 = sampler.run([tqc1], shots=1024)
result1 = job1.result()
counts1 = result1[0].data.meas.get_counts()
print(f'\n✅ TEST 1 RESULT: {counts1}', flush=True)
total1 = sum(counts1.values())
p0_1 = counts1.get('0', 0) / total1 * 100
print(f'   P(0) = {p0_1:.2f}%', flush=True)

# --- TEST 2: X → X → measure (X² = I → |0⟩) ---
print(f'\n{"="*50}', flush=True)
print('TEST 2: X·X = I → |0⟩ (simplest identity)', flush=True)
qc2 = QuantumCircuit(1)
qc2.x(0)
qc2.x(0)  # X² = I
qc2.measure_all()
tqc2 = transpile(qc2, backend, optimization_level=0, seed_transpiler=42)
try:
    from qiskit.qasm2 import dumps
    print(f'QASM2:\n{dumps(tqc2)}', flush=True)
except:
    pass

job2 = sampler.run([tqc2], shots=1024)
result2 = job2.result()
counts2 = result2[0].data.meas.get_counts()
print(f'\n✅ TEST 2 RESULT: {counts2}', flush=True)
total2 = sum(counts2.values())
p0_2 = counts2.get('0', 0) / total2 * 100
print(f'   P(0) = {p0_2:.2f}%', flush=True)

# --- TEST 3: Same U gate from loschmidt test ---
print(f'\n{"="*50}', flush=True)
print('TEST 3: U·U† (same loschmidt angles) → |0⟩', flush=True)
np.random.seed(42)
t = float(np.random.uniform(0, 2*np.pi))
p = float(np.random.uniform(0, 2*np.pi))
l = float(np.random.uniform(0, 2*np.pi))
print(f'Angles: theta={t:.4f}, phi={p:.4f}, lam={l:.4f}', flush=True)

qc3 = QuantumCircuit(1)
qc3.u(t, p, l, 0)
qc3.barrier()
qc3.u(t, p, l, 0).inverse()  # Echo
qc3.barrier()
qc3.measure_all()
tqc3 = transpile(qc3, backend, optimization_level=0, seed_transpiler=42)
try:
    from qiskit.qasm2 import dumps
    print(f'QASM2:\n{dumps(tqc3)}', flush=True)
except:
    pass

job3 = sampler.run([tqc3], shots=1024)
result3 = job3.result()
counts3 = result3[0].data.meas.get_counts()
print(f'\n✅ TEST 3 RESULT: {counts3}', flush=True)
total3 = sum(counts3.values())
p0_3 = counts3.get('0', 0) / total3 * 100
print(f'   P(0) = {p0_3:.2f}%', flush=True)

# --- TEST 4: Same U without echo (control for this U) ---
print(f'\n{"="*50}', flush=True)
print('TEST 4: U only (no echo) — expected P(0) = cos²(θ/2)', flush=True)
qc4 = QuantumCircuit(1)
qc4.u(t, p, l, 0)
qc4.measure_all()
tqc4 = transpile(qc4, backend, optimization_level=0, seed_transpiler=42)
job4 = sampler.run([tqc4], shots=1024)
result4 = job4.result()
counts4 = result4[0].data.meas.get_counts()
p0_4 = counts4.get('0', 0) / sum(counts4.values()) * 100
print(f'✅ TEST 4 RESULT: {counts4}, P(0) = {p0_4:.2f}%', flush=True)
expected = np.cos(t/2)**2 * 100
print(f'   Expected P(0) = cos²(θ/2) = {expected:.2f}%', flush=True)

# --- SUMMARY ---
print(f'\n{"="*50}', flush=True)
print('ÖSSZEFOGLALÓ:', flush=True)
print(f'  TEST 1 (RY·RY†=I):  P(0) = {p0_1:.2f}%  (expected ~98%)', flush=True)
print(f'  TEST 2 (X·X=I):     P(0) = {p0_2:.2f}%  (expected ~99%)', flush=True)
print(f'  TEST 3 (U·U†=I):    P(0) = {p0_3:.2f}%  (expected ~98%)', flush=True)
print(f'  TEST 4 (U only):     P(0) = {p0_4:.2f}%  (expected {expected:.2f}%)', flush=True)

results = {
    'test1_ry_echo': {'p0': p0_1, 'counts': counts1, 'qasm_angles': 'RY(pi/2)->RY(-pi/2)', 'expected': '~98%'},
    'test2_xx': {'p0': p0_2, 'counts': counts2, 'expected': '~99%'},
    'test3_loschmidt': {'p0': p0_3, 'counts': counts3, 'angles': {'theta': t, 'phi': p, 'lam': l}, 'expected': '~98%'},
    'test4_control': {'p0': p0_4, 'counts': counts4, 'expected': f'{expected:.2f}%'},
}
with open('results/qam_calibration_test.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f'\n✅ Mentve: results/qam_calibration_test.json', flush=True)
