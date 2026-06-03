"""
Check all pending_choice entries for missing prompt keys.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

lines = content.split('\n')
issues = []
for i, line in enumerate(lines):
    if '"type": "pending_choice"' in line or '"type":"pending_choice"' in line:
        # Gather context: look 15 lines forward for "prompt" and "id"
        chunk = '\n'.join(lines[i:i+15])
        has_prompt = '"prompt"' in chunk
        id_m = re.search(r'"id":\s*"([^"]+)"', chunk)
        cid = id_m.group(1) if id_m else '?'
        if not has_prompt:
            issues.append((i + 1, cid))

print(f"pending_choice without nearby prompt: {len(issues)}")
for lineno, cid in issues[:40]:
    print(f"  Line {lineno}: {cid}")
