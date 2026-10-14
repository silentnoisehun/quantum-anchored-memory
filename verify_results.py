# -*- coding: utf-8 -*-
import json

# Check qam_real_results.json
d = json.load(open('results/qam_real_results.json', encoding='utf-8'))
print('qam_real_results.json:')
print('  sync_operations:', len(d['results']['sync_operations']))
for s in d['results']['sync_operations']:
    test = s.get('test', 'unknown')
    sr = s.get('success_rate', 0)
    print(f'  {test}: P(0)={sr*100:.2f}%')

print()
raw = json.load(open('results/qam_raw_output.json', encoding='utf-8'))
print('qam_raw_output.json keys:', list(raw.keys()))
print('  calibration_tests:', len(raw.get('calibration_tests', [])))
print('  corrected_sync:', 'loschmidt_echo_qbit91' in raw.get('corrected_sync_results', {}))

print()
sync = json.load(open('results/qam_sync_real_test.json', encoding='utf-8'))
print('qam_sync_real_test.json:')
print(f"  sync: P(0)={sync['sync']['p0']:.2f}%  counts={sync['sync']['counts']}")
print(f"  control: P(0)={sync['control']['p0']:.2f}%  counts={sync['control']['counts']}")
print(f"  ratio: {sync['sync']['p0'] / sync['control']['p0']:.2f}x")
print(f"  qubit: {sync['physical_qubit']}")
