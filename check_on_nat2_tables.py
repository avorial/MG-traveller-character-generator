"""
Check skill_check entries in event TABLES (line 10000+) that have non-empty on_nat2 effects.
These should be intentional. List them for review.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

table_lines = lines[9999:]
table_content = ''.join(table_lines)

# Find on_nat2 that are NOT empty
non_empty_nat2 = re.findall(
    r'"on_nat2":\s*(\[[^\[\]]+\])',
    table_content
)

print(f"Non-empty on_nat2 entries in event tables: {len(non_empty_nat2)}")
for entry in non_empty_nat2:
    print(f"  {entry[:100]}")
