"""Run fixed SYnc on available backends with shorter shots for faster queue."""
import json, os, sys, time, traceback

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

# Try all backends
for backend_name in ['ibm_fez', 'ibm_kingston', 'ibm_marrakesh']:
    try:
        print(f'\n=== {backend_name} ===', flush=True)
        qam = QAM(token=token, backend=backend_name)
        print(f'Connected: {qam.backend.name} ({qam.backend.configuration().n_qubits} qubits)', flush=True)
        
        # 1-qubit fixed SYnc with 256 shots (faster)
        r1 = qam.sync_operation(qubits=1, shots=256)
        print(f'1-qubit: job={r1["job_id"]}, success={r1["success_rate"]:.4f} ({r1["success_rate"]*100:.2f}%), entropy={float(r1["entropy"]):.4f}, time={r1["time_us"]/1e6:.1f}s', flush=True)
        
        # Save immediately
        with open(f'results/qam_fixed_{backend_name}.json', 'w', encoding='utf-8') as f:
            json.dump({'backend': backend_name, 'circuit': 'H·X·H = Z', '1_qubit': r1}, f, indent=2, default=str)
        print(f'Saved: results/qam_fixed_{backend_name}.json', flush=True)
        
    except Exception as e:
        print(f'❌ {e}', flush=True)
        traceback.print_exc()
