"""
Validate career JSON files: check mustering_out table completeness.
"""
import json, os, glob

career_dir = 'app/data/careers'
files = glob.glob(os.path.join(career_dir, '*.json'))
issues = []

for fp in sorted(files):
    with open(fp, encoding='utf-8-sig') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            issues.append(f"JSON ERROR in {os.path.basename(fp)}: {e}")
            continue

    cid = data.get('id', os.path.basename(fp).replace('.json', ''))

    # Check mustering_out table
    mo = data.get('mustering_out', {})
    if not mo:
        issues.append(f"{cid}: no mustering_out table")
        continue

    keys = set(int(k) for k in mo.keys())
    expected = set(range(1, 8))  # 1-7
    missing = expected - keys
    extra = keys - expected
    if missing:
        issues.append(f"{cid}: mustering_out missing rolls {sorted(missing)} (has: {sorted(keys)})")
    if extra:
        issues.append(f"{cid}: mustering_out extra rolls {sorted(extra)}")

    # Check each entry has cash and benefit
    for k, v in mo.items():
        if 'cash' not in v:
            issues.append(f"{cid}: mustering_out[{k}] missing 'cash'")
        if 'benefit' not in v:
            issues.append(f"{cid}: mustering_out[{k}] missing 'benefit'")
        elif not v['benefit'].strip():
            issues.append(f"{cid}: mustering_out[{k}] 'benefit' is empty")

if issues:
    print(f"Career JSON issues ({len(issues)}):")
    for issue in issues[:60]:
        print(f"  {issue}")
else:
    print("All career mustering_out tables look valid!")
