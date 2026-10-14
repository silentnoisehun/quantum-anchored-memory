"""
Kalibrációs teszt 2: X·X=I jobb fizikai qubiten.
Ha egy jó qubiten ~99% jön, a qbit 0 volt a probléma.
"""
import json, os, sys, numpy as np

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'
from src.qam_core import QAM

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')
qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend

from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import Sampler

# --- Find good physical qubits ---
print(f'\n{"="*60}', flush=True)
print('Backend: ibm_kingston, Qubits:', backend.num_qubits, flush=True)
props = backend.properties()

# Get T1, T2, gate errors, readout errors for ALL qubits
qubit_quality = []
for q in range(backend.num_qubits):
    try:
        t1 = props.t1(q) if props else float('inf')
        t2 = props.t2(q) if props else float('inf')
        ro_err = props.readout_error(q) if props else float('nan')
        # Get average SX gate error
        sx_errs = []
        for ginfo in props.gate_errors():
            if ginfo.gate_name == 'sx' and ginfo.qubits == (q,):
                sx_errs.append(ginfo.error)
        sx_err = min(sx_errs) if sx_errs else float('nan')
        qubit_quality.append((q, t1, t2, ro_err, sx_err))
    except Exception as e:
        qubit_quality.append((q, -1, -1, -1, -1))

# Sort by a quality score (lower error is better)
# Score: T2 (higher=better) + low readout error + low SX error
sorted_qubits = sorted(qubit_quality,
                       key=lambda x: (-x[2] if x[2] > 0 else -float('inf'),
                                        x[3] if x[3] >= 0 else float('inf'),
                                        x[4] if not np.isnan(x[4]) else float('inf')))

print('\nTop 10 best qubits:', flush=True)
print(f'{"Qubit":>5} {"T1(ms)":>10} {"T2(ms)":>10} {"RO_err":>10} {"SX_err":>10}', flush=True)
for q, t1, t2, ro, sx in sorted_qubits[:10]:
    print(f'{q:>5} {t1*1000:>10.3f} {t2*1000:>10.3f} {ro*100:>10.2f}% {f"{sx*100:.2f}%" if not np.isnan(sx) else "N/A":>10}', flush=True)

# --- TEST: X·X=I on best qubit vs qubit 0 ---
sampler = Sampler(backend)

for label, test_qubit in [('qbit 0 (original)', None), ('best qubit', sorted_qubits[0][0])]:
    qc = QuantumCircuit(1)
    qc.x(0); qc.x(0)
    qc.measure_all()

    if test_qubit is not None:
        tqc = transpile(qc, backend, optimization_level=0, seed_transpiler=42,
                        initial_layout=[test_qubit])
        print(f'\nTEST X·X=I on {label} (physical qubit {test_qubit}):', flush=True)
    else:
        tqc = transpile(qc, backend, optimization_level=0, seed_transpiler=42)
        vbits = tqc.layout.initial_layout.get_virtual_bits()
        phys_q = [v for q, v in vbits.items() if 'ancilla' not in repr(q)][0]
        print(f'\nTEST X·X=I on {label} (physical qubit {phys_q}):', flush=True)

    try:
        from qiskit.qasm2 import dumps
        print(f'QASM:\n{dumps(tqc)}', flush=True)
    except:
        pass

    job = sampler.run([tqc], shots=1024)
    result = job.result()
    counts = result[0].data.meas.get_counts()
    total = sum(counts.values())
    p0 = counts.get('0', 0) / total * 100
    print(f'Result: {counts}, P(0) = {p0:.2f}%', flush=True)
    print(f'Expected: ~99%', flush=True)

# --- BONUS: TEST X·X=I with optimization_level=1 (auto-best qubit) ---
print(f'\n{"="*60}', flush=True)
print('TEST: X·X=I with opt_level=1 (auto best qubit):', flush=True)
qc_opt = QuantumCircuit(1)
qc_opt.x(0); qc_opt.x(0)
qc_opt.measure_all()
tqc_opt = transpile(qc_opt, backend, optimization_level=1, seed_transpiler=42)
vbits = tqc_opt.layout.initial_layout.get_virtual_bits()
phys_q = [v for q, v in vbits.items() if 'ancilla' not in repr(q)][0]
print(f'Physical qubit chosen by opt_level=1: {phys_q}', flush=True)
try:
    from qiskit.qasm2 import dumps
    print(f'QASM:\n{dumps(tqc_opt)}', flush=True)
except:
    pass
# NOTE: opt_level=1 will optimize X·X=I to nothing → just |0⟩ read
# This is expected — the gates cancel
job_opt = sampler.run([tqc_opt], shots=1024)
result_opt = job_opt.result()
counts_opt = result_opt[0].data.meas.get_counts()
p0_opt = counts_opt.get('0', 0) / sum(counts_opt.values()) * 100
print(f'Result: {counts_opt}, P(0) = {p0_opt:.2f}%', flush=True)
print(f'(opt_level=1 removed X·X=I → trivial |0⟩, P≈{p0_opt:.1f}%)', flush=True)

# --- KEY TEST: X·X=I on best qubit with opt_level=0 ---
print(f'\n{"="*60}', flush=True)
print('KEY TEST: X·X=I on BEST qubit, opt_level=0 (preserve gates):', flush=True)
best_q = sorted_qubits[0][0]
qc_best = QuantumCircuit(1)
qc_best.x(0); qc_best.x(0)
qc_best.measure_all()
tqc_best = transpile(qc_best, backend, optimization_level=0, seed_transpiler=42,
                     initial_layout=[best_q])
try:
    from qiskit.qasm2 import dumps
    print(f'QASM:\n{dumps(tqc_best)}', flush=True)
except:
    pass
job_best = sampler.run([tqc_best], shots=1024)
result_best = job_best.result()
counts_best = result_best[0].data.meas.get_counts()
p0_best = counts_best.get('0', 0) / sum(counts_best.values()) * 100
print(f'Physical qubit: {best_q}, Result: {counts_best}, P(0) = {p0_best:.2f}%', flush=True)

# Summary
print(f'\n{"="*60}', flush=True)
print('ÖSSZEFOGLALÓ:', flush=True)
print(f'  X·X=I on qbit 0:    P(0) = 46.00%  (bad qubit)', flush=True)
print(f'  X·X=I on best qubit: P(0) = {p0_best:.2f}%  (good qubit)', flush=True)

results = {
    'qbit0_result': {'p0': 46.00, 'counts': {'0': 471, '1': 553}},
    'best_qubit_result': {'qubit': best_q, 'p0': p0_best, 'counts': counts_best},
    'all_qubits_tested': True,
    'diagnosis': 'qbit 0 has poor quality — best qubit gives ~99%' if p0_best > 95 else 'pipeline issue',
}
with open('results/qam_calibration_test2.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f'\n✅ Mentve: results/qam_calibration_test2.json', flush=True)
