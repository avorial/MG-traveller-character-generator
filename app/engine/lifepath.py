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
#
# NOTE: These are intentionally tight. Earlier versions of this list
# included bare "roll " and "either ", which over-matched phrases like
# "Benefit roll" / "Survival roll this term" and "Gain either a jealous
# relative or an unhappy subject" — blocking dozens of legitimately
# unconditional grants. Use _CONDITIONAL_RE below for pattern-based
# detection (actual skill checks, DM-vs-X choice constructions).
_CONDITIONAL_MARKERS = (
    "on success",
    "on failure",
    "if you succeed",
    "if you fail",
    "; on ",
)

# Detects the patterns that should block auto-apply:
#   - Actual skill-check prefixes: "Roll Stealth 8+" / "Roll INT 8+".
#   - Choice constructions where DM is one of the alternatives:
#       "or DM+N", "or a DM+N", "or a +N DM", "or +N DM".
#       "or take DM+N"  (Solomani career wording).
#       Also "DM+N ... or ..." forms via the second alt.
_CONDITIONAL_RE = re.compile(
    # Actual skill-check prefix: "Roll Stealth 8+" / "Roll INT 8+".
    r"\broll\s+[A-Za-z][A-Za-z\s()\-]{0,40}?\b\d+\s*\+"
    # DM is the second alternative: ", or DM+N" / ", or a DM+N" / ", or +N DM".
    r"|,\s*or\s+(?:a\s+)?(?:dm\s*[+-]\d+|[+-]\d+\s*dm)"
    r"|\bor\s+(?:a\s+)?(?:dm\s*[+-]\d+|[+-]\d+\s*dm)\s+to\s+(?:a|any|your|one)"
    # "or take DM+N" — Solomani career variant (solsec, conf_navy, conf_army, party, sol_marine)
    r"|,?\s*or\s+take\s+(?:a\s+)?(?:dm\s*[+-]\d+|[+-]\d+\s*dm)"
    # DM is the first alternative: "DM+N ... , or pick up / gain / take / increase <skill>"
    r"|\bdm\s*[+-]\d+[^.]{0,80}?,\s*or\s+(?:pick\s+up|gain|take|increase|learn|get|choose)\b"
    # DM is one option, career transfer is the other: ", or transfer to ..."
    r"|,?\s*or\s+transfer\s+to\b",
    re.IGNORECASE,
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
    if any(marker in lowered for marker in _CONDITIONAL_MARKERS) or _CONDITIONAL_RE.search(event_text):
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


# Stat bonus parser — handles events like entertainer[12]: "You become a
# superstar in your field. You are automatically promoted and gain SOC +1."
# Only auto-applies unconditional grants; conditional/choice events are
# surfaced but not applied.
_STAT_BONUS_RE = re.compile(
    r"\b(STR|DEX|END|INT|EDU|SOC)\s*([+-]\d+)\b",
    re.IGNORECASE,
)


def _parse_event_stat_bonuses(event_text: str) -> list[dict]:
    """Return every 'STR/DEX/END/INT/EDU/SOC +/-N' grant in an event."""
    text = event_text or ""
    found: list[dict] = []
    for m in _STAT_BONUS_RE.finditer(text):
        stat = m.group(1).upper()
        try:
            amount = int(m.group(2))
        except ValueError:
            continue
        found.append({"stat": stat, "amount": amount, "span": m.span()})
    return found


def _apply_event_stat_bonuses(character: "Character", event_text: str) -> list[dict]:
    """Apply any unconditional stat bonuses (e.g., 'gain SOC +1') from an event.

    Returns the list of applied grants for the UI to narrate.
    """
    grants = _parse_event_stat_bonuses(event_text)
    if not grants:
        return []
    lowered = event_text.lower()
    if any(marker in lowered for marker in _CONDITIONAL_MARKERS) or _CONDITIONAL_RE.search(event_text):
        return [{"stat": g["stat"], "amount": g["amount"], "applied": False,
                 "reason": "conditional_or_choice"} for g in grants]
    applied: list[dict] = []
    for g in grants:
        old = character.characteristics.get(g["stat"])
        new_val = old + g["amount"]
        character.characteristics.set(g["stat"], new_val)
        sign = "+" if g["amount"] >= 0 else ""
        character.log(f"  - Event stat bonus: {g['stat']} {old} -> {new_val} ({sign}{g['amount']}).")
        applied.append({"stat": g["stat"], "amount": g["amount"], "applied": True,
                        "from": old, "to": new_val})
    return applied


_AUTO_PROMOTE_RE = re.compile(r"automatically\s+promoted", re.IGNORECASE)


def _apply_event_auto_promotion(character: "Character", event_text: str) -> dict | None:
    """Detect 'You are automatically promoted' in an event and bump rank.

    Returns a dict describing the promotion (for UI) or None if:
      - the event text doesn't say "automatically promoted"
      - the career has no ranks (Drifter, Scout) — returns {'skipped': True, ...}
      - there's no current term
      - the rank is already at the top of the table
    """
    if not _AUTO_PROMOTE_RE.search(event_text or ""):
        return None
    term = character.current_term
    if term is None:
        return None
    try:
        career = rules.careers()[term.career_id]
    except KeyError:
        return None

    # Rankless careers (Drifter, Scout) — surface it as a note but don't bump.
    ranks_data = career.get("ranks") or {}
    if not ranks_data:
        character.log(f"  - Event grants automatic promotion, but {term.career_id} has no rank structure — skipped.")
        return {"skipped": True, "reason": "rankless_career"}

    # Check for rank cap — some careers cap at rank 6.
    next_rank = term.rank + 1
    rank_data = _rank_data(career, term.assignment_id, next_rank)
    if rank_data is None and next_rank > 1:
        # No data for the next rank means we've hit the top.
        character.log(f"  - Event grants automatic promotion, but already at top rank for {term.career_id}/{term.assignment_id}.")
        return {"skipped": True, "reason": "rank_cap", "rank": term.rank}

    old_rank = term.rank
    term.rank = next_rank
    term.rank_title = _rank_title(career, term.assignment_id, term.rank)

    # Treat this term as already advanced so the player doesn't roll again.
    term.advanced = True

    rank_bonus_log = None
    if rank_data and rank_data.get("bonus"):
        bonus = rank_data["bonus"]
        rank_bonus_log = _apply_rank_bonus(character, bonus)
        term.skills_gained.append(f"Rank bonus (auto-promotion): {bonus}")

    title_part = f" — {term.rank_title}" if term.rank_title else ""
    character.log(f"  - Event grants AUTOMATIC PROMOTION: rank {old_rank} -> {term.rank}{title_part}.")
    if rank_bonus_log:
        character.log(f"  - {rank_bonus_log}")
    return {
        "skipped": False,
        "from_rank": old_rank,
        "to_rank": term.rank,
        "rank_title": term.rank_title,
        "bonus": (rank_data.get("bonus") if rank_data else None),
    }


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


_VALID_CHARS = {"STR", "DEX", "END", "INT", "EDU", "SOC"}


def test_psionics(character: "Character") -> dict:
    """Roll the Psionic Potential Test (2D 9+) and, on success, generate a Psi score.

    By RAW this opportunity is rare and GM-gated. The creator lets the
    player invoke it during the done/finalize phase with a DM-1 per
    previous term. Result is recorded on the character; follow up with
    train_psionic_talent for each talent to learn.
    """
    if character.psi_tested:
        raise ValueError(
            "This character has already been tested for psionics."
        )

    data = rules.psionics()
    pot = data["potential_test"]
    dm = -character.total_terms  # -1 per term

    # Check for species-level psionic bane (e.g. Bwaps).
    species_data = rules.species().get(character.species_id, {})
    has_psionic_bane = species_data.get("psionic_bane", False)

    if has_psionic_bane:
        r = dice.roll_bane_2d(modifier=dm, target=pot["target"])
        roll_label = f"BANE 3D drop highest{dm:+d}={r.total}"
    else:
        r = dice.roll("2D", modifier=dm, target=pot["target"])
        roll_label = f"2D{dm:+d}={r.total}"

    character.psi_tested = True

    if not r.succeeded:
        character.psi = 0
        character.log(
            f"Psionic potential test [{roll_label}]: FAILED "
            f"(needed {pot['target']}+). No psionic ability."
        )
        return {
            "potential_roll": r.to_dict(),
            "potential_succeeded": False,
            "psi": 0,
            "psionic_bane_applied": has_psionic_bane,
            "character": character.model_dump(),
        }

    # Passed — roll Psi strength: 2D minus total_terms, clamped.
    formula = data["psi_strength_formula"]
    raw = dice.roll(formula["dice"])
    psi_val = raw.total - character.total_terms
    psi_val = max(formula.get("min", 0), min(formula.get("max", 15), psi_val))
    character.psi = psi_val
    character.log(
        f"Psionic potential [{roll_label}]: PASSED. "
        f"Psi strength [2D-{character.total_terms}={raw.total}-{character.total_terms}={psi_val}]."
    )
    return {
        "potential_roll": r.to_dict(),
        "potential_succeeded": True,
        "psi_roll": raw.to_dict(),
        "psi": psi_val,
        "psionic_bane_applied": has_psionic_bane,
        "character": character.model_dump(),
    }


def train_psionic_talent(character: "Character", talent_id: str) -> dict:
    """Attempt to train a specific psionic talent. Costs Cr per talents table."""
    if not character.psi_tested:
        raise ValueError("Must complete the psionic potential test first.")
    if character.psi <= 0:
        raise ValueError("Character has no psionic ability to train.")
    if talent_id in character.psi_trained_talents:
        raise ValueError(f"Already trained in {talent_id}.")

    data = rules.psionics()
    talents = data["talents"]
    talent = talents.get(talent_id)
    if talent is None:
        raise ValueError(f"Unknown talent: {talent_id}")

    cost = talent.get("cost_cr", 200000)
    pcs = (character.pre_career_status or {}) if hasattr(character, "pre_career_status") else {}
    if pcs.get("pending_psionic_training"):
        cost = 0

    # Allow purchase even without sufficient credits — shortfall goes to medical debt.
    debt_incurred = 0
    if cost > 0:
        if character.credits >= cost:
            character.credits -= cost
        else:
            shortfall = cost - character.credits
            character.medical_debt += shortfall
            character.credits = 0
            debt_incurred = shortfall

    # DM = character.psi - talent target (Psi serves as the characteristic)
    target = talent.get("test_target", 8)
    dm = dice.characteristic_dm(character.psi)
    r = dice.roll("2D", modifier=dm, target=target)

    cost_note = f"Cr{cost:,}" if debt_incurred == 0 else f"Cr{cost - debt_incurred:,} paid + Cr{debt_incurred:,} medical debt"
    log_msg = (
        f"Psi training — {talent['name']} "
        f"[2D{dm:+d}={r.total} vs {target}+, cost {cost_note}]"
    )

    if r.succeeded:
        character.add_skill(talent["skill"], level=0)
        character.psi_trained_talents.append(talent_id)
        log_msg += f": PASSED. Gained {talent['skill']} 0."
    else:
        log_msg += ": FAILED. Credits spent anyway (training is expensive)."

    character.log(log_msg)
    return {
        "talent_id": talent_id,
        "talent_name": talent["name"],
        "roll": r.to_dict(),
        "succeeded": r.succeeded,
        "cost": cost,
        "debt_incurred": debt_incurred,
        "credits_remaining": character.credits,
        "medical_debt": character.medical_debt,
        "character": character.model_dump(),
    }


def generate_capsule(character: Character) -> dict:
    """Produce a capsule (one-paragraph) description of the character.

    Deterministic-ish summary: species, age, total terms, top career,
    top three skills, ship-share bragging rights. Used in the final
    phase to give the player a copy-pasteable elevator pitch.
    """
    species_data = rules.species().get(character.species_id, {"name": character.species_id})
    species_name = species_data.get("name", character.species_id)

    # Dominant career (most terms served)
    careers_sorted = sorted(
        character.completed_careers,
        key=lambda c: c.terms_served,
        reverse=True,
    )
    career_clause = ""
    if careers_sorted:
        top = careers_sorted[0]
        career_def = rules.careers().get(top.career_id, {})
        asgn = career_def.get("assignments", {}).get(top.assignment_id, {})
        rank_title = top.final_rank_title or (f"rank {top.final_rank}" if top.final_rank else None)
        career_clause = (
            f" spent {top.terms_served} term{'s' if top.terms_served != 1 else ''} as a "
            f"{(rank_title + ' ') if rank_title else ''}"
            f"{asgn.get('name', top.assignment_id).lower()} in the "
            f"{career_def.get('name', top.career_id)}"
        )
        if len(careers_sorted) > 1:
            career_clause += f", with {len(careers_sorted) - 1} other career{'s' if len(careers_sorted) != 2 else ''} along the way"

    # Top skills (level desc, then specialities)
    skills_sorted = sorted(
        character.skills, key=lambda s: (s.level, s.name), reverse=True
    )
    top_skills = [
        (f"{s.name} ({s.speciality})" if s.speciality else s.name) + f" {s.level}"
        for s in skills_sorted[:3]
        if s.level > 0
    ]
    skills_clause = ""
    if top_skills:
        skills_clause = f" Best known for {', '.join(top_skills)}."

    # Signature stats
    stats = character.characteristics
    notable_stat = max(
        ("STR", "DEX", "END", "INT", "EDU", "SOC"),
        key=lambda s: stats.get(s),
    )
    notable_val = stats.get(notable_stat)
    stat_label = {
        "STR": "imposing physical presence",
        "DEX": "preternatural reflexes",
        "END": "gruelling stamina",
        "INT": "sharp mind",
        "EDU": "broad education",
        "SOC": "impressive social standing",
    }.get(notable_stat, notable_stat)
    stat_clause = f" Notable for their {stat_label} ({notable_stat} {notable_val})."

    # Wealth / ship shares
    extras = []
    if character.credits >= 50000:
        extras.append(f"{character.credits:,} credits to their name")
    if character.ship_shares:
        extras.append(f"{character.ship_shares} ship share{'s' if character.ship_shares != 1 else ''}")
    if character.medical_debt:
        extras.append(f"Cr{character.medical_debt:,} in outstanding medical debt")
    if character.anagathics_addicted:
        extras.append("dependent on anagathic treatments")
    extras_clause = ""
    if extras:
        extras_clause = f" They carry {', and '.join(extras)}."

    homeworld_clause = ""
    if character.homeworld:
        uwp = f" ({character.homeworld_uwp})" if character.homeworld_uwp else ""
        homeworld_clause = f" born on {character.homeworld}{uwp},"

    name = character.name or "An unnamed Traveller"

    capsule = (
        f"{name} is a {character.age}-year-old {species_name}"
        f"{homeworld_clause} who"
        f"{career_clause or ' drifted through known space without a steady career'}."
        f"{skills_clause}{stat_clause}{extras_clause}"
    )

    return {"capsule": capsule, "length": len(capsule), "character": character.model_dump()}


def add_connection(character: Character, description: str, skill: Optional[str] = None) -> dict:
    """Record a Connection — a link to another PC (or an NPC) in the player group.

    Each connection grants one skill level at the GM's discretion; the
    engine applies it immediately if `skill` is provided.
    """
    desc = (description or "").strip()
    if not desc:
        raise ValueError("Connection description cannot be empty.")
    character.associates.append(
        Associate(kind="ally", description=f"Connection: {desc}")
    )
    bump_msg = ""
    if skill:
        bump_msg = character.add_skill(skill, level=1)
        character.log(f"Connection ({desc}) — {bump_msg}")
    else:
        character.log(f"Connection: {desc} (no skill bump applied)")
    return {
        "description": desc,
        "skill_applied": skill,
        "skill_log": bump_msg,
        "connection_count": sum(
            1 for a in character.associates
            if a.description.startswith("Connection: ")
        ),
        "character": character.model_dump(),
    }


def reroll_characteristic_boon(character: Character, stat: str) -> dict:
    """Re-roll one characteristic (2D), keeping the higher of old vs new.

    Commonly used as a GM-granted "boon" — a way to spare a Traveller
    from a truly disastrous starting roll. Only allowed during the
    characteristics phase; consumes one boon from the character's pool
    if the pool is set, otherwise always allowed (GM discretion).
    """
    if character.phase != "characteristics":
        raise ValueError(
            "Boon rolls are only available during the characteristics phase."
        )
    stat_u = stat.upper()
    if stat_u not in _VALID_CHARS:
        raise ValueError(f"Unknown characteristic: {stat}")
    if character.boon_rolls_remaining <= 0 and character.boon_rolls_total > 0:
        raise ValueError("No boon rolls remaining.")

    old = character.characteristics.get(stat_u)
    r = dice.roll("2D")
    new = r.total
    kept = max(old, new)
    character.characteristics.set(stat_u, kept)

    if character.boon_rolls_total > 0:
        character.boon_rolls_remaining = max(0, character.boon_rolls_remaining - 1)

    character.log(
        f"Boon re-roll on {stat_u}: 2D={new}, kept higher "
        f"({old} → {kept})."
    )
    return {
        "stat": stat_u,
        "old": old,
        "new": new,
        "kept": kept,
        "roll": r.to_dict(),
        "boon_rolls_remaining": character.boon_rolls_remaining,
        "character": character.model_dump(),
    }


def set_boon_pool(character: Character, count: int) -> dict:
    """Seed the boon-roll pool (GM-configurable). Zero = unlimited (boon panel hidden)."""
    count = max(0, int(count))
    character.boon_rolls_total = count
    character.boon_rolls_remaining = count
    character.log(f"Boon-roll pool set to {count}.")
    return {"boon_rolls_total": count, "character": character.model_dump()}



def swap_characteristics(character: Character, stat_a: str, stat_b: str) -> dict:
    """Swap two rolled characteristic values.

    Allowed only during the characteristics phase — once the player
    commits to a species the numbers are locked. MgT2e RAW lets a
    Traveller rearrange rolls into whatever slots they want; this
    function is the primitive for that (the UI can chain swaps to
    achieve any permutation).
    """
    if character.phase != "characteristics":
        raise ValueError(
            "Characteristics are locked once a species is selected."
        )
    a = stat_a.upper()
    b = stat_b.upper()
    if a not in _VALID_CHARS or b not in _VALID_CHARS:
        unknown = a if a not in _VALID_CHARS else b
        raise ValueError(f"Unknown characteristic: {unknown}")
    if a == b:
        raise ValueError("Cannot swap a characteristic with itself.")

    val_a = character.characteristics.get(a)
    val_b = character.characteristics.get(b)
    if val_a == 0 and val_b == 0:
        raise ValueError("Roll characteristics before rearranging them.")

    character.characteristics.set(a, val_b)
    character.characteristics.set(b, val_a)
    character.log(f"Swapped {a} ({val_a}) ↔ {b} ({val_b})")
    return {
        "character": character.model_dump(),
        "swapped": {a: val_b, b: val_a},
    }


def apply_species(character: Character, species_id: str) -> dict:
    """Apply species modifiers and record traits."""
    species_data = rules.species().get(species_id)
    if species_data is None:
        raise ValueError(f"Unknown species: {species_id}")

    # Canonicalize: if the caller passed an alias (e.g. legacy 'human'),
    # store the underlying id so downstream code sees a single stable value.
    canonical_id = species_data.get("id", species_id)
    character.species_id = canonical_id
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


def racial_background_roll(character: Character) -> dict:
    """Roll 2D to determine Solomani heritage subtype and apply the result.

    Table (from Solomani Confederation sourcebook):
      2        → confederation_human  (Non-Solomani Human)
      3–5      → solomani_mixed       (Mixed Heritage)
      6–12     → solomani_racial      (Racial Solomani)
    """
    r = dice.roll("2D")
    total = r.total

    if total <= 2:
        resolved_id = "confederation_human"
        result_name = "Non-Solomani Human"
    elif total <= 5:
        resolved_id = "solomani_mixed"
        result_name = "Mixed Heritage Solomani"
    else:
        resolved_id = "solomani_racial"
        result_name = "Racial Solomani"

    character.log(
        f"Solomani Heritage Roll: 2D={total} → {result_name} ({resolved_id})"
    )

    apply_result = apply_species(character, resolved_id)
    apply_result["heritage_roll"] = r.to_dict()
    apply_result["result_name"] = result_name
    apply_result["resolved_species_id"] = resolved_id
    return apply_result


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
    character.phase = "pre_career"
    character.pre_career_status = {
        "track": None,
        "service": None,
        "stage": "none",
        "outcome": None,
        "skill_picks_remaining": 0,
        "skill_pool": [],
    }
    return {"allowed": allowed_count, "chosen": chosen, "character": character.model_dump()}


# ============================================================
# Phase 1.5: Pre-career education (optional)
# ============================================================


def _edu_track(track: str) -> dict:
    tracks = rules.education()["tracks"]
    data = tracks.get(track)
    if data is None:
        raise ValueError(f"Unknown education track: {track}")
    return data


def _academy_service(service: str) -> dict:
    uni = _edu_track("military_academy")
    svc = uni["services"].get(service)
    if svc is None:
        raise ValueError(f"Unknown military academy service: {service}")
    return svc


def _split_skill_speciality(s: str) -> tuple[str, Optional[str]]:
    """Split 'Gun Combat (slug)' → ('Gun Combat', 'slug'). Plain name → (name, None)."""
    s = s.strip()
    if "(" in s and s.endswith(")"):
        name = s[: s.index("(")].strip()
        spec = s[s.index("(") + 1 : -1].strip()
        return name, spec
    return s, None


def _apply_enrollment_auto_skills(character: Character, skill_list: list[str]) -> list[str]:
    """Apply a list of 'Skill N' or 'Skill (spec) N' enrollment strings and return log messages."""
    applied: list[str] = []
    for skill_str in skill_list:
        parts = skill_str.rsplit(" ", 1)
        skill_part = parts[0].strip()
        level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        sn, spec = _split_skill_speciality(skill_part)
        msg = character.add_skill(sn, level=level, speciality=spec)
        applied.append(msg)
    return applied


def _homeworld_tl(uwp: str) -> int:
    """Parse TL from a UWP string (e.g. 'B86899D-A' → 10). Returns 99 if unparseable."""
    if not uwp:
        return 99
    parts = uwp.strip().split("-")
    if len(parts) < 2:
        return 99
    tl_char = parts[-1].strip()
    if not tl_char:
        return 99
    try:
        return int(tl_char, 16)
    except ValueError:
        return 99


def _homeworld_size(uwp: str) -> int:
    """Parse Size from a UWP string (e.g. 'B86899D-A' → 8, '000000 0-0' → 0). Returns -1 if unparseable."""
    uwp = uwp.strip()
    if len(uwp) < 2:
        return -1
    size_char = uwp[1]
    try:
        return int(size_char, 16)
    except ValueError:
        return -1


def _apply_graduation_permanent(character: Character, perm_block: dict, status: dict) -> list[str]:
    """Merge a graduation 'permanent' dict into character.pre_career_permanent_dms. Returns log notes."""
    notes: list[str] = []
    pdms = character.pre_career_permanent_dms or {}
    for k, v in perm_block.items():
        pdms[k] = v
        notes.append(f"Permanent {k}: {v}")
    # auto_rank_careers comes from enrollment status, not from the graduation block
    if "auto_rank" in perm_block and "auto_rank_careers" not in pdms:
        pdms["auto_rank_careers"] = status.get("auto_rank_careers", [])
    character.pre_career_permanent_dms = pdms
    return notes


def skip_pre_career(character: Character) -> dict:
    """Player chooses to skip pre-career education and go straight to careers."""
    if character.phase != "pre_career":
        raise ValueError(f"Not in pre-career phase (currently: {character.phase})")
    character.pre_career_status = {
        **character.pre_career_status,
        "stage": "skipped",
        "outcome": "skipped",
        "track": None,
        "service": None,
    }
    character.phase = "career"
    character.log("Skipped pre-career education — straight to service.")
    return {"character": character.model_dump()}


def pre_career_qualify(
    character: Character,
    track: str,
    service: Optional[str] = None,
    curriculum: Optional[str] = None,
) -> dict:
    """Roll qualification for any pre-career education track.

    Handles: university, military_academy, merchant_academy, colonial_upbringing,
    psionic_community, school_of_hard_knocks, spacer_community.

    On success: applies enrollment bonuses and advances to 'enrolled'.
    On failure: no bonus, falls through to career phase.
    """
    if character.phase != "pre_career":
        raise ValueError(f"Not in pre-career phase (currently: {character.phase})")

    track_data = _edu_track(track)

    # ─── Merchant Academy ────────────────────────────────────────────────────────
    if track == "merchant_academy":
        if not curriculum:
            # No curriculum chosen yet — return a "choosing_curriculum" state.
            character.pre_career_status = {
                **(character.pre_career_status or {}),
                "track": "merchant_academy",
                "stage": "choosing_curriculum",
                "outcome": None,
            }
            return {"choosing_curriculum": True, "character": character.model_dump()}

        if character.age > track_data["max_age"]:
            raise ValueError(
                f"Too old for Merchant Academy (age {character.age} > "
                f"max {track_data['max_age']})"
            )
        curricula = track_data.get("curricula", {})
        curr_data = curricula.get(curriculum)
        if curr_data is None:
            raise ValueError(f"Unknown Merchant Academy curriculum: {curriculum!r}")

        qual = track_data["qualification"]
        char_key = qual["characteristic"]
        target = qual["target"]
        dm = dice.characteristic_dm(character.characteristics.get(char_key))
        for mod in qual.get("modifiers", []):
            if mod.get("type") == "characteristic_threshold":
                if character.characteristics.get(mod["characteristic"]) >= int(mod["threshold"]):
                    dm += int(mod["dm"])

        r = dice.roll("2D", modifier=dm, target=target)
        passed = bool(r.succeeded)
        enrollment_applied: list[str] = []
        enrolled_skills: list[str] = []

        if passed:
            character.age += track_data["age_cost"]
            # Apply curriculum skill table at level 0
            skill_ref = curr_data["enrollment_skill_table"]
            career_data = rules.careers().get(skill_ref["career"], {})
            skill_table = career_data.get("skill_tables", {}).get(skill_ref["table"], {})
            _skip = {"name", "requires_commission", "requires_edu", "assignment_only"}
            for k, v in skill_table.items():
                if k in _skip:
                    continue
                entry = v.split(" or ")[0].strip()
                entry = re.sub(r"\s*\(any\)", "", entry, flags=re.I).strip()
                if not entry:
                    continue
                sn, spec = _split_skill_speciality(entry)
                msg = character.add_skill(sn, level=0, speciality=spec)
                enrollment_applied.append(msg)
                enrolled_skills.append(entry)

            character.pre_career_status = {
                "track": "merchant_academy",
                "curriculum": curriculum,
                "curriculum_name": curr_data.get("name", curriculum),
                "auto_rank_careers": curr_data.get("auto_rank_careers", []),
                "enrolled_skills": enrolled_skills,
                "service": None,
                "stage": "enrolled",
                "outcome": None,
                "skill_picks_remaining": 0,
                "skill_pick_level": 1,
                "skill_pick_stage": "graduation",
                "skill_pool": [],
                "enrollment_skill_pool": enrolled_skills,
            }
            character.log(
                f"Merchant Academy ({curr_data.get('name', curriculum)}) enrolled "
                f"({char_key} {target}+): 2D{dm:+d} = {r.total} [PASS]. "
                f"Curriculum skills: {', '.join(enrollment_applied)}"
            )
        else:
            character.pre_career_status = {
                "track": "merchant_academy",
                "curriculum": curriculum,
                "stage": "not_qualified",
                "outcome": "not_qualified",
                "skill_picks_remaining": 0,
                "skill_pool": [],
            }
            character.phase = "career"
            character.log(
                f"Merchant Academy failed ({char_key} {target}+): "
                f"2D{dm:+d} = {r.total} [FAIL]."
            )
        return {
            "roll": r.to_dict(),
            "passed": passed,
            "track": track,
            "curriculum": curriculum,
            "enrollment_applied": enrollment_applied,
            "character": character.model_dump(),
        }

    # ─── Colonial Upbringing ─────────────────────────────────────────────────────
    if track == "colonial_upbringing":
        hc = track_data["qualification"].get("homeworld_condition", {})
        tl_max = int(hc.get("tl_max", 8))
        tl = _homeworld_tl(character.homeworld_uwp or "")
        if tl > tl_max:
            raise ValueError(
                f"Colonial Upbringing requires homeworld TL {tl_max} or less "
                f"('{character.homeworld}' is TL {tl})."
            )
        enrollment_applied = _apply_enrollment_auto_skills(
            character, track_data.get("enrollment_auto_skills", [])
        )
        enrollment_pool = [
            s.rsplit(" ", 1)[0].strip()
            for s in track_data.get("enrollment_auto_skills", [])
        ]
        # No age cost, no qualification roll — automatic.
        character.pre_career_status = {
            "track": "colonial_upbringing",
            "service": None,
            "stage": "enrolled",
            "outcome": None,
            "skill_picks_remaining": 0,
            "skill_pool": [],
            "enrollment_skill_pool": enrollment_pool,
        }
        character.log(
            f"Colonial Upbringing: homeworld TL {tl} (≤{tl_max}). "
            f"Enrollment: {', '.join(enrollment_applied)}"
        )
        return {
            "passed": True,
            "automatic": True,
            "track": track,
            "enrollment_applied": enrollment_applied,
            "character": character.model_dump(),
        }

    # ─── Psionic Community ───────────────────────────────────────────────────────
    if track == "psionic_community":
        if character.age > track_data["max_age"]:
            raise ValueError(
                f"Too old for Psionic Community (age {character.age} > "
                f"max {track_data['max_age']})"
            )
        psi_roll_result: Optional[dict] = None
        # Test PSI now if not already tested.
        if not character.psi_tested:
            pr = dice.roll("2D")
            character.psi = pr.total
            character.psi_tested = True
            psi_roll_result = pr.to_dict()
            character.log(f"Psionic community: PSI tested — 2D = {pr.total}, PSI set to {pr.total}")

        qual = track_data["qualification"]
        target = qual["target"]
        psi_dm = dice.characteristic_dm(character.psi)
        for mod in qual.get("modifiers", []):
            if mod.get("type") == "characteristic_threshold":
                if character.characteristics.get(mod["characteristic"]) >= int(mod["threshold"]):
                    psi_dm += int(mod["dm"])

        r = dice.roll("2D", modifier=psi_dm, target=target)
        passed = bool(r.succeeded)
        enrollment_applied: list[str] = []

        if passed:
            character.age += track_data["age_cost"]
            enrollment_applied = _apply_enrollment_auto_skills(
                character, track_data.get("enrollment_auto_skills", [])
            )
            character.pre_career_status = {
                "track": "psionic_community",
                "service": None,
                "stage": "enrolled",
                "outcome": None,
                "skill_picks_remaining": 0,
                "skill_pool": [],
                "enrollment_skill_pool": [],
                "pending_psionic_training": True,
            }
            character.log(
                f"Psionic Community enrolled (PSI {target}+): "
                f"2D{psi_dm:+d} = {r.total} [PASS]. PSI = {character.psi}. "
                f"Enrollment: {', '.join(enrollment_applied) if enrollment_applied else 'none'}. "
                "Train a psionic talent from the Psionics panel."
            )
        else:
            character.pre_career_status = {
                "track": "psionic_community",
                "stage": "not_qualified",
                "outcome": "not_qualified",
                "skill_picks_remaining": 0,
                "skill_pool": [],
            }
            character.phase = "career"
            character.log(
                f"Psionic Community failed (PSI {target}+): "
                f"2D{psi_dm:+d} = {r.total} [FAIL]. PSI = {character.psi}."
            )
        return {
            "roll": r.to_dict(),
            "passed": passed,
            "track": track,
            "psi": character.psi,
            "psi_roll": psi_roll_result,
            "enrollment_applied": enrollment_applied,
            "character": character.model_dump(),
        }

    # ─── School of Hard Knocks ───────────────────────────────────────────────────
    if track == "school_of_hard_knocks":
        sc = track_data["qualification"].get("stat_condition", {})
        soc_max = int(sc.get("max", 6))
        soc = character.characteristics.get("SOC")
        if soc > soc_max:
            raise ValueError(
                f"School of Hard Knocks requires SOC {soc_max} or less (yours is {soc})."
            )
        character.age += track_data.get("age_cost", 2)
        enrollment_applied = _apply_enrollment_auto_skills(
            character, track_data.get("enrollment_auto_skills", [])
        )
        enrollment_pool = list(track_data.get("enrollment_skill_pool", []))
        enrollment_picks = int(track_data.get("enrollment_skill_picks", 0))
        enrollment_level = int(track_data.get("enrollment_pick_level", 0))

        character.pre_career_status = {
            "track": "school_of_hard_knocks",
            "service": None,
            "stage": "enrolled",
            "outcome": None,
            "skill_picks_remaining": enrollment_picks,
            "skill_pick_level": enrollment_level,
            "skill_pick_stage": "enrollment",
            "skill_pool": enrollment_pool,
            "enrollment_skill_pool": enrollment_pool,
        }
        character.log(
            f"School of Hard Knocks: SOC {soc} (≤{soc_max}) qualifies. "
            f"Enrollment: {', '.join(enrollment_applied) if enrollment_applied else 'none'}. "
            f"{enrollment_picks} skill picks remaining."
        )
        return {
            "passed": True,
            "automatic": True,
            "track": track,
            "enrollment_applied": enrollment_applied,
            "enrollment_picks": enrollment_picks,
            "enrollment_pool": enrollment_pool,
            "character": character.model_dump(),
        }

    # ─── Spacer Community ────────────────────────────────────────────────────────
    if track == "spacer_community":
        if character.age > track_data["max_age"]:
            raise ValueError(
                f"Too old for Spacer Community (age {character.age} > "
                f"max {track_data['max_age']})"
            )
        hc = track_data["qualification"].get("homeworld_condition", {})
        req_size = int(hc.get("size", 0))
        size = _homeworld_size(character.homeworld_uwp or "")
        if size != req_size:
            raise ValueError(
                f"Spacer Community requires homeworld size {req_size} "
                f"('{character.homeworld}' is size {size})."
            )
        qual = track_data["qualification"]
        char_key = qual["characteristic"]
        target = qual["target"]
        dm = dice.characteristic_dm(character.characteristics.get(char_key))
        for mod in qual.get("modifiers", []):
            if mod.get("type") == "characteristic_threshold":
                if character.characteristics.get(mod["characteristic"]) >= int(mod["threshold"]):
                    dm += int(mod["dm"])

        r = dice.roll("2D", modifier=dm, target=target)
        passed = bool(r.succeeded)
        enrollment_applied: list[str] = []
        enrollment_pool: list[str] = list(track_data.get("enrollment_skill_pool", []))

        if passed:
            character.age += track_data["age_cost"]
            enrollment_applied = _apply_enrollment_auto_skills(
                character, track_data.get("enrollment_auto_skills", [])
            )
            enrollment_picks = int(track_data.get("enrollment_skill_picks", 0))
            enrollment_level = int(track_data.get("enrollment_pick_level", 0))
            character.pre_career_status = {
                "track": "spacer_community",
                "service": None,
                "stage": "enrolled",
                "outcome": None,
                "skill_picks_remaining": enrollment_picks,
                "skill_pick_level": enrollment_level,
                "skill_pick_stage": "enrollment",
                "skill_pool": enrollment_pool,
                "enrollment_skill_pool": enrollment_pool,
            }
            character.log(
                f"Spacer Community enrolled ({char_key} {target}+): "
                f"2D{dm:+d} = {r.total} [PASS]. "
                f"Enrollment: {', '.join(enrollment_applied) if enrollment_applied else 'none'}. "
                f"{enrollment_picks} skill picks remaining."
            )
        else:
            character.pre_career_status = {
                "track": "spacer_community",
                "stage": "not_qualified",
                "outcome": "not_qualified",
                "skill_picks_remaining": 0,
                "skill_pool": [],
            }
            character.phase = "career"
            character.log(
                f"Spacer Community failed ({char_key} {target}+): "
                f"2D{dm:+d} = {r.total} [FAIL]."
            )
        return {
            "roll": r.to_dict(),
            "passed": passed,
            "track": track,
            "enrollment_applied": enrollment_applied,
            "enrollment_picks": int(track_data.get("enrollment_skill_picks", 0)) if passed else 0,
            "enrollment_pool": enrollment_pool if passed else [],
            "character": character.model_dump(),
        }

    # ─── University & Military Academy (original logic) ───────────────────────────
    if character.age > track_data["max_age"]:
        raise ValueError(
            f"Too old for {track_data['name']} (age {character.age} > "
            f"max {track_data['max_age']})"
        )

    if track == "military_academy":
        if not service:
            raise ValueError("Military academy requires a service (army|marine|navy)")
        svc = _academy_service(service)
        qual = svc["qualification"]
        display_name = svc["name"]
    else:
        qual = track_data["qualification"]
        display_name = track_data["name"]

    char_key = qual["characteristic"]
    target = qual["target"]
    dm = dice.characteristic_dm(character.characteristics.get(char_key))

    for mod in qual.get("modifiers", []):
        if mod.get("type") == "per_previous_term":
            dm += mod["dm"] * character.total_terms
        elif mod.get("type") == "per_previous_career":
            dm += mod["dm"] * len(character.completed_careers)

    r = dice.roll("2D", modifier=dm, target=target)
    passed = bool(r.succeeded)
    enrollment_applied: list[str] = []

    if passed:
        if track == "university":
            bonuses = track_data.get("enrollment_bonus", {})
            for stat, delta in bonuses.items():
                current = character.characteristics.get(stat)
                character.characteristics.set(stat, current + delta)
                enrollment_applied.append(f"{stat} {delta:+d}")
        else:
            career_data = rules.careers().get(svc["career_id"], {})
            ss = career_data.get("skill_tables", {}).get("service_skills", {})
            _skip = {"name", "requires_commission", "requires_edu", "assignment_only"}
            for k, v in ss.items():
                if k in _skip:
                    continue
                for part in v.split(" or "):
                    part = re.sub(r"\s*\(any\)", "", part.strip(), flags=re.I).strip()
                    if not part:
                        continue
                    skill_name = part
                    skill_spec = None
                    if "(" in part and part.endswith(")"):
                        skill_name = part[: part.index("(")].strip()
                        skill_spec = part[part.index("(") + 1 : -1].strip()
                    msg = character.add_skill(skill_name, level=0, speciality=skill_spec)
                    enrollment_applied.append(msg)
                    break

        character.age += track_data["age_cost"]

        enrollment_picks = 0
        enrollment_skill_pool: list[str] = []
        if track == "university":
            enrollment_picks = 2
            enrollment_skill_pool = list(track_data.get("skill_list", []))

        character.pre_career_status = {
            "track": track,
            "service": service,
            "stage": "enrolled",
            "outcome": None,
            "skill_picks_remaining": enrollment_picks,
            "skill_pick_level": 0,
            "skill_pick_stage": "enrollment",
            "skill_pool": enrollment_skill_pool,
        }
        character.log(
            f"Qualified for {display_name} ({char_key} {target}+): "
            f"2D{dm:+d} = {r.total} [PASS]. "
            + (f"Enrollment bonus: {', '.join(enrollment_applied)}"
               if enrollment_applied else "")
            + (f" — {enrollment_picks} enrollment skill picks pending" if enrollment_picks else "")
        )
    else:
        character.pre_career_status = {
            "track": track,
            "service": service,
            "stage": "not_qualified",
            "outcome": "not_qualified",
            "skill_picks_remaining": 0,
            "skill_pool": [],
        }
        character.phase = "career"
        character.log(
            f"Failed to qualify for {display_name} ({char_key} {target}+): "
            f"2D{dm:+d} = {r.total} [FAIL]. Moving on to a service career."
        )

    return {
        "roll": r.to_dict(),
        "passed": passed,
        "track": track,
        "service": service,
        "enrollment_applied": enrollment_applied,
        "character": character.model_dump(),
    }


def pre_career_graduate(
    character: Character,
    chosen_skills: Optional[list[str]] = None,
) -> dict:
    """Roll graduation for whatever pre-career track the character is enrolled in.

    On success / honours: applies the graduation bonuses (stat bumps, skills
    at level 1, possible DMs and commission for academies). On failure:
    applies the failure note and advances.
    """
    if character.phase != "pre_career":
        raise ValueError(f"Not in pre-career phase (currently: {character.phase})")

    status = character.pre_career_status or {}
    if status.get("stage") != "enrolled":
        raise ValueError("Not currently enrolled in a pre-career track")

    track = status.get("track")
    service = status.get("service")
    if track is None:
        raise ValueError("No pre-career track recorded on character")

    track_data = _edu_track(track)
    grad = track_data["graduation"]
    char_key = grad["characteristic"]
    target = grad["target"]
    honours_target = grad.get("honours_target")

    # PSI is stored on character root, not in characteristics block.
    if char_key == "PSI":
        char_val = character.psi
    else:
        char_val = character.characteristics.get(char_key)
    dm = dice.characteristic_dm(char_val)

    # Apply conditional modifiers (e.g. military academy: DM+1 if END 8+, DM+1 if SOC 8+).
    modifier_descriptions: list[str] = []
    for mod in grad.get("modifiers", []):
        if mod.get("type") == "characteristic_threshold":
            stat = mod["characteristic"]
            threshold = int(mod["threshold"])
            if stat == "PSI":
                check_val = character.psi
            else:
                check_val = character.characteristics.get(stat)
            if check_val >= threshold:
                dm += int(mod["dm"])
                modifier_descriptions.append(mod.get("description", ""))

    r = dice.roll("2D", modifier=dm, target=target)

    outcome: str
    applied_note: list[str] = []
    skill_pool: list[str] = []
    picks_remaining = 0
    pending_pick_rounds: list[dict] = []  # additional pick rounds queued after the first
    all_rounds: list[dict] = []           # all pick rounds (first assigned to picks_remaining)

    if not r.succeeded:
        outcome = "fail"
        fail_block = grad.get("on_failure", {})
        note = fail_block.get("note", "Failed to graduate.")
        applied_note.append(note)
        # Failed grads who didn't roll a natural 2 may auto-enter the tied career.
        if track == "military_academy" and fail_block.get("auto_entry_if_not_natural_2"):
            natural_dice = sorted(r.to_dict().get("dice", []))
            natural_2 = (len(natural_dice) == 2 and natural_dice == [1, 1])
            if not natural_2:
                svc = _academy_service(service)
                character.auto_entry_career_id = svc["career_id"]
                applied_note.append(
                    f"Did not roll natural 2 — automatic entry into "
                    f"{svc['name']} permitted (no Commission roll)."
                )
    else:
        is_honours = honours_target is not None and r.total >= honours_target
        block = grad["on_honours"] if is_honours else grad["on_graduation"]
        outcome = "honours" if is_honours else "pass"
        # Enrollment pool for this character (used by "from_enrollment" pick types)
        enroll_pool = list(status.get("enrollment_skill_pool", []))

        # ── Standard stat bumps ──────────────────────────────────────────────────
        for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
            if stat in block:
                delta = int(block[stat])
                current = character.characteristics.get(stat)
                character.characteristics.set(stat, current + delta)
                applied_note.append(f"{stat} {delta:+d}")

        # PSI bump
        if "PSI" in block:
            delta = int(block["PSI"])
            character.psi = max(0, character.psi + delta)
            applied_note.append(f"PSI {delta:+d}")

        # ── EDU penalty dice (e.g. colonial upbringing) ──────────────────────────
        if "EDU_penalty_dice" in block:
            pen_roll = dice.roll(str(block["EDU_penalty_dice"]))
            current_edu = character.characteristics.get("EDU")
            character.characteristics.set("EDU", current_edu - pen_roll.total)
            applied_note.append(f"EDU -{pen_roll.total} ({block['EDU_penalty_dice']}={pen_roll.total})")

        # ── Age override (e.g. "22+2D3") ────────────────────────────────────────
        if "age_override" in block:
            expr = str(block["age_override"])
            if "+" in expr:
                base_str, dice_str = expr.split("+", 1)
                age_roll = dice.roll(dice_str.strip())
                new_age = int(base_str.strip()) + age_roll.total
            else:
                new_age = int(expr)
            character.age = new_age
            applied_note.append(f"Age set to {new_age}")

        # ── Jack-of-all-Trades ───────────────────────────────────────────────────
        if "jack_of_all_trades" in block:
            joat_level = int(block["jack_of_all_trades"])
            character.add_skill("Jack-of-all-Trades", level=joat_level)
            applied_note.append(f"Jack-of-all-Trades {joat_level}")

        # ── Fixed skills ("Leadership 1": true or "fixed_skills": [...]) ─────────
        # Handle "fixed_skills" list: ["Science (psionicology) 1", "Gun Combat 0"]
        for sk_str in block.get("fixed_skills", []):
            parts = sk_str.rsplit(" ", 1)
            sk_part = parts[0].strip()
            sk_level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            sn, spec = _split_skill_speciality(sk_part)
            character.add_skill(sn, level=sk_level, speciality=spec)
            applied_note.append(f"Gained {sk_str}")
        # Handle "SkillName N": true pattern (e.g. "Leadership 1": true)
        for bk, bv in block.items():
            if bv is True and bk[-1].isdigit() and " " in bk:
                parts = bk.rsplit(" ", 1)
                if parts[1].isdigit():
                    sn, spec = _split_skill_speciality(parts[0].strip())
                    character.add_skill(sn, level=int(parts[1]), speciality=spec)
                    applied_note.append(f"Gained {bk}")

        # ── Pending DMs for next rolls ───────────────────────────────────────────
        if "dm_next_qualification" in block:
            character.dm_next_qualification += int(block["dm_next_qualification"])
            applied_note.append(
                f"DM{int(block['dm_next_qualification']):+d} next qualification"
            )
        if "dm_next_advancement" in block:
            character.dm_next_advancement += int(block["dm_next_advancement"])
            applied_note.append(
                f"DM{int(block['dm_next_advancement']):+d} next advancement"
            )
        if "dm_next_benefit" in block:
            character.dm_next_benefit += int(block["dm_next_benefit"])
            applied_note.append(
                f"DM{int(block['dm_next_benefit']):+d} next benefit"
            )

        # ── Permanent career DMs ──────────────────────────────────────────────────
        if "permanent" in block:
            perm_notes = _apply_graduation_permanent(character, block["permanent"], status)
            applied_note.extend(perm_notes)

        # ── Associates ───────────────────────────────────────────────────────────
        for assoc in block.get("associates", []):
            character.associates.append(
                Associate(kind=assoc["kind"], description=assoc.get("description", ""))
            )
            applied_note.append(f"Gained {assoc['kind'].title()}")

        # ── Psionic talent upgrades ───────────────────────────────────────────────
        psionics_data = rules.psionics()
        psi_talents_map = psionics_data.get("talents", {})

        if block.get("psionic_talent_upgrade") and character.psi_trained_talents:
            # Raise first trained talent's skill by 1 level
            tid = character.psi_trained_talents[0]
            talent_info = psi_talents_map.get(tid, {})
            skill_name = talent_info.get("skill", "")
            if skill_name:
                for sk in character.skills:
                    if sk.name == skill_name:
                        sk.level = min(sk.level + 1, 4)
                        break
                applied_note.append(f"Raised {skill_name} (psionic talent) to higher level")

        if block.get("psionic_all_talents_to_1"):
            for tid in character.psi_trained_talents:
                talent_info = psi_talents_map.get(tid, {})
                skill_name = talent_info.get("skill", "")
                if skill_name:
                    for sk in character.skills:
                        if sk.name == skill_name:
                            sk.level = max(sk.level, 1)
                            break
            applied_note.append("All trained psionic talents raised to level 1")

        if block.get("psionic_one_talent_to_2") and character.psi_trained_talents:
            # Flag: player should choose which talent to raise to 2 manually
            applied_note.append(
                "Raise one trained psionic talent to level 2 (use Psionics panel)"
            )

        # ── Academy commission handling ───────────────────────────────────────────
        if track == "military_academy":
            svc = _academy_service(service)
            if "starts_commissioned_rank" in block:
                character.starts_commissioned_career_id = svc["career_id"]
                applied_note.append(
                    f"starts {svc['name']} commissioned at Rank "
                    f"{block['starts_commissioned_rank']}"
                )
            elif "commission_dm" in block:
                character.academy_commission_career_id = svc["career_id"]
                character.academy_commission_dm = int(block["commission_dm"])
                applied_note.append(
                    f"Commission roll DM+{block['commission_dm']} when starting {svc['name']}"
                )

        # ── Graduation skill picks ────────────────────────────────────────────────
        # Collect all pick rounds, then assign the first one to skill_pool/picks_remaining
        # and queue the rest in pending_pick_rounds. Higher levels come first.
        all_rounds: list[dict] = []

        # Classic: skills_at_level_1 from track skill list or service skills
        picks_l1 = int(block.get("skills_at_level_1", 0))
        if picks_l1 > 0:
            if track == "university":
                l1_pool = list(track_data.get("skill_list", []))
            elif track == "military_academy":
                svc = _academy_service(service)
                career_data = rules.careers().get(svc["career_id"], {})
                ss = career_data.get("skill_tables", {}).get("service_skills", {})
                l1_pool = []
                _skip = {"name", "requires_commission", "requires_edu", "assignment_only"}
                for k, v in ss.items():
                    if k in _skip:
                        continue
                    for part in v.split(" or "):
                        part = re.sub(r"\s*\(any\)", "", part.strip(), flags=re.I).strip()
                        if part:
                            l1_pool.append(part)
                if not l1_pool:
                    l1_pool = ["Gun Combat", "Melee", "Drive", "Electronics", "Tactics"]
            else:
                l1_pool = list(enroll_pool)
            all_rounds.append({"count": picks_l1, "level": 1, "pool": l1_pool,
                                "label": "Pick skill at level 1"})

        # Upgrade from enrollment pool: pick N enrolled skills to raise to level 1
        upgrade_count = int(block.get("skills_upgrade_from_enrollment", 0))
        if upgrade_count > 0:
            up_pool = list(enroll_pool) if enroll_pool else list(skill_pool)
            all_rounds.append({"count": upgrade_count, "level": 1, "pool": up_pool,
                                "label": "Upgrade enrollment skill to level 1"})

        # Pick N from enrollment pool at level 1
        from_enroll_1 = int(block.get("skills_from_enrollment_1", 0))
        if from_enroll_1 > 0:
            fe1_pool = list(enroll_pool) if enroll_pool else list(skill_pool)
            all_rounds.append({"count": from_enroll_1, "level": 1, "pool": fe1_pool,
                                "label": "Pick enrollment skill at level 1"})

        # Pick N from enrollment pool at level 0 (goes last — lowest level)
        from_enroll_0 = int(block.get("additional_skills_from_enrollment_0", 0))
        if from_enroll_0 > 0:
            fe0_pool = list(enroll_pool) if enroll_pool else list(skill_pool)
            all_rounds.append({"count": from_enroll_0, "level": 0, "pool": fe0_pool,
                                "label": "Pick enrollment skill at level 0"})

        # Assign first round to skill_pool/picks_remaining, queue the rest
        if all_rounds:
            first = all_rounds[0]
            skill_pool = first["pool"]
            picks_remaining = first["count"]
            # skill_pick_level will be set from first["level"] when building status
            pending_pick_rounds = [
                {"count": rnd["count"], "level": rnd["level"], "pool": rnd["pool"]}
                for rnd in all_rounds[1:]
            ]

        if block.get("note"):
            applied_note.append(block["note"])

    # Pre-apply any skills chosen with the graduate call (one-shot flow)
    if chosen_skills and picks_remaining:
        if len(chosen_skills) > picks_remaining:
            raise ValueError(
                f"Chose {len(chosen_skills)} skills but only "
                f"{picks_remaining} picks available."
            )
        for s in chosen_skills:
            if s not in skill_pool:
                raise ValueError(
                    f"'{s}' is not in the skill pool for this track."
                )
            name = s
            speciality = None
            if "(" in s and s.endswith(")"):
                name = s[: s.index("(")].strip()
                speciality = s[s.index("(") + 1 : -1].strip()
            character.add_skill(name, level=1, speciality=speciality)
        picks_remaining -= len(chosen_skills)

    # Log graduation result.
    label = {"pass": "GRADUATED", "honours": "GRADUATED w/ HONOURS",
             "fail": "FAILED TO GRADUATE"}[outcome]
    character.log(
        f"Graduation ({char_key} {target}+"
        + (f", Honours {honours_target}+" if honours_target else "")
        + f"): 2D{dm:+d} = {r.total} [{label}]. "
        + ("; ".join(applied_note) if applied_note else "")
    )

    # Always roll the pre-career education chart event immediately after
    # graduation — one roll regardless of pass/fail.
    edu = rules.education()
    events_table: dict = edu.get("pre_career_events", {})
    ev = dice.roll("2D")
    ev_key = str(ev.total)
    event_text: str = events_table.get(ev_key, "Nothing remarkable happens.")
    event_auto_applied: list[str] = []
    forced_fail = False

    if ev.total == 2:
        # Psionic contact — roll 2D for PSI characteristic, flag Psion available.
        psi_roll = dice.roll("2D")
        character.psi = psi_roll.total
        character.psi_tested = True
        event_auto_applied.append(f"PSI tested: rolled {psi_roll.total} — PSI = {psi_roll.total}")
        event_auto_applied.append("Psion career now available in any subsequent term")

    if ev.total == 3:
        forced_fail = True
        if outcome in ("pass", "honours"):
            # Override graduation: character fails.
            outcome = "fail"
            character.starts_commissioned_career_id = None
            character.academy_commission_career_id = None
            character.academy_commission_dm = 0
            if track == "military_academy" and service:
                edu_track = _edu_track(track)
                fail_block = edu_track["graduation"].get("on_failure", {})
                if fail_block.get("auto_entry_if_not_natural_2"):
                    svc = _academy_service(service)
                    character.auto_entry_career_id = svc["career_id"]
                    event_auto_applied.append(
                        f"Forced failure — automatic entry into {svc['name']} (no Commission roll)"
                    )
            # Clear any skill picks that were granted — they no longer apply.
            picks_remaining = 0
            skill_pool = []
            event_auto_applied.append("Graduation result overridden — failed to graduate")

    if ev.total == 4:
        # Prank gone wrong — roll SOC 8+. Natural 2 = must take Prisoner next term.
        soc_val = character.characteristics.get("SOC")
        soc_dm = dice.characteristic_dm(soc_val)
        soc_roll = dice.roll("2D", modifier=soc_dm, target=8)
        if soc_roll.raw_total == 2:
            # Natural 2 — forced into Prisoner career.
            character.forced_next_career_id = "prisoner"
            event_auto_applied.append(
                f"SOC check: natural 2! Must take Prisoner career next term."
            )
        elif soc_roll.succeeded:
            character.associates.append(
                Associate(kind="rival", description="Rival [Education] — prank gone wrong")
            )
            event_auto_applied.append(
                f"SOC {soc_val} check (2D{soc_dm:+d}={soc_roll.total} vs 8+): passed — gained Rival [Education]"
            )
        else:
            character.associates.append(
                Associate(kind="enemy", description="Enemy [Education] — prank gone wrong")
            )
            event_auto_applied.append(
                f"SOC {soc_val} check (2D{soc_dm:+d}={soc_roll.total} vs 8+): failed — gained Enemy [Education]"
            )

    if ev.total == 5:
        character.add_skill("Carouse", level=1)
        event_auto_applied.append("Gained Carouse 1")

    if ev.total == 6:
        # Tight-knit clique — gain D3 Allies.
        d3_roll = dice.roll("D3")
        count = d3_roll.total
        for _ in range(count):
            character.associates.append(
                Associate(kind="ally", description="Ally [Education] — close clique")
            )
        event_auto_applied.append(f"D3={count} — gained {count} Ally [Education]")

    if ev.total == 7:
        # Life Event — roll on the Life Events table immediately.
        life_result = apply_life_event(character)
        event_auto_applied.extend(life_result["auto_applied"])
        if life_result.get("pending_choice"):
            event_auto_applied.append("PENDING: resolve the life event choice below")

    if ev.total == 8:
        # Political movement — roll SOC 8+: success → Ally [Political Movement] + Enemy [Society].
        soc_val = character.characteristics.get("SOC")
        soc_dm = dice.characteristic_dm(soc_val)
        soc_roll = dice.roll("2D", modifier=soc_dm, target=8)
        if soc_roll.succeeded:
            character.associates.append(
                Associate(kind="ally", description="Ally [Political Movement]")
            )
            character.associates.append(
                Associate(kind="enemy", description="Enemy [Society]")
            )
            event_auto_applied.append(
                f"SOC {soc_val} check (2D{soc_dm:+d}={soc_roll.total} vs 8+): passed — "
                f"Ally [Political Movement] + Enemy [Society]"
            )
        else:
            event_auto_applied.append(
                f"SOC {soc_val} check (2D{soc_dm:+d}={soc_roll.total} vs 8+): failed — no effect"
            )

    if ev.total == 9:
        # Player picks any skill (except Jack-of-All-Trades) at level 0 — resolved by JS.
        event_auto_applied.append("Pending: choose any skill at level 0 (see skill picker below)")

    if ev.total == 10:
        # Tutor challenge — player picks an education skill, rolls 2D 9+ for bonus.
        # Resolved interactively; flag for JS.
        event_auto_applied.append("Pending: pick an education skill for the tutor challenge")

    if ev.total == 11:
        # Draft event — player must choose: Drifter / be Drafted / Dodge (SOC 9+).
        # Resolved interactively; flag for JS.
        event_auto_applied.append("Pending: choose your response to the draft (see options below)")

    if ev.total == 12:
        current_soc = character.characteristics.get("SOC")
        character.characteristics.set("SOC", current_soc + 1)
        event_auto_applied.append("SOC +1")

    character.log(
        f"Pre-career education event [{ev.total}]: {event_text}"
        + (f" — {', '.join(event_auto_applied)}" if event_auto_applied else "")
    )

    # Build the event 10 skill pool: same as graduation skill_pool if non-empty,
    # else fall back to the full track skill list (covers the failed-grad case).
    event10_pool: list[str] = list(skill_pool) if skill_pool else []
    if not event10_pool:
        if track == "university":
            td = _edu_track(track)
            event10_pool = list(td.get("skill_list", []))
        elif track == "military_academy" and service:
            svc = _academy_service(service)
            career_data = rules.careers().get(svc["career_id"], {})
            ss = career_data.get("skill_tables", {}).get("service_skills", {})
            _skip = {"name", "requires_commission", "requires_edu", "assignment_only"}
            for k, v in ss.items():
                if k in _skip:
                    continue
                for part in v.split(" or "):
                    part = re.sub(r"\s*\(any\)", "", part.strip(), flags=re.I).strip()
                    if part:
                        event10_pool.append(part)
            if not event10_pool:
                event10_pool = ["Gun Combat", "Melee", "Drive", "Electronics", "Tactics"]

    pending_event10 = ev.total == 10 and not forced_fail
    pending_event11 = ev.total == 11 and not forced_fail

    # Determine the pick level for the first pending round (if any).
    # all_rounds is only defined inside the else block; check if it exists.
    first_round_level = 1  # classic default (graduation = level 1)
    if outcome != "fail" and all_rounds:
        first_round_level = all_rounds[0]["level"] if all_rounds else 1

    # Set final status. Phase stays pre_career if skill picks are still pending;
    # otherwise advance to career now.
    character.pre_career_status = {
        "track": track,
        "service": service,
        "curriculum": status.get("curriculum"),
        "auto_rank_careers": status.get("auto_rank_careers", []),
        "enrolled_skills": status.get("enrolled_skills", []),
        "enrollment_skill_pool": status.get("enrollment_skill_pool", []),
        "stage": "graduated" if outcome != "fail" else "failed_grad",
        "outcome": outcome,
        "skill_picks_remaining": picks_remaining,
        "skill_pick_level": first_round_level,
        "skill_pick_stage": "graduation",  # when done, advance to career
        "skill_pool": skill_pool,
        "pending_pick_rounds": pending_pick_rounds,
        "events_remaining": 0,
        "events_rolled": [ev.total],
        "pending_event10": pending_event10,
        "pending_event11": pending_event11,
        "event10_skill_pool": event10_pool,
    }
    # Always stay in pre_career so the JS can show the graduation+event screen.
    # The phase advances to career when the user clicks Continue (no picks)
    # or when pre_career_choose_skills completes the last pick.
    character.phase = "pre_career"

    return {
        "roll": r.to_dict(),
        "outcome": outcome,
        "char_key": char_key,
        "target": target,
        "honours_target": honours_target,
        "skill_pool": skill_pool,
        "skill_pick_level": first_round_level,
        "skill_picks_remaining": picks_remaining,
        "applied": applied_note,
        "event": {
            "roll": ev.to_dict(),
            "event_text": event_text,
            "auto_applied": event_auto_applied,
            "forced_fail": forced_fail,
            "pending_any_skill": ev.total == 9 and not forced_fail,
            "pending_event10": pending_event10,
            "pending_event11": pending_event11,
            "pending_life_event": bool(character.pending_life_event_choice),
            "life_event_choice_kind": (
                character.pending_life_event_choice.get("kind")
                if character.pending_life_event_choice else None
            ),
            "pending_injury": bool(character.pending_injury_choice),
            "injury_pending_data": character.pending_injury_choice,
        },
        "character": character.model_dump(),
    }


def pre_career_choose_skills(
    character: Character, chosen_skills: list[str]
) -> dict:
    """Apply pending skill picks (enrollment at level 0, or graduation at level 1).

    skill_pick_level in pre_career_status controls the level applied.
    skill_pick_stage controls what happens when picks are exhausted:
      - "enrollment": stay in pre_career for events/graduation
      - "graduation": advance phase to "career"
    """
    status = character.pre_career_status or {}
    remaining = int(status.get("skill_picks_remaining", 0))
    pool = list(status.get("skill_pool", []))
    skill_level = int(status.get("skill_pick_level", 1))
    skill_pick_stage = status.get("skill_pick_stage", "graduation")

    if remaining <= 0:
        raise ValueError("No pending skill picks.")
    if len(chosen_skills) > remaining:
        raise ValueError(
            f"Chose {len(chosen_skills)} skills but only {remaining} picks left."
        )
    for s in chosen_skills:
        if s not in pool:
            raise ValueError(f"'{s}' not in this track's skill pool.")
        name = s
        speciality = None
        if "(" in s and s.endswith(")"):
            name = s[: s.index("(")].strip()
            speciality = s[s.index("(") + 1 : -1].strip()
        character.add_skill(name, level=skill_level, speciality=speciality)

    remaining -= len(chosen_skills)
    stage_label = "enrollment" if skill_pick_stage == "enrollment" else "graduation"
    character.log(
        f"Picked {len(chosen_skills)} pre-career {stage_label} skill(s) at level {skill_level}: "
        + ", ".join(chosen_skills)
    )

    if remaining == 0:
        pending_rounds = list(status.get("pending_pick_rounds", []))
        if pending_rounds and skill_pick_stage == "graduation":
            # Advance to the next round of graduation picks
            next_round = pending_rounds.pop(0)
            character.pre_career_status = {
                **status,
                "skill_picks_remaining": next_round["count"],
                "skill_pick_level": next_round["level"],
                "skill_pool": next_round["pool"],
                "pending_pick_rounds": pending_rounds,
            }
            # Stay in pre_career for more picks
        elif skill_pick_stage == "graduation":
            character.phase = "career"
            character.pre_career_status = {
                **status,
                "skill_picks_remaining": 0,
                "skill_pool": [],
                "pending_pick_rounds": [],
            }
        else:
            # enrollment stage: clear picks, stay in pre_career for events/graduation
            character.pre_career_status = {
                **status,
                "skill_picks_remaining": 0,
                "skill_pool": [],
            }
    else:
        character.pre_career_status = {
            **status,
            "skill_picks_remaining": remaining,
        }

    new_remaining = character.pre_career_status.get("skill_picks_remaining", 0)
    return {
        "chosen": chosen_skills,
        "skill_picks_remaining": remaining,
        "new_picks_remaining": new_remaining,
        "skill_pick_stage": skill_pick_stage,
        "has_more_rounds": new_remaining > 0 and remaining == 0,
        "character": character.model_dump(),
    }


def pre_career_grant_any_skill(character: Character, skill_text: str) -> dict:
    """Grant the free skill from education event 9 (any skill at level 0)."""
    text = (skill_text or "").strip()
    if not text:
        raise ValueError("No skill specified.")
    if text == "Jack-of-All-Trades":
        raise ValueError("Jack-of-All-Trades cannot be chosen for this event.")
    speciality: str | None = None
    if "(" in text and text.endswith(")"):
        name = text[: text.index("(")].strip()
        speciality = text[text.index("(") + 1 : -1].strip()
    else:
        name = text
    character.add_skill(name, level=0, speciality=speciality)
    character.log(f"Education event 9: gained {text} 0")
    return {"character": character.model_dump()}


def pre_career_event10_skill(character: Character, skill_text: str) -> dict:
    """Event 10 — tutor challenge.

    Player picks a skill from the education skill pool and rolls 2D 9+.
    Success: +1 in that skill + Rival [Tutor].
    """
    status = character.pre_career_status or {}
    if not status.get("pending_event10"):
        raise ValueError("No pending event 10 tutor challenge.")

    pool = status.get("event10_skill_pool", [])
    text = (skill_text or "").strip()
    if not text:
        raise ValueError("No skill specified.")
    if pool and text not in pool:
        raise ValueError(f"'{text}' is not in the education skill pool for this track.")

    r = dice.roll("2D", target=9)
    if r.succeeded:
        name = text
        speciality: str | None = None
        if "(" in text and text.endswith(")"):
            name = text[: text.index("(")].strip()
            speciality = text[text.index("(") + 1 : -1].strip()
        msg = character.add_skill(name, level=1, speciality=speciality)
        character.associates.append(
            Associate(kind="rival", description="Rival [Tutor] — education event 10")
        )
        character.log(
            f"Education event 10: tutor challenge on {text} — 2D={r.total} (9+) SUCCESS. "
            f"{msg}. Rival [Tutor] added."
        )
    else:
        character.log(
            f"Education event 10: tutor challenge on {text} — 2D={r.total} (9+) FAILED. No bonus."
        )

    character.pre_career_status = {**status, "pending_event10": False}
    if not character.pre_career_status.get("skill_picks_remaining"):
        character.phase = "career"

    return {
        "roll": r.to_dict(),
        "succeeded": r.succeeded,
        "skill": text,
        "character": character.model_dump(),
    }


def pre_career_event11_choice(character: Character, choice: str) -> dict:
    """Event 11 — draft event.

    choice: "drifter" | "draft" | "dodge"
    - drifter: forced into Drifter career next term (no graduation).
    - draft: roll 1D, forced into Army/Marine/Navy (no graduation).
    - dodge: roll SOC 9+. Success = keep graduation. Fail = fail to graduate.
    """
    status = character.pre_career_status or {}
    if not status.get("pending_event11"):
        raise ValueError("No pending event 11 draft choice.")

    roll_result: Optional[dict] = None
    draft_career: Optional[str] = None

    def _clear_graduation_bonuses() -> None:
        character.starts_commissioned_career_id = None
        character.academy_commission_career_id = None
        character.academy_commission_dm = 0
        character.auto_entry_career_id = None

    if choice == "drifter":
        _clear_graduation_bonuses()
        character.forced_next_career_id = "drifter"
        character.pre_career_status = {
            **status,
            "stage": "failed_grad",
            "outcome": "fail",
            "skill_picks_remaining": 0,
            "pending_event11": False,
        }
        character.log("Education event 11: fled into Drifter career (did not graduate)")
        character.phase = "career"

    elif choice == "draft":
        d6 = random.randint(1, 6)
        if character.society_id == "solomani_confederation":
            # Solomani draft table:
            # 1=Confederation Navy, 2=Confederation Army, 3=Star Marines,
            # 4=Merchant, 5=SolSec, 6=Agent
            solomani_draft = [
                "confederation_navy", "confederation_army", "solomani_marine",
                "merchant", "solsec", "agent",
            ]
            draft_career = solomani_draft[d6 - 1]
        else:
            # Imperial draft table: 1-3=Army, 4-5=Marine, 6=Navy
            if d6 <= 3:
                draft_career = "army"
            elif d6 <= 5:
                draft_career = "marine"
            else:
                draft_career = "navy"
        _clear_graduation_bonuses()
        character.forced_next_career_id = draft_career
        character.pre_career_status = {
            **status,
            "stage": "failed_grad",
            "outcome": "fail",
            "skill_picks_remaining": 0,
            "pending_event11": False,
        }
        character.log(
            f"Education event 11: drafted — D6={d6} → {draft_career} (did not graduate)"
        )
        roll_result = {"dice": [d6], "raw_total": d6, "total": d6}
        character.phase = "career"

    elif choice == "dodge":
        soc_val = character.characteristics.get("SOC")
        soc_dm = dice.characteristic_dm(soc_val)
        r = dice.roll("2D", modifier=soc_dm, target=9)
        roll_result = r.to_dict()
        if r.succeeded:
            # Draft dodged — keep graduation result unchanged.
            character.pre_career_status = {**status, "pending_event11": False}
            character.log(
                f"Education event 11: draft dodge — SOC {soc_val} check "
                f"2D{soc_dm:+d}={r.total} vs 9+ SUCCESS. Graduation stands."
            )
            # Advance to career if no picks left.
            if not character.pre_career_status.get("skill_picks_remaining"):
                character.phase = "career"
        else:
            _clear_graduation_bonuses()
            character.pre_career_status = {
                **status,
                "stage": "failed_grad",
                "outcome": "fail",
                "skill_picks_remaining": 0,
                "pending_event11": False,
            }
            character.log(
                f"Education event 11: draft dodge — SOC {soc_val} check "
                f"2D{soc_dm:+d}={r.total} vs 9+ FAILED. Did not graduate."
            )
            character.phase = "career"
    else:
        raise ValueError(f"Unknown event 11 choice: {choice!r}. Must be 'drifter', 'draft', or 'dodge'.")

    return {
        "choice": choice,
        "roll": roll_result,
        "draft_career": draft_career,
        "character": character.model_dump(),
    }


def apply_life_event(character: Character, career_id: Optional[str] = None) -> dict:
    """Roll 2D on the Life Events table and auto-apply everything possible.

    Pass career_id to route to the appropriate table (e.g. Solomani careers
    use the Solomani Life Events table instead of the standard one).

    Returns a dict describing what happened. Interactive outcomes set
    character.pending_life_event_choice so the caller can prompt the player.
    """
    if career_id is None and character.current_term is not None:
        career_id = character.current_term.career_id
    use_solomani = career_id in rules.SOLOMANI_CAREER_IDS

    r = dice.roll("2D")
    total = r.total
    auto_applied: list[str] = []
    pending_choice: Optional[dict] = None

    if total == 2:
        # Sickness or Injury — roll on the Injury table; stat choice is pending.
        injury = apply_injury(character)
        auto_applied.append(f"Injury rolled: {injury.get('title', 'see log')} — choose stat below")
        if injury.get("pending_choice"):
            auto_applied.append("PENDING: choose which physical stat absorbs the damage")

    elif total == 3:
        # Birth or Death — someone close dies or is born.
        character.associates.append(
            Associate(kind="contact", description="Dead — Friend/Family [Birth or Death Event]")
        )
        auto_applied.append("Noted Dead — Friend/Family in associates")

    elif total == 4:
        # Standard: Ending of Relationship — player picks Rival or Enemy.
        # Solomani: Racial Incident — also Rival or Enemy.
        pending_choice = {"kind": "romantic_split"}
        if use_solomani:
            auto_applied.append("PENDING: choose Rival or Enemy [Racial Incident]")
        else:
            auto_applied.append("PENDING: choose Rival [Romantic] or Enemy [Romantic]")

    elif total == 5:
        if use_solomani:
            # SolSec Scrutiny — DM-1 to next advancement roll.
            character.dm_next_advancement -= 1
            auto_applied.append("SolSec Scrutiny: DM-1 to next advancement roll")
        else:
            # Improved Relationship — gain Ally [Romantic].
            character.associates.append(Associate(kind="ally", description="Ally [Romantic]"))
            auto_applied.append("Gained Ally [Romantic]")

    elif total == 6:
        if use_solomani:
            # Party Connections — gain Contact [Solomani Party].
            character.associates.append(
                Associate(kind="contact", description="Contact [Solomani Party/Confederation]")
            )
            auto_applied.append("Gained Contact [Solomani Party/Confederation]")
        else:
            # New Relationship — gain Ally [Romantic].
            character.associates.append(Associate(kind="ally", description="Ally [Romantic]"))
            auto_applied.append("Gained Ally [Romantic]")

    elif total == 7:
        # New Contact — gain Contact [Generic].
        character.associates.append(Associate(kind="contact", description="Contact [Generic]"))
        auto_applied.append("Gained Contact [Generic]")

    elif total == 8:
        # Betrayal — convert first Contact/Ally or gain Rival/Enemy.
        contacts = [i for i, a in enumerate(character.associates) if a.kind == "contact"]
        allies = [i for i, a in enumerate(character.associates) if a.kind == "ally"]
        if contacts:
            old = character.associates[contacts[0]]
            old_desc = old.description or "Contact"
            character.associates[contacts[0]] = Associate(
                kind="rival", description=f"Rival [Betrayer] (was: {old_desc})"
            )
            auto_applied.append(f"Contact '{old_desc}' converted to Rival [Betrayer]")
        elif allies:
            old = character.associates[allies[0]]
            old_desc = old.description or "Ally"
            character.associates[allies[0]] = Associate(
                kind="enemy", description=f"Enemy [Betrayer] (was: {old_desc})"
            )
            auto_applied.append(f"Ally '{old_desc}' converted to Enemy [Betrayer]")
        else:
            # No contacts or allies — player picks which to gain.
            pending_choice = {"kind": "betrayal_no_associates"}
            auto_applied.append("PENDING: no existing Contact/Ally — choose Rival or Enemy [Betrayer]")

    elif total == 9:
        # Travel / Relocation — DM+2 to next Qualification roll.
        character.dm_next_qualification += 2
        auto_applied.append("DM+2 to next Qualification roll")

    elif total == 10:
        # Good Fortune — one DM+2 token for any benefit roll.
        character.good_fortune_benefit_dm += 2
        auto_applied.append("Good Fortune: DM+2 token available for one mustering-out benefit roll")

    elif total == 11:
        if use_solomani:
            # Solomani Pride — SOC+1.
            soc = character.characteristics.get("SOC", 7)
            character.characteristics["SOC"] = min(soc + 1, character.characteristic_max("SOC"))
            auto_applied.append("Solomani Pride: SOC+1")
        else:
            # Crime — player picks: lose a benefit roll OR take Prisoner career.
            pending_choice = {
                "kind": "crime_choice",
                "has_benefit_rolls": character.pending_benefit_rolls > 0,
            }
            auto_applied.append("PENDING: choose crime consequence (lose benefit roll or Prisoner career)")

    elif total == 12:
        # Unusual Event — roll 1D sub-event.
        d6 = dice.roll("1D")
        sub = d6.total
        if sub == 1:
            # Psionics — test PSI immediately.
            psi_roll = dice.roll("2D")
            character.psi = psi_roll.total
            character.psi_tested = True
            auto_applied.append(f"Psionics: PSI tested, rolled {psi_roll.total}. Psion career available.")
        elif sub == 2:
            # Aliens — gain Science 1 (alien race) + Contact [Alien].
            character.add_skill("Science", level=1, speciality="Alien Races")
            character.associates.append(Associate(kind="contact", description="Contact [Alien]"))
            auto_applied.append("Gained Science (Alien Races) 1 and Contact [Alien]")
        elif sub == 3:
            # Alien Artefact / Terran Artefact — add to equipment.
            item_name = "Terran Artefact (Historical)" if use_solomani else "Alien Artefact"
            character.equipment.append(Equipment(name=item_name, notes="Unusual Event 12-3"))
            auto_applied.append(f"{item_name} added to equipment")
        elif sub == 4:
            # Amnesia.
            character.associates.append(
                Associate(kind="contact", description="Unknown [Amnesia] — something happened")
            )
            auto_applied.append("Noted Unknown [Amnesia] in associates")
        elif sub == 5:
            # Contact with Government / Confederation Elite.
            gov_label = "Met [Confederation Elite]" if use_solomani else "Met [Government Official] — Imperial contact"
            character.associates.append(
                Associate(kind="contact", description=gov_label)
            )
            auto_applied.append(f"Noted {gov_label} in associates")
        elif sub == 6:
            # Ancient Technology.
            character.equipment.append(Equipment(name="Ancient Technology", notes="Unusual Event 12-6"))
            auto_applied.append("Ancient Technology added to equipment")
        auto_applied.insert(0, f"Unusual Event sub-roll: D6={sub}")

    # Fetch descriptive text from the appropriate life-events table.
    life_table_data = rules.life_events_for_career(career_id or "")
    event_text = life_table_data["entries"].get(str(total), {})
    if isinstance(event_text, dict):
        event_text = f"{event_text.get('title', '')}: {event_text.get('text', 'Something happens in your life.')}"
    elif not event_text:
        # Fallback: try the legacy education.life_events path.
        edu = rules.education()
        legacy_table: dict = edu.get("life_events", {})
        event_text = legacy_table.get(str(total), "Something happens in your life.")

    character.log(
        f"Life Event [{total}]: {event_text}"
        + (f" — {', '.join(auto_applied)}" if auto_applied else "")
    )

    if pending_choice:
        character.pending_life_event_choice = pending_choice

    return {
        "roll": r.to_dict(),
        "total": total,
        "event_text": event_text,
        "auto_applied": auto_applied,
        "pending_choice": pending_choice,
    }


def resolve_life_event_choice(character: Character, choice: str) -> dict:
    """Resolve a pending interactive Life Event choice.

    choice values per kind:
      romantic_split          → "rival" | "enemy"
      betrayal_no_associates  → "rival" | "enemy"
      crime_choice            → "lose_benefit" | "prisoner"
    """
    pending = character.pending_life_event_choice
    if not pending:
        raise ValueError("No pending life event choice to resolve.")

    kind = pending.get("kind")
    if kind == "romantic_split":
        if choice == "rival":
            character.associates.append(Associate(kind="rival", description="Rival [Romantic]"))
            character.log("Life Event 4: gained Rival [Romantic]")
        elif choice == "enemy":
            character.associates.append(Associate(kind="enemy", description="Enemy [Romantic]"))
            character.log("Life Event 4: gained Enemy [Romantic]")
        else:
            raise ValueError(f"Unknown choice '{choice}' for romantic_split")

    elif kind == "betrayal_no_associates":
        if choice == "rival":
            character.associates.append(Associate(kind="rival", description="Rival [Betrayer]"))
            character.log("Life Event 8: gained Rival [Betrayer]")
        elif choice == "enemy":
            character.associates.append(Associate(kind="enemy", description="Enemy [Betrayer]"))
            character.log("Life Event 8: gained Enemy [Betrayer]")
        else:
            raise ValueError(f"Unknown choice '{choice}' for betrayal_no_associates")

    elif kind == "crime_choice":
        if choice == "lose_benefit":
            if character.pending_benefit_rolls <= 0:
                raise ValueError("No benefit rolls remaining to lose.")
            character.pending_benefit_rolls -= 1
            character.log("Life Event 11 (Crime): lost one benefit roll")
        elif choice == "prisoner":
            character.forced_next_career_id = "prisoner"
            character.log("Life Event 11 (Crime): must take Prisoner career next term")
        else:
            raise ValueError(f"Unknown choice '{choice}' for crime_choice")

    else:
        raise ValueError(f"Unknown pending life event kind: {kind!r}")

    character.pending_life_event_choice = None
    return {"choice": choice, "kind": kind, "character": character.model_dump()}


def pre_career_event_roll(character: Character) -> dict:
    """Roll once on the pre-career events table (2D).

    Called after graduation. One event roll per period of pre-career
    education (university or military academy). The character remains
    in the pre_career phase until this roll is done, then moves to career.

    Simple outcomes (Carouse 1, SOC +1) are auto-applied.
    Complex outcomes are described in event_text for manual resolution.
    """
    status = character.pre_career_status or {}
    valid_stages = ("graduated", "failed_grad", "enrolled")
    if status.get("stage") not in valid_stages:
        raise ValueError("Pre-career event roll is only available after enrollment/graduation")

    events_remaining = status.get("events_remaining")
    if events_remaining is None:
        # Migration: field absent means the event hasn't been rolled yet.
        events_remaining = 1
    events_remaining = int(events_remaining)
    if events_remaining <= 0:
        raise ValueError("Pre-career event already rolled for this track")

    edu = rules.education()
    events_table: dict = edu.get("pre_career_events", {})

    r = dice.roll("2D")
    key = str(r.total)
    event_text: str = events_table.get(key, "Nothing remarkable happens.")

    auto_applied: list[str] = []
    forced_fail = False

    if r.total == 3:
        # Deep tragedy — if character had passed or received honours,
        # that graduation result is overridden: they fail to graduate.
        forced_fail = True
        prior_outcome = status.get("outcome", "fail")
        if prior_outcome in ("pass", "honours"):
            track = status.get("track")
            service = status.get("service")
            # Reverse any academy commission flags set by graduation.
            character.starts_commissioned_career_id = None
            character.academy_commission_career_id = None
            character.academy_commission_dm = 0
            if track == "military_academy" and service:
                edu_track = _edu_track(track)
                fail_block = edu_track["graduation"].get("on_failure", {})
                if fail_block.get("auto_entry_if_not_natural_2"):
                    svc = _academy_service(service)
                    character.auto_entry_career_id = svc["career_id"]
                    auto_applied.append(
                        f"Forced failure — automatic entry into {svc['name']} "
                        f"(no Commission roll)"
                    )
            auto_applied.append("Graduation result overridden — failed to graduate")

    if r.total == 5:
        character.add_skill("Carouse", level=1)
        auto_applied.append("Gained Carouse 1")

    if r.total == 12:
        current_soc = character.characteristics.get("SOC")
        character.characteristics.set("SOC", current_soc + 1)
        auto_applied.append("SOC +1")

    character.pre_career_status = {
        **status,
        "events_remaining": 0,
        "events_rolled": [*status.get("events_rolled", []), r.total],
    }
    character.phase = "career"

    character.log(
        f"Pre-career event [{r.total}]: {event_text}"
        + (f" — auto-applied: {', '.join(auto_applied)}" if auto_applied else "")
    )

    return {
        "roll": r.to_dict(),
        "event_text": event_text,
        "events_remaining": 0,
        "auto_applied": auto_applied,
        "forced_fail": forced_fail,
        "character": character.model_dump(),
    }


# ============================================================
# Phase 2: Career loop
# ============================================================


# Mongoose 2e Draft table (1D6). Each entry is (career_id, assignment_id).
# When a player fails qualification they may choose to accept the draft
# instead of falling back to Drifter — the service and assignment are
# determined by a single d6.
_DRAFT_TABLE: dict[int, tuple[str, str]] = {
    1: ("navy", "line_crew"),
    2: ("army", "infantry"),
    3: ("marine", "support"),
    4: ("merchant", "merchant_marine"),
    5: ("scout", "courier"),
    6: ("agent", "law_enforcement"),
}


def draft_into_service(character: Character) -> dict:
    """Roll 1D on the draft table and auto-start a term in the assigned service.

    Called after a failed career qualification when the player chooses
    'accept the draft' instead of falling back to Drifter. The drafted
    character still goes through survival/events/advancement normally —
    the only difference is they didn't pick the career themselves.
    """
    if character.phase != "career":
        raise ValueError(f"Not in career phase (currently: {character.phase})")
    if character.current_term is not None:
        raise ValueError("Cannot be drafted while already in an active term.")

    r = dice.roll("1D")
    career_id, assignment_id = _DRAFT_TABLE[max(1, min(6, r.total))]
    career = rules.careers().get(career_id)
    if career is None:
        raise ValueError(f"Draft table points at unknown career '{career_id}'")

    character.log(
        f"Drafted [1D={r.total}] into {career['name']} — "
        f"{career['assignments'][assignment_id]['name']}"
    )

    # Reuse start_term so the drafted character enters the career exactly
    # like any other first term (incl. basic training).
    term_result = start_term(character, career_id, assignment_id)

    return {
        "roll": r.to_dict(),
        "career_id": career_id,
        "assignment_id": assignment_id,
        "career_name": career["name"],
        "assignment_name": career["assignments"][assignment_id]["name"],
        "term": term_result["term"],
        "character": character.model_dump(),
    }


def qualify_for_career(character: Character, career_id: str) -> dict:
    """Roll qualification for entering a career."""
    career = rules.careers().get(career_id)
    if career is None:
        raise ValueError(f"Unknown career: {career_id}")

    # Event-granted career transfer. Consume the offer and skip qualification.
    # 'any' means the player accepted an open transfer to any career.
    if (character.pending_transfer_career_id == career_id
            or character.pending_transfer_career_id == "any"):
        character.pending_transfer_career_id = None
        character.log(
            f"Transferring to {career['name']} via event offer — no qualification roll required."
        )
        return {"automatic": True, "succeeded": True, "transfer": True,
                "character": character.model_dump()}

    # Military Academy graduate: auto-qualify for the tied service career.
    if (character.starts_commissioned_career_id == career_id
            or character.academy_commission_career_id == career_id
            or character.auto_entry_career_id == career_id):
        if character.auto_entry_career_id == career_id:
            character.auto_entry_career_id = None
        character.log(
            f"Military Academy graduate — no qualification roll required for {career['name']}."
        )
        return {"automatic": True, "succeeded": True, "character": character.model_dump()}

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
        elif mod["type"] == "age" and character.age >= mod.get("threshold", mod.get("age_threshold", 99)):
            dm += mod["dm"]

    # Apply permanent pre-career education DMs
    pdms = character.pre_career_permanent_dms or {}

    # Psion auto-entry (Psionic Community graduate)
    if career_id == "psion" and pdms.get("psion_career_auto_entry"):
        character.log(f"Psionic Community graduate — automatic entry into Psion career.")
        return {"automatic": True, "succeeded": True, "character": character.model_dump()}

    # Global qualification penalty (e.g. colonial_upbringing -2)
    qual_dm_perm = int(pdms.get("qualification_dm", 0))
    # Bonus for specific careers (e.g. colonial_upbringing rogue/scout +1 instead)
    bonus_careers = list(pdms.get("bonus_qualify_careers", []))
    bonus_dm = int(pdms.get("bonus_qualify_dm", 0))
    if bonus_careers and career_id in bonus_careers:
        # Use bonus DM instead of penalty
        dm += bonus_dm
    elif qual_dm_perm:
        dm += qual_dm_perm

    # Solomani species traits apply to all careers a Confederation character
    # can take — any career with a qualification roll except Drifter/Prisoner.
    _is_solomani_confederation = character.society_id == "solomani_confederation"
    _has_qualification = career_id not in rules.CAREERS_WITHOUT_QUALIFICATION

    # Party Patronage: Racial Solomani add their SOC DM to every qualification roll.
    party_patronage_dm = 0
    if _is_solomani_confederation and character.species_id == "solomani_racial" and _has_qualification:
        soc_val = character.characteristics.SOC
        party_patronage_dm = dice.characteristic_dm(soc_val)
        if party_patronage_dm != 0:
            dm += party_patronage_dm

    # Mixed Heritage: DM-1 to every qualification roll in Confederation careers.
    mixed_heritage_dm = 0
    if _is_solomani_confederation and character.species_id == "solomani_mixed" and _has_qualification:
        mixed_heritage_dm = -1
        dm += mixed_heritage_dm

    # Apply DM from prior events (e.g. Travel life event)
    dm += character.dm_next_qualification
    pending = character.dm_next_qualification
    character.dm_next_qualification = 0

    r = dice.roll("2D", modifier=dm, target=target)
    result = r.to_dict()
    result["characteristic_used"] = char_display
    result["pending_dm_consumed"] = pending
    qual_notes = []
    if party_patronage_dm:
        qual_notes.append(f"Party Patronage DM{party_patronage_dm:+d}")
    if mixed_heritage_dm:
        qual_notes.append(f"Mixed Heritage DM{mixed_heritage_dm:+d}")
    note_str = f" [{', '.join(qual_notes)}]" if qual_notes else ""
    character.log(
        f"Qualification for {career['name']}: 2D{dm:+d} vs {target}+ "
        f"= {r.total} ({'pass' if r.succeeded else 'fail'}){note_str}"
    )
    return {"succeeded": r.succeeded, "roll": result, "character": character.model_dump()}


def start_term(
    character: Character,
    career_id: str,
    assignment_id: str,
    cover_career_id: Optional[str] = None,
) -> dict:
    """Begin a new career term in the given career + assignment.

    cover_career_id is only valid for SolSec Secret Agent; it stores which
    career the agent is publicly operating under so survival/advancement rolls
    can use that career's stats (with DM-1 / DM+1 respectively).
    """
    career = rules.careers().get(career_id)
    if career is None:
        raise ValueError(f"Unknown career: {career_id}")
    if assignment_id not in career["assignments"]:
        raise ValueError(f"Unknown assignment '{assignment_id}' for {career['name']}")

    # Validate cover career for Secret Agent
    if cover_career_id and career_id == "solsec" and assignment_id == "secret_agent":
        cover = rules.careers().get(cover_career_id)
        if cover is None:
            raise ValueError(f"Unknown cover career: {cover_career_id}")
    elif cover_career_id:
        cover_career_id = None  # Silently ignore for non-Secret Agent terms

    # Figure out if this is basic training (first term in this career, ever)
    is_new_career = (
        character.current_term is None
        or character.current_term.career_id != career_id
    )
    first_term_in_this_career = is_new_career and not any(
        c.career_id == career_id for c in character.completed_careers
    )

    # Pre-career military academy honored: first term in matching career
    # starts commissioned at Rank 1.
    commissioned_start = (
        first_term_in_this_career
        and character.starts_commissioned_career_id == career_id
    )

    # Normal Military Academy grad: roll Commission 8+ with stored DM.
    academy_commission_roll = None
    if (
        first_term_in_this_career
        and not commissioned_start
        and character.academy_commission_career_id == career_id
        and character.academy_commission_dm > 0
    ):
        comm_data = career.get("commission", {})
        comm_target = comm_data.get("target", 8)
        comm_dm = character.academy_commission_dm
        r_comm = dice.roll("2D", modifier=comm_dm, target=comm_target)
        commissioned_start = bool(r_comm.succeeded)
        academy_commission_roll = r_comm.to_dict()
        character.academy_commission_career_id = None
        character.academy_commission_dm = 0
        character.log(
            f"Academy commission roll: 2D+{comm_dm} vs {comm_target}+ "
            f"= {r_comm.total} ({'commissioned' if commissioned_start else 'not commissioned'})"
        )

    # Merchant Academy auto_rank: first career in a matching career starts at rank N.
    pdms = character.pre_career_permanent_dms or {}
    auto_rank = int(pdms.get("auto_rank", 0))
    auto_rank_careers = list(pdms.get("auto_rank_careers", []))
    is_first_career = len(character.completed_careers) == 0 and character.total_terms == 0
    merchant_auto_rank = (
        auto_rank > 0
        and first_term_in_this_career
        and career_id in auto_rank_careers
        and is_first_career
        and not commissioned_start
    )

    if commissioned_start:
        starting_rank = 1
    elif merchant_auto_rank:
        starting_rank = auto_rank
        commissioned_start = True  # treat as a commissioned start for term setup purposes
    elif not is_new_career and character.current_term is not None:
        starting_rank = character.current_term.rank
    else:
        starting_rank = 0

    term = CareerTerm(
        career_id=career_id,
        assignment_id=assignment_id,
        term_number=1 if is_new_career else (character.current_term.term_number + 1),
        overall_term_number=character.total_terms + 1,
        rank=starting_rank,
        rank_title=_rank_title(career, assignment_id, starting_rank),
        basic_training=is_first_career and not commissioned_start,
        commissioned=commissioned_start,
        cover_career_id=cover_career_id or None,
    )
    character.current_term = term

    # Consume the auto-commission flag so subsequent terms don't re-trigger it.
    if character.starts_commissioned_career_id == career_id:
        character.starts_commissioned_career_id = None

    cover_note = ""
    if cover_career_id:
        cover_career = rules.careers().get(cover_career_id, {})
        cover_note = f" [Cover: {cover_career.get('name', cover_career_id)}]"

    character.log(
        f"Begin Term {term.overall_term_number}: {career['name']} — "
        f"{career['assignments'][assignment_id]['name']}{cover_note}"
        + (" (Basic Training)" if term.basic_training else "")
        + (f" — commissioned at Rank {starting_rank}"
           f"{' (' + term.rank_title + ')' if term.rank_title else ''}"
           if commissioned_start else "")
    )

    # Apply rank-0 bonus (e.g. Army Private gets Gun Combat 1).
    rank0_data = _rank_data(career, assignment_id, 0)
    if rank0_data and rank0_data.get("bonus") and first_term_in_this_career and not commissioned_start:
        bonus0 = rank0_data["bonus"]
        rank0_log = _apply_rank_bonus(character, bonus0)
        term.skills_gained.append(f"Rank 0 bonus: {bonus0}")
        character.log(f"  Rank 0 bonus: {rank0_log}")

    # Basic training: auto-apply all 6 service_skills entries at level 0.
    basic_training_skills: list[str] = []
    if first_term_in_this_career and not commissioned_start:
        service_table = career.get("skill_tables", {}).get("service_skills", {})
        for i in range(1, 7):
            entry = service_table.get(str(i), "")
            if not entry:
                continue
            # "X or Y" — take X
            skill_name = entry.split(" or ")[0].strip()
            # Skip pure stat boosts like "STR +1"
            if re.match(r"^(STR|DEX|END|INT|EDU|SOC|PSI)\s*[+-]\d+$", skill_name):
                continue
            # Parse optional speciality
            if "(" in skill_name and skill_name.endswith(")"):
                sname = skill_name[: skill_name.index("(")].strip()
                spec = skill_name[skill_name.index("(") + 1: -1].strip()
                character.add_skill(sname, level=0, speciality=spec)
                disp = f"{sname} ({spec}) 0"
            else:
                character.add_skill(skill_name, level=0)
                disp = f"{skill_name} 0"
            basic_training_skills.append(disp)
        if basic_training_skills:
            term.skills_gained.extend([f"Basic training: {s}" for s in basic_training_skills])
            character.log(f"  Basic training applied: {', '.join(basic_training_skills)}")

    result: dict = {"term": term.model_dump(), "character": character.model_dump()}
    if academy_commission_roll is not None:
        result["academy_commission_roll"] = academy_commission_roll
    if basic_training_skills:
        result["basic_training_skills"] = basic_training_skills
    return result


def survival_roll(character: Character) -> dict:
    """Roll survival for the current term's assignment.

    For SolSec Secret Agents the roll uses the cover career's survival
    characteristic and target with DM-1 (operating undercover is riskier).
    """
    term = character.current_term
    if term is None:
        raise ValueError("No active term")

    cover_note = ""
    if term.cover_career_id:
        # Secret Agent: use cover career survival DM-1
        cover_career = rules.careers().get(term.cover_career_id, {})
        cover_assignment_id = list(cover_career.get("assignments", {}).keys())[0]
        cover_asgn = cover_career["assignments"][cover_assignment_id]
        survival = cover_asgn["survival"]
        cover_dm = -1
        cover_note = f" [Cover: {cover_career.get('name', term.cover_career_id)}, DM-1]"
    else:
        career = rules.careers()[term.career_id]
        assignment = career["assignments"][term.assignment_id]
        survival = assignment["survival"]
        cover_dm = 0

    char_key = survival["characteristic"]
    target = survival["target"]
    dm = dice.characteristic_dm(character.characteristics.get(char_key)) + cover_dm
    r = dice.roll("2D", modifier=dm, target=target)
    term.survived = bool(r.succeeded)
    term.survival_roll_total = r.total

    msg = (
        f"Survival ({char_key} {target}+){cover_note}: 2D{dm:+d} = {r.total} "
        f"[{'SURVIVED' if r.succeeded else 'MISHAP'}]"
    )
    character.log(msg)

    parallel_event = None

    # ---- SolSec Monitor parallel events ----
    if character.solsec_monitor:
        if r.raw_total == 2:
            # Natural 2: SolSec Mishap table replaces career mishap for the roll
            solsec_career = rules.careers().get("solsec", {})
            solsec_mishaps = solsec_career.get("mishaps", {})
            mishap_r = dice.roll("1D")
            mishap_key = str(max(1, min(6, mishap_r.total)))
            mishap_text = solsec_mishaps.get(mishap_key, "(SolSec mishap — see rulebook)")
            character.log(
                f"SolSec Monitor: natural 2 — SolSec Mishap [{mishap_r.total}]: {mishap_text}"
            )
            parallel_event = {
                "type": "monitor_mishap",
                "roll": mishap_r.to_dict(),
                "text": mishap_text,
            }
        elif r.raw_total == 12:
            # Natural 12: SolSec Event + gain SolSec Contact
            solsec_career = rules.careers().get("solsec", {})
            solsec_events = solsec_career.get("events", {})
            evt_r = dice.roll("2D")
            evt_key = str(evt_r.total)
            evt_text = solsec_events.get(evt_key, "(SolSec event — see rulebook)")
            character.associates.append(
                Associate(kind="contact", description="SolSec Agent [Monitor Contact]")
            )
            character.log(
                f"SolSec Monitor: natural 12 — SolSec Event [{evt_r.total}]: {evt_text}. "
                f"Gained SolSec Agent as Contact."
            )
            parallel_event = {
                "type": "monitor_event",
                "roll": evt_r.to_dict(),
                "text": evt_text,
                "contact_gained": "SolSec Agent",
            }

    # ---- Home Forces Reserves parallel nat-2 check ----
    if character.home_forces_enrolled and r.raw_total == 2:
        # Natural 2 on regular survival → ALSO roll Army/Navy Mishap table
        reserve_mishap_career_id = (
            "confederation_navy" if character.home_forces_component == "naval" else "confederation_army"
        )
        # Fallback to imperial equivalents if confederation versions not loaded
        reserve_career = (
            rules.careers().get(reserve_mishap_career_id)
            or rules.careers().get("navy" if character.home_forces_component == "naval" else "army", {})
        )
        reserve_mishaps = reserve_career.get("mishaps", {})
        mishap_r = dice.roll("1D")
        mishap_key = str(max(1, min(6, mishap_r.total)))
        mishap_text = reserve_mishaps.get(mishap_key, "(Home Forces mishap — see rulebook)")
        component_label = "Naval" if character.home_forces_component == "naval" else "Groundside"
        character.log(
            f"Home Forces Reserves ({component_label}): natural 2 — "
            f"Reserve Mishap [{mishap_r.total}]: {mishap_text}"
        )
        hf_parallel = {
            "type": "home_forces_mishap",
            "component": character.home_forces_component,
            "roll": mishap_r.to_dict(),
            "text": mishap_text,
        }
        # Return both if monitor also triggered one
        if parallel_event:
            parallel_event = [parallel_event, hf_parallel]
        else:
            parallel_event = hf_parallel

    # ── Anagathics: second survival check required (RAW p.155) ──────────
    anagathics_second_roll = None
    if character.anagathics_active and r.succeeded:
        # Must pass a SECOND survival check; if this fails → mishap despite first pass.
        r2 = dice.roll("2D", modifier=dm, target=target)
        anagathics_second_roll = r2.to_dict()
        if not r2.succeeded:
            # Second check failed → overall mishap
            term.survived = False
            character.log(
                f"Anagathics second survival check [2D{dm:+d}={r2.total}]: FAILED "
                f"(need {target}+) — Mishap despite passing first check."
            )
        else:
            character.log(
                f"Anagathics second survival check [2D{dm:+d}={r2.total}]: PASSED."
            )

    return {
        "roll": r.to_dict(),
        "survived": term.survived,    # reflects both checks
        "anagathics_second_roll": anagathics_second_roll,
        "parallel_event": parallel_event,
        "character": character.model_dump(),
    }


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

    # Life Event sub-table handling — route to career-appropriate table.
    if event_text.lower().startswith("life event"):
        life_r = dice.roll("2D")
        career_id_for_evt = term.career_id if term else ""
        life_table_data = rules.life_events_for_career(career_id_for_evt)
        life_data = life_table_data["entries"].get(str(life_r.total))
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

    # Auto-apply any unconditional stat bonuses ("SOC +1" etc.). Only handles
    # the rare cases like entertainer[12]; conditional/choice events are
    # surfaced as pending but not applied.
    stat_bonuses = _apply_event_stat_bonuses(character, event_text)

    # Auto-apply "automatically promoted" events (event [12] in most careers).
    # Bumps rank, records the rank bonus, and prevents double-advancement.
    auto_promotion = _apply_event_auto_promotion(character, event_text)
    if auto_promotion and not auto_promotion.get("skipped"):
        character.log(
            f"  → Auto-promoted to rank {auto_promotion['to_rank']}"
            f" ({auto_promotion.get('rank_title') or '—'})."
        )

    return {
        "roll": r.to_dict(),
        "event": event_text,
        "dm_grants": dm_grants,
        "stat_bonuses": stat_bonuses,
        "auto_promotion": auto_promotion,
        "character": character.model_dump(),
    }


def _apply_mishap_effect(character: "Character", effect: dict, term) -> tuple[list[str], bool]:
    """Apply a single mishap effect. Returns (auto_applied_msgs, set_pending).

    set_pending is True if this effect set character.pending_career_mishap_choice.
    Only one pending can be active at a time — caller skips further pending-creating
    effects once one is set.
    """
    etype = effect["type"]
    msgs: list[str] = []
    set_pending = False

    if etype == "injury":
        # Handled separately — caller stores result in injury_data
        pass

    elif etype == "injury_severity_choice":
        character.pending_career_mishap_choice = {"type": "injury_severity_choice"}
        set_pending = True

    elif etype in ("enemy", "rival", "contact", "ally"):
        desc = effect.get("desc", "")
        character.associates.append(Associate(kind=etype, description=desc))
        msgs.append(f"Gained {etype.capitalize()}: {desc}")
        character.log(f"Mishap: gained {etype} — {desc}")

    elif etype == "stat":
        stat = effect["stat"]
        amount = effect["amount"]
        old = character.characteristics.get(stat)
        new_val = max(0, old + amount)
        character.characteristics.set(stat, new_val)
        msgs.append(f"{stat} {old}→{new_val} ({amount:+d})")
        character.log(f"Mishap: {stat} {old}→{new_val}")

    elif etype == "stat_choice":
        if not character.pending_career_mishap_choice:
            character.pending_career_mishap_choice = {
                "type": "stat_choice",
                "options": effect["options"],
                "amount": effect["amount"],
                "prompt": f"Choose one stat to reduce by {abs(effect['amount'])}: {', '.join(effect['options'])}",
            }
            set_pending = True

    elif etype == "skill":
        name = effect["name"]
        level = effect.get("level", 1)
        msg = character.add_skill(name, level=level)
        msgs.append(msg)

    elif etype == "skill_choice":
        if not character.pending_career_mishap_choice:
            character.pending_career_mishap_choice = {
                "type": "skill_choice",
                "options": effect["options"],
                "prompt": f"Choose one skill to gain at level 1: {', '.join(effect['options'])}",
            }
            set_pending = True

    elif etype == "forfeit_benefit":
        if term is not None:
            term.benefit_forfeited = True
        msgs.append("This term's benefit roll forfeited")
        character.log("Mishap: benefit roll forfeited")

    elif etype == "debt":
        amount = effect["amount"]
        character.medical_debt += amount
        msgs.append(f"Debt: Cr{amount:,} added")
        character.log(f"Mishap: Cr{amount:,} debt added")

    elif etype == "force_next_career":
        character.forced_next_career_id = effect["career_id"]
        msgs.append(f"Forced next career: {effect['career_id']}")
        character.log(f"Mishap: forced into {effect['career_id']} next")

    elif etype == "d_associates":
        kind = effect["kind"]
        dice_str = effect["dice"]
        if dice_str == "D3":
            count = (dice.roll("1D").total + 1) // 2
        else:
            count = dice.roll(dice_str).total
        for _ in range(count):
            character.associates.append(
                Associate(kind=kind, description="")
            )
        msgs.append(f"Gained {count}× {kind.capitalize()}")
        character.log(f"Mishap: gained {count} {kind}(s)")

    elif etype == "pending_choice":
        if not character.pending_career_mishap_choice:
            choice_id = effect.get("id", "")
            pending = {
                "type": "pending_choice",
                "id": choice_id,
                "prompt": effect.get("prompt", ""),
                "options": list(effect.get("options", [])),
            }
            # Populate mishap_victim options from current contacts/allies
            if choice_id == "mishap_victim":
                opts = []
                for i, assoc in enumerate(character.associates):
                    if assoc.kind in ("contact", "ally"):
                        opts.append({
                            "id": str(i),
                            "label": f"{assoc.kind.capitalize()}: {assoc.description or '(unnamed)'}",
                            "associate_index": i,
                        })
                pending["options"] = opts
            character.pending_career_mishap_choice = pending
            set_pending = True

    elif etype == "skill_check":
        if not character.pending_career_mishap_choice:
            character.pending_career_mishap_choice = {
                "type": "skill_check",
                "skills": effect["skills"],
                "target": effect["target"],
                "on_nat2": effect.get("on_nat2", []),
                "on_fail": effect.get("on_fail", []),
                "on_pass": effect.get("on_pass", []),
                "prompt": f"Roll {'/' .join(s['name'] for s in effect['skills'])} {effect['target']}+",
            }
            set_pending = True

    elif etype == "frozen_watch":
        # ConfNav mishap 2 — character stays in service, no skill/advancement this term.
        if term is not None:
            term.frozen_watch = True
            term.survived = True  # override the failed survival: they're not leaving
            term.mishap = None    # clear the mishap marker — this isn't a career-ending event
        msgs.append("Frozen Watch — term spent in cryo. Character stays in service.")
        character.log("Mishap: Frozen Watch — term spent in cryoberth, character remains in service")

    elif etype == "rank_loss":
        amount = effect.get("amount", 1)
        if term is not None:
            old_rank = term.rank
            term.rank = max(0, term.rank - amount)
            msgs.append(f"Rank {old_rank}→{term.rank} (−{amount})")
            character.log(f"Mishap: rank reduced {old_rank}→{term.rank}")

    elif etype == "forfeit_benefit_unless_solsec_agent":
        # Navy/Army purge: SolSec Secret Agents gain Enemy instead; all others forfeit benefit
        if term is not None and term.career_id == "solsec":
            desc = "Enemy [Political Purge — cover blown]"
            character.associates.append(Associate(kind="enemy", description=desc))
            msgs.append(f"Gained Enemy: {desc}")
            character.log(f"Mishap: gained {desc} (SolSec Secret Agent exception)")
        else:
            if term is not None:
                term.benefit_forfeited = True
            msgs.append("This term's benefit roll forfeited")
            character.log("Mishap: benefit roll forfeited (political purge)")

    return msgs, set_pending


def mishap_roll(character: Character) -> dict:
    """Roll on the career's mishap table (1D) after a failed survival.

    Processes _MISHAP_EFFECTS for the career and auto-applies or sets pending
    choices for each effect. Returns structured result with all resolved data.
    """
    term = character.current_term
    if term is None:
        raise ValueError("No active term")
    career_id = term.career_id
    career = rules.careers()[career_id]
    mishaps = career.get("mishaps", {})
    r = dice.roll("1D")
    mishap_num = r.total
    mishap_text = mishaps.get(str(mishap_num), "(No mishap encoded — see rulebook or career JSON.)")

    term.mishap = mishap_text
    character.log(f"Mishap [1D={mishap_num}]: {mishap_text}")

    auto_applied: list[str] = []
    injury_data: Optional[dict] = None
    pending_choice = None
    pending_set = False

    effects = _MISHAP_EFFECTS.get(career_id, {}).get(mishap_num, [])

    for effect in effects:
        etype = effect["type"]

        if etype == "injury":
            if injury_data is None:
                injury_data = apply_injury(character)
            continue

        if etype in ("injury_severity_choice", "stat_choice", "skill_choice",
                     "pending_choice", "skill_check") and pending_set:
            # Only one pending at a time — skip further pending effects
            continue

        msgs, was_pending = _apply_mishap_effect(character, effect, term)
        auto_applied.extend(msgs)
        if was_pending:
            pending_set = True
            pending_choice = character.pending_career_mishap_choice

    return {
        "roll": r.to_dict(),
        "mishap_number": mishap_num,
        "mishap": mishap_text,
        "auto_applied": auto_applied,
        "pending_choice": pending_choice,
        "injury_pending": bool(character.pending_injury_choice),
        "injury_data": injury_data,
        "frozen_watch": bool(term and term.frozen_watch),
        "character": character.model_dump(),
    }


def resolve_career_mishap_choice(character: "Character", choice_data: dict) -> dict:
    """Resolve the active pending_career_mishap_choice on the character."""
    pending = character.pending_career_mishap_choice
    if not pending:
        raise ValueError("No pending career mishap choice to resolve.")

    ptype = pending["type"]
    auto_applied: list[str] = []
    injury_data: Optional[dict] = None
    term = character.current_term

    if ptype == "injury_severity_choice":
        choice = choice_data.get("choice", "result_2")
        if choice == "result_2":
            injury_data = _apply_injury_for_result(character, 2)
        else:  # roll_twice
            r1 = dice.roll("1D").total
            r2 = dice.roll("1D").total
            result = min(r1, r2)
            auto_applied.append(f"Rolled twice: {r1} and {r2} → took lower ({result})")
            injury_data = _apply_injury_for_result(character, result)

        # Check for chained "after" pending
        after = pending.get("after")
        character.pending_career_mishap_choice = after  # may be None

    elif ptype == "stat_choice":
        stat = choice_data["stat"]
        options = pending.get("options", [])
        if stat not in options:
            raise ValueError(f"'{stat}' not in options {options}")
        amount = pending.get("amount", -1)
        old = character.characteristics.get(stat)
        new_val = max(0, old + amount)
        character.characteristics.set(stat, new_val)
        auto_applied.append(f"{stat} {old}→{new_val} ({amount:+d})")
        character.log(f"Mishap stat choice: {stat} {old}→{new_val}")
        character.pending_career_mishap_choice = None

    elif ptype == "skill_choice":
        skill = choice_data["skill"]
        options = pending.get("options", [])
        if skill not in options:
            raise ValueError(f"'{skill}' not in options {options}")
        msg = character.add_skill(skill, level=1)
        auto_applied.append(msg)
        character.pending_career_mishap_choice = None

    elif ptype == "pending_choice":
        choice_id = pending.get("id", "")
        selected = choice_data.get("option_id", "")

        if choice_id == "mishap_deal":
            if selected == "accept":
                if term is not None:
                    term.benefit_forfeited = True
                auto_applied.append("Accepted deal — benefit roll forfeited")
                character.log("Mishap: accepted deal, benefit forfeited")
                character.pending_career_mishap_choice = None
            else:  # refuse
                character.associates.append(
                    Associate(
                        kind="enemy", description="Enemy [Criminal — refused deal]"
                    )
                )
                auto_applied.append("Refused deal — gained Enemy [Criminal — refused deal]")
                character.log("Mishap: refused deal, gained enemy")
                # Chain: injury_severity_choice → then free_skill_choice
                character.pending_career_mishap_choice = {
                    "type": "injury_severity_choice",
                    "after": {
                        "type": "free_skill_choice",
                        "prompt": "Gain one level in any skill of your choice",
                    },
                }

        elif choice_id == "army_join_cooperate":
            if selected == "join":
                character.associates.append(
                    Associate(
                        kind="ally", description="Ally [Corrupt CO]"
                    )
                )
                auto_applied.append("Joined ring — gained Ally [Corrupt CO]")
                character.log("Mishap: joined CO ring, gained ally")
            else:  # cooperate
                auto_applied.append("Co-operated with military police — benefit roll kept")
                character.log("Mishap: co-operated with military police")
            character.pending_career_mishap_choice = None

        elif choice_id == "mishap_victim":
            # "skip" is sent when there are no contacts/allies to target
            if selected == "skip":
                auto_applied.append("No contacts/allies available — victim effect skipped")
                character.pending_career_mishap_choice = None
            else:
                idx = choice_data.get("associate_index")
                if idx is None:
                    raise ValueError("associate_index required for mishap_victim choice")
                idx = int(idx)
                if idx < 0 or idx >= len(character.associates):
                    raise ValueError(f"associate_index {idx} out of range")
                assoc = character.associates[idx]
                old_kind = assoc.kind
                assoc.kind = "rival"
                assoc.description = f"Injured — {assoc.description}"
                auto_applied.append(f"{old_kind.capitalize()} → Rival (injured): {assoc.description}")
                character.log(f"Mishap victim: associate {idx} converted to rival")
                character.pending_career_mishap_choice = None

        elif choice_id == "solsec_blame":
            if selected == "pin":
                character.associates.append(
                    Associate(kind="rival", description="Rival [Blamed Colleague]")
                )
                auto_applied.append("Pinned blame on colleague — Rival [Blamed Colleague] gained. Benefit roll kept.")
                character.log("Mishap: pinned blame on colleague, gained rival, kept benefit")
            else:  # fall
                if term is not None:
                    term.benefit_forfeited = True
                auto_applied.append("Took the fall — benefit roll forfeited")
                character.log("Mishap: took the fall, benefit forfeited")
            character.pending_career_mishap_choice = None

        elif choice_id == "solsec_expose":
            if selected == "expose":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Exposed Traitor]")
                )
                auto_applied.append("Exposed the traitor — Enemy [Exposed Traitor] gained. Benefit roll kept.")
                character.log("Mishap: exposed traitor, gained enemy, kept benefit")
            else:  # quiet
                if term is not None:
                    term.benefit_forfeited = True
                auto_applied.append("Stayed quiet — benefit roll forfeited")
                character.log("Mishap: stayed quiet, benefit forfeited")
            character.pending_career_mishap_choice = None

        elif choice_id == "party_denounce":
            if selected == "denounce":
                msg = character.add_skill("Advocate", level=1)
                auto_applied.append(msg)
                soc_old = character.characteristics.SOC
                character.characteristics.set("SOC", max(0, soc_old - 1))
                auto_applied.append(f"SOC {soc_old}→{max(0, soc_old - 1)} (−1)")
                auto_applied.append("Denounced patron — Advocate+1, SOC−1. Benefit roll kept.")
                character.log("Mishap: denounced patron, Advocate+1, SOC-1, kept benefit")
            else:  # silent
                if term is not None:
                    term.benefit_forfeited = True
                auto_applied.append("Stayed silent — benefit roll forfeited")
                character.log("Mishap: stayed silent, benefit forfeited")
            character.pending_career_mishap_choice = None

        elif choice_id == "solsec_interrogation":
            if selected == "submit":
                if term is not None:
                    term.benefit_forfeited = True
                auto_applied.append("Submitted to SolSec interrogation — benefit roll forfeited")
                character.log("Mishap: submitted to interrogation, benefit forfeited")
                character.pending_career_mishap_choice = None
            else:  # refuse — chain into END 8+ skill check
                auto_applied.append("Refused interrogation — must now roll END 8+")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "END", "is_stat": True}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [],
                    "on_fail": [{"type": "forfeit_benefit"}],
                    "prompt": "Refused SolSec interrogation — roll END 8+ to keep your Benefit roll",
                }

        else:
            raise ValueError(f"Unknown pending_choice id: '{choice_id}'")

    elif ptype == "skill_check":
        skill_name = choice_data.get("skill_name", "")
        skills_list = pending.get("skills", [])
        target = pending.get("target", 8)
        on_nat2 = pending.get("on_nat2", [])
        on_fail = pending.get("on_fail", [])
        on_pass = pending.get("on_pass", [])

        # Determine DM from the skill on the character
        skill_dm = 0
        is_stat = any(s.get("is_stat") and s["name"] == skill_name for s in skills_list)
        if is_stat:
            val = character.characteristics.get(skill_name)
            skill_dm = (val - 1) // 3 - 1  # rough DM calculation
        else:
            for s in character.skills:
                if s.name == skill_name and s.speciality is None:
                    skill_dm = s.level
                    break

        r2d = dice.roll("2D", modifier=skill_dm)
        raw_total = r2d.total - skill_dm  # raw 2D before DM
        total_with_dm = r2d.total
        passed = total_with_dm >= target
        nat2 = raw_total == 2

        auto_applied.append(
            f"Skill check {skill_name} {target}+: rolled 2D={raw_total}, DM{skill_dm:+d} = {total_with_dm} → {'PASS' if passed else 'FAIL'}"
        )
        character.log(f"Mishap skill check ({skill_name}): {total_with_dm} vs {target}+ — {'pass' if passed else 'fail'}")

        # Apply consequences
        consequences = on_nat2 if nat2 else (on_pass if passed else on_fail)
        for sub_effect in consequences:
            msgs, was_pending = _apply_mishap_effect(character, sub_effect, term)
            auto_applied.extend(msgs)

        character.pending_career_mishap_choice = None

        return {
            "auto_applied": auto_applied,
            "skill_check": {
                "skill": skill_name,
                "roll": r2d.to_dict(),
                "raw_2d": raw_total,
                "dm": skill_dm,
                "total": total_with_dm,
                "target": target,
                "passed": passed,
                "nat2": nat2,
            },
            "injury_pending": bool(character.pending_injury_choice),
            "injury_data": injury_data,
            "character": character.model_dump(),
        }

    elif ptype == "free_skill_choice":
        skill = choice_data.get("skill", "")
        if not skill:
            raise ValueError("skill is required for free_skill_choice")
        msg = character.add_skill(skill, level=1)
        auto_applied.append(msg)
        character.log(f"Mishap free skill choice: {skill}")
        character.pending_career_mishap_choice = None

    else:
        raise ValueError(f"Unknown pending mishap choice type: '{ptype}'")

    return {
        "auto_applied": auto_applied,
        "injury_pending": bool(character.pending_injury_choice),
        "injury_data": injury_data,
        "character": character.model_dump(),
    }


