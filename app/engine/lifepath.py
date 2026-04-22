"""
The lifepath engine.

Each function takes a Character and an action, applies Traveller's rules,
returns the updated Character plus a structured log of what happened so the
UI can narrate it.
"""

import random
import re
from typing import Optional

from . import dice, rules
from .character import (
    Character,
    CareerTerm,
    CareerRecord,
    Associate,
    Equipment,
)


# ============================================================
# Event DM parser
# ============================================================

# Match "DM+N" or "DM -N" or "+N DM" followed by a short filler
# (up to 4 words) and one of the three target categories Traveller
# actually tracks between phases.
_DM_RE = re.compile(
    r"(?:DM\s*([+-]?\d+)|([+-]\d+)\s*DM)\s+"
    r"(?:to|on)\s+"
    r"(?:\w+\s+){0,4}?"
    r"(qualification|advancement|benefit)",
    re.IGNORECASE,
)

# If any of these phrases appear, the event grant is either conditional
# on an in-fiction check or offers the player a choice — auto-applying
# the DM could strip away a decision, so we just report the grant and
# let the player resolve it manually.
_CONDITIONAL_MARKERS = (
    "on success",
    "on failure",
    "if you succeed",
    "if you fail",
    "either ",
    " or dm",
    "; on ",
    "roll ",
)


def _parse_event_dms(event_text: str) -> list[dict]:
    """Find every 'DM+N to [qualification|advancement|benefit]' grant in an event.

    Returns a list of dicts: [{"target": "advancement", "dm": 2}, ...].
    Only clean grants are returned (no matches found inside conditional
    phrases like 'on success, gain DM+2…').
    """
    text = event_text or ""
    found: list[dict] = []
    for m in _DM_RE.finditer(text):
        amount_raw = m.group(1) if m.group(1) is not None else m.group(2)
        try:
            amount = int(amount_raw)
        except (TypeError, ValueError):
            continue
        target = m.group(3).lower()
        found.append({"target": target, "dm": amount, "span": m.span()})
    return found


def _apply_event_dms(character: Character, event_text: str) -> list[dict]:
    """Apply any clean (unconditional, non-choice) DM grants found in an event.

    Returns the list of applied grants so the UI/log can narrate them.
    """
    grants = _parse_event_dms(event_text)
    if not grants:
        return []

    lowered = event_text.lower()
    if any(marker in lowered for marker in _CONDITIONAL_MARKERS):
        # Conditional/choice event — skip auto-apply. We still return the
        # parsed grants so the UI can surface them as hints.
        return [{"target": g["target"], "dm": g["dm"], "applied": False,
                 "reason": "conditional_or_choice"} for g in grants]

    applied: list[dict] = []
    for g in grants:
        tgt, dm = g["target"], g["dm"]
        if tgt == "qualification":
            character.dm_next_qualification += dm
        elif tgt == "advancement":
            character.dm_next_advancement += dm
        elif tgt == "benefit":
            character.dm_next_benefit += dm
        else:
            continue
        applied.append({"target": tgt, "dm": dm, "applied": True})
    return applied


# ============================================================
# Phase 1: Characteristics + Species
# ============================================================


def roll_initial_characteristics(character: Character) -> dict:
    """Roll 2D for each of the six characteristics. Does NOT apply species mods."""
    rolls = {}
    for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
        r = dice.roll("2D")
        character.characteristics.set(stat, r.total)
        rolls[stat] = r.to_dict()
    character.log(
        "Rolled characteristics: "
        + ", ".join(f"{k} {character.characteristics.get(k)}" for k in rolls)
    )
    return {"rolls": rolls, "character": character.model_dump()}


