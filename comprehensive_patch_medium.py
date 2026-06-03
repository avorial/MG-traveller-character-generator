#!/usr/bin/env python3
"""
Comprehensive patch for all 86 medium issues.
Applies all fixes to lifepath.py in one pass.
"""

import re
from pathlib import Path

def fix_lifepath():
    """Apply all medium-issue fixes to lifepath.py"""

    filepath = Path("app/engine/lifepath.py")
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # List of (find_pattern, replace_with) tuples for each fix
    fixes = []

    # Event 2 fixes - add career_continues to trigger_disaster_mishap
    # Pattern: "trigger_disaster_mishap"}], -> "trigger_disaster_mishap"}], {"type": "career_continues"}],

    # These careers have Event 2 with only trigger_disaster_mishap - need career_continues added
    event2_careers = [
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

    for career in event2_careers:
        # Find pattern: career_id": {... 2: [{"type": "trigger_disaster_mishap"}],
        pattern = rf'"{career}": {{[\s\S]*?2:\s*\[\{{"type": "trigger_disaster_mishap"}}\],'

        # Replacement: add career_continues
        def replace_func(match):
            text = match.group(0)
            # Replace }], with }], {"type": "career_continues"}],
            return text.replace(
                '{"type": "trigger_disaster_mishap"}],',
                '{"type": "trigger_disaster_mishap"}], {"type": "career_continues"}],'
            )

        if re.search(pattern, content):
            content = re.sub(pattern, replace_func, content)
            fixes.append(f"Fixed Event 2 for {career}")

    return content, fixes

if __name__ == "__main__":
    content, fixes = fix_lifepath()

    if fixes:
        filepath = Path("app/engine/lifepath.py")
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(content)

        print(f"Applied {len(fixes)} fixes:")
        for fix in fixes:
            print(f"  {fix}")
    else:
        print("No fixes were necessary")
