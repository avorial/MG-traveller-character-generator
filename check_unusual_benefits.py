"""
Check potentially unhandled benefit types in _apply_benefit.
"""
import json, os, glob, re

career_dir = 'app/data/careers'
files = glob.glob(os.path.join(career_dir, '*.json'))

# Collect benefit-career mappings
unusual = []
for fp in sorted(files):
    with open(fp, encoding='utf-8-sig') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue
    cid = data.get('id', os.path.basename(fp).replace('.json', ''))
    mo = data.get('mustering_out')
    if not mo or not isinstance(mo, dict):
        continue
    for k, row in mo.items():
        if isinstance(row, dict):
            b = row.get('benefit', '')
            if not b:
                continue
            # Check for PSI +1 or PSI +2
            if re.match(r'^PSI\s*\+\d+$', b, re.IGNORECASE):
                unusual.append((cid, k, b, 'PSI bonus not in stat loop'))
            # Check for "Reduce Large/Small Debt"
            if 'reduce' in b.lower() and 'debt' in b.lower():
                unusual.append((cid, k, b, 'Debt reduction - becomes equipment'))
            # Check for D3/D6 associates
            if re.match(r'^D\d+\s+', b, re.IGNORECASE):
                unusual.append((cid, k, b, 'Dice-count benefit - may become equipment'))
            # Check for compound comma benefits
            if ',' in b and ' or ' in b:
                unusual.append((cid, k, b, 'Compound comma-or benefit - complex handling'))

if unusual:
    print(f"Unusual benefits ({len(unusual)}):")
    for cid, k, b, reason in unusual:
        print(f"  {cid}[{k}]: '{b}' ({reason})")
else:
    print("No unusual benefits found!")
