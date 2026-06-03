"""
Check benefit tables: ensure all careers have benefit entries and
check for unusual benefit amounts.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find _BENEFIT_TABLES section
start_line = None
for i, line in enumerate(lines):
    if '_BENEFIT_TABLES' in line and '= {' in line:
        start_line = i
        break

if start_line is None:
    print("ERROR: _BENEFIT_TABLES not found")
    exit(1)

# Find _EVENT_EFFECTS to see all expected careers
event_start = None
for i, line in enumerate(lines):
    if '_EVENT_EFFECTS:' in line and '= {' in line:
        event_start = i
        break

# Get careers from _EVENT_EFFECTS
event_careers = set()
event_depth = 0
for i in range(event_start, len(lines)):
    stripped = lines[i].strip()
    opens = stripped.count('{'); closes = stripped.count('}')
    if event_depth == 1:
        cm = re.match(r'"([a-z_]+)":\s*\{', stripped)
        if cm:
            event_careers.add(cm.group(1))
    event_depth += opens - closes
    if event_depth <= 0 and i > event_start:
        break

# Get careers from _BENEFIT_TABLES
benefit_careers = set()
benefit_depth = 0
for i in range(start_line, len(lines)):
    stripped = lines[i].strip()
    opens = stripped.count('{'); closes = stripped.count('}')
    if benefit_depth == 1:
        cm = re.match(r'"([a-z_]+)":\s*\{', stripped)
        if cm:
            benefit_careers.add(cm.group(1))
    benefit_depth += opens - closes
    if benefit_depth <= 0 and i > start_line:
        break

print(f"Careers in events: {len(event_careers)}")
print(f"Careers in benefit tables: {len(benefit_careers)}")

missing_benefits = event_careers - benefit_careers
if missing_benefits:
    print(f"\nCareers missing from benefit tables: {sorted(missing_benefits)}")
else:
    print("All careers have benefit tables!")

extra_benefits = benefit_careers - event_careers
if extra_benefits:
    print(f"\nBenefit-only careers (not in events): {sorted(extra_benefits)}")
