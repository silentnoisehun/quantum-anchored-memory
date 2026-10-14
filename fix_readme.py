# -*- coding: utf-8 -*-
"""Fix README — replace old Loschmidt Echo 45.31% section with 99.41% results."""
import re

with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old Loschmidt Echo section header and table
old_header = "### Valódi SYnc teszt (Loschmidt Echo) — opt_level=0 (gate-ek megőrzve)"
new_header = "### Valódi SYnc teszt (Loschmidt Echo) — opt_level=0, **qbit 91** (jó qubit)"
content = content.replace(old_header, new_header)

# Replace 45.31% row
old_sync_row = "| **SYnc (Echo)** | 10 (6rz+4sz) | **45.31%** | 464×`0`, 560×`1` | `db7uus8r1c5c738lc8i0` |"
new_sync_row = "| **SYnc (Echo)** | 10 (6rz+4sz) | **99.41%** | 1018×`0`, 6×`1` | ~99%+ | újrafuttatva |"
content = content.replace(old_sync_row, new_sync_row)

# Replace 20.51% control row
old_ctrl_row = "| **Control (nincs Echo)** | 5 (3rz+2sz) | **20.51%** | 210×`0`, 814×`1` | `db7uusur6oqs7388co40` |"
new_ctrl_row = "| **Control (nincs Echo)** | 5 (3rz+2sz) | **15.33%** | 157×`0`, 867×`1` | cos²(θ/2)=14.75% | újrafuttatva |"
content = content.replace(old_ctrl_row, new_ctrl_row)

# Replace the description text
old_desc = "**A SYnc tényleg működik!** 45.31% vs 20.51% — **2.2x fejlesztés**. A 45.31% alacsonyabb a 100%-nél, mert 10 gate zaj kumulálódik. A különbség a Kontroll és a SYnc között a valós kvantum interferencia bizonyítéka."
new_desc = "**A SYnc tényleg működik!** 99.41% vs 15.33% — **6.48x javulás**. A U·U† Echo visszaállítja a |0⟩ állapotot, és 99.41% a 99.80%-os opt_level=3 eredményhez közel áll (10 kapu hiba miatt enyhén alacsonyabb)."
content = content.replace(old_desc, new_desc)

# Replace the Javulási folyamat table — add the bad qubit row and update last row
old_phase = "| ✅ Valódi SYnc | U·U† (opt=0) | 10 | **45.31%** | `db7uus8r1c5c738lc8i0` |"
new_phases = "| ❌ Valódi SYnc (rossz qubit) | U·U† (opt=0) | 10 | 45.31% | **0** | ❌ `backend.properties()` hibás → rossz qubit |\n| ✅ **Valódi SYnc (jó qubit)** | U·U† (opt=0) | 10 | **99.41%** | **91** | ✅ `initial_layout=[91]` kulcsfontosságú |"
content = content.replace(old_phase, new_phases)

# Replace the old comment at the bottom
old_comment = "**Megjegyzés:** A 99.80% azért lehetséges `opt_level=3`-mal, mert a transpiler felismeri, hogy H·X·H = Z → RZ(π) (virtuális kapu, 0% hiba). A valódi SYnc teszt (opt_level=0, U·U† megőrzve) 45.31%-ot ér el — a valós kvantum interferencia bizonyítéka, a zaj miatt alacsonyabb. A Kontroll (20.51%) alacsonyabb, így a SYnc Echo-valán."
new_comment = """**Megjegyzés:** A 99.80% azért lehetséges `opt_level=3`-mal, mert a transpiler felismeri, hogy H·X·H = Z → RZ(π) (virtuális kapu, 0% hiba). A valódi SYnc teszthez két dolog szükséges:
1. **`initial_layout=[91]`** vagy `opt_level=1` — a transpiler `opt_level=0` alapból a qbit 0-át választotta (mert `backend.properties()` hibás vagy -1)
2. **`opt_level=0`** — a kapukat megőrítjük (a `opt_level=3` kitörli a U·U† = I-t, így csak mérés marad → triviálisan ~99.8%)
3. **A Heron család**: a `ibm_fez`, `ibm_kingston`, `ibm_marrakesh` mind Heron processzorok (nem egyedi gép nevek)
4. **Mitiq**: Python 3.14-en nem települ (`setuptools.build_meta` hiba), de a `qiskit_aer` szimulátor + manuális `initial_layout` elegendő"""
content = content.replace(old_comment, new_comment)

# Also add the diagnostic table before the optimized section
diag_table = """### Diagnosztikai teszt: miért 45.31% a rossz qbiten?
| Teszt | Qubit | P(0) | Megjegyzés |
|-------|-------|------|------------|
| X·X=I (szimulátor) | sim | **100.00%** | ✅ A kód helyes |
| X·X=I (hardware) | **0** (auto) | **49.32%** | ❌ Rossz qubit, `backend.properties()` hibás |
| X·X=I (hardware) | **91** (forced) | **99.32%** | ✅ Jó qubit |
| U·U† (hardware) | **91** (forced) | **99.41%** | ✅ SYnc működik! |

**A 45.31% rossz volt!** A transpiler `opt_level=0` alapból a qbit 0-át választotta (mert `backend.properties()` -1 mindenütt). A jó qbit 91-en `initial_layout`-el a teszt **99.41%**-ot ad.

"""
content = content.replace("### Optimalizált SYnc", diag_table + "### Optimalizált SYnc")

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: README frissítve")
