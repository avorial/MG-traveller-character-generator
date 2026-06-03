"""
Check rank bonus skill names in career JSON files.
Rank bonuses are strings like "Admin 1" or "Pilot (Spacecraft) 1" or "SOC +1" or "STR +1".
"""
import json, os, glob, re

career_dir = 'app/data/careers'
files = glob.glob(os.path.join(career_dir, '*.json'))

# Load skills.json for valid skill names
with open('app/data/tables/skills.json', encoding='utf-8') as f:
    skills_data = json.load(f)

VALID_CORE_SKILLS = set(skills_data.get('core', []))
VALID_SPECS = {}
for skill, specs in skills_data.get('speciality', {}).items():
    VALID_SPECS[skill] = set(s.lower() for s in specs)

VALID_STATS = {'STR', 'DEX', 'END', 'INT', 'EDU', 'SOC', 'PSI', 'RES', 'REP', 'TER'}

issues = []
for fp in sorted(files):
    with open(fp, encoding='utf-8-sig') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue

    cid = data.get('id', os.path.basename(fp).replace('.json', ''))

    for assign_id, assign_ranks in (data.get('ranks') or {}).items():
        for rank_num, rank_data in assign_ranks.items():
            bonus = rank_data.get('bonus')
            if not bonus:
                continue

            # Parse bonus: "Skill N" or "Skill (Spec) N" or "STAT +N"
            # Could be "Admin 1" or "Pilot (Spacecraft) 1" or "SOC +1"
            stat_m = re.match(r'^([A-Z]{2,4})\s*[+-]?\d+$', bonus)
            if stat_m:
                stat = stat_m.group(1)
                if stat not in VALID_STATS:
                    issues.append(f"{cid} rank {assign_id}/{rank_num}: invalid stat in bonus '{bonus}'")
                continue

            skill_m = re.match(r'^(.+?)(?:\s*\((.+?)\))?\s+(\d+)$', bonus)
            if skill_m:
                skill_name = skill_m.group(1).strip()
                spec_name = skill_m.group(2)
                # Check if skill is valid
                if skill_name not in VALID_CORE_SKILLS:
                    # Check non-core skills (Patriarchy, etc.)
                    non_core = {'Patriarchy', 'Outsider', 'Jack-of-all-Trades', 'Jack-of-All-Trades',
                                'Language', 'Seafarer', 'Flyer', 'Drive', 'Gun Combat'}
                    if skill_name not in non_core:
                        issues.append(f"{cid} rank {assign_id}/{rank_num}: unrecognised skill '{skill_name}' in bonus '{bonus}'")
                # Check speciality if present
                if spec_name and skill_name in VALID_SPECS:
                    if spec_name.lower() not in VALID_SPECS[skill_name]:
                        issues.append(f"{cid} rank {assign_id}/{rank_num}: unknown spec '{spec_name}' for {skill_name} in bonus '{bonus}'")
            else:
                issues.append(f"{cid} rank {assign_id}/{rank_num}: can't parse bonus '{bonus}'")

if issues:
    print(f"Rank bonus issues ({len(issues)}):")
    for issue in issues[:50]:
        print(f"  {issue}")
else:
    print("All rank bonuses look valid!")
