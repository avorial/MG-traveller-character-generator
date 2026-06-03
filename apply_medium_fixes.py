#!/usr/bin/env python3
"""
Apply all 86 medium-issue fixes to lifepath.py systematically.
This uses targeted string replacements for each fix.
"""

import re
from pathlib import Path

filepath = Path("app/engine/lifepath.py")
with open(filepath, encoding='utf-8') as f:
    content = f.read()

changes = []

# List of Event 2 fixes - add career_continues where trigger_disaster_mishap exists
event2_fixes = [
    "agent", "army", "aslan_ceremonial", "aslan_envoy", "aslan_management",
    "aslan_military", "aslan_outcast", "aslan_scientist", "aslan_spacer",
    "aslan_wanderer", "citizen", "confederation_army", "confederation_navy",
    "dolphin_civilian", "dolphin_military", "entertainer", "ge_fleet",
    "ge_landless_one", "ge_slave", "ge_warrior", "girug_kagh_translator",
    "hiver_academic", "hiver_generalist", "hiver_manipulator", "hiver_merchant",
    "kkree_merchant", "kkree_noble", "kkree_pastoral", "kkree_servant",
    "marine", "merchant", "navy", "noble", "party", "philosopher_elder",
    "prisoner", "psion", "scholar", "scout", "solomani_marine", "solsec",
    "spirit_singer", "storm_knight_inconstant_star", "storm_knight_shadows",
    "storm_knight_thunder", "truther", "vargr_army", "vargr_citizen",
    "vargr_corsair", "vargr_emissary", "vargr_law_enforcement", "vargr_loner",
    "vargr_marines", "vargr_merchant", "vargr_navy", "vargr_psion",
    "vargr_scientist", "zhodani_agent", "zhodani_army", "zhodani_entertainer",
    "zhodani_government", "zhodani_guard", "zhodani_merchant", "zhodani_navy",
    "zhodani_scholar",
]

# Fix Event 2 entries - use a more targeted approach
for career in event2_fixes:
    # Find and replace pattern for this specific career's event 2
    # Pattern: "CAREER": { ... 2: [{"type": "trigger_disaster_mishap"}],
    pattern = rf'("{career}": {{[^}}]*?2:\s*\[{{"type": "trigger_disaster_mishap"}}\],)'

    def make_replacer(match):
        text = match.group(1)
        if ', {"type": "career_continues"}]' not in text:
            # Replace }], with }], {"type": "career_continues"}],
            return text.replace(
                '{"type": "trigger_disaster_mishap"}],',
                '{"type": "trigger_disaster_mishap"}], {"type": "career_continues"}],'
            )
        return text

    old_content = content
    content = re.sub(pattern, make_replacer, content, flags=re.DOTALL)

    if old_content != content:
        changes.append(f"Fixed Event 2 career_continues for {career}")

# Fix Event 10 duel entries that need forfeit_all_benefits
duel_fixes = [
    ("aslan_military_officer", 10),
    ("aslan_space_officer", 10),
    ("ge_fleet_officer", 10),
    ("ge_warrior_officer", 10),
]

for career, event_num in duel_fixes:
    # Add forfeit_all_benefits to on_fail of event 10
    # This is tricky - need to find the event 10 entry and add to on_fail
    pattern = rf'("{career}": {{[^}}]*?{event_num}:\s*\[{{"type": "skill_check"[^]]*?"on_fail":\s*\[)([\s\S]*?)(\],\s*"prompt")'

    def make_replacer(match):
        pre = match.group(1)
        content_part = match.group(2)
        post = match.group(3)

        # Check if forfeit_all_benefits is already there
        if 'forfeit_all_benefits' not in content_part:
            # Add it
            if content_part.strip() == '':
                # Empty on_fail list
                return pre + '[{"type": "forfeit_all_benefits"}]' + post
            else:
                # Has other content
                return pre + content_part + ', {"type": "forfeit_all_benefits"}' + post
        return match.group(0)

    old_content = content
    content = re.sub(pattern, make_replacer, content, flags=re.DOTALL)

    if old_content != content:
        changes.append(f"Fixed Event {event_num} forfeit_all_benefits for {career}")

# Fix Believer event 9 - add forfeit_all_benefits
# Pattern: believer event 9 needs forfeit_all_benefits in on_fail of skill_check
pattern = r'("believer": {[^}]*?9:\s*\[{"type": "skill_check"[^]]*?"on_fail":\s*\[)([\s\S]*?)(\])'
def fix_believer_e9(match):
    pre = match.group(1)
    content_part = match.group(2)
    post = match.group(3)

    if 'forfeit_all_benefits' not in content_part:
        return pre + '[{"type": "forfeit_all_benefits"}]' + post
    return match.group(0)

old_content = content
content = re.sub(pattern, fix_believer_e9, content, flags=re.DOTALL)
if old_content != content:
    changes.append("Fixed Believer event 9 forfeit_all_benefits")

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Applied {len(changes)} fixes:")
for change in changes:
    print(f"  {change}")

if not changes:
    print("No fixes were applied. The file may already be fixed or the patterns did not match.")
else:
    print("\nFile updated successfully!")
