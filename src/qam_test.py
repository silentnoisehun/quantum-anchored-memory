"""One-shot smoke runner for QAM (uses environment token if set, else local simulator)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.qam_core import QAM, resolve_ibm_token


def main() -> None:
    backend_name = os.environ.get("QAM_BACKEND", "ibm_kingston")
    token = resolve_ibm_token()
    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / "results" / "qam_test_output.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    qam = QAM(backend=backend_name, local=(token is None))
    sync_res = qam.sync_operation(qubits=1, shots=1024, include_control=True)
    coh_res = qam.coherence_test(qubits=5, shots=1024)

    lines = [
        f"Mode: {sync_res['result_type']} ({sync_res['evidence_grade']})",
        f"Backend: {sync_res['backend']}",
        f"SYnc result: {json.dumps(sync_res, indent=2, default=str)}",
        f"Coherence result: {json.dumps(coh_res, indent=2, default=str)}",
        "DONE",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({sync_res['result_type']})")


if __name__ == "__main__":
    main()
