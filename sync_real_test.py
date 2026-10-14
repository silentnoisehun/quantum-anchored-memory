"""
Valódi SYnc teszt (Loschmidt Echo) a jó qbiten (91).
Ha ~98%, a SYnc tényleg működik!
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

np.random.seed(42)
theta = float(np.random.uniform(0, 2*np.pi))
phi = float(np.random.uniform(0, 2*np.pi))
lam = float(np.random.uniform(0, 2*np.pi))
print(f'Angles: theta={theta:.4f}, phi={phi:.4f}, lam={lam:.4f}', flush=True)
print(f'Expected P(0) for U|0>: cos²(θ/2) = {np.cos(theta/2)**2 * 100:.2f}%', flush=True)
print(f'Target qubit: 91 (jó qubit, megerősítve X·X=I 99.32%-dal)', flush=True)

sampler = Sampler(backend)

# --- SYnc (Echo): U·U† → |0⟩ ---
print(f'\n{"="*60}', flush=True)
print('SYnc (Echo): U·U† → |0⟩, opt_level=0, qubit 91', flush=True)
qc_sync = QuantumCircuit(1)
qc_sync.u(theta, phi, lam, 0)
qc_sync.barrier()
qc_sync.u(theta, phi, lam, 0).inverse()  # Echo
qc_sync.barrier()
qc_sync.measure_all()

tqc_sync = transpile(qc_sync, backend, optimization_level=0, seed_transpiler=42,
                     initial_layout=[91])
from qiskit.qasm2 import dumps
print(f'QASM:\n{dumps(tqc_sync)}', flush=True)
print(f'Gates: {dict(tqc_sync.count_ops())}, Depth: {tqc_sync.depth()}', flush=True)

job_sync = sampler.run([tqc_sync], shots=1024)
result_sync = job_sync.result()
counts_sync = result_sync[0].data.meas.get_counts()
p0_sync = counts_sync.get('0', 0) / sum(counts_sync.values()) * 100
print(f'\n✅ SYnc RESULT: {counts_sync}  P(0) = {p0_sync:.2f}%', flush=True)
print(f'   Expected: ~98%+ (10 kapu, jó qubit)', flush=True)

# --- Control: U|0⟩ only ---
print(f'\n{"="*60}', flush=True)
print('Control: U|0⟩, opt_level=0, qubit 91', flush=True)
qc_ctrl = QuantumCircuit(1)
qc_ctrl.u(theta, phi, lam, 0)
qc_ctrl.barrier()
qc_ctrl.measure_all()

tqc_ctrl = transpile(qc_ctrl, backend, optimization_level=0, seed_transpiler=42,
                     initial_layout=[91])
print(f'QASM:\n{dumps(tqc_ctrl)}', flush=True)
print(f'Gates: {dict(tqc_ctrl.count_ops())}, Depth: {tqc_ctrl.depth()}', flush=True)

job_ctrl = sampler.run([tqc_ctrl], shots=1024)
result_ctrl = job_ctrl.result()
counts_ctrl = result_ctrl[0].data.meas.get_counts()
p0_ctrl = counts_ctrl.get('0', 0) / sum(counts_ctrl.values()) * 100
print(f'\n✅ Control RESULT: {counts_ctrl}  P(0) = {p0_ctrl:.2f}%', flush=True)
print(f'   Expected: cos²(θ/2) = {np.cos(theta/2)**2 * 100:.2f}%', flush=True)

# --- SUMMARY ---
print(f'\n{"="*60}', flush=True)
print('🎯 SYNC TESZT ÖSSZEFOGLALÓ (qbit 91, opt_level=0):', flush=True)
print(f'  SYnc (U·U† Echo): P(0) = {p0_sync:.2f}%  counts={counts_sync}', flush=True)
print(f'  Control (U only): P(0) = {p0_ctrl:.2f}%  counts={counts_ctrl}', flush=True)
ratio = p0_sync / p0_ctrl if p0_ctrl > 0 else float('inf')
print(f'  Improvement ratio: {ratio:.2f}x', flush=True)

if p0_sync > 95:
    verdict = '✅ SYNC MŰKÖDIK — U·U† → |0⟩ teszi a munkáját!'
elif p0_sync > 50 and p0_sync > p0_ctrl * 1.5:
    verdict = '✅ SYNC jól működik — jelentős javulás a kontrollhoz képest'
elif p0_sync > 50:
    verdict = '⚠️ SYNC enyhíteni próbál, de nem elég erős'
else:
    verdict = '❌ SYNC nem működik — valami még mindig rossz'
print(f'  Verdiktum: {verdict}', flush=True)

results = {
    'test_name': 'Real SYnc Loschmidt Echo (qbit 91)',
    'angles': {'theta': theta, 'phi': phi, 'lam': lam},
    'expected_control_p0': np.cos(theta/2)**2 * 100,
    'sync': {'p0': p0_sync, 'counts': counts_sync, 'job_id': job_sync.job_id() if hasattr(job_sync, 'job_id') else 'N/A'},
    'control': {'p0': p0_ctrl, 'counts': counts_ctrl, 'job_id': job_ctrl.job_id() if hasattr(job_ctrl, 'job_id') else 'N/A'},
    'verdict': verdict,
    'backend': 'ibm_kingston',
    'physical_qubit': 91,
    'opt_level': 0,
    'sync_qasm': dumps(tqc_sync),
    'control_qasm': dumps(tqc_ctrl),
}
with open('results/qam_sync_real_test.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f'\n✅ Mentve: results/qam_sync_real_test.json', flush=True)