def apply_species(character: Character, species_id: str) -> dict:
    """Apply species modifiers and record traits."""
    species_data = rules.species().get(species_id)
    if species_data is None:
        raise ValueError(f"Unknown species: {species_id}")

    character.species_id = species_id
    mods = species_data.get("characteristic_modifiers", {})
    applied = {}
    for stat, delta in mods.items():
        if delta == 0:
            continue
        current = character.characteristics.get(stat)
        new_val = max(1, current + delta)  # Aliens can exceed 15 but never below 1
        character.characteristics.set(stat, new_val)
        applied[stat] = {"from": current, "to": new_val, "delta": delta}

    character.traits = species_data.get("traits", [])
    if applied:
        mods_str = ", ".join(f"{k} {v['delta']:+d}" for k, v in applied.items())
        character.log(f"Applied species: {species_data['name']} ({mods_str})")
    else:
        character.log(f"Applied species: {species_data['name']}")
    return {"applied": applied, "traits": character.traits, "character": character.model_dump()}


def set_background_skills(character: Character, chosen: list[str]) -> dict:
    """Grant the selected background skills at level 0."""
    edu_dm = dice.characteristic_dm(character.characteristics.EDU)
    allowed_count = max(0, edu_dm + 3)
    if len(chosen) > allowed_count:
        raise ValueError(f"Too many background skills chosen: {len(chosen)} (allowed {allowed_count})")

    valid = set(rules.background_skills()["skills"])
    for skill_name in chosen:
        if skill_name not in valid:
            raise ValueError(f"Not a background skill: {skill_name}")
        character.add_skill(skill_name, level=0)

    character.log(f"Gained {len(chosen)} background skill(s): {', '.join(chosen) or '(none)'}")
    character.phase = "career"
    return {"allowed": allowed_count, "chosen": chosen, "character": character.model_dump()}


# ============================================================
# Phase 2: Career loop
# ============================================================


def qualify_for_career(character: Character, career_id: str) -> dict:
    """Roll qualification for entering a career."""
    career = rules.careers().get(career_id)
    if career is None:
        raise ValueError(f"Unknown career: {career_id}")

    qual = career.get("qualification", {})
    if qual.get("automatic"):
        character.log(f"Automatic qualification for {career['name']}.")
        return {"automatic": True, "succeeded": True, "character": character.model_dump()}

    auto_qualify = qual.get("auto_qualify_if")
    if auto_qualify:
        # e.g. {"SOC": ">=10"} for Noble
        for stat, cond in auto_qualify.items():
            if cond.startswith(">="):
                threshold = int(cond[2:])
                if character.characteristics.get(stat) >= threshold:
                    character.log(f"Auto-qualified for {career['name']} (SOC ≥ {threshold}).")
                    return {"automatic": True, "succeeded": True, "character": character.model_dump()}

    char_key = qual["characteristic"]
    target = qual["target"]

    # Special case: DEX_OR_INT (Entertainer)
    if char_key == "DEX_OR_INT":
        dm = max(
            dice.characteristic_dm(character.characteristics.DEX),
            dice.characteristic_dm(character.characteristics.INT),
        )
        char_display = "DEX or INT (higher)"
    else:
        dm = dice.characteristic_dm(character.characteristics.get(char_key))
        char_display = char_key

    # Apply modifiers
    for mod in qual.get("modifiers", []):
        if mod["type"] == "per_previous_career":
            dm += mod["dm"] * len(character.completed_careers)
        elif mod["type"] == "age" and character.age >= mod["threshold"]:
            dm += mod["dm"]

    # Apply DM from prior events (e.g. Travel life event)
    dm += character.dm_next_qualification
    pending = character.dm_next_qualification
    character.dm_next_qualification = 0

    r = dice.roll("2D", modifier=dm, target=target)
    result = r.to_dict()
    result["characteristic_used"] = char_display
    result["pending_dm_consumed"] = pending
    character.log(
        f"Qualification for {career['name']}: 2D{dm:+d} vs {target}+ "
        f"= {r.total} ({'pass' if r.succeeded else 'fail'})"
    )
    return {"succeeded": r.succeeded, "roll": result, "character": character.model_dump()}


