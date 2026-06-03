"""
Check all career JSONs for null or missing mustering_out.
Also check for the Profession (K'kree ritual) capitalisation in skill tables.
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
            issues.append(f"JSON ERROR: {os.path.basename(fp)}: {e}")
            continue

    cid = data.get('id', os.path.basename(fp).replace('.json', ''))
    mo = data.get('mustering_out')
    if mo is None and 'mustering_out' not in data:
        issues.append(f"{cid}: key 'mustering_out' is absent entirely")
    # null is handled by engine now, so just note it
    elif mo is None:
        print(f"NOTE: {cid} has mustering_out=null (engine will grant 0 rolls)")

    # Check skill_table values for K'kree ritual capitalisation
    for tname, table in (data.get('skill_tables') or {}).items():
        for k, v in (table.items() if isinstance(table, dict) else {}):
            if isinstance(v, str) and "k'kree ritual" in v.lower() and v != "Profession (K'kree Ritual)":
                issues.append(f"{cid}.skill_tables.{tname}[{k}]: '{v}' should be 'Profession (K'kree Ritual)'")

if issues:
    print(f"\nIssues ({len(issues)}):")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\nAll career JSONs look good!")