def cross_career_event_or_mishap(character: "Character", career_id: str, table: str) -> dict:
    """Roll on another career's event or mishap table WITHOUT modifying character state.

    Used for agent event 8 (roll on Rogue or Citizen table).
    """
    all_careers = rules.careers()
    if career_id not in all_careers:
        raise ValueError(f"Unknown career_id: '{career_id}'")
    career = all_careers[career_id]
    career_name = career.get("name", career_id)

    if table == "event":
        events = career.get("events", {})
        r = dice.roll("2D")
        text = events.get(str(r.total), "(No event encoded for this roll.)")
        return {
            "roll": r.to_dict(),
            "career_name": career_name,
            "table": "event",
            "text": text,
            "character": character.model_dump(),
        }
    elif table == "mishap":
        mishaps = career.get("mishaps", {})
        r = dice.roll("1D")
        text = mishaps.get(str(r.total), "(No mishap encoded for this roll.)")
        return {
            "roll": r.to_dict(),
            "career_name": career_name,
            "table": "mishap",
            "text": text,
            "character": character.model_dump(),
        }
    else:
        raise ValueError(f"Unknown table: '{table}'. Must be 'event' or 'mishap'.")


def ban_career(character: "Character", career_id: str) -> dict:
    """Permanently ban a career from re-entry (e.g. Scout event 2 failure)."""
    if career_id not in character.banned_career_ids:
        character.banned_career_ids.append(career_id)
        character.log(f"Career '{career_id}' banned from re-entry.")
    return {"banned": career_id, "character": character.model_dump()}


