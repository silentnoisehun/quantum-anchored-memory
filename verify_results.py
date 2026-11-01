#!/usr/bin/env python3
"""
Offline audit verifier for the committed hardware measurement records in results/.
Recomputes exact proportions, Wilson 95% confidence intervals, and analytical
control expectations using only the Python standard library.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def wilson_ci(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    half = z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * total)) / total) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    results_dir = repo_root / "results"
    errors: list[str] = []

    print("=" * 70)
    print("QAM HARDWARE AUDIT TRAIL VERIFIER")
    print("=" * 70)

    # 1. Verify primary Loschmidt Echo run on ibm_kingston physical qubit 91
    sync_path = results_dir / "qam_sync_real_test.json"
    sync_data = json.loads(sync_path.read_text(encoding="utf-8"))

    theta = float(sync_data["angles"]["theta"])
    expected_ctrl = (math.cos(theta / 2.0) ** 2) * 100.0
    recorded_exp_ctrl = float(sync_data["expected_control_p0"])
    if abs(expected_ctrl - recorded_exp_ctrl) > 1e-6:
        errors.append(f"Control expectation mismatch: {expected_ctrl} vs {recorded_exp_ctrl}")

    sync_counts = sync_data["sync"]["counts"]
    sync_total = sum(int(v) for v in sync_counts.values())
    sync_zeros = int(sync_counts.get("0", 0))
    if sync_total != 1024 or sync_zeros != 1018:
        errors.append(f"Unexpected sync counts in qam_sync_real_test.json: {sync_counts}")
    if not sync_data["sync"].get("job_id"):
        errors.append("Missing sync job_id in qam_sync_real_test.json")

    ctrl_counts = sync_data["control"]["counts"]
    ctrl_total = sum(int(v) for v in ctrl_counts.values())
    ctrl_zeros = int(ctrl_counts.get("0", 0))
    if ctrl_total != 1024 or ctrl_zeros != 157:
        errors.append(f"Unexpected control counts in qam_sync_real_test.json: {ctrl_counts}")
    if not sync_data["control"].get("job_id"):
        errors.append("Missing control job_id in qam_sync_real_test.json")

    sync_ci = wilson_ci(sync_zeros, sync_total)
    ctrl_ci = wilson_ci(ctrl_zeros, ctrl_total)

    print(
        f"[OK] Loschmidt Echo (ibm_kingston, q91, job={sync_data['sync']['job_id']}): "
        f"{sync_zeros}/{sync_total} = {sync_zeros / sync_total * 100:.2f}% "
        f"(Wilson 95% CI [{sync_ci[0] * 100:.2f}%, {sync_ci[1] * 100:.2f}%])"
    )
    print(
        f"[OK] Control U|0>   (ibm_kingston, q91, job={sync_data['control']['job_id']}): "
        f"{ctrl_zeros}/{ctrl_total} = {ctrl_zeros / ctrl_total * 100:.2f}% "
        f"(Wilson 95% CI [{ctrl_ci[0] * 100:.2f}%, {ctrl_ci[1] * 100:.2f}%], "
        f"theory cos²(θ/2) = {expected_ctrl:.2f}%)"
    )

    # 2. Verify optimized H·X·H -> RZ jobs (1Q, 5Q, 10Q)
    opt1 = json.loads((results_dir / "qam_optimized_results.json").read_text(encoding="utf-8"))
    opt_multi = json.loads((results_dir / "qam_optimized_jobs.json").read_text(encoding="utf-8"))

    for label, rec, zero_key in (
        ("1Q opt=3", opt1, "0"),
        ("5Q opt=3", opt_multi["5qubit"], "00000"),
        ("10Q opt=3", opt_multi["10qubit"], "0000000000"),
    ):
        counts = rec["counts"]
        tot = sum(int(v) for v in counts.values())
        zh = int(counts.get(zero_key, 0))
        if tot != 1024:
            errors.append(f"{label}: expected 1024 shots, got {tot}")
        ci = wilson_ci(zh, tot)
        print(
            f"[OK] {label:<9} (ibm_kingston, job={rec['job_id']}): "
            f"{zh}/{tot} = {zh / tot * 100:.2f}% "
            f"(Wilson 95% CI [{ci[0] * 100:.2f}%, {ci[1] * 100:.2f}%])"
        )

    # 3. Verify all JSON files in results/ parse cleanly
    json_files = sorted(results_dir.glob("*.json"))
    for jf in json_files:
        try:
            json.loads(jf.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON in {jf.name}: {exc}")
    print(f"[OK] Parsed {len(json_files)} JSON artifact(s) in results/")

    if errors:
        print("\nAUDIT FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("=" * 70)
    print("RESULT: PASS — all committed hardware records verified.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
