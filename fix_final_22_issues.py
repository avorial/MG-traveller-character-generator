#!/usr/bin/env python3
"""
Fix the final 22 MEDIUM issues systematically.

Strategy:
1. For Event 10 duel entries: find "on_fail": [ and add forfeit_all_benefits if missing
2. For mishaps needing career_continues: find the closing ] and add it
3. For events needing forbeit_all_benefits: find on_fail and add it

Using careful line-by-line parsing to avoid syntax errors.
"""

from pathlib import Path
import re

filepath = Path("app/engine/lifepath.py")
with open(filepath, encoding='utf-8') as f:
    content = f.read()

changes = []

# ===== FIX 1: Event 10 Duel Events - Add forfeit_all_benefits to on_fail =====
duel_careers = [
    "aslan_military_officer",
    "aslan_space_officer",
    "ge_fleet_officer",
    "ge_warrior_officer",
]

for career in duel_careers:
    # Pattern: find the career's event 10 which has a skill_check with on_fail
    # We need to add forfeit_all_benefits to the on_fail array

    # More specific: look for the duel pattern in event 10
    pattern = rf'("{career}": {{[^}}]*?10:\s*\[\{{"type": "skill_check"[^]]*?"on_fail":\s*\[)([\s\S]*?)(\],\s*"prompt")'

    def add_forfeit_to_duel(match):
        pre = match.group(1)
        on_fail_content = match.group(2)
        post = match.group(3)

        # Check if forfeit_all_benefits is already there
        if 'forfeit_all_benefits' not in on_fail_content:
            # Add it to the beginning of on_fail
            if on_fail_content.strip() == '':
                # Empty on_fail
                return pre + '[{"type": "forfeit_all_benefits"}]' + post
            else:
                # Has existing content
                return pre + '[{"type": "forfeit_all_benefits"}]' + post
        return match.group(0)

    old_content = content
    content = re.sub(pattern, add_forfeit_to_duel, content, flags=re.DOTALL)

    if old_content != content:
        changes.append(f"Added forfeit_all_benefits to {career} event 10")

# ===== FIX 2: Mishap 2 entries - Add forfeit_all_benefits where "lose all" text exists =====
mishap2_careers = [
    ("aslan_outcast", 2),
    ("ge_fleet_officer", 2),
    ("ge_landless_one", 2),
]

for career, mishap_num in mishap2_careers:
    # Find the mishap entry and add forfeit_all_benefits if missing
    pattern = rf'("{career}": {{[^}}]*?{mishap_num}:\s*\[)([\s\S]*?)(\],)'

    def add_forfeit_to_mishap(match):
        pre = match.group(1)
        content_part = match.group(2)
        post = match.group(3)

        if 'forfeit_all_benefits' not in content_part:
            # Add it
            if content_part.strip().startswith('{'):
                # Has other effects, add as additional
                return pre + content_part + ', {"type": "forfeit_all_benefits"}' + post
            else:
                # Empty
                return pre + '{"type": "forfeit_all_benefits"}' + post
        return match.group(0)

    old_content = content
    content = re.sub(pattern, add_forfeit_to_mishap, content, flags=re.DOTALL)

    if old_content != content:
        changes.append(f"Added forfeit_all_benefits to {career} mishap {mishap_num}")

# ===== FIX 3: Believer event 9 - Add forfeit_all_benefits =====
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
    changes.append("Added forfeit_all_benefits to believer event 9")

# ===== FIX 4: Specific mishaps needing career_continues =====
mishap_cc = [
    ("aslan_spacer", 5),
    ("confederation_navy", 2),
    ("ge_fleet", 3),
]

for career, mishap_num in mishap_cc:
    pattern = rf'("{career}": {{[^}}]*?{mishap_num}:\s*\[)([\s\S]*?)(\],)'

    def add_cc_to_mishap(match):
        pre = match.group(1)
        content_part = match.group(2)
        post = match.group(3)

        if 'career_continues' not in content_part:
            # Add it
            if content_part.strip().startswith('{'):
                return pre + content_part + ', {"type": "career_continues"}' + post
            else:
                return pre + '{"type": "career_continues"}' + post
        return match.group(0)

    old_content = content
    content = re.sub(pattern, add_cc_to_mishap, content, flags=re.DOTALL)

    if old_content != content:
        changes.append(f"Added career_continues to {career} mishap {mishap_num}")

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Applied {len(changes)} final fixes:")
for change in changes:
    print(f"  {change}")

if changes:
    print("\nFile updated successfully!")
else:
    print("No changes were applied")