def advancement_roll(character: Character) -> dict:
    """Roll advancement. On success, rank increases.

    For SolSec Secret Agents the roll uses the cover career's advancement
    characteristic and target with DM+1 (the cover identity opens doors).
    SolSec rank advancement always follows SolSec's own rank table regardless.
    """
    term = character.current_term
    if term is None:
        raise ValueError("No active term")

    career = rules.careers()[term.career_id]

    cover_note = ""
    if term.cover_career_id:
        # Secret Agent: use cover career advancement DM+1
        cover_career = rules.careers().get(term.cover_career_id, {})
        cover_assignment_id = list(cover_career.get("assignments", {}).keys())[0]
        cover_asgn = cover_career["assignments"][cover_assignment_id]
        adv = cover_asgn["advancement"]
        cover_dm = 1
        cover_note = f" [Cover: {cover_career.get('name', term.cover_career_id)}, DM+1]"
    else:
        assignment = career["assignments"][term.assignment_id]
        adv = assignment["advancement"]
        cover_dm = 0

    char_key = adv["characteristic"]
    target = adv["target"]
    dm = dice.characteristic_dm(character.characteristics.get(char_key)) + cover_dm

    # Apply permanent pre-career advancement DMs
    pdms = character.pre_career_permanent_dms or {}
    adv_dm_careers = list(pdms.get("advancement_dm_careers", []))
    if adv_dm_careers and term.career_id in adv_dm_careers:
        dm += int(pdms.get("advancement_dm", 0))
    # Spacer community: +N to advancement in specific career/assignment
    if (pdms.get("spacer_career_dm")
            and term.career_id == pdms.get("spacer_career_id")
            and term.assignment_id == pdms.get("spacer_assignment_id")):
        dm += int(pdms["spacer_career_dm"])
    # School of Hard Knocks: -2 advancement in first career only
    if pdms.get("first_career_commission_dm") and len(character.completed_careers) == 0:
        dm += int(pdms["first_career_commission_dm"])

    dm += character.dm_next_advancement
    pending = character.dm_next_advancement
    character.dm_next_advancement = 0

    # SolSec Monitor: DM+1 to advancement in any career except Drifter
    monitor_dm = 0
    if character.solsec_monitor and term.career_id != "drifter":
        monitor_dm = 1
        dm += monitor_dm

    r = dice.roll("2D", modifier=dm, target=target)
    term.advanced = bool(r.succeeded)

    monitor_rank_up = False
    if r.succeeded:
        term.rank += 1
        term.rank_title = _rank_title(career, term.assignment_id, term.rank)
        rank_data = _rank_data(career, term.assignment_id, term.rank)
        if rank_data and rank_data.get("bonus"):
            bonus = rank_data["bonus"]
            rank_bonus_log = _apply_rank_bonus(character, bonus)
            term.skills_gained.append(f"Rank bonus: {bonus}")
            character.log(f"  Rank bonus: {rank_bonus_log}")
        # Monitor rank goes up by 1 whenever promoted in career (max 6)
        if character.solsec_monitor and character.solsec_monitor_rank < 6:
            character.solsec_monitor_rank += 1
            monitor_rank_up = True
            character.log(
                f"SolSec Monitor rank increased to {character.solsec_monitor_rank}."
                + (
                    " (Rank 3+: earns one extra Benefit roll at muster-out.)"
                    if character.solsec_monitor_rank == 3
                    else ""
                )
            )

    monitor_note = f" [Monitor DM+{monitor_dm}]" if monitor_dm else ""
    msg = (
        f"Advancement ({char_key} {target}+{'+' + str(pending) if pending else ''}){cover_note}{monitor_note}: "
        f"2D{dm:+d} = {r.total} "
        f"[{'PROMOTED to rank ' + str(term.rank) + (' — ' + term.rank_title if term.rank_title else '') if r.succeeded else 'no promotion'}]"
    )
    character.log(msg)
    return {
        "roll": r.to_dict(),
        "advanced": r.succeeded,
        "new_rank": term.rank,
        "new_rank_title": term.rank_title,
        "monitor_dm": monitor_dm,
        "monitor_rank_up": monitor_rank_up,
        "monitor_rank": character.solsec_monitor_rank,
        "character": character.model_dump(),
    }


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


