"""
QAM Full Benchmark Runner – valós quantum futás IBM Quantum hardware-en.
"""
import os, sys, json, traceback

# Python 3.14 dataclasses patch – qiskit-ibm-runtime importhoz
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.qam_benchmark import main

# Override sys.argv for the benchmark
sys.argv = ["qam_benchmark.py", "--backend", "ibm_kingston"]

output_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "results", "qam_full_benchmark.log"))
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# UTF-8 fájl nyitása – hogy az emoji-k (🚀🌊✅) ne legyenek problémák
with open(output_file, "w", encoding="utf-8") as f:
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, data):
            for file_obj in self.files:
                try:
                    file_obj.write(data)
                    file_obj.flush()
                except Exception:
                    pass  # Encoding hiba esetén ne omoljon össze
        def flush(self):
            for file_obj in self.files:
                try:
                    file_obj.flush()
                except Exception:
                    pass

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Tee(sys.__stdout__, f)
    sys.stderr = Tee(sys.__stderr__, f)

    try:
        main()
        f.write("\n=== BENCHMARK COMPLETE ===\n")
    except Exception as e:
        f.write(f"\n=== ERROR ===\n")
        f.write(str(e) + "\n")
        f.write(traceback.format_exc())
        f.write("\n=== ENDED WITH ERROR ===\n")
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
