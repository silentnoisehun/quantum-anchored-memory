"""Retrieve the job result for the optimized SYnc circuit."""
import json, os, sys, time

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM
from qiskit_ibm_runtime import QiskitRuntimeService

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

service = QiskitRuntimeService(token=token, instance='auto')

job_id = 'db7tthor1c5c738la3ig'
print(f'🔍 Visszakerem a jobot: {job_id}', flush=True)

job = service.job(job_id)
print(f'Státus: {job.status()}', flush=True)

# Wait for completion
for _ in range(60):
    status = job.status()
    s = str(status)
    print(f'  Státus: {s}', flush=True)
    if s in ('DONE', 'SUCCEEDED'):
        break
    if s in ('ERROR', 'CANCELED'):
        print(f'  Job hiba: {s}', flush=True)
        break
    print(f'  Várakozás... ({s})', flush=True)
    time.sleep(10)

# Get result
try:
    result = job.result()
    counts = result[0].data.meas.get_counts()
    success_rate = counts.get('0', 0) / 1024

    print(f'\n📊 EREDMÉNY (optimized H·X·H = RZ, ibm_kingston):', flush=True)
    print(f'  job_id:        {job_id}', flush=True)
    print(f'  success_rate:  {success_rate:.4f} ({success_rate*100:.2f}%)', flush=True)
    print(f'  counts:        {counts}', flush=True)
    print(f'  transpiled:    rz(1 gate) — opt_level=3', flush=True)

    output = {
        'backend': 'ibm_kingston',
        'circuit': 'H·X·H = Z → RZ gate (opt_level=3)',
        'qubits': 1,
        'shots': 1024,
        'job_id': job_id,
        'success_rate': success_rate,
        'counts': counts,
        'transpiled_gates': {'rz': 1, 'barrier': 1, 'measure': 1},
        'result_type': 'quantum',
        'retrieved_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
    }
    with open('results/qam_optimized_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\n✅ Mentve: results/qam_optimized_results.json', flush=True)

except Exception as e:
    print(f'❌ Hiba: {e}', flush=True)
    import traceback; traceback.print_exc()