def start_term(character: Character, career_id: str, assignment_id: str) -> dict:
    """Begin a new career term in the given career + assignment."""
    career = rules.careers().get(career_id)
    if career is None:
        raise ValueError(f"Unknown career: {career_id}")
    if assignment_id not in career["assignments"]:
        raise ValueError(f"Unknown assignment '{assignment_id}' for {career['name']}")

    # Figure out if this is basic training (first term in this career, ever)
    is_new_career = (
        character.current_term is None
        or character.current_term.career_id != career_id
    )
    first_term_in_this_career = is_new_career and not any(
        c.career_id == career_id for c in character.completed_careers
    )

    term = CareerTerm(
        career_id=career_id,
        assignment_id=assignment_id,
        term_number=1 if is_new_career else (character.current_term.term_number + 1),
        overall_term_number=character.total_terms + 1,
        rank=0,
        rank_title=_rank_title(career, assignment_id, 0),
        basic_training=first_term_in_this_career,
    )
    character.current_term = term
    character.log(
        f"Begin Term {term.overall_term_number}: {career['name']} — "
        f"{career['assignments'][assignment_id]['name']}"
        + (" (Basic Training)" if term.basic_training else "")
    )
    return {"term": term.model_dump(), "character": character.model_dump()}


def survival_roll(character: Character) -> dict:
    """Roll survival for the current term's assignment."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")
    career = rules.careers()[term.career_id]
    assignment = career["assignments"][term.assignment_id]
    survival = assignment["survival"]

    char_key = survival["characteristic"]
    target = survival["target"]
    dm = dice.characteristic_dm(character.characteristics.get(char_key))
    r = dice.roll("2D", modifier=dm, target=target)
    term.survived = bool(r.succeeded)

    msg = (
        f"Survival ({char_key} {target}+): 2D{dm:+d} = {r.total} "
        f"[{'SURVIVED' if r.succeeded else 'MISHAP'}]"
    )
    character.log(msg)
    return {"roll": r.to_dict(), "survived": r.succeeded, "character": character.model_dump()}


def event_roll(character: Character) -> dict:
    """Roll on the career's event table (2D, 2-12)."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")
    career = rules.careers()[term.career_id]
    events = career.get("events", {})
    r = dice.roll("2D")
    key = str(r.total)
    event_text = events.get(key, "(No event encoded for this roll — see rulebook or the career JSON file.)")

    # Life Event sub-table handling
    if event_text.lower().startswith("life event"):
        life_r = dice.roll("2D")
        life_data = rules.life_events()["entries"].get(str(life_r.total))
        if life_data:
            event_text = f"Life Event — {life_data['title']}: {life_data['text']}"
            if life_data.get("sub_table"):
                sub_r = dice.roll("1D")
                sub_text = life_data["sub_table"].get(str(sub_r.total))
                event_text += f" [{sub_r.dice[0]}] {sub_text}"

    term.events.append(event_text)
    character.log(f"Event [2D={r.total}]: {event_text}")

    # Auto-apply any unconditional "DM+N to your next X" grants in the
    # event text so the player doesn't have to remember them between phases.
    dm_grants = _apply_event_dms(character, event_text)
    for g in dm_grants:
        if g.get("applied"):
            tgt = g["target"].capitalize()
            sign = "+" if g["dm"] >= 0 else ""
            character.log(f"  → Auto-applied DM{sign}{g['dm']} to next {tgt} roll.")

    return {
        "roll": r.to_dict(),
        "event": event_text,
        "dm_grants": dm_grants,
        "character": character.model_dump(),
    }


def mishap_roll(character: Character) -> dict:
    """Roll on the career's mishap table (1D) after a failed survival."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")
    career = rules.careers()[term.career_id]
    mishaps = career.get("mishaps", {})
    r = dice.roll("1D")
    mishap_text = mishaps.get(str(r.total), "(No mishap encoded — see rulebook or career JSON.)")

    term.mishap = mishap_text
    character.log(f"Mishap [1D={r.total}]: {mishap_text}")
    return {"roll": r.to_dict(), "mishap": mishap_text, "character": character.model_dump()}


def advancement_roll(character: Character) -> dict:
    """Roll advancement. On success, rank increases."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")
    career = rules.careers()[term.career_id]
    assignment = career["assignments"][term.assignment_id]
    adv = assignment["advancement"]

    char_key = adv["characteristic"]
    target = adv["target"]
    dm = dice.characteristic_dm(character.characteristics.get(char_key))

    dm += character.dm_next_advancement
    pending = character.dm_next_advancement
    character.dm_next_advancement = 0

    r = dice.roll("2D", modifier=dm, target=target)
    term.advanced = bool(r.succeeded)

    if r.succeeded:
        term.rank += 1
        term.rank_title = _rank_title(career, term.assignment_id, term.rank)
        rank_data = _rank_data(career, term.assignment_id, term.rank)
        if rank_data and rank_data.get("bonus"):
            bonus = rank_data["bonus"]
            term.skills_gained.append(f"Rank bonus: {bonus}")

    msg = (
        f"Advancement ({char_key} {target}+{'+' + str(pending) if pending else ''}): "
        f"2D{dm:+d} = {r.total} "
        f"[{'PROMOTED to rank ' + str(term.rank) + (' — ' + term.rank_title if term.rank_title else '') if r.succeeded else 'no promotion'}]"
    )
    character.log(msg)
    return {"roll": r.to_dict(), "advanced": r.succeeded, "new_rank": term.rank,
            "new_rank_title": term.rank_title, "character": character.model_dump()}


