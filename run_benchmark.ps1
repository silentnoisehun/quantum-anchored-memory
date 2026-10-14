# QAM benchmark futtató script
$env:IBM_QUANTUM_TOKEN = (Get-Content "C:\Users\mater\.codync\bots\69ea5c5b-5783-44fd-9c74-505d948621ce\workspace\uploads\f5ecde4c-1606-4c56-901b-3198edf6e08c\apikey.json" | ConvertFrom-Json).apikey
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "."
chcp 65001 > $null
cd C:\Users\mater\.codync\bots\69ea5c5b-5783-44fd-9c74-505d948621ce\workspace\qam
python -u run_qam_benchmark.py > results\qam_full_benchmark.log 2>&1
