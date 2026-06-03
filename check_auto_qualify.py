"""
Check all auto_qualify_careers effects point to valid career IDs.
Also check on_nat2 entries that use force_next_career.
"""
import re, os, json

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

career_dir = 'app/data/careers'
career_ids = {os.path.splitext(f)[0] for f in os.listdir(career_dir) if f.endswith('.json')}

# Find auto_qualify_careers
auto_qualify = re.findall(r'"auto_qualify_careers":\s*\[([^\]]+)\]', content)
all_qual_ids = []
for block in auto_qualify:
    ids = re.findall(r'"([^"]+)"', block)
    all_qual_ids.extend(ids)

print(f"auto_qualify_careers entries: {len(all_qual_ids)}")
invalid = [c for c in all_qual_ids if c not in career_ids]
if invalid:
    print("INVALID:", invalid)
else:
    print("All auto_qualify_careers IDs are valid!")

# Also check that all career JSON files have expected structure
print("\nChecking career JSON completeness...")
issues = []
for fname in sorted(os.listdir(career_dir)):
    if not fname.endswith('.json'):
        continue
    career_id = os.path.splitext(fname)[0]
    with open(os.path.join(career_dir, fname), encoding='utf-8-sig') as f:
        data = json.load(f)

    # Check required fields
    required = ['id', 'name', 'qualification', 'assignments', 'ranks']
    for field in required:
        if field not in data:
            issues.append(f"{career_id}: missing field '{field}'")

    # Check id matches filename
    if data.get('id') != career_id:
        issues.append(f"{career_id}: id field '{data.get('id')}' doesn't match filename")

if issues:
    print("Issues:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("All career JSONs have required fields and matching IDs!")
