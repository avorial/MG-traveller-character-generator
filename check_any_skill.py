"""
Find all skill_table entries with 'Any', 'Life Event', and unusual formats
to check they're all handled in the engine.
"""
import json, os, glob, re

career_dir = 'app/data/careers'
files = glob.glob(os.path.join(career_dir, '*.json'))

# Known special handled values
KNOWN_SPECIAL = {
    "Life Event", "K'kree Life Event",
    "Any psionic skill", "Caste",
    # Droyne caste-specific
    "Appeal", "Flight", "Prediction", "Ancients Tech",
}

weird_entries = []
for fp in sorted(files):
    with open(fp, encoding='utf-8-sig') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue
    cid = data.get('id', os.path.basename(fp).replace('.json', ''))
    for tname, table in (data.get('skill_tables') or {}).items():
        if not isinstance(table, dict):
            continue
        for k, v in table.items():
            if k == 'name':
                continue
            if not isinstance(v, str):
                continue
            entry = v.strip()
            # Check for "Any" pattern that isn't known
            if 'any' in entry.lower() and entry not in KNOWN_SPECIAL:
                weird_entries.append((cid, tname, k, entry))

if weird_entries:
    print(f"Potentially unhandled 'Any' skill entries ({len(weird_entries)}):")
    for cid, tname, k, entry in weird_entries:
        print(f"  {cid}.{tname}[{k}]: '{entry}'")
else:
    print("No unhandled 'Any' skill entries found!")
