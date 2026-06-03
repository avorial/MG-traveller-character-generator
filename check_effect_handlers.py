"""
For each "UNKNOWN" effect type, check if it's handled in _apply_mishap_effect
or elsewhere in lifepath.py.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

UNKNOWN_TYPES = [
    'rank_adjustment', 'stat_choice', 'd_associates', 'zhodani_re_education',
    'stat_cap', 'rank_loss', 'zhodani_soc_conditional', 'psi_adjust',
    'd_extra_benefit', 'dm_qualification', 'kkree_wife_loss', 'equipment',
    'd_stat', 'kkree_degree_reset', 'monitor_mishap', 'monitor_event',
    'home_forces_mishap', 'debt', 'frozen_watch',
    'forfeit_benefit_unless_solsec_agent', 'forfeit_all_benefits_except_one',
    'injury_twice_higher', 'choose_physical',
    'career_continues', 'force_next_career', 'force_career_end',
    'auto_qualify_careers', 'contacts_soc_dm_min1', 'dm_qualification_terms_in_career',
    'skill_loss_choice', 'psi_check', 'psi_training',
]

for t in UNKNOWN_TYPES:
    occurrences = content.count(f'"{t}"')
    # Check if there's handling code
    has_handler = bool(re.search(rf"eff\[.type.\]\s*==\s*['\"]({re.escape(t)})['\"]|"
                                  rf'effect_type\s*==\s*["\']({re.escape(t)})["\']|'
                                  rf'"\s*{re.escape(t)}\s*"', content))
    handled = bool(re.search(
        rf'''(["']){re.escape(t)}\1''',
        content
    ))
    # Look for it in _apply_mishap_effect or similar
    in_apply = content.find(f'"{t}"') != -1
    # Find first context
    idx = content.find(f'"{t}"')
    ctx_line = content[:idx].count('\n') + 1 if idx != -1 else 0
    print(f"  {t}: appears={occurrences} times, first at line ~{ctx_line}")
