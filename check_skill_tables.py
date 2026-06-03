"""
Check skill_table entries in career JSON files.
Look for entries that don't match known patterns:
  - "Skill"
  - "Skill (Spec)"
  - "STAT +1"
  - Special: "K'kree Life Event", "Any skill", etc.
"""
import json, os, glob, re

career_dir = 'app/data/careers'
files = glob.glob(os.path.join(career_dir, '*.json'))

# All base skill names (core + speciality base)
with open('app/data/tables/skills.json', encoding='utf-8') as f:
    skills_data = json.load(f)

VALID_SKILLS = set(skills_data.get('core', []))
VALID_SKILLS.update(skills_data.get('speciality', {}).keys())

# Add alien-specific skills that aren't in the main table
ALIEN_SKILLS = {
    'Patriarchy', 'Outsider', 'Tolerance', 'Independence',  # K'kree / Aslan
    'Psi', 'Psionic Strength', 'PSI',  # Zhodani
    'Charisma', 'CHA',  # various
    'Rank', 'Caste',  # alien mechanics
    'Life Event', "K'kree Life Event",
    'Jack-of-all-Trades',  # alternate capitalisation
}

VALID_STATS = {'STR', 'DEX', 'END', 'INT', 'EDU', 'SOC', 'PSI', 'RES', 'REP', 'TER'}

SPECIAL_VALUES = {
    "Life Event", "K'kree Life Event", "Any skill",
    "Any combat skill", "Any service skill",
}

issues = []
for fp in sorted(files):
    with open(fp, encoding='utf-8-sig') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue

    cid = data.get('id', os.path.basename(fp).replace('.json', ''))

    for tname, table in (data.get('skill_tables') or {}).items():
        if not isinstance(table, dict):
            continue
        for k, v in table.items():
            if k == 'name':
                continue
            if not isinstance(v, str):
                continue
            entry = v.strip()

            # Skip special values
            if entry in SPECIAL_VALUES:
                continue

            # "STAT +1" or "STAT +2"
            if re.match(r'^(STR|DEX|END|INT|EDU|SOC|PSI|RES|REP|TER|PSI)\s*[+-]\d+$', entry):
                continue

            # "Skill" or "Skill (Spec)"
            m = re.match(r'^([^(]+?)(?:\s*\(([^)]+)\))?\s*$', entry)
            if m:
                skill_name = m.group(1).strip()
                spec_name = m.group(2)
                all_valid = VALID_SKILLS | ALIEN_SKILLS
                if skill_name not in all_valid:
                    issues.append(f"{cid}.{tname}[{k}]: unknown skill '{skill_name}' in '{entry}'")
                continue

            issues.append(f"{cid}.{tname}[{k}]: unrecognised format '{entry}'")

if issues:
    print(f"Skill table issues ({len(issues)}):")
    for issue in issues[:50]:
        print(f"  {issue}")
else:
    print("All skill table entries look valid!")
