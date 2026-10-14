"""Check all three IBM Quantum API keys for ibm_heron access."""
import json
import os
import sys

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import from qam_core to get the monkeypatch applied automatically
from src.qam_core import QAM

apikey_files = [
    'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/b6e25d02-b251-4b93-a20e-214bbf93e3ec/apikey (1).json',
    'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json',
    'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/b695fceb-1ab2-4303-9547-5ee1faf5f217/apikey (2).json',
]

from qiskit_ibm_runtime import QiskitRuntimeService

for i, path in enumerate(apikey_files):
    try:
        data = json.load(open(path))
        token = data.get('apikey') or data.get('token')
        if not token:
            print(f"Key {i+1}: nincs apikey/token mező — {list(data.keys())}")
            continue
        name = data.get('name', f'key_{i+1}')
        token_len = len(token)
        print(f"Key {i+1} (name: {name}, {token_len} chars): próba...", flush=True)
        service = QiskitRuntimeService(token=token, instance='auto')
        backends = service.backends()
        backend_names = [b.name for b in backends]
        print(f"  Backends: {backend_names}")
        if 'ibm_heron' in backend_names:
            print(f"  ✅ **ibm_heron ELÉRHETŐ!**")
            b = service.backend('ibm_heron')
            print(f"  n_qubits: {b.configuration().n_qubits}")
            print(f"  status: {b.status().operational_status}")
            print(f"  basis_gates: {b.configuration().basis_gates}")
    except Exception as e:
        print(f"  ❌ Hiba: {e}")
    print()
