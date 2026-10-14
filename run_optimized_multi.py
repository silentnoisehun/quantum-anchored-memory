"""Submit optimized 5qubit + 10qubit SYnc (H·X·H → RZ) to ibm_kingston."""
import json, os, sys, time

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import Sampler

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

print('🔧 Csatlakozás ibm_kingston-hoz...', flush=True)
qam = QAM(token=token, backend='ibm_kingston')
print(f'Backend: {qam.backend.name} ({qam.backend.configuration().n_qubits} qubits)', flush=True)

# Save job info for later retrieval
job_infos = {}

for qubits in [5, 10]:
    try:
        print(f'\n🚀 {qubits}-qubit SYnc (H·X·H → RZ)...', flush=True)
        qc = QuantumCircuit(qubits)
        for q in range(qubits):
            qc.h(q)
            qc.x(q)
            qc.h(q)
        qc.measure_all()

        tqc = transpile(qc, qam.backend, optimization_level=3, seed_transpiler=42)
        print(f'  Transpiled: {tqc.count_ops()}', flush=True)

        time.sleep(3)
        sampler = Sampler(qam.backend)
        job = sampler.run([tqc], shots=1024)
        jid = job.job_id()
        print(f'  Job ID: {jid}', flush=True)

        job_infos[f'{qubits}qubit'] = {
            'job_id': jid,
            'qubits': qubits,
            'shots': 1024,
            'backend': 'ibm_kingston',
            'circuit': 'H·X·H = Z → RZ (opt_level=3)',
            'transpiled_gates': dict(tqc.count_ops()),
        }

        # Try immediate result
        try:
            result = job.result()
            counts = result[0].data.meas.get_counts()
            zero_key = '0' * qubits
            sr = counts.get(zero_key, 0) / 1024
            print(f'  ✅ success_rate: {sr:.4f} ({sr*100:.2f}%)', flush=True)
            print(f'  counts (top 5): {dict(list(counts.items())[:5])}', flush=True)
            job_infos[f'{qubits}qubit']['success_rate'] = sr
            job_infos[f'{qubits}qubit']['counts'] = counts
            job_infos[f'{qubits}qubit']['result_type'] = 'quantum'
        except Exception as e:
            print(f'  ⏳ Job még fut: {e}', flush=True)
            job_infos[f'{qubits}qubit']['status'] = 'pending'

    except Exception as e:
        print(f'  ❌ Hiba: {e}', flush=True)
        job_infos[f'{qubits}qubit'] = {'error': str(e)}

# Save job infos
with open('results/qam_optimized_jobs.json', 'w', encoding='utf-8') as f:
    json.dump(job_infos, f, indent=2, default=str)
print(f'\n✅ Job info mentve: results/qam_optimized_jobs.json', flush=True)