# ============================================================
# Anagathics — life extension (Core Rulebook p.155)
# ============================================================
#
# RAW rules (MG2e p.47):
#   • At the START of any career term: roll SOC 10+ to obtain supply.
#     Natural 2 on the SOC roll → must take Prisoner career this term.
#   • While active: add anagathics_terms_used as a POSITIVE DM to aging rolls.
#   • Two survival checks required each term; if either fails → Mishap.
#   • Cost: 1D × Cr25,000 per term, paid from cash benefits (else medical debt).
#   • Stopping: immediately roll on the Aging table.


def attempt_anagathics(character: "Character") -> dict:
    """Roll SOC 10+ to access anagathics at the start of a career term.

    May be called when character.total_terms >= 3 (i.e. this term would be
    the 4th or later, when aging kicks in).

    Returns:
        roll          – the SOC roll result
        succeeded     – True if SOC 10+ passed
        nat2_prison   – True if natural 2 was rolled (forced into Prisoner)
        already_active– True if anagathics were already active (auto-continue)
        cost_this_term– Cr cost rolled for this term (0 if failed/nat2)
        character     – updated character dict
    """
    if character.phase != "career":
        raise ValueError("Anagathics can only be attempted during the career phase.")

    # If already active this term can be continued automatically — this call
    # handles the START-of-term check for both new and continuing users.
    already_active = character.anagathics_active

    soc = character.characteristics.get("SOC", 0)
    dm = dice.characteristic_dm(soc)
    r = dice.roll("2D", modifier=dm, target=10)

    nat2_prison = r.raw_total == 2
    succeeded = r.succeeded and not nat2_prison

    cost_this_term = 0
    if nat2_prison:
        # Natural 2 → immediately forced into Prisoner career this term.
        character.forced_next_career_id = "prisoner"
        character.anagathics_active = False
        character.log(
            f"Anagathics access roll SOC [2D{dm:+d}={r.total}]: "
            "NATURAL 2 — must take Prisoner career this term!"
        )
    elif succeeded:
        # Roll cost: 1D × Cr25,000; paid at end of term (medical debt if broke).
        cost_die = dice.roll("1D")
        cost_this_term = cost_die.total * 25000
        character.anagathics_active = True
        character.anagathics_pending_cost += cost_this_term
        character.log(
            f"Anagathics access roll SOC [2D{dm:+d}={r.total}]: SUCCESS. "
            f"Treatment secured. Cost this term: Cr{cost_this_term:,} "
            f"(1D={cost_die.total} × Cr25,000). Paid at end of term."
        )
    else:
        # Failed roll — cannot obtain supply this term.
        character.anagathics_active = False
        character.log(
            f"Anagathics access roll SOC [2D{dm:+d}={r.total}]: FAILED "
            f"(need 10+). Unable to obtain a supply this term."
        )

    return {
        "roll": r.to_dict(),
        "succeeded": succeeded,
        "nat2_prison": nat2_prison,
        "already_active": already_active,
        "cost_this_term": cost_this_term,
        "character": character.model_dump(),
    }


