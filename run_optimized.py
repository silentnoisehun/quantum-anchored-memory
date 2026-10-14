"""Submit fixed SYnc job to IBM Quantum — optimized circuit, then retrieve result later."""
import json, os, sys

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import Sampler

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

# Build circuit: H·X·H = Z (kioltás)
qc = QuantumCircuit(1)
qc.h(0)
qc.x(0)
qc.h(0)
qc.measure_all()

qam = QAM(token=token, backend='ibm_kingston')
backend = qam.backend

# Optimize to minimal circuit
tqc = transpile(qc, backend, optimization_level=3, seed_transpiler=42)
print(f'Transpiled gates: {tqc.count_ops()}', flush=True)
print(f'Transpiled depth: {tqc.depth()}', flush=True)

# Submit job
sampler = Sampler(backend)
job = sampler.run([tqc], shots=1024)
job_id = job.job_id()
print(f'Job ID: {job_id}', flush=True)

# Save job ID for later retrieval
job_info = {
    'job_id': job_id,
    'backend': 'ibm_kingston',
    'circuit': 'H·X·H = Z (opt_level=3 → RZ gate)',
    'qubits': 1,
    'shots': 1024,
    'transpiled_gates': tqc.count_ops(),
    'submitted_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
}
with open('results/qam_optimized_job.json', 'w', encoding='utf-8') as f:
    json.dump(job_info, f, indent=2, default=str)
print('Saved job info to results/qam_optimized_job.json', flush=True)

# Try to get result immediately
try:
    result = job.result()
    counts = result[0].data.meas.get_counts()
    success_rate = counts.get('0', 0) / 1024
    print(f'\n✅ RESULT:', flush=True)
    print(f'  success_rate: {success_rate:.4f} ({success_rate*100:.2f}%)', flush=True)
    print(f'  counts: {counts}', flush=True)
    
    output = {**job_info, 'success_rate': success_rate, 'counts': counts, 'result_type': 'quantum'}
    with open('results/qam_optimized_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)
    print('Saved to results/qam_optimized_results.json', flush=True)
except Exception as e:
    print(f'\n⏳ Job még fut (vagy hiba): {e}', flush=True)
    print('Job ID mentve, később visszakeressük.', flush=True)
