"""Run ONLY 1-qubit fixed SYnc on ibm_kingston — no other backends."""
import json, os, sys, time

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

print('🔧 ibm_kingston csatlakozás...', flush=True)
qam = QAM(token=token, backend='ibm_kingston')
print(f'Backend: {qam.backend.name} ({qam.backend.configuration().n_qubits} qubits)', flush=True)

time.sleep(3)
print('🚀 1-qubit SYnc (H·X·H = Z) — fut a valós kvantum hardware-n...', flush=True)

r1 = qam.sync_operation(qubits=1, shots=1024)
print(f'\n📊 EREDMÉNY:', flush=True)
print(f'  job_id:        {r1["job_id"]}', flush=True)
print(f'  success_rate:  {r1["success_rate"]:.4f} ({r1["success_rate"]*100:.2f}%)', flush=True)
print(f'  entropy:       {float(r1["entropy"]):.4f}', flush=True)
print(f'  time:          {r1["time_us"]/1e6:.1f}s', flush=True)
print(f'  backend:       {r1["backend"]}', flush=True)
print(f'  result_type:   {r1["result_type"]}', flush=True)

# Mentés
with open('results/qam_fixed_kingston.json', 'w', encoding='utf-8') as f:
    json.dump(r1, f, indent=2, default=str)
print(f'\n✅ Mentve: results/qam_fixed_kingston.json', flush=True)
