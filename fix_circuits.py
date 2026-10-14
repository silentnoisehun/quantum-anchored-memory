"""Build qam_all_circuits.json — physical qubits from QASM parsing + get_virtual_bits."""
import json, os, sys, re, numpy as np

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'
from src.qam_core import QAM  # applies monkeypatch

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')
qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend

from qiskit import QuantumCircuit, transpile

def get_physical_qubits(tqc, n_qubits):
    """Extract physical qubit indices from the transpiled circuit.

    In qiskit 2.x transpiled circuit QASM, qreg is the backend size (156)
    and gates reference q[PHYS_ID] directly since the layout is already
    applied. We parse gate lines to find which physical qubits are used.
    """
    try:
        from qiskit.qasm2 import dumps as qasm_dumps
        qasm_str = qasm_dumps(tqc)
    except Exception:
        qasm_str = tqc.qasm() if hasattr(tqc, 'qasm') else ''

    # Parse QASM: find all q[N] references in gate/measure lines (not qreg)
    qubit_refs = set()
    for line in qasm_str.split('\n'):
        line = line.strip()
        if line.startswith('qreg') or not line:
            continue
        # Match q[N] in gate lines like: rz(-pi) q[91];  measure q[91] -> meas[0];
        matches = re.findall(r'q\[(\d+)\]', line)
        qubit_refs.update(int(m) for m in matches)

    # Sort and return
    return sorted(qubit_refs)

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
        t = np.random.uniform(0, 2*np.pi)
        p = np.random.uniform(0, 2*np.pi)
        l = np.random.uniform(0, 2*np.pi)
        qc.u(t, p, l, q); qc.barrier()
        qc.u(t, p, l, q).inverse(); qc.barrier()
    qc.measure_all()
    return qc

def build_control(qubits):
    np.random.seed(42)
    qc = QuantumCircuit(qubits)
    for q in range(qubits):
        t = np.random.uniform(0, 2*np.pi)
        p = np.random.uniform(0, 2*np.pi)
        l = np.random.uniform(0, 2*np.pi)
        qc.u(t, p, l, q); qc.barrier()
    qc.measure_all()
    return qc

np.random.seed(42)
angles = {
    'theta': float(np.random.uniform(0, 2*np.pi)),
    'phi': float(np.random.uniform(0, 2*np.pi)),
    'lam': float(np.random.uniform(0, 2*np.pi)),
}

# Also get initial_layout mapping for full transparency
def get_layout_info(tqc):
    """Get the full virtual→physical mapping."""
    layout = tqc.layout
    if layout is None:
        return {}
    initial = layout.initial_layout
    vbits = initial.get_virtual_bits()
    # Build mapping: filter for the actual circuit qubits (not ancilla)
    mapping = {}
    for qubit, phys in vbits.items():
        # In qiskit 2.x, repr shows the register info
        qrepr = repr(qubit)
        if 'ancilla' not in qrepr:
            # This is a real circuit qubit
            idx_match = re.search(r'index=(\d+)', qrepr)
            if idx_match:
                v_idx = int(idx_match.group(1))
                mapping[f'v[{v_idx}]'] = phys
    return mapping

builders = {
    'sync_1qubit_hxh_optimized': (1, 3, 'db7tthor1c5c738la3ig', build_sync_hxh),
    'sync_5qubit_hxh_optimized': (5, 3, 'db7ufs6il99s73fotfcg', build_sync_hxh),
    'sync_10qubit_hxh_optimized': (10, 3, 'db7ugt0r1c5c738lb9a0', build_sync_hxh),
    'loschmidt_sync_1qubit': (1, 0, 'db7uus8r1c5c738lc8i0', build_loschmidt),
    'loschmidt_control_1qubit': (1, 0, 'db7uusur6oqs7388co40', build_control),
}

circuit_data = {'angles': angles, 'circuits': {}}

for name, (qubits, opt_level, job_id, builder) in builders.items():
    print(f'  {name}...', flush=True)
    qc = builder(qubits)
    tqc = transpile(qc, backend, optimization_level=opt_level, seed_transpiler=42)

    # Get QASM
    try:
        from qiskit.qasm2 import dumps as qasm_dumps
        qasm_str = qasm_dumps(tqc)
    except Exception:
        try:
            qasm_str = tqc.qasm()
        except Exception:
            qasm_str = 'QASM not available'

    # Get physical qubits from QASM
    physical_qubits = get_physical_qubits(tqc, qubits)
    # Get full layout mapping
    layout_info = get_layout_info(tqc)

    circuit_data['circuits'][name] = {
        'job_id': job_id,
        'qubits_virtual': qubits,
        'qubits_physical': physical_qubits,
        'virtual_to_physical': layout_info,
        'opt_level': opt_level,
        'gate_counts': dict(tqc.count_ops()),
        'depth': tqc.depth(),
        'transpiled_qasm': qasm_str,
    }
    print(f'  Physical qubits: {physical_qubits}', flush=True)
    print(f'  Layout: {layout_info}', flush=True)
    print(f'  Gates: {dict(tqc.count_ops())}', flush=True)

with open('results/qam_all_circuits.json', 'w', encoding='utf-8') as f:
    json.dump(circuit_data, f, indent=2, default=str, ensure_ascii=False)
print(f'\n✅ Mentve: results/qam_all_circuits.json', flush=True)

# Print all QASMs
for name in circuit_data['circuits']:
    print(f'\n{"="*60}', flush=True)
    print(f'{name} (job: {circuit_data["circuits"][name]["job_id"]})', flush=True)
    print(f'Physical qubits: {circuit_data["circuits"][name]["qubits_physical"]}', flush=True)
    print(f'Layout: {circuit_data["circuits"][name]["virtual_to_physical"]}', flush=True)
    print(f'Gates: {circuit_data["circuits"][name]["gate_counts"]}', flush=True)
    print(f'{"="*60}', flush=True)
    print(circuit_data['circuits'][name]['transpiled_qasm'], flush=True)
    print(flush=True)
