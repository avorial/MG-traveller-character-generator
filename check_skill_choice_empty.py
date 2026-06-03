"""
Find skill_choice effects with empty options lists.
These require a prompt to explain what skills are allowed.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

lines = content.split('\n')
issues = []
for i, line in enumerate(lines):
    if '"type": "skill_choice"' in line:
        # Check the surrounding context for options
        chunk = '\n'.join(lines[max(0, i-2):i+8])
        # Look for empty options
        if '"options": []' in chunk or '"options":[]' in chunk:
            has_prompt = '"prompt"' in chunk
            if not has_prompt:
                issues.append((i+1, line.strip()[:100]))

print(f"skill_choice with empty options and no prompt: {len(issues)}")
for lineno, ctx in issues:
    print(f"  Line {lineno}: {ctx}")