def roll_on_skill_table(character: Character, table_key: str) -> dict:
    """Roll 1D on one of the career's skill tables and gain the result."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")
    career = rules.careers()[term.career_id]
    skill_tables = career.get("skill_tables", {})
    table = skill_tables.get(table_key)
    if table is None:
        raise ValueError(f"Unknown skill table: {table_key}")

    # Gate: advanced education requires EDU threshold
    if table.get("requires_edu") and character.characteristics.EDU < table["requires_edu"]:
        raise ValueError(f"Advanced Education requires EDU {table['requires_edu']}+")
    # Gate: officer table requires commission
    if table.get("requires_commission") and not term.commissioned:
        raise ValueError("Officer table requires a commission")
    # Gate: assignment-specific tables
    if table.get("assignment_only") and table["assignment_only"] != term.assignment_id:
        raise ValueError(f"That skill table is for the {table['assignment_only']} assignment only")

    r = dice.roll("1D")
    result = table.get(str(r.total), "(Unknown)")

    # The result is either a skill name, a characteristic bonus ("DEX +1"), or similar.
    applied = _apply_skill_result(character, result)
    term.skills_gained.append(f"{table.get('name', table_key)}: {result}")
    character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: {result} — {applied}")
    return {"roll": r.to_dict(), "result": result, "applied": applied,
            "character": character.model_dump()}


def end_term(character: Character, leaving: bool = False, reason: str = "voluntary") -> dict:
    """Close out the current term — apply aging if needed, commit the term record."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")

    character.age += 4
    character.total_terms += 1
    character.term_history.append(term)

    aging_log = None
    if character.total_terms >= 4:
        aging_log = _apply_aging(character)

    if leaving:
        # Record career completion
        # Find previous terms in this career to count
        terms_in_career = sum(
            1 for h in character.term_history if h.career_id == term.career_id
        )
        character.completed_careers.append(
            CareerRecord(
                career_id=term.career_id,
                assignment_id=term.assignment_id,
                terms_served=terms_in_career,
                final_rank=term.rank,
                final_rank_title=term.rank_title,
                commissioned=term.commissioned,
                left_due_to=reason,
            )
        )
        # Benefit rolls = 1 per full term + rank bonus
        rank_bonus = _benefit_rolls_from_rank(term.rank)
        earned = terms_in_career + rank_bonus
        character.pending_benefit_rolls += earned
        character.current_term = None
        character.log(
            f"Left {rules.careers()[term.career_id]['name']} "
            f"({reason}). {terms_in_career} terms served. "
            f"Earns {earned} benefit rolls ({terms_in_career} base + {rank_bonus} rank bonus)."
        )
    else:
        character.log(f"Completed term {term.overall_term_number}, age now {character.age}.")

    return {
        "aging": aging_log,
        "age": character.age,
        "total_terms": character.total_terms,
        "pending_benefit_rolls": character.pending_benefit_rolls,
        "character": character.model_dump(),
    }


# ============================================================
# Phase 3: Aging
# ============================================================


