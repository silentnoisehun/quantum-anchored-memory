"""Extract physical qubit mapping using qiskit 2.x API."""
import json, os, sys

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'
from src.qam_core import QAM  # applies monkeypatch

import numpy as np
from qiskit import QuantumCircuit, transpile

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend

# 1-qubit optimized SYnc circuit
qc = QuantumCircuit(1)
qc.h(0); qc.x(0); qc.h(0)
qc.measure_all()
tqc = transpile(qc, backend, optimization_level=3, seed_transpiler=42)

layout = tqc.layout
print(f'layout type: {type(layout)}', flush=True)
print(f'layout attributes: {[a for a in dir(layout) if not a.startswith("_")]}', flush=True)

# Try different approaches
if layout is not None:
    initial = layout.initial_layout
    print(f'\ninitial_layout type: {type(initial)}', flush=True)
    print(f'initial_layout attributes: {[a for a in dir(initial) if not a.startswith("_")]}', flush=True)

    # Approach 1: get_virtual_bits
    try:
        vbits = initial.get_virtual_bits()
        print(f'\nget_virtual_bits() returned {len(vbits)} entries', flush=True)
        for k, v in list(vbits.items())[:5]:
            print(f'  {type(k).__name__}({k}) -> {v}', flush=True)
    except Exception as e:
        print(f'  get_virtual_bits() error: {e}', flush=True)

    # Approach 2: get_physical_bits
    try:
        pbits = initial.get_physical_bits()
        print(f'\nget_physical_bits() returned {len(pbits)} entries', flush=True)
        # Find the physical bits that correspond to our circuit qubits
        for k, v in list(pbits.items())[:10]:
            print(f'  phys {k} -> {type(v).__name__}', flush=True)
    except Exception as e:
        print(f'  get_physical_bits() error: {e}', flush=True)

    # Approach 3: Try indexing
    try:
        for q in tqc.qubits[:1]:
            print(f'\n  tqc.qubits[0] type: {type(q)}', flush=True)
            print(f'  initial[q]: {initial[q]}', flush=True)
    except Exception as e:
        print(f'  indexing error: {e}', flush=True)

    # Approach 4: __getitem__
    try:
        print(f'\n  initial[ClassicalRegister[0]]: {initial[tqc.clbits[0]] if tqc.clbits else "no clbits"}', flush=True)
    except Exception as e:
        print(f'  __getitem__ error: {e}', flush=True)

# Also try the QASM approach — look for qubit names
print(f'\nQASM output:', flush=True)
try:
    from qiskit.qasm2 import dumps
    qasm_str = dumps(tqc)
    print(qasm_str[:1000], flush=True)
except Exception as e:
    print(f'QASM error: {e}', flush=True)
    try:
        qasm_str = tqc.qasm()
        print(qasm_str[:1000], flush=True)
    except Exception as e2:
        print(f'  qasm() error: {e2}', flush=True)