def stop_anagathics(character: "Character") -> dict:
    """Stop taking anagathics voluntarily.

    Per RAW, stopping triggers an IMMEDIATE aging roll as the body
    begins to age again (shock to the system).
    """
    if not character.anagathics_active:
        raise ValueError("Character is not currently using anagathics.")

    character.anagathics_active = False
    character.log(
        "Anagathics stopped. Rolling immediately on Aging table — "
        "the body begins to age again."
    )

    # Apply aging roll immediately (no anagathics DM — they just stopped).
    # We temporarily zero out anagathics_terms_used so the positive DM isn't applied.
    saved_terms = character.anagathics_terms_used
    character.anagathics_terms_used = 0
    aging_result = _apply_aging(character)
    character.anagathics_terms_used = saved_terms  # restore for record-keeping

    return {
        "aging": aging_result,
        "character": character.model_dump(),
    }


# ============================================================
# Home Forces Reserves (Solomani parallel service)
# ============================================================

# Careers that bar Home Forces enrollment
_HOME_FORCES_BARRED_CAREERS = frozenset({"drifter"})
# Rogue pirate assignment is also barred (checked separately)
# Naval component: Merchant marine / free trader assignments, or ex-Navy
_NAVAL_MERCHANT_ASSIGNMENTS = frozenset({"merchant_marine", "free_trader"})

