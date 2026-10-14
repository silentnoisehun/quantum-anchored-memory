"""One-shot test: run a single SYnc operation on real quantum hardware."""
import os, sys, json
# Apply the Python 3.14 dataclasses patch before importing qiskit_ibm_runtime
import dataclasses as _dc
_orig_fields = _dc.fields
def _patched_fields(cls):
    try:
        return _orig_fields(cls)
    except (AttributeError, TypeError):
        try:
            fd = cls.__dataclass_fields__
            if isinstance(fd, dict):
                return tuple(f for f in fd.values() if getattr(f, "_field_type", _dc._FIELD) is _dc._FIELD)
        except:
            pass
        return ()
_dc.fields = _patched_fields

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.qam_core import QAM

token = os.environ.get("IBM_QUANTUM_TOKEN")
backend_name = os.environ.get("QAM_BACKEND", "ibm_kingston")

try:
    with open(os.path.join(os.path.dirname(__file__), "..", "results", "qam_test_output.txt"), "w") as f:
        f.write(f"Token loaded: {len(token) if token else 0} chars\n")
        f.write(f"Backend: {backend_name}\n")
        f.write("Connecting to IBM Quantum...\n")
        f.flush()

    qam = QAM(token=token, backend=backend_name)
    backend_str = qam.backend.name if qam.backend else "None"

    with open(os.path.join(os.path.dirname(__file__), "..", "results", "qam_test_output.txt"), "a") as f:
        f.write(f"Backend connected: {backend_str}\n")
        f.write("Running SYnc operation (1 qubit)...\n")
        f.flush()

    result = qam.sync_operation(qubits=1, shots=1024)

    with open(os.path.join(os.path.dirname(__file__), "..", "results", "qam_test_output.txt"), "a") as f:
        f.write(f"SYnc result: {json.dumps(result, default=str, indent=2)}\n")
        f.write("Running coherence test (5 qubits)...\n")
        f.flush()

    coh = qam.coherence_test(qubits=5, shots=1024)
    with open(os.path.join(os.path.dirname(__file__), "..", "results", "qam_test_output.txt"), "a") as f:
        f.write(f"Coherence: {json.dumps(coh, default=str, indent=2)}\n")
        f.write("DONE\n")

except Exception as e:
    with open(os.path.join(os.path.dirname(__file__), "..", "results", "qam_test_output.txt"), "a") as f:
        import traceback
        f.write(f"ERROR: {e}\n")
        f.write(traceback.format_exc())
        f.write("DONE_WITH_ERROR\n")
