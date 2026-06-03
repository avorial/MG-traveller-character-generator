"""
Check that all skill names used in skill_check effects are valid.
Valid: skill names from skills.json, stat names, or known alien skills.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all skill_check skill entries
# Pattern: {"name": "X", ...} inside a skill_check effect
skill_names_used = set()
for m in re.finditer(r'"type":\s*"skill_check".*?"skills":\s*\[([^\]]*)\]', content, re.DOTALL):
    skills_block = m.group(1)
    for nm in re.finditer(r'"name":\s*"([^"]+)"', skills_block):
        skill_names_used.add(nm.group(1))

print(f"Skill names used in skill_check effects: {sorted(skill_names_used)}")

# Valid skill base names
import json
with open('app/data/tables/skills.json', encoding='utf-8') as f:
    skills_data = json.load(f)
VALID = set(skills_data.get('core', []))
VALID.update(skills_data.get('speciality', {}).keys())
STATS = {'STR', 'DEX', 'END', 'INT', 'EDU', 'SOC', 'PSI', 'RES', 'REP', 'TER'}
ALIEN = {'Patriarchy', 'Outsider', 'Tolerance', 'Independence', 'Psi', 'Carouse'}

all_valid = VALID | STATS | ALIEN

unknown = {s for s in skill_names_used if s not in all_valid}
if unknown:
    print(f"\nUnknown skill names in skill_check effects: {sorted(unknown)}")
else:
    print("\nAll skill names in skill_check effects are valid!")