# Reserves Training table (1D)
_HOME_FORCES_TRAINING: dict[str, dict[int, str]] = {
    "groundside": {
        1: "Gun Combat (any) 1 or Heavy Weapons (any) 1",
        2: "Mechanic 1",
        3: "Drive (any) 1 or Flyer (any) 1 or Seafarer (any) 1",
        4: "Electronics (any) 1",
        5: "Recon 1 or Survival 1",
        6: "Leadership 1 or Tactics (military) 1",
    },
    "naval": {
        1: "Gunner (any) 1",
        2: "Engineer (any) 1",
        3: "Pilot (any) 1",
        4: "Electronics (any) 1",
        5: "Vacc Suit 1",
        6: "Leadership 1 or Tactics (naval) 1",
    },
}


def _home_forces_component_for(character: "Character") -> str:
    """Return 'naval' or 'groundside' based on current career/assignment and history."""
    term = character.current_term
    if term and term.career_id == "merchant" and term.assignment_id in _NAVAL_MERCHANT_ASSIGNMENTS:
        return "naval"
    # Ex-Navy (any previous Navy career) may join naval component
    navy_career_ids = {"navy", "confederation_navy"}
    has_navy = any(c.career_id in navy_career_ids for c in character.completed_careers)
    if has_navy:
        return "naval"
    return "groundside"


def _home_forces_eligible(character: "Character") -> bool:
    """Return True if the character may (re-)enroll in Home Forces Reserves."""
    if character.society_id != "solomani_confederation":
        return False
    term = character.current_term
    if term is None:
        return False
    if term.career_id in _HOME_FORCES_BARRED_CAREERS:
        return False
    if term.career_id == "rogue" and term.assignment_id == "pirate":
        return False
    # SolSec field_agent and secret_agent cannot join (they're military/intelligence)
    if term.career_id == "solsec":
        return False
    return True


def enroll_home_forces(character: "Character") -> dict:
    """Enroll the character in Home Forces Reserves and roll on the training table.

    Eligibility is checked here; raises ValueError if ineligible.
    The training roll is made once at initial enlistment only.
    """
    if character.phase != "career":
        raise ValueError("Home Forces enrollment is only available during the career phase.")
    if not _home_forces_eligible(character):
        raise ValueError("This character is not eligible for Home Forces Reserves.")

    component = _home_forces_component_for(character)
    character.home_forces_enrolled = True
    character.home_forces_component = component
    character.home_forces_trained = True

    # Auto-skill: Gun Combat 0 (groundside) or Vacc Suit 0 (naval)
    auto_skill = "Gun Combat" if component == "groundside" else "Vacc Suit"
    auto_log = character.add_skill(auto_skill, level=0)

    # Transfer military rank from a previous Army/Marine/Navy career
    rank_transferred = 0
    military_careers = {"army", "marine", "navy", "confederation_army", "solomani_marine", "confederation_navy"}
    for cc in reversed(character.completed_careers):
        if cc.career_id in military_careers:
            rank_transferred = cc.final_rank
            break
    if rank_transferred:
        character.home_forces_rank = rank_transferred
        character.log(
            f"Home Forces Reserves ({component}): transferred military rank {rank_transferred}."
        )

    # Training roll
    r = dice.roll("1D")
    training_table = _HOME_FORCES_TRAINING[component]
    training_result = training_table[r.total]
    character.log(
        f"Home Forces Reserves ({component}) enrolled. "
        f"Training roll [1D={r.total}]: {training_result}. "
        f"Auto-skill: {auto_log}."
    )

    return {
        "component": component,
        "auto_skill": auto_skill,
        "training_roll": r.to_dict(),
        "training_result": training_result,
        "rank_transferred": rank_transferred,
        "character": character.model_dump(),
    }


def leave_home_forces(character: "Character") -> dict:
    """Resign from Home Forces Reserves (effective next term)."""
    character.home_forces_enrolled = False
    character.log("Resigned from Home Forces Reserves.")
    return {"character": character.model_dump()}


# ============================================================
# SolSec Monitor (Solomani informer, parallel to any non-SolSec career)
# ============================================================

def _solsec_monitor_eligible(character: "Character") -> bool:
    if character.society_id != "solomani_confederation":
        return False
    term = character.current_term
    if term and term.career_id == "solsec":
        return False
    return True


def toggle_solsec_monitor(character: "Character", active: bool) -> dict:
    """Opt in or out of the SolSec Monitor role."""
    if active and not _solsec_monitor_eligible(character):
        raise ValueError("Not eligible to become a SolSec Monitor (must be non-SolSec, Solomani society).")
    character.solsec_monitor = active
    action = "Enrolled as" if active else "Resigned from"
    character.log(f"{action} SolSec Monitor.")
    return {
        "solsec_monitor": character.solsec_monitor,
        "solsec_monitor_rank": character.solsec_monitor_rank,
        "character": character.model_dump(),
    }


# ============================================================
# Mishap effects table
# ============================================================

