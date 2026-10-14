"""
Retrieve transpiled circuit + qubit mapping for every quantum job.
"""
import json, os, sys, time, numpy as np

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend

# Recreate circuits and transpile with same params to get QASM + layout
jobs_to_reconstruct = {
    'sync_1qubit_hxh_optimized': {
        'qubits': 1,
        'builder': lambda q: _build_sync_hxh(q, 1),
        'opt_level': 3,
        'job_id': 'db7tthor1c5c738la3ig',
    },
    'sync_5qubit_hxh_optimized': {
        'qubits': 5,
        'builder': lambda q: _build_sync_hxh(q, 5),
        'opt_level': 3,
        'job_id': 'db7ufs6il99s73fotfcg',
    },
    'sync_10qubit_hxh_optimized': {
        'qubits': 10,
        'builder': lambda q: _build_sync_hxh(q, 10),
        'opt_level': 3,
        'job_id': 'db7ugt0r1c5c738lb9a0',
    },
    'loschmidt_sync_1qubit': {
        'qubits': 1,
        'builder': lambda q: _build_loschmidt(q),
        'opt_level': 0,
        'job_id': 'db7uus8r1c5c738lc8i0',
    },
    'loschmidt_control_1qubit': {
        'qubits': 1,
        'builder': lambda q: _build_control(q),
        'opt_level': 0,
        'job_id': 'db7uusur6oqs7388co40',
    },
}

def _build_sync_hxh(qubits, _=None):
    """H·X·H = Z circuit"""
    qc = QuantumCircuit(qubits)
    for q in range(qubits):
        qc.h(q)
        qc.x(q)
        qc.h(q)
    qc.measure_all()
    return qc

def _build_loschmidt(qubits):
    """U|0⟩ → U† → |0⟩ (Loschmidt Echo)"""
    np.random.seed(42)
    qc = QuantumCircuit(qubits)
    for q in range(qubits):
        theta = np.random.uniform(0, 2*np.pi)
        phi = np.random.uniform(0, 2*np.pi)
        lam = np.random.uniform(0, 2*np.pi)
        qc.u(theta, phi, lam, q)
        qc.barrier()
        qc.u(theta, phi, lam, q).inverse()
        qc.barrier()
    qc.measure_all()
    return qc

def _build_control(qubits):
    """U|0⟩ only (Control — no Echo)"""
    np.random.seed(42)
    qc = QuantumCircuit(qubits)
    for q in range(qubits):
        theta = np.random.uniform(0, 2*np.pi)
        phi = np.random.uniform(0, 2*np.pi)
        lam = np.random.uniform(0, 2*np.pi)
        qc.u(theta, phi, lam, q)
        qc.barrier()
    qc.measure_all()
    return qc

print('🔧 Re-transpiling minden job...', flush=True)

circuit_data = {}
for name, info in jobs_to_reconstruct.items():
    print(f'\n  {name} (job: {info["job_id"]})...', flush=True)
    qc = info['builder'](info['qubits'])
    tqc = transpile(qc, backend, optimization_level=info['opt_level'], seed_transpiler=42)

    # Get physical qubit layout
    layout = tqc.layout
    try:
        # qiskit 2.x: TranspileLayout
        from qiskit.providers import Backend
        physical_qubits = [qc_bit for qc_bit in layout.initial_layout.get_virtual_bits().values()] if layout and layout.initial_layout else list(range(info['qubits']))
    except Exception:
        try:
            physical_qubits = [int(str(q)) if str(q).isdigit() else q for q in layout.qubits] if layout else list(range(info['qubits']))
        except Exception:
            physical_qubits = list(range(info['qubits']))

    # Get QASM
    qasm_str = tqc.qasm() if hasattr(tqc, 'qasm') else 'QASM not available'

    # Gate counts
    gate_counts = dict(tqc.count_ops())

    circuit_data[name] = {
        'job_id': info['job_id'],
        'qubits': info['qubits'],
        'opt_level': info['opt_level'],
        'physical_qubits': physical_qubits,
        'gate_counts': gate_counts,
        'depth': tqc.depth() if hasattr(tqc, 'depth') else None,
        'transpiled_qasm': qasm_str[:2000] if qasm_str else None,  # truncate for readability
    }
    print(f'  Gates: {gate_counts}', flush=True)
    print(f'  Physical qubits: {physical_qubits}', flush=True)
    print(f'  Depth: {tqc.depth()}', flush=True)

# Save
with open('results/qam_all_circuits.json', 'w', encoding='utf-8') as f:
    json.dump(circuit_data, f, indent=2, default=str)
print(f'\n✅ Mentve: results/qam_all_circuits.json', flush=True)

# Also try to retrieve job metadata from IBM Quantum
service = QiskitRuntimeService(token=token, instance='auto')
job_metadata = {}
for name, info in jobs_to_reconstruct.items():
    try:
        job = service.job(info['job_id'])
        job_metadata[name] = {
            'job_id': info['job_id'],
            'status': str(job.status()),
            'created': str(job.creation_date) if hasattr(job, 'creation_date') else 'N/A',
            'runtime': str(job.time_per_step()) if hasattr(job, 'time_per_step') else 'N/A',
        }
        print(f'  {name}: status={job_metadata[name]["status"]}', flush=True)
    except Exception as e:
        job_metadata[name] = {'job_id': info['job_id'], 'error': str(e)}
        print(f'  {name}: ❌ {e}', flush=True)

# Merge into circuit_data
for name in circuit_data:
    if name in job_metadata:
        circuit_data[name]['ibm_metadata'] = job_metadata[name]

with open('results/qam_all_circuits.json', 'w', encoding='utf-8') as f:
    json.dump(circuit_data, f, indent=2, default=str)
print(f'✅ Frissítve: results/qam_all_circuits.json (metadata-vel)', flush=True)

# Print full QASM for the main circuit
print(f'\n{"="*60}', flush=True)
print('FULL QASM — SYnc optimized (H·X·H → RZ, 1 qubit):', flush=True)
print(f'{"="*60}', flush=True)
print(circuit_data['sync_1qubit_hxh_optimized']['transpiled_qasm'], flush=True)
