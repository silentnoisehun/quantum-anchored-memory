"""
QAM Teljes Benchmark Suite
===========================
Futtatás: python3 qam_benchmark.py --token YOUR_TOKEN --backend ibm_heron

Ezt a scriptet a QAM (Quantum Anchored Memory) projekt részeként írtuk.
A micropscope-memory integrációval és a wave-quantum kódolással kombinálva.
"""

from src.qam_core import QAM
from src.qam_memory import QAMMemory
from src.qam_quantum import QAMQuantum

import argparse
import json
import os
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="QAM Benchmark Suite")
    parser.add_argument("--token", type=str, help="IBM Quantum API kulcs")
    parser.add_argument("--backend", type=str, default="ibm_heron", help="Backend név")
    parser.add_argument("--qubits", type=int, default=5, help="Qubit szám")
    args = parser.parse_args()

    # Token beolvasása környezeti változóból ha nincs megadva
    token = args.token or os.environ.get("IBM_QUANTUM_TOKEN")

    print("=" * 60)
    print("🚀 QAM Benchmark Suite – Quantum Anchored Memory")
    print("=" * 60)
    print(f"  Backend: {args.backend}")
    print(f"  Token:   {'✅ beállítva' if token else '❌ hiányzik (szimulátor módban)'}")
    print("=" * 60)

    qam = QAM(token=token, backend=args.backend)
    results = []

    # --- SYnc művelet benchmark ---
    print("\n🔍 SYnc művelet benchmark (ψ(t) + Echo → 0 → ψ'(t))...")
    for qubits in [1, 5, 10]:
        try:
            res = qam.sync_operation(qubits=qubits)
            results.append(res)
            print(f"   ✅ Qubits: {qubits:2d}, Idő: {res['time_us']:.1f} µs, "
                  f"Siker: {res['success_rate']*100:.2f}%, "
                  f"Entropia: {res['entropy']:.4f}, "
                  f"Mód: {res.get('result_type', 'quantum')}")
        except Exception as e:
            print(f"   ❌ Qubits: {qubits}: {str(e)[:60]}")

    # --- Koherencia benchmark ---
    print("\n🔍 Koherencia benchmark...")
    try:
        res = qam.coherence_test(qubits=5)
        results.append(res)
        print(f"   ✅ Koherencia: {res['coherence']*100:.4f}%, Mód: {res.get('result_type', 'quantum')}")
    except Exception as e:
        print(f"   ❌ Koherencia: {str(e)[:60]}")

    # --- Memory integráció benchmark ---
    print("\n🔍 Memory integráció (microscope-memory D0-D8)...")
    try:
        qam_mem = QAMMemory(token=token, backend=args.backend)
        mem_result = qam_mem.store_quantum_memory("QAM_TEST_DATA", depth=9)
        results.append(mem_result)
        print(f"   ✅ Memória tárolás: depth={mem_result['depth']}, "
              f"idő: {mem_result['qam_result']['time_us']:.1f} µs")

        recall_result = qam_mem.recall_quantum_memory("QAM_TEST_DATA", depth=9)
        results.append(recall_result)
        print(f"   ✅ Memória visszaállítás: {recall_result['result']}")
    except Exception as e:
        print(f"   ❌ Memory: {str(e)[:60]}")

    # --- Wave-Quantum integráció benchmark ---
    print("\n🔍 Wave-Quantum integráció (Pearson 0.87-0.999)...")
    try:
        qam_q = QAMQuantum(token=token, backend=args.backend)
        wq_result = qam_q.wave_quantum_encoding("QAM_WAVE_DATA", qubits=5)
        results.append(wq_result)
        print(f"   ✅ Wave encoding: Pearson = {wq_result['pearson']:.4f}")
    except Exception as e:
        print(f"   ❌ Wave-Quantum: {str(e)[:60]}")

    # --- Eredmények mentése ---
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(results_dir, exist_ok=True)

    filepath = os.path.join(results_dir, f"qam_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print(f"✅ Benchmark kész! Eredmények: {filepath}")
    print("=" * 60)

    # Kiírja a legfontosabb eredményeket
    sync_results = [r for r in results if "time_us" in r]
    if sync_results:
        avg_time = sum(r["time_us"] for r in sync_results) / len(sync_results)
        print(f"\n📊 Összefoglalás:")
        print(f"   Átlag SYnc idő: {avg_time:.1f} µs")
        print(f"   Cél (< 10 µs): {'✅ Elértük' if avg_time < 10 else '⚠️'}")

    cohe_results = [r for r in results if "coherence" in r]
    if cohe_results:
        avg_cohe = sum(r["coherence"] for r in cohe_results) / len(cohe_results)
        print(f"   Átlag koherencia: {avg_cohe*100:.2f}%")
        print(f"   Cél (> 99%): {'✅ Elértük' if avg_cohe > 0.99 else '⚠️'}")


if __name__ == "__main__":
    main()
