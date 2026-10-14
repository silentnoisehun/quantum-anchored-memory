# -*- coding: utf-8 -*-
"""Update qam_core.py: sync_operation uses Loschmidt Echo + opt_level=0 + initial_layout."""
import re

with open('src/qam_core.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace sync_operation signature + docstring + circuit + transpile call
# Find the old method body (from 'def sync_operation' to 'elapsed = time.time() - start')
old_pattern = re.compile(
    r'    def sync_operation\(self, qubits=5, shots=1024\):.*?elapsed = time\.time\(\) - start',
    re.DOTALL
)

new_method = '''    def sync_operation(self, qubits=5, shots=1024, opt_level=0, initial_layout=None):
        """
        SYnc művelet: psi(t) + Echo(pi) -> 0 -> psi'(t)

        Valódi Loschmidt Echo megközelites:
          1. psi(t) = U|0>       (veletlen allapot)
          2. Echo(pi) = U†      (inverz kapu)
          3. SYnc: U·U†|0> = |0> (destruktiv interferencia)

        Ket kritikus parameter:
        - opt_level=0 (alapertelmezett): megorzi a kapukat!
          (opt_level=3 a U·U†=I-t torli -> trivalisan ~99.8%)
        - initial_layout: a jo fizikai qubit megadasa!
          (opt_level=0 a qbit 0-at valasztja, ami rossz lehet)

        Ha initial_layout=None es qubits==1, akkor opt_level=3-mal megtalalja a
        jol mukodo fizikai qubitet, majd opt_level=0-val fut a teszt rajta.
        """
        if not self.backend:
            return self._simulated_sync(qubits=qubits, shots=shots)

        # --- Qubit kivalasztas: ha nincs explicit layout, hasznaljunk opt_level=3-at ---
        if initial_layout is None and qubits == 1:
            qc_tmp = QuantumCircuit(1)
            qc_tmp.x(0)
            qc_tmp.x(0)  # X·X = I -> semmi kapu
            qc_tmp.measure_all()
            tqc_tmp = transpile(qc_tmp, self.backend, optimization_level=3,
                                seed_transpiler=42)
            vbits = tqc_tmp.layout.initial_layout.get_virtual_bits()
            good_qubits = [v for q, v in vbits.items() if 'ancilla' not in repr(q)]
            initial_layout = good_qubits[:qubits] if good_qubits else None
            print(f"  Auto-detected good qubit: {initial_layout[0] if initial_layout else 'None'}", flush=True)

        # --- Loschmidt Echo kor: U|0> -> U† -> |0> ---
        np.random.seed(42)
        qc = QuantumCircuit(qubits)

        for q in range(qubits):
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, 2 * np.pi)
            lam = np.random.uniform(0, 2 * np.pi)
            qc.u(theta, phi, lam, q)            # psi(t) = U|0>
            qc.barrier()
            qc.u(theta, phi, lam, q).inverse()  # Echo = U†
            qc.barrier()

        qc.measure_all()

        # Transpile — FONTOS: opt_level=0 a kapuk megorzese erdekeben!
        transpile_kwargs = {
            'optimization_level': opt_level,
            'seed_transpiler': 42,
        }
        if initial_layout is not None:
            transpile_kwargs['initial_layout'] = initial_layout
        qc = transpile(qc, self.backend, **transpile_kwargs)

        sampler = Sampler(self.backend)
        start = time.time()
        job = sampler.run([qc], shots=shots)
        result = job.result()
        elapsed = time.time() - start'''

content_new = old_pattern.sub(new_method, content, count=1)

if content_new == content:
    print("ERROR: No replacement made — pattern not found!")
else:
    print("OK: sync_operation replaced")

    # 2. Also update the simulated sync docstring for consistency
    old_sim = "        # H·X·H = Z → Z|0⟩ = |0⟩ → ~100% siker"
    new_sim = "        # U·U† = I → I|0⟩ = |0⟩ → ~100% siker"
    if old_sim in content_new:
        content_new = content_new.replace(old_sim, new_sim)
        print("OK: simulated sync comment updated")

    with open('src/qam_core.py', 'w', encoding='utf-8') as f:
        f.write(content_new)
    print("✅ qam_core.py mentve")
