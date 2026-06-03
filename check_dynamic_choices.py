"""
Check dynamically-created pending_career_mishap_choice dicts in resolve handlers.
Look for skill_choice and pending_choice types missing 'prompt' key.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

lines = content.split('\n')
issues = []
in_block = False
block_start = 0
brace_depth = 0
block_lines = []

for i, line in enumerate(lines):
    if 'pending_career_mishap_choice = {' in line:
        in_block = True
        block_start = i + 1
        block_lines = [line]
        brace_depth = line.count('{') - line.count('}')
        if brace_depth <= 0:
            # Single-line assignment — already closed
            block_str = line
            ptype = re.search(r'"type":\s*"([^"]+)"', block_str)
            has_prompt = '"prompt"' in block_str
            if ptype and not has_prompt:
                issues.append((block_start, ptype.group(1)))
            in_block = False
            block_lines = []
        continue

    if in_block:
        block_lines.append(line)
        brace_depth += line.count('{') - line.count('}')
        if brace_depth <= 0:
            block_str = '\n'.join(block_lines)
            ptype = re.search(r'"type":\s*"([^"]+)"', block_str)
            has_prompt = '"prompt"' in block_str
            if ptype and not has_prompt:
                issues.append((block_start, ptype.group(1)))
            in_block = False
            block_lines = []

print(f"Dynamic pending_choice assignments missing 'prompt': {len(issues)}")
for lineno, ptype in issues[:40]:
    print(f"  Line {lineno}: type={ptype}")