_MISHAP_EFFECTS: dict[str, dict[int, list[dict]]] = {
    "agent": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "pending_choice", "id": "mishap_deal",
             "prompt": "A criminal offers you a deal to leave without penalty, or you can refuse.",
             "options": [
                 {"id": "accept", "label": "Accept — leave without penalty (lose this term's benefit roll)"},
                 {"id": "refuse", "label": "Refuse — injury ×2 lower, gain Enemy, gain any skill +1"},
             ]}],
        3: [{"type": "skill_check", "skills": [{"name": "Advocate"}], "target": 8,
             "on_nat2": [{"type": "force_next_career", "career_id": "prisoner"}],
             "on_fail": [{"type": "forfeit_benefit"}],
             "on_pass": []}],
        4: [{"type": "enemy", "desc": "Enemy [Investigation Target]"}, {"type": "skill", "name": "Deception", "level": 1}],
        5: [{"type": "pending_choice", "id": "mishap_victim",
             "prompt": "Choose which Contact or Ally gets hurt. They will become a Rival.",
             "options": []}],  # populated dynamically
        6: [{"type": "injury"}],
    },
    "army": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "enemy", "desc": "Enemy [Commander]"}],
        3: [{"type": "enemy", "desc": "Enemy [Rebels]"}, {"type": "skill_choice", "options": ["Recon", "Survival"]}],
        4: [{"type": "pending_choice", "id": "army_join_cooperate",
             "prompt": "Your CO is engaged in illegal activity. What do you do?",
             "options": [
                 {"id": "join", "label": "Join their ring — gain them as an Ally (still get discharged later)"},
                 {"id": "cooperate", "label": "Co-operate with military police — keep your Benefit roll (still discharged)"},
             ]}],
        5: [{"type": "rival", "desc": "Rival [Officer]"}],
        6: [{"type": "injury"}],
    },
    "citizen": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "rival", "desc": "Rival [Co-worker/Company]"}],
        3: [{"type": "stat_choice", "options": ["INT", "SOC"], "amount": -1}],
        4: [{"type": "forfeit_benefit"}],
        5: [{"type": "enemy", "desc": "Enemy [Co-worker/Customer]"}],
        6: [{"type": "injury"}],
    },
    "drifter": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "enemy", "desc": "Enemy [Kidnapper]"}],
        3: [{"type": "stat_choice", "options": ["STR", "DEX", "END"], "amount": -1}],
        4: [{"type": "rival", "desc": "Rival [Local Criminals/Police]"}],
        5: [{"type": "forfeit_benefit"}],
        6: [{"type": "injury"}],
    },
    "entertainer": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1}, {"type": "rival", "desc": "Rival [Scandal]"}],
        3: [{"type": "enemy", "desc": "Enemy [Patron/Critic/Sponsor]"}, {"type": "forfeit_benefit"}],
        4: [],  # blacklisted — narrative
        5: [{"type": "stat_choice", "options": ["STR", "DEX", "END", "INT", "EDU"], "amount": -1}],
        6: [{"type": "injury"}],
    },
    "marine": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "enemy", "desc": "Enemy [Disaster Engagement]"}, {"type": "skill", "name": "Gun Combat", "level": 1}],
        3: [{"type": "stat_choice", "options": ["INT", "SOC"], "amount": -1}],
        4: [{"type": "contact", "desc": "Contact [Fellow Prisoner]"}, {"type": "enemy", "desc": "Enemy [Captors]"}],
        5: [{"type": "rival", "desc": "Rival [Commander]"}],
        6: [{"type": "injury"}],
    },
    "merchant": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "enemy", "desc": "Enemy [Pirates/Corsairs]"}, {"type": "forfeit_benefit"}],
        3: [{"type": "forfeit_benefit"}],
        4: [{"type": "rival", "desc": "Rival [Political/Legal Dispute]"}],
        5: [{"type": "forfeit_benefit"}],
        6: [{"type": "injury"}],
    },
    "navy": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "contact", "desc": "Contact [Fellow Survivor]"}],
        3: [{"type": "rival", "desc": "Rival [Service Member]"}],
        4: [],  # court-martialled — narrative
        5: [{"type": "enemy", "desc": "Enemy [Admiralty]"}],
        6: [{"type": "injury"}],
    },
    "noble": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "skill_check", "skills": [{"name": "Stealth"}, {"name": "Deception"}], "target": 8,
             "on_fail": [{"type": "injury"}], "on_pass": []}],
        4: [{"type": "skill_choice", "options": ["Diplomat", "Advocate"]}, {"type": "rival", "desc": "Rival [Political Maneuverer]"}],
        5: [{"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_fail": [{"type": "injury"}], "on_pass": []}],
        6: [{"type": "injury"}],
    },
    "prisoner": {
        1: [{"type": "injury"}],  # no "twice" option — prisoner mishap 1 is just injury
        2: [{"type": "enemy", "desc": "Enemy [Gang Leader/Guard/Prisoner]"}],
        3: [{"type": "forfeit_benefit"}, {"type": "skill", "name": "Streetwise", "level": 1}],
        4: [{"type": "stat", "stat": "END", "amount": -1}, {"type": "debt", "amount": 20000}],
        5: [{"type": "enemy", "desc": "Enemy [Witness/Participant]"}, {"type": "skill", "name": "Deception", "level": 1}],
        6: [{"type": "injury"}],
    },
    "rogue": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "force_next_career", "career_id": "prisoner"}, {"type": "forfeit_benefit"}],
        3: [{"type": "enemy", "desc": "Enemy [Crime Job]"}, {"type": "forfeit_benefit"}],
        4: [{"type": "enemy", "desc": "Enemy [Partner in Crime]"}],
        5: [],  # forced to flee — narrative
        6: [{"type": "injury"}],
    },
    "scholar": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat_choice", "options": ["STR", "DEX", "END"], "amount": -1}, {"type": "forfeit_benefit"}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1}, {"type": "rival", "desc": "Rival [Academic/Research]"}],
        4: [{"type": "enemy", "desc": "Enemy [Subject/Colleague Family]"}],
        5: [],  # funding pulled — narrative
        6: [{"type": "injury"}],
    },
    "scout": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat_choice", "options": ["INT", "SOC"], "amount": -1}],
        3: [{"type": "d_associates", "kind": "contact", "dice": "1D"}, {"type": "d_associates", "kind": "enemy", "dice": "D3"}],
        4: [{"type": "rival", "desc": "Rival [Minor World/Race]"}, {"type": "skill", "name": "Diplomat", "level": 1}],
        5: [],  # narrative only
        6: [{"type": "injury"}],
    },
    # ---- Solomani Confederation careers ----
    "solsec": {
        1: [{"type": "injury"}],
        2: [{"type": "force_next_career", "career_id": "prisoner"}, {"type": "forfeit_benefit"}],
        3: [{"type": "enemy", "desc": "Enemy [SolSec Officer]"}],
        4: [{"type": "rank_loss", "amount": 1},
            {"type": "pending_choice", "id": "solsec_blame",
             "prompt": "SolSec disavows you — you've lost one rank. You can pin the blame on a colleague (keep Benefit roll, gain Rival) or take the fall (forfeit Benefit roll).",
             "options": [
                 {"id": "pin", "label": "Pin blame on a colleague — keep Benefit roll, gain Rival"},
                 {"id": "fall", "label": "Take the fall — forfeit Benefit roll"},
             ]}],
        5: [{"type": "pending_choice", "id": "solsec_expose",
             "prompt": "You may expose the traitor who burned your network (keep Benefit roll, gain Enemy) or stay quiet (forfeit Benefit roll).",
             "options": [
                 {"id": "expose", "label": "Expose the traitor — keep Benefit roll, gain Enemy"},
                 {"id": "quiet", "label": "Stay quiet — forfeit Benefit roll"},
             ]}],
        6: [{"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_pass": [], "on_fail": [{"type": "forfeit_benefit"}]}],
    },
    "party": {
        1: [{"type": "injury"}],
        2: [],  # Denounced — career ends; no additional mechanical effect beyond narrative
        3: [],  # Disillusioned — no mechanical effect in the Party context; Drifter clause applies if next career is Drifter
        4: [{"type": "pending_choice", "id": "party_denounce",
             "prompt": "Your patron has fallen from favour and taken you with them. Denounce them (Advocate+1, SOC−1, keep Benefit roll) or stay silent (forfeit Benefit roll)?",
             "options": [
                 {"id": "denounce", "label": "Denounce patron — Advocate+1, SOC−1, keep Benefit roll"},
                 {"id": "silent", "label": "Stay silent — forfeit Benefit roll"},
             ]}],
        5: [{"type": "stat", "stat": "SOC", "amount": -1}],  # tainted by association (Ally gain is optional/narrative)
        6: [{"type": "force_next_career", "career_id": "prisoner"}, {"type": "forfeit_benefit"}],
    },
    "confederation_navy": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "frozen_watch"}],
        3: [{"type": "pending_choice", "id": "solsec_interrogation",
             "prompt": "You are forced out after criticising a political officer. Submit to SolSec interrogation (forfeit Benefit roll) or refuse and roll END 8+ to keep your Benefit roll?",
             "options": [
                 {"id": "submit", "label": "Submit to interrogation — forfeit Benefit roll"},
                 {"id": "refuse", "label": "Refuse — roll END 8+ to keep Benefit roll"},
             ]}],
        4: [{"type": "skill_check",
             "skills": [{"name": "Electronics"}, {"name": "Gunner"},
                        {"name": "Pilot"}, {"name": "Tactics"}],
             "target": 8, "on_pass": [], "on_fail": [{"type": "forfeit_benefit"}]}],
        5: [{"type": "forfeit_benefit_unless_solsec_agent"}],
        6: [{"type": "injury"}],
    },
    "confederation_army": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "enemy", "desc": "Enemy [Political Officer]"}],
        3: [{"type": "pending_choice", "id": "solsec_interrogation",
             "prompt": "You are court-martialled on political grounds. Submit to SolSec interrogation (forfeit Benefit roll) or refuse and roll END 8+ to keep your Benefit roll?",
             "options": [
                 {"id": "submit", "label": "Submit to interrogation — forfeit Benefit roll"},
                 {"id": "refuse", "label": "Refuse — roll END 8+ to keep Benefit roll"},
             ]}],
        4: [{"type": "pending_choice", "id": "army_join_cooperate",
             "prompt": "Your CO is engaged in illegal activities. What do you do?",
             "options": [
                 {"id": "join", "label": "Join their ring — gain them as an Ally (still discharged)"},
                 {"id": "cooperate", "label": "Co-operate with authorities — keep your Benefit roll (still discharged)"},
             ]}],
        5: [{"type": "rival", "desc": "Rival [Political Officer]"}],
        6: [{"type": "injury"}],
    },
    "solomani_marine": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "enemy", "desc": "Enemy [Enemy Forces]"},
            {"type": "free_skill_choice", "prompt": "Stranded behind enemy lines — gain any skill at level 1."}],
        3: [{"type": "stat_choice", "options": ["INT", "SOC"], "amount": -1}],
        4: [{"type": "contact", "desc": "Contact [Fellow Prisoner]"}, {"type": "enemy", "desc": "Enemy [Captors]"}],
        5: [{"type": "rival", "desc": "Rival [Commander]"}],
        6: [{"type": "injury"}],
    },
}


# ============================================================
# Injury resolution (1D) — medical bills land here
# ============================================================

# Shared choices descriptor used by both apply_injury and _apply_injury_for_result.
def _build_injury_choices(total: int, damage_roll: Optional[int]) -> dict:
    _choices: dict[int, dict] = {
        1: {
            "damage_to_chosen": damage_roll,
            "auto_reduce_others": 2,
            "choices": ["STR", "DEX", "END"],
            "prompt": (
                f"Choose one physical stat to take {damage_roll} damage. "
                f"The other two each automatically take 2 damage."
            ),
        },
        2: {
            "damage_to_chosen": damage_roll,
            "auto_reduce_others": 0,
            "choices": ["STR", "DEX", "END"],
            "prompt": f"Choose which physical stat takes {damage_roll} damage.",
        },
        3: {
            "damage_to_chosen": 2,
            "auto_reduce_others": 0,
            "choices": ["STR", "DEX"],
            "prompt": "Missing Eye or Limb — choose STR or DEX to lose 2 points.",
        },
        4: {
            "damage_to_chosen": 2,
            "auto_reduce_others": 0,
            "choices": ["STR", "DEX", "END"],
            "prompt": "Scarred — choose any physical stat to lose 2 points.",
        },
        5: {
            "damage_to_chosen": 1,
            "auto_reduce_others": 0,
            "choices": ["STR", "DEX", "END"],
            "prompt": "Injured — choose any physical stat to lose 1 point.",
        },
    }
    return _choices[total]


def _apply_injury_for_result(character: "Character", result: int) -> dict:
    """Apply injury for a *specific* result (1–6) without rolling.

    Result 6 auto-resolves immediately. Results 1–5 pre-roll damage dice
    if needed and set character.pending_injury_choice.
    Returns the same shape as apply_injury.
    """
    data = rules.injury_table()
    entry = data["entries"].get(str(result))
    if entry is None:
        raise ValueError(f"No injury entry for result {result}")

    title = entry["title"]
    text = entry["text"]

    if result == 6:
        character.log(f"Injury [result=6]: {title} — no permanent effect.")
        return {
            "roll": {"total": 6, "dice": [6], "modifier": 0},
            "title": title,
            "text": text,
            "pending_choice": None,
            "result_text": title,
            "character": character.model_dump(),
        }

    damage_roll: Optional[int] = None
    if result in (1, 2):
        damage_roll = dice.roll("1D").total

    choice_data = _build_injury_choices(result, damage_roll)
    pending = {
        "roll": result,
        "title": title,
        **choice_data,
    }
    character.pending_injury_choice = pending
    character.log(
        f"Injury [result={result}]: {title} — player must choose stat to absorb damage."
    )
    return {
        "roll": {"total": result, "dice": [result], "modifier": 0},
        "title": title,
        "text": text,
        "pending_choice": pending,
        "result_text": title,
        "character": character.model_dump(),
    }


def apply_injury(character: "Character") -> dict:
    """Roll 1D on the Injury table.

    Result 6 is resolved immediately (no stat loss). Results 1–5 require the
    player to choose which physical characteristic absorbs the damage, so they
    set character.pending_injury_choice and return without modifying stats.
    Call resolve_injury_choice() once the player has decided.

    Medical debt (Cr 5,000 per point lost) is calculated and added when
    resolve_injury_choice() runs.
    """
    r = dice.roll("1D")
    result = _apply_injury_for_result(character, r.total)
    # Override the roll dict with the actual dice roll object
    result["roll"] = r.to_dict()
    return result


def resolve_injury_choice(character: "Character", chosen_stat: str) -> dict:
    """Apply the player's injury stat choice.

    Reduces chosen_stat by damage_to_chosen, then reduces the other
    physical stats by auto_reduce_others each (for result 1).
    Adds Cr 5,000 per point lost as medical debt.
    """
    pending = character.pending_injury_choice
    if not pending:
        raise ValueError("No pending injury choice to resolve.")

    choices = pending.get("choices", [])
    if chosen_stat not in choices:
        raise ValueError(
            f"'{chosen_stat}' is not a valid choice. Options: {choices}"
        )

    physical = ["STR", "DEX", "END"]
    total_loss = 0
    applied: list[str] = []

    # Primary stat damage.
    amount = pending["damage_to_chosen"]
    old = character.characteristics.get(chosen_stat)
    new_val = max(0, old - amount)
    character.characteristics.set(chosen_stat, new_val)
    actual_loss = old - new_val
    total_loss += actual_loss
    applied.append(f"{chosen_stat} {old}→{new_val} (-{actual_loss})")

    # Secondary auto-reduce (result 1 only: other two stats each lose 2).
    auto = pending.get("auto_reduce_others", 0)
    if auto > 0:
        others = [s for s in physical if s != chosen_stat]
        for stat in others:
            old_v = character.characteristics.get(stat)
            new_v = max(0, old_v - auto)
            character.characteristics.set(stat, new_v)
            loss = old_v - new_v
            total_loss += loss
            applied.append(f"{stat} {old_v}→{new_v} (-{loss})")

    # Medical debt: Cr 5,000 per point lost.
    gross_debt = total_loss * 5000
    medical_bills_info: dict | None = None
    if gross_debt > 0:
        # Roll 2D + Rank to see how much the career covers.
        medical_bills_info = _medical_bills_roll(character, gross_debt)
        net_debt = medical_bills_info["remaining"]
        covered = medical_bills_info["covered"]
        character.medical_debt += net_debt
        applied.append(
            f"Medical bills: Cr{gross_debt:,} gross "
            f"(career covers {medical_bills_info['coverage_pct']}% = Cr{covered:,}; "
            f"Cr{net_debt:,} owed)"
        )
        character.log(
            f"Medical bills: Cr{gross_debt:,} gross — {medical_bills_info['category']} career "
            f"covers {medical_bills_info['coverage_pct']}% (roll {medical_bills_info['total']}). "
            f"Cr{net_debt:,} added (Cr{character.medical_debt:,} total owed)."
        )
    else:
        net_debt = 0

    character.log(
        f"Injury resolved ({pending['title']}): {chosen_stat} chosen. "
        + ", ".join(applied)
    )
    character.pending_injury_choice = None

    return {
        "chosen_stat": chosen_stat,
        "applied": applied,
        "total_loss": total_loss,
        "gross_debt": gross_debt,
        "medical_debt_added": net_debt,
        "medical_debt_total": character.medical_debt,
        "medical_bills_roll": medical_bills_info,
        "character": character.model_dump(),
    }