def _apply_aging(character: Character) -> dict:
    """Roll on the aging table: 2D - total terms."""
    dm = -character.total_terms  # "the older you are, the heavier the effects"
    r = dice.roll("2D", modifier=dm)
    aging_data = rules.aging_table()["entries"]

    # Find matching entry
    entry = None
    key = r.total
    if key <= -6:
        entry = aging_data.get("-6_or_less")
    elif key >= 1:
        entry = aging_data.get("1_or_more")
    else:
        entry = aging_data.get(str(key))

    if entry is None:
        character.log(f"Aging roll {r.total}: no matching entry")
        return {"roll": r.to_dict(), "effects_applied": []}

    effects_applied = []
    for effect in entry.get("effects", []):
        applied = _apply_aging_effect(character, effect)
        effects_applied.extend(applied)

    # Check for aging crisis (any stat at 0)
    crisis = [s for s in ("STR", "DEX", "END", "INT", "EDU", "SOC")
              if character.characteristics.get(s) <= 0]
    if crisis:
        character.log(
            f"AGING CRISIS: {', '.join(crisis)} reduced to 0. "
            "Character dies unless 1D × Cr10,000 is paid for medical care."
        )
        # For the creator we'll mark but not auto-kill — let the player decide
        character.dead = True
        character.death_reason = f"Aging crisis ({', '.join(crisis)} = 0)"

    character.log(
        f"Aging [2D{dm:+d}={r.total}] {entry['title']}: "
        + (", ".join(effects_applied) if effects_applied else "no effect")
    )
    return {"roll": r.to_dict(), "title": entry["title"], "effects_applied": effects_applied}


def _apply_aging_effect(character: Character, effect: dict) -> list[str]:
    """Apply a single aging effect. Returns log strings."""
    physical = ["STR", "DEX", "END"]
    mental = ["INT", "EDU", "SOC"]
    logs = []

    if effect["type"] == "reduce_physical":
        # Pick characteristics at random — player choice in rulebook but simpler to auto
        count = effect["count"]
        amount = effect["amount"]
        targets = random.sample(physical, min(count, len(physical)))
        for stat in targets:
            old = character.characteristics.get(stat)
            character.characteristics.set(stat, old - amount)
            logs.append(f"{stat} {old}→{character.characteristics.get(stat)}")
    elif effect["type"] == "reduce_mental":
        count = effect["count"]
        amount = effect["amount"]
        targets = random.sample(mental, min(count, len(mental)))
        for stat in targets:
            old = character.characteristics.get(stat)
            character.characteristics.set(stat, old - amount)
            logs.append(f"{stat} {old}→{character.characteristics.get(stat)}")
    return logs


# ============================================================
# Phase 4: Mustering Out
# ============================================================


def muster_out_roll(character: Character, career_id: str, column: str) -> dict:
    """Roll on the mustering-out table (1D), applying the chosen column: cash or benefits."""
    if character.pending_benefit_rolls <= 0:
        raise ValueError("No benefit rolls remaining")
    if column not in ("cash", "benefit"):
        raise ValueError("Column must be 'cash' or 'benefit'")
    if column == "cash" and character.cash_rolls_used >= 3:
        raise ValueError("Cash column maxed out (3 rolls total across all careers)")

    career = rules.careers().get(career_id)
    if career is None:
        raise ValueError(f"Unknown career: {career_id}")
    table = career.get("mustering_out", {})
    if not table:
        raise ValueError(f"{career['name']} has no mustering-out table encoded yet")

    # Gambler bonus on cash rolls
    dm = 0
    if column == "cash":
        if any(s.name.lower() == "gambler" for s in character.skills):
            dm += 1
    dm += character.dm_next_benefit
    pending_dm = character.dm_next_benefit
    character.dm_next_benefit = 0

    r = dice.roll("1D", modifier=dm)
    # 1D result capped to 1-6 for table lookup
    key = str(max(1, min(6, r.total)))
    row = table.get(key)
    if row is None:
        raise ValueError(f"No row for result {key}")

    if column == "cash":
        cash = row["cash"]
        character.credits += cash
        character.cash_rolls_used += 1
        result_text = f"Cr{cash:,}"
        character.log(f"Muster out (cash)[{r.total}]: gained Cr{cash:,}")
    else:
        benefit = row["benefit"]
        _apply_benefit(character, benefit)
        result_text = benefit
        character.log(f"Muster out (benefit)[{r.total}]: {benefit}")

    character.pending_benefit_rolls -= 1
    return {"roll": r.to_dict(), "result": result_text,
            "remaining_rolls": character.pending_benefit_rolls,
            "character": character.model_dump()}


