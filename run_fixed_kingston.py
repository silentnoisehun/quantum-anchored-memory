"""Run fixed SYnc (H·X·H = Z) on ibm_kingston — single qubit only."""
import json
import os
import sys
import time
import traceback

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from src.qam_core import QAM

apikey_path = 'C:/Users/mater/.codync/bots/69ea5c5b-5783-44fd-9c74-505d948621ce/workspace/uploads/f5ecde4c-1606-4c56-901b-3198edf6e08c/apikey.json'
token = json.load(open(apikey_path)).get('apikey')

log_path = 'results/qam_fixed_run.log'
with open(log_path, 'w', encoding='utf-8') as f:
    f.write(f"QAM Fixed SYnc Run — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Backend: ibm_kingston\n")
    f.write(f"Circuit: H·X·H = Z (javított SYnc)\n\n")

    try:
        f.write("Connecting...\n")
        f.flush()
        qam = QAM(token=token, backend='ibm_kingston')
        f.write(f"Backend: {qam.backend.name}\n")
        f.write(f"n_qubits: {qam.backend.configuration().n_qubits}\n")
        f.flush()

        time.sleep(3)
        f.write("\n1-qubit SYnc (H·X·H = Z)...\n")
        f.flush()

        r1 = qam.sync_operation(qubits=1, shots=1024)
        f.write(f"  job_id: {r1['job_id']}\n")
        f.write(f"  success_rate: {r1['success_rate']:.4f} ({r1['success_rate']*100:.2f}%)\n")
        f.write(f"  entropy: {float(r1['entropy']):.4f}\n")
        f.write(f"  time_s: {r1['time_us']/1e6:.1f}\n")
        f.write(f"  result_type: {r1['result_type']}\n")
        f.flush()

        # Save immediately
        with open('results/qam_fixed_results.json', 'w', encoding='utf-8') as rf:
            json.dump({'backend': 'ibm_kingston', 'circuit': 'H·X·H = Z', '1_qubit': r1}, rf, indent=2, default=str)
        f.write("\n✅ 1-qubit eredmény mentve.\n")
        f.flush()

        # Now try 5-qubit
        time.sleep(5)
        f.write("\n5-qubit SYnc...\n")
        f.flush()
        r5 = qam.sync_operation(qubits=5, shots=1024)
        f.write(f"  job_id: {r5['job_id']}\n")
        f.write(f"  success_rate: {r5['success_rate']:.4f} ({r5['success_rate']*100:.2f}%)\n")
        f.write(f"  entropy: {float(r5['entropy']):.4f}\n")
        f.write(f"  time_s: {r5['time_us']/1e6:.1f}\n")
        f.write(f"  result_type: {r5['result_type']}\n")
        f.flush()

        # Save again
        with open('results/qam_fixed_results.json', 'w', encoding='utf-8') as rf:
            json.dump({'backend': 'ibm_kingston', 'circuit': 'H·X·H = Z', '1_qubit': r1, '5_qubit': r5}, rf, indent=2, default=str)
        f.write("\n✅ 5-qubit eredmény mentve.\n")
        f.write("\n✅ Mindkét eredmény mentve.\n")
        f.flush()

    except Exception as e:
        f.write(f"\n❌ HIBA: {e}\n")
        f.write(traceback.format_exc())
        f.flush()
