"""
Find all empty [] event/mishap entries and print them with context.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Find lines with "N: []," or "N: [],  # comment" patterns
empty_pattern = re.compile(r'^\s+(\d+):\s*\[\],?\s*(#.*)?$')
in_effects_section = False
current_career = None
results = []

for i, line in enumerate(lines):
    # Track current career block
    career_match = re.match(r'\s+"([a-z_]+)":\s*\{', line)
    if career_match:
        current_career = career_match.group(1)

    empty_match = empty_pattern.match(line)
    if empty_match:
        event_num = empty_match.group(1)
        comment = empty_match.group(2) or ''
        # Skip if comment says intentional
        if 'intentional' in comment.lower() or 'standard ejection' in comment.lower() or 'ejection only' in comment.lower() or 'gap' in comment.lower() or 'no mechanical' in comment.lower() or 'no effect' in comment.lower():
            continue
        results.append((i+1, current_career, event_num, comment.strip()))

print(f"Empty entries without 'intentional'/'no effect'/'gap' comments: {len(results)}")
for lineno, career, event_num, comment in results:
    print(f"  Line {lineno}: {career} #{event_num}  {comment}")
