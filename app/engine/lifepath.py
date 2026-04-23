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
#       Also "DM+N ... or ..." forms via the second alt.
_CONDITIONAL_RE = re.compile(
    # Actual skill-check prefix: "Roll Stealth 8+" / "Roll INT 8+".
    r"\broll\s+[A-Za-z][A-Za-z\s()\-]{0,40}?\b\d+\s*\+"
    # DM is the second alternative: ", or DM+N" / ", or a DM+N" / ", or +N DM".
    r"|,\s*or\s+(?:a\s+)?(?:dm\s*[+-]\d+|[+-]\d+\s*dm)"
    r"|\bor\s+(?:a\s+)?(?:dm\s*[+-]\d+|[+-]\d+\s*dm)\s+to\s+(?:a|any|your|one)"
    # DM is the first alternative: "DM+N ... , or pick up / gain / take / increase <skill>"
    r"|\bdm\s*[+-]\d+[^.]{0,80}?,\s*or\s+(?:pick\s+up|gain|take|increase|learn|get|choose)\b",
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

    if rank_data and rank_data.get("bonus"):
        bonus = rank_data["bonus"]
        term.skills_gained.append(f"Rank bonus (auto-promotion): {bonus}")

    title_part = f" — {term.rank_title}" if term.rank_title else ""
    character.log(f"  - Event grants AUTOMATIC PROMOTION: rank {old_rank} -> {term.rank}{title_part}.")
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
    r = dice.roll("2D", modifier=dm, target=pot["target"])

    character.psi_tested = True

    if not r.succeeded:
        character.psi = 0
        character.log(
            f"Psionic potential test [2D{dm:+d}={r.total}]: FAILED "
            f"(needed {pot['target']}+). No psionic ability."
        )
        return {
            "potential_roll": r.to_dict(),
            "potential_succeeded": False,
            "psi": 0,
            "character": character.model_dump(),
        }

    # Passed — roll Psi strength: 2D minus total_terms, clamped.
    formula = data["psi_strength_formula"]
    raw = dice.roll(formula["dice"])
    psi_val = raw.total - character.total_terms
    psi_val = max(formula.get("min", 0), min(formula.get("max", 15), psi_val))
    character.psi = psi_val
    character.log(
        f"Psionic potential [2D{dm:+d}={r.total}]: PASSED. "
        f"Psi strength [2D-{character.total_terms}={raw.total}-{character.total_terms}={psi_val}]."
    )
    return {
        "potential_roll": r.to_dict(),
        "potential_succeeded": True,
        "psi_roll": raw.to_dict(),
        "psi": psi_val,
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
    if character.credits < cost:
        raise ValueError(
            f"Insufficient credits: need Cr{cost:,}, have Cr{character.credits:,}."
        )

    # DM = character.psi - talent target (Psi serves as the characteristic)
    target = talent.get("test_target", 8)
    dm = dice.characteristic_dm(character.psi)
    r = dice.roll("2D", modifier=dm, target=target)

    character.credits -= cost
    log_msg = (
        f"Psi training — {talent['name']} "
        f"[2D{dm:+d}={r.total} vs {target}+, cost Cr{cost:,}]"
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
        "credits_remaining": character.credits,
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
    character: Character, track: str, service: Optional[str] = None
) -> dict:
    """Roll qualification for University or a Military Academy service.

    On success: applies enrollment bonus (e.g. +1 EDU for University,
    or enrollment skills for an Academy) and advances to the 'enrolled'
    stage. On failure: no bonus, falls through to career phase.
    """
    if character.phase != "pre_career":
        raise ValueError(f"Not in pre-career phase (currently: {character.phase})")

    track_data = _edu_track(track)

    if character.age > track_data["max_age"]:
        raise ValueError(
            f"Too old for {track_data['name']} (age {character.age} > "
            f"max {track_data['max_age']})"
        )

    # Which qualification block applies?
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

    # Optional generic modifiers (currently: per_previous_term)
    for mod in qual.get("modifiers", []):
        if mod.get("type") == "per_previous_term":
            dm += mod["dm"] * character.total_terms
        elif mod.get("type") == "per_previous_career":
            dm += mod["dm"] * len(character.completed_careers)

    r = dice.roll("2D", modifier=dm, target=target)

    passed = bool(r.succeeded)
    enrollment_applied: list[str] = []

    if passed:
        # Enrollment bonuses. University applies +1 EDU; academies apply
        # fixed enrollment skills.
        if track == "university":
            bonuses = track_data.get("enrollment_bonus", {})
            for stat, delta in bonuses.items():
                current = character.characteristics.get(stat)
                character.characteristics.set(stat, current + delta)
                enrollment_applied.append(f"{stat} {delta:+d}")
        else:
            for sk in svc.get("enrollment_skills", []):
                msg = character.add_skill(
                    sk["name"], level=sk.get("level", 0),
                    speciality=sk.get("speciality"),
                )
                enrollment_applied.append(msg)

        # Age ticks on successful enrollment (student has committed).
        character.age += track_data["age_cost"]

        character.pre_career_status = {
            "track": track,
            "service": service,
            "stage": "enrolled",
            "outcome": None,
            "skill_picks_remaining": 0,
            "skill_pool": [],
        }
        character.log(
            f"Qualified for {display_name} ({char_key} {target}+): "
            f"2D{dm:+d} = {r.total} [PASS]. "
            + (f"Enrollment bonus: {', '.join(enrollment_applied)}"
               if enrollment_applied else "")
        )
    else:
        # Failed qualification — no age cost, fall through to careers.
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
    dm = dice.characteristic_dm(character.characteristics.get(char_key))

    r = dice.roll("2D", modifier=dm, target=target)

    outcome: str
    applied_note: list[str] = []
    skill_pool: list[str] = []
    picks_remaining = 0

    if not r.succeeded:
        outcome = "fail"
        note = grad.get("on_failure", {}).get("note", "Failed to graduate.")
        applied_note.append(note)
    else:
        is_honours = honours_target is not None and r.total >= honours_target
        block = grad["on_honours"] if is_honours else grad["on_graduation"]
        outcome = "honours" if is_honours else "pass"

        # Stat bumps
        for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
            if stat in block:
                delta = int(block[stat])
                current = character.characteristics.get(stat)
                character.characteristics.set(stat, current + delta)
                applied_note.append(f"{stat} {delta:+d}")

        # Pending DMs for next rolls
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

        # Academy commission: first term of matching career starts at Rank 1.
        if "starts_commissioned_rank" in block and track == "military_academy":
            svc = _academy_service(service)
            character.starts_commissioned_career_id = svc["career_id"]
            applied_note.append(
                f"starts {svc['name']} commissioned at Rank "
                f"{block['starts_commissioned_rank']}"
            )

        # Skill picks
        picks = int(block.get("skills_at_level_1", 0))
        if picks > 0:
            picks_remaining = picks
            if track == "university":
                skill_pool = list(track_data.get("skill_list", []))
            else:
                svc = _academy_service(service)
                skill_pool = [s["name"] for s in svc.get("enrollment_skills", [])]
                # Fallback: if academy has no explicit pool, fall back to a
                # small generic military list.
                if not skill_pool:
                    skill_pool = ["Gun Combat", "Melee", "Drive",
                                  "Electronics", "Tactics"]

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
            character.add_skill(s, level=1)
        picks_remaining -= len(chosen_skills)

    # Update status + phase
    still_needs_picks = picks_remaining > 0
    character.pre_career_status = {
        "track": track,
        "service": service,
        "stage": "graduated" if outcome != "fail" else "failed_grad",
        "outcome": outcome,
        "skill_picks_remaining": picks_remaining,
        "skill_pool": skill_pool,
    }
    if not still_needs_picks:
        character.phase = "career"

    label = {"pass": "GRADUATED", "honours": "GRADUATED w/ HONOURS",
             "fail": "FAILED TO GRADUATE"}[outcome]
    character.log(
        f"Graduation ({char_key} {target}+"
        + (f", Honours {honours_target}+" if honours_target else "")
        + f"): 2D{dm:+d} = {r.total} [{label}]. "
        + ("; ".join(applied_note) if applied_note else "")
    )

    return {
        "roll": r.to_dict(),
        "outcome": outcome,
        "honours_target": honours_target,
        "skill_pool": skill_pool,
        "skill_picks_remaining": picks_remaining,
        "applied": applied_note,
        "character": character.model_dump(),
    }


def pre_career_choose_skills(
    character: Character, chosen_skills: list[str]
) -> dict:
    """Apply pending graduation skill picks (used when the UI resolves picks
    separately from the graduation roll)."""
    status = character.pre_career_status or {}
    remaining = int(status.get("skill_picks_remaining", 0))
    pool = list(status.get("skill_pool", []))

    if remaining <= 0:
        raise ValueError("No pending skill picks.")
    if len(chosen_skills) > remaining:
        raise ValueError(
            f"Chose {len(chosen_skills)} skills but only {remaining} picks left."
        )
    for s in chosen_skills:
        if s not in pool:
            raise ValueError(f"'{s}' not in this track's skill pool.")
        character.add_skill(s, level=1)

    remaining -= len(chosen_skills)
    character.pre_career_status = {
        **status,
        "skill_picks_remaining": remaining,
    }
    character.log(
        f"Picked {len(chosen_skills)} pre-career graduation skill(s): "
        + ", ".join(chosen_skills)
    )
    if remaining == 0:
        character.phase = "career"
    return {
        "chosen": chosen_skills,
        "skill_picks_remaining": remaining,
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

    # Event-granted career transfer (e.g. army[10] "transfer to the Marines
    # without a Qualification roll"). Consume the offer and skip qualification.
    if character.pending_transfer_career_id == career_id:
        character.pending_transfer_career_id = None
        character.log(
            f"Transferring to {career['name']} via event offer — no qualification roll required."
        )
        return {"automatic": True, "succeeded": True, "transfer": True,
                "character": character.model_dump()}

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

    # Pre-career military academy honored: first term in matching career
    # starts commissioned at Rank 1.
    commissioned_start = (
        first_term_in_this_career
        and character.starts_commissioned_career_id == career_id
    )
    starting_rank = 1 if commissioned_start else 0

    term = CareerTerm(
        career_id=career_id,
        assignment_id=assignment_id,
        term_number=1 if is_new_career else (character.current_term.term_number + 1),
        overall_term_number=character.total_terms + 1,
        rank=starting_rank,
        rank_title=_rank_title(career, assignment_id, starting_rank),
        basic_training=first_term_in_this_career and not commissioned_start,
        commissioned=commissioned_start,
    )
    character.current_term = term

    # Consume the commission so subsequent terms don't re-trigger it.
    if commissioned_start:
        character.starts_commissioned_career_id = None

    character.log(
        f"Begin Term {term.overall_term_number}: {career['name']} — "
        f"{career['assignments'][assignment_id]['name']}"
        + (" (Basic Training)" if term.basic_training else "")
        + (f" — commissioned at Rank {starting_rank}"
           f"{' (' + term.rank_title + ')' if term.rank_title else ''}"
           if commissioned_start else "")
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


# ============================================================
# Anagathics — life extension (Core Rulebook p.155)
# ============================================================

# Cost per 4-year term of anagathic treatment (Cr50,000/yr × 4).
ANAGATHICS_COST_PER_TERM = 200000


def purchase_anagathics(character: "Character") -> dict:
    """Buy one term's worth of anagathics treatment.

    The character must be in the career phase with the credits in hand.
    Each purchase banks one suppressed aging roll — consumed automatically
    the next time end_term would trigger aging.
    """
    if character.phase != "career":
        raise ValueError(
            f"Anagathics can only be bought during the career phase "
            f"(currently: {character.phase})"
        )
    if character.credits < ANAGATHICS_COST_PER_TERM:
        raise ValueError(
            f"Insufficient credits: need Cr{ANAGATHICS_COST_PER_TERM:,}, "
            f"have Cr{character.credits:,}"
        )

    character.credits -= ANAGATHICS_COST_PER_TERM
    character.anagathics_purchased_terms += 1
    character.log(
        f"Purchased anagathics (Cr{ANAGATHICS_COST_PER_TERM:,}). "
        f"Next aging roll will be suppressed. "
        f"Treatments banked: {character.anagathics_purchased_terms}."
    )
    return {
        "cost": ANAGATHICS_COST_PER_TERM,
        "credits_remaining": character.credits,
        "anagathics_purchased_terms": character.anagathics_purchased_terms,
        "character": character.model_dump(),
    }


# ============================================================
# Injury resolution (1D) — medical bills land here
# ============================================================


def apply_injury(character: "Character") -> dict:
    """Roll 1D on the Injury table and apply its effects plus medical bills.

    Used after a mishap or a "serious injury" event outcome. Severity
    drives both characteristic loss and the resulting medical debt,
    which is then deducted from mustering-out cash.
    """
    data = rules.injury_table()
    r = dice.roll("1D")
    entry = data["entries"].get(str(r.total))
    if entry is None:
        raise ValueError(f"No injury entry for roll {r.total}")

    effects_applied: list[str] = []
    for effect in entry.get("effects", []):
        effects_applied.extend(_apply_injury_effect(character, effect))

    # Medical bills scale with severity (rulebook: "medical care" costs).
    severity_cost = {
        1: 100000,  # Nearly killed
        2: 50000,   # Severely injured
        3: 30000,   # Missing Eye or Limb
        4: 10000,   # Scarred
        5: 10000,   # Injured
        6: 0,       # Lightly Injured
    }
    debt = severity_cost.get(r.total, 0)
    if debt:
        character.medical_debt += debt
        character.log(
            f"Medical bills: Cr{debt:,} added to debt "
            f"(now Cr{character.medical_debt:,} owed)."
        )

    character.log(
        f"Injury [1D={r.total}]: {entry['title']} — "
        + (", ".join(effects_applied) if effects_applied else "no stat effect")
    )
    return {
        "roll": r.to_dict(),
        "title": entry["title"],
        "text": entry["text"],
        "effects_applied": effects_applied,
        "medical_debt_added": debt,
        "medical_debt_total": character.medical_debt,
        "character": character.model_dump(),
    }


def _apply_injury_effect(character: "Character", effect: dict) -> list[str]:
    """Apply one injury-table effect dict to the character."""
    physical = ["STR", "DEX", "END"]
    logs: list[str] = []
    etype = effect.get("type")
    amount = effect.get("amount", 0)
    if isinstance(amount, str) and amount.upper() == "1D":
        amount = dice.roll("1D").total

    if etype == "reduce_physical_random":
        target = random.choice(physical)
        old = character.characteristics.get(target)
        character.characteristics.set(target, old - amount)
        logs.append(f"{target} {old}→{character.characteristics.get(target)}")
    elif etype == "reduce_physical_other":
        count = effect.get("count", 1)
        targets = random.sample(physical, min(count, len(physical)))
        for stat in targets:
            old = character.characteristics.get(stat)
            character.characteristics.set(stat, old - amount)
            logs.append(f"{stat} {old}→{character.characteristics.get(stat)}")
    elif etype == "reduce_choice":
        options = effect.get("characteristics", physical)
        target = random.choice(options)
        old = character.characteristics.get(target)
        character.characteristics.set(target, old - amount)
        logs.append(f"{target} {old}→{character.characteristics.get(target)}")
    return logs



def end_term(character: Character, leaving: bool = False, reason: str = "voluntary") -> dict:
    """Close out the current term — apply aging if needed, commit the term record."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")

    character.age += 4
    character.total_terms += 1
    character.term_history.append(term)

    aging_log = None
    anagathics_suppressed = False
    if character.total_terms >= 4:
        if character.anagathics_purchased_terms > 0:
            character.anagathics_purchased_terms -= 1
            anagathics_suppressed = True
            character.log(
                f"Anagathics active — aging roll suppressed "
                f"({character.anagathics_purchased_terms} treatments left)."
            )
            # Long-term anagathics use: small chance of addiction after several terms.
            if (not character.anagathics_addicted
                    and character.total_terms >= 6
                    and dice.roll("2D").total <= 3):
                character.anagathics_addicted = True
                character.log(
                    "ANAGATHICS ADDICTION: character is now dependent on "
                    "treatment. Stopping will cause accelerated aging."
                )
        else:
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
        "anagathics_suppressed": anagathics_suppressed,
        "anagathics_purchased_terms": character.anagathics_purchased_terms,
        "anagathics_addicted": character.anagathics_addicted,
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
    """
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
