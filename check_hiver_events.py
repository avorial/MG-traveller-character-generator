"""
Check Hiver career event and mishap coverage.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find hiver career event table entries
hiver_careers = ['hiver_academic', 'hiver_generalist', 'hiver_manipulator', 'hiver_merchant']

for career in hiver_careers:
    # Find the career block in _EVENT_EFFECTS
    pattern = re.compile(rf'"{career}":\s*\{{([^}}]+(?:\{{[^}}]*\}}[^}}]*)*)\}}', re.DOTALL)
    m = pattern.search(content)
    if not m:
        print(f"{career}: NOT FOUND in event tables")
        continue
    block = m.group(1)
    # Count event entries
    entries = re.findall(r'^\s+(\d+):\s*\[', block, re.MULTILINE)
    print(f"{career}: events {sorted([int(e) for e in entries])}")

print()
# Check mishap tables too
print("=== MISHAP TABLES ===")
for career in hiver_careers:
    pattern = re.compile(rf'"{career}":\s*\{{([^}}]+(?:\{{[^}}]*\}}[^}}]*)*)\}}', re.DOTALL)
    # Find in mishap section (after _MISHAP_EFFECTS line)
    mishap_start = content.find('_MISHAP_EFFECTS')
    if mishap_start == -1:
        print("_MISHAP_EFFECTS not found!")
        break
    mishap_content = content[mishap_start:]
    m = pattern.search(mishap_content)
    if not m:
        print(f"{career}: NOT FOUND in mishap tables")
        continue
    block = m.group(1)
    entries = re.findall(r'^\s+(\d+):\s*\[', block, re.MULTILINE)
    print(f"{career}: mishaps {sorted([int(e) for e in entries])}")
