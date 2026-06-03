"""
Check that each career's event table has entries for dice values 2-12.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find _EVENT_EFFECTS section start
start_line = None
for i, line in enumerate(lines):
    if '_EVENT_EFFECTS:' in line and '= {' in line:
        start_line = i
        break

if start_line is None:
    print("ERROR: _EVENT_EFFECTS not found")
    exit(1)

career_dice = {}
current_career = None
depth = 0

for i in range(start_line, len(lines)):
    line = lines[i]
    stripped = line.strip()

    opens = stripped.count('{')
    closes = stripped.count('}')

    if depth == 1:
        cm = re.match(r'"([a-z_]+)":\s*\{', stripped)
        if cm:
            current_career = cm.group(1)
            career_dice[current_career] = set()
            depth += opens - closes
            continue

    if depth == 2 and current_career:
        km = re.match(r'^(\d+):\s*[\[\{]', stripped)
        if km:
            career_dice[current_career].add(int(km.group(1)))

    depth += opens - closes

    if depth <= 0 and i > start_line:
        break

print(f"Total careers in _EVENT_EFFECTS: {len(career_dice)}")
issues = []
for cid, keys in sorted(career_dice.items()):
    missing = set(range(2, 13)) - keys
    extra = keys - set(range(2, 13))
    if missing:
        issues.append(f"  {cid}: missing #{sorted(missing)} (has: {sorted(keys)})")
    if extra:
        issues.append(f"  {cid}: unexpected keys {sorted(extra)}")

if issues:
    print(f"\nIssues ({len(issues)}):")
    for issue in issues:
        print(issue)
else:
    print("All event tables have entries 2-12!")
