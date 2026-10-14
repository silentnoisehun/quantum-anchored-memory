"""Run fixed SYnc (H·X·H = Z) on all available real quantum backends."""
import json
import os
import sys
import time

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import from qam_core — applies monkeypatch before qiskit_ibm_runtime import
from src.qam_core import QAM

# Load token from uploaded file
apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

backends_to_try = ['ibm_fez', 'ibm_kingston', 'ibm_marrakesh']

results = {}
for backend_name in backends_to_try:
    print(f'\n{"-"*60}', flush=True)
    print(f'Backend: {backend_name}', flush=True)
    print(f'{"-"*60}', flush=True)
    try:
        qam = QAM(token=token, backend=backend_name)
        if not qam.backend:
            print(f'  ❌ Nem sikerült csatlakozni', flush=True)
            continue

        b = qam.backend
        cfg = b.configuration()
        print(f'  n_qubits: {cfg.n_qubits}', flush=True)
        print(f'  basis_gates: {cfg.basis_gates}', flush=True)

        # 1-qubit SYnc
        time.sleep(2)
        print(f'  1-qubit SYnc...', flush=True)
        r1 = qam.sync_operation(qubits=1, shots=1024)
        print(f'  → job={r1["job_id"]}, success={r1["success_rate"]:.4f}, entropy={r1["entropy"]:.4f}, time={r1["time_us"]/1e6:.1f}s', flush=True)

        time.sleep(3)
        # 5-qubit SYnc
        print(f'  5-qubit SYnc...', flush=True)
        r5 = qam.sync_operation(qubits=5, shots=1024)
        print(f'  → job={r5["job_id"]}, success={r5["success_rate"]:.4f}, entropy={r5["entropy"]:.4f}, time={r5["time_us"]/1e6:.1f}s', flush=True)

        results[backend_name] = {
            '1qubit': r1,
            '5qubit': r5,
        }
    except Exception as e:
        print(f'  ❌ Hiba: {e}', flush=True)
        results[backend_name] = {'error': str(e)}

# Save results
os.makedirs('results', exist_ok=True)
with open('results/qam_fixed_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str)
print(f'\n✅ Eredmények mentve: results/qam_fixed_results.json', flush=True)
