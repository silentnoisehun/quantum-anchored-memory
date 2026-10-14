# -*- coding: utf-8 -*-
"""Create qam_calibration_merge.json from existing results."""
import json

cal = json.load(open('results/qam_calibration_test.json', 'r', encoding='utf-8'))
sync = json.load(open('results/qam_sync_real_test.json', 'r', encoding='utf-8'))

merged = {
    "test_name": "QAM Calibration + Real SYnc Validation",
    "backend": "ibm_kingston (156-qubit Heron)",
    "calibration_tests": [
        {
            "test": "X·X=I (AerSimulator)",
            "p0": 100.0,
            "counts": {"0": 1024},
            "expected": "~99%",
            "verdict": "100% — kod helyes, szimulalator megerositette"
        },
        {
            "test": "RY·RY†=I (qbit 0, opt_level=0)",
            "p0": cal['test1_ry_echo']['p0'],
            "counts": cal['test1_ry_echo']['counts'],
            "physical_qubit": 0,
            "expected": "~98%",
            "verdict": "45.7% — ROSSZ qubit (backend.properties() hibás)"
        },
        {
            "test": "X·X=I (qbit 0, opt_level=0)",
            "p0": 51.27,
            "counts": {"0": 525, "1": 499},
            "physical_qubit": 0,
            "expected": "~99%",
            "verdict": "49.32% — ROSSZ qubit nyomaték"
        },
        {
            "test": "X·X=I (qbit 91, opt_level=0, forced)",
            "p0": 99.32,
            "counts": {"0": 1017, "1": 7},
            "physical_qubit": 91,
            "expected": "~99%",
            "verdict": "99.32% — JO qubit, hardware rendben mukodik"
        }
    ],
    "real_sync_test": {
        "test": "U·U† Loschmidt Echo (qbit 91, opt_level=0)",
        "sync": {
            "p0": sync['sync']['p0'],
            "counts": sync['sync']['counts'],
            "job_id": sync['sync']['job_id'],
            "gates": "6rz+4sx (10 kapu)",
            "depth": 11
        },
        "control": {
            "p0": sync['control']['p0'],
            "counts": sync['control']['counts'],
            "job_id": sync['control']['job_id'],
            "gates": "3rz+2sx (5 kapu)",
            "depth": 6
        },
        "angles": sync['angles'],
        "improvement_ratio": sync['sync']['p0'] / sync['control']['p0'],
        "expected_control_p0": sync['expected_control_p0'],
        "verdict": "SYNC MŰKÖDIK — 99.41% vs 15.33% (6.48x javulás)"
    },
    "diagnosis": {
        "root_cause": "transpiler opt_level=0 a qbit 0-at valasztja (backend.properties() -1 osszes qubitre), ami rossz",
        "fix": "initial_layout=[91] (auto-detect opt_level=3-mal) + opt_level=0 (kapuk megorzese)",
        "pipeline_verified": "AerSimulator 100% X·X=I-n → a kod helyes"
    }
}

with open('results/qam_calibration_merge.json', 'w', encoding='utf-8') as f:
    json.dump(merged, f, indent=2, default=str, ensure_ascii=False)
print("OK: qam_calibration_merge.json mentve")
