"""Run fixed SYnc (H·X·H = Z) on ibm_kingston AND ibm_marrakesh for comparison."""
import json, os, sys, time

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

results = {}

# 1. ibm_marrakesh 1-qubit (might have lower noise)
for backend_name in ['ibm_marrakesh']:
    try:
        print(f'\n=== {backend_name} ===', flush=True)
        qam = QAM(token=token, backend=backend_name)
        if not qam.backend:
            print(f'  ❌ Nem sikerült csatlakozni', flush=True)
            continue
        print(f'Backend: {qam.backend.name} ({qam.backend.configuration().n_qubits} qubits)', flush=True)

        time.sleep(3)
        # 1-qubit
        print('🚀 1-qubit SYnc (H·X·H = Z)...', flush=True)
        r1 = qam.sync_operation(qubits=1, shots=1024)
        print(f'  job_id: {r1["job_id"]}', flush=True)
        print(f'  success_rate: {r1["success_rate"]:.4f} ({r1["success_rate"]*100:.2f}%)', flush=True)
        print(f'  entropy: {float(r1["entropy"]):.4f}', flush=True)
        print(f'  time: {r1["time_us"]/1e6:.1f}s', flush=True)
        print(f'  result_type: {r1["result_type"]}', flush=True)

        # 5-qubit
        time.sleep(5)
        print('\n🚀 5-qubit SYnc (H·X·H = Z)...', flush=True)
        r5 = qam.sync_operation(qubits=5, shots=1024)
        print(f'  job_id: {r5["job_id"]}', flush=True)
        print(f'  success_rate: {r5["success_rate"]:.4f} ({r5["success_rate"]*100:.2f}%)', flush=True)
        print(f'  entropy: {float(r5["entropy"]):.4f}', flush=True)
        print(f'  time: {r5["time_us"]/1e6:.1f}s', flush=True)
        print(f'  result_type: {r5["result_type"]}', flush=True)

        results[backend_name] = {'1_qubit': r1, '5_qubit': r5}

        with open(f'results/qam_fixed_{backend_name}.json', 'w', encoding='utf-8') as f:
            json.dump(results[backend_name], f, indent=2, default=str)
        print(f'\n✅ Mentve: results/qam_fixed_{backend_name}.json', flush=True)

    except Exception as e:
        print(f'  ❌ Hiba: {e}', flush=True)
        import traceback; traceback.print_exc()

# Also update the consolidated results file
if results:
    consolidated = {
        'project': 'Quantum Anchored Memory (QAM)',
        'circuit': 'H·X·H = Z (fixed SYnc — H·X·H=Z, Z|0⟩=|0⟩ → annihilation → |0⟩)',
        'note': 'Original bug: H×H×H = H (not identity). Fixed: H·X·H = Z.',
        'results': results
    }
    with open('results/qam_fixed_all_results.json', 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, indent=2, default=str)
    print(f'\n✅ Összesítve: results/qam_fixed_all_results.json', flush=True)
