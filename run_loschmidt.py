"""Submit real SYnc teszt (Loschmidt Echo) — opt_level=0 to preserve U·U† gates."""
import json, os, sys, time, numpy as np

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import Sampler

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

np.random.seed(42)
qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend
print(f'Backend: {backend.name}', flush=True)

# 1-qubit valós SYnc (U·U† = I, de a kapuk megőrzik opt_level=0 miatt)
angles = {'theta': np.random.uniform(0, 2*np.pi),
          'phi': np.random.uniform(0, 2*np.pi),
          'lam': np.random.uniform(0, 2*np.pi)}

# SYnc: U|0⟩ → U† → |0⟩ (Echo)
qc_sync = QuantumCircuit(1)
qc_sync.u(angles['theta'], angles['phi'], angles['lam'], 0)
qc_sync.barrier()  # Barrier a szétválasztáshoz
qc_sync.u(angles['theta'], angles['phi'], angles['lam'], 0).inverse()
qc_sync.barrier()
qc_sync.measure_all()

# Control: csak U|0⟩, nincs Echo
qc_control = QuantumCircuit(1)
qc_control.u(angles['theta'], angles['phi'], angles['lam'], 0)
qc_control.barrier()
qc_control.measure_all()

print(f'\nAngles: theta={angles["theta"]:.4f}, phi={angles["phi"]:.4f}, lam={angles["lam"]:.4f}', flush=True)

# opt_level=0 — a kapuk megőrzik
tqc_sync = transpile(qc_sync, backend, optimization_level=0, seed_transpiler=42)
tqc_control = transpile(qc_control, backend, optimization_level=0, seed_transpiler=42)
print(f'  SYnc gates (opt=0): {tqc_sync.count_ops()}', flush=True)
print(f'  Control gates (opt=0): {tqc_control.count_ops()}', flush=True)

# Submit 1-qubit only
time.sleep(3)
sampler = Sampler(backend)
print(f'\n🚀 1-qubit SYnc fut (opt_level=0)...', flush=True)
job_sync = sampler.run([tqc_sync], shots=1024)
print(f'  Job ID: {job_sync.job_id()}', flush=True)

print(f'  Control fut...', flush=True)
job_ctrl = sampler.run([tqc_control], shots=1024)
print(f'  Control Job ID: {job_ctrl.job_id()}', flush=True)

# Save job IDs for later retrieval
job_info = {
    'sync_job_id': job_sync.job_id(),
    'control_job_id': job_ctrl.job_id(),
    'angles': angles,
    'backend': 'ibm_kingston',
    'circuit': 'U|0⟩ → U† → |0⟩ (opt_level=0)',
    'submitted_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'sync_transpiled_gates': dict(tqc_sync.count_ops()),
    'control_transpiled_gates': dict(tqc_control.count_ops()),
}
with open('results/qam_loschmidt_jobid.json', 'w', encoding='utf-8') as f:
    json.dump(job_info, f, indent=2, default=str)
print('\n✅ Job ID mentve: results/qam_loschmidt_jobid.json', flush=True)

# Try to wait for results
print('\n⏳ Várom az eredményeket...', flush=True)
try:
    result_sync = job_sync.result()
    counts_sync = result_sync[0].data.meas.get_counts()
    sr_sync = counts_sync.get('0', 0) / 1024
    print(f'  SYnc: {sr_sync*100:.2f}% (counts: {counts_sync})', flush=True)
except Exception as e:
    print(f'  SYnc: még fut ({e})', flush=True)
    sr_sync = None
    counts_sync = None

try:
    result_ctrl = job_ctrl.result()
    counts_ctrl = result_ctrl[0].data.meas.get_counts()
    sr_ctrl = counts_ctrl.get('0', 0) / 1024
    print(f'  Control: {sr_ctrl*100:.2f}% (counts: {counts_ctrl})', flush=True)
except Exception as e:
    print(f'  Control: még fut ({e})', flush=True)
    sr_ctrl = None
    counts_ctrl = None

results = {'job_info': job_info}
if sr_sync is not None:
    results['sync'] = {'success_rate': sr_sync, 'counts': counts_sync, 'result_type': 'quantum'}
if sr_ctrl is not None:
    results['control'] = {'success_rate': sr_ctrl, 'counts': counts_ctrl, 'result_type': 'quantum'}

with open('results/qam_loschmidt_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str)
print(f'\n✅ Eredmények mentve: results/qam_loschmidt_results.json', flush=True)
