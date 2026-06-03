"""
Check mishap table completeness by examining actual lifepath.py content
using the Python interpreter to load the data directly.
"""
import sys, os
sys.path.insert(0, os.path.abspath('.'))

# We can't import the module directly (FastAPI deps), so parse more carefully
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find the _MISHAP_EFFECTS section start
start_line = None
end_line = None
for i, line in enumerate(lines):
    if '_MISHAP_EFFECTS: dict' in line and '= {' in line:
        start_line = i
        break

if start_line is None:
    print("ERROR: not found")
    exit(1)

# Walk forward to find all top-level "career_id": { keys and their dice keys
# Track brace depth: at depth=1 we're inside _MISHAP_EFFECTS (top-level careers)
# at depth=2 we're inside a career's dict (mishap numbers)
career_dice = {}  # career_id -> set of dice numbers
current_career = None
depth = 0

for i in range(start_line, len(lines)):
    line = lines[i]
    stripped = line.strip()

    # Count brace changes
    opens = stripped.count('{')
    closes = stripped.count('}')

    # Check for career key pattern at depth=1 (right after opening brace of _MISHAP_EFFECTS)
    if depth == 1:
        cm = re.match(r'"([a-z_]+)":\s*\{', stripped)
        if cm:
            current_career = cm.group(1)
            career_dice[current_career] = set()
            # The opening brace for this career is on this line
            depth += opens - closes
            continue

    # Check for dice key pattern at depth=2 (inside a career dict)
    if depth == 2 and current_career:
        km = re.match(r'^(\d+):\s*[\[\{]', stripped)
        if km:
            career_dice[current_career].add(int(km.group(1)))

    depth += opens - closes

    # Stop if we've exited _MISHAP_EFFECTS
    if depth <= 0 and i > start_line:
        break

print(f"Total careers in _MISHAP_EFFECTS: {len(career_dice)}")
issues = []
for cid, keys in sorted(career_dice.items()):
    missing = set(range(1, 7)) - keys
    extra = keys - set(range(1, 7))
    if missing:
        issues.append(f"  {cid}: missing #{sorted(missing)} (has: {sorted(keys)})")
    if extra:
        issues.append(f"  {cid}: unexpected keys {sorted(extra)}")

if issues:
    print(f"\nIssues ({len(issues)}):")
    for issue in issues:
        print(issue)
else:
    print("All mishap tables have entries 1-6!")