def _apply_benefit(character: Character, benefit: str) -> None:
    """Apply a mustering-out benefit to the character."""
    b = benefit.strip()

    # Characteristic bonuses
    for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
        if b == f"{stat} +1":
            species_data = rules.species().get(character.species_id, {})
            max_stat = species_data.get("characteristic_maximum", 15)
            current = character.characteristics.get(stat)
            if current < max_stat:
                character.characteristics.set(stat, current + 1)
            else:
                if stat == "SOC":
                    character.ship_shares += 1
            return

    # Ship shares
    if b == "Ship Share":
        character.ship_shares += 1
        return
    if b == "Two Ship Shares":
        character.ship_shares += 2
        return
    if b == "1D Ship Shares":
        character.ship_shares += dice.roll("1D").total
        return
    if b == "2D Ship Shares":
        character.ship_shares += dice.roll("2D").total
        return

    # Multi-part "SOC +1 and Yacht"
    if " and " in b:
        for part in b.split(" and "):
            _apply_benefit(character, part)
        return
    if " or " in b:
        # Ambiguous — add as equipment/note with options
        character.equipment.append(
            Equipment(name=b, notes="Player choice: pick one")
        )
        return

    # Everything else → equipment/reference
    character.equipment.append(Equipment(name=b, notes="From mustering out"))


# ============================================================
# Helpers
# ============================================================


def _rank_title(career: dict, assignment_id: str, rank: int) -> Optional[str]:
    """Look up rank title for a career+assignment."""
    ranks_data = career.get("ranks", {})
    # Careers use various key structures:
    #  - by assignment ("law_enforcement", "intelligence"...)
    #  - single "default" (Scout)
    #  - "enlisted" + "officer" (Army/Navy/Marines)
    rank_table = (
        ranks_data.get(assignment_id)
        or ranks_data.get("default")
        or ranks_data.get("enlisted")
    )
    if rank_table is None:
        return None
    entry = rank_table.get(str(rank))
    return entry.get("title") if entry else None


def _rank_data(career: dict, assignment_id: str, rank: int) -> Optional[dict]:
    ranks_data = career.get("ranks", {})
    rank_table = (
        ranks_data.get(assignment_id)
        or ranks_data.get("default")
        or ranks_data.get("enlisted")
    )
    if rank_table is None:
        return None
    return rank_table.get(str(rank))


def _benefit_rolls_from_rank(rank: int) -> int:
    if rank >= 5:
        return 3
    if rank >= 3:
        return 2
    if rank >= 1:
        return 1
    return 0


def _apply_skill_result(character: Character, result: str) -> str:
    """Parse a skill-table result string and apply it. Returns a log summary."""
    if not result:
        return "no result"
    stripped = result.strip()

    # Characteristic bonuses ("STR +1", "DEX +1", etc.)
    for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
        if stripped == f"{stat} +1":
            species_data = rules.species().get(character.species_id, {})
            max_stat = species_data.get("characteristic_maximum", 15)
            current = character.characteristics.get(stat)
            if current < max_stat:
                character.characteristics.set(stat, current + 1)
                return f"{stat} {current}→{current + 1}"
            return f"{stat} already at max ({max_stat})"

    # "X or Y" — just record both options; first one is granted for simplicity
    if " or " in stripped:
        first = stripped.split(" or ")[0]
        character.add_skill(first)
        return f"Gained {first} (from choice: {stripped})"

    # Skill with speciality: "Melee (blade)", "Pilot (small craft)"
    if "(" in stripped and ")" in stripped:
        name = stripped.split("(")[0].strip()
        spec = stripped.split("(")[1].rstrip(")")
        character.add_skill(name, speciality=spec)
        return f"Gained {name} ({spec}) 0"

    # Plain skill name
    character.add_skill(stripped)
    return f"Gained {stripped} 0"