def end_term(character: Character, leaving: bool = False, reason: str = "voluntary") -> dict:
    """Close out the current term — apply aging if needed, commit the term record."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")

    character.age += 4
    character.total_terms += 1
    character.term_history.append(term)

    aging_log = None
    anagathics_cost_paid = 0
    anagathics_debt = 0
    if character.total_terms >= 4:
        # ── Anagathics cost settlement (RAW: 1D×Cr25,000 per term) ────────
        if character.anagathics_active and character.anagathics_pending_cost > 0:
            cost = character.anagathics_pending_cost
            character.anagathics_pending_cost = 0
            if character.credits >= cost:
                character.credits -= cost
                anagathics_cost_paid = cost
                character.log(f"Anagathics cost: Cr{cost:,} paid from credits.")
            else:
                paid = character.credits
                shortfall = cost - paid
                character.credits = 0
                character.medical_debt += shortfall
                anagathics_cost_paid = paid
                anagathics_debt = shortfall
                character.log(
                    f"Anagathics cost: Cr{paid:,} paid, "
                    f"Cr{shortfall:,} added to medical debt."
                )

        # ── Aging roll (with anagathics positive DM if active) ────────────
        if character.anagathics_active:
            character.anagathics_terms_used += 1
            character.log(
                f"Anagathics active (term {character.anagathics_terms_used}): "
                f"+{character.anagathics_terms_used} DM on aging roll."
            )
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
        forfeit_note = ""
        if term.benefit_forfeited:
            earned = max(0, earned - 1)
            forfeit_note = " (−1 forfeited by mishap)"
        character.pending_benefit_rolls += earned
        character.current_term = None

        # Retirement pension (MgT 2e p.53) — recalculate each time a career
        # ends so the final value reflects total terms served so far.
        # Pension is paid annually (Cr/yr) after the character retires.
        _PENSION_TABLE = {5: 10_000, 6: 12_000, 7: 14_000}
        old_pension = character.pension_per_year
        if character.total_terms >= 8:
            character.pension_per_year = 16_000
        elif character.total_terms in _PENSION_TABLE:
            character.pension_per_year = _PENSION_TABLE[character.total_terms]
        elif character.total_terms >= 5:
            character.pension_per_year = 10_000
        else:
            character.pension_per_year = 0
        pension_note = ""
        if character.pension_per_year > 0 and character.pension_per_year != old_pension:
            pension_note = (
                f" Pension updated: Cr{character.pension_per_year:,}/year."
            )

        # SolSec Monitor rank 3+: one extra benefit roll at final muster-out
        monitor_bonus_note = ""
        if character.solsec_monitor and character.solsec_monitor_rank >= 3:
            character.pending_benefit_rolls += 1
            monitor_bonus_note = " SolSec Monitor (rank 3+): +1 extra Benefit roll."

        character.log(
            f"Left {rules.careers()[term.career_id]['name']} "
            f"({reason}). {terms_in_career} terms served. "
            f"Earns {earned} benefit rolls ({terms_in_career} base + {rank_bonus} rank bonus{forfeit_note}).{pension_note}{monitor_bonus_note}"
        )
    else:
        character.log(f"Completed term {term.overall_term_number}, age now {character.age}.")

    return {
        "aging": aging_log,
        "anagathics_active": character.anagathics_active,
        "anagathics_terms_used": character.anagathics_terms_used,
        "anagathics_cost_paid": anagathics_cost_paid,
        "anagathics_debt": anagathics_debt,
        "age": character.age,
        "total_terms": character.total_terms,
        "pending_benefit_rolls": character.pending_benefit_rolls,
        "character": character.model_dump(),
    }


# ============================================================
# Phase 3: Aging
# ============================================================


def _apply_aging(character: Character) -> dict:
    """Roll on the aging table: 2D - total_terms + anagathics_bonus.

    Physical stat reductions are returned as ``pending_reductions`` for the
    player to choose which characteristics to reduce.  Mental reductions are
    applied automatically (random, per RAW).

    Anagathics positive DM: +anagathics_terms_used (RAW p.155).
    """
    dm = -character.total_terms  # "the older you are, the heavier the effects"
    ana_dm = character.anagathics_terms_used if character.anagathics_terms_used > 0 else 0
    dm += ana_dm
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
        return {"roll": r.to_dict(), "title": "No Effect", "effects_applied": [], "pending_reductions": []}

    effects_applied = []   # auto-applied (mental)
    pending_reductions = []  # player must choose which physical stats

    for effect in entry.get("effects", []):
        if effect["type"] == "reduce_physical":
            # Player chooses which physical stats to reduce
            pending_reductions.append({
                "type": "choose_physical",
                "count": effect["count"],
                "amount": effect["amount"],
                "options": ["STR", "DEX", "END"],
            })
        else:
            applied = _apply_aging_effect_auto(character, effect)
            effects_applied.extend(applied)

    pending_note = (
        f" + Choose {sum(p['count'] for p in pending_reductions)} physical stat reduction(s)"
        if pending_reductions else ""
    )
    character.log(
        f"Aging [2D{dm:+d}={r.total}] {entry['title']}: "
        + (", ".join(effects_applied) if effects_applied else "no auto effect")
        + pending_note
    )
    return {
        "roll": r.to_dict(),
        "title": entry["title"],
        "effects_applied": effects_applied,
        "pending_reductions": pending_reductions,
    }


def _apply_aging_effect_auto(character: Character, effect: dict) -> list[str]:
    """Apply an aging effect that does not require player choice (mental stats).

    Returns log strings.
    """
    mental = ["INT", "EDU", "SOC"]
    logs = []

    if effect["type"] == "reduce_mental":
        count = effect["count"]
        amount = effect["amount"]
        targets = random.sample(mental, min(count, len(mental)))
        for stat in targets:
            old = character.characteristics.get(stat)
            character.characteristics.set(stat, old - amount)
            logs.append(f"{stat} {old}→{character.characteristics.get(stat)}")
    # Note: reduce_physical is handled via pending_reductions / resolve_aging_choice
    return logs


# Keep old name as an alias so nothing else breaks if referenced elsewhere
def _apply_aging_effect(character: Character, effect: dict) -> list[str]:
    """Deprecated shim — routes to _apply_aging_effect_auto."""
    return _apply_aging_effect_auto(character, effect)


def resolve_aging_choice(character: Character, reductions: list[dict]) -> dict:
    """Apply player-chosen physical aging stat reductions.

    ``reductions`` is a list of ``{"stat": "STR", "amount": 1}`` objects.
    Only STR / DEX / END are accepted.
    """
    applied = []
    for item in reductions:
        stat = item.get("stat", "")
        amount = int(item.get("amount", 1))
        if stat not in ("STR", "DEX", "END"):
            raise ValueError(f"Invalid stat for aging choice: {stat!r}")
        old = character.characteristics.get(stat)
        character.characteristics.set(stat, old - amount)
        character.log(f"Aging (player choice): {stat} {old}→{character.characteristics.get(stat)}")
        applied.append(f"{stat} {old}→{character.characteristics.get(stat)}")

    # Check for aging crisis (any stat at 0 after reductions)
    crisis = [s for s in ("STR", "DEX", "END", "INT", "EDU", "SOC")
              if character.characteristics.get(s) <= 0]
    if crisis and not character.dead:
        character.log(
            f"AGING CRISIS: {', '.join(crisis)} reduced to 0. "
            "Character dies unless 1D × Cr10,000 is paid for medical care."
        )
        character.dead = True
        character.death_reason = f"Aging crisis ({', '.join(crisis)} = 0)"

    return {
        "applied": applied,
        "crisis": crisis,
        "character": character.model_dump(),
    }


# ============================================================
# Phase 4: Mustering Out
# ============================================================


def muster_out_roll(
    character: Character, career_id: str, column: str, use_good_fortune: bool = False
) -> dict:
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

    # Good Fortune token (Life Event 10) — voluntary DM+2 on benefit rolls.
    good_fortune_used = False
    if use_good_fortune and character.good_fortune_benefit_dm > 0:
        dm += 2
        character.good_fortune_benefit_dm -= 2
        good_fortune_used = True

    r = dice.roll("1D", modifier=dm)
    # 1D result capped to 1-6 for table lookup
    key = str(max(1, min(6, r.total)))
    row = table.get(key)
    if row is None:
        raise ValueError(f"No row for result {key}")

    if column == "cash":
        cash = row["cash"]
        debt_paid = 0
        if character.medical_debt > 0:
            debt_paid = min(character.medical_debt, cash)
            character.medical_debt -= debt_paid
            cash -= debt_paid
            character.log(
                f"Paid Cr{debt_paid:,} in medical bills "
                f"(Cr{character.medical_debt:,} still owed)."
            )
        character.credits += cash
        character.cash_rolls_used += 1
        result_text = (
            f"Cr{cash:,}" + (f" (after Cr{debt_paid:,} medical)" if debt_paid else "")
        )
        character.log(
            f"Muster out (cash)[{r.total}]: gross Cr{row['cash']:,}, "
            f"medical Cr{debt_paid:,}, net Cr{cash:,}."
        )
    else:
        benefit = row["benefit"]
        _apply_benefit(character, benefit)
        result_text = benefit
        character.log(f"Muster out (benefit)[{r.total}]: {benefit}")

    character.pending_benefit_rolls -= 1
    return {
        "roll": r.to_dict(),
        "result": result_text,
        "remaining_rolls": character.pending_benefit_rolls,
        "good_fortune_used": good_fortune_used,
        "good_fortune_remaining": character.good_fortune_benefit_dm,
        "character": character.model_dump(),
    }


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

    # Associates — Ally, Contact, Rival, Enemy
    _ASSOC_KINDS = {
        "ally": "ally",
        "contact": "contact",
        "rival": "rival",
        "enemy": "enemy",
    }
    b_lower = b.lower()
    if b_lower in _ASSOC_KINDS:
        character.associates.append(
            Associate(kind=_ASSOC_KINDS[b_lower], description="From mustering out")
        )
        return

    # Multi-part "SOC +1 and Yacht"
    if " and " in b:
        for part in b.split(" and "):
            _apply_benefit(character, part)
        return

    # "X or Y" — if either side is an associate, keep both options visible as a note;
    # if both sides are concrete items, add as equipment with a choice note
    if " or " in b:
        parts = [p.strip() for p in b.split(" or ")]
        # Check if any part is an associate kind
        assoc_parts = [p for p in parts if p.lower() in _ASSOC_KINDS]
        non_assoc_parts = [p for p in parts if p.lower() not in _ASSOC_KINDS]
        if assoc_parts and non_assoc_parts:
            # Mixed: e.g. "Blade or Ally" — add as equipment note so player can choose
            character.equipment.append(
                Equipment(name=b, notes="Player choice: pick one (Ally/Contact/Rival/Enemy → Associates)")
            )
        elif assoc_parts:
            # All parts are associates — add the first as a note; player picks
            character.equipment.append(
                Equipment(name=b, notes="Player choice: pick one → add to Associates")
            )
        else:
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


_STAT_KEYS_RANK = {"STR", "DEX", "END", "INT", "EDU", "SOC", "PSI"}


def _apply_rank_bonus(character: "Character", bonus_str: str) -> str:
    """Parse and apply a rank-bonus string to the character.

    Handles:
      - "STAT +N"            e.g. "SOC +2"
      - "SkillName N"        e.g. "Gun Combat 1"
      - "Skill (spec) N"     e.g. "Tactics (military) 1"
      - "SOC 10 or SOC +1, whichever is higher"
      - Plain skill name     e.g. "Jack-of-All-Trades" (treated as level 1)

    Returns a human-readable log string.
    """
    if not bonus_str:
        return "no bonus"
    text = bonus_str.strip()

    # Complex SOC-style: "SOC 10 or SOC +1, whichever is higher"
    m_complex = re.match(
        r"^(SOC|STR|DEX|END|INT|EDU|PSI)\s+(\d+)\s+or\s+\1\s*\+(\d+)",
        text, re.IGNORECASE
    )
    if m_complex:
        stat = m_complex.group(1).upper()
        floor_val = int(m_complex.group(2))
        bonus_n = int(m_complex.group(3))
        current = character.characteristics.get(stat)
        new_val = max(floor_val, current + bonus_n)
        character.characteristics.set(stat, new_val)
        return f"{stat} {current}→{new_val} (rank bonus)"

    # "STAT +N" or "STAT+N"
    m_stat = re.match(r"^(STR|DEX|END|INT|EDU|SOC|PSI)\s*\+(\d+)$", text, re.IGNORECASE)
    if m_stat:
        stat = m_stat.group(1).upper()
        n = int(m_stat.group(2))
        species_data = rules.species().get(character.species_id, {})
        max_stat = species_data.get("characteristic_maximum", 15)
        current = character.characteristics.get(stat)
        new_val = min(max_stat, current + n)
        character.characteristics.set(stat, new_val)
        return f"{stat} {current}→{new_val} (rank bonus)"

    # "Skill (spec) N" or "Skill N" or plain "Skill"
    # Try to strip a trailing digit as the level
    level = 1
    m_level = re.search(r"\s+(\d+)\s*$", text)
    if m_level:
        level = int(m_level.group(1))
        text = text[: m_level.start()].strip()

    speciality: str | None = None
    if "(" in text and text.endswith(")"):
        name = text[: text.index("(")].strip()
        speciality = text[text.index("(") + 1: -1].strip()
    else:
        name = text

    applied_msg = character.add_skill(name, level=level, speciality=speciality)
    disp = f"{name}{f' ({speciality})' if speciality else ''} {level}"
    return f"Rank bonus applied: {disp} ({applied_msg})"


def _medical_bills_roll(character: "Character", gross_debt: int) -> dict:
    """Roll 2D + Rank to see how much of medical debt the character's career pays.

    MgT 2e p.47 medical bills table:
      Military (army/marine/navy):
        Roll <4: 0%  | 4–7: 75% | 8+: 100%
      Civilian (agent/noble/scholar/entertainer/merchant/citizen):
        Roll <4: 0%  | 4–7: 50% | 8–11: 75% | 12+: 100%
      Fringe (scout/rogue/drifter/prisoner/others):
        Roll <4: 0%  | 4–7: 0%  | 8–11: 50% | 12+: 75%

    Returns a dict with roll info and how much debt was cancelled.
    """
    _MILITARY = {"army", "marine", "navy"}
    _CIVILIAN = {"agent", "noble", "scholar", "entertainer", "merchant", "citizen"}

    career_id = ""
    rank = 0
    if character.current_term:
        career_id = character.current_term.career_id
        rank = character.current_term.rank

    r = dice.roll("2D")
    total = r.total + rank

    if career_id in _MILITARY:
        if total >= 8:
            pct = 100
        elif total >= 4:
            pct = 75
        else:
            pct = 0
        category = "Military"
    elif career_id in _CIVILIAN:
        if total >= 12:
            pct = 100
        elif total >= 8:
            pct = 75
        elif total >= 4:
            pct = 50
        else:
            pct = 0
        category = "Civilian"
    else:
        # Fringe: scout, rogue, drifter, prisoner, pre-career, etc.
        if total >= 12:
            pct = 75
        elif total >= 8:
            pct = 50
        else:
            pct = 0
        category = "Fringe"

    covered = int(gross_debt * pct / 100)
    remaining = gross_debt - covered
    return {
        "roll": r.to_dict(),
        "rank_dm": rank,
        "total": total,
        "category": category,
        "coverage_pct": pct,
        "covered": covered,
        "remaining": remaining,
    }


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
        character.add_skill(first, level=1)
        return f"Gained {first} 1 (from choice: {stripped})"

    # Skill with speciality: "Melee (blade)", "Pilot (small craft)"
    if "(" in stripped and ")" in stripped:
        name = stripped.split("(")[0].strip()
        spec = stripped.split("(")[1].rstrip(")")
        character.add_skill(name, level=1, speciality=spec)
        return f"Gained {name} ({spec}) 1"

    # Plain skill name
    character.add_skill(stripped, level=1)
    return f"Gained {stripped} 1"


def grant_event_skill(character: Character, skill_text: str) -> dict:
    """Grant a skill chosen from a multi-option event (e.g. 'Gain one of X, Y, Z or W').

    The text can be a bare skill name ("Vacc Suit"), a skill with a level
    ("Vacc Suit 1"), a skill with a speciality ("Tactics (military)"), or
    both ("Tactics (military) 1"). Parent skill auto-seeding is handled by
    Character.add_skill.
    """
    term = character.current_term
    if term is None:
        raise ValueError("No active term — event skills can only be granted during a career term")

    text = (skill_text or "").strip()
    if not text:
        raise ValueError("Empty skill name")

    # Pull an optional trailing level: "... 1" or "... 2"
    level = 1
    m = re.search(r"\s+(\d+)\s*$", text)
    if m:
        level = int(m.group(1))
        text = text[: m.start()].strip()

    # Optional speciality in parens: "Tactics (military)"
    speciality: str | None = None
    if "(" in text and text.endswith(")"):
        name = text[: text.index("(")].strip()
        speciality = text[text.index("(") + 1 : -1].strip()
    else:
        name = text

    applied_msg = character.add_skill(name, level=level, speciality=speciality)
    display = f"{name}{f' ({speciality})' if speciality else ''} {level}"
    term.skills_gained.append(f"Event choice: {display}")
    character.log(f"Event skill chosen: {display} — {applied_msg}")

    return {"applied": applied_msg, "skill": display, "character": character.model_dump()}


def grant_event_dm(character: Character, dm: int, target: str) -> dict:
    """Apply a DM grant chosen from an event-11 "gain skill OR DM+N" picker.

    `target` must be one of 'advancement', 'qualification', 'benefit'. Mirrors
    the auto-apply path in _apply_event_dms but is explicit/user-initiated.
    """
    term = character.current_term
    if term is None:
        raise ValueError("No active term — event DM grants only apply during a career term")
    tgt = (target or "").strip().lower()
    if tgt == "advancement":
        character.dm_next_advancement += dm
    elif tgt == "qualification":
        character.dm_next_qualification += dm
    elif tgt == "benefit":
        character.dm_next_benefit += dm
    else:
        raise ValueError(f"Unknown DM target: {target}")
    sign = "+" if dm >= 0 else ""
    msg = f"DM{sign}{dm} to next {tgt.capitalize()} roll"
    term.events.append(f"Event choice: {msg}")
    character.log(f"Event DM chosen: {msg}")
    return {"applied": msg, "dm": dm, "target": tgt, "character": character.model_dump()}


_STAT_KEYS = {"STR", "DEX", "END", "INT", "EDU", "SOC", "PSI"}


def apply_event_stat_change(
    character: Character, stat: str, delta: int, reason: str = ""
) -> dict:
    """Apply a ±N delta to a characteristic from an event branch.

    Used by multi-clause events where a branch-specific stat change cannot
    be detected by the generic unconditional stat-bonus parser. Examples:
    noble[3] refuse (SOC -1), noble[3] accept+success (SOC +1), noble[3]
    accept+fail (SOC -1).
    """
    key = (stat or "").strip().upper()
    if key not in _STAT_KEYS:
        raise ValueError(
            f"Unknown stat: {stat!r} (must be one of {sorted(_STAT_KEYS)})"
        )
    try:
        amount = int(delta)
    except (TypeError, ValueError):
        raise ValueError(f"Stat delta must be an integer, got {delta!r}")
    if key == "PSI":
        before = int(character.psi or 0)
        character.psi = max(0, before + amount)
        after = character.psi
    else:
        before = int(character.characteristics.get(key))
        character.characteristics.set(key, before + amount)
        after = character.characteristics.get(key)
    sign = "+" if amount >= 0 else ""
    why = f" ({reason})" if reason else ""
    msg = f"Event outcome: {key} {before} → {after} ({sign}{amount}){why}"
    term = character.current_term
    if term is not None:
        term.events.append(msg)
    character.log(msg)
    return {
        "applied": {"stat": key, "from": before, "to": after, "delta": amount},
        "reason": reason,
        "character": character.model_dump(),
    }


def accept_transfer_offer(character: Character, target_career_id: str) -> dict:
    """Record a career-transfer offer from an event. On the next qualify
    call targeting this career, the qualification roll is skipped.
    'any' means the player may transfer to ANY career without a qualification roll.
    """
    if target_career_id == "any":
        character.pending_transfer_career_id = "any"
        msg = "Event choice: may transfer to any career at term end (no qualification roll)"
        if character.current_term is not None:
            character.current_term.events.append(msg)
        character.log(msg)
        return {"pending_transfer": "any", "target_name": "any career",
                "character": character.model_dump()}
    careers = rules.careers()
    if target_career_id not in careers:
        raise ValueError(f"Unknown career: {target_career_id!r}")
    target_name = careers[target_career_id].get("name", target_career_id)
    character.pending_transfer_career_id = target_career_id
    term = character.current_term
    msg = f"Event choice: transfer to {target_name} at term end (no qualification roll)"
    if term is not None:
        term.events.append(msg)
    character.log(msg)
    return {
        "pending_transfer": target_career_id,
        "target_name": target_name,
        "character": character.model_dump(),
    }


# ============================================================
# Associate mutations (gain Contact/Ally/Rival/Enemy, Betrayal)
# ============================================================

_ASSOCIATE_KINDS = {"contact", "ally", "rival", "enemy"}


def add_associate(character: Character, kind: str, description: str = "") -> dict:
    """Add a new Associate (contact/ally/rival/enemy) to the character.

    Triggered by event text like 'Gain an Ally', 'Gain a Rival', etc. When
    an event offers a choice ('Gain a Rival or Enemy'), the UI decides and
    passes the resolved ``kind`` here.
    """
    k = (kind or "").strip().lower()
    if k not in _ASSOCIATE_KINDS:
        raise ValueError(
            f"Unknown associate kind: {kind!r} (must be one of {sorted(_ASSOCIATE_KINDS)})"
        )
    desc = (description or "").strip() or f"Unnamed {k.capitalize()}"
    character.associates.append(Associate(kind=k, description=desc))
    if character.current_term is not None:
        character.current_term.events.append(f"Gained {k.capitalize()}: {desc}")
    character.log(f"Gained {k.capitalize()}: {desc}")
    return {
        "added": {"kind": k, "description": desc},
        "associate_count": len(character.associates),
        "character": character.model_dump(),
    }


def convert_associate(character: Character, index: int, to_kind: str) -> dict:
    """Convert an existing Contact or Ally into a Rival or Enemy.

    Used by the Betrayal life event: 'If you have any Contacts or Allies,
    convert one into a Rival or Enemy.'
    """
    if index < 0 or index >= len(character.associates):
        raise ValueError(
            f"Associate index {index} out of range (have {len(character.associates)})"
        )
    a = character.associates[index]
    to = (to_kind or "").strip().lower()
    if to not in {"rival", "enemy"}:
        raise ValueError(
            f"Can only convert to 'rival' or 'enemy' (got {to_kind!r})"
        )
    if a.kind not in {"contact", "ally"}:
        raise ValueError(
            f"Can only convert a Contact or Ally (this one is a {a.kind.capitalize()})"
        )
    from_kind = a.kind
    a.kind = to
    msg = f"Betrayal: {from_kind.capitalize()} → {to.capitalize()}"
    if a.description:
        msg += f" ({a.description})"
    if character.current_term is not None:
        character.current_term.events.append(msg)
    character.log(msg)
    return {
        "converted": {
            "from_kind": from_kind,
            "to_kind": to,
            "description": a.description,
            "index": index,
        },
        "character": character.model_dump(),
    }


# ============================================================
# NPC Auto-generation
# ============================================================

def _npc_pick_career(character: "Character") -> str:
    """Score each complete career by the character's DM for its qualification stat."""
    all_careers = rules.careers()
    scores: list[tuple[int, str]] = []
    for cid, career in all_careers.items():
        if not career.get("complete"):
            continue
        if cid in (character.banned_career_ids or []):
            continue
        qual = career.get("qualification", {})
        if qual.get("automatic"):
            score = 0
        else:
            char_key = qual.get("characteristic", "INT")
            if char_key == "DEX_OR_INT":
                score = max(
                    dice.characteristic_dm(character.characteristics.DEX),
                    dice.characteristic_dm(character.characteristics.INT),
                )
            else:
                score = dice.characteristic_dm(
                    getattr(character.characteristics, char_key, 7)
                )
        scores.append((score, cid))
    scores.sort(reverse=True)
    # Pick randomly among the top scorers (within 1 point of best)
    best = scores[0][0] if scores else 0
    top = [cid for s, cid in scores if s >= best - 1]
    return random.choice(top) if top else "drifter"


def _npc_best_assignment(career: dict, character: "Character") -> str:
    """Return the assignment with the best survival DM for the character."""
    best_id = list(career["assignments"].keys())[0]
    best_dm = -99
    for aid, asgn in career["assignments"].items():
        char_key = asgn.get("survival", {}).get("characteristic", "END")
        dm = dice.characteristic_dm(getattr(character.characteristics, char_key, 7))
        if dm > best_dm:
            best_dm = dm
            best_id = aid
    return best_id


def generate_npc() -> dict:
    """Generate a complete NPC character automatically.

    Rolls characteristics, picks the most suitable career, runs 2-4 terms,
    then mustering out — all server-side with no player interaction.
    """
    char = Character()

    # ── Characteristics
    for stat, val in dice.roll_characteristics().items():
        setattr(char.characteristics, stat, val)

    # ── Species: Imperial Human (no modifiers, but apply traits)
    sp = rules.species().get("imperial_human", {})
    char.species_id = "imperial_human"
    char.traits = sp.get("traits", [])
    char.phase = "background"

    # ── Background skills (3 + EDU DM, min 1)
    edu_dm = dice.characteristic_dm(char.characteristics.EDU)
    bg_count = max(1, 3 + edu_dm)
    bg = rules.background_skills()
    for sk in list(bg.get("skills", {}).keys())[:bg_count]:
        char.add_skill(sk, level=0)

    char.phase = "career"

    # ── Career selection
    career_id = _npc_pick_career(char)
    career = rules.careers()[career_id]
    assignment_id = _npc_best_assignment(career, char)
    char.log(f"NPC: Selected {career['name']} / {assignment_id}")

    # ── Basic training: all service skills at level 0
    service_table = career.get("skill_tables", {}).get("service_skills", {})
    for i in range(1, 7):
        sk = service_table.get(str(i), "")
        if sk:
            _apply_skill_result(char, sk.split(" ")[0] if "+" not in sk else "")
    # More reliable: just add service skills at 0
    for i in range(1, 7):
        sk = service_table.get(str(i), "")
        if sk and "+" not in sk:
            char.add_skill(sk.split("(")[0].strip(), level=0)

    # ── Run terms
    num_terms = random.randint(2, 4)
    assignment = career["assignments"][assignment_id]
    surv_cfg = assignment["survival"]
    adv_cfg = assignment["advancement"]

    for term_num in range(1, num_terms + 1):
        overall_num = char.total_terms + 1
        term = CareerTerm(
            career_id=career_id,
            assignment_id=assignment_id,
            term_number=term_num,
            overall_term_number=overall_num,
        )
        char.current_term = term

        # One service skill roll
        r = dice.roll("1D")
        sk_result = service_table.get(str(r.total), "")
        if sk_result:
            applied = _apply_skill_result(char, sk_result)
            term.skills_gained.append(f"Service: {sk_result}")

        # Survival
        surv_dm = dice.characteristic_dm(
            getattr(char.characteristics, surv_cfg["characteristic"], 7)
        )
        surv_roll = dice.roll("2D", modifier=surv_dm, target=surv_cfg["target"])
        term.survived = bool(surv_roll.succeeded)
        term.survival_roll_total = surv_roll.total

        if not surv_roll.succeeded:
            # Mishap — auto-apply safe effects, end career
            mishap_r = dice.roll("1D")
            mishap_num = mishap_r.total
            mishap_text = career.get("mishaps", {}).get(str(mishap_num), "Mishap.")
            term.mishap = mishap_text
            char.log(f"NPC Mishap [1D={mishap_num}]: {mishap_text}")
            effects = _MISHAP_EFFECTS.get(career_id, {}).get(mishap_num, [])
            for eff in effects:
                if eff["type"] in ("enemy", "rival", "contact", "ally", "stat", "skill",
                                   "forfeit_benefit", "debt", "d_associates"):
                    _apply_mishap_effect(char, eff, term)
            # Light auto-injury for result 1/6 mishaps
            if any(e["type"] in ("injury", "injury_severity_choice") for e in effects):
                inj = _apply_injury_for_result(char, 5)  # result 5 = lose 1 physical
                if char.pending_injury_choice:
                    resolve_injury_choice(char, char.pending_injury_choice["choices"][0])
            # End career via mishap
            char.age += 4
            char.total_terms += 1
            char.term_history.append(term)
            char.current_term = None
            terms_in_career = sum(1 for h in char.term_history if h.career_id == career_id)
            rank_bonus = _benefit_rolls_from_rank(term.rank)
            earned = max(0, terms_in_career + rank_bonus - (1 if term.benefit_forfeited else 0))
            char.pending_benefit_rolls += earned
            char.completed_careers.append(CareerRecord(
                career_id=career_id, assignment_id=assignment_id,
                terms_served=terms_in_career, final_rank=term.rank,
                final_rank_title=term.rank_title, left_due_to="mishap",
            ))
            break

        # Event (auto-apply safe effects only)
        events_table = career.get("events", {})
        ev_r = dice.roll("2D")
        ev_text = events_table.get(str(ev_r.total), "")
        if ev_text:
            term.events.append(ev_text)
            _apply_event_dms(char, ev_text)
            _apply_event_stat_bonuses(char, ev_text)
            _apply_event_auto_promotion(char, ev_text)
            # Life event sub-roll — route to career-appropriate table.
            if ev_text.lower().startswith("life event"):
                life_r = dice.roll("2D")
                life_table_data = rules.life_events_for_career(term.career_id)
                life_data = life_table_data["entries"].get(str(life_r.total))
                if life_data:
                    term.events[-1] += f" — {life_data['title']}: {life_data['text']}"

        # Advancement
        adv_dm = dice.characteristic_dm(
            getattr(char.characteristics, adv_cfg["characteristic"], 7)
        )
        adv_dm += char.dm_next_advancement
        char.dm_next_advancement = 0
        adv_roll = dice.roll("2D", modifier=adv_dm, target=adv_cfg["target"])
        term.advanced = bool(adv_roll.succeeded)
        if adv_roll.succeeded:
            term.rank += 1
            term.rank_title = _rank_title(career, assignment_id, term.rank)
            rd = _rank_data(career, assignment_id, term.rank)
            if rd and rd.get("bonus"):
                _apply_skill_result(char, rd["bonus"])
                term.skills_gained.append(f"Rank bonus: {rd['bonus']}")

        # End term
        char.age += 4
        char.total_terms += 1
        char.term_history.append(term)
        char.current_term = None

    # ── Finalise career (if not already ended by mishap)
    if not char.completed_careers:
        terms_in_career = sum(1 for h in char.term_history if h.career_id == career_id)
        rank_bonus = _benefit_rolls_from_rank(
            char.term_history[-1].rank if char.term_history else 0
        )
        char.pending_benefit_rolls += terms_in_career + rank_bonus
        final_term = char.term_history[-1] if char.term_history else None
        char.completed_careers.append(CareerRecord(
            career_id=career_id, assignment_id=assignment_id,
            terms_served=terms_in_career,
            final_rank=final_term.rank if final_term else 0,
            final_rank_title=final_term.rank_title if final_term else None,
            left_due_to="voluntary",
        ))

    # ── Muster out: roll all pending benefit rolls (max 3 cash rolls)
    muster_table = career.get("mustering_out", {})
    max_entries = len(muster_table)
    while char.pending_benefit_rolls > 0:
        char.pending_benefit_rolls -= 1
        r = min(dice.roll("1D").total, max_entries)
        entry = muster_table.get(str(r), {})
        if isinstance(entry, dict):
            if char.cash_rolls_used < 3:
                char.credits += entry.get("cash", 0)
                char.cash_rolls_used += 1
            else:
                benefit = entry.get("benefit", "")
                if benefit:
                    _apply_skill_result(char, benefit)

    char.phase = "complete"
    char.log(f"NPC generation complete. Age {char.age}, {char.total_terms} terms.")
    return {"character": char.model_dump()}


# ============================================================
# Skill Packages (MgT2e p.42)
# ============================================================

def apply_skill_package(character: Character, package_id: str) -> dict:
    """Apply a skill package to the character after character creation.

    Each entry in the package is a string like "Pilot 1" or "Tactics (naval) 1".
    The character.add_skill call increases an existing skill by level, or
    creates it at that level if new.
    """
    packages_data = rules.skill_packages()
    package = packages_data.get("packages", {}).get(package_id)
    if package is None:
        raise ValueError(f"Unknown skill package: {package_id}")

    applied: list[str] = []
    for skill_str in package.get("skills", []):
        text = skill_str.strip()
        # Extract trailing level number
        level = 1
        m = re.search(r"\s+(\d+)\s*$", text)
        if m:
            level = int(m.group(1))
            text = text[: m.start()].strip()
        # Extract optional speciality
        speciality: str | None = None
        if "(" in text and text.endswith(")"):
            name = text[: text.index("(")].strip()
            speciality = text[text.index("(") + 1: -1].strip()
        else:
            name = text
        msg = character.add_skill(name, level=level, speciality=speciality)
        disp = f"{name}{f' ({speciality})' if speciality else ''} {level}"
        applied.append(disp)
        character.log(f"Skill package '{package_id}': {disp} — {msg}")

    return {"applied": applied, "character": character.model_dump()}
