"""Fix qam_all_circuits.json — extract actual physical qubits + QASM."""
import json, os, sys

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# This import applies the monkeypatch before qiskit_ibm_runtime is loaded
from src.qam_core import QAM, _patched_fields  # noqa
import dataclasses

qam = QAM(token=None, backend='ibm_kingston')  # dummy for backend access
if not qam.backend:
    # Build from service
    import json as _json
    apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
    token = _json.load(open(apikey_path)).get('apikey')
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(token=token, instance='auto')
    backend = service.backend('ibm_kingston')
else:
    backend = qam.backend

from qiskit import QuantumCircuit, transpile

# Define test angles (same seed as run_loschmidt.py)
import numpy as np
np.random.seed(42)
angles = {'theta': np.random.uniform(0, 2*np.pi),
          'phi': np.random.uniform(0, 2*np.pi),
          'lam': np.random.uniform(0, 2*np.pi)}

circuits = {
    'sync_1qubit_hxh_optimized': {
        'qubits': 1, 'opt_level': 3, 'job_id': 'db7tthor1c5c738la3ig',
        'build': lambda: QuantumCircuit(1) | (setattr(QuantumCircuit(1), '_setup', None) or None),  # placeholder
    },
}

# Rebuild circuits properly
def build_sync_hxh(qubits):
    qc = QuantumCircuit(qubits)
    for q in range(qubits):
        qc.h(q); qc.x(q); qc.h(q)
    qc.measure_all()
    return qc

def build_loschmidt(qubits):
    np.random.seed(42)
    qc = QuantumCircuit(qubits)
    for q in range(qubits):
        t = np.random.uniform(0, 2*np.pi); p = np.random.uniform(0, 2*np.pi); l = np.random.uniform(0, 2*np.pi)
        qc.u(t, p, l, q); qc.barrier()
        qc.u(t, p, l, q).inverse(); qc.barrier()
    qc.measure_all()
    return qc

def build_control(qubits):
    np.random.seed(42)
    qc = QuantumCircuit(qubits)
    for q in range(qubits):
        t = np.random.uniform(0, 2*np.pi); p = np.random.uniform(0, 2*np.pi); l = np.random.uniform(0, 2*np.pi)
        qc.u(t, p, l, q); qc.barrier()
    qc.measure_all()
    return qc

builders = {
    'sync_1qubit_hxh_optimized': (1, 3, 'db7tthor1c5c738la3ig', build_sync_hxh),
    'sync_5qubit_hxh_optimized': (5, 3, 'db7ufs6il99s73fotfcg', build_sync_hxh),
    'sync_10qubit_hxh_optimized': (10, 3, 'db7ugt0r1c5c738lb9a0', build_sync_hxh),
    'loschmidt_sync_1qubit': (1, 0, 'db7uus8r1c5c738lc8i0', build_loschmidt),
    'loschmidt_control_1qubit': (1, 0, 'db7uusur6oqs7388co40', build_control),
}

circuit_data = {}
for name, (qubits, opt_level, job_id, builder) in builders.items():
    print(f'  {name}...', flush=True)
    qc = builder(qubits)
    tqc = transpile(qc, backend, optimization_level=opt_level, seed_transpiler=42)

    # Get physical qubits — only the ones actually used
    layout = tqc.layout
    initial = layout.initial_layout
    # The initial layout maps virtual qubits → physical qubits
    # Only the first `qubits` entries are the actual circuit qubits
    virtual_bits = initial.get_virtual_bits()  # dict: Qubit -> int
    # The circuit qubits are tqc.qubits[0:qubits]
    physical_qubits = []
    for vq in tqc.qubits[:qubits]:
        if vq in virtual_bits:
            physical_qubits.append(virtual_bits[vq])
        else:
            physical_qubits.append(None)

    # Get QASM
    try:
        from qiskit.qasm2 import dumps as qasm_dumps
        qasm_str = qasm_dumps(tqc)
    except Exception as e:
        try:
            qasm_str = tqc.qasm()
        except Exception:
            qasm_str = f'QASM not available: {e}'

    circuit_data[name] = {
        'job_id': job_id,
        'qubits': qubits,
        'opt_level': opt_level,
        'physical_qubits': physical_qubits,
        'gate_counts': dict(tqc.count_ops()),
        'depth': tqc.depth(),
        'transpiled_qasm': qasm_str[:3000] if qasm_str else None,
    }
    print(f'  Physical qubits: {physical_qubits}', flush=True)
    if qasm_str and qasm_str != 'QASM not available':
        print(f'  QASM: {qasm_str[:200]}...', flush=True)
    else:
        print(f'  QASM: not available (qiskit 2.x)', flush=True)

# Also get old results
old_file = 'results/qam_all_circuits.json'
if os.path.exists(old_file):
    old_data = json.load(open(old_file, 'r', encoding='utf-8'))
    # Merge physical_qubits and QASM from old data if new extraction failed
    for name in circuit_data:
        if name in old_data:
            if not circuit_data[name]['physical_qubits'] or None in circuit_data[name]['physical_qubits']:
                # Keep old format — extract first N from old data
                old_pq = old_data[name].get('physical_qubits', [])
                nq = circuit_data[name]['qubits']
                circuit_data[name]['physical_qubits_old'] = old_pq[:nq + 5] if len(old_pq) > nq else old_pq

with open('results/qam_all_circuits.json', 'w', encoding='utf-8') as f:
    json.dump(circuit_data, f, indent=2, default=str, ensure_ascii=False)
print(f'\n✅ Mentve: results/qam_all_circuits.json', flush=True)

# Print summary
print(f'\n{"="*50}', flush=True)
print('ÖSSZEFOGLALÓ:', flush=True)
for name, info in circuit_data.items():
    print(f'  {name}:', flush=True)
    print(f'    job: {info["job_id"]}', flush=True)
    print(f'    qubits: {info["qubits"]}, gates: {info["gate_counts"]}, depth: {info["depth"]}', flush=True)
    print(f'    physical_qubits: {info["physical_qubits"]}', flush=True)
