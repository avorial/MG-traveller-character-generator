"""
Find all unique benefit strings across all career mustering_out tables.
Check for any that might not be handled by the engine.
"""
import json, os, glob

career_dir = 'app/data/careers'
files = glob.glob(os.path.join(career_dir, '*.json'))

benefit_values = set()
for fp in sorted(files):
    with open(fp, encoding='utf-8-sig') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue
    mo = data.get('mustering_out')
    if not mo or not isinstance(mo, dict):
        continue
    for k, row in mo.items():
        if isinstance(row, dict):
            b = row.get('benefit')
            if b:
                benefit_values.add(b)

print(f"Total unique benefit values: {len(benefit_values)}")
for b in sorted(benefit_values):
    print(f"  {b}")
