"""
Check all {"type": "skill", "name": "..."} effects to validate skill names.
"""
import re, json

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

with open('app/data/tables/skills.json', encoding='utf-8') as f:
    skills_data = json.load(f)

core_skills = {s.lower() for s in skills_data.get('core', [])}
speciality_map = {k.lower(): [v.lower() for v in vs] for k, vs in skills_data.get('speciality', {}).items()}

# Known alien/custom skills that are intentional
ALIEN_SKILLS = {
    'appeal', 'caste', 'independence', 'patriarchy', 'tolerance', 'outsider',
    'rep', 'ter', 'resonance', 'psi', 'sport', 'drone', 'technician', 'warrior',
    'artificer', 'dreaming', 'harmony', 'pack', 'ancients tech',
}

# Find all skill effect name values
skill_effects = re.findall(r'\{"type":\s*"skill",\s*"name":\s*"([^"]+)"', content)
print(f"Total skill effects: {len(skill_effects)}")

unknown = []
for name in set(skill_effects):
    nl = name.lower()
    m = re.match(r'^(.+?) \((.+)\)$', name)
    if m:
        base = m.group(1).lower()
        spec = m.group(2).lower()
        if base in speciality_map:
            if spec not in speciality_map[base]:
                unknown.append(f"INVALID SPEC: {name!r} — valid: {speciality_map[base]}")
        elif base not in core_skills and base not in ALIEN_SKILLS:
            unknown.append(f"UNKNOWN BASE+SPEC: {name!r}")
    else:
        if nl not in core_skills and nl not in speciality_map and nl not in ALIEN_SKILLS:
            unknown.append(f"UNKNOWN SKILL: {name!r}")

if unknown:
    print("Issues:")
    for u in unknown:
        safe = u.encode('ascii', errors='replace').decode('ascii')
        print(f"  {safe}")
else:
    print("All skill effects use valid skill names!")
