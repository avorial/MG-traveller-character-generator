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
    r"\b(STR|DEX|END|INT|EDU|SOC|TER)\s*([+-]\d+)\b",
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
        old = _get_stat(character, g["stat"])
        new_val = max(0, old + g["amount"])
        _set_stat(character, g["stat"], new_val)
        character.log(f"  - Event stat bonus: {g['stat']} {old} -> {new_val} ({g['amount']:+d}).")
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
    rank_data = _rank_data(career, term.assignment_id, next_rank, commissioned=term.commissioned)
    if rank_data is None and next_rank > 1:
        # No data for the next rank means we've hit the top.
        character.log(f"  - Event grants automatic promotion, but already at top rank for {term.career_id}/{term.assignment_id}.")
        return {"skipped": True, "reason": "rank_cap", "rank": term.rank}

    old_rank = term.rank
    term.rank = next_rank
    term.rank_title = _rank_title(career, term.assignment_id, term.rank, commissioned=term.commissioned)

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


def roll_initial_characteristics(character: Character, heroic: bool = False) -> dict:
    """Roll characteristics. Standard: 6×2D. Heroic: 4×2D + 2×3D drop lowest."""
    import random as _random
    stats = ("STR", "DEX", "END", "INT", "EDU", "SOC")
    rolls = {}
    heroic_stats = set(_random.sample(list(stats), 2)) if heroic else set()

    for stat in stats:
        if stat in heroic_stats:
            three_dice = [dice.roll("1D").total for _ in range(3)]
            kept = sorted(three_dice)[1:]  # drop lowest, keep best 2
            total = sum(kept)
            rolls[stat] = {"dice": three_dice, "kept": kept, "total": total, "heroic": True}
        else:
            r = dice.roll("2D")
            d = r.to_dict()
            d["heroic"] = False
            rolls[stat] = d
        character.characteristics.set(stat, rolls[stat]["total"])

    character.log(
        ("Heroic roll: " if heroic else "Rolled characteristics: ")
        + ", ".join(
            f"{k} {character.characteristics.get(k)}{'*' if k in heroic_stats else ''}"
            for k in stats
        )
        + (" (* = 3D best 2)" if heroic else "")
    )
    return {"rolls": rolls, "character": character.model_dump()}


_VALID_EXTRA_STATS = {"PSI", "WLT", "LCK", "MRL", "STY", "TER"}


def roll_extra_characteristics(character: Character, stats: list[str], heroic: bool = False) -> dict:
    """Roll optional extra characteristics (PSI, WLT, LCK, MRL, STY, TER).
    Standard: 2D per stat. Heroic: each selected stat rolls 3D drop lowest."""
    import random as _random
    valid = [s.upper() for s in stats if s.upper() in _VALID_EXTRA_STATS]
    if not valid:
        return {"rolls": {}, "character": character.model_dump()}

    rolls = {}
    for stat in valid:
        if heroic:
            three_dice = [dice.roll("1D").total for _ in range(3)]
            kept = sorted(three_dice)[1:]
            total = sum(kept)
            rolls[stat] = {"dice": three_dice, "kept": kept, "total": total, "heroic": True}
        else:
            r = dice.roll("2D")
            d = r.to_dict()
            d["heroic"] = False
            rolls[stat] = d
        character.extra_characteristics[stat] = rolls[stat]["total"]
        # PSI also updates the dedicated psi field so psionics system stays in sync
        if stat == "PSI":
            character.psi = rolls[stat]["total"]

    character.log(
        ("Heroic extra stats: " if heroic else "Rolled extra stats: ")
        + ", ".join(f"{k} {character.extra_characteristics[k]}{'*' if heroic else ''}" for k in valid)
        + (" (* = 3D best 2)" if heroic else "")
    )
    return {"rolls": rolls, "character": character.model_dump()}


_VALID_CHARS = {"STR", "DEX", "END", "INT", "EDU", "SOC"}

# All characteristic keys including PSI (used for GM set-stat and event branches).
_STAT_KEYS: frozenset[str] = frozenset({"STR", "DEX", "END", "INT", "EDU", "SOC", "PSI"})


def _zhodani_class(soc: int) -> str:
    """Return the Zhodani social class for a given SOC value.

    Noble: SOC 11+  — undergoes psionic training; auto-advances first term; DM+1 advancement.
    Intendant: SOC 10 — undergoes psionic training; Government rank capped at 3.
    Prole: SOC 9-  — no psionic training; Government rank capped at 3.
    """
    if soc >= 11:
        return "noble"
    if soc == 10:
        return "intendant"
    return "prole"


def _char_dm(character: "Character", char_key: str) -> int:
    """Return the DM for a characteristic, including REP, PSI, RES, TER, and FOL.

    REP is stored on character.reputation.
    PSI is stored on character.psi.
    RES (Hiver Resolve) is an alias for SOC (stored in characteristics.SOC).
    TER/FOL are stored in extra_characteristics.
    All others use the standard Characteristics object.  Unknown keys return DM 0.
    """
    k = char_key.upper()
    if k == "REP":
        return dice.characteristic_dm(character.reputation)
    if k == "BOL":
        return dice.characteristic_dm(character.boldness)
    if k == "PSI":
        return dice.characteristic_dm(character.psi)
    if k == "RES":
        return dice.characteristic_dm(character.characteristics.SOC)
    if k in ("TER", "FOL"):
        return dice.characteristic_dm(character.extra_characteristics.get(k, 0))
    val = character.characteristics.get(k)
    return dice.characteristic_dm(val) if val is not None else 0

# Retirement pension table (MgT 2e p.53): terms_served → Cr/year.
# Terms ≥ 8 pay Cr16,000; 9+ add Cr2,000 per term beyond 8. Terms < 5 pay nothing.
_PENSION_TABLE: dict[int, int] = {5: 10_000, 6: 12_000, 7: 14_000, 8: 16_000}

# Careers excluded from pension eligibility (RAW p.53).
# Aslan careers are all exempt — Aslan have no pension system (they use Clan Shares instead).
_PENSION_EXEMPT_CAREERS: frozenset[str] = frozenset({
    "scout", "rogue", "prisoner", "drifter",
    "aslan_ceremonial", "aslan_envoy", "aslan_management",
    "aslan_military", "aslan_military_officer", "aslan_scientist",
    "aslan_spacer", "aslan_space_officer", "aslan_outcast",
    "aslan_outlaw", "aslan_wanderer",
})


def _pension_for_terms(n: int) -> int:
    """Annual pension in Cr for n qualifying (non-exempt) terms. 0 if n < 5."""
    if n < 5:
        return 0
    if n <= 8:
        return _PENSION_TABLE[n]
    return 16_000 + (n - 8) * 2_000


# Associate kinds that can appear as mustering-out benefits.
_BENEFIT_ASSOC_KINDS: frozenset[str] = frozenset({"ally", "contact", "rival", "enemy"})

# Matches "Skill Name N" or "Skill (Spec) N" — e.g. "Advocate 1", "Science (Biology) 2"
_SKILL_LEVEL_RE = re.compile(
    r"^[A-Za-z][A-Za-z\s\-/']*(?:\([A-Za-z\s\-/']+\))?\s+\d+$"
)


def _is_skill_choice_benefit(benefit: str) -> list[str]:
    """Return the list of player-choice options for any 'X or Y [or Z...]' benefit.

    Handles all types of interactive benefit choices:
      - Skill choices: "Advocate 1 or Broker 1"
      - Mixed choices: "SOC +1 or Combat Implant", "Combat Implant or two Ship Shares"
      - Equipment/ship share choices: "Air/Raft or Ship Share"
      - Multi-comma choices: "Free Trader, Safari Ship or Yacht" → all three are choices

    Returns empty list if:
      - No " or " present (not a choice)
      - Has comma with leading stat/char bonus ("INT +1, Independence or Streetwise")
        — those are handled by _apply_benefit's compound-stat handler separately.
    """
    if " or " not in benefit:
        return []
    if "," in benefit:
        # Check if the first comma-separated part is a stat/characteristic bonus.
        # If so, this is a "fixed stat, choice" pattern — let _apply_benefit handle it.
        _first_part = benefit.split(",")[0].strip()
        if re.match(r"^(STR|DEX|END|INT|EDU|SOC|PSI|RES|TER)\s*\+\d+$", _first_part, re.IGNORECASE):
            return []
        # Otherwise it's a multi-option comma+or list: split on ", " and " or "
        raw_parts = re.split(r",\s*|\s+or\s+", benefit)
        parts = [p.strip() for p in raw_parts if p.strip()]
        if len(parts) >= 2:
            return parts
        return []
    parts = [p.strip() for p in benefit.split(" or ")]
    if len(parts) < 2:
        return []
    # All parts must be non-empty
    if any(not p for p in parts):
        return []
    return parts


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

    # Check for species-level psionic block (e.g. Hivers).
    species_data = rules.species().get(character.species_id or "", {})
    if species_data.get("no_psionics"):
        raise ValueError(
            f"{species_data.get('name', 'This species')} cannot develop psionic ability."
        )

    data = rules.psionics()
    pot = data["potential_test"]
    dm = -character.total_terms  # -1 per term

    # Check for species-level psionic bane (e.g. Bwaps).
    species_data = rules.species().get(character.species_id or "", {})
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
    pcs = character.pre_career_status or {}
    free_training = bool(pcs.get("pending_psionic_training"))
    if free_training:
        cost = 0
        # Each talent may only be attempted ONCE during free training (pass OR fail).
        if talent_id in character.psi_free_training_attempts:
            raise ValueError(
                f"You have already attempted {talent['name']} during your free training. "
                "Each talent may only be attempted once."
            )

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

    # Record the attempt during free training so it cannot be retried.
    if free_training:
        character.psi_free_training_attempts.append(talent_id)

    if r.succeeded:
        character.add_skill(talent["skill"], level=0)
        character.psi_trained_talents.append(talent_id)
        log_msg += f": PASSED. Gained {talent['skill']} 0."
    else:
        if free_training:
            log_msg += ": FAILED. This talent cannot be attempted again during free training."
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
        "free_training": free_training,
        "free_training_attempts": list(character.psi_free_training_attempts),
        "character": character.model_dump(),
    }


def _cap_ordinal(n: int) -> str:
    """Return ordinal string: 1 → '1st', 2 → '2nd', etc."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    suffix = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]
    return f"{n}{suffix[n % 10]}"


def _cap_term_ages(overall_term: int, starting_age: int = 18) -> str:
    """Return 'age 18–22' for term 1, 'age 22–26' for term 2, etc."""
    start = starting_age + (overall_term - 1) * 4
    return f"age {start}–{start + 4}"


def _cap_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _cap_join(items: list) -> str:
    """Oxford-comma join."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


# ---------------------------------------------------------------------------
# Capsule narrative helpers — turn raw lifepath log strings into readable prose
# ---------------------------------------------------------------------------

# Sentences containing these are game mechanics, not story — drop them.
_CAPSULE_MECH_RE = re.compile(
    r"(\broll\b|\brolls\b|\brolled\b|DM\s*[+\-±]\d|DM[+\-]|\b\dD\d?\b|\bD66\b|\bD3\b"
    r"|\b\d+\+|\bgain one\b|\bgain a level\b|\bchoose\b|\bpick one\b|\bpick which\b"
    r"|\bbenefit roll|\badvancement roll|\bqualification|\bskill table"
    r"|\bif you (succeed|fail|accept|refuse|agree|wish)\b|\byou may\b|\binstead\b"
    r"|\bautomatically promoted\b|\bnot ejected\b|\bmishaps? table\b"
    r"|\bgain (a|an|one|two|three|d3)\b|\blose\b|\bsuffer\b|\bforfeit|\breduced?\b)",
    re.IGNORECASE,
)

# Log lines that are pure bookkeeping — never narrate these.
_CAPSULE_SKIP_RE = re.compile(
    r"^(event choice:|mishap/event:|event dm chosen|specialty (choice|applied)"
    r"|rank \d+ bonus:|rank bonus:|basic training:|event \[|life event \["
    r"|took the .+ career package)",
    re.IGNORECASE,
)

_CAPSULE_ASSOC_RE = re.compile(r"^Gained (Contact|Ally|Rival|Enemy):\s*(.*)$", re.IGNORECASE)


def _capsule_third_person(text: str) -> str:
    """Convert rulebook second person to third person. 'you' and 'they' share
    verb forms in English, so a word-level swap reads correctly."""
    swaps = [
        (r"\bYou are\b", "They are"), (r"\byou are\b", "they are"),
        (r"\bYou're\b", "They're"), (r"\byou're\b", "they're"),
        (r"\bYourself\b", "Themselves"), (r"\byourself\b", "themselves"),
        (r"\bYours\b", "Theirs"), (r"\byours\b", "theirs"),
        (r"\bYour\b", "Their"), (r"\byour\b", "their"),
        (r"\bYou\b", "They"), (r"\byou\b", "they"),
    ]
    for pat, rep in swaps:
        text = re.sub(pat, rep, text)
    return text


def _capsule_narrative(text: str) -> str:
    """Extract the story from an event/mishap string: keep sentences free of
    dice mechanics, in third person. Falls back to the first sentence cut at
    the first mechanics marker so something always survives."""
    text = re.sub(r"^Life Event\s*[—-]\s*", "", (text or "").strip())
    text = re.sub(r"^[A-Z][a-z]+ Incident:\s*", lambda m: m.group(0), text)  # keep titles
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = [s for s in sentences if s and not _CAPSULE_MECH_RE.search(s)]
    if not kept and sentences:
        # Cut the lead sentence at the first mechanics marker.
        lead = sentences[0]
        m = _CAPSULE_MECH_RE.search(lead)
        if m and m.start() > 20:
            lead = lead[:m.start()].rstrip(" ,;:—-") + "."
            kept = [lead]
    out = " ".join(kept).strip()
    return _capsule_third_person(out) if out else ""


def _capsule_clean_skill(entry: str) -> str:
    """'Basic training: Carouse 0' / 'Gained Melee (blade) 2' / 'Increased Recon
    to 1' → 'Carouse 0' / 'Melee (blade) 2' / 'Recon 1'."""
    e = (entry or "").strip()
    if ":" in e:
        prefix, _, rest = e.partition(":")
        # Keep specialty parentheses intact; only strip the table/source prefix.
        if rest.strip():
            e = rest.strip()
    # Career-package log verbs
    e = re.sub(r"^(gained|already has|took)\s+", "", e, flags=re.IGNORECASE)
    e = re.sub(r"^increased\s+(.+?)\s+to\s+(\d+)$", r"\1 \2", e, flags=re.IGNORECASE)
    return e


def _capsule_assoc_label(kind: str, desc: str) -> Optional[str]:
    """A human label for a gained associate, or None for placeholders."""
    d = (desc or "").strip()
    if not d or re.search(r"unnamed|from mustering", d, re.IGNORECASE):
        return None
    m = re.search(r"\[(.+?)\]", d)
    if m:
        return m.group(1)
    # Drop a leading kind word ("Contact: Foo", "Ally Foo")
    d = re.sub(rf"^{kind}\s*[:\-—]?\s*", "", d, flags=re.IGNORECASE).strip()
    return d or None


def _capsule_descriptors(character: Character) -> list[str]:
    """Up to two characteristic-driven adjectives for the opening line."""
    g = character.characteristics.get
    out: list[str] = []
    if (g("INT") or 0) >= 11:
        out.append("sharp-minded")
    if (g("EDU") or 0) >= 11:
        out.append("highly educated")
    if (g("SOC") or 0) >= 10:
        out.append("well-connected")
    if (g("STR") or 0) >= 9 or (g("END") or 0) >= 9:
        out.append("physically formidable")
    if (g("DEX") or 0) >= 9:
        out.append("quick-handed")
    if sum(1 for k in ("STR", "DEX", "END") if (g(k) or 0) <= 3) >= 2:
        out.append("visibly worn by a hard life")
    return out[:2]


# Varied sentence openers so consecutive terms don't all read identically.
_CAPSULE_TRAINING_OPENERS = [
    "Training that term brought",
    "The years sharpened",
    "They came away with",
    "The service taught them",
    "That stretch added",
]


def generate_capsule(character: Character) -> dict:
    """Produce a multi-paragraph narrative description of the character.

    Compiles the full mission log into prose: dice mechanics are stripped from
    event text, second person becomes third person, placeholder associates are
    summarised rather than dumped, and per-term training reads as a sentence.
    Returned as plain text with double-newline paragraph breaks so the UI
    can split on \\n\\n and render as <p> tags.
    """
    species_data = rules.species().get(character.species_id, {"name": character.species_id})
    species_name = species_data.get("name", character.species_id)
    name = character.name or "An unnamed Traveller"
    paragraphs: list[str] = []

    # ── Opening paragraph ──────────────────────────────────────────────────
    # Build origin clause: prefer specific homeworld; fall back to society name.
    societies_map = {s["id"]: s["name"] for s in rules.list_societies()}
    society_name = societies_map.get(character.society_id or "", "")
    if character.homeworld:
        uwp = f" ({character.homeworld_uwp})" if character.homeworld_uwp else ""
        origin = character.homeworld + uwp
        homeworld_clause = f", originally from {origin},"
    elif society_name and society_name.lower() not in ("other / far domains", "other"):
        homeworld_clause = f", a {society_name} citizen,"
    else:
        homeworld_clause = ""

    terms = character.total_terms
    years = terms * 4

    _cp_packages = (rules.career_packages().get("packages") or {}) if character.career_package_taken else {}

    def _career_display_name(career_id: str) -> str:
        """Resolve a career_id to a human-readable name, checking packages first."""
        if career_id in _cp_packages:
            return _cp_packages[career_id].get("name", career_id.replace("_", " ").title())
        cd = rules.careers().get(career_id, {})
        return cd.get("name", career_id.replace("_", " ").title())

    unique_career_names: list[str] = []
    seen: set[str] = set()
    for cc in character.completed_careers:
        cn = _career_display_name(cc.career_id)
        if cn not in seen:
            unique_career_names.append(cn)
            seen.add(cn)

    if unique_career_names:
        if len(unique_career_names) == 1:
            career_summary = f"a career in the {unique_career_names[0]}"
        else:
            career_summary = (
                "careers spanning the "
                + _cap_join([f"{n}" for n in unique_career_names])
            )
    else:
        career_summary = "a life adrift among the stars"

    _descr = _capsule_descriptors(character)
    _descr_clause = (", ".join(_descr) + " ") if _descr else ""

    # Retirement rank — the last career record with a real title.
    _retire = ""
    for cc in reversed(character.completed_careers):
        if cc.final_rank_title:
            _retire = (
                f" They left the {_career_display_name(cc.career_id)} as "
                f"{_cap_article(cc.final_rank_title)} {cc.final_rank_title}."
            )
            break

    paragraphs.append(
        f"{name} is a {character.age}-year-old {_descr_clause}{species_name}{homeworld_clause} "
        f"who spent {terms} term{'s' if terms != 1 else ''} "
        f"({years} years) building {career_summary}.{_retire}"
    )

    # ── Background package note ────────────────────────────────────────────
    pre_status = character.pre_career_status or {}
    if pre_status.get("track") == "background_package":
        bp_id = pre_status.get("outcome", "")
        bp_data = rules.background_packages().get(bp_id, {})
        bp_name = bp_data.get("name", bp_id.replace("_", " ").title())
        paragraphs.append(
            f"Prior to their career, {name} chose the {bp_name} background package "
            f"instead of traditional education, arriving at career age with specialised "
            f"homeworld skills and Cr{bp_data.get('credits', 0):,} in starting funds."
        )

    # ── Career package note ────────────────────────────────────────────────
    if character.career_package_taken and character.career_package_id:
        cp_data = (rules.career_packages().get("packages") or {}).get(character.career_package_id, {})
        cp_name = cp_data.get("name", character.career_package_id.replace("_", " ").title())
        rank      = cp_data.get("rank", 0)
        rank_title = cp_data.get("rank_title") or ""
        rank_clause = f" at rank {rank}" + (f" ({rank_title})" if rank_title else "") if rank else ""
        paragraphs.append(
            f"{name} took a career package rather than following a traditional career path, "
            f"spending their formative years as a {cp_name}{rank_clause}."
        )

    # ── Per-term career narrative ──────────────────────────────────────────
    _prev_rank_by_career: dict[str, int] = {}
    for term in character.term_history:
        career_def  = rules.careers().get(term.career_id, {})
        career_name = _career_display_name(term.career_id)
        asgn        = career_def.get("assignments", {}).get(term.assignment_id, {})
        # For career packages the assignment_id == career_id, so avoid "Wanderer: Wanderer"
        if asgn:
            asgn_name = asgn.get("name", term.assignment_id)
        elif term.career_id == term.assignment_id:
            asgn_name = "Package"
        else:
            asgn_name = term.assignment_id.replace("_", " ").title()

        age_range = _cap_term_ages(term.overall_term_number)

        _prev_rank = _prev_rank_by_career.get(term.career_id)
        _promoted = _prev_rank is not None and term.rank > _prev_rank
        _prev_rank_by_career[term.career_id] = term.rank

        rank_clause = ""
        if term.rank_title:
            rank_clause = (
                f", newly promoted to {term.rank_title}" if _promoted
                else f" serving as {_cap_article(term.rank_title)} {term.rank_title}"
            )
        elif term.rank:
            rank_clause = (
                f", newly promoted to rank {term.rank}" if _promoted
                else f" at rank {term.rank}"
            )

        commissioned_clause = ""
        if term.commissioned and term.term_number == 1:
            commissioned_clause = " They received a commission."

        frozen_clause = " (This term was spent in cryogenic suspension.)" if term.frozen_watch else ""

        header = (
            f"Term {term.overall_term_number} ({age_range}) — "
            f"{career_name}: {asgn_name}{rank_clause}.{commissioned_clause}{frozen_clause}"
        )

        body_parts: list[str] = []

        # Events — separate associate gains (summarised) from story (cleaned),
        # and drop pure-bookkeeping lines entirely.
        _assoc_gained: dict[str, list[Optional[str]]] = {}
        for evt in (term.events or []):
            evt = evt.strip()
            if not evt:
                continue
            m_assoc = _CAPSULE_ASSOC_RE.match(evt)
            if m_assoc:
                kind = m_assoc.group(1).lower()
                _assoc_gained.setdefault(kind, []).append(
                    _capsule_assoc_label(kind, m_assoc.group(2))
                )
                continue
            if _CAPSULE_SKIP_RE.match(evt):
                continue
            story = _capsule_narrative(evt)
            if story:
                body_parts.append(story)

        if _assoc_gained:
            _assoc_bits: list[str] = []
            for kind in ("ally", "contact", "rival", "enemy"):
                entries = _assoc_gained.get(kind)
                if not entries:
                    continue
                n = len(entries)
                names = [x for x in entries if x]
                plural = {"ally": "allies", "contact": "contacts",
                          "rival": "rivals", "enemy": "enemies"}[kind]
                noun = kind if n == 1 else plural
                count_word = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}.get(n, str(n))
                bit = (f"{_cap_article(noun)} {noun}" if n == 1 else f"{count_word} {noun}")
                if names:
                    bit += f" ({_cap_join(names[:3])})"
                _assoc_bits.append(bit)
            body_parts.append(f"The term left them with {_cap_join(_assoc_bits)}.")

        # Skills gained — strip table prefixes, special-case basic training.
        if term.skills_gained:
            cleaned = []
            _seen_sk: set[str] = set()
            for sgi in term.skills_gained:
                cs = _capsule_clean_skill(sgi)
                if cs and cs.lower() not in _seen_sk:
                    cleaned.append(cs)
                    _seen_sk.add(cs.lower())
            if cleaned:
                if term.basic_training:
                    body_parts.append(f"Basic training grounded them in {_cap_join(cleaned)}.")
                else:
                    opener = _CAPSULE_TRAINING_OPENERS[
                        (term.overall_term_number - 1) % len(_CAPSULE_TRAINING_OPENERS)
                    ]
                    body_parts.append(f"{opener} {_cap_join(cleaned)}.")

        # Mishap — narrate it as the term's turning point.
        if term.mishap:
            m_story = _capsule_narrative(term.mishap)
            if m_story:
                body_parts.append(f"The term ended badly: {m_story[:1].lower()}{m_story[1:]}")
            else:
                body_parts.append("The term ended badly.")

        if body_parts:
            term_text = header + " " + " ".join(body_parts)
        else:
            term_text = header

        paragraphs.append(term_text)

    # ── Muster-out paragraph ──────────────────────────────────────────────
    muster_parts: list[str] = []
    if character.credits:
        muster_parts.append(f"Cr{character.credits:,} in credits")
    if character.ship_shares:
        ss = character.ship_shares
        muster_parts.append(f"{ss} ship share{'s' if ss != 1 else ''}")
    if character.equipment:
        eq_names = [e.name for e in character.equipment[:6]]
        muster_parts.append("equipment including " + _cap_join(eq_names))
    if character.pension_per_year:
        muster_parts.append(f"a pension of Cr{character.pension_per_year:,}/year")
    if character.medical_debt:
        muster_parts.append(f"Cr{character.medical_debt:,} in outstanding medical debt")
    if character.anagathics_addicted:
        muster_parts.append("a dependency on anagathic treatments")

    ally_count = sum(1 for a in character.associates if a.kind == "ally")
    contact_count = sum(1 for a in character.associates if a.kind == "contact")
    rival_count = sum(1 for a in character.associates if a.kind == "rival")
    enemy_count = sum(1 for a in character.associates if a.kind == "enemy")

    assoc_parts: list[str] = []
    if ally_count:
        assoc_parts.append(f"{ally_count} {'ally' if ally_count == 1 else 'allies'}")
    if contact_count:
        assoc_parts.append(f"{contact_count} {'contact' if contact_count == 1 else 'contacts'}")
    if rival_count:
        assoc_parts.append(f"{rival_count} {'rival' if rival_count == 1 else 'rivals'}")
    if enemy_count:
        assoc_parts.append(f"{enemy_count} {'enemy' if enemy_count == 1 else 'enemies'}")

    muster_sentence = ""
    if muster_parts:
        muster_sentence = f"Mustering out, {name} carries {_cap_join(muster_parts)}."
    else:
        muster_sentence = f"{name} mustered out with little to show in material terms."

    assoc_sentence = ""
    if assoc_parts:
        assoc_sentence = f" Along the way they accumulated {_cap_join(assoc_parts)}."

    paragraphs.append(muster_sentence + assoc_sentence)

    # ── Closing flavour ───────────────────────────────────────────────────
    _named_enemy = next(
        (lbl for a in character.associates if a.kind == "enemy"
         for lbl in [_capsule_assoc_label("enemy", a.description)] if lbl),
        None,
    )
    if enemy_count or rival_count:
        _small = {1: None, 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
        _grudge_bits = []
        if enemy_count:
            _grudge_bits.append("an enemy" if enemy_count == 1
                                else f"{_small.get(enemy_count, enemy_count)} enemies")
        if rival_count:
            _grudge_bits.append("a rival" if rival_count == 1
                                else f"{_small.get(rival_count, rival_count)} rivals")
        _closing = f"Not everyone remembers them fondly — {_cap_join(_grudge_bits)} still hold a grudge"
        if _named_enemy:
            _closing += f", the {_named_enemy} chief among them"
        paragraphs.append(_closing + ".")
    elif ally_count >= 3:
        paragraphs.append(
            "Few Travellers leave the service so well liked — wherever they dock, "
            "someone owes them a drink."
        )

    # ── Skills paragraph ──────────────────────────────────────────────────
    skills_sorted = sorted(
        character.skills, key=lambda s: (s.level, s.name), reverse=True
    )
    notable = [
        (f"{s.name} ({s.speciality})" if s.speciality else s.name) + f" {s.level}"
        for s in skills_sorted[:6]
        if s.level > 0
    ]
    if notable:
        paragraphs.append(f"Notable skills upon retirement: {', '.join(notable)}.")

    capsule = "\n\n".join(paragraphs)
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


def _stat_cap(species_data: dict, stat: str) -> int:
    """Return the effective maximum for *stat* for this species.

    Uses ``characteristic_maximum_overrides`` for per-stat raises above the
    species global cap (e.g. Ghenani STR 17, Murian STR/END 18), otherwise
    falls back to ``characteristic_maximum`` (default 15).
    """
    overrides: dict = species_data.get("characteristic_maximum_overrides") or {}
    if stat in overrides:
        return int(overrides[stat])
    return int(species_data.get("characteristic_maximum", 15))


def _enforce_characteristic_caps(character: Character, species_data: dict) -> list[str]:
    """Reduce any characteristics that exceed the species-defined per-stat caps.

    Species may define ``characteristic_caps`` as a dict mapping stat name to
    an integer maximum (e.g. ``{"EDU": 7}`` for Martians, ``{"END": 10}`` for
    Segani).  Any stat currently above its cap is reduced to the cap value.

    Returns a list of human-readable messages for each stat that was clamped.
    """
    caps: dict = species_data.get("characteristic_caps", {}) or {}
    clamped: list[str] = []
    for stat, cap in caps.items():
        current = character.characteristics.get(stat)
        if current is not None and current > cap:
            character.characteristics.set(stat, cap)
            clamped.append(f"{stat} reduced to {cap} (was {current})")
    return clamped


def apply_species(character: Character, species_id: str) -> dict:
    """Apply species modifiers and record traits."""
    species_data = rules.species().get(species_id)
    if species_data is None:
        raise ValueError(f"Unknown species: {species_id}")

    # Caste-choice species (e.g. Souggvuez): return a pending choice immediately
    # without applying anything — the player must pick their caste first, then
    # the UI calls apply_species again with the specific caste variant ID.
    if species_data.get("caste_choice"):
        caste_pending = {
            "kind": "species_caste_choice",
            "species_name": species_data.get("name", ""),
            "options": species_data.get("caste_options", []),
        }
        return {
            "character": character.model_dump(),
            "pending_choice": caste_pending,
            "applied": {},
        }

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

    # Apply species-specific starting age if defined (e.g. Dolphins start at 12)
    starting_age = species_data.get("starting_age")
    if starting_age is not None:
        character.age = int(starting_age)

    if applied:
        mods_str = ", ".join(f"{k} {v['delta']:+d}" for k, v in applied.items())
        character.log(f"Applied species: {species_data['name']} ({mods_str})")
    else:
        character.log(f"Applied species: {species_data['name']}")

    # Vargr Extents: CHA replaces SOC. Re-roll SOC as 1D+2 (not the standard 2D).
    if species_data.get("uses_cha"):
        cha_roll = dice.roll_d6() + 2
        old_soc = character.characteristics.SOC
        character.characteristics.set("SOC", cha_roll)
        character.log(f"CHA (SOC) re-rolled as 1D+2 = {cha_roll} (was {old_soc})")

    # custom_characteristic_rolls: species-specific roll formulas (e.g. Zhdianshe STR fixed:1,
    # DEX 2D+2).  Supports "fixed:N" (always exactly N) and any standard dice notation.
    # PSI is intentionally skipped here — it is handled by the rolls_psi_at_start block below.
    custom_roll_map = species_data.get("custom_characteristic_rolls", {})
    if custom_roll_map:
        custom_parts: list[str] = []
        for stat, formula in custom_roll_map.items():
            if stat.upper() == "PSI":
                continue  # handled via rolls_psi_at_start
            if isinstance(formula, str) and formula.startswith("fixed:"):
                fixed_val = int(formula.split(":", 1)[1])
                character.characteristics.set(stat, fixed_val)
                custom_parts.append(f"{stat} = {fixed_val} (fixed)")
            else:
                cr = dice.roll(str(formula))
                character.characteristics.set(stat, cr.total)
                custom_parts.append(f"{stat} ({formula}) = {cr.total}")
        if custom_parts:
            character.log(
                f"{species_data['name']} custom characteristic rolls: "
                + ", ".join(custom_parts)
            )

    # Boldness (BOL) — the Za'tachk seventh characteristic (AoCS Vol. 4).
    # Roll the formula (1D+1), then apply the caste modifier; min 1.
    bol_formula = species_data.get("boldness_roll")
    if bol_formula:
        bol_r = dice.roll(str(bol_formula))
        bol_mod = int(species_data.get("boldness_modifier", 0))
        character.boldness = max(1, bol_r.total + bol_mod)
        _mod_str = f" {bol_mod:+d} (caste)" if bol_mod else ""
        character.log(
            f"{species_data['name']} Boldness (BOL): {bol_formula}={bol_r.total}{_mod_str} "
            f"= {character.boldness}"
        )

    # Species with custom characteristic dice (e.g. Ladybug, Selenite): re-roll those
    # stats using the species-defined formulas immediately after species is applied.
    # Droyne has its own caste-system path that handles characteristic_dice separately.
    char_dice_map = species_data.get("characteristic_dice", {})
    if char_dice_map and not species_data.get("droyne_caste_system"):
        reroll_parts: list[str] = []
        for stat, formula in char_dice_map.items():
            if formula is None:
                character.characteristics.set(stat, 0)
                reroll_parts.append(f"{stat} → 0")
            else:
                cr = dice.roll(formula)
                character.characteristics.set(stat, cr.total)
                reroll_parts.append(f"{stat} ({formula}) = {cr.total}")
        character.log(
            f"{species_data['name']} characteristic re-roll: "
            + ", ".join(reroll_parts)
        )

    # Hiver: RES replaces SOC, rolled as 1D+6 (range 7–12) when the species is chosen.
    if species_data.get("res_replaces_soc"):
        res_r = dice.roll("1D+6")
        old_soc = character.characteristics.SOC
        character.characteristics.set("SOC", res_r.total)
        character.log(f"RES (SOC) rolled as 1D+6 = {res_r.total} (was {old_soc})")

    # Store species forbidden skills on the character so add_skill can enforce them.
    forbidden = species_data.get("forbidden_skills", []) or []
    if forbidden:
        character.forbidden_skills = list(forbidden)
        character.log(f"Species forbidden skills: {', '.join(forbidden)}")

    # Extra background skills granted unconditionally by species (e.g. Caprisap: Astrogation 0).
    for extra_skill in (species_data.get("extra_background_skills", []) or []):
        sn, spec = _split_skill_speciality(extra_skill.strip())
        character.add_skill(sn, level=0, speciality=spec)
        display = f"{sn} ({spec})" if spec else sn
        character.log(f"Species extra background skill: {display} 0")

    # Auto-grant species background skills (e.g. Vargr: Melee (Infighting) 0).
    species_bg_skills = species_data.get("background_skills", [])
    for skill_entry in species_bg_skills:
        # Parse "Skill (Speciality) N" — default level 0
        level = 0
        entry = skill_entry.strip()
        m = re.search(r"\s+(\d+)\s*$", entry)
        if m:
            level = int(m.group(1))
            entry = entry[: m.start()].strip()
        sn, spec = _split_skill_speciality(entry)
        character.add_skill(sn, level=level, speciality=spec)
        display = f"{sn} ({spec})" if spec else sn
        character.log(f"Species background skill: {display} {level}")

    # Auto-grant species starting equipment (e.g. natural armour items).
    # Each entry may have: name (str), notes (str), protection (int).
    for eq_entry in (species_data.get("starting_equipment", []) or []):
        eq_item = Equipment(
            name=eq_entry["name"],
            notes=eq_entry.get("notes"),
            protection=eq_entry.get("protection"),
        )
        # Avoid duplicating on re-apply (species switch etc.)
        already = any(e.name == eq_item.name for e in character.equipment)
        if not already:
            character.equipment.append(eq_item)
            prot_str = f" (Protection +{eq_item.protection})" if eq_item.protection else ""
            character.log(f"Species starting equipment: {eq_item.name}{prot_str}")

    # Enforce per-stat characteristic caps defined by the species (e.g. Martian EDU max 7).
    _apply_cap_msgs = _enforce_characteristic_caps(character, species_data)
    for msg in _apply_cap_msgs:
        character.log(f"Species characteristic cap applied: {msg}")

    # Zhodani (and any future species with psi_ruleset_choice): present a pending
    # choice between the Sourcebook rule (guaranteed 1D+6 PSI) and the Core Rulebook
    # optional rule (2D+DM vs 9+, chance of failure).  Both paths live in
    # resolve_zhodani_psi_choice(); we defer here and let the player decide.
    psi_ruleset_pending: dict | None = None
    if species_data.get("psi_ruleset_choice") and not character.psi_tested:
        psi_ruleset_pending = {
            "kind": "zhodani_psi_ruleset",
            "options": [
                {
                    "id": "sourcebook",
                    "label": "Sourcebook (AoCS)",
                    "description": (
                        "All Zhodani have PSI. Roll 1D+6 — guaranteed PSI 7-12. "
                        "Noble/Intendant caste system applies; Nobles and Intendants "
                        "undergo psionic talent training before careers."
                    ),
                },
                {
                    "id": "core_rulebook",
                    "label": "Core Rulebook optional",
                    "description": (
                        "Childhood PSI test: 2D+1 vs 9+. "
                        "Pass = PSI (raw dice, not counting DM); Fail = PSI 0. "
                        "PSI 8+ grants SOC+1 (Intendant caste)."
                    ),
                },
            ],
        }
        character.pending_life_event_choice = psi_ruleset_pending
    else:
        # Non-choice psionic society: roll 2D+DM vs 9+. PSI = raw dice on success.
        # (No species currently uses this path; kept for future data-driven species.)
        if species_data.get("psionic_society") and not character.psi_tested:
            test_dm = int(species_data.get("psionic_society_test_dm", 0))
            soc_bonus_threshold = int(species_data.get("psionic_society_soc_bonus_psi", 0))
            test_r = dice.roll("2D", modifier=test_dm, target=9)
            character.psi_tested = True
            if test_r.succeeded:
                character.psi = test_r.raw_total  # PSI = raw dice (MgT rule)
                character.log(
                    f"Psionic society childhood test: 2D{test_dm:+d} = {test_r.total} [PASS] — PSI {character.psi}"
                )
                if soc_bonus_threshold and character.psi >= soc_bonus_threshold:
                    old_soc = character.characteristics.get("SOC") or 0
                    character.characteristics.set("SOC", old_soc + 1)
                    character.log(
                        f"PSI {character.psi} >= {soc_bonus_threshold} — Noble/Intendant caste: SOC +1 (now {old_soc + 1})"
                    )
            else:
                character.log(
                    f"Psionic society childhood test: 2D{test_dm:+d} = {test_r.total} [FAIL] — PSI 0"
                )

        # Sourcebook Zhodani: unconditionally roll PSI using the species psi_roll formula.
        # This is the full Noble/Intendant/Prole class system with guaranteed psionic ability.
        # Skipped when psi_ruleset_choice deferred above.
    if species_data.get("rolls_psi_at_start") and not psi_ruleset_pending:
        psi_dice = species_data.get("psi_roll", "2D")
        psi_r = dice.roll(psi_dice)
        character.psi = psi_r.total
        character.psi_tested = True
        character.log(f"{species_data['name']}: PSI rolled {psi_dice} = {psi_r.total}")
        # psi_linked_soc: starting SOC equals starting PSI (e.g. Zhdianshe).
        # SOC can drop below PSI later but never exceed it.
        if species_data.get("psi_linked_soc"):
            character.characteristics.set("SOC", character.psi)
            character.log(f"SOC set to PSI ({character.psi}) — psi_linked_soc rule")
        # Apply characteristic adjustments based on PSI / SOC / EDU interplay.
        sp_max = int(species_data.get("characteristic_maximum", 15))
        for adj in species_data.get("characteristic_adjustments", []):
            cond = adj.get("condition", "")
            psi_val = character.psi or 0
            soc_val = character.characteristics.get("SOC")
            edu_val = character.characteristics.get("EDU")
            if cond == "psi_gte_9_and_soc_lte_9":
                if psi_val >= 9 and soc_val <= 9:
                    character.characteristics.set("SOC", 10)
                    character.log(adj.get("description", "SOC raised to 10"))
            elif cond == "edu_gt_soc":
                soc_val = character.characteristics.get("SOC")  # may have been updated
                if edu_val > soc_val:
                    character.characteristics.set("EDU", soc_val)
                    character.log(adj.get("description", f"EDU lowered to {soc_val}"))
            elif cond == "edu_lte_7_and_soc_gte_10":
                soc_val = character.characteristics.get("SOC")  # may have been updated
                edu_val = character.characteristics.get("EDU")   # may have been updated
                if edu_val <= 7 and soc_val >= 10:
                    character.characteristics.set("EDU", 8)
                    character.log(adj.get("description", "EDU raised to 8"))

        # After characteristic adjustments: enter psionic training phase if applicable.
        if species_data.get("psionic_training_at_start"):
            if canonical_id == "zhodani":
                # Zhodani: only Nobles and Intendants train.
                zclass = _zhodani_class(character.characteristics.get("SOC") or 0)
                if zclass in ("noble", "intendant"):
                    character.phase = "zhodani_training"
                    character.log(
                        f"Zhodani {zclass.capitalize()} — begins psionic talent training before careers."
                    )
            else:
                # Non-Zhodani species (e.g. Zhdianshe): apply auto-talents immediately,
                # then enter training for any remaining interactive talent checks.
                training_table = species_data.get("psionic_training_table", {})
                for auto_t in training_table.get("auto_talents", []):
                    t_name = auto_t["name"]
                    t_level = int(auto_t.get("level", 0))
                    character.add_skill(t_name, level=t_level)
                    character.log(
                        f"{species_data['name']} childhood psionics: auto-granted {t_name} {t_level}"
                    )
                if training_table.get("talents"):
                    character.phase = "zhodani_training"
                    character.log(
                        f"{species_data['name']} — begins psionic talent training before careers."
                    )

    # Droyne caste system: re-roll characteristics using species-defined dice,
    # roll caste (1D), apply casting bonus, and apply caste modifiers.
    droyne_caste_result: dict | None = None
    if species_data.get("droyne_caste_system"):
        char_dice_map = species_data.get("characteristic_dice", {})
        if char_dice_map:
            char_rerolls: dict[str, int] = {}
            for stat, formula in char_dice_map.items():
                if formula is None:
                    # SOC not used by Droyne — set to 0
                    character.characteristics.set(stat, 0)
                    char_rerolls[stat] = 0
                elif formula.upper() == "PSI" or stat.upper() == "PSI":
                    # PSI rolled as 2D; store separately
                    psi_r = dice.roll("2D")
                    character.psi = psi_r.total
                    character.psi_tested = True
                    char_rerolls["PSI"] = psi_r.total
                else:
                    # Parse "NdX+M" or "ND+M" format using the dice engine
                    cr = dice.roll(formula)
                    character.characteristics.set(stat, cr.total)
                    char_rerolls[stat] = cr.total
            character.log(
                "Droyne characteristics (1D+1 each): "
                + ", ".join(f"{k} {v}" for k, v in char_rerolls.items())
            )

        # Apply the Iskyar casting bonus (+1 to each physical/mental stat from ritual)
        casting_bonus = species_data.get("droyne_casting_bonus", {})
        casting_parts: list[str] = []
        for stat, bonus in casting_bonus.items():
            if bonus and stat.upper() != "PSI":
                old = character.characteristics.get(stat) or 0
                character.characteristics.set(stat, old + bonus)
                casting_parts.append(f"{stat} {old}→{old + bonus}")
        if casting_parts:
            character.log(f"Iskyar casting bonus: {', '.join(casting_parts)}")

        # Roll 1D for caste
        caste_table = species_data.get("droyne_caste_table", {})
        caste_r = dice.roll("1D")
        caste_name = caste_table.get(str(caste_r.total), "worker")
        character.droyne_caste = caste_name
        character.droyne_caste_number = caste_r.total
        character.log(f"Droyne caste roll: 1D={caste_r.total} → {caste_name.capitalize()}")

        # Apply caste stat modifiers
        caste_mods = species_data.get("droyne_caste_mods", {}).get(caste_name, {})
        caste_mod_parts: list[str] = []
        for stat, delta in caste_mods.items():
            if delta:
                old = character.characteristics.get(stat) or 0
                character.characteristics.set(stat, old + delta)
                caste_mod_parts.append(f"{stat} {old}→{old + delta} ({delta:+d})")
        if caste_mod_parts:
            character.log(f"Caste ({caste_name}) modifiers: {', '.join(caste_mod_parts)}")
        character.droyne_caste_mods_applied = True

        droyne_caste_result = {
            "caste": caste_name,
            "caste_number": caste_r.total,
            "caste_mods": caste_mods,
        }

    # Hiver Federation: roll 2D on nest table to determine home nest type.
    # Nest type determines the Senior and Manipulator advancement bonuses.
    hiver_nest_result: dict | None = None
    if species_data.get("hiver_species"):
        nest_table = species_data.get("hiver_nest_table", {})
        if nest_table:
            nest_r = dice.roll("2D")
            nest_type = nest_table.get(str(nest_r.total), "generalist")
            character.hiver_nest_type = nest_type
            character.log(f"Hiver nest type: 2D={nest_r.total} → {nest_type.capitalize()}")
            hiver_nest_result = {"nest_type": nest_type, "roll": nest_r.to_dict()}

    # Aslan Hierate: skip background/pre_career phases; go directly to aslan_setup
    needs_aslan_setup = species_data.get("uses_clan_shares", False)
    if needs_aslan_setup:
        character.phase = "aslan_setup"
        # Ensure TER characteristic is present (start at 0; rolled during begin_aslan_setup)
        if "TER" not in character.extra_characteristics:
            character.extra_characteristics["TER"] = 0

    needs_zhodani_training = character.phase == "zhodani_training"

    # Species skill grant choice (e.g. Dynchia: gain Gun Combat 1 OR Melee 1).
    # Only fires when no other pending choice is already set.
    species_skill_choice_pending: dict | None = None
    skill_grant_choices = species_data.get("species_skill_grant_choice", [])
    if skill_grant_choices and not character.pending_life_event_choice:
        skill_grant_prompt = species_data.get(
            "species_skill_grant_prompt", "Choose a skill granted by your species:"
        )
        species_skill_choice_pending = {
            "kind": "species_skill_grant",
            "prompt": skill_grant_prompt,
            "options": [
                {"id": s, "label": s, "description": f"Gain {s}"}
                for s in skill_grant_choices
            ],
        }
        character.pending_life_event_choice = species_skill_choice_pending

    return {
        "applied": applied,
        "traits": character.traits,
        "needs_aslan_setup": needs_aslan_setup,
        "needs_zhodani_training": needs_zhodani_training,
        "zhodani_class": _zhodani_class(character.characteristics.get("SOC") or 0) if character.species_id == "zhodani" else None,
        "droyne_caste": droyne_caste_result,
        "hiver_nest": hiver_nest_result,
        "pending_choice": psi_ruleset_pending or species_skill_choice_pending,
        "character": character.model_dump(),
    }


def resolve_zhodani_psi_choice(character: Character, ruleset: str) -> dict:
    """Resolve the Zhodani PSI ruleset choice set by apply_species.

    ruleset values:
      "sourcebook"    — Sourcebook (AoCS): guaranteed 1D+6 PSI, caste system,
                        Nobles/Intendants enter psionic training phase.
      "core_rulebook" — Core Rulebook optional: 2D+1 vs 9+; PSI = raw dice on
                        pass, PSI 0 on fail; PSI 8+ grants SOC+1.
    """
    pending = character.pending_life_event_choice
    if not pending or pending.get("kind") != "zhodani_psi_ruleset":
        raise ValueError("No pending Zhodani PSI ruleset choice to resolve.")

    species_data = rules.species().get(character.species_id or "", {})
    character.pending_life_event_choice = None

    if ruleset == "sourcebook":
        psi_dice = species_data.get("psi_roll", "1D+6")
        psi_r = dice.roll(psi_dice)
        character.psi = psi_r.total
        character.psi_tested = True
        character.log(f"Zhodani PSI (Sourcebook): {psi_dice} = {psi_r.total}")

        sp_max = int(species_data.get("characteristic_maximum", 15))
        for adj in species_data.get("characteristic_adjustments", []):
            cond = adj.get("condition", "")
            psi_val = character.psi or 0
            soc_val = character.characteristics.get("SOC")
            edu_val = character.characteristics.get("EDU")
            if cond == "psi_gte_9_and_soc_lte_9":
                if psi_val >= 9 and soc_val <= 9:
                    character.characteristics.set("SOC", 10)
                    character.log(adj.get("description", "SOC raised to 10"))
            elif cond == "edu_gt_soc":
                soc_val = character.characteristics.get("SOC")
                if edu_val > soc_val:
                    character.characteristics.set("EDU", soc_val)
                    character.log(adj.get("description", f"EDU lowered to {soc_val}"))
            elif cond == "edu_lte_7_and_soc_gte_10":
                soc_val = character.characteristics.get("SOC")
                edu_val = character.characteristics.get("EDU")
                if edu_val <= 7 and soc_val >= 10:
                    character.characteristics.set("EDU", 8)
                    character.log(adj.get("description", "EDU raised to 8"))

        if species_data.get("psionic_training_at_start"):
            zclass = _zhodani_class(character.characteristics.get("SOC") or 0)
            if zclass in ("noble", "intendant"):
                character.phase = "zhodani_training"
                character.log(
                    f"Zhodani {zclass.capitalize()} — begins psionic talent training before careers."
                )

    elif ruleset == "core_rulebook":
        test_dm = int(species_data.get("psionic_society_test_dm", 1))
        soc_bonus_threshold = int(species_data.get("psionic_society_soc_bonus_psi", 8))
        test_r = dice.roll("2D", modifier=test_dm, target=9)
        character.psi_tested = True
        if test_r.succeeded:
            character.psi = test_r.raw_total  # PSI = raw dice (MgT rule: PSI = dice, not dice+DM)
            character.log(
                f"Zhodani PSI (Core Rulebook): 2D{test_dm:+d} = {test_r.total} [PASS] — PSI {character.psi}"
            )
            if soc_bonus_threshold and character.psi >= soc_bonus_threshold:
                old_soc = character.characteristics.get("SOC") or 0
                character.characteristics.set("SOC", old_soc + 1)
                character.log(
                    f"PSI {character.psi} >= {soc_bonus_threshold} — Intendant caste: SOC +1 (now {old_soc + 1})"
                )
        else:
            character.log(
                f"Zhodani PSI (Core Rulebook): 2D{test_dm:+d} = {test_r.total} [FAIL] — PSI 0"
            )
    else:
        raise ValueError(f"Unknown Zhodani PSI ruleset: '{ruleset}'")

    needs_zhodani_training = character.phase == "zhodani_training"
    zhodani_class = _zhodani_class(character.characteristics.get("SOC") or 0)

    return {
        "ruleset": ruleset,
        "psi": character.psi,
        "psi_tested": character.psi_tested,
        "needs_zhodani_training": needs_zhodani_training,
        "zhodani_class": zhodani_class,
        "character": character.model_dump(),
    }


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


def zhodani_train_talent(character: Character, talent_name: str) -> dict:
    """Attempt to learn one psionic talent during Zhodani pre-career training.

    Roll 2D + PSI DM + talent DM − (number of talents already attempted this
    session) vs 8+.  On success the talent is added at level 0 as a skill.
    On failure the talent is simply not gained.

    The cumulative penalty is tracked by counting entries in psi_trained_talents
    that contain the suffix "/attempted" OR successful gains — i.e. the number
    of checks made so far (both passes and fails).  We store attempted-but-failed
    talents with a trailing "/failed" marker so they can be shown in the UI but
    distinguished from gained talents.
    """
    if character.phase != "zhodani_training":
        raise ValueError("Not in psionic training phase")

    # Load talent table from the character's own species (works for Zhodani AND others)
    sp_id = character.species_id or "zhodani"
    species_data = rules.species().get(sp_id, {})
    talent_table = species_data.get("psionic_training_table", {})

    # Zhodani-only gate: Proles do not train
    if sp_id == "zhodani":
        zclass = _zhodani_class(character.characteristics.get("SOC") or 0)
        if zclass == "prole":
            raise ValueError("Proles do not undergo psionic training")

    talents_list = talent_table.get("talents", [])
    talent_entry = next((t for t in talents_list if t["name"].lower() == talent_name.lower()), None)
    if talent_entry is None:
        raise ValueError(f"Unknown talent: {talent_name}")

    # Enforce required_next: species may require a specific talent to be attempted first
    required_next = talent_table.get("required_next")
    if required_next:
        req_name = required_next["name"]
        already_attempted_req = any(
            t == req_name or t == f"{req_name}/failed"
            for t in (character.psi_trained_talents or [])
        )
        if not already_attempted_req and talent_name.lower() != req_name.lower():
            raise ValueError(
                f"Must attempt {req_name} before other talents "
                f"(species training rule)."
            )

    # Count attempts already made this session (both successes and failures)
    attempts_so_far = sum(
        1 for t in (character.psi_trained_talents or [])
        if not t.endswith("/pending")
    )

    psi_dm = dice.characteristic_dm(character.psi)
    talent_dm = int(talent_entry.get("dm", 0))
    cumulative_dm = -attempts_so_far
    total_dm = psi_dm + talent_dm + cumulative_dm

    r = dice.roll("2D", modifier=total_dm, target=8)
    succeeded = bool(r.succeeded)

    # required_next talent may be gained at a higher level than 0
    success_level = 0
    if succeeded and required_next and talent_name.lower() == required_next["name"].lower():
        success_level = int(required_next.get("level", 0))

    dm_parts = []
    if psi_dm != 0:
        dm_parts.append(f"PSI DM{psi_dm:+d}")
    if talent_dm != 0:
        dm_parts.append(f"talent DM{talent_dm:+d}")
    if cumulative_dm != 0:
        dm_parts.append(f"cumulative DM{cumulative_dm:+d}")
    dm_note = f" [{', '.join(dm_parts)}]" if dm_parts else ""

    if succeeded:
        character.add_skill(talent_name, level=success_level)
        character.psi_trained_talents.append(talent_name)
        character.log(
            f"Psionic training: {talent_name} — "
            f"2D{total_dm:+d}=8+ roll: {r.total}{dm_note} — GAINED (level {success_level})"
        )
    else:
        character.psi_trained_talents.append(f"{talent_name}/failed")
        character.log(
            f"Psionic training: {talent_name} — "
            f"2D{total_dm:+d}=8+ roll: {r.total}{dm_note} — failed"
        )

    return {
        "talent": talent_name,
        "roll": r.to_dict(),
        "succeeded": succeeded,
        "success_level": success_level,
        "psi_dm": psi_dm,
        "talent_dm": talent_dm,
        "cumulative_dm": cumulative_dm,
        "attempts_so_far": attempts_so_far,
        "character": character.model_dump(),
    }


def finish_zhodani_training(character: Character) -> dict:
    """End psionic training and advance to the background-skills phase."""
    if character.phase != "zhodani_training":
        raise ValueError("Not in Zhodani training phase")
    character.phase = "background"
    gained = [t for t in (character.psi_trained_talents or []) if not t.endswith("/failed")]
    if gained:
        character.log(
            f"Zhodani psionic training complete — talents gained: {', '.join(gained)}"
        )
    else:
        character.log("Zhodani psionic training complete — no talents gained.")
    return {"character": character.model_dump()}


def set_background_skills(character: Character, chosen: list[str]) -> dict:
    """Grant the selected background skills at level 0."""
    edu_dm = dice.characteristic_dm(character.characteristics.EDU)
    allowed_count = max(0, edu_dm + 3)
    if len(chosen) > allowed_count:
        raise ValueError(f"Too many background skills chosen: {len(chosen)} (allowed {allowed_count})")

    valid = set(rules.background_skills()["skills"])
    for skill_name in chosen:
        # Accept "Skill (Specialty)" when the base skill is in the valid list
        base = skill_name.split(" (")[0].strip()
        if skill_name not in valid and base not in valid:
            raise ValueError(f"Not a background skill: {skill_name}")
        sn, spec = _split_skill_speciality(skill_name)
        character.add_skill(sn, level=0, speciality=spec)

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


def apply_background_package(
    character: Character,
    package_id: str,
    skill_choices: dict[str, str] | None = None,
) -> dict:
    """
    Apply a Traveller Companion background package instead of education skills
    and pre-career education.  Sets age to 22, grants all package skills,
    applies stat modifiers, adds starting credits and equipment, then
    transitions directly to the career phase.

    skill_choices maps skill name → chosen speciality for any skills marked
    "any": true in the JSON (e.g. {"Profession": "merchant", "Science": "physics"}).
    """
    if character.phase != "background":
        raise ValueError(f"Background packages can only be chosen during the background phase (currently: {character.phase})")

    packages = rules.background_packages()
    pkg = packages.get(package_id)
    if pkg is None:
        raise ValueError(f"Unknown background package: {package_id!r}")

    if skill_choices is None:
        skill_choices = {}

    # ── Stat modifiers ────────────────────────────────────────────────────────
    for stat, mod in pkg.get("stat_mods", {}).items():
        current = getattr(character.characteristics, stat, 0)
        setattr(character.characteristics, stat, max(1, current + mod))

    # ── Skills ────────────────────────────────────────────────────────────────
    for sk in pkg["skills"]:
        name  = sk["name"]
        level = sk["level"]
        spec  = sk.get("speciality")

        if sk.get("any"):
            chosen_spec = skill_choices.get(name, "").strip()
            if not chosen_spec:
                raise ValueError(f"No speciality chosen for {name} (any) in package '{pkg['name']}'")
            spec = _SPEC_LOOKUP.get(chosen_spec.lower(), chosen_spec)
        elif sk.get("options"):
            chosen_spec = skill_choices.get(name, "").strip()
            if not chosen_spec:
                raise ValueError(f"No speciality chosen for {name} in package '{pkg['name']}'")
            allowed = [o.lower() for o in sk["options"]]
            if chosen_spec.lower() not in allowed:
                raise ValueError(f"Invalid speciality '{chosen_spec}' for {name} — must be one of {sk['options']}")
            spec = _SPEC_LOOKUP.get(chosen_spec.lower(), chosen_spec)

        character.add_skill(name, level=level, speciality=spec, fixed_level=(level > 0))

    # ── Credits & equipment ───────────────────────────────────────────────────
    credit_bonus = pkg.get("credits", 0)
    character.credits += credit_bonus

    for item_name in pkg.get("equipment", []):
        if item_name:
            character.equipment.append(Equipment(name=item_name))

    # ── Age & phase ───────────────────────────────────────────────────────────
    character.age = 22
    character.pre_career_terms = 1          # counts as one pre-career block
    character.pre_career_status = {
        "track": "background_package",
        "stage": "completed",
        "outcome": package_id,
    }

    stat_parts = [
        f"{s}{'+' if v > 0 else ''}{v}"
        for s, v in pkg.get("stat_mods", {}).items()
    ]
    character.log(
        f"Background Package — {pkg['name']}: "
        f"{'  '.join(stat_parts) or 'no stat changes'}  |  Cr{credit_bonus:,} starting credits"
    )
    character.phase = "career"

    return {"character": character.model_dump()}


# ============================================================
# Phase 2 (alternate): Career Packages
# ============================================================


def apply_career_package(
    character: Character,
    package_id: str,
    skill_choices: dict[str, str] | None = None,
    career_choice: str = "rank_4_only",
    career_skill: str | None = None,
    career_skill_speciality: str | None = None,
    career_3skills: list[dict] | None = None,
    traveller_pair_id: int = 1,
    traveller_specialties: dict[str, str] | None = None,
    benefit_id: int = 1,
) -> dict:
    """
    Apply a career package instead of normal careers.  Applies all package
    skills/stats/benefits, processes the three finalising choices, rolls d3
    for age, then transitions to skill_package phase.

    career_choice:
      "boost_one_to_4"  → career_skill + career_skill_speciality (optional)
      "boost_three_by_1"→ career_3skills = [{"name":..., "speciality":...}, ...]
      "rank_4_only"     → no extra input, just rank raised to 4

    traveller_specialties maps skill key/name → chosen specialty for pair skills
    with "any": true (e.g. {"Gunner": "turret", "Electronics_ts": "computers"}).
    """
    if character.phase != "career":
        raise ValueError(
            f"Career packages can only be chosen at the start of the career phase "
            f"(currently: {character.phase})"
        )
    if character.total_terms != 0:
        raise ValueError("Career packages can only be taken as your first and only career.")

    cp_data = rules.career_packages()
    packages = cp_data.get("packages", {})
    pkg = packages.get(package_id)
    if pkg is None:
        raise ValueError(f"Unknown career package: {package_id!r}")

    if skill_choices is None:
        skill_choices = {}
    if traveller_specialties is None:
        traveller_specialties = {}
    if career_3skills is None:
        career_3skills = []

    # ── SOC requirement (Noble only) ──────────────────────────────────────
    min_soc = pkg.get("min_soc")
    if min_soc is not None:
        if character.characteristics.SOC < min_soc:
            raise ValueError(
                f"The {pkg['name']} package requires SOC {min_soc}+ "
                f"(character has SOC {character.characteristics.SOC})."
            )

    # ── Stat modifiers ────────────────────────────────────────────────────
    for stat, mod in pkg.get("stat_mods", {}).items():
        current = getattr(character.characteristics, stat, 0)
        new_val = current + mod
        if mod > 0:
            new_val = max(1, new_val)
        setattr(character.characteristics, stat, max(0, new_val))

    # ── Package skills ────────────────────────────────────────────────────
    pkg_skill_results: list[str] = []
    for sk in pkg["skills"]:
        name  = sk["name"]
        level = sk["level"]
        spec  = sk.get("speciality")
        key   = sk.get("key", name)

        if sk.get("any"):
            chosen_spec = skill_choices.get(key, skill_choices.get(name, "")).strip()
            if level >= 1 and not chosen_spec:
                raise ValueError(
                    f"No speciality chosen for {name} ({key}) in package '{pkg['name']}'"
                )
            spec = _SPEC_LOOKUP.get(chosen_spec.lower(), chosen_spec) if chosen_spec else None

        msg = character.add_skill(name, level=level, speciality=spec, fixed_level=(level > 0))
        pkg_skill_results.append(msg)

    # ── Credits & equipment ───────────────────────────────────────────────
    character.credits += pkg.get("credits", 0)
    for item_name in pkg.get("equipment", []):
        if item_name:
            character.equipment.append(Equipment(name=item_name))

    # ── Noble title ───────────────────────────────────────────────────────
    noble_title = pkg.get("noble_title")
    if noble_title:
        character.equipment.append(Equipment(name=noble_title))

    # ── Rank ──────────────────────────────────────────────────────────────
    base_rank  = pkg.get("rank", 0)
    rank_title = pkg.get("rank_title") or ""

    # ── Contacts & allies from package ────────────────────────────────────
    for _ in range(pkg.get("contacts", 0)):
        character.associates.append(
            Associate(kind="contact",
                      description=f"Contact: {pkg.get('contact_description', 'career contact')}")
        )
    for _ in range(pkg.get("allies", 0)):
        character.associates.append(
            Associate(kind="ally",
                      description=f"Ally: {pkg.get('ally_description', 'career ally')}")
        )

    # ── Age roll (d3) ─────────────────────────────────────────────────────
    age_roll = random.randint(1, 3)
    character.age += age_roll

    # ── Finalising: CAREER choice ─────────────────────────────────────────
    final_rank = base_rank

    if career_choice == "rank_4_only":
        final_rank = max(4, base_rank)

    elif career_choice == "boost_one_to_4":
        if not career_skill:
            raise ValueError("boost_one_to_4 requires career_skill to be set.")
        # Verify the skill is in the package at level 1+
        eligible = [
            s for s in pkg["skills"]
            if s["name"] == career_skill and s["level"] >= 1
        ]
        if not eligible:
            raise ValueError(
                f"'{career_skill}' is not listed at level 1+ in the {pkg['name']} package."
            )
        # Find and boost the character's skill
        boosted = False
        for sk in character.skills:
            match_name = sk.name == career_skill
            match_spec = (
                career_skill_speciality is None
                or sk.speciality == career_skill_speciality
                or (career_skill_speciality and sk.speciality and
                    sk.speciality.lower() == career_skill_speciality.lower())
            )
            if match_name and match_spec and sk.level >= 1:
                sk.level = 4
                boosted = True
                break
        if not boosted:
            # Fallback: boost any matching skill by name
            for sk in character.skills:
                if sk.name == career_skill:
                    sk.level = 4
                    boosted = True
                    break
        if not boosted:
            raise ValueError(
                f"Could not find skill '{career_skill}' on the character to boost to level 4."
            )

    elif career_choice == "boost_three_by_1":
        if len(career_3skills) != 3:
            raise ValueError("boost_three_by_1 requires exactly 3 skills.")
        pkg_skill_names = {s["name"] for s in pkg["skills"]}
        seen_boosts: set[str] = set()
        for sk_ref in career_3skills:
            sname = sk_ref.get("name", "")
            sspec = sk_ref.get("speciality")
            if sname not in pkg_skill_names:
                raise ValueError(
                    f"'{sname}' is not in the {pkg['name']} package skill list."
                )
            dedup_key = f"{sname}|{sspec}"
            if dedup_key in seen_boosts:
                raise ValueError(f"Cannot boost '{sname}' twice.")
            seen_boosts.add(dedup_key)
            # Find the skill and boost (max level 2)
            for char_sk in character.skills:
                match_name = char_sk.name == sname
                match_spec = (
                    sspec is None
                    or char_sk.speciality == sspec
                    or (sspec and char_sk.speciality and
                        char_sk.speciality.lower() == sspec.lower())
                )
                if match_name and match_spec:
                    char_sk.level = min(2, char_sk.level + 1)
                    break
            else:
                # Skill not yet present (was level 0 cascade base) — add at level 1
                spec = sspec.lower() if sspec else None
                character.add_skill(sname, level=1, speciality=spec)

    # ── Finalising: TRAVELLER SKILLS ──────────────────────────────────────
    ts_table = cp_data.get("finalising", {}).get("traveller_skills", [])
    ts_pair  = next((p for p in ts_table if p["id"] == traveller_pair_id), None)
    if ts_pair is None:
        raise ValueError(f"Unknown traveller_skills pair id: {traveller_pair_id}")

    for ts_sk in ts_pair["skills"]:
        ts_name = ts_sk["name"]
        ts_key  = ts_sk.get("key", ts_name)
        ts_spec: str | None = None
        if ts_sk.get("any"):
            ts_spec = traveller_specialties.get(ts_key, traveller_specialties.get(ts_name, "")).strip()
            if not ts_spec:
                raise ValueError(
                    f"No speciality chosen for traveller_skills pair {traveller_pair_id} skill '{ts_name}'."
                )
            ts_spec = ts_spec.lower()
        character.add_skill(ts_name, level=1, speciality=ts_spec)

    # ── Finalising: BENEFIT ───────────────────────────────────────────────
    benefits_table = cp_data.get("finalising", {}).get("benefits", [])
    benefit_entry  = next((b for b in benefits_table if b["id"] == benefit_id), None)
    if benefit_entry is None:
        raise ValueError(f"Unknown benefit id: {benefit_id}")

    btype = benefit_entry.get("type")
    if btype == "ship_share":
        character.ship_shares += benefit_entry.get("value", 1)
    elif btype == "credits":
        character.credits += benefit_entry.get("value", 0)
    elif btype == "equipment":
        character.equipment.append(Equipment(name=benefit_entry["value"]))
    elif btype == "associates":
        for _ in range(benefit_entry.get("allies", 0)):
            character.associates.append(Associate(kind="ally", description="Career package ally"))
        for _ in range(benefit_entry.get("contacts", 0)):
            character.associates.append(Associate(kind="contact", description="Career package contact"))
    elif btype == "stat_mod":
        stat = benefit_entry.get("stat", "SOC")
        val  = benefit_entry.get("value", 1)
        setattr(character.characteristics, stat,
                max(0, getattr(character.characteristics, stat, 0) + val))

    # ── Record career history ─────────────────────────────────────────────
    character.career_package_id   = package_id
    character.career_package_taken = True
    character.total_terms          = 1

    career_rec = CareerRecord(
        career_id=package_id,
        assignment_id=package_id,
        terms_served=1,
        final_rank=final_rank,
        final_rank_title=rank_title if career_choice == "rank_4_only" or base_rank == final_rank else rank_title,
        left_due_to="voluntary",
        benefit_rolls_used=0,
        benefit_rolls_earned=0,
    )
    character.completed_careers.append(career_rec)

    career_term = CareerTerm(
        career_id=package_id,
        assignment_id=package_id,
        term_number=1,
        overall_term_number=1,
        rank=final_rank,
        rank_title=rank_title or None,
        events=[
            f"Took the {pkg['name']} career package (d3 age roll: +{age_roll} years).",
            f"Finalising bonus: {career_choice.replace('_', ' ')}.",
            f"Traveller skills: {ts_pair['label']}.",
            f"Benefit: {benefit_entry['label']}.",
        ],
        skills_gained=pkg_skill_results,
    )
    character.term_history.append(career_term)

    # ── Log & phase ───────────────────────────────────────────────────────
    stat_parts = [
        f"{s}{'+' if v > 0 else ''}{v}"
        for s, v in pkg.get("stat_mods", {}).items()
    ]
    character.log(
        f"Career Package — {pkg['name']}: "
        f"{'  '.join(stat_parts) or 'no stat changes'}  |  "
        f"Cr{pkg.get('credits', 0):,}  |  Rank {final_rank}  |  "
        f"Age +{age_roll} → {character.age}"
    )

    character.phase = "skill_package"

    return {
        "age_roll": age_roll,
        "package_name": pkg["name"],
        "final_rank": final_rank,
        "character": character.model_dump(),
    }


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


def _build_spec_lookup() -> dict[str, str]:
    """Build lowercase → canonical-case lookup from skills.json speciality lists."""
    lookup: dict[str, str] = {}
    for spec_list in rules.skills().get("speciality", {}).values():
        for sp in spec_list:
            lookup[sp.lower()] = sp
    return lookup


# Module-level lookup so we normalise speciality case on every add_skill call.
_SPEC_LOOKUP: dict[str, str] = _build_spec_lookup()


def _split_skill_speciality(s: str) -> tuple[str, Optional[str]]:
    """Split 'Gun Combat (Slug)' → ('Gun Combat', 'Slug'). Plain name → (name, None).

    Normalises the speciality to canonical Title Case using the skills.json lookup so that
    'computers', 'Computers' and 'COMPUTERS' all resolve to 'Computers'.  Specialities not
    in the lookup (e.g. 'any', 'the Way', custom Profession specs) are returned unchanged.
    """
    s = s.strip()
    if "(" in s and s.endswith(")"):
        name = s[: s.index("(")].strip()
        spec = s[s.index("(") + 1 : -1].strip()
        spec = _SPEC_LOOKUP.get(spec.lower(), spec)
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
        if character.homeworld_uwp and tl > tl_max:
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
        if character.homeworld_uwp and size != req_size:
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

    # ─── Aslan University ────────────────────────────────────────────────────────
    if track == "aslan_university":
        if character.age > track_data["max_age"]:
            raise ValueError(
                f"Too old for Aslan University (age {character.age} > "
                f"max {track_data['max_age']})"
            )
        qual = track_data["qualification"]
        char_key = qual["characteristic"]
        target = qual["target"]
        dm = dice.characteristic_dm(character.characteristics.get(char_key))

        for mod in qual.get("modifiers", []):
            if mod.get("type") == "characteristic_threshold":
                stat = mod.get("characteristic", "")
                threshold = int(mod.get("threshold", 0))
                stat_val = character.characteristics.get(stat)
                if stat_val is not None and stat_val >= threshold:
                    dm += int(mod.get("dm", 0))
            elif mod.get("type") == "per_previous_term":
                dm += mod["dm"] * character.total_terms

        r = dice.roll("2D", modifier=dm, target=target)
        passed = bool(r.succeeded)
        enrollment_applied: list[str] = []

        if passed:
            # Apply enrollment EDU bonus
            bonuses = track_data.get("enrollment_bonus", {})
            for stat, delta in bonuses.items():
                current = character.characteristics.get(stat)
                character.characteristics.set(stat, current + delta)
                enrollment_applied.append(f"{stat} {delta:+d}")

            character.age += track_data["age_cost"]

            # Gender-specific skill pool
            gender = character.gender or "male"
            pool_key = "skill_list_male" if gender == "male" else "skill_list_female"
            enrollment_skill_pool = list(track_data.get(pool_key, []))
            enrollment_picks = int(track_data.get("enrollment_skill_picks", 1))

            character.pre_career_status = {
                "track": "aslan_university",
                "service": None,
                "stage": "enrolled",
                "outcome": None,
                "skill_picks_remaining": enrollment_picks,
                "skill_pick_level": 0,
                "skill_pick_stage": "enrollment",
                "skill_pool": enrollment_skill_pool,
                "enrollment_skill_pool": enrollment_skill_pool,
            }
            character.log(
                f"Qualified for Aslan University ({char_key} {target}+): "
                f"2D{dm:+d} = {r.total} [PASS]. Gender pool ({gender}). "
                + (f"Enrollment bonus: {', '.join(enrollment_applied)}. " if enrollment_applied else "")
                + f"{enrollment_picks} enrollment skill pick pending."
            )
        else:
            character.pre_career_status = {
                "track": "aslan_university",
                "service": None,
                "stage": "not_qualified",
                "outcome": "not_qualified",
                "skill_picks_remaining": 0,
                "skill_pool": [],
            }
            character.phase = "career"
            character.log(
                f"Failed to qualify for Aslan University ({char_key} {target}+): "
                f"2D{dm:+d} = {r.total} [FAIL]. Moving on to careers."
            )
        return {
            "roll": r.to_dict(),
            "passed": passed,
            "track": track,
            "enrollment_applied": enrollment_applied,
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
        elif mod.get("type") == "characteristic_threshold":
            stat = mod["characteristic"]
            check_val = character.psi if stat == "PSI" else character.characteristics.get(stat)
            if check_val >= int(mod["threshold"]):
                dm += int(mod["dm"])

    # Apply species-specific pre-career DMs (e.g. Dolphins DM-1 university, Orca DM-2 university)
    _sp_data = rules.species().get(character.species_id or "", {})
    if track == "university":
        _sp_uni_dm = int(_sp_data.get("university_dm", 0))
        if _sp_uni_dm:
            dm += _sp_uni_dm
    elif track == "military_academy":
        _sp_mil_dm = int(_sp_data.get("military_academy_dm", 0))
        if _sp_mil_dm:
            dm += _sp_mil_dm

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
                    skill_name, skill_spec = _split_skill_speciality(part)
                    msg = character.add_skill(skill_name, level=0, speciality=skill_spec)
                    enrollment_applied.append(msg)
                    break

        character.age += track_data["age_cost"]

        enrollment_picks = 0
        enrollment_skill_pool: list[str] = []
        pending_pick_rounds: list[dict] = []
        if track == "university":
            enrollment_picks = 1
            enrollment_skill_pool = list(track_data.get("skill_list", []))
            pending_pick_rounds = [
                {"count": 1, "level": 1, "pool": enrollment_skill_pool, "fixed_level": True}
            ]

        character.pre_career_status = {
            "track": track,
            "service": service,
            "enrolled_skills": [],
            "enrollment_skill_pool": enrollment_skill_pool,
            "stage": "enrolled",
            "outcome": None,
            "skill_picks_remaining": enrollment_picks,
            "skill_pick_level": 0,
            "skill_pick_fixed_level": False,
            "skill_pick_stage": "enrollment",
            "skill_pool": enrollment_skill_pool,
            "pending_pick_rounds": pending_pick_rounds,
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
        enrolled_skills = list(status.get("enrolled_skills", []))
        # Psionic talent upgrade pick rounds (built in the psionic block, queued below)
        psi_upgrade_round: Optional[dict] = None
        psi_to2_round: Optional[dict] = None

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
            character.add_skill("Jack-of-all-Trades", level=joat_level, fixed_level=True)
            applied_note.append(f"Jack-of-all-Trades {joat_level}")

        # ── Fixed skills ("Leadership 1": true or "fixed_skills": [...]) ─────────
        # Rank listed → fixed_level=True (take only if better than current).
        # Handle "fixed_skills" list: ["Science (Psionicology) 1", "Gun Combat 0"]
        for sk_str in block.get("fixed_skills", []):
            parts = sk_str.rsplit(" ", 1)
            sk_part = parts[0].strip()
            sk_level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            sn, spec = _split_skill_speciality(sk_part)
            character.add_skill(sn, level=sk_level, speciality=spec, fixed_level=(sk_level > 0))
            applied_note.append(f"Gained {sk_str}")
        # Handle "SkillName N": true pattern (e.g. "Leadership 1": true)
        for bk, bv in block.items():
            if bv is True and bk[-1].isdigit() and " " in bk:
                parts = bk.rsplit(" ", 1)
                if parts[1].isdigit():
                    sn, spec = _split_skill_speciality(parts[0].strip())
                    character.add_skill(sn, level=int(parts[1]), speciality=spec, fixed_level=True)
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

        def _resolve_talent_skill(entry: str) -> str:
            """Resolve a psi_trained_talents entry to its skill name.

            Entries may be a lowercase talent id ('teleportation', from the
            Psionic Community free training) OR a capitalised talent name
            ('Teleportation', from species childhood training). May carry a
            '/failed' suffix from zhodani-style training — strip it.
            """
            e = entry.replace("/failed", "").strip()
            # Lowercase id lookup
            info = psi_talents_map.get(e.lower())
            if info and info.get("skill"):
                return info["skill"]
            # Match by capitalised name
            for t in psi_talents_map.values():
                if t.get("name", "").lower() == e.lower() or t.get("skill", "").lower() == e.lower():
                    return t["skill"]
            return e  # assume it's already a skill name

        # Resolve all *successfully* trained talents (exclude '/failed' markers) to skills.
        _trained_skills: list[str] = []
        for entry in (character.psi_trained_talents or []):
            if entry.endswith("/failed"):
                continue
            sk_name = _resolve_talent_skill(entry)
            if sk_name and sk_name not in _trained_skills:
                _trained_skills.append(sk_name)

        # psionic_talent_upgrade: player CHOOSES which trained talent rises to level 1.
        # Build a pick round (resolved later with the other graduation picks).
        if block.get("psionic_talent_upgrade") and _trained_skills:
            psi_upgrade_round = {
                "count": 1, "level": 1, "pool": list(_trained_skills),
                "label": "Raise one psionic talent to level 1",
            }

        # psionic_all_talents_to_1: raise every trained talent to at least level 1 (no choice).
        if block.get("psionic_all_talents_to_1"):
            for sk_name in _trained_skills:
                for sk in character.skills:
                    if sk.name == sk_name:
                        sk.level = max(sk.level, 1)
                        break
            if _trained_skills:
                applied_note.append("All trained psionic talents raised to level 1")

        # psionic_one_talent_to_2: player CHOOSES which trained talent rises to level 2.
        if block.get("psionic_one_talent_to_2") and _trained_skills:
            psi_to2_round = {
                "count": 1, "level": 2, "pool": list(_trained_skills),
                "label": "Raise one psionic talent to level 2",
            }

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
            if track == "aslan_university":
                gender = character.gender or "male"
                pool_key = "skill_list_male" if gender == "male" else "skill_list_female"
                l1_pool = list(track_data.get(pool_key, []))
            elif track == "university":
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
            up_pool = list(enrolled_skills) if enrolled_skills else (list(enroll_pool) if enroll_pool else list(skill_pool))
            all_rounds.append({"count": upgrade_count, "level": 1, "pool": up_pool,
                                "label": "Upgrade enrollment skill to level 1",
                                "fixed_level": True})

        # Increase enrolled skills by one level (University graduation)
        increase_count = int(block.get("skills_increase_from_enrollment", 0))
        if increase_count > 0:
            inc_pool = list(enrolled_skills) if enrolled_skills else (list(enroll_pool) if enroll_pool else list(skill_pool))
            all_rounds.append({"count": increase_count, "level": 1, "pool": inc_pool,
                                "label": "Increase university skill by one level",
                                "fixed_level": False})

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

        # Psionic talent picks go FIRST (highest level): level 2 before level 1.
        if psi_to2_round:
            all_rounds.insert(0, psi_to2_round)
        if psi_upgrade_round:
            # Insert after the level-2 round (if any) but before normal skill picks.
            insert_at = 1 if psi_to2_round else 0
            all_rounds.insert(insert_at, psi_upgrade_round)

        # Assign first round to skill_pool/picks_remaining, queue the rest
        if all_rounds:
            first = all_rounds[0]
            skill_pool = first["pool"]
            picks_remaining = first["count"]
            # skill_pick_level will be set from first["level"] when building status
            pending_pick_rounds = [
                {
                    "count": rnd["count"],
                    "level": rnd["level"],
                    "pool": rnd["pool"],
                    "fixed_level": rnd.get("fixed_level", rnd["level"] > 0),
                }
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
            sn, spec = _split_skill_speciality(s)
            character.add_skill(sn, level=1, speciality=spec, fixed_level=True)
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
    # Aslan University uses its own event table.
    _aslan_track = track == "aslan_university"
    events_table: dict = edu.get(
        "aslan_pre_career_events" if _aslan_track else "pre_career_events", {}
    )
    ev = dice.roll("2D")
    ev_key = str(ev.total)
    event_text: str = events_table.get(ev_key, "Nothing remarkable happens.")
    event_auto_applied: list[str] = []
    forced_fail = False

    if ev.total == 2:
        if _aslan_track:
            # Aslan event 2: neglectful students — pending interactive choice (JS resolves)
            event_auto_applied.append(
                "Pending: choose whether to join the neglectful students (see choice below)"
            )
        else:
            # Standard: Psionic contact — roll 2D for PSI characteristic, flag Psion available.
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
        soc_val = character.characteristics.get("SOC")
        soc_dm = dice.characteristic_dm(soc_val)
        soc_roll = dice.roll("2D", modifier=soc_dm, target=8)
        if _aslan_track:
            # Aslan event 4: honour duel — natural 2 = Outcast (not Prisoner)
            if soc_roll.raw_total == 2:
                character.forced_next_career_id = "aslan_outcast"
                event_auto_applied.append(
                    f"SOC check: natural 2! Must become Outcast next term."
                )
            elif soc_roll.succeeded:
                character.associates.append(
                    Associate(kind="rival", description="Rival [Aslan University] — honour duel")
                )
                event_auto_applied.append(
                    f"SOC {soc_val} check (2D{soc_dm:+d}={soc_roll.total} vs 8+): passed — gained Rival [Aslan University]"
                )
            else:
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Aslan University] — honour duel")
                )
                event_auto_applied.append(
                    f"SOC {soc_val} check (2D{soc_dm:+d}={soc_roll.total} vs 8+): failed — gained Enemy [Aslan University]"
                )
        else:
            # Standard: prank gone wrong — roll SOC 8+. Natural 2 = must take Prisoner next term.
            if soc_roll.raw_total == 2:
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
        if _aslan_track:
            # Aslan event 11: clan war — flee (Outcast) or join a military career.
            event_auto_applied.append("Pending: choose your response to the clan war (see options below)")
        else:
            # Draft event — player must choose: Drifter / be Drafted / Dodge (SOC 9+).
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
        if track == "aslan_university":
            td = _edu_track(track)
            gender = character.gender or "male"
            pool_key = "skill_list_male" if gender == "male" else "skill_list_female"
            event10_pool = list(td.get(pool_key, []))
        elif track == "university":
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
    pending_aslan_event2 = ev.total == 2 and _aslan_track and not forced_fail

    # Determine the pick level for the first pending round (if any).
    # all_rounds is only defined inside the else block; check if it exists.
    first_round_level = all_rounds[0]["level"] if (outcome != "fail" and all_rounds) else 1

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
        "skill_pick_fixed_level": all_rounds[0].get("fixed_level", first_round_level > 0) if (outcome != "fail" and all_rounds) else True,
        "skill_pick_stage": "graduation",  # when done, advance to career
        "skill_pool": skill_pool,
        "pending_pick_rounds": pending_pick_rounds,
        "events_remaining": 0,
        "events_rolled": [ev.total],
        "pending_event10": pending_event10,
        "pending_event11": pending_event11,
        "pending_aslan_event2": pending_aslan_event2,
        "event10_skill_pool": event10_pool,
    }
    # Always stay in pre_career so the JS can show the graduation+event screen.
    # The phase advances to career when the user clicks Continue (no picks)
    # or when pre_career_choose_skills completes the last pick.
    # Count this as a pre-career term when no further server calls will do so.
    if picks_remaining == 0 and not pending_event10 and not pending_event11 and not pending_aslan_event2:
        character.pre_career_terms += 1
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
            "pending_aslan_event2": pending_aslan_event2,
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
    fixed_level = bool(status.get("skill_pick_fixed_level", skill_level > 0))
    skill_pick_stage = status.get("skill_pick_stage", "graduation")

    if remaining <= 0:
        raise ValueError("No pending skill picks.")
    if len(chosen_skills) > remaining:
        raise ValueError(
            f"Chose {len(chosen_skills)} skills but only {remaining} picks left."
        )
    for s in chosen_skills:
        # Accept "Skill (Specialty)" when the pool contains the base "Skill"
        base = s.split(" (")[0].strip()
        if s not in pool and base not in pool:
            raise ValueError(f"'{s}' not in this track's skill pool.")
        sn, spec = _split_skill_speciality(s)
        character.add_skill(sn, level=skill_level, speciality=spec, fixed_level=fixed_level)

    remaining -= len(chosen_skills)
    enrolled_skills = list(status.get("enrolled_skills", []))
    if skill_pick_stage == "enrollment":
        for s in chosen_skills:
            if s not in enrolled_skills:
                enrolled_skills.append(s)

    stage_label = "enrollment" if skill_pick_stage == "enrollment" else "graduation"
    character.log(
        f"Picked {len(chosen_skills)} pre-career {stage_label} skill(s) at level {skill_level}: "
        + ", ".join(chosen_skills)
    )

    if remaining == 0:
        pending_rounds = list(status.get("pending_pick_rounds", []))
        if pending_rounds:
            # Advance to the next queued pick round.
            next_round = pending_rounds.pop(0)
            character.pre_career_status = {
                **status,
                "enrolled_skills": enrolled_skills,
                "skill_picks_remaining": next_round["count"],
                "skill_pick_level": next_round["level"],
                "skill_pick_fixed_level": next_round.get("fixed_level", next_round["level"] > 0),
                "skill_pool": next_round["pool"],
                "pending_pick_rounds": pending_rounds,
            }
            # Stay in pre_career for more picks
        elif skill_pick_stage == "graduation":
            character.pre_career_terms += 1
            character.phase = "career"
            character.pre_career_status = {
                **status,
                "enrolled_skills": enrolled_skills,
                "skill_picks_remaining": 0,
                "skill_pool": [],
                "pending_pick_rounds": [],
            }
        else:
            # enrollment stage: clear picks, stay in pre_career for events/graduation
            character.pre_career_status = {
                **status,
                "enrolled_skills": enrolled_skills,
                "skill_picks_remaining": 0,
                "skill_pool": [],
                "pending_pick_rounds": [],
            }
    else:
        character.pre_career_status = {
            **status,
            "enrolled_skills": enrolled_skills,
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
    name, speciality = _split_skill_speciality(text)
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
    base_text = text.split(" (")[0].strip()
    if pool and text not in pool and base_text not in pool:
        raise ValueError(f"'{text}' is not in the education skill pool for this track.")

    r = dice.roll("2D", target=9)
    if r.succeeded:
        name, speciality = _split_skill_speciality(text)
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
        character.pre_career_terms += 1
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
        character.pre_career_terms += 1
        character.phase = "career"

    elif choice == "draft":
        d6 = dice.roll("1D").total
        if character.society_id == "solomani_confederation":
            # Solomani draft table:
            # 1=Confederation Navy, 2=Confederation Army, 3=Star Marines,
            # 4=Merchant, 5=SolSec, 6=Agent
            solomani_draft = [
                "confederation_navy", "confederation_army", "solomani_marine",
                "merchant", "solsec", "agent",
            ]
            draft_career = solomani_draft[d6 - 1]
        elif character.society_id == "vargr_extents":
            # Vargr Extents draft table: 1-3=Army, 4=Marines, 5=Navy, 6=Law Enforcement
            if d6 <= 3:
                draft_career = "vargr_army"
            elif d6 == 4:
                draft_career = "vargr_marines"
            elif d6 == 5:
                draft_career = "vargr_navy"
            else:
                draft_career = "vargr_law_enforcement"
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
        character.pre_career_terms += 1
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
                character.pre_career_terms += 1
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
            character.pre_career_terms += 1
            character.phase = "career"
    else:
        raise ValueError(f"Unknown event 11 choice: {choice!r}. Must be 'drifter', 'draft', or 'dodge'.")

    return {
        "choice": choice,
        "roll": roll_result,
        "draft_career": draft_career,
        "character": character.model_dump(),
    }


def pre_career_aslan_event2_choice(character: Character, choice: str) -> dict:
    """Aslan University event 2 — neglectful students choice.

    choice: "join" | "focus"
    - join: SOC is set to 2 (if currently higher), free-qualify for Outlaw or Wanderer.
    - focus: no effect, clear the pending flag.
    """
    status = character.pre_career_status or {}
    if not status.get("pending_aslan_event2"):
        raise ValueError("No pending Aslan event 2 choice.")

    applied: list[str] = []

    if choice == "join":
        soc_now = character.characteristics.get("SOC")
        if soc_now is not None and soc_now > 2:
            character.characteristics.set("SOC", 2)
            applied.append(f"SOC reduced to 2 (was {soc_now})")
        else:
            applied.append("SOC already 2 or lower — no change")
        # Grant free qualification for Outlaw or Wanderer
        pdms = dict(character.pre_career_permanent_dms or {})
        pdms["aslan_outlaw_wanderer_free_qualify"] = True
        character.pre_career_permanent_dms = pdms
        applied.append("Aslan Outlaw and Wanderer careers: free qualification next term")
        character.log(
            "Aslan University event 2: joined neglectful students — "
            + ", ".join(applied)
        )
    elif choice == "focus":
        applied.append("Stayed focused on studies — no effect")
        character.log("Aslan University event 2: stayed focused on studies (no effect)")
    else:
        raise ValueError(f"Unknown event 2 choice: {choice!r}. Must be 'join' or 'focus'.")

    character.pre_career_status = {
        **status,
        "pending_aslan_event2": False,
    }

    # Advance to career if nothing else is pending
    if not character.pre_career_status.get("skill_picks_remaining") and \
       not character.pre_career_status.get("pending_event10") and \
       not character.pre_career_status.get("pending_event11"):
        character.pre_career_terms += 1
        character.phase = "career"

    return {
        "choice": choice,
        "applied": applied,
        "character": character.model_dump(),
    }


def pre_career_aslan_event11_choice(character: Character, choice: str) -> dict:
    """Aslan University event 11 — clan war.

    choice: "outcast" | "aslan_military" | "aslan_military_officer" | "aslan_spacer" | "aslan_space_officer"
    - outcast: flee, become Outcast next term, do not graduate.
    - any career choice: forced into that career next term, do not graduate.
    """
    status = character.pre_career_status or {}
    if not status.get("pending_event11"):
        raise ValueError("No pending event 11 clan war choice.")

    valid = ("outcast", "aslan_military", "aslan_military_officer", "aslan_spacer", "aslan_space_officer")
    if choice not in valid:
        raise ValueError(
            f"Unknown Aslan event 11 choice: {choice!r}. "
            f"Must be one of: {', '.join(valid)}"
        )

    def _clear_graduation_bonuses() -> None:
        character.starts_commissioned_career_id = None
        character.academy_commission_career_id = None
        character.academy_commission_dm = 0
        character.auto_entry_career_id = None

    _clear_graduation_bonuses()

    if choice == "outcast":
        character.forced_next_career_id = "aslan_outcast"
        log_msg = "fled the clan war — becoming Outcast (did not graduate)"
    else:
        character.forced_next_career_id = choice
        career_name = choice.replace("_", " ").title()
        log_msg = f"enlisted in {career_name} career due to clan war (did not graduate)"

    character.pre_career_status = {
        **status,
        "stage": "failed_grad",
        "outcome": "fail",
        "skill_picks_remaining": 0,
        "pending_event11": False,
    }
    character.log(f"Aslan University event 11 (clan war): {log_msg}")
    character.pre_career_terms += 1
    character.phase = "career"

    return {
        "choice": choice,
        "character": character.model_dump(),
    }


def pre_career_aslan_outlaw_wanderer_qualify_check(character: Character) -> bool:
    """Return True if the character has free-qualify for aslan_outlaw/aslan_wanderer."""
    pdms = character.pre_career_permanent_dms or {}
    return bool(pdms.get("aslan_outlaw_wanderer_free_qualify"))


def _consume_aslan_outlaw_wanderer_free_qualify(character: Character, career_id: str) -> bool:
    """Consume the free-qualify flag for aslan_outlaw/aslan_wanderer. Returns True if consumed."""
    pdms = character.pre_career_permanent_dms or {}
    if pdms.get("aslan_outlaw_wanderer_free_qualify") and career_id in ("aslan_outlaw", "aslan_wanderer"):
        pdms2 = dict(pdms)
        del pdms2["aslan_outlaw_wanderer_free_qualify"]
        character.pre_career_permanent_dms = pdms2
        return True
    return False


def _apply_homeworld_life_event(character: Character, species_id: str) -> dict:
    """Roll 1D on a homeworld-specific life events table and apply effects.

    Used for Drinax (Floating Palace), Drinax (Wasteland), and Asim characters
    whose homeworld tables roll 1D (1–6) instead of the standard 2D.
    """
    sp_max = int(rules.species().get(species_id, {}).get("characteristic_maximum", 15))

    def clamp_stat(char: Character, stat: str, delta: int) -> None:
        val = char.characteristics.get(stat, 7)
        char.characteristics.set(stat, max(1, min(val + delta, sp_max)))

    r = dice.roll("1D")
    total = r.total
    auto_applied: list[str] = []
    pending_choice: Optional[dict] = None

    # ── DRINAX — FLOATING PALACE ─────────────────────────────────────────────
    if species_id == "drinax_palace_human":
        if total == 1:
            character.associates.append(
                Associate(kind="contact", description="Contact [Drinax Court]")
            )
            auto_applied.append("Gained Contact [Drinax Court]")

        elif total == 2:
            sub = dice.roll("1D").total
            auto_applied.append(f"Family Affairs sub-roll: 1D={sub}")
            if sub <= 2:
                clamp_stat(character, "SOC", -1)
                auto_applied.append("Family Affairs (1-2): SOC-1 — title lost to succession")
            elif sub <= 4:
                pending_choice = {"kind": "drinax_arranged_marriage"}
                auto_applied.append(
                    "Family Affairs (3-4): Arranged marriage — choose whether to accept"
                )
            else:
                pending_choice = {
                    "kind": "family_inheritance",
                    "options": [
                        {"id": "benefit", "label": "Extra Benefit roll"},
                        {"id": "soc", "label": "SOC +1"},
                    ],
                }
                auto_applied.append(
                    "Family Affairs (5-6): Inheritance — PENDING: choose extra Benefit roll or SOC+1"
                )

        elif total == 3:
            sub = dice.roll("1D").total
            auto_applied.append(f"Romantic Entanglement sub-roll: 1D={sub}")
            if sub == 1:
                auto_applied.append("Romantic (1): Amicable breakup — no mechanical effect")
            elif sub == 2:
                pending_choice = {"kind": "romantic_split"}
                auto_applied.append("PENDING: choose Rival or Enemy [Nasty Breakup]")
            elif sub <= 4:
                character.associates.append(
                    Associate(kind="contact", description="Contact [Romantic Partner — Drinax Court]")
                )
                auto_applied.append("Romantic (3-4): Gained Contact [Romantic Partner]")
            elif sub == 5:
                character.associates.append(Associate(kind="ally", description="Ally [Spouse — Drinax Court]"))
                auto_applied.append("Romantic (5): Gained Ally [Spouse]")
            else:
                character.associates.append(
                    Associate(kind="contact", description="Deceased [Tragic Death/Disappearance — Romantic]")
                )
                auto_applied.append("Romantic (6): Tragic death or disappearance — noted in associates")

        elif total == 4:
            sub = dice.roll("1D").total
            auto_applied.append(f"Misfortune sub-roll: 1D={sub}")
            if sub <= 2:
                lost = min(2, character.pending_benefit_rolls)
                character.pending_benefit_rolls = max(0, character.pending_benefit_rolls - 2)
                clamp_stat(character, "SOC", -2)
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Treacherous Uncle — Stolen Inheritance]")
                )
                auto_applied.append(
                    f"Misfortune (1-2): Lost {lost} Benefit roll(s), SOC-2, gained Enemy [Treacherous Uncle]"
                )
            elif sub <= 4:
                clamp_stat(character, "END", -1)
                auto_applied.append("Misfortune (3-4): END-1 — disease contracted from Vespexers")
            else:
                character.associates.append(
                    Associate(kind="rival", description="Rival [Cheating Duelling Opponent — Drinax Court]")
                )
                character.add_skill("Melee", level=1, speciality="Blade")
                pending_choice = {
                    "kind": "drinax_duel_penalty",
                    "has_benefits": character.pending_benefit_rolls > 0,
                }
                auto_applied.append(
                    "Misfortune (5-6): Gained Rival [Duelling Opponent], Melee (Blade) +1 — "
                    "choose your additional penalty"
                )

        elif total == 5:
            sub = dice.roll("1D").total
            auto_applied.append(f"Good Fortune sub-roll: 1D={sub}")
            if sub <= 2:
                cash_roll = dice.roll("1D").total
                cash = cash_roll * 10_000
                character.credits += cash
                auto_applied.append(f"Good Fortune (1-2): Gained Cr{cash:,} (1D={cash_roll}×Cr10,000) — family heirloom sold")
            elif sub <= 4:
                pending_choice = {"kind": "drinax_star_guard"}
                auto_applied.append(
                    "Good Fortune (3-4): Star Guard commission — choose: sell for cash OR take a Navy commission"
                )
            else:
                character.pending_life_event_choice = {
                    "kind": "drinax_weapon_choice",
                    "options": [
                        {"id": "rapier", "label": "Ancient Rapier"},
                        {"id": "laser_pistol", "label": "Laser Pistol"},
                    ],
                }
                auto_applied.append(
                    "Good Fortune (5-6): Choose your weapon from the Palace armoury — Ancient Rapier or Laser Pistol."
                )

        elif total == 6:
            sub = dice.roll("1D").total
            auto_applied.append(f"Unusual Event sub-roll: 1D={sub}")
            if sub <= 2:
                psi_roll = dice.roll("2D")
                psi_total = min(psi_roll.total + 4, 15)
                character.psi = psi_total
                character.psi_tested = True
                auto_applied.append(
                    f"Unusual Event (1-2): Psionic! PSI tested 2D={psi_roll.total}+DM+4 → PSI {psi_total}"
                )
            elif sub <= 4:
                planets = {1: "Paal", 2: "Torpal", 3: "Clarke", 4: "Asim", 5: "Banks/Khusai", 6: "Sindalian world (player's choice)"}
                planet_roll = dice.roll("1D").total
                planet = planets[planet_roll]
                character.notes.append(f"Family estate claim: {planet} (Unusual Event — Drinax Palace).")
                auto_applied.append(
                    f"Unusual Event (3-4): Family owned estates on {planet} (1D={planet_roll}) — noted"
                )
            else:
                character.notes.append("Bastard child of King Oleb (Unusual Event — Drinax Palace).")
                auto_applied.append("Unusual Event (5-6): Bastard child of King Oleb — noted")

    # ── DRINAX — WASTELAND (VESPEXER) ────────────────────────────────────────
    elif species_id == "drinax_wasteland_human":
        if total == 1:
            character.associates.append(
                Associate(kind="contact", description="Contact [Drinax Wasteland — Rachando/Galx/Dancet/Harrick]")
            )
            auto_applied.append("Gained Contact [Drinax Wasteland Court]")

        elif total == 2:
            sub = dice.roll("1D").total
            auto_applied.append(f"Family Affairs sub-roll: 1D={sub}")
            if sub <= 2:
                pending_choice = {"kind": "drinax_child_crisis"}
                auto_applied.append(
                    "Family Affairs (1-2): Child born — tribe cannot feed them. Choose how to resolve."
                )
            elif sub <= 4:
                character.pending_benefit_rolls += 1
                auto_applied.append("Family Affairs (3-4): Tribe struck by disease — inherited possessions, extra Benefit roll added")
            else:
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Exiled Kin — Vespexer Tribe]")
                )
                auto_applied.append("Family Affairs (5-6): Gained Enemy [Vengeful Exiled Kin]")

        elif total == 3:
            sub = dice.roll("1D").total
            auto_applied.append(f"Romantic Entanglement sub-roll: 1D={sub}")
            if sub <= 2:
                character.associates.append(
                    Associate(kind="contact", description="Deceased [Partner — Married Off, Died]")
                )
                auto_applied.append("Romantic (1-2): Spouse died — noted in associates")
            elif sub <= 5:
                children_roll = dice.roll("1D").total
                children = max(0, children_roll - 3)
                character.associates.append(
                    Associate(kind="ally", description=f"Ally [Spouse — Vespexer Tribe{', ' + str(children) + ' children' if children > 0 else ''}]")
                )
                auto_applied.append(
                    f"Romantic (3-5): Gained Ally [Spouse], {children} children (1D={children_roll}-3)"
                )
            else:
                character.associates.append(
                    Associate(kind="contact", description="Deceased [Tragic Death/Disappearance — Romantic]")
                )
                auto_applied.append("Romantic (6): Tragic death or disappearance — noted")

        elif total == 4:
            sub = dice.roll("1D").total
            auto_applied.append(f"Misfortune sub-roll: 1D={sub}")
            if sub <= 2:
                clamp_stat(character, "SOC", -1)
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Persecutor — Framed for Crime, Exiled]")
                )
                auto_applied.append("Misfortune (1-2): SOC-1, gained Enemy [Persecutor]")
            elif sub <= 4:
                clamp_stat(character, "END", -1)
                auto_applied.append("Misfortune (3-4): END-1 — disease from Aslan ruins")
            else:
                lost = min(1, character.pending_benefit_rolls)
                character.pending_benefit_rolls = max(0, character.pending_benefit_rolls - 1)
                auto_applied.append(f"Misfortune (5-6): Lost {lost} Benefit roll — hazard suit repair")

        elif total == 5:
            sub = dice.roll("1D").total
            auto_applied.append(f"Good Fortune sub-roll: 1D={sub}")
            if sub <= 2:
                cash_roll = dice.roll("1D").total
                cash = cash_roll * 10_000
                character.credits += cash
                auto_applied.append(f"Good Fortune (1-2): Gained Cr{cash:,} (1D={cash_roll}×Cr10,000) — relic sold to Rachando")
            elif sub <= 4:
                pending_choice = {"kind": "drinax_ship_berth"}
                auto_applied.append(
                    "Good Fortune (3-4): Ship berth offered — choose your new career path"
                )
            else:
                character.pending_benefit_rolls += 1
                auto_applied.append("Good Fortune (5-6): Tribe prospers — extra Benefit roll added")

        elif total == 6:
            sub = dice.roll("1D").total
            auto_applied.append(f"Unusual Event sub-roll: 1D={sub}")
            if sub <= 2:
                psi_roll = dice.roll("2D")
                psi_total = min(psi_roll.total + 4, 15)
                character.psi = psi_total
                character.psi_tested = True
                auto_applied.append(
                    f"Unusual Event (1-2): Psionic! PSI tested 2D={psi_roll.total}+DM+4 → PSI {psi_total}"
                )
            elif sub <= 4:
                character.equipment.append(
                    Equipment(name="Mysterious Aslan Chest [Syoisuis symbol]", notes="Unusual Event — Drinax Wasteland. Sealed; never been opened.")
                )
                auto_applied.append("Unusual Event (3-4): Mysterious Aslan chest (Syoisuis assassin-clan) — added to equipment")
            else:
                character.notes.append("Declared Hlax Kur Eisa by tribe wise-woman — Vespexer messiah prophecy.")
                auto_applied.append("Unusual Event (5-6): Declared Hlax Kur Eisa — noted")

    # ── ASIM ─────────────────────────────────────────────────────────────────
    elif species_id == "asim_human":
        if total == 1:
            character.associates.append(
                Associate(kind="contact", description="Contact [Asim Court — Cleon Hardy/Rachando/Kisayl/Lord Wrax]")
            )
            auto_applied.append("Gained Contact [Asim Court]")

        elif total == 2:
            sub = dice.roll("1D").total
            auto_applied.append(f"Family Affairs sub-roll: 1D={sub}")
            if sub <= 2:
                clamp_stat(character, "SOC", 1)
                auto_applied.append("Family Affairs (1-2): SOC+1 — family thrived since reconquest")
            elif sub <= 4:
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Drinaxi Noble — killed father during the war]")
                )
                auto_applied.append("Family Affairs (3-4): Gained Enemy [Drinaxi Noble — killed father]")
            else:
                pending_choice = {
                    "kind": "asim_family_aid",
                    "has_benefits": character.pending_benefit_rolls > 0,
                }
                auto_applied.append(
                    "Family Affairs (5-6): Impoverished family — choose whether to help them"
                )

        elif total == 3:
            sub = dice.roll("1D").total
            auto_applied.append(f"Romantic Entanglement sub-roll: 1D={sub}")
            if sub <= 3:
                character.associates.append(Associate(kind="ally", description="Ally [Spouse — Arranged Marriage, Asim]"))
                auto_applied.append("Romantic (1-3): Married off — gained Ally [Spouse]")
            else:
                # Roll 1D for how it turned out (same as standard romantic table)
                sub2 = dice.roll("1D").total
                auto_applied.append(f"Romantic (4-6) sub-sub-roll: 1D={sub2}")
                if sub2 == 1:
                    auto_applied.append("Romantic (4-6, 1): Amicable breakup — no mechanical effect")
                elif sub2 == 2:
                    pending_choice = {"kind": "romantic_split"}
                    auto_applied.append("PENDING: choose Rival or Enemy [Nasty Breakup]")
                elif sub2 <= 4:
                    character.associates.append(
                        Associate(kind="contact", description="Contact [Romantic Partner — Drinax]")
                    )
                    auto_applied.append("Romantic (4-6, 3-4): Gained Contact [Romantic Partner]")
                elif sub2 == 5:
                    character.associates.append(Associate(kind="ally", description="Ally [Spouse — Drinax]"))
                    auto_applied.append("Romantic (4-6, 5): Gained Ally [Spouse]")
                else:
                    character.associates.append(
                        Associate(kind="contact", description="Deceased [Tragic Death/Disappearance — Romantic]")
                    )
                    auto_applied.append("Romantic (4-6, 6): Tragic death or disappearance — noted")

        elif total == 4:
            sub = dice.roll("1D").total
            auto_applied.append(f"Misfortune sub-roll: 1D={sub}")
            if sub <= 2:
                # Lose 1 benefit roll OR lose a Contact/Ally — player chooses
                contacts_allies = [
                    {"idx": i, "kind": a.kind, "description": a.description}
                    for i, a in enumerate(character.associates)
                    if a.kind in ("contact", "ally")
                ]
                has_benefits = character.pending_benefit_rolls > 0
                if has_benefits or contacts_allies:
                    pending_choice = {
                        "kind": "asim_misfortune_choice",
                        "has_benefits": has_benefits,
                        "contacts_allies": contacts_allies,
                    }
                    auto_applied.append(
                        "Misfortune (1-2): Dangerous misunderstanding — choose your penalty"
                    )
                else:
                    auto_applied.append(
                        "Misfortune (1-2): Dangerous misunderstanding — no Benefit rolls or associates to lose; narrative only"
                    )
            elif sub <= 4:
                injury = apply_injury(character)
                auto_applied.append(f"Misfortune (3-4): Injured while travelling — {injury.get('title', 'see log')}")
            else:
                slavers_roll = dice.roll("1D").total
                if slavers_roll <= 2:
                    career_label = "Navy"
                elif slavers_roll <= 4:
                    career_label = "Army"
                else:
                    career_label = "Scout"
                character.notes.append(
                    f"Aslan Slavers (Misfortune — Asim): enslaved, placed in {career_label} "
                    f"(1D={slavers_roll}). Cannot gain Commission or Benefit rolls while enslaved. "
                    "May escape each term on 2D 8+ (fail → Injury table). Apply career change manually."
                )
                auto_applied.append(
                    f"Misfortune (5-6): ASLAN SLAVERS! Placed in {career_label} (1D={slavers_roll}). "
                    "Cannot gain Commission or Benefits while enslaved. Escape 8+ each term or roll Injury. Noted."
                )

        elif total == 5:
            character.good_fortune_benefit_dm += 1
            auto_applied.append("Good Fortune: DM+1 token available for one mustering-out Benefit roll")

        elif total == 6:
            sub = dice.roll("1D").total
            auto_applied.append(f"Unusual Event sub-roll: 1D={sub}")
            if sub <= 2:
                character.associates.append(
                    Associate(kind="contact", description="Contact [Aslan — time spent in Hierate]")
                )
                auto_applied.append("Unusual Event (1-2): Gained Contact [Aslan]")
            elif sub <= 4:
                character.notes.append("Secret Foundation agent — mission to spy on Drinax court (Unusual Event — Asim).")
                auto_applied.append(
                    "Unusual Event (3-4): Secret Foundation conspiracy — inducted as agent, mission to spy on Drinax. Noted."
                )
            else:
                psi_roll = dice.roll("2D")
                psi_total = min(psi_roll.total + 4, 15)
                character.psi = psi_total
                character.psi_tested = True
                auto_applied.append(
                    f"Unusual Event (5-6): Psionic! PSI tested 2D={psi_roll.total}+DM+4 → PSI {psi_total}"
                )

    # Fetch descriptive text from the homeworld table.
    homeworld_table = rules.life_events_for_species(species_id) or {}
    event_entry = homeworld_table.get("entries", {}).get(str(total), {})
    if isinstance(event_entry, dict):
        event_text = f"{event_entry.get('title', '')}: {event_entry.get('text', 'Something happens in your life.')}"
    else:
        event_text = str(event_entry) if event_entry else "Something happens in your life."

    character.log(
        f"Homeworld Life Event [1D={total}]: {event_text}"
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
        "homeworld_table": True,
    }


def _apply_vargr_pack_event(character: Character) -> list[str]:
    """Roll 1D on the Pack Events sub-table and auto-apply mechanical effects.

    Returns a list of log strings for the caller to append to auto_applied.
    Called when a Vargr Extents life event result is 6 or 8.
    """
    sp_max = int(rules.species().get(character.species_id or "", {}).get("characteristic_maximum", 15))
    r = dice.roll("1D")
    sub = r.total
    applied: list[str] = [f"Pack Event sub-roll: 1D={sub}"]

    pack_table = rules.vargr_extents_life_events().get("pack_events", {})
    result_text = pack_table.get("results", {}).get(str(sub), "")
    if result_text:
        applied.append(result_text)

    if sub == 1:
        # Failure — lose SOC-1
        soc = character.characteristics.get("SOC")
        character.characteristics.set("SOC", max(1, soc - 1))
        applied.append("Pack Failure: SOC-1")
    elif sub == 2:
        # Leave Pack — auto-roll SOC 6+ to stay; if fail, note ejection risk
        soc = character.characteristics.get("SOC")
        stay_r = dice.roll("2D", modifier=dice.characteristic_dm(soc), target=6)
        if stay_r.succeeded:
            applied.append(f"Leave Pack: SOC 6+ roll = {stay_r.total} — stayed in career")
        else:
            applied.append(f"Leave Pack: SOC 6+ roll = {stay_r.total} — ejected from career")
            character.log("Pack Event: forced to leave pack — ejected from career")
    elif sub == 3:
        # Join Pack — gain Contact
        character.associates.append(Associate(kind="contact", description="Contact [New Pack]"))
        applied.append("Join Pack: Gained Contact [New Pack]")
    elif sub == 4:
        # Power Struggle — roll 1D: 1-3 Rival, 4-6 Ally
        struggle_r = dice.roll("1D").total
        if struggle_r <= 3:
            character.associates.append(Associate(kind="rival", description="Rival [Pack Power Struggle]"))
            applied.append(f"Power Struggle (1D={struggle_r}): current leader kept — Gained Rival")
        else:
            character.associates.append(Associate(kind="ally", description="Ally [New Pack Leader]"))
            applied.append(f"Power Struggle (1D={struggle_r}): new leader chosen — Gained Ally")
    elif sub == 5:
        # Success — SOC+1
        soc = character.characteristics.get("SOC")
        character.characteristics.set("SOC", min(soc + 1, sp_max))
        applied.append("Pack Success: SOC+1")
    elif sub == 6:
        # Leadership Challenge — note as pending; auto-apply Rival on failure
        soc = character.characteristics.get("SOC")
        lead_r = dice.roll("2D", modifier=dice.characteristic_dm(soc), target=10)
        if lead_r.succeeded:
            character.dm_next_advancement += 2
            applied.append(f"Leadership Challenge (2D={lead_r.total}): succeeded — became pack leader, DM+2 to next Advancement")
        else:
            character.associates.append(Associate(kind="rival", description="Rival [Lost Leadership Challenge]"))
            applied.append(f"Leadership Challenge (2D={lead_r.total}): failed — Gained Rival")

    return applied


def _apply_hiver_life_event(character: "Character") -> dict:
    """Roll on the Hiver Life Events table (2D).

    Hiver life events happen when career event 7 triggers a Life Event.
    The table is 2–12 with Hiver-specific results.
    """
    r = dice.roll("2D")
    total = r.total
    auto_applied: list[str] = []
    pending_choice: dict | None = None
    sp_max = int(rules.species().get(character.species_id or "", {}).get("characteristic_maximum", 15))

    if total == 2:
        # Injury
        injury = apply_injury(character)
        auto_applied.append(f"Injury rolled: {injury.get('title', 'see log')}")
        if injury.get("pending_choice"):
            auto_applied.append("PENDING: choose which stat absorbs the damage")

    elif total == 3:
        # Deficiency Disease — lose 1 from a random characteristic
        stats = ["STR", "DEX", "END", "INT", "EDU"]
        stat = stats[dice.roll("1D").total % len(stats)]
        old_val = character.characteristics.get(stat)
        character.characteristics.set(stat, max(0, old_val - 1))
        auto_applied.append(f"Deficiency Disease: {stat} {old_val} → {max(0, old_val - 1)}")

    elif total == 4:
        # Relationship Collapses — gain Enemy
        character.associates.append(Associate(kind="enemy", description="Enemy [Collapsed Relationship]"))
        auto_applied.append("Gained Enemy [Collapsed Relationship]")

    elif total == 5:
        # Work Clashes — gain Rival
        character.associates.append(Associate(kind="rival", description="Rival [Work Friction]"))
        auto_applied.append("Gained Rival [Work Friction]")

    elif total == 6:
        # Useful Alliance — gain Ally
        character.associates.append(Associate(kind="ally", description="Ally [Manipulated Into Loyalty]"))
        auto_applied.append("Gained Ally [Manipulated Into Loyalty]")

    elif total == 7:
        # New Connections — gain Contact
        character.associates.append(Associate(kind="contact", description="Contact [New Connection]"))
        auto_applied.append("Gained Contact [New Connection]")

    elif total == 8:
        # Plotting Discovered — convert Contact/Ally to Rival, or gain Enemy
        contacts = [i for i, a in enumerate(character.associates) if a.kind == "contact"]
        allies   = [i for i, a in enumerate(character.associates) if a.kind == "ally"]
        if contacts:
            old = character.associates[contacts[0]]
            old_desc = old.description or "Contact"
            character.associates[contacts[0]] = Associate(
                kind="rival", description=f"Rival [Plotting Discovered — was: {old_desc}]"
            )
            auto_applied.append(f"Contact '{old_desc}' converted to Rival [Plotting Discovered]")
        elif allies:
            old = character.associates[allies[0]]
            old_desc = old.description or "Ally"
            character.associates[allies[0]] = Associate(
                kind="rival", description=f"Rival [Plotting Discovered — was: {old_desc}]"
            )
            auto_applied.append(f"Ally '{old_desc}' converted to Rival [Plotting Discovered]")
        else:
            character.associates.append(Associate(kind="enemy", description="Enemy [Uncovered Plotter]"))
            auto_applied.append("No Contact/Ally available — gained Enemy [Uncovered Plotter]")

    elif total == 9:
        # New Knowledge — DM+2 to next advancement check
        character.dm_next_advancement += 2
        auto_applied.append("New Knowledge: DM+2 to next advancement check")

    elif total == 10:
        # Nest Change — gain 1 additional cash benefit roll
        character.pending_benefit_rolls += 1
        auto_applied.append("Nest Change: gained 1 additional cash benefit roll")

    elif total == 11:
        # Great Manipulator — choose Deception, Diplomat, or Persuade
        pending_choice = {
            "kind": "hiver_great_manipulator",
        }
        character.pending_life_event_choice = pending_choice
        auto_applied.append("PENDING: choose Deception, Diplomat or Persuade to gain at level 1")

    elif total == 12:
        # Manipulator's Gift — RES +1 (stored as SOC)
        old_soc = character.characteristics.SOC
        new_soc = min(old_soc + 1, sp_max)
        character.characteristics.SOC = new_soc
        auto_applied.append(f"Manipulator's Gift: RES {old_soc} → {new_soc}")

    life_table = rules.hiver_life_events()
    event_entry = life_table.get("entries", {}).get(str(total), {})
    event_text = (
        f"{event_entry.get('title', '')}: {event_entry.get('text', 'Something happens.')}"
        if isinstance(event_entry, dict) else str(event_entry)
    )
    character.log(
        f"Hiver Life Event [{total}]: {event_text}"
        + (f" — {', '.join(auto_applied)}" if auto_applied else "")
    )

    return {
        "roll": r.to_dict(),
        "total": total,
        "event_text": event_text,
        "auto_applied": auto_applied,
        "pending_choice": pending_choice,
    }


def _apply_droyne_life_event(character: "Character") -> dict:
    """Roll on the Droyne Life Events table (2D).

    Called when the end-of-term 2D + caste_number roll reaches 10+.
    """
    r = dice.roll("2D")
    total = r.total
    auto_applied: list[str] = []
    pending_choice: dict | None = None

    if total == 2:
        # Build starship — choose Engineer, Electronics, Mechanic, or rank +1
        pending_choice = {"kind": "droyne_starship_skill"}
        character.pending_life_event_choice = pending_choice
        auto_applied.append("PENDING: choose Engineer, Electronics, Mechanic, or Rank +1")

    elif total == 3:
        # Leader dies — Caste skill check → rank +1 on pass, −1 on fail
        caste_name = (character.droyne_caste or "worker").capitalize()
        caste_level = max(
            (sk.level for sk in character.skills
             if sk.name.lower() == "caste" and (sk.speciality or "").lower() == (character.droyne_caste or "").lower()),
            default=0
        )
        check_r = dice.roll("2D")
        check_total = check_r.total + caste_level
        term = character.current_term
        if check_total >= 8:
            if term is not None:
                term.rank = min(term.rank + 1, 6)
            auto_applied.append(f"Caste check [2D+{caste_level}={check_total}] PASSED: rank +1")
        else:
            if term is not None:
                term.rank = max(term.rank - 1, 0)
            auto_applied.append(f"Caste check [2D+{caste_level}={check_total}] FAILED: rank −1")

    elif total == 4:
        # Gain a Black Skill — player chooses
        pending_choice = {"kind": "droyne_black_skill"}
        character.pending_life_event_choice = pending_choice
        auto_applied.append("PENDING: choose a Black Skill (Carouse, Deception, Gambler, Persuade, Streetwise)")

    elif total == 5:
        # Gain Caste skill level
        caste_name = (character.droyne_caste or "worker").capitalize()
        log = character.add_skill("Caste", level=1, speciality=caste_name)
        auto_applied.append(f"Gained Caste ({caste_name}) 1: {log}")

    elif total == 6:
        # Caste check or rank −1
        caste_level = max(
            (sk.level for sk in character.skills
             if sk.name.lower() == "caste"),
            default=0
        )
        check_r = dice.roll("2D")
        check_total = check_r.total + caste_level
        if check_total >= 8:
            auto_applied.append(f"Caste check [2D+{caste_level}={check_total}] PASSED: no ill effects")
        else:
            term = character.current_term
            if term is not None:
                term.rank = max(term.rank - 1, 0)
            auto_applied.append(f"Caste check [2D+{caste_level}={check_total}] FAILED: rank −1")

    elif total == 7:
        # Nothing
        auto_applied.append("The Oytrip endures. Nothing significant occurs.")

    elif total == 8:
        # Appeal check → Contact on pass
        appeal_level = max(
            (sk.level for sk in character.skills if sk.name.lower() == "appeal"),
            default=0
        )
        check_r = dice.roll("2D")
        check_total = check_r.total + appeal_level
        if check_total >= 8:
            character.associates.append(Associate(kind="contact", description="Contact [Important Leader]"))
            auto_applied.append(f"Appeal check [2D+{appeal_level}={check_total}] PASSED: gained Contact [Important Leader]")
        else:
            auto_applied.append(f"Appeal check [2D+{appeal_level}={check_total}] FAILED: no contact")

    elif total == 9:
        # Outsider check → Ally on pass, Outsider 1 on fail
        outsider_level = max(
            (sk.level for sk in character.skills if sk.name.lower() == "outsider"),
            default=0
        )
        check_r = dice.roll("2D")
        check_total = check_r.total + outsider_level
        if check_total >= 8:
            character.associates.append(Associate(kind="ally", description="Ally [Outside the Oytrip]"))
            auto_applied.append(f"Outsider check [2D+{outsider_level}={check_total}] PASSED: gained Ally [Outsider]")
        else:
            log = character.add_skill("Outsider", level=1)
            auto_applied.append(f"Outsider check [2D+{outsider_level}={check_total}] FAILED: {log}")

    elif total == 10:
        # Voyage — choose Pilot, Astrogation, Engineer, or Electronics
        pending_choice = {"kind": "droyne_voyage_skill"}
        character.pending_life_event_choice = pending_choice
        auto_applied.append("PENDING: choose Pilot, Astrogation, Engineer or Electronics")

    elif total == 11:
        # PSI +1
        old_psi = character.psi
        sp_max = int(rules.species().get(character.species_id or "", {}).get("characteristic_maximum", 15))
        character.psi = min(old_psi + 1, sp_max)
        auto_applied.append(f"PSI +1: {old_psi} → {character.psi}")

    elif total == 12:
        # Ancients Tech
        log = character.add_skill("Ancients Tech", level=1)
        auto_applied.append(f"Ancients Tech 1: {log}")

    life_table = rules.droyne_life_events()
    event_entry = life_table.get("events", {}).get(str(total), {})
    event_text = event_entry.get("description", "Something happens.") if isinstance(event_entry, dict) else str(event_entry)
    character.log(
        f"Droyne Life Event [{total}]: {event_text}"
        + (f" — {', '.join(auto_applied)}" if auto_applied else "")
    )

    return {
        "roll": r.to_dict(),
        "total": total,
        "event_text": event_text,
        "auto_applied": auto_applied,
        "pending_choice": pending_choice,
    }


def apply_life_event(character: Character, career_id: Optional[str] = None) -> dict:
    """Roll 2D on the Life Events table and auto-apply everything possible.

    Pass career_id to route to the appropriate table (e.g. Solomani careers
    use the Solomani Life Events table instead of the standard one).
    For species with homeworld-specific 1D tables (Drinax, Asim), delegates
    to _apply_homeworld_life_event instead.

    Returns a dict describing what happened. Interactive outcomes set
    character.pending_life_event_choice so the caller can prompt the player.
    """
    if career_id is None and character.current_term is not None:
        career_id = character.current_term.career_id

    # Homeworld override: species with their own 1D life events tables.
    if rules.life_events_for_species(character.species_id or ""):
        return _apply_homeworld_life_event(character, character.species_id)

    # Hiver Federation careers use the Hiver Life Events table.
    if career_id in rules.HIVER_CAREER_IDS:
        return _apply_hiver_life_event(character)

    # Droyne careers: life events are only triggered from end_term via a 2D+caste_number
    # threshold check. When this function IS called for a Droyne, use the Droyne table.
    if career_id in rules.DROYNE_CAREER_IDS:
        return _apply_droyne_life_event(character)

    use_solomani = career_id in rules.SOLOMANI_CAREER_IDS
    use_vargr = career_id in rules.VARGR_CAREER_IDS
    use_zhodani = career_id in rules.ZHODANI_CAREER_IDS

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
        # The JS life-event choice UI handles the picker; no auto_applied message needed.
        pending_choice = {"kind": "racial_incident"} if use_solomani else {"kind": "romantic_split"}

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
        if use_vargr:
            # Pack Event (Vargr) — roll 1D on Pack Events sub-table.
            auto_applied.extend(_apply_vargr_pack_event(character))
        elif use_solomani:
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
        if use_vargr:
            # Pack Event (Vargr) — roll 1D on Pack Events sub-table.
            auto_applied.extend(_apply_vargr_pack_event(character))
        else:
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

    elif total == 9:
        # Travel / Relocation — DM+2 to next Qualification roll.
        character.dm_next_qualification += 2
        auto_applied.append("DM+2 to next Qualification roll")

    elif total == 10:
        if use_vargr:
            # Good Fortune (Vargr) — gain a Benefit roll or SOC+1.
            character.pending_benefit_rolls += 1
            auto_applied.append("Good Fortune: gained extra Benefit roll (or take SOC+1 instead)")
        else:
            # Good Fortune — one DM+2 token for any benefit roll.
            character.good_fortune_benefit_dm += 2
            auto_applied.append("Good Fortune: DM+2 token available for one mustering-out benefit roll")

    elif total == 11:
        if use_zhodani:
            # Crime (Zhodani) — roll SOC 8+; if failed lose benefit roll and roll Re-education Events.
            soc_val = character.characteristics.get("SOC")
            soc_dm = dice.characteristic_dm(soc_val)
            check_r = dice.roll("2D")
            check_total = check_r.total + soc_dm
            if check_total >= 8:
                auto_applied.append(f"Crime: SOC 8+ check passed (2D={check_r.total}+DM{soc_dm:+d}={check_total}) — no penalty")
            else:
                # Lose one benefit roll (minimum 0).
                if character.pending_benefit_rolls > 0:
                    character.pending_benefit_rolls -= 1
                    auto_applied.append(f"Crime: SOC 8+ check failed (2D={check_r.total}+DM{soc_dm:+d}={check_total}) — lost 1 Benefit roll")
                else:
                    auto_applied.append(f"Crime: SOC 8+ check failed (2D={check_r.total}+DM{soc_dm:+d}={check_total}) — no Benefit roll to lose")
                # Roll Re-education Events (1D sub-table).
                re_r = dice.roll("1D")
                re_table = rules.zhodani_life_events().get("re_education_events", {})
                re_results = re_table.get("results", {})
                re_text = re_results.get(str(re_r.total), "Re-education: consult Re-education Events table.")
                character.log(f"Re-education Events [1D={re_r.total}]: {re_text}")
                auto_applied.append(f"Re-education Events 1D={re_r.total}: {re_text}")
        elif use_vargr:
            # Crime (Vargr) — lose SOC-1.
            sp_max = int(rules.species().get(character.species_id or "", {}).get("characteristic_maximum", 15))
            soc = character.characteristics.get("SOC")
            character.characteristics.set("SOC", max(1, soc - 1))
            auto_applied.append("Crime: SOC-1")
        elif use_solomani:
            # Solomani Pride — SOC+1.
            soc = character.characteristics.get("SOC")
            sp_max = int(rules.species().get(character.species_id or "", {}).get("characteristic_maximum", 15))
            character.characteristics.set("SOC", min(soc + 1, sp_max))
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
            if use_zhodani:
                # Psionics (Zhodani) — direct PSI +2 grant; Prole elevation if PSI now > 8.
                old_psi = character.psi or 0
                new_psi = min(old_psi + 2, 15)
                character.psi = new_psi
                character.psi_tested = True
                auto_applied.append(f"Psionics: PSI +2 ({old_psi} → {new_psi})")
                soc_now = character.characteristics.get("SOC")
                if soc_now <= 9 and new_psi > 8:
                    # Prole elevated to Intendant.
                    character.characteristics.set("SOC", 10)
                    auto_applied.append("Prole elevated to Intendant: SOC raised to 10")
            else:
                # Psionics — test PSI immediately.
                psi_roll = dice.roll("2D")
                character.psi = psi_roll.total
                character.psi_tested = True
                auto_applied.append(f"Psionics: PSI tested, rolled {psi_roll.total}. Psion career available.")
        elif sub == 2:
            if use_vargr:
                # Aliens (Vargr) — gain Language 1 + Contact [Alien].
                character.add_skill("Language", level=1)
                character.associates.append(Associate(kind="contact", description="Contact [Alien Race]"))
                auto_applied.append("Aliens: Gained Language 1 and Contact [Alien Race]")
            else:
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
            if use_vargr:
                # Contact with Government (Vargr) — pack became well known, SOC+1.
                sp_max_v = int(rules.species().get(character.species_id or "", {}).get("characteristic_maximum", 15))
                soc_v = character.characteristics.get("SOC")
                character.characteristics.set("SOC", min(soc_v + 1, sp_max_v))
                auto_applied.append("Contact with Government: SOC+1")
            elif use_zhodani:
                # Contact with Government (Zhodani) — gain one Benefit roll.
                character.pending_benefit_rolls += 1
                auto_applied.append("Contact with Government: gained 1 Benefit roll")
            else:
                # Contact with Government / Confederation Elite.
                gov_label = "Met [Confederation Elite]" if use_solomani else "Met [Government Official] — Imperial contact"
                character.associates.append(
                    Associate(kind="contact", description=gov_label)
                )
                auto_applied.append(f"Noted {gov_label} in associates")
        elif sub == 6:
            # Ancient Technology (Vargr: believed left by the Ancients).
            item_label = "Ancient Technology (Ancients — Vargr Origin)" if use_vargr else "Ancient Technology"
            character.equipment.append(Equipment(name=item_label, notes="Unusual Event 12-6"))
            auto_applied.append(f"{item_label} added to equipment")
        auto_applied.insert(0, f"Unusual Event sub-roll: D6={sub}")

    # Fetch descriptive text from the appropriate life-events table.
    life_table_data = rules.life_events_for_career(career_id or "")
    event_text = life_table_data.get("entries", life_table_data).get(str(total), {})
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
      family_inheritance      → "benefit" | "soc"
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

    elif kind == "racial_incident":
        # Solomani Life Event — Racial Incident: a relationship suffers; gain a
        # Rival or an Enemy. (apply_life_event sets this kind for Solomani; the
        # non-Solomani equivalent is 'romantic_split'.)
        if choice == "rival":
            character.associates.append(Associate(kind="rival", description="Rival [Racial Incident]"))
            character.log("Solomani Life Event — Racial Incident: gained Rival")
        elif choice == "enemy":
            character.associates.append(Associate(kind="enemy", description="Enemy [Racial Incident]"))
            character.log("Solomani Life Event — Racial Incident: gained Enemy")
        else:
            raise ValueError(f"Unknown choice '{choice}' for racial_incident")

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

    elif kind == "drinax_arranged_marriage":
        if choice == "accept":
            old_soc = character.characteristics.get("SOC")
            character.characteristics.set("SOC", old_soc + 1)
            character.log(f"Drinax Life Event — Arranged Marriage accepted: SOC {old_soc}→{character.characteristics.get('SOC')}")
        elif choice == "decline":
            character.log("Drinax Life Event — Arranged Marriage declined: no change")
        else:
            raise ValueError(f"Unknown choice '{choice}' for drinax_arranged_marriage")

    elif kind == "drinax_star_guard":
        if choice == "sell":
            cash_roll = dice.roll("1D").total
            cash = cash_roll * 10_000
            character.credits += cash
            character.log(f"Drinax Good Fortune — Star Guard commission sold: Cr{cash:,} (1D={cash_roll}×Cr10,000)")
        elif choice == "commission":
            character.pending_transfer_career_id = "navy"
            character.dm_next_advancement += 12
            character.log(
                "Drinax Good Fortune — Star Guard commission accepted: auto-qualify Navy; "
                "dm_next_advancement +12 (guaranteed promotion first term)"
            )
        else:
            raise ValueError(f"Unknown choice '{choice}' for drinax_star_guard")

    elif kind == "drinax_duel_penalty":
        if choice == "lose_benefit":
            if character.pending_benefit_rolls <= 0:
                raise ValueError("No benefit rolls remaining to lose.")
            character.pending_benefit_rolls -= 1
            character.log("Drinax Misfortune — Duel penalty: lost 1 Benefit roll")
        elif choice == "lose_soc":
            old_soc = character.characteristics.get("SOC")
            character.characteristics.set("SOC", max(1, old_soc - 1))
            character.log(f"Drinax Misfortune — Duel penalty: SOC {old_soc}→{character.characteristics.get('SOC')}")
        elif choice == "lose_end":
            old_end = character.characteristics.get("END")
            character.characteristics.set("END", max(1, old_end - 1))
            character.log(f"Drinax Misfortune — Duel penalty: END {old_end}→{character.characteristics.get('END')}")
        else:
            raise ValueError(f"Unknown choice '{choice}' for drinax_duel_penalty")

    elif kind == "drinax_child_crisis":
        if choice == "child_dies":
            character.log("Drinax Wasteland Family Affairs — Child died: narrative outcome, no mechanical change")
        elif choice == "drifter":
            character.forced_next_career_id = "drifter"
            character.log("Drinax Wasteland Family Affairs — Left career to care for child: next career must be Drifter")
        elif choice == "rogue":
            character.forced_next_career_id = "rogue"
            character.log("Drinax Wasteland Family Affairs — Left career to care for child: next career must be Rogue")
        else:
            raise ValueError(f"Unknown choice '{choice}' for drinax_child_crisis")

    elif kind == "drinax_ship_berth":
        if choice == "rogue":
            character.pending_transfer_career_id = "rogue"
            character.log("Drinax Wasteland Good Fortune — Ship berth taken: auto-qualify for Rogue career")
        elif choice == "merchant":
            character.pending_transfer_career_id = "merchant"
            character.log("Drinax Wasteland Good Fortune — Ship berth taken: auto-qualify for Merchant career")
        elif choice == "decline":
            character.log("Drinax Wasteland Good Fortune — Ship berth declined")
        else:
            raise ValueError(f"Unknown choice '{choice}' for drinax_ship_berth")

    elif kind == "asim_family_aid":
        if choice == "pay":
            if character.pending_benefit_rolls <= 0:
                raise ValueError("No benefit rolls remaining to lose.")
            character.pending_benefit_rolls -= 1
            character.dm_next_advancement += 1
            character.log(
                "Asim Family Affairs — Helped impoverished family: lost 1 Benefit roll, "
                "gained DM+1 to next Advancement roll"
            )
        elif choice == "keep":
            character.log("Asim Family Affairs — Did not help impoverished family: no change")
        else:
            raise ValueError(f"Unknown choice '{choice}' for asim_family_aid")

    elif kind == "asim_misfortune_choice":
        if choice == "lose_benefit":
            if character.pending_benefit_rolls <= 0:
                raise ValueError("No benefit rolls remaining to lose.")
            character.pending_benefit_rolls -= 1
            character.log("Asim Misfortune — Dangerous misunderstanding: lost 1 Benefit roll")
        elif choice.startswith("lose_associate_"):
            idx_str = choice[len("lose_associate_"):]
            try:
                idx = int(idx_str)
            except ValueError:
                raise ValueError(f"Invalid associate index in choice '{choice}'")
            if idx < 0 or idx >= len(character.associates):
                raise ValueError(f"Associate index {idx} out of range")
            removed = character.associates.pop(idx)
            character.log(
                f"Asim Misfortune — Dangerous misunderstanding: lost {removed.kind} [{removed.description or 'unnamed'}]"
            )
        else:
            raise ValueError(f"Unknown choice '{choice}' for asim_misfortune_choice")

    elif kind == "hiver_great_manipulator":
        # Hiver Life Event 11: choose Deception, Diplomat, or Persuade
        valid = {"Deception", "Diplomat", "Persuade"}
        if choice not in valid:
            raise ValueError(f"Choice must be one of {valid!r}")
        log = character.add_skill(choice, level=1)
        character.log(f"Hiver Great Manipulator: gained {choice} 1 — {log}")

    elif kind == "droyne_starship_skill":
        # Droyne Life Event 2: choose Engineer, Electronics, Mechanic, or rank +1
        if choice == "rank +1":
            term = character.current_term
            if term is not None:
                term.rank = min(term.rank + 1, 6)
            character.log("Droyne Life Event — Build Starship: rank +1")
        elif choice in ("Engineer", "Electronics", "Mechanic"):
            log = character.add_skill(choice, level=1)
            character.log(f"Droyne Life Event — Build Starship: gained {choice} 1 — {log}")
        else:
            raise ValueError(f"Unknown choice '{choice}' for droyne_starship_skill")

    elif kind == "droyne_black_skill":
        # Droyne Life Event 4: choose a Black Skill
        valid_black = {"Carouse", "Deception", "Gambler", "Persuade", "Streetwise"}
        if choice not in valid_black:
            raise ValueError(f"Choice must be one of {valid_black!r}")
        log = character.add_skill(choice, level=1)
        character.log(f"Droyne Life Event — Black Skill: gained {choice} 1 — {log}")

    elif kind == "droyne_voyage_skill":
        # Droyne Life Event 10: choose Pilot, Astrogation, Engineer, or Electronics
        valid_voyage = {"Pilot", "Astrogation", "Engineer", "Electronics"}
        if choice not in valid_voyage:
            raise ValueError(f"Choice must be one of {valid_voyage!r}")
        log = character.add_skill(choice, level=1)
        character.log(f"Droyne Life Event — Voyage: gained {choice} 1 — {log}")

    elif kind == "drinax_weapon_choice":
        weapon_id = choice if choice in ("rapier", "laser_pistol") else "rapier"
        weapon_name = "Ancient Rapier" if weapon_id == "rapier" else "Laser Pistol"
        character.equipment.append(
            Equipment(name=weapon_name, notes="From Drinax Palace armoury (Good Fortune event)")
        )
        character.log(f"Drinax weapon choice: {weapon_name}")

    elif kind == "family_inheritance":
        # Life Event 2 (Family Affairs 5-6): extra Benefit roll OR SOC+1
        if choice == "benefit":
            character.pending_benefit_rolls += 1
            character.log("Family Affairs — Inheritance: gained 1 extra Benefit roll")
        elif choice == "soc":
            old_soc = character.characteristics.get("SOC")
            character.characteristics.set("SOC", old_soc + 1)
            character.log(f"Family Affairs — Inheritance: SOC {old_soc}→{character.characteristics.get('SOC')}")
        else:
            raise ValueError(f"Unknown choice '{choice}' for family_inheritance")

    elif kind == "species_skill_grant":
        # e.g. Dynchia Warrior People: gain Gun Combat 1 OR Melee 1
        options = pending.get("options", [])
        valid_ids = {o["id"] for o in options}
        if choice not in valid_ids:
            raise ValueError(
                f"Invalid choice '{choice}' for species_skill_grant. "
                f"Valid options: {', '.join(sorted(valid_ids))}"
            )
        # Parse "Skill (spec) N" or "Skill N"
        parts = choice.rsplit(" ", 1)
        skill_str = parts[0].strip()
        level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        sn, spec = _split_skill_speciality(skill_str)
        character.add_skill(sn, level=level, speciality=spec)
        disp = f"{sn}{f' ({spec})' if spec else ''} {level}"
        character.log(f"Species skill (Warrior People): gained {disp}")

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
    character.pre_career_terms += 1
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


_VARGR_DRAFT_TABLE: dict[int, tuple[str, str]] = {
    1: ("vargr_army", "infantry"),
    2: ("vargr_army", "infantry"),
    3: ("vargr_army", "infantry"),
    4: ("vargr_marines", "marine"),
    5: ("vargr_navy", "crew"),
    6: ("vargr_law_enforcement", "enforcer"),
}

_ZHODANI_DRAFT_TABLE: dict[int, tuple[str, str]] = {
    1: ("zhodani_army", "infantry"),
    2: ("zhodani_army", "infantry"),
    3: ("zhodani_army", "infantry"),
    4: ("zhodani_merchant", "corporate"),
    5: ("zhodani_merchant", "corporate"),
    6: ("zhodani_navy", "crew"),
}

# Solomani Confederation draft — Confederation services, not Imperial ones
# (mirrors the pre-career education event 11 Solomani draft).
_SOLOMANI_DRAFT_TABLE: dict[int, tuple[str, str]] = {
    1: ("confederation_navy", "line_crew"),
    2: ("confederation_army", "infantry"),
    3: ("solomani_marine", "star_marine"),
    4: ("merchant", "merchant_marine"),
    5: ("solsec", "field_agent"),
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
    if character.society_id == "vargr_extents":
        career_id, assignment_id = _VARGR_DRAFT_TABLE[max(1, min(6, r.total))]
    elif character.society_id == "zhodani_consulate":
        career_id, assignment_id = _ZHODANI_DRAFT_TABLE[max(1, min(6, r.total))]
    elif character.society_id == "solomani_confederation":
        career_id, assignment_id = _SOLOMANI_DRAFT_TABLE[max(1, min(6, r.total))]
    else:
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


# ============================================================
# Aslan Hierate Character Setup
# ============================================================


def begin_aslan_setup(character: Character) -> dict:
    """Initialise the Aslan Hierate background setup phase.

    Called when the player reaches the aslan_setup phase.
    Sets up the aslan_setup_status state machine.
    TER is already set to 0 by apply_species; it's populated from ancestry rolls.
    """
    sp_data = rules.species().get(character.species_id or "", {})
    if not sp_data.get("uses_clan_shares"):
        raise ValueError("begin_aslan_setup called for non-Aslan species")

    character.aslan_setup_status = {
        "phase": "gender",  # gender → clan → ancestry → family → rite → done
        "clan_type": None,
        "clan_dm_ancestral_deeds": 0,
        "ancestral_territory": 0,
        "past_deeds_rolls": [],
        "family_position": None,
        "inherits_territory": False,
        "rite_roll": None,
        "rite_score": 0,
        "rite_doubles": False,
        "rite_doubles_key": None,
    }
    character.log("Aslan background setup started. Choose gender.")
    return {"phase": "gender", "character": character.model_dump()}


def choose_aslan_gender(character: Character, gender: str) -> dict:
    """Set the Aslan character's gender. gender must be 'male' or 'female'."""
    if gender not in ("male", "female"):
        raise ValueError("Gender must be 'male' or 'female'")
    setup = character.aslan_setup_status
    if setup is None or setup.get("phase") != "gender":
        raise ValueError("Not in gender selection phase")

    character.gender = gender
    setup["phase"] = "clan"
    character.log(f"Gender chosen: {gender}.")
    return {"phase": "clan", "gender": gender, "character": character.model_dump()}


def roll_aslan_clan(character: Character) -> dict:
    """Determine clan membership.

    For Glorious Empire Aslan the clan is fixed (Tokouea'we, DM 0) — no dice
    are rolled.  For all other Hierate Aslan a 1D roll determines Minor or
    Major clan.
    """
    setup = character.aslan_setup_status
    if setup is None or setup.get("phase") != "clan":
        raise ValueError("Not in clan phase")

    sp_data = rules.species().get(character.species_id or "", {})
    fixed = sp_data.get("clan_determination") == "fixed"

    if fixed:
        # Glorious Empire: always Tokouea'we, no roll, DM 0
        clan_name = sp_data.get("fixed_clan_name", "Tokouea'we")
        clan_dm = int(sp_data.get("fixed_clan_dm", 0))
        setup["clan_type"] = clan_name
        setup["clan_dm_ancestral_deeds"] = clan_dm
        setup["phase"] = "ancestry"
        character.log(
            f"Clan: {clan_name} (all Glorious Empire Aslan are Tokouea'we; "
            f"DM{clan_dm:+d} to Ancestral Deeds)"
        )
        return {
            "phase": "ancestry",
            "roll": None,
            "clan_type": clan_name,
            "dm_ancestral_deeds": clan_dm,
            "fixed_clan": True,
            "character": character.model_dump(),
        }

    # Normal Hierate: roll 1D
    r = dice.roll("1D")
    tables = rules.aslan_background_tables()
    clan_results = tables["clan"]["results"]
    result = clan_results[str(r.total)]

    setup["clan_type"] = result["label"]
    setup["clan_dm_ancestral_deeds"] = result["dm_ancestral_deeds"]
    setup["phase"] = "ancestry"

    character.log(f"Clan roll: 1D={r.total} → {result['label']} (DM{result['dm_ancestral_deeds']:+d} to Ancestral Deeds)")
    return {
        "phase": "ancestry",
        "roll": r.to_dict(),
        "clan_type": result["label"],
        "dm_ancestral_deeds": result["dm_ancestral_deeds"],
        "fixed_clan": False,
        "character": character.model_dump(),
    }


def roll_aslan_ancestry(character: Character) -> dict:
    """Roll Ancestral Deeds (1D) and twice on Past Deeds (2D).

    Calculates the starting Ancestral Territory (TER).

    For Glorious Empire Aslan the clan DM is always 0, but males with STR 10+
    and females with INT 8+ receive DM+1 on the Ancestral Deeds roll instead.
    """
    setup = character.aslan_setup_status
    if setup is None or setup.get("phase") != "ancestry":
        raise ValueError("Not in ancestry phase")

    tables = rules.aslan_background_tables()
    dm_from_clan = setup.get("clan_dm_ancestral_deeds", 0)

    # Glorious Empire stat-based DM bonus (overrides or supplements clan DM)
    sp_data = rules.species().get(character.species_id or "", {})
    stat_bonus_cfg = sp_data.get("ancestry_stat_bonus")
    dm_from_stat = 0
    stat_bonus_note = ""
    if stat_bonus_cfg:
        gender = character.gender or "male"
        cond = stat_bonus_cfg.get(gender, {})
        stat_name = cond.get("characteristic", "")
        stat_min = int(cond.get("min", 99))
        char_val = character.characteristics.get(stat_name) if stat_name else 0
        if char_val >= stat_min:
            dm_from_stat = 1
            stat_bonus_note = f"{stat_name} {char_val} ≥ {stat_min}: DM+1 to Ancestral Deeds"

    total_dm = dm_from_clan + dm_from_stat

    # Ancestral Deeds roll (1D + total DM, min 1 max 7)
    r_ancestral = dice.roll("1D", modifier=total_dm)
    key_a = str(max(1, min(7, r_ancestral.total)))
    ancestral_result = tables["ancestral_deeds"]["results"][key_a]
    territory = ancestral_result["territory"]

    # Past Deeds — roll twice (grandfather then father)
    past_rolls = []
    for who in ("Grandfather's deeds", "Father's deeds"):
        r_past = dice.roll("2D")
        key_p = str(r_past.total)
        past_result = tables["past_deeds"]["results"][key_p]
        past_ter = past_result.get("territory", 0)
        if past_ter == "lose_all":
            territory = 0
        else:
            territory += int(past_ter)
            territory = max(0, territory)
        past_rolls.append({
            "who": who,
            "roll": r_past.to_dict(),
            "key": key_p,
            "label": past_result["label"],
            "territory_change": past_ter,
            "bonus": past_result.get("bonus") or past_result.get(
                "bonus_male" if character.gender == "male" else "bonus_female"
            ),
        })

    setup["ancestral_territory"] = territory
    setup["past_deeds_rolls"] = past_rolls
    setup["phase"] = "family"

    # TER = Ancestral Territory (SOC is independent and unchanged)
    character.extra_characteristics["TER"] = max(0, territory)

    # TER 10+ male: gain Leadership 1
    bonus_notes = []
    if character.gender == "male" and territory >= 10:
        character.add_skill("Leadership", level=1)
        bonus_notes.append("TER 10+ male: Leadership 1 gained")

    dm_note = f"DM{total_dm:+d}" if total_dm != 0 else "no DM"
    log_parts = [
        f"Ancestry: Ancestral Deeds 1D ({dm_note})={r_ancestral.total} → {territory} Ancestral Territory.",
        f"TER set to {territory}.",
    ]
    if stat_bonus_note:
        log_parts.append(stat_bonus_note)
    character.log(" ".join(log_parts))
    return {
        "phase": "family",
        "ancestral_roll": r_ancestral.to_dict(),
        "ancestral_result": ancestral_result,
        "past_deeds_rolls": past_rolls,
        "ancestral_territory": territory,
        "ter_set_to": territory,
        "bonus_notes": bonus_notes,
        "stat_bonus_note": stat_bonus_note,
        "character": character.model_dump(),
    }


def roll_aslan_family(character: Character) -> dict:
    """Roll on the Family Inheritance table (2D) to determine birth order."""
    setup = character.aslan_setup_status
    if setup is None or setup.get("phase") != "family":
        raise ValueError("Not in family phase")

    r = dice.roll("2D")
    tables = rules.aslan_background_tables()
    key = str(r.total)
    result = tables["family_inheritance"]["results"][key]

    gender = character.gender or "male"
    label_key = f"label_{gender}"
    position = result.get(label_key, result.get("label_male", "Unknown"))
    inherits = result.get("inherits_territory", False)

    # Only the first son/eldest daughter inherits full Ancestral Territory.
    # Non-heirs have TER reset to 0. SOC is not affected.
    if not inherits:
        character.extra_characteristics["TER"] = 0
        setup["ancestral_territory"] = 0

    setup["family_position"] = position
    setup["inherits_territory"] = inherits
    setup["phase"] = "rite"

    ter = character.extra_characteristics.get("TER", 0)
    character.log(
        f"Family: 2D={r.total} → {position} ({'inherits' if inherits else 'does not inherit'} territory). "
        f"TER = {ter}."
    )
    return {
        "phase": "rite",
        "roll": r.to_dict(),
        "family_position": position,
        "inherits_territory": inherits,
        "ter": ter,
        "character": character.model_dump(),
    }


def roll_aslan_rite(character: Character) -> dict:
    """Roll the Rite of Passage (2D). Calculate score. Handle doubles events."""
    setup = character.aslan_setup_status
    if setup is None or setup.get("phase") != "rite":
        raise ValueError("Not in rite phase")

    r = dice.roll("2D")
    die1 = r.dice[0] if r.dice else 0
    die2 = r.dice[1] if len(r.dice) > 1 else 0
    is_doubles = die1 == die2

    gender = character.gender or "male"
    score = 0

    if gender == "male":
        # Male: score = X (the 2D roll) + Y (count of STR/DEX/END/INT/EDU/SOC that exceed X)
        count_above = sum(
            1 for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC")
            if character.characteristics.get(stat) > r.total
        )
        score = r.total + count_above
    else:
        # Female: score = X (the 2D roll) + 2 for each of INT/EDU/SOC that exceeds X
        score = r.total
        for stat in ("INT", "EDU", "SOC"):
            if character.characteristics.get(stat) > r.total:
                score += 2

    # Doubles event — detect, apply, and record
    doubles_key = None
    doubles_result = None
    doubles_applied: list[str] = []
    if is_doubles:
        doubles_key = f"{die1}+{die2}"
        tables = rules.aslan_background_tables()
        doubles_result = tables.get("rite_of_passage_events", {}).get("results", {}).get(doubles_key)

        if doubles_result:
            bonus = doubles_result.get("bonus")
            if bonus == "1D Clan Shares":
                cs_roll = dice.roll("1D")
                character.clan_shares += cs_roll.total
                doubles_applied.append(f"Gained {cs_roll.total} Clan Share{'s' if cs_roll.total != 1 else ''} (1D={cs_roll.total})")
            elif bonus == "Cr5000":
                character.credits += 5000
                doubles_applied.append("Gained Cr5,000")
            elif bonus == "Contact":
                character.associates.append(
                    Associate(kind="contact", description="Aslan met during the Rite of Passage")
                )
                doubles_applied.append("Gained a Contact (Aslan from the Rite)")
            elif bonus == "Rival":
                character.associates.append(
                    Associate(kind="rival", description="Aslan rival from the Rite of Passage")
                )
                doubles_applied.append("Gained a Rival (Aslan from the Rite)")
            elif bonus == "END +1":
                current_end = character.characteristics.END
                character.characteristics.set("END", current_end + 1)
                doubles_applied.append(f"END +1 (now {character.characteristics.END})")
            elif bonus is None:
                # 5+5: scar — cosmetic only
                doubles_applied.append("Distinctive scar across your fur (no mechanical effect)")

    setup["rite_roll"] = r.to_dict()
    setup["rite_score"] = score
    setup["rite_doubles"] = is_doubles
    setup["rite_doubles_key"] = doubles_key
    setup["phase"] = "done"

    # Transition character to background phase so Aslan can pick gender-specific
    # background skills and optionally attend Aslan University before careers.
    character.phase = "background"

    character.log(
        f"Rite of Passage: 2D={r.total} ({die1},{die2}). Score={score}."
        + (f" Doubles! Event {doubles_key}: {doubles_result['label'] if doubles_result else '?'}." if is_doubles else "")
        + (f" {' '.join(doubles_applied)}" if doubles_applied else "")
    )
    return {
        "phase": "done",
        "roll": r.to_dict(),
        "rite_total": r.total,
        "is_doubles": is_doubles,
        "doubles_key": doubles_key,
        "doubles_result": doubles_result,
        "doubles_applied": doubles_applied,
        "rite_score": score,
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

    # ── Species / career access controls ──────────────────────────────────────
    # These gates apply before any qualification roll and before auto-qualify paths.
    _qual_sp_data = rules.species().get(character.species_id or "", {})

    def _qual_block(reason: str) -> dict:
        character.log(f"Qualification blocked: {reason}")
        character.failed_qualifications_this_term += 1
        return {"automatic": False, "succeeded": False,
                "character": character.model_dump(), "roll": None, "reason": reason}

    # Species blocked_careers (e.g. Dolphins cannot enter Merchant/Noble/Drifter)
    if career_id in (_qual_sp_data.get("blocked_careers") or []):
        return _qual_block(f"{_qual_sp_data.get('name', 'This species')} cannot enter {career['name']}.")

    # Species allowed_species_careers whitelist (e.g. Dolphins can only enter dolphin_civilian/dolphin_military)
    _sp_allowed = _qual_sp_data.get("allowed_species_careers") or []
    if _sp_allowed and career_id not in _sp_allowed:
        return _qual_block(
            f"{_qual_sp_data.get('name', 'This species')} can only enter species-specific careers "
            f"({', '.join(_sp_allowed)})."
        )

    # Species allowed_career_ids whitelist (e.g. Floriani Feskal/Barnai — restricted career lists)
    _sp_career_allowed = _qual_sp_data.get("allowed_career_ids") or []
    if _sp_career_allowed and career_id not in _sp_career_allowed:
        _readable = ", ".join(c.capitalize() for c in _sp_career_allowed
                              if c not in ("drifter", "prisoner"))
        return _qual_block(
            f"{_qual_sp_data.get('name', 'This species')} may only enter: {_readable}."
        )

    # vacc_suit_required_for_core_careers: must have Vacc Suit 0+ to enter standard core careers
    if _qual_sp_data.get("vacc_suit_required_for_core_careers"):
        _CORE_CAREERS = {"agent", "army", "citizen", "drifter", "entertainer",
                         "marine", "merchant", "navy", "noble", "rogue", "scholar", "scout"}
        if career_id in _CORE_CAREERS:
            _has_vacc = any(
                sk.name.lower() == "vacc suit" and sk.speciality is None
                for sk in character.skills
            )
            if not _has_vacc:
                return _qual_block(
                    f"Vacc Suit 0 required before {_qual_sp_data.get('name', 'this species')} "
                    f"can enter {career['name']}."
                )

    # Career blocked_societies (e.g. Imperial careers blocked to Solomani Confederation)
    if character.society_id in (career.get("blocked_societies") or []):
        return _qual_block(f"{career['name']} is not available to {character.society_id} characters.")

    # Career allowed_societies whitelist (e.g. Party requires solomani_confederation)
    _career_allowed_societies = career.get("allowed_societies") or []
    if _career_allowed_societies and character.society_id not in _career_allowed_societies:
        return _qual_block(
            f"{career['name']} is only available to Solomani Confederation characters."
        )

    # Solomani Party: Non-Solomani humans cannot qualify, regardless of SOC.
    # Mixed Heritage may qualify with a DM-3 penalty (or be treated as Racial if passing).
    if career_id == "party" and character.society_id == "solomani_confederation":
        if character.species_id == "confederation_human":
            return _qual_block(
                "Non-Solomani humans cannot qualify for the Solomani Party."
            )

    # Career blocked_species
    if character.species_id in (career.get("blocked_species") or []):
        return _qual_block(
            f"{career['name']} is not available to "
            f"{_qual_sp_data.get('name', character.species_id)}."
        )

    # Career allowed_species whitelist
    _career_allowed_species = career.get("allowed_species") or []
    if _career_allowed_species and character.species_id not in _career_allowed_species:
        return _qual_block(f"{career['name']} is restricted to specific species.")

    # Storm Knight cross-Order ejection block:
    # A career-ending mishap in any Order bars entry to all three Orders.
    _STORM_KNIGHT_IDS = {"storm_knight_thunder", "storm_knight_inconstant_star", "storm_knight_shadows"}
    if career_id in _STORM_KNIGHT_IDS:
        if character.storm_knight_ejected:
            return _qual_block(
                "A career-ending mishap in a Storm Knight Order bars entry to all other Orders."
            )
        # Also check completed_careers in case the flag wasn't set (legacy saves)
        for _cr in character.completed_careers:
            if _cr.career_id in _STORM_KNIGHT_IDS and _cr.left_due_to == "mishap":
                character.storm_knight_ejected = True
                return _qual_block(
                    "A career-ending mishap in a Storm Knight Order bars entry to all other Orders."
                )

    # Aslan gender_restriction (e.g. envoy = male-only, management = female-only)
    _gender_req = career.get("gender_restriction")
    if _gender_req and character.gender and character.gender != _gender_req:
        return _qual_block(
            f"{career['name']} is only available to {_gender_req} characters."
        )

    # Zhodani prole_career: Nobles and Intendants cannot enter Prole careers
    if career.get("prole_career") and character.species_id == "zhodani":
        if _zhodani_class(character.characteristics.get("SOC") or 0) in ("noble", "intendant"):
            return _qual_block("Zhodani Nobles and Intendants cannot enter Prole careers.")

    # Ihatei core-career restriction: character must join a Core Rulebook career
    # (societies absent, empty, or includes "third_imperium").
    if character.next_career_must_be_core:
        career_societies = career.get("societies") or []
        is_core = (
            not career_societies
            or "third_imperium" in career_societies
        )
        if not is_core:
            return _qual_block(
                "Having joined the ihatei, you must qualify for a Core Rulebook career this term "
                f"({career['name']} is restricted to {', '.join(career_societies)})."
            )
        # Career is core — consume the flag (allow this qualification to proceed)
        character.next_career_must_be_core = False
        character.log(f"Ihatei core-career restriction satisfied by {career['name']} — flag cleared.")

    # ── Imperial Guard prerequisite gate ─────────────────────────────────────
    if career_id == "imperial_guard":
        _IG_SOURCE = {"army", "marine", "confederation_army", "solomani_marine",
                      "vargr_army", "vargr_marines", "zhodani_army", "zhodani_guard"}
        # One attempt only — add to banned_career_ids on any failure
        if "imperial_guard" in character.banned_career_ids:
            return _qual_block(
                "Imperial Guard: you have already attempted qualification and been refused. "
                "Future attempts are permanently barred."
            )
        # Must currently be serving in Army or Marines
        cur = character.current_term
        if cur is None or cur.career_id not in _IG_SOURCE:
            return _qual_block(
                "Imperial Guard: you must be currently serving in the Army or Marines to apply."
            )
        # Must have received a promotion in this (current) term
        if not cur.advanced:
            return _qual_block(
                "Imperial Guard: you must have received a promotion in the term immediately "
                "prior to application."
            )
        # No mishaps in the entire career history
        _has_mishap = any(
            (h.mishap and h.mishap.strip()) or h.survived is False
            for h in character.term_history
        )
        if _has_mishap:
            return _qual_block(
                "Imperial Guard: applicants must have an unblemished record — no mishaps "
                "may have occurred during the Traveller's career."
            )
        # STR or END must be 10+
        if (character.characteristics.STR < 10 and character.characteristics.END < 10):
            return _qual_block(
                "Imperial Guard: STR or END 10+ is required."
            )
        # Vacc Suit 1 or higher
        _vacc_level = next(
            (sk.level for sk in character.skills
             if sk.name.lower() == "vacc suit" and sk.speciality is None),
            -1
        )
        if _vacc_level < 1:
            return _qual_block(
                "Imperial Guard: Vacc Suit 1 or higher is required."
            )

    # Imperial Naval Intelligence: must currently be serving in a Navy career.
    # Failure is NOT permanent — the posting is simply denied this term.
    _INI_NAVY_SOURCE = {"navy", "confederation_navy", "vargr_navy", "zhodani_navy"}
    if career_id == "ini":
        _ini_cur = character.current_term
        if _ini_cur is None or _ini_cur.career_id not in _INI_NAVY_SOURCE:
            return _qual_block(
                "Imperial Naval Intelligence: you must currently be serving in the Navy "
                "to request an INI field-agent posting."
            )
        # No permanent ban on failure — posting denied, character may try again next term.

    # INI return to Navy: if the character is leaving INI and returning to their Navy career,
    # no qualification roll is required — they simply re-enter at their held rank.
    if career_id in _INI_NAVY_SOURCE and character.ini_can_return_to_navy:
        _src = character.ini_source_career_id or ""
        if _src == career_id or _src in _INI_NAVY_SOURCE:
            if character.ini_frozen_navy_rank is not None:
                character.pending_transfer_rank = character.ini_frozen_navy_rank
            character.ini_can_return_to_navy = False
            character.ini_frozen_navy_rank = None
            character.log(
                f"INI → Navy: auto-qualified (no roll required); "
                f"Navy rank {character.pending_transfer_rank} restored."
            )
            _ini_return_result = {
                "total": 12, "succeeded": True, "natural": 12, "modifier": 0, "target": 0,
                "characteristic_used": "Auto (INI return)", "pending_dm_consumed": 0,
            }
            return {"succeeded": True, "roll": _ini_return_result, "character": character.model_dump()}

    qual = career.get("qualification", {})
    if qual.get("automatic"):
        # Droyne caste check: career is locked to a specific caste
        required_caste = career.get("droyne_caste")
        if required_caste and character.droyne_caste != required_caste:
            character.log(
                f"Droyne caste mismatch: {career['name']} requires {required_caste} caste, "
                f"character is {character.droyne_caste or 'uncasted'}."
            )
            character.failed_qualifications_this_term += 1
            return {
                "automatic": False, "succeeded": False,
                "character": character.model_dump(),
                "roll": None,
                "reason": f"This career is only open to the {required_caste.capitalize()} caste.",
            }
        # Hiver career nest-type qualification.
        # Careers with hiver_open_to=['any'] allow all nest types automatically.
        # Careers with a specific nest list require either a matching nest OR a
        # minimum-qualification roll (with the species-level DM penalties).
        _hiver_open_to = career.get("hiver_open_to") or []
        if _hiver_open_to and "any" not in _hiver_open_to:
            _nest = character.hiver_nest_type or ""
            if _nest not in _hiver_open_to:
                # Check full qualification skills first (bypasses penalty entirely)
                _full_qual = career.get("hiver_full_qualification") or []
                def _skill_at_level(skill_str: str) -> bool:
                    parts = skill_str.rsplit(" ", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        return any(
                            sk.name == parts[0].strip() and sk.level >= int(parts[1])
                            for sk in character.skills
                        )
                    return False
                _fully_qual = _full_qual and all(_skill_at_level(s) for s in _full_qual)
                if _fully_qual:
                    character.log(
                        f"Hiver career {career['name']}: nest mismatch waived — "
                        f"fully qualified ({', '.join(_full_qual)})."
                    )
                    # Falls through to automatic return below
                else:
                    # Roll minimum qualification check with penalty DM
                    _hiver_penalties = rules.species().get("hiver", {}).get(
                        "hiver_qualification_penalties", {}
                    )
                    _min_qual = career.get("hiver_min_qualification") or {}
                    _char_key = _min_qual.get("characteristic", "EDU")
                    _min_target = int(_min_qual.get("target", 8))
                    _char_dm_val = dice.characteristic_dm(
                        character.characteristics.get(_char_key) or 0
                    )
                    _meets_dm = int(_hiver_penalties.get("meets_minimum", -2))
                    _fails_dm = int(_hiver_penalties.get("does_not_meet_minimum", -6))
                    _roll_dm = _char_dm_val + _meets_dm
                    _r = dice.roll("2D", modifier=_roll_dm, target=_min_target)
                    character.log(
                        f"Hiver career {career['name']}: wrong nest ({_nest!r}, needs "
                        f"{_hiver_open_to}). Min qual: {_char_key} {_min_target}+, "
                        f"2D{_roll_dm:+d} = {_r.total} — "
                        f"{'PASS' if _r.succeeded else 'FAIL'}."
                    )
                    if not _r.succeeded:
                        character.failed_qualifications_this_term += 1
                        return {
                            "automatic": False, "succeeded": False,
                            "character": character.model_dump(),
                            "roll": _r.to_dict(),
                            "reason": (
                                f"Failed minimum qualification for {career['name']}: "
                                f"wrong nest type and {_char_key} check failed."
                            ),
                        }
                    return {
                        "automatic": False, "succeeded": True,
                        "character": character.model_dump(),
                        "roll": _r.to_dict(),
                    }

        character.log(f"Automatic qualification for {career['name']}.")
        return {"automatic": True, "succeeded": True, "character": character.model_dump()}

    # K'kree SOC-range qualification
    if "soc_min" in qual or "soc_max" in qual:
        soc = character.characteristics.SOC
        soc_min = qual.get("soc_min", 0)
        soc_max = qual.get("soc_max", 99)
        career_name = career.get("name", career_id)
        if soc_min <= soc <= soc_max:
            character.log(f"K'kree caste qualification for {career_name}: SOC {soc} is within range {soc_min}-{soc_max}.")
            return {"automatic": True, "succeeded": True, "character": character.model_dump()}
        else:
            character.log(f"K'kree caste qualification failed for {career_name}: SOC {soc} not in range {soc_min}-{soc_max}.")
            character.failed_qualifications_this_term += 1
            return {"automatic": False, "succeeded": False, "character": character.model_dump(),
                    "roll": None, "reason": f"SOC {soc} not in range {soc_min}–{soc_max} for {career_name}"}

    auto_qualify = qual.get("auto_qualify_if")
    if auto_qualify:
        # e.g. {"SOC": ">=10"} for Noble
        for stat, cond in auto_qualify.items():
            if cond.startswith(">="):
                threshold = int(cond[2:])
                if character.characteristics.get(stat) >= threshold:
                    character.log(f"Auto-qualified for {career['name']} (SOC ≥ {threshold}).")
                    return {"automatic": True, "succeeded": True, "character": character.model_dump()}

    # Event-granted auto-qualify for specific career(s) (e.g. Party event 3 for Citizen/Merchant)
    if career_id in character.auto_qualify_career_ids:
        character.auto_qualify_career_ids = [
            c for c in character.auto_qualify_career_ids if c != career_id
        ]
        character.dm_next_advancement += 2  # Party event 3 also grants DM+2 advancement
        character.log(
            f"Auto-qualified for {career['name']} (Party event 3 benefit). DM+2 next advancement."
        )
        return {"automatic": True, "succeeded": True, "character": character.model_dump()}

    char_key = qual["characteristic"]
    target = qual["target"]

    # Aslan: Scientist male_target override — males need a higher Rite score
    if career.get("male_target") is not None and character.gender == "male":
        target = career["male_target"]

    # Special case: DEX_OR_INT (Entertainer)
    if char_key == "DEX_OR_INT":
        dm = max(
            dice.characteristic_dm(character.characteristics.DEX),
            dice.characteristic_dm(character.characteristics.INT),
        )
        char_display = "DEX or INT (higher)"
    elif char_key == "RITE_OF_PASSAGE":
        # Aslan: Rite of Passage score is used as the DM directly (not characteristic DM)
        rite_score = (character.aslan_setup_status or {}).get("rite_score", 0)
        dm = rite_score
        char_display = f"Rite of Passage ({rite_score})"
    else:
        dm = dice.characteristic_dm(_get_stat(character, char_key))
        char_display = char_key

    # Apply modifiers
    for mod in qual.get("modifiers", []):
        if mod["type"] == "per_previous_career":
            dm += mod["dm"] * len(character.completed_careers)
        elif mod["type"] == "per_previous_term":
            dm += mod["dm"] * character.total_terms
        elif mod["type"] == "age" and character.age >= mod.get("threshold", mod.get("age_threshold", 99)):
            dm += mod["dm"]
        elif mod["type"] == "last_career":
            # DM applies if the most recent completed career is in the list
            careers_list = mod.get("careers", [])
            if character.completed_careers and character.completed_careers[-1].career_id in careers_list:
                dm += mod["dm"]
        elif mod["type"] == "soc_minimum":
            # DM if SOC meets or exceeds threshold
            if character.characteristics.SOC >= mod.get("soc", 99):
                dm += mod["dm"]
        elif mod["type"] == "characteristic_minimum":
            # DM+N if a characteristic meets or exceeds a minimum value
            _char_val = _get_stat(character, mod.get("characteristic", "STR"))
            if _char_val >= mod.get("min_value", 99):
                dm += mod["dm"]

    # Apply permanent pre-career education DMs
    pdms = character.pre_career_permanent_dms or {}

    # Psion auto-entry (Psionic Community graduate)
    if career_id == "psion" and pdms.get("psion_career_auto_entry"):
        character.log(f"Psionic Community graduate — automatic entry into Psion career.")
        return {"automatic": True, "succeeded": True, "character": character.model_dump()}

    # Careers that require PSI to have been tested: block if PSI is untested or 0.
    if career.get("qualification_requires_psi_tested") and not character.psi_tested:
        character.failed_qualifications_this_term += 1
        character.log("Psion qualification blocked — PSI must be tested first (visit a Psionics Institute).")
        return {
            "automatic": False, "succeeded": False, "character": character.model_dump(),
            "roll": None,
            "reason": "You must test for psionic potential before entering the Psion career.",
        }

    # Aslan event 2 free-qualify for Outlaw/Wanderer
    if _consume_aslan_outlaw_wanderer_free_qualify(character, career_id):
        character.log(
            f"Aslan University event 2 benefit — free qualification for {career['name']}."
        )
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

    # Species-specific career qualify DMs (e.g. Dolphins gain DM+1 for Scholar and Scout)
    species_data = rules.species().get(character.species_id or "", {})
    species_career_dms = species_data.get("career_qualify_dms", {})
    if career_id in species_career_dms:
        dm += int(species_career_dms[career_id])

    # Solomani species traits apply to all careers a Confederation character
    # can take — any career with a qualification roll except Drifter/Prisoner.
    _is_solomani_confederation = character.society_id == "solomani_confederation"
    _has_qualification = career_id not in rules.CAREERS_WITHOUT_QUALIFICATION

    # Party Patronage: Racial Solomani (or a Mixed Heritage character who is
    # currently "passing" with falsified documents) add their SOC DM to every
    # qualification roll in Confederation careers.
    party_patronage_dm = 0
    _is_treated_racial = (
        character.species_id == "solomani_racial"
        or (character.species_id == "solomani_mixed" and character.solomani_passing)
    )
    if _is_solomani_confederation and _is_treated_racial and _has_qualification:
        soc_val = character.characteristics.SOC
        party_patronage_dm = dice.characteristic_dm(soc_val)
        if party_patronage_dm != 0:
            dm += party_patronage_dm

    # Mixed Heritage: DM penalty on Confederation career qualification rolls.
    #   - Passing characters are treated as Racial — no penalty.
    #   - Party career: DM-3 (raw rulebook rule specific to Party).
    #   - All other Confederation careers: DM-1 general penalty.
    mixed_heritage_dm = 0
    if (
        _is_solomani_confederation
        and character.species_id == "solomani_mixed"
        and _has_qualification
        and not character.solomani_passing
    ):
        mixed_heritage_dm = -3 if career_id == "party" else -1
        dm += mixed_heritage_dm

    # RAW: DM-1 for each career previously attempted (failed) this selection round.
    # Vargr Extents (no_career_change_penalty) are exempt from this penalty.
    failed_dm = -character.failed_qualifications_this_term
    if failed_dm and not species_data.get("no_career_change_penalty"):
        dm += failed_dm

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
        label = "Party Patronage (Passing)" if character.species_id == "solomani_mixed" else "Party Patronage"
        qual_notes.append(f"{label} DM{party_patronage_dm:+d}")
    if mixed_heritage_dm:
        label = f"Mixed Heritage (Party) DM{mixed_heritage_dm:+d}" if career_id == "party" else f"Mixed Heritage DM{mixed_heritage_dm:+d}"
        qual_notes.append(label)
    if failed_dm:
        qual_notes.append(f"Failed attempts DM{failed_dm:+d}")
    note_str = f" [{', '.join(qual_notes)}]" if qual_notes else ""
    character.log(
        f"Qualification for {career['name']}: 2D{dm:+d} vs {target}+ "
        f"= {r.total} ({'pass' if r.succeeded else 'fail'}){note_str}"
    )

    # Track failed attempts for subsequent rolls this round
    if not r.succeeded:
        character.failed_qualifications_this_term += 1
        # Imperial Guard failure is permanent — ban future attempts
        if career_id == "imperial_guard":
            if "imperial_guard" not in character.banned_career_ids:
                character.banned_career_ids.append("imperial_guard")
            character.log("Imperial Guard qualification failed — permanently barred from future attempts.")

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

    # Validate gender restriction for Aslan assignments
    assignment_data = career["assignments"][assignment_id]
    allowed_genders = assignment_data.get("allowed_genders")
    if allowed_genders and character.gender and character.gender not in allowed_genders:
        raise ValueError(
            f"Assignment '{assignment_data.get('name', assignment_id)}' is restricted to "
            f"{'/'.join(allowed_genders)} characters. This character is {character.gender}."
        )

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
    pdms = character.pre_career_permanent_dms or {}
    is_first_career = len(character.completed_careers) == 0 and character.total_terms == 0

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
        academy_commission_roll["label"] = "Academy Commission Roll"
        character.academy_commission_career_id = None
        character.academy_commission_dm = 0
        character.log(
            f"Academy commission roll: 2D+{comm_dm} vs {comm_target}+ "
            f"= {r_comm.total} ({'commissioned' if commissioned_start else 'not commissioned'})"
        )

    # University graduate: may attempt a Commission roll before the first term
    # of a military career; honours grants DM+2.
    if (
        first_term_in_this_career
        and not commissioned_start
        and is_first_career
        and career_id in list(pdms.get("university_commission_careers", []))
    ):
        comm_data = career.get("commission", {})
        comm_target = comm_data.get("target", 8)
        comm_dm = int(pdms.get("university_commission_dm", 0))
        r_comm = dice.roll("2D", modifier=comm_dm, target=comm_target)
        commissioned_start = bool(r_comm.succeeded)
        academy_commission_roll = r_comm.to_dict()
        academy_commission_roll["label"] = "University Commission Roll"
        character.log(
            f"University commission roll: 2D{comm_dm:+d} vs {comm_target}+ "
            f"= {r_comm.total} ({'commissioned' if commissioned_start else 'not commissioned'})"
        )

    # Merchant Academy auto_rank: first career in a matching career starts at rank N.
    auto_rank = int(pdms.get("auto_rank", 0))
    auto_rank_careers = list(pdms.get("auto_rank_careers", []))
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
    elif character.pending_transfer_rank is not None and is_new_career:
        # Rank carried over from a career-transfer event (e.g. Zhodani Merchant → Zhodani Navy)
        starting_rank = character.pending_transfer_rank
        character.pending_transfer_rank = None
        if starting_rank > 0:
            commissioned_start = True  # suppress basic training; log as ranked entry
        character.log(f"Rank {starting_rank} carried over from career transfer.")
    elif not is_new_career and character.current_term is not None:
        starting_rank = character.current_term.rank
    else:
        starting_rank = 0

    # Imperial Guard: record the source Army/Marines career before we replace current_term
    if career_id == "imperial_guard" and first_term_in_this_career:
        if character.current_term is not None:
            character.imperial_guard_source_career_id = character.current_term.career_id
            character.log(
                f"Imperial Guard: source career recorded as '{character.current_term.career_id}'."
            )

    # INI: record source Navy career and freeze the Navy rank before we replace current_term
    if career_id == "ini" and first_term_in_this_career:
        if character.current_term is not None:
            character.ini_source_career_id = character.current_term.career_id
            character.ini_frozen_navy_rank = character.current_term.rank
            character.log(
                f"INI: source career recorded as '{character.current_term.career_id}', "
                f"Navy rank {character.current_term.rank} frozen for duration of service."
            )

    term = CareerTerm(
        career_id=career_id,
        assignment_id=assignment_id,
        term_number=1 if is_new_career else (character.current_term.term_number + 1),
        overall_term_number=character.total_terms + character.pre_career_terms + 1,
        rank=starting_rank,
        rank_title=_rank_title(career, assignment_id, starting_rank, commissioned=commissioned_start),
        basic_training=is_first_career and not commissioned_start,
        commissioned=commissioned_start,
        cover_career_id=cover_career_id or None,
    )
    character.current_term = term

    # Consume the auto-commission flag so subsequent terms don't re-trigger it.
    if character.starts_commissioned_career_id == career_id:
        character.starts_commissioned_career_id = None

    # all_commissioned: some careers auto-commission all characters at first term
    # (e.g. Zhodani Guard — all ranks are officer equivalents).
    if career.get("all_commissioned") and first_term_in_this_career and not term.commissioned:
        term.commissioned = True
        term.rank = 1
        term.rank_title = _rank_title(career, assignment_id, 1, commissioned=True)
        character.log(f"Auto-commissioned on entry to {career['name']} (all_commissioned career).")

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

    # Prisoner career: roll the Parole Threshold (1D+2, never above 12) on entry.
    # Persists across terms in prison; cleared on release (see end_term).
    if career_id == "prisoner" and first_term_in_this_career and character.parole_threshold is None:
        pt = dice.roll("1D").total + 2
        character.parole_threshold = min(pt, 12)
        character.log(
            f"Parole Threshold set to {character.parole_threshold} (1D+2). Each term, an "
            f"advancement roll greater than this ends the sentence."
        )

    # Initialize career-specific extra characteristics (e.g. Truther's FOL starts at 0)
    if first_term_in_this_career:
        for ec_key, ec_val in career.get("extra_characteristic_start", {}).items():
            if ec_key not in character.extra_characteristics:
                character.extra_characteristics[ec_key] = int(ec_val)
                character.log(f"  Career entry: {ec_key} initialized to {ec_val}")

    # Apply rank-0 bonus (e.g. Army Private gets Gun Combat 1).
    rank0_data = _rank_data(career, assignment_id, 0)
    if rank0_data and rank0_data.get("bonus") and first_term_in_this_career and not commissioned_start:
        bonus0 = rank0_data["bonus"]
        rank0_log = _apply_rank_bonus(character, bonus0)
        term.skills_gained.append(f"Rank 0 bonus: {bonus0}")
        character.log(f"  Rank 0 bonus: {rank0_log}")

    # Career-start skills: auto-applied on the very first term in this career.
    # Used by careers like Girug'kagh Translator (Steward 1 + Diplomat 1 at entry).
    career_start_skill_log: list[str] = []
    if first_term_in_this_career:
        career_start_skills = career.get("career_start_skills", [])
        if career_start_skills:
            career_start_skill_log = _apply_enrollment_auto_skills(character, career_start_skills)
            for msg in career_start_skill_log:
                character.log(f"  Career start skill: {msg}")
            term.skills_gained.extend([f"Career start: {s}" for s in career_start_skills])

    # Species-conditional career start skills (e.g. Halkan Citizen: Profession (Farming) 1).
    # Applied on first entry to a matching career regardless of assignment.
    sp_data_for_start = rules.species().get(character.species_id or "", {})
    sp_career_start_map = sp_data_for_start.get("species_career_start_skills", {})
    sp_career_start_log: list[str] = []
    if first_term_in_this_career and career_id in sp_career_start_map:
        sp_career_start_log = _apply_enrollment_auto_skills(
            character, sp_career_start_map[career_id]
        )
        for msg in sp_career_start_log:
            character.log(f"  Species career start skill: {msg}")
        term.skills_gained.extend(
            [f"Species career start: {s}" for s in sp_career_start_map[career_id]]
        )

    # Imperial Guard first term: auto-roll 1D on service_skills (extra training).
    # Guardsmen receive one free service skill roll in addition to normal term skills.
    ig_entry_skill_log: list[str] = []
    if career_id == "imperial_guard" and first_term_in_this_career:
        svc_table = career.get("skill_tables", {}).get("service_skills", {})
        _ig_roll = dice.roll("1D")
        _ig_entry = svc_table.get(str(_ig_roll.total), "")
        if _ig_entry:
            _ig_skill_name = _ig_entry.split(" or ")[0].strip()
            _ig_sname, _ig_spec = _split_skill_speciality(_ig_skill_name)
            character.add_skill(_ig_sname, level=1, speciality=_ig_spec)
            _ig_disp = f"{_ig_sname}{f' ({_ig_spec})' if _ig_spec else ''} 1"
            ig_entry_skill_log.append(_ig_disp)
            term.skills_gained.append(f"Imperial Guard entry training: {_ig_disp}")
            character.log(
                f"  Imperial Guard entry training: rolled {_ig_roll.total} on service skills → {_ig_disp}"
            )

    # Basic training: auto-apply all 6 skill entries at level 0.
    # basic_training_from_specialist: use the specialist table for this assignment
    # instead of the service_skills table (e.g. Zhodani Prole career).
    basic_training_skills: list[str] = []
    if first_term_in_this_career and not commissioned_start:
        if career.get("basic_training_from_specialist"):
            _asgn_table_key = f"{assignment_id}_skills"
            service_table = career.get("skill_tables", {}).get(_asgn_table_key, {})
            if not service_table:
                # Try without _skills suffix (Believer-style assignment tables)
                service_table = career.get("skill_tables", {}).get(assignment_id, {})
            if not service_table:
                # Fall back to service_skills if specialist table not found
                service_table = career.get("skill_tables", {}).get("service_skills", {})
        else:
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
            sname, spec = _split_skill_speciality(skill_name)
            character.add_skill(sname, level=0, speciality=spec)
            disp = f"{sname}{f' ({spec})' if spec else ''} 0"
            basic_training_skills.append(disp)
        if basic_training_skills:
            term.skills_gained.extend([f"Basic training: {s}" for s in basic_training_skills])
            character.log(f"  Basic training applied: {', '.join(basic_training_skills)}")

    result: dict = {"term": term.model_dump(), "character": character.model_dump()}
    if academy_commission_roll is not None:
        result["academy_commission_roll"] = academy_commission_roll
    if basic_training_skills:
        result["basic_training_skills"] = basic_training_skills
    if career_start_skill_log:
        result["career_start_skills"] = career_start_skill_log
    if ig_entry_skill_log:
        result["ig_entry_skills"] = ig_entry_skill_log
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

    # Hiver/no-survival careers: automatically survive every term
    career_data = rules.careers().get(term.career_id, {})
    if career_data.get("no_survival"):
        term.survived = True
        term.survival_roll_total = 99  # sentinel for "auto-passed"
        character.log(f"{career_data.get('name', term.career_id)}: no survival check (automatic).")
        return {
            "roll": None,
            "survived": True,
            "auto_survived": True,
            "mishap_no_eject": False,
            "anagathics_second_roll": None,
            "parallel_event": None,
            "character": character.model_dump(),
        }

    # Event-triggered ejection: skip the dice, career ends without mishap table
    if character.force_career_end:
        character.force_career_end = False
        term.survived = False
        term.survival_roll_total = 0
        character.log("Ejected from career by event — survival auto-failed, no mishap table roll.")
        career_for_flag = rules.careers().get(term.career_id, {})
        return {
            "roll": None,
            "survived": False,
            "ejected": True,
            "mishap_no_eject": False,
            "anagathics_second_roll": None,
            "parallel_event": None,
            "character": character.model_dump(),
        }

    char_key = survival["characteristic"]
    target = survival["target"]
    survival_dm_bonus = character.dm_next_survival
    character.dm_next_survival = 0

    # Storm Knight Heroism Rule: apply chosen negative DM to survival.
    _heroism_dm = character.storm_knight_heroism_dm
    _STORM_KNIGHT_IDS_SK = {"storm_knight_thunder", "storm_knight_inconstant_star", "storm_knight_shadows"}
    if _heroism_dm != 0 and term.career_id not in _STORM_KNIGHT_IDS_SK:
        _heroism_dm = 0  # only applies to Storm Knight careers
    if _heroism_dm != 0:
        character.log(f"Storm Knight Heroism: DM{_heroism_dm:+d} applied to survival roll.")

    dm = _char_dm(character, char_key) + cover_dm + survival_dm_bonus + _heroism_dm
    r = dice.roll("2D", modifier=dm, target=target)
    term.survived = bool(r.succeeded)
    term.survival_roll_total = r.total

    # Natural 2 is always a mishap regardless of DMs
    if r.raw_total == 2 and term.survived:
        term.survived = False
        character.log("Natural 2 on survival roll — automatic mishap regardless of DMs.")

    msg = (
        f"Survival ({char_key} {target}+){cover_note}: 2D{dm:+d} = {r.total} "
        f"[{'SURVIVED' if term.survived else 'MISHAP'}]"
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

    # ── Solomani Passing exposure: natural 2 in military or Party careers ──
    # A character carrying falsified genetic records is exposed on a natural 2.
    # Effect: passing status revoked, SOC halved (round down), career ends.
    _PASSING_EXPOSURE_CAREERS = frozenset({
        "confederation_army", "confederation_navy", "solomani_marine",
        "solsec", "party",
    })
    passing_exposed = False
    if (
        character.solomani_passing
        and r.raw_total == 2
        and term.career_id in _PASSING_EXPOSURE_CAREERS
    ):
        old_soc = character.characteristics.SOC
        new_soc = old_soc // 2
        character.characteristics.SOC = new_soc
        character.solomani_passing = False
        passing_exposed = True
        character.log(
            f"PASSING EXPOSED (natural 2 in {term.career_id})! "
            f"Falsified documents discovered — SOC {old_soc} → {new_soc} (halved, rounded down). "
            f"Career ends without Benefit rolls."
        )

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

    # Storm Knight Heroism Rule: after final survival result is known, resolve DM side-effect.
    if _heroism_dm != 0:
        if term.survived:
            _events_dm = abs(_heroism_dm)
            character.dm_next_events += _events_dm
            character.log(
                f"Storm Knight Heroism: survived with DM{_heroism_dm:+d} — "
                f"DM+{_events_dm} granted to next Events roll."
            )
        character.storm_knight_heroism_dm = 0  # always consume

    # Career-level flag: some careers (e.g. Bounty Hunter) never eject on mishap.
    career_for_flag = rules.careers().get(term.career_id, {})
    mishap_no_eject = bool(career_for_flag.get("mishap_no_eject", False))

    return {
        "roll": r.to_dict(),
        "survived": term.survived,    # reflects both checks
        "mishap_no_eject": mishap_no_eject,
        "anagathics_second_roll": anagathics_second_roll,
        "parallel_event": parallel_event,
        "passing_exposed": passing_exposed,
        "character": character.model_dump(),
    }


def event_roll(character: Character) -> dict:
    """Roll on the career's event table (2D, 2-12)."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")
    career = rules.careers()[term.career_id]
    events = career.get("events", {})
    # Storm Knight Heroism Rule: consume any pending events DM.
    _events_dm_bonus = character.dm_next_events
    character.dm_next_events = 0
    if _events_dm_bonus:
        character.log(f"Storm Knight Heroism: DM+{_events_dm_bonus} applied to Events roll.")

    r = dice.roll("2D", modifier=_events_dm_bonus)
    key = str(min(12, r.total))  # cap at 12 for table lookup
    event_text = events.get(key, "(No event encoded for this roll — see rulebook or the career JSON file.)")

    # Parse unconditional DM/stat/promotion grants from the ORIGINAL event text
    # (before any life-event expansion) so we don't double-apply grants that
    # apply_life_event() handles programmatically.
    dm_grants = _apply_event_dms(character, event_text)
    for g in dm_grants:
        if g.get("applied"):
            character.log(f"  → Auto-applied DM{g['dm']:+d} to next {g['target'].capitalize()} roll.")

    stat_bonuses = _apply_event_stat_bonuses(character, event_text)

    auto_promotion = _apply_event_auto_promotion(character, event_text)
    if auto_promotion and not auto_promotion.get("skipped"):
        character.log(
            f"  → Auto-promoted to rank {auto_promotion['to_rank']}"
            f" ({auto_promotion.get('rank_title') or '—'})."
        )

    # Life Event sub-table handling — call apply_life_event() so effects are
    # actually applied (contacts, stat changes, DMs, pending choices).
    # This replaces the old code that only expanded the display text.
    life_event_result: dict | None = None
    if event_text.lower().startswith("life event"):
        life_event_result = apply_life_event(character)
        event_text = f"Life Event — {life_event_result['event_text']}"

    term.events.append(event_text)
    _evt_log = f"Event [2D={r.raw_total}" + (f"+{_events_dm_bonus}={r.total}" if _events_dm_bonus else "") + f"]: {event_text}"
    character.log(_evt_log)

    # Apply structured event effects from _EVENT_EFFECTS (skill grants, choices, etc.)
    event_effects_applied, disaster_mishap = _apply_event_effects(
        character, term.career_id, r.total, term
    )
    for msg in event_effects_applied:
        character.log(f"  → Event effect: {msg}")

    # Prepend life event auto-applied messages so they appear first in the UI
    if life_event_result:
        life_auto = life_event_result.get("auto_applied", [])
        if life_auto:
            event_effects_applied = life_auto + event_effects_applied

    # When the event created a pending interactive choice (e.g. a skill_check
    # whose on_pass/on_fail already encode the conditional rewards), drop any
    # *unapplied* (conditional) text-parsed DM grants. Otherwise the UI could
    # surface a stray, independently-claimable "DM+N to <roll>" button that lets
    # the player collect the reward without — or even after FAILING — the gating
    # roll. See bounty_hunter event 9: "...DM+1 to one Benefit roll. If you
    # fail, roll on the Mishaps table..." where the DM+1 is owned by the
    # skill_check's on_pass and must never be granted on a failed/un-rolled check.
    if character.pending_career_event_choice is not None:
        dm_grants = [g for g in dm_grants if g.get("applied")]

    return {
        "roll": r.to_dict(),
        "event": event_text,
        "dm_grants": dm_grants,
        "stat_bonuses": stat_bonuses,
        "auto_promotion": auto_promotion,
        "event_effects": event_effects_applied,
        "disaster_mishap": disaster_mishap,
        "pending_event_choice": character.pending_career_event_choice,
        "character": character.model_dump(),
    }


def _apply_zhodani_re_education(character: "Character", msgs: list[str]) -> None:
    """Roll 1D on the Zhodani Re-education Events sub-table and log the result."""
    re_r = dice.roll("1D")
    re_table = rules.zhodani_life_events().get("re_education_events", {})
    re_results = re_table.get("results", {})
    re_text = re_results.get(str(re_r.total), "Re-education: consult Re-education Events table.")
    character.log(f"Re-education Events [1D={re_r.total}]: {re_text}")
    msgs.append(f"Re-education Events 1D={re_r.total}: {re_text}")


_STORM_KNIGHT_IDS_HONOURS = frozenset({
    "storm_knight_thunder", "storm_knight_inconstant_star", "storm_knight_shadows"
})


def _grant_knight_commander_by_rank(character: "Character") -> list[str]:
    """Grant Knight Commander By Rank (advancement to/past rank 6). Returns log messages."""
    msgs: list[str] = []
    character.knight_commander_by_rank = True
    current_soc = character.characteristics.get("SOC")
    if character.knight_commander_by_deed:
        new_soc = max(current_soc, 11)
        msgs.append("Knight Commander By Rank — already By Deed: SOC raised to minimum 11")
    else:
        new_soc = max(current_soc + 1, 10)
        msgs.append(f"Knight Commander By Rank — SOC {current_soc}→{new_soc} (min 10)")
    character.characteristics.set("SOC", new_soc)
    has_sword = any(e.name == "Sword of Honour" for e in character.equipment)
    character.equipment.append(
        Equipment(name="Medallion of the Order", notes="Knight Commander By Rank — heraldic symbols inscribed")
    )
    character.equipment.append(
        Equipment(name="White Sash of Honour", notes="Knight Commander By Rank")
    )
    if not has_sword:
        character.equipment.append(Equipment(name="Sword of Honour", notes="Knight Commander"))
    msgs.append("Awarded: Medallion of the Order, White Sash of Honour" + ("" if has_sword else ", Sword of Honour"))
    character.log(f"Knight Commander By Rank granted. SOC {current_soc}→{new_soc}.")
    return msgs


def _grant_knight_grand_cross(character: "Character") -> list[str]:
    """Grant Knight Grand Cross Commander (advancement when already Knight Commander By Rank)."""
    msgs: list[str] = []
    character.knight_grand_cross = True
    current_soc = character.characteristics.get("SOC")
    new_soc = max(current_soc, 12)
    character.characteristics.set("SOC", new_soc)
    character.equipment.append(
        Equipment(name="Grand Cross Medallion", notes="Knight Grand Cross Commander — ornate heraldic medallion")
    )
    character.equipment.append(
        Equipment(name="Grand Cross Sash", notes="Knight Grand Cross Commander — ornate sash")
    )
    msgs.append(f"Knight Grand Cross Commander — SOC {current_soc}→{new_soc} (min 12)")
    msgs.append("Awarded: Grand Cross Medallion, Grand Cross Sash")
    character.log(f"Knight Grand Cross Commander granted. SOC {current_soc}→{new_soc}.")
    return msgs


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

    elif etype == "enemy_if_none":
        # Add enemy only if the character has no existing enemies (e.g. Drifter event 8).
        desc = effect.get("desc", "Enemy")
        has_enemy = any(a.kind == "enemy" for a in character.associates)
        if not has_enemy:
            character.associates.append(Associate(kind="enemy", description=desc))
            msgs.append(f"Gained Enemy: {desc}")
            character.log(f"Event: enemy_if_none — {desc} (no prior enemies, added)")
        else:
            msgs.append(f"Enemy not added (already has an enemy; {desc})")
            character.log(f"Event: enemy_if_none — skipped, character already has an enemy")

    elif etype == "stat":
        stat = effect["stat"]
        amount = effect["amount"]
        if stat == "REP":
            old = character.reputation
            character.reputation = max(0, old + amount)
            msgs.append(f"REP {old}→{character.reputation} ({amount:+d})")
            character.log(f"Mishap/event: REP {amount:+d}")
        elif stat == "TER":
            old = character.extra_characteristics.get("TER", 0)
            new_val = max(0, old + amount)
            character.extra_characteristics["TER"] = new_val
            msgs.append(f"TER {old}→{new_val} ({amount:+d})")
            character.log(f"Mishap/event: TER {amount:+d}")
        elif stat == "FOL":
            old = character.extra_characteristics.get("FOL", 0)
            new_val = max(0, old + amount)
            character.extra_characteristics["FOL"] = new_val
            msgs.append(f"FOL {old}→{new_val} ({amount:+d})")
            character.log(f"Mishap/event: FOL {amount:+d}")
        elif stat == "PSI":
            old = character.psi
            character.psi = max(0, old + amount)
            msgs.append(f"PSI {old}→{character.psi} ({amount:+d})")
            character.log(f"Mishap/event: PSI {amount:+d}")
        elif stat == "RES":
            old = character.characteristics.SOC
            character.characteristics.SOC = max(0, old + amount)
            msgs.append(f"RES {old}→{character.characteristics.SOC} ({amount:+d})")
            character.log(f"Mishap/event: RES {amount:+d}")
        else:
            old = character.characteristics.get(stat)
            new_val = max(0, old + amount)
            character.characteristics.set(stat, new_val)
            msgs.append(f"{stat} {old}→{new_val} ({amount:+d})")
            character.log(f"Mishap: {stat} {old}→{new_val}")

    elif etype == "stat_cap":
        # Set stat to min(current, cap) — used for "SOC drops to 2" / "TER drops to 0" etc.
        stat = effect["stat"]
        cap = effect["cap"]
        if stat == "PSI":
            old = character.psi
            new_val = min(old, cap)
            if new_val != old:
                character.psi = new_val
                msgs.append(f"PSI {old}→{new_val} (capped at {cap})")
                character.log(f"Mishap: PSI capped at {cap}: {old}→{new_val}")
            else:
                msgs.append(f"PSI already ≤ {cap} (stays at {old})")
        else:
            old = _get_stat(character, stat)
            new_val = min(old, cap)
            if new_val != old:
                # Save SOC before first outcast-level reduction for redemption restore
                if stat == "SOC" and cap <= 2 and character.pre_outcast_soc == 0:
                    character.pre_outcast_soc = old
                _set_stat(character, stat, new_val)
                msgs.append(f"{stat} {old}→{new_val} (capped at {cap})")
                character.log(f"Mishap: {stat} capped at {cap}: {old}→{new_val}")
            else:
                msgs.append(f"{stat} already ≤ {cap} (stays at {old})")

    elif etype == "force_career_end":
        character.force_career_end = True
        character.ejected_by_event = True
        msgs.append("Career ended — ejected from this career")

    elif etype == "dm_next_advancement":
        amount = int(effect.get("amount", 0))
        character.dm_next_advancement += amount
        msgs.append(f"DM{amount:+d} to next Advancement roll")
        character.log(f"Mishap/event: dm_next_advancement {amount:+d}")

    elif etype == "good_fortune_benefit_dm":
        amount = int(effect.get("amount", 1))
        character.good_fortune_benefit_dm += amount
        msgs.append(f"DM{amount:+d} token for one Benefit roll")
        character.log(f"Mishap/event: good_fortune_benefit_dm +{amount}")

    elif etype == "d6_subtable":
        # Auto-roll 1D and apply matching range effects inline (usable in mishap path too).
        sub_r = dice.roll("1D")
        sub = sub_r.total
        msgs.append(f"1D sub-roll = {sub}")
        character.log(f"Mishap d6_subtable: 1D={sub}")
        for rng in effect.get("ranges", []):
            if rng.get("min", 1) <= sub <= rng.get("max", 6):
                for sub_eff in rng.get("effects", []):
                    if sub_eff.get("type") == "injury":
                        inj = apply_injury(character)
                        if inj:
                            msgs.append(f"Injury: {inj.get('description', 'injured')}")
                    else:
                        s_msgs, s_pend = _apply_mishap_effect(character, sub_eff, term)
                        msgs.extend(s_msgs)
                        if s_pend:
                            set_pending = True
                break

    elif etype == "dm_qualification_terms_in_career":
        # Officer-caste consideration: DM to next Qualification = terms served in current career
        if term is not None:
            terms_count = sum(1 for t in character.term_history if t.career_id == term.career_id) + 1
            character.dm_next_qualification += terms_count
            msgs.append(f"Officer consideration: DM+{terms_count} to next Qualification roll ({terms_count} term(s) in career)")
            character.log(f"Officer consideration: dm_next_qualification +{terms_count}")
        else:
            msgs.append("Officer consideration: could not count terms (no active term)")

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
        msg = character.add_skill(name, level=level, fixed_level=True)
        msgs.append(msg)

    elif etype == "skill_choice":
        if not character.pending_career_mishap_choice:
            character.pending_career_mishap_choice = {
                "type": "skill_choice",
                "options": effect["options"],
                "prompt": f"Choose one skill to gain at level 1: {', '.join(effect['options'])}",
            }
            set_pending = True

    elif etype == "skill_loss_choice":
        if not character.pending_career_mishap_choice:
            _slc = {
                "type": "skill_loss_choice",
                "prompt": effect.get("prompt", "Lose one level in a skill you possess (choose which):"),
            }
            if effect.get("filter"):
                _slc["filter"] = effect["filter"]   # e.g. "Science" restricts picker to Science skills
            character.pending_career_mishap_choice = _slc
            set_pending = True

    elif etype == "forfeit_benefit":
        if term is not None:
            term.benefit_forfeited = True
        msgs.append("This term's benefit roll forfeited")
        character.log("Mishap: benefit roll forfeited")

    elif etype == "forfeit_all_benefits":
        # Lose ALL pending benefit rolls (Truther/Believer mishap 5)
        lost = character.pending_benefit_rolls
        character.pending_benefit_rolls = 0
        msgs.append(f"Lost all {lost} pending benefit roll(s) for this career")
        character.log(f"Mishap: forfeit_all_benefits — lost {lost} pending rolls")

    elif etype == "permanent_advancement_dm":
        amount = int(effect.get("amount", 0))
        character.permanent_advancement_dm += amount
        msgs.append(f"Permanent advancement DM {amount:+d} (cumulative: {character.permanent_advancement_dm:+d})")
        character.log(f"Event: permanent_advancement_dm {amount:+d}")

    elif etype == "permanent_benefit_dm":
        amount = int(effect.get("amount", 0))
        character.permanent_benefit_dm += amount
        msgs.append(f"Permanent benefit DM {amount:+d} (cumulative: {character.permanent_benefit_dm:+d})")
        character.log(f"Event: permanent_benefit_dm {amount:+d}")

    elif etype == "extra_benefit":
        n = effect.get("amount", 1)
        character.pending_benefit_rolls += n
        msgs.append(f"Extra benefit roll{'s' if n > 1 else ''} gained (+{n})")
        character.log(f"Event: +{n} benefit roll(s) added")

    elif etype == "dm_advancement":
        amount = effect.get("amount", 0)
        character.dm_next_advancement += amount
        msgs.append(f"DM{amount:+d} to next Advancement roll")
        character.log(f"Event: dm_next_advancement {amount:+d}")

    elif etype == "dm_permanent_advancement":
        amount = effect.get("amount", 0)
        character.dm_permanent_advancement += amount
        msgs.append(f"Permanent DM{amount:+d} to ALL future Advancement rolls (never consumed)")
        character.log(f"Event: dm_permanent_advancement {amount:+d}")

    elif etype == "auto_advance":
        character.dm_next_advancement += 12
        msgs.append("Automatically promoted this term (DM+12 to Advancement roll)")
        character.log("Event: auto_advance — dm_next_advancement +12")

    elif etype == "equipment":
        item_name = effect.get("name", "")
        item_notes = effect.get("notes", "")
        if item_name:
            character.equipment.append(Equipment(name=item_name, notes=item_notes))
            msgs.append(f"Equipment gained: {item_name}")
            character.log(f"Event: equipment added — {item_name}")

    elif etype == "d_stat":
        # Roll a variable die and apply to a stat (always reduces for mishaps unless negative=False).
        stat = effect["stat"]
        dice_expr = effect.get("dice", "D3")
        negative = effect.get("negative", True)
        r_d = dice.roll(dice_expr)
        amount = -r_d.total if negative else r_d.total
        if stat == "REP":
            old = character.reputation
            character.reputation = max(0, old + amount)
            msgs.append(f"REP {old}→{character.reputation} ({amount:+d}, rolled {r_d.total})")
            character.log(f"Mishap d_stat REP {amount:+d} ({dice_expr}={r_d.total})")
        elif stat == "TER":
            old = character.extra_characteristics.get("TER", 0)
            new_val = max(0, old + amount)
            character.extra_characteristics["TER"] = new_val
            msgs.append(f"TER {old}→{new_val} ({amount:+d}, rolled {r_d.total})")
            character.log(f"Mishap d_stat TER {amount:+d} ({dice_expr}={r_d.total})")
        elif stat == "FOL":
            old = character.extra_characteristics.get("FOL", 0)
            new_val = max(0, old + amount)
            character.extra_characteristics["FOL"] = new_val
            msgs.append(f"FOL {old}→{new_val} ({amount:+d}, rolled {r_d.total})")
            character.log(f"Mishap d_stat FOL {amount:+d} ({dice_expr}={r_d.total})")
        else:
            old = character.characteristics.get(stat)
            if old is not None:
                new_val = max(0, old + amount)
                character.characteristics.set(stat, new_val)
                msgs.append(f"{stat} {old}→{new_val} ({amount:+d}, rolled {r_d.total})")
                character.log(f"Mishap d_stat {stat} {amount:+d} ({dice_expr}={r_d.total})")

    elif etype == "kkree_wife_loss":
        # Remove the most recently acquired wife from associates.
        wife_indices = [i for i, a in enumerate(character.associates) if a.kind == "wife"]
        if wife_indices:
            removed = character.associates.pop(wife_indices[-1])
            msgs.append(f"Lost a wife ({removed.description or 'Wife'})")
            character.log(f"Mishap: wife lost — {removed.description or 'Wife'}")
        else:
            msgs.append("Lost a wife (none recorded in associates)")
            character.log("Mishap: kkree_wife_loss — no wife associate found")

    elif etype == "kkree_degree_reset":
        # Revert SOC rank degree to servant-to-rankholder (caste demotion from mishap).
        old_deg = character.kkree_soc_rank_degree
        character.kkree_soc_rank_degree = "servant_of_rankholder"
        msgs.append(f"SOC rank degree reverted to Servant-of-Rankholder (was {old_deg})")
        character.log(f"Mishap: kkree_soc_rank_degree reset to servant_of_rankholder (was {old_deg})")

    elif etype == "debt":
        amount = effect["amount"]
        character.medical_debt += amount
        msgs.append(f"Debt: Cr{amount:,} added")
        character.log(f"Mishap: Cr{amount:,} debt added")

    elif etype == "d_cash":
        # "d_cash": {"dice": "1D", "multiplier": 1000} — roll dice × multiplier credits
        _dice_str = effect.get("dice", "1D")
        _multiplier = effect.get("multiplier", 1)
        _roll = dice.roll(_dice_str).total
        _amount = _roll * _multiplier
        character.credits += _amount
        msgs.append(f"Cash payout: Cr{_amount:,} ({_dice_str}={_roll} × Cr{_multiplier:,})")
        character.log(f"Mishap d_cash: {_dice_str}={_roll} × {_multiplier:,} = Cr{_amount:,} added")

    elif etype == "force_next_career":
        character.forced_next_career_id = effect["career_id"]
        msgs.append(f"Forced next career: {effect['career_id']}")
        character.log(f"Mishap: forced into {effect['career_id']} next")

    elif etype == "d_associates":
        kind = effect["kind"]
        dice_str = effect["dice"]
        desc_prefix = effect.get("desc_prefix", "")
        count = dice.roll(dice_str).total
        for i in range(count):
            desc = desc_prefix or ""
            character.associates.append(
                Associate(kind=kind, description=desc)
            )
        msgs.append(f"Gained {count}× {kind.capitalize()}")
        character.log(f"Mishap: gained {count} {kind}(s)")

    elif etype == "d6_result":
        r6 = dice.roll("1D")
        result = r6.total
        msgs.append(f"1D = {result}")
        for rng in effect.get("ranges", []):
            if rng.get("min", 1) <= result <= rng.get("max", 6):
                for sub_eff in rng.get("effects", []):
                    sub_msgs, sub_pend = _apply_mishap_effect(character, sub_eff, term)
                    msgs.extend(sub_msgs)
                    if sub_pend:
                        set_pending = True
                break

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
            # Populate ge_lose_associate_or_forfeit from contacts/allies (or auto-forfeit)
            elif choice_id == "ge_lose_associate_or_forfeit":
                opts = []
                for i, assoc in enumerate(character.associates):
                    if assoc.kind in ("contact", "ally"):
                        opts.append({
                            "id": f"associate_{i}",
                            "label": f"Lose {assoc.kind.capitalize()}: {assoc.description or '(unnamed)'}",
                        })
                if not opts:
                    opts = [{"id": "forfeit",
                             "label": "No Allies or Contacts to lose — forfeit this term's Benefit roll"}]
                pending["options"] = opts
            # Populate zhodani_lose_associate from contacts/allies (or skip if none)
            elif choice_id == "zhodani_lose_associate":
                opts = []
                for i, assoc in enumerate(character.associates):
                    if assoc.kind in ("contact", "ally"):
                        opts.append({
                            "id": str(i),
                            "label": f"Lose {assoc.kind.capitalize()}: {assoc.description or '(unnamed)'}",
                        })
                if not opts:
                    opts = [{"id": "skip", "label": "No Allies or Contacts to lose"}]
                pending["options"] = opts
            # Populate vargr_corsair_betrayal — pick a contact/ally to become Enemy, or auto-enemy if none
            elif choice_id == "vargr_corsair_betrayal":
                opts = []
                for i, assoc in enumerate(character.associates):
                    if assoc.kind in ("contact", "ally"):
                        opts.append({
                            "id": str(i),
                            "label": f"{assoc.kind.capitalize()} → Enemy: {assoc.description or '(unnamed)'}",
                            "associate_index": i,
                        })
                if not opts:
                    opts = [{"id": "auto_enemy",
                             "label": "No Allies or Contacts in band — gain Enemy [Corsair Betrayer]"}]
                pending["options"] = opts
            # psion_mishap6: pick Ally or Contact → Enemy (with skip if none)
            elif choice_id == "psion_mishap6":
                opts = []
                for i, assoc in enumerate(character.associates):
                    if assoc.kind in ("contact", "ally"):
                        opts.append({
                            "id": str(i),
                            "label": f"{assoc.kind.capitalize()} → Enemy: {assoc.description or '(unnamed)'}",
                        })
                if not opts:
                    opts = [{"id": "skip", "label": "No Allies or Contacts — gain a generic Enemy [Former Friend]"}]
                pending["options"] = opts
            # psion_event3: pick Contact or Ally → Rival (with skip if none)
            elif choice_id == "psion_event3":
                opts = []
                for i, assoc in enumerate(character.associates):
                    if assoc.kind in ("contact", "ally"):
                        opts.append({
                            "id": str(i),
                            "label": f"{assoc.kind.capitalize()} → Rival: {assoc.description or '(unnamed)'}",
                        })
                if not opts:
                    opts = [{"id": "skip", "label": "No Contacts or Allies — no mechanical effect"}]
                pending["options"] = opts
            character.pending_career_mishap_choice = pending
            set_pending = True

    elif etype == "skill_check":
        if not character.pending_career_mishap_choice:
            _default_prompt = (
                f"Roll {'/' .join(s['name'] for s in effect['skills'])} {effect['target']}+"
            )
            character.pending_career_mishap_choice = {
                "type": "skill_check",
                "skills": effect["skills"],
                "target": effect["target"],
                "on_nat2": effect.get("on_nat2", []),
                "on_fail": effect.get("on_fail", []),
                "on_pass": effect.get("on_pass", []),
                "prompt": effect.get("prompt") or _default_prompt,
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

    elif etype == "career_continues":
        # Skill check passed → override the mishap; character stays in career
        if term is not None:
            term.survived = True
            term.mishap = None
        msgs.append("Career continues — not ejected from this career")
        character.log("Mishap skill check passed — character stays in career")

    elif etype == "knight_commander_deed":
        # Storm Knight honour: Knight Commander By Deed.
        # SOC = max(current + 1, 10); if also By Rank already, ensure SOC ≥ 11.
        # Equipment: medallion + scarlet sash + Sword of Honour (once only).
        already_had = character.knight_commander_by_deed
        character.knight_commander_by_deed = True
        current_soc = character.characteristics.get("SOC")
        if already_had:
            # Honour already held — just apply the standard SOC formula (SOC+1 floor 10)
            new_soc = max(current_soc + 1, 10)
        elif character.knight_commander_by_rank:
            new_soc = max(current_soc, 11)
        else:
            new_soc = max(current_soc + 1, 10)
        character.characteristics.set("SOC", new_soc)
        msgs.append(f"Knight Commander By Deed — SOC {current_soc}→{new_soc}")
        if not already_had:
            character.equipment.append(
                Equipment(name="Medallion of the Order", notes="Knight Commander By Deed — heraldic symbols inscribed")
            )
            character.equipment.append(
                Equipment(name="Scarlet Sash of Honour", notes="Knight Commander By Deed")
            )
            has_sword = any(e.name == "Sword of Honour" for e in character.equipment)
            if not has_sword:
                character.equipment.append(Equipment(name="Sword of Honour", notes="Knight Commander"))
            msgs.append("Awarded: Medallion of the Order, Scarlet Sash of Honour"
                         + ("" if has_sword else ", Sword of Honour"))
        character.log(f"Knight Commander By Deed granted. SOC {current_soc}→{new_soc}.")

    elif etype == "dm_benefit":
        amount = effect.get("amount", 0)
        character.dm_next_benefit += amount
        msgs.append(f"DM{amount:+d} to next Benefit roll")
        character.log(f"Event: dm_next_benefit {amount:+d}")

    elif etype == "dm_qualification":
        amount = effect.get("amount", 0)
        character.dm_next_qualification += amount
        msgs.append(f"DM{amount:+d} to next Qualification roll")
        character.log(f"Event: dm_next_qualification {amount:+d}")

    elif etype == "dm_survival":
        amount = effect.get("amount", 0)
        character.dm_next_survival += amount
        msgs.append(f"DM{amount:+d} to next Survival roll")
        character.log(f"Event: dm_next_survival {amount:+d}")

    elif etype == "psi_adjust":
        amount = effect.get("amount", 0)
        old_psi = character.psi
        character.psi = max(0, old_psi + amount)
        msgs.append(f"PSI {old_psi}→{character.psi} ({amount:+d})")
        character.log(f"Event: PSI {amount:+d}")

    elif etype == "d_extra_benefit":
        dice_str = effect.get("dice", "1D")
        if dice_str == "D3":
            count = (dice.roll("1D").total + 1) // 2
        else:
            count = dice.roll(dice_str).total
        character.pending_benefit_rolls += count
        msgs.append(f"Gained {count} extra Benefit roll(s)")
        character.log(f"Event: +{count} extra benefit rolls (rolled {dice_str})")

    elif etype == "zhodani_re_education":
        _apply_zhodani_re_education(character, msgs)

    elif etype == "zhodani_soc_conditional":
        # If SOC 10+, apply if_soc_gte_10 effects; otherwise roll Re-education Events.
        soc = character.characteristics.get("SOC")
        if soc >= 10:
            for sub_eff in effect.get("if_soc_gte_10", []):
                sub_msgs, sub_pending = _apply_mishap_effect(character, sub_eff, term)
                msgs.extend(sub_msgs)
                if sub_pending and not set_pending:
                    set_pending = True
        else:
            _apply_zhodani_re_education(character, msgs)

    elif etype == "forfeit_all_benefits_except_one":
        # Forfeit all accumulated benefit rolls, keeping exactly one.
        character.pending_benefit_rolls = 1
        if term is not None:
            term.benefit_forfeited = True
        msgs.append("Disgraced — all Benefit rolls forfeited except one (keeping 1)")
        character.log("Mishap: forfeit all benefits except one, keeping 1")

    elif etype == "rank_adjustment":
        # Adjust current term rank by ±N (used by Droyne event/mishap effects).
        amount = effect.get("amount", 0)
        if term is not None:
            old_rank = term.rank
            term.rank = max(0, min(term.rank + amount, 6))
            msgs.append(f"Rank {old_rank}→{term.rank} ({amount:+d})")
            character.log(f"Rank adjusted {amount:+d}: {old_rank}→{term.rank}")
        else:
            msgs.append(f"Rank adjustment {amount:+d} (no active term)")

    elif etype == "auto_qualify_careers":
        # Grant auto-qualification for one or more specific career IDs next term.
        # e.g. Party event 3: auto-qualify Citizen or Merchant + DM+2 advancement.
        career_ids = effect.get("career_ids", [])
        character.auto_qualify_career_ids = list(
            set(character.auto_qualify_career_ids) | set(career_ids)
        )
        label = " or ".join(career_ids)
        msgs.append(f"Auto-qualify for {label} next term (no roll needed) + DM+2 advancement")
        character.log(f"Event: auto-qualify [{', '.join(career_ids)}] granted for next term")

    elif etype == "trigger_disaster_mishap":
        # Used in skill_check on_fail: roll on mishap table.
        # career_continues=True (default) keeps the character in the career.
        # career_continues=False ends the career (sets force_career_end-equivalent via ejected_by_event after mishap).
        career_continues = effect.get("career_continues", True)
        try:
            mishap_roll(character)
            if career_continues and term is not None:
                term.survived = True
                term.mishap = None
                msgs.append("Rolled on Mishap table — career continues")
                character.log("Event skill-check fail: triggered mishap roll, career continues")
            else:
                # Career ends: mishap table already rolled above.
                # force_career_end → survival auto-fails.
                # ejected_by_event → mishap_roll skips the table (already rolled).
                character.force_career_end = True
                character.ejected_by_event = True
                msgs.append("Rolled on Mishap table — career ended")
                character.log("Event skill-check fail: triggered mishap roll, career ended")
        except Exception as _exc:
            msgs.append(f"Mishap roll (event on_fail) error: {_exc}")

    return msgs, set_pending


def mishap_roll(character: Character) -> dict:
    """Roll on the career's mishap table (1D) after a failed survival.

    Processes _MISHAP_EFFECTS for the career and auto-applies or sets pending
    choices for each effect. Returns structured result with all resolved data.
    """
    term = character.current_term
    if term is None:
        raise ValueError("No active term")

    # Event-triggered ejection: skip the mishap table entirely
    if character.ejected_by_event:
        character.ejected_by_event = False
        term.mishap = "Ejected from career by event"
        character.log("Mishap skipped — career ended by event ejection.")
        return {
            "roll": None,
            "mishap_number": 0,
            "mishap": term.mishap,
            "auto_applied": ["Career ended — ejected from career by event."],
            "pending_choice": None,
            "injury_pending": False,
            "injury_data": None,
            "frozen_watch": False,
            "character": character.model_dump(),
        }

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

    # Clear any stale pending choice from a previous term before applying this mishap's
    # effects — otherwise the "if not character.pending_career_mishap_choice" guards in
    # _apply_mishap_effect would silently block the new pending from being set.
    character.pending_career_mishap_choice = None

    effects = _MISHAP_EFFECTS.get(career_id, {}).get(mishap_num, [])

    for effect in effects:
        etype = effect["type"]

        if etype == "injury":
            if injury_data is None:
                injury_data = apply_injury(character)
            continue

        if etype == "injury_twice_higher":
            r1 = dice.roll("1D").total
            r2 = dice.roll("1D").total
            result = max(r1, r2)
            auto_applied.append(f"Injury ×2 (higher): rolled {r1} and {r2} → using result {result}")
            character.log(f"Mishap injury_twice_higher: {r1},{r2} → {result}")
            if injury_data is None:
                injury_data = _apply_injury_for_result(character, result)
            continue

        if etype in ("injury_severity_choice", "stat_choice", "skill_choice",
                     "pending_choice", "skill_check", "skill_loss_choice") and pending_set:
            # Only one pending at a time — skip further pending effects
            continue

        msgs, was_pending = _apply_mishap_effect(character, effect, term)
        auto_applied.extend(msgs)
        if was_pending:
            pending_set = True
            pending_choice = character.pending_career_mishap_choice

    # ── Droyne continuation check ──────────────────────────────────────────
    # All Droyne mishaps require a continuation check: 2D + Caste skill level
    # − caste_number ≥ 2 (Simple difficulty).  If failed, ejected from Oytrip.
    continuation_no_eject: Optional[bool] = None
    if career.get("mishap_no_eject") and career.get("droyne_caste"):
        caste_number = character.droyne_caste_number or 0
        # Find the Caste skill level (generic "Caste" or "Caste (caste_name)")
        caste_skill_level = 0
        caste_name = (character.droyne_caste or "").lower()
        for sk in character.skills:
            sname = sk.name.lower()
            spec = (sk.speciality or "").lower()
            if sname == "caste" and (not spec or spec == caste_name):
                caste_skill_level = max(caste_skill_level, sk.level)
        # Also check for any Black Skills DM
        black_skill_names = {"carouse", "deception", "gambler", "persuade", "streetwise"}
        highest_black = 0
        for sk in character.skills:
            if sk.name.lower() in black_skill_names:
                highest_black = max(highest_black, sk.level)
        cont_dm = caste_skill_level - caste_number - highest_black
        cont_roll = dice.roll("2D")
        cont_total = cont_roll.total + cont_dm
        # Simple (2+) difficulty
        continuation_passed = cont_total >= 2
        continuation_no_eject = continuation_passed
        if continuation_passed:
            # Override: career continues despite mishap
            term.survived = True
            term.mishap = mishap_text  # keep the mishap text but career continues
            character.log(
                f"Droyne continuation check [2D{cont_dm:+d}={cont_total}]: PASSED — "
                f"career continues (Caste skill {caste_skill_level}, caste# {caste_number}, "
                f"Black DM {-highest_black if highest_black else 0})."
            )
            auto_applied.append(
                f"Continuation check: 2D{cont_dm:+d} = {cont_total} (needed 2+) — PASSED, career continues."
            )
        else:
            # Ejected from Oytrip
            term.survived = False
            character.log(
                f"Droyne continuation check [2D{cont_dm:+d}={cont_total}]: FAILED — "
                f"ejected from Oytrip."
            )
            auto_applied.append(
                f"Continuation check: 2D{cont_dm:+d} = {cont_total} (needed 2+) — FAILED, ejected from Oytrip."
            )

    return {
        "roll": r.to_dict(),
        "mishap_number": mishap_num,
        "mishap": mishap_text,
        "auto_applied": auto_applied,
        "pending_choice": pending_choice,
        "injury_pending": bool(character.pending_injury_choice),
        "injury_data": injury_data,
        "frozen_watch": bool(term and term.frozen_watch),
        "continuation_no_eject": continuation_no_eject,
        "character": character.model_dump(),
    }


def _apply_event_effects(character: "Character", career_id: str, event_num: int,
                          term) -> tuple[list[str], dict | None]:
    """Apply structured effects from _EVENT_EFFECTS for the given career/event.

    Returns (auto_applied_msgs, disaster_mishap_result).
    disaster_mishap_result is non-None if a trigger_disaster_mishap effect fired.
    """
    effects = _EVENT_EFFECTS.get(career_id, {}).get(event_num, [])
    if not effects:
        return [], None

    auto_applied: list[str] = []
    disaster_result = None
    pending_set = False

    for effect in effects:
        etype = effect.get("type", "")

        if etype == "trigger_disaster_mishap":
            # Roll on the career's own mishap table; career is NOT ended.
            try:
                disaster_result = mishap_roll(character)
                # For Droyne, the continuation check in mishap_roll already set
                # term.survived — don't override it if the check failed.
                cont = disaster_result.get("continuation_no_eject") if disaster_result else None
                if term is not None and cont is not False:
                    # Non-Droyne or Droyne who passed the continuation check: career continues.
                    term.survived = True
                    term.mishap = None
                # Surface any auto-applied messages from the mishap (e.g. stat reductions).
                for msg in (disaster_result.get("auto_applied") or []):
                    auto_applied.append(msg)
                auto_applied.append("Disaster! Rolled on mishap table — career continues")
                # Redirect any pending mishap choice (e.g. stat_choice) to the event
                # choice slot so the player sees the picker on the event screen.
                if character.pending_career_mishap_choice is not None and not pending_set:
                    character.pending_career_event_choice = character.pending_career_mishap_choice
                    character.pending_career_mishap_choice = None
                    pending_set = True
            except Exception as ex:
                auto_applied.append(f"Disaster mishap error: {ex}")
            continue

        if etype == "d6_result":
            # Auto-roll 1D and apply effects from the matching range.
            r6 = dice.roll("1D")
            result = r6.total
            auto_applied.append(f"1D = {result}")
            for rng in effect.get("ranges", []):
                if rng.get("min", 1) <= result <= rng.get("max", 6):
                    for sub_eff in rng.get("effects", []):
                        if sub_eff.get("type") == "injury":
                            inj = apply_injury(character)
                            if inj:
                                auto_applied.append(f"Injury: {inj.get('description', 'injured')}")
                        else:
                            s_msgs, s_pend = _apply_mishap_effect(character, sub_eff, term)
                            auto_applied.extend(s_msgs)
                            if s_pend and not pending_set:
                                if character.pending_career_mishap_choice is not None:
                                    character.pending_career_event_choice = character.pending_career_mishap_choice
                                    character.pending_career_mishap_choice = None
                                pending_set = True
                    break
            continue

        if etype == "contacts_soc_dm_min1":
            # Gain Contacts equal to max(1, SOC DM).
            soc_val = character.characteristics.get("SOC")
            soc_dm = (soc_val // 3) - 2  # standard MgT 2e DM formula
            count = max(1, soc_dm)
            desc = effect.get("desc", "Contact")
            for _ in range(count):
                character.associates.append(Associate(kind="contact", description=desc))
            auto_applied.append(f"Gained {count}× {desc}")
            character.log(f"Event contacts_soc_dm_min1: +{count} contacts")
            continue

        if etype == "injury":
            inj = apply_injury(character)
            if inj:
                auto_applied.append(f"Injury: {inj.get('description', 'injured')}")
            continue

        if etype in ("skill_choice", "stat_choice", "pending_choice", "skill_check",
                     "free_skill_choice", "injury_severity_choice", "skill_loss_choice") and pending_set:
            continue  # only one pending at a time

        msgs, was_pending = _apply_mishap_effect(character, effect, term)
        # Redirect pending to event choice field instead of mishap choice field
        if was_pending and character.pending_career_mishap_choice is not None:
            character.pending_career_event_choice = character.pending_career_mishap_choice
            character.pending_career_mishap_choice = None
            pending_set = True
        auto_applied.extend(msgs)
        if was_pending:
            pending_set = True

    return auto_applied, disaster_result


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
        skill_level = int(pending.get("level", 1))   # custom level (e.g. 2 for Truther event 9)
        # Empty options list means "any skill" — skip validation
        if options and skill not in options:
            raise ValueError(f"'{skill}' not in options {options}")
        # Support "Contact [...]" options: add as a contact rather than a skill
        if skill.startswith("Contact"):
            desc = skill  # e.g. "Contact [Criminal]"
            character.associates.append(Associate(kind="contact", description=desc))
            auto_applied.append(f"Gained {desc}")
            character.log(f"Skill choice: contact option selected — {desc}")
            character.pending_career_mishap_choice = None
        elif re.match(r"^(.+?)\s*\(any\)$", skill, re.IGNORECASE):
            # "Pilot (any)", "Science (any)" — chain another picker for the speciality
            _any_base = re.match(r"^(.+?)\s*\(any\)$", skill, re.IGNORECASE).group(1).strip()
            _spec_list = rules.skill_specialities().get(_any_base, [])
            character.pending_career_mishap_choice = None
            if _spec_list:
                # Temporarily put a new choice in the event-choice slot so JS sees it
                character.pending_career_event_choice = {
                    "type": "skill_choice",
                    "options": [f"{_any_base} ({s})" for s in _spec_list],
                    "prompt": f"Choose a {_any_base} speciality to gain at level 1:",
                }
                auto_applied.append(f"{_any_base} speciality choice pending")
                character.log(f"Skill choice: {_any_base} (any) → speciality picker chained")
            else:
                # No specialities — add base skill
                msg = character.add_skill(_any_base, level=1, speciality=None)
                auto_applied.append(msg)
                character.log(f"Skill choice: {_any_base} (any) → no specialities known, base skill added")
        else:
            sn, spec = _split_skill_speciality(skill)
            # Strip literal "(any)" speciality — shouldn't be stored as a real speciality
            if spec and spec.lower() == "any":
                spec = None
            msg = character.add_skill(sn, level=skill_level, speciality=spec)
            auto_applied.append(msg)
            character.pending_career_mishap_choice = None

    elif ptype == "skill_loss_choice":
        skill = choice_data.get("skill", "")
        if not skill:
            raise ValueError("skill_loss_choice requires a 'skill' key in choice_data")
        sn, spec = _split_skill_speciality(skill)
        # Find the matching Skill object in the list (character.skills is a list, not a dict)
        matched: Optional["Skill"] = None
        for sk in character.skills:
            if sk.name == sn and (sk.speciality or "").lower() == (spec or "").lower():
                matched = sk
                break
        if matched is None:
            # Try base-name-only match (ignore speciality)
            for sk in character.skills:
                if sk.name == sn:
                    matched = sk
                    break
        if matched is None:
            auto_applied.append(f"{skill} not found on this character — no level lost")
            character.log(f"Mishap skill loss: {skill} not found, no change")
        elif matched.level <= 0:
            auto_applied.append(f"{skill} already at level 0 — no further reduction")
            character.log(f"Mishap skill loss: {skill} already at 0")
        else:
            old_lvl = matched.level
            matched.level -= 1
            auto_applied.append(f"{skill} {old_lvl}→{matched.level}")
            character.log(f"Mishap skill loss: {skill} {old_lvl}→{matched.level}")
        character.pending_career_mishap_choice = None

    elif ptype == "pending_choice":
        choice_id = pending.get("id", "")
        selected = choice_data.get("option_id", "")

        if choice_id == "party_mishap5_ally":
            if selected == "accept":
                character.associates.append(
                    Associate(kind="ally", description="Ally [Fellow Sufferer]")
                )
                auto_applied.append("Gained Ally [Fellow Sufferer]")
                character.log("Mishap: party_mishap5_ally accepted — Ally gained")
            else:
                auto_applied.append("Declined solidarity — no Ally gained")
                character.log("Mishap: party_mishap5_ally declined")
            character.pending_career_mishap_choice = None

        # ---- Vargr pending_choice handlers ----

        elif choice_id == "vargr_army_illegal_leader":
            if selected == "join":
                character.associates.append(
                    Associate(kind="ally", description="Ally [Corrupt Pack Leader]")
                )
                old_soc = character.characteristics.get("SOC")
                character.characteristics["SOC"] = max(0, old_soc - 1)
                auto_applied.append(f"Joined ring — Ally [Corrupt Pack Leader] + SOC {old_soc}→{character.characteristics['SOC']}")
                character.log("Mishap vargr_army_illegal_leader: joined, ally gained, SOC-1")
            else:  # testify
                old_soc = character.characteristics.get("SOC")
                character.characteristics["SOC"] = old_soc + 1
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Reported Pack Leader]")
                )
                auto_applied.append(f"Testified — SOC {old_soc}→{character.characteristics['SOC']} + Enemy [Reported Pack Leader]")
                character.log("Mishap vargr_army_illegal_leader: testified, SOC+1, enemy gained")
            character.pending_career_mishap_choice = None

        elif choice_id == "vargr_citizen_cooperate":
            if selected == "aid":
                character.dm_next_qualification += 2
                auto_applied.append("Aided investigations — DM+2 to next Qualification roll")
                character.log("Mishap vargr_citizen_cooperate: aided, dm_next_qualification +2")
            else:  # refuse
                character.associates.append(
                    Associate(kind="ally", description="Ally [Criminal Company Contact]")
                )
                auto_applied.append("Refused — gained Ally [Criminal Company Contact]")
                character.log("Mishap vargr_citizen_cooperate: refused, ally gained")
            character.pending_career_mishap_choice = None

        elif choice_id == "vargr_corsair_betrayal":
            if selected == "auto_enemy":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Corsair Betrayer]")
                )
                auto_applied.append("No contacts/allies in band — gained Enemy [Corsair Betrayer]")
                character.log("Mishap vargr_corsair_betrayal: auto enemy (no contacts/allies)")
            else:
                idx = choice_data.get("associate_index")
                if idx is None:
                    raise ValueError("associate_index required for vargr_corsair_betrayal")
                idx = int(idx)
                if idx < 0 or idx >= len(character.associates):
                    raise ValueError(f"associate_index {idx} out of range")
                assoc = character.associates[idx]
                old_kind = assoc.kind
                assoc.kind = "enemy"
                assoc.description = f"Enemy [Betrayer — was {old_kind}]: {assoc.description or ''}"
                auto_applied.append(f"{old_kind.capitalize()} betrayed you → Enemy: {assoc.description}")
                character.log(f"Mishap vargr_corsair_betrayal: associate {idx} ({old_kind}) → enemy")
            character.pending_career_mishap_choice = None

        elif choice_id == "vargr_law_deal":
            if selected == "accept":
                old_soc = character.characteristics.get("SOC")
                character.characteristics["SOC"] = max(0, old_soc - 1)
                auto_applied.append(f"Accepted deal — forced out + SOC {old_soc}→{character.characteristics['SOC']}")
                character.log("Mishap vargr_law_deal: accepted, SOC-1, forced out")
            else:  # refuse
                inj = apply_injury(character)
                if inj:
                    auto_applied.append(f"Injury: {inj.get('description', 'injured')}")
                    injury_data = inj
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Criminal — refused deal]")
                )
                auto_applied.append("Refused — Enemy [Criminal] gained")
                character.log("Mishap vargr_law_deal: refused, injury + enemy")
            character.pending_career_mishap_choice = None

        elif choice_id == "vargr_scientist_funding":
            if selected == "stay":
                if term is not None:
                    term.survived = True
                    term.mishap = None
                    term.benefit_forfeited = True
                auto_applied.append("Stayed quietly — career continues, benefit forfeited")
                character.log("Mishap vargr_scientist_funding: stayed, career_continues, benefit forfeited")
            else:  # roll_soc
                soc_val = character.characteristics.get("SOC", 0)
                soc_dm = (soc_val // 3) - 2
                r2d = dice.roll("2D", modifier=soc_dm)
                raw = r2d.total - soc_dm
                total = r2d.total
                passed = total >= 8
                auto_applied.append(
                    f"SOC 8+ check: 2D={raw}, DM{soc_dm:+d} = {total} → {'PASS' if passed else 'FAIL'}"
                )
                if passed:
                    if term is not None:
                        term.survived = True
                        term.mishap = None
                    character.associates.append(
                        Associate(kind="enemy", description="Enemy [Former Pack / Old Employer]")
                    )
                    auto_applied.append("Career continues with new pack — Enemy [Former Pack] gained")
                    character.log("Mishap vargr_scientist_funding: SOC check passed, career continues, enemy gained")
                else:
                    auto_applied.append("SOC check failed — forced out of career")
                    character.log("Mishap vargr_scientist_funding: SOC check failed, career ends")
            character.pending_career_mishap_choice = None

        elif choice_id == "mishap_deal":
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

        elif choice_id == "aslan_brave_fight":
            if selected == "fight":
                # Chain into skill check — player chose to fight bravely
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Gun Combat"}, {"name": "Athletics"}],
                    "target": 8,
                    "on_nat2": [{"type": "injury"}],
                    "on_pass": [{"type": "career_continues"}],
                    "on_fail": [{"type": "injury"}],
                    "prompt": "Fighting bravely — Roll Gun Combat or Athletics 8+ to survive and stay",
                }
                auto_applied.append("Chose to fight bravely — must now roll Gun Combat or Athletics 8+")
            else:  # refuse — career simply ends (no further effects)
                character.pending_career_mishap_choice = None
                auto_applied.append("Refused to fight bravely — career ends")
                character.log("Mishap: refused to fight bravely, career ends")

        elif choice_id == "aslan_mgmt_accused":
            if selected == "guilty":
                # Stole: SOC reduced to 2, forced into Outcast next
                old_soc = character.characteristics.get("SOC")
                if old_soc > 2 and character.pre_outcast_soc == 0:
                    character.pre_outcast_soc = old_soc
                character.characteristics.set("SOC", min(old_soc, 2))
                character.forced_next_career_id = "aslan_outcast"
                character.pending_career_mishap_choice = None
                auto_applied.append(f"Admitted guilt — SOC reduced to 2 (was {old_soc}), must take Outcast career next")
                character.log("Mishap: admitted theft — SOC→2, forced into Outcast")
            else:  # innocent — chain into Advocate skill check
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Advocate"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "career_continues"}],
                    "on_fail": [],
                    "prompt": "Protesting innocence — Roll Advocate 8+ to defend yourself and stay in the career",
                }
                auto_applied.append("Claiming innocence — must now roll Advocate 8+")

        elif choice_id == "aslan_scientist_leave":
            if selected == "leave":
                character.forced_next_career_id = "scholar"
                auto_applied.append("Left for human space — auto-qualifies for Scholar career next term")
                character.log("Mishap: scientist leaves for human space, Scholar auto-entry set")
            else:
                auto_applied.append("Accepted career end — no further effect")
            character.pending_career_mishap_choice = None

        elif choice_id == "ge_forced_career_choice":
            career_map = {"landless_one": "ge_landless_one", "outlaw": "aslan_outlaw"}
            next_id = career_map.get(selected, "ge_landless_one")
            character.forced_next_career_id = next_id
            auto_applied.append(f"Must take {next_id.replace('_', ' ').title()} career next term")
            character.log(f"Mishap: GE forced career choice — {next_id}")
            character.pending_career_mishap_choice = None

        elif choice_id == "ge_hierate_capture":
            if selected == "return":
                # Return to Empire — choose Landless One or Outlaw (give them one more choice)
                character.pending_career_mishap_choice = {
                    "type": "pending_choice",
                    "id": "ge_forced_career_choice",
                    "prompt": "Return to Empire — choose your next career:",
                    "options": [
                        {"id": "landless_one", "label": "Landless One"},
                        {"id": "outlaw",       "label": "Outlaw"},
                    ],
                }
                auto_applied.append("Returning to Empire — choose Landless One or Outlaw next")
            else:
                # Stay in Hierate — SOC 2, gain Contact
                old_soc = character.characteristics.get("SOC")
                if old_soc > 2 and character.pre_outcast_soc == 0:
                    character.pre_outcast_soc = old_soc
                character.characteristics.set("SOC", min(old_soc, 2))
                character.associates.append(
                    Associate(kind="contact", description="Contact [Hierate Clan Member]")
                )
                auto_applied.append(
                    f"Stayed in Hierate — SOC {old_soc}→{min(old_soc, 2)}, gained Contact [Hierate Clan Member]"
                )
                character.log("Mishap: stayed in Hierate — SOC capped at 2, gained Contact")
                character.pending_career_mishap_choice = None

        elif choice_id == "ge_lose_associate_or_forfeit":
            if selected.startswith("associate_"):
                try:
                    idx = int(selected.split("_", 1)[1])
                    if 0 <= idx < len(character.associates):
                        removed = character.associates.pop(idx)
                        auto_applied.append(
                            f"Lost {removed.kind.capitalize()}: {removed.description or '(unnamed)'}"
                        )
                        character.log(f"Mishap: lost associate {removed.kind} — {removed.description}")
                except (ValueError, IndexError):
                    pass
            else:  # forfeit
                if term is not None:
                    term.benefit_forfeited = True
                auto_applied.append("Benefit roll forfeited (no Allies/Contacts to lose)")
                character.log("Mishap: forfeit benefit — no associates")
            character.pending_career_mishap_choice = None

        elif choice_id == "ge_slave_revolt":
            if selected == "report":
                # Auto-promote + Enemy [Revolt Leader]
                if term is not None:
                    old_rank = term.rank
                    max_rank = max((int(k) for k in rules.careers().get(term.career_id, {})
                                   .get("ranks", {}).get(term.assignment_id or "", {}).keys()),
                                  default=6)
                    term.rank = min(old_rank + 1, max_rank)
                    auto_applied.append(f"Reported the revolt — auto-promoted: rank {old_rank}→{term.rank}")
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Slave Revolt Leader]")
                )
                auto_applied.append("Gained Enemy [Slave Revolt Leader]")
                character.log("Mishap: reported revolt — promoted + enemy gained")
            else:  # allow revolt
                inj = apply_injury(character)
                if inj:
                    auto_applied.append(f"Revolt injury: {inj.get('description', 'injured')}")
                character.forced_next_career_id = "prisoner"
                auto_applied.append("Allowed revolt — roll on Injury table and must take Prisoner career next term")
                character.log("Mishap: allowed revolt — injury + forced Prisoner")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_ter_or_dm4":
            if selected == "ter":
                ter_val = character.extra_characteristics.get("TER", 0)
                new_ter = ter_val + 2
                character.extra_characteristics["TER"] = new_ter
                auto_applied.append(f"TER {ter_val}→{new_ter} (+2)")
                character.log("Event choice: TER +2")
            else:
                character.dm_next_advancement += 4
                auto_applied.append("DM+4 to next Advancement roll")
                character.log("Event choice: DM+4 to next advancement")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_skill_or_dm4":
            if selected == "skill":
                skill_name = pending.get("skill_option", "")
                if skill_name:
                    msg = character.add_skill(skill_name, level=1)
                    auto_applied.append(msg)
            else:
                dm = pending.get("dm_amount", 4)
                auto_applied.append(f"DM+{dm} to next Advancement roll")
                character.dm_next_advancement += dm
                character.log(f"Event choice: DM+{dm} to next advancement")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_ransom_or_free":
            if selected == "ransom":
                ter_amount = pending.get("ransom_ter_amount", 2)
                ter_val = character.extra_characteristics.get("TER", 0)
                new_ter = ter_val + ter_amount
                character.extra_characteristics["TER"] = new_ter
                auto_applied.append(f"TER +{ter_amount}: {ter_val}→{new_ter}")
                character.log(f"Event choice: ransomed commander for TER +{ter_amount}")
            else:
                character.associates.append(
                    Associate(kind="ally", description="Ally [Freed Enemy Commander]")
                )
                auto_applied.append("Gained Ally [Freed Enemy Commander]")
                character.log("Event choice: freed commander, gained Ally")
            character.pending_career_mishap_choice = None

        # ----- generic event choice handlers -----

        elif choice_id == "event_skillmulti_or_dm4":
            # option id = exact skill name (e.g. "Heavy Weapons") or "dm4"
            if selected == "dm4":
                dm = pending.get("dm_amount", 4)
                character.dm_next_advancement += dm
                auto_applied.append(f"DM+{dm} to next Advancement roll")
                character.log(f"Event choice: DM+{dm} to next advancement")
            else:
                sn, spec = _split_skill_speciality(selected)
                msg = character.add_skill(sn, level=1, speciality=spec)
                auto_applied.append(msg)
            character.pending_career_mishap_choice = None

        elif choice_id == "event_contact_or_ally":
            contact_desc = pending.get("contact_desc", "Contact")
            ally_desc = pending.get("ally_desc", "Ally")
            if selected == "contact":
                character.associates.append(Associate(kind="contact", description=contact_desc))
                auto_applied.append(f"Gained {contact_desc}")
            else:
                character.associates.append(Associate(kind="ally", description=ally_desc))
                auto_applied.append(f"Gained {ally_desc}")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_dm_type_choice":
            # citizen event 10: DM+2 advancement OR DM+1 benefit
            if selected == "advancement":
                character.dm_next_advancement += 2
                auto_applied.append("DM+2 to next Advancement roll")
                character.log("Event choice: DM+2 advancement")
            else:
                character.dm_next_benefit += 1
                auto_applied.append("DM+1 to next Benefit roll")
                character.log("Event choice: DM+1 benefit")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_expose_or_suppress":
            # expose → dm_advancement+2 + enemy; suppress → ally
            ally_desc = pending.get("ally_desc", "Ally [Suppressed Information]")
            enemy_desc = pending.get("enemy_desc", "Enemy [Exposed Person]")
            if selected == "expose":
                character.dm_next_advancement += 2
                auto_applied.append("DM+2 to next Advancement roll")
                character.associates.append(Associate(kind="enemy", description=enemy_desc))
                auto_applied.append(f"Gained {enemy_desc}")
                character.log(f"Event choice: expose — DM+2 advancement, gained {enemy_desc}")
            else:
                character.associates.append(Associate(kind="ally", description=ally_desc))
                auto_applied.append(f"Gained {ally_desc}")
                character.log(f"Event choice: suppress — gained {ally_desc}")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_report_or_suppress":
            # report → dm_advancement+2 + enemy; suppress → ally
            ally_desc = pending.get("ally_desc", "Ally [Corrupt Contact]")
            enemy_desc = pending.get("enemy_desc", "Enemy [Reported Person]")
            if selected == "report":
                character.dm_next_advancement += 2
                auto_applied.append("DM+2 to next Advancement roll")
                character.associates.append(Associate(kind="enemy", description=enemy_desc))
                auto_applied.append(f"Gained {enemy_desc}")
                character.log(f"Event choice: report — DM+2 advancement, gained {enemy_desc}")
            else:
                character.associates.append(Associate(kind="ally", description=ally_desc))
                auto_applied.append(f"Gained {ally_desc}")
                character.log(f"Event choice: suppress — gained {ally_desc}")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_surveil_or_rapport":
            # solsec event 4: surveil (skill choice) or rapport (contact)
            if selected == "surveil":
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Investigate", "Stealth"],
                    "prompt": "Choose skill gained from surveillance:",
                }
            else:
                desc = pending.get("contact_desc", "Contact [Monitored Citizen]")
                character.associates.append(Associate(kind="contact", description=desc))
                auto_applied.append(f"Gained {desc}")
                character.pending_career_mishap_choice = None

        elif choice_id == "event_marine_rescue":
            # marine/solomani_marine event 10: ally always; DM+1 benefit OR transfer note
            ally_desc = pending.get("ally_desc", "Ally [Rescued Marine]")
            character.associates.append(Associate(kind="ally", description=ally_desc))
            auto_applied.append(f"Gained {ally_desc}")
            if selected == "benefit":
                character.dm_next_benefit += 1
                auto_applied.append("DM+1 to next Benefit roll")
            else:
                character.pending_transfer_career_id = "army"
                auto_applied.append("Transfer offer accepted — will auto-qualify for Army next term (no Qualification roll).")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_navy_transfer":
            # navy event 10: skill choice OR transfer to Marines note
            if selected == "transfer":
                character.pending_transfer_career_id = "marines"
                auto_applied.append("Transfer accepted — will auto-qualify for Marines next term (no Qualification roll).")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Gun Combat", "Melee (blade)", "Vacc Suit", "Leadership"],
                    "prompt": "Choose skill gained from elite unit transfer:",
                }

        elif choice_id == "event_entertainer_celebrity":
            # entertainer event 6: player chooses relationship type with celebrity
            desc = pending.get("desc", f"{selected.capitalize()} [Celebrity/Noble/Criminal Figure]")
            if selected in ("contact", "ally", "rival", "enemy"):
                character.associates.append(Associate(kind=selected, description=desc))
                auto_applied.append(f"Gained {selected.capitalize()}: {desc}")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_noble_duel":
            # noble event 3: refuse (SOC-1) or accept (Melee blade 8+ → pass SOC+1, fail injury+SOC-1)
            if selected == "refuse":
                soc_old = character.characteristics.SOC
                character.characteristics.set("SOC", max(0, soc_old - 1))
                auto_applied.append(f"Refused duel — SOC {soc_old}→{max(0, soc_old - 1)} (−1)")
                character.log("Noble duel: refused, SOC-1")
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Melee (blade)", "Leadership", "Tactics", "Deception"],
                    "prompt": "Gain one skill from the duel:",
                }
            else:
                auto_applied.append("Accepted duel — rolling Melee (blade) 8+")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Melee (blade)"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1},
                                {"type": "skill_choice",
                                 "options": ["Melee (blade)", "Leadership", "Tactics", "Deception"],
                                 "prompt": "Duel complete — gain one skill:"}],
                    "on_fail": [{"type": "injury"}, {"type": "stat", "stat": "SOC", "amount": -1},
                                {"type": "skill_choice",
                                 "options": ["Melee (blade)", "Leadership", "Tactics", "Deception"],
                                 "prompt": "Duel complete — gain one skill:"}],
                    "prompt": "You accepted the duel — roll Melee (blade) 8+: pass SOC+1; fail injury+SOC−1. Either way gain a skill.",
                }

        elif choice_id == "event_noble_duel_skill":
            # always-fired skill choice after noble duel (win or lose still get skill)
            character.pending_career_mishap_choice = {
                "type": "skill_choice",
                "options": ["Melee (blade)", "Leadership", "Tactics", "Deception"],
                "prompt": "Gain one skill from the duel:",
            }

        elif choice_id == "event_noble_conspiracy":
            # noble event 8: refuse (enemy) or accept (Deception/Persuade 8+)
            if selected == "refuse":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Noble Conspiracy]")
                )
                auto_applied.append("Refused conspiracy — gained Enemy [Noble Conspiracy]")
                character.log("Noble conspiracy: refused, gained enemy")
                character.pending_career_mishap_choice = None
            else:
                auto_applied.append("Accepted conspiracy — rolling Deception or Persuade 8+")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Deception"}, {"name": "Persuade"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "skill_choice",
                                 "options": ["Deception", "Persuade", "Tactics", "Carouse"]}],
                    "on_fail": [{"type": "trigger_disaster_mishap"}],
                    "prompt": "Conspiracy operation — roll Deception or Persuade 8+: pass skill choice; fail mishap (career continues)",
                }

        elif choice_id == "event_party_takebane":
            # party event 5: accept blame (ally or benefit DM) or refuse (DM-2 adv + rival)
            if selected == "accept":
                character.associates.append(
                    Associate(kind="ally", description="Ally [Senior Party Member]")
                )
                auto_applied.append("Accepted blame — gained Ally [Senior Party Member]")
                character.dm_next_benefit += 1
                auto_applied.append("DM+1 to next Benefit roll")
                character.log("Party event 5: accepted blame, ally + benefit DM")
            else:
                character.dm_next_advancement -= 2
                auto_applied.append("Refused — DM−2 to next Advancement roll")
                character.associates.append(
                    Associate(kind="rival", description="Rival [Senior Party Member]")
                )
                auto_applied.append("Gained Rival [Senior Party Member]")
                character.log("Party event 5: refused, DM-2 advancement, rival")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_party_evidence":
            # party event 8: expose (DM+2 adv) or suppress (ally)
            if selected == "expose":
                character.dm_next_advancement += 2
                auto_applied.append("Exposed superior — DM+2 to next Advancement roll")
                character.log("Party event 8: exposed superior, DM+2 advancement")
            else:
                character.associates.append(
                    Associate(kind="ally", description="Ally [Party Superior — supported]")
                )
                auto_applied.append("Suppressed evidence — gained Ally [Party Superior]")
                character.log("Party event 8: suppressed evidence, gained ally")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_merchant_agreement":
            # merchant event 8: ally always; DM+1 benefit OR DM+2 advancement
            character.associates.append(Associate(kind="ally", description="Ally [Major Client]"))
            auto_applied.append("Gained Ally [Major Client]")
            if selected == "benefit":
                character.dm_next_benefit += 1
                auto_applied.append("DM+1 to next Benefit roll")
            else:
                character.dm_next_advancement += 2
                auto_applied.append("DM+2 to next Advancement roll")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_citizen_free_transfer":
            # citizen/drifter event 11: skill OR free career transfer
            if selected == "transfer":
                character.pending_transfer_career_id = "any"
                auto_applied.append("Free transfer accepted — will auto-qualify for any non-military career next term (no Qualification roll).")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "free_skill_choice",
                    "prompt": "Gain one level in any service skill of your choice:",
                }

        elif choice_id == "event_drifter_skill_or_transfer":
            # drifter event 11 (new): free skill OR transfer to any career
            if selected == "transfer":
                character.pending_transfer_career_id = "any"
                auto_applied.append("Free transfer accepted — will auto-qualify for any career next term (no Qualification roll).")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "free_skill_choice",
                    "prompt": "Gain one level in any skill of your choice:",
                }

        elif choice_id == "event_solsec_leverage":
            # solsec event 10: expose (DM+2 adv + enemy) or leverage (ally + rival)
            if selected == "expose":
                character.dm_next_advancement += 2
                auto_applied.append("Exposed disloyal official — DM+2 to next Advancement roll")
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Exposed Official]")
                )
                auto_applied.append("Gained Enemy [Exposed Official]")
            else:
                character.associates.append(
                    Associate(kind="ally", description="Ally [Official — leveraged silence]")
                )
                auto_applied.append("Gained Ally [Official — leveraged silence]")
                character.associates.append(
                    Associate(kind="rival", description="Rival [Suspicious SolSec Faction]")
                )
                auto_applied.append("Gained Rival [Suspicious SolSec Faction]")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_confnav_recreation":
            # confederation navy event 4: recreation (skill) or study (DM+2 adv or INT 8+ for skill)
            if selected == "recreation":
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Carouse", "Gambler"],
                    "prompt": "Recreation — choose skill gained:",
                }
            elif selected == "study":
                character.dm_next_advancement += 2
                auto_applied.append("Study group — DM+2 to next Advancement roll")
                character.pending_career_mishap_choice = None
            elif selected == "study_int":
                # Roll INT 8+ to gain Advocate, History (Science) or Science
                int_dm = dice.characteristic_dm(character.characteristics.INT)
                r = dice.roll("2D", modifier=int_dm, target=8)
                if r.succeeded:
                    character.pending_career_mishap_choice = {
                        "type": "skill_choice",
                        "options": ["Advocate", "Science (History)", "Science"],
                        "prompt": "Study group INT roll succeeded — choose skill gained:",
                    }
                    auto_applied.append(
                        f"Study group INT 8+ check: {r.total} (2D{int_dm:+d}={r.total} vs 8+) — passed"
                    )
                else:
                    auto_applied.append(
                        f"Study group INT 8+ check: {r.total} (2D{int_dm:+d}={r.total} vs 8+) — failed (no skill gained)"
                    )
                    character.pending_career_mishap_choice = None

        elif choice_id == "navy_specialist_training":
            # navy event 11: upgrade any existing skill OR DM+4 advancement
            if selected == "dm4":
                character.dm_next_advancement += 4
                auto_applied.append("DM+4 to next Advancement roll")
                character.log("Event choice: DM+4 advancement (navy specialist training)")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "free_skill_choice",
                    "prompt": "Increase any one skill you already have by one level:",
                }

        elif choice_id == "prisoner_contraband":
            # prisoner event 5: skill choice or DM+2 benefit
            if selected == "benefit":
                character.dm_next_benefit += 2
                auto_applied.append("DM+2 to next Benefit roll")
                character.log("Event choice: DM+2 benefit (prisoner contraband)")
                character.pending_career_mishap_choice = None
            else:
                sn, spec = _split_skill_speciality(selected)
                msg = character.add_skill(sn, level=1, speciality=spec)
                auto_applied.append(msg)
                character.pending_career_mishap_choice = None

        elif choice_id == "entertainer_patronage":
            # entertainer event 11: free skill OR DM+4 advancement
            if selected == "dm4":
                character.dm_next_advancement += 4
                auto_applied.append("DM+4 to next Advancement roll")
                character.log("Event choice: DM+4 to next advancement")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "free_skill_choice",
                    "prompt": "Gain one level in any skill of your choice:",
                }

        elif choice_id == "bounty_hunter_deal":
            # bounty hunter mishap 2: accept (Cr50k + REP-1) or refuse (enemy + D3 enemies)
            if selected == "accept":
                character.reputation = max(0, character.reputation - 1)
                character.credits += 50000
                auto_applied.append(f"Accepted deal — REP −1 (now {character.reputation}), gained Cr50,000 (credits now {character.credits:,}).")
                character.log("BH mishap 2: accepted deal, REP-1")
            else:
                character.reputation = max(0, character.reputation - 1)
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Bounty Mark]")
                )
                auto_applied.append(f"Refused — Enemy [Bounty Mark] gained; REP −1 (now {character.reputation})")
                # D3 more enemies from the mark's associates
                count = (dice.roll("1D").total + 1) // 2
                for _ in range(count):
                    character.associates.append(
                        Associate(kind="enemy", description="Enemy [Mark's Ally/Friend]")
                    )
                auto_applied.append(f"Also gained {count} more Enemy (mark's associates)")
                character.log(f"BH mishap 2: refused, Enemy + {count} enemies, REP-1")
            character.pending_career_mishap_choice = None

        elif choice_id == "bounty_hunter_rep_or_debt":
            # bounty hunter mishap 6: REP-1 OR MCr1 debt
            if selected == "rep":
                character.reputation = max(0, character.reputation - 1)
                auto_applied.append(f"Took REP hit — REP −1 (now {character.reputation})")
                character.log("BH mishap 6: REP-1")
            else:
                character.medical_debt += 1_000_000
                auto_applied.append("Took MCr1 debt to crime lord (Cr1,000,000 at 20% annual interest once mustered out)")
                character.log("BH mishap 6: MCr1 debt to crime lord")
            character.pending_career_mishap_choice = None

        elif choice_id == "cetacean_conflict_choice":
            # dolphin/orca event 3: diplomacy or violence, each with a skill check
            skill_options = pending.get("diplomacy_skills", ["Advocate", "Diplomat"])
            violence_skills = pending.get("violence_skills", ["Explosives", "Gun Combat", "Tactics"])
            if selected == "diplomacy":
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": s} for s in skill_options],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 2}],
                    "on_fail": [{"type": "forfeit_benefit"}],
                    "prompt": f"Diplomacy — roll {'/'.join(skill_options)} 8+: pass DM+2 Adv; fail lose Benefit roll",
                }
                auto_applied.append("Chose diplomacy — rolling skill check")
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": s} for s in violence_skills],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [],
                    "on_fail": [{"type": "dm_advancement", "amount": -2}, {"type": "injury"}],
                    "prompt": f"Violence — roll {'/'.join(violence_skills)} 8+: fail DM−2 Adv + injury",
                }
                auto_applied.append("Chose violence — rolling skill check")

        elif choice_id == "cetacean_fight_or_flee":
            # dolphin/orca/spirit_singer event 9: flee (enemy) or fight (skill check → ally/injury)
            fight_skills = pending.get("fight_skills", ["Melee (natural)", "Gun Combat"])
            target = pending.get("target", 7)
            if selected == "flee":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Survivor Who Blames You]")
                )
                auto_applied.append("Fled — gained Enemy [Survivor Who Blames You]")
                character.log("Cetacean event 9: fled, gained enemy")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": s} for s in fight_skills],
                    "target": target,
                    "on_nat2": [],
                    "on_pass": [{"type": "ally", "desc": "Ally [Rescued Companion]"}],
                    "on_fail": [{"type": "injury"}],
                    "prompt": f"Fought — roll {'/'.join(fight_skills)} {target}+: pass Ally; fail injury",
                }
                auto_applied.append("Stayed and fought — rolling skill check")

        elif choice_id == "cetacean_accept_or_protest":
            # dolphin_military event 10: accept blame (DM-1 adv) or protest (Advocate/SOC 8+)
            if selected == "accept":
                character.dm_next_advancement -= 1
                auto_applied.append("Accepted blame — DM−1 to next Advancement roll")
                character.log("Cetacean event 10: accepted blame, DM-1 advancement")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Advocate"}, {"name": "SOC", "is_stat": True}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 1},
                                {"type": "skill_choice", "options": ["Leadership", "Advocate"]}],
                    "on_fail": [{"type": "dm_advancement", "amount": -2}],
                    "prompt": "Protest — roll Advocate or SOC 8+: pass DM+1 Adv + skill; fail DM−2 Adv",
                }
                auto_applied.append("Protested — rolling Advocate or SOC 8+")

        elif choice_id == "spirit_singer_matriarch":
            # spirit_singer event 10: consult dying matriarch (agree or decline)
            if selected == "agree":
                character.associates.append(
                    Associate(kind="ally", description="Ally [Dying Matriarch's Pod]")
                )
                auto_applied.append("Agreed — gained Ally [Dying Matriarch's Pod]")
                character.associates.append(
                    Associate(kind="rival", description="Rival [Own Faith — disapproves]")
                )
                auto_applied.append("Gained Rival [Own Faith — disapproves of choice]")
                character.log("Spirit singer event 10: agreed, ally + rival")
            else:
                auto_applied.append("Declined — no mechanical effect")
                character.log("Spirit singer event 10: declined")
            character.pending_career_mishap_choice = None

        elif choice_id == "aslan_outcast_join_ihatei":
            # aslan_outcast event 9: join the ihatei's retinue or decline
            if selected == "join":
                character.associates.append(
                    Associate(kind="ally", description="Ally [Ihatei — joined retinue]")
                )
                character.next_career_must_be_core = True
                auto_applied.append("Joined ihatei — gained Ally [Ihatei]. Must qualify for a Core Rulebook career next term.")
                character.log("Outcast event 9: joined ihatei, ally, next career must be core rulebook")
            else:
                auto_applied.append("Declined — no effect")
            character.pending_career_mishap_choice = None

        elif choice_id == "aslan_outlaw_bounty":
            # aslan_outlaw event 5: normal path OR try to claim reward yourself
            if selected == "normal":
                # enemy + skill choice
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Clan — put price on your head]")
                )
                auto_applied.append("Clan put price on head — gained Enemy [Clan]")
                character.log("Outlaw event 5: normal path, enemy + skill choice")
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Stealth", "Streetwise", "Gun Combat", "Survival"],
                    "prompt": "Gain one skill from evading the bounty:",
                }
            else:
                # Risky: Deception 8+ → 3 benefit rolls; fail END-2 + career ends
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Clan — put price on your head]")
                )
                auto_applied.append("Attempting to claim the reward — rolling Deception 8+")
                character.log("Outlaw event 5: risky path, Enemy added, rolling Deception")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Deception"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "extra_benefit", "amount": 3}],
                    "on_fail": [{"type": "stat", "stat": "END", "amount": -2},
                                {"type": "force_career_end"}],
                    "prompt": "Claim the reward — roll Deception 8+: pass 3 extra Benefit rolls; fail END−2 and ejected from career",
                }

        elif choice_id == "aslan_outlaw_pass_reward":
            # aslan_outlaw event 9 pass: extra benefit OR SOC+1
            if selected == "benefit":
                character.pending_benefit_rolls += 1
                auto_applied.append("Gained 1 extra Benefit roll")
                character.log("Outlaw event 9 pass: extra benefit")
            else:
                soc_old = character.characteristics.SOC
                character.characteristics.set("SOC", soc_old + 1)
                auto_applied.append(f"SOC {soc_old}→{soc_old + 1} (+1)")
                character.log("Outlaw event 9 pass: SOC+1")
            character.pending_career_mishap_choice = None

        elif choice_id == "aslan_outlaw_mission":
            # aslan_outlaw event 10: accept mission (Stealth 8+) OR inform enemies (benefit + enemy)
            if selected == "accept":
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Stealth"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "extra_benefit", "amount": 1}],
                    "on_fail": [],
                    "prompt": "Covert mission — roll Stealth 8+: pass 1 extra Benefit roll; fail nothing gained",
                }
                auto_applied.append("Accepted mission — rolling Stealth 8+")
            else:
                character.pending_benefit_rolls += 1
                auto_applied.append("Informed enemies — gained 1 Benefit roll")
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Clan — informed on]")
                )
                auto_applied.append("Gained Enemy [Clan — informed on]")
                character.log("Outlaw event 10: informed, benefit + enemy")
                character.pending_career_mishap_choice = None

        elif choice_id == "aslan_outlaw_redemption":
            # aslan_outlaw event 11: male (TER+1 + SOC restore) or female (reroll SOC)
            # Both options leave career after this term
            if selected == "male":
                ter_old = character.extra_characteristics.get("TER", 0)
                character.extra_characteristics["TER"] = ter_old + 1
                auto_applied.append(f"TER {ter_old}→{ter_old + 1} (+1)")
                if character.pre_outcast_soc > 0:
                    old_soc = character.characteristics.SOC
                    character.characteristics.set("SOC", character.pre_outcast_soc)
                    auto_applied.append(f"SOC restored to pre-outcast value: {old_soc}→{character.pre_outcast_soc}")
                    character.log(f"Outlaw redemption (male): SOC {old_soc}→{character.pre_outcast_soc} (restored)")
                else:
                    auto_applied.append("SOC restoration: pre-outcast SOC not recorded — no change made")
                    character.log("Outlaw redemption (male): pre_outcast_soc=0, SOC not restored")
                auto_applied.append("Must leave this career after this term")
                character.log("Outlaw event 11: male redemption, TER+1, SOC restore, career ends next term")
            elif selected == "female":
                soc_roll = dice.roll("2D")
                old_soc = character.characteristics.SOC
                character.characteristics.set("SOC", soc_roll.total)
                auto_applied.append(f"SOC rerolled: 2D={soc_roll.total} (was {old_soc}) → SOC now {soc_roll.total}")
                character.log(f"Outlaw redemption (female): SOC rerolled {old_soc}→{soc_roll.total}")
                auto_applied.append("Must leave this career after this term")
                character.log("Outlaw event 11: female redemption, SOC reroll, career ends next term")
            else:
                auto_applied.append("Declined redemption — no effect")
            character.pending_career_mishap_choice = None

        elif choice_id == "dolphin_mil_massacre":
            # dolphin_military mishap 3: refuse (ejected) or participate (enemy, career continues)
            if selected == "refuse":
                # Career ends normally — nothing to override; ejection proceeds
                auto_applied.append("Refused to participate — ejected from career")
                character.log("DolMil mishap 3: refused massacre, ejected")
            else:
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Indigenous Aquatic Alien]")
                )
                auto_applied.append("Participated — gained Enemy [Indigenous Aquatic Alien]; career continues")
                if term is not None:
                    term.survived = True
                    term.mishap = None
                character.log("DolMil mishap 3: participated, enemy gained, career continues")
            character.pending_career_mishap_choice = None

        elif choice_id == "dolphin_mil_denounce":
            # dolphin_military mishap 5: denounce (enemy, career continues) or don't (ejected)
            if selected == "denounce":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Commander's Ally]")
                )
                auto_applied.append("Denounced commander — gained Enemy [Commander's Ally]; career continues")
                if term is not None:
                    term.survived = True
                    term.mishap = None
                character.log("DolMil mishap 5: denounced, enemy, career continues")
            else:
                auto_applied.append("Did not denounce — ejected from career")
                character.log("DolMil mishap 5: did not denounce, ejected")
            character.pending_career_mishap_choice = None

        elif choice_id == "kkree_noble_mishap4":
            # kkree_noble mishap 4: 1D sub-roll: 1-2 ejected (no further career), 3-4 ejected + Enemy, 5-6 Ally
            sub_r = dice.roll("1D")
            sub = sub_r.total
            if sub <= 2:
                all_career_ids = list(rules.careers().keys())
                for cid in all_career_ids:
                    if cid not in character.banned_career_ids:
                        character.banned_career_ids.append(cid)
                auto_applied.append(
                    f"Mishap 4 (1D={sub}, 1-2): Your fault — ejected; permanently banned from all further careers."
                )
                character.log(f"K'kree Noble mishap 4: 1D={sub}, fault — ejected, all careers banned")
            elif sub <= 4:
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Superior — Blamed You]")
                )
                auto_applied.append(
                    f"Mishap 4 (1D={sub}, 3-4): Blamed — ejected + Enemy [Superior]"
                )
                character.log(f"K'kree Noble mishap 4: 1D={sub}, blamed — ejected + enemy")
            else:
                character.associates.append(
                    Associate(kind="ally", description="Ally [K'kree — Outside Clan]")
                )
                auto_applied.append(
                    f"Mishap 4 (1D={sub}, 5-6): Acclaim — gained Ally [K'kree — Outside Clan]; career continues"
                )
                if term is not None:
                    term.survived = True
                    term.mishap = None
                character.log(f"K'kree Noble mishap 4: 1D={sub}, acclaim — ally, career continues")
            character.pending_career_mishap_choice = None

        elif choice_id == "kkree_servant_mishap4":
            # kkree_servant mishap 4: accept (SOC-1, gain Ally) or refuse (Enemy, gain Outsider 1)
            if selected == "accept":
                old_soc = character.characteristics.get("SOC", 0)
                character.characteristics["SOC"] = max(0, old_soc - 1)
                character.associates.append(Associate(kind="ally", description="Ally [K'kree — Showed Mercy]"))
                auto_applied.append(
                    f"Accepted humiliation — SOC {old_soc}→{character.characteristics['SOC']} (−1); "
                    "gained Ally [K'kree — Showed Mercy]"
                )
                character.log("K'kree Servant mishap 4: accepted, SOC-1, ally")
            else:
                character.associates.append(Associate(kind="enemy", description="Enemy [K'kree — Chose Honour]"))
                _apply_mishap_effect(character, {"type": "skill", "name": "Outsider", "level": 1}, msgs, term)
                auto_applied.append("Refused humiliation — gained Enemy + Outsider 1")
                character.log("K'kree Servant mishap 4: refused, enemy, outsider 1")
            character.pending_career_mishap_choice = None

        # ── Zhodani pending choices ──────────────────────────────────────────

        elif choice_id == "zhodani_army_illegal_co":
            if selected == "join":
                character.associates.append(
                    Associate(kind="ally", description="Ally [Corrupt Commanding Officer]")
                )
                _apply_zhodani_re_education(character, auto_applied)
                auto_applied.append("Joined illegal ring — gained Ally [Corrupt CO], then Re-education Events")
                character.log("Mishap: joined corrupt CO ring, gained ally, re-education")
            else:  # cooperate
                auto_applied.append("Co-operated with Thought Police — kept Benefit roll, left career")
                character.log("Mishap: co-operated with Thought Police, kept benefit")
            character.pending_career_mishap_choice = None

        elif choice_id == "zhodani_guard_conscience":
            if selected == "accept":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Lone Survivor]")
                )
                if term is not None:
                    term.survived = True
                    term.mishap = None
                auto_applied.append("Accepted mission — gained Enemy [Lone Survivor]; stayed in Guards")
                character.log("Mishap: accepted conscience mission, enemy gained, career_continues")
            else:  # refuse
                _apply_zhodani_re_education(character, auto_applied)
                auto_applied.append("Refused mission — rolled Re-education Events, left Guards")
                character.log("Mishap: refused conscience mission, re-education")
            character.pending_career_mishap_choice = None

        elif choice_id == "zhodani_agent_contest":
            if selected == "accept":
                character.pending_benefit_rolls += 1
                auto_applied.append("Accepted fate — gained extra Benefit roll as compensation, left career")
                character.log("Mishap: accepted fate, extra benefit roll")
                character.pending_career_mishap_choice = None
            else:  # contest — chain into Advocate 8+ skill check
                auto_applied.append("Contesting accusation — must roll Advocate 8+")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Advocate"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "career_continues"}],
                    "on_fail": [{"type": "zhodani_re_education"}],
                    "prompt": "Contesting accusation — Roll Advocate 8+ to stay in career",
                }

        elif choice_id == "zhodani_merchant_fine":
            if selected == "pay":
                if term is not None:
                    term.survived = True
                    term.mishap = None
                auto_applied.append("Fine paid — stayed in career")
                character.log("Mishap: merchant fine paid, career continues")
            else:  # dont_pay
                soc = character.characteristics.get("SOC")
                if soc <= 9:
                    _apply_zhodani_re_education(character, auto_applied)
                    auto_applied.append("Fine not paid, SOC 9- — Re-education Events rolled, left career")
                    character.log("Mishap: merchant fine unpaid, SOC 9-, re-education")
                else:
                    auto_applied.append("Fine not paid, SOC 10+ — left career")
                    character.log("Mishap: merchant fine unpaid, SOC 10+, career ends")
            character.pending_career_mishap_choice = None

        elif choice_id == "zhodani_merchant_decline":
            if term is not None:
                term.survived = True
                term.mishap = None
                term.benefit_forfeited = True
            auto_applied.append("Chose to continue — career continues but Benefit roll forfeited this term")
            character.log("Mishap: merchant declining fortunes, career continues, benefit forfeited")
            character.pending_career_mishap_choice = None

        elif choice_id == "zhodani_scholar_research":
            if selected == "secretly":
                if term is not None:
                    term.benefit_forfeited = True
                auto_applied.append("Researching secretly — Benefit roll forfeited")
                character.log("Mishap: scholar research secretly, benefit forfeited")
            else:
                auto_applied.append("Researching openly — no Benefit penalty")
                character.log("Mishap: scholar research openly")
            # Either way: gain one level of any Science skill
            character.pending_career_mishap_choice = {
                "type": "skill_choice",
                "options": [],
                "prompt": "Gain one level in any Science skill (despite government interference)",
            }

        elif choice_id == "zhodani_scholar_sabotage":
            if selected == "give_up":
                auto_applied.append("Gave up research — left career, kept Benefit roll")
                character.log("Mishap: sabotaged research, gave up, career ends, benefit kept")
                character.pending_career_mishap_choice = None
            else:  # restart
                if term is not None:
                    term.survived = True
                    term.mishap = None
                    term.benefit_forfeited = True
                auto_applied.append("Restarting from scratch — career continues, Benefit roll forfeited")
                character.log("Mishap: sabotaged research, restarting, career continues, benefit forfeited")
                character.pending_career_mishap_choice = None

        elif choice_id == "zhodani_lose_associate":
            if selected == "skip":
                auto_applied.append("No Allies or Contacts to lose")
                character.log("Mishap: zhodani_lose_associate — no associates to remove")
            else:
                try:
                    idx = int(selected)
                    if 0 <= idx < len(character.associates):
                        removed = character.associates.pop(idx)
                        auto_applied.append(
                            f"Lost {removed.kind.capitalize()}: {removed.description or '(unnamed)'}"
                        )
                        character.log(f"Mishap: lost associate [{removed.kind}] — {removed.description}")
                except (ValueError, IndexError):
                    pass
            character.pending_career_mishap_choice = None

        # ── Aslan new handlers ────────────────────────────────────────────────

        elif choice_id == "event_aslan_kinfolk_honour":
            # aslan_ceremonial event 10: cover up (ally) or expose (Melee 8+)
            if selected == "cover":
                character.associates.append(
                    Associate(kind="ally", description="Ally [Dishonourable Kinfolk — silence kept]")
                )
                auto_applied.append("Covered up — gained Ally [Dishonourable Kinfolk]")
                character.log("Ceremonial event 10: covered up, ally")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Melee"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "enemy", "desc": "Enemy [Exposed Kinfolk]"},
                                {"type": "stat", "stat": "TER", "amount": 2}],
                    "on_fail": [{"type": "rival", "desc": "Rival [Victorious Kinfolk]"},
                                {"type": "stat", "stat": "SOC", "amount": -2}],
                    "prompt": "Expose kinfolk — roll Melee 8+: pass Enemy + TER+2; fail Rival + SOC−2",
                }

        elif choice_id == "event_ceremonial_secret":
            # aslan_ceremonial event 3: trade secret for 1D Clan Shares (+ elder Enemy) or keep
            if selected == "trade":
                r1d = dice.roll("1D")
                character.clan_shares += r1d.total
                auto_applied.append(f"Traded secret — gained {r1d.total} Clan Shares (total {character.clan_shares})")
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Clan Elder — secret revealed]")
                )
                auto_applied.append("Gained Enemy [Clan Elder — secret revealed]")
                character.log(f"Ceremonial event 3: traded secret, +{r1d.total} clan shares, enemy elder")
            else:
                auto_applied.append("Kept secret in reserve — no immediate effect (enemy if ever used)")
                character.log("Ceremonial event 3: secret kept in reserve")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_aslan_military_insult":
            # aslan_military event 9: duel or prove courage
            if selected == "duel":
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Melee (natural)"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1}],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
                    "prompt": "Duel — roll Melee (natural) 8+: pass SOC+1; fail SOC−1",
                }
            else:  # prove
                r1d = dice.roll("1D")
                if r1d.total <= 3:
                    inj = apply_injury(character)
                    auto_applied.append(f"Trying to prove courage (1D={r1d.total}, 1–3) — wounded!")
                    if inj:
                        auto_applied.append(f"Injury: {inj.get('description', 'injured')}")
                    character.log(f"Military event 9: prove courage 1D={r1d.total} → wounded")
                else:
                    old_soc = character.characteristics.SOC
                    character.characteristics.set("SOC", old_soc + 1)
                    auto_applied.append(f"Proved courage (1D={r1d.total}, 4+) — SOC {old_soc}→{old_soc+1}; DM+4 next Advancement")
                    character.dm_next_advancement += 4
                    character.associates.append(
                        Associate(kind="rival", description="Rival [Officer Who Insulted Your Courage]")
                    )
                    auto_applied.append("Gained Rival [Officer Who Insulted Your Courage]")
                    character.log(f"Military event 9: proved courage 1D={r1d.total} → SOC+1, DM+4, rival")
                character.pending_career_mishap_choice = None

        elif choice_id == "event_aslan_scientist_rival":
            # aslan_scientist event 9: research / sabotage / nothing
            if selected == "research":
                character.associates.append(
                    Associate(kind="rival", description="Rival [Competing Clan Researcher]")
                )
                auto_applied.append("Gained Rival [Competing Clan Researcher]")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Science"}],
                    "target": 10,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 2}],
                    "on_fail": [{"type": "forfeit_all_benefits"}],
                    "prompt": "Research race — roll Science 10+: pass DM+2 Advancement; fail lose all Benefits this term",
                }
            elif selected == "sabotage":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Sabotaged Clan Researcher]")
                )
                auto_applied.append("Gained Enemy [Sabotaged Clan Researcher]")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Stealth"}, {"name": "Deception"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 2}],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -2}],
                    "prompt": "Sabotage rival — roll Stealth or Deception 8+: pass DM+2 Advancement; fail SOC−2",
                }
            else:  # nothing
                character.associates.append(
                    Associate(kind="rival", description="Rival [Competing Clan Researcher]")
                )
                auto_applied.append("Did nothing — Rival [Competing Clan Researcher]")
                character.log("Scientist event 9: did nothing, rival gained")
                character.pending_career_mishap_choice = None

        elif choice_id == "event_ge_warrior_battle":
            # ge_warrior event 5: choose skill, then roll it 8+
            sn, spec = _split_skill_speciality(selected)
            msg = character.add_skill(sn, level=1, speciality=spec)
            auto_applied.append(msg)
            character.pending_career_mishap_choice = {
                "type": "skill_check",
                "skills": [{"name": selected}],
                "target": 8,
                "on_nat2": [],
                "on_pass": [{"type": "pending_choice", "id": "event_ge_warrior_battle_reward",
                             "prompt": "Victory! Choose your reward:",
                             "options": [
                                 {"id": "soc",     "label": "SOC +1"},
                                 {"id": "benefit", "label": "DM+2 to next Benefit roll"},
                             ]}],
                "on_fail": [{"type": "dm_advancement", "amount": -2}],
                "prompt": f"Roll {selected} 8+: pass SOC+1 or DM+2 Benefit; fail DM−2 Advancement",
            }

        elif choice_id == "event_ge_warrior_battle_reward":
            # ge_warrior event 5 (pass reward): SOC+1 or DM+2 benefit
            if selected == "soc":
                old = character.characteristics.SOC
                character.characteristics.set("SOC", old + 1)
                auto_applied.append(f"SOC {old}→{old+1} (+1)")
                character.log("Battle event reward: SOC+1")
            else:
                character.dm_next_benefit += 2
                auto_applied.append("DM+2 to next Benefit roll")
                character.log("Battle event reward: DM+2 benefit")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_ge_officer_duel":
            # officer duel: refuse (1D SOC loss) or accept (Melee 8+; pass DM+2 Adv [+ extras]; fail forfeit benefit)
            if selected == "refuse":
                r1d = dice.roll("1D")
                old_soc = character.characteristics.SOC
                new_soc = max(0, old_soc - r1d.total)
                character.characteristics.set("SOC", new_soc)
                auto_applied.append(f"Refused duel — SOC {old_soc}→{new_soc} (−{r1d.total})")
                character.log(f"Officer duel: refused, SOC −{r1d.total}")
                character.pending_career_mishap_choice = None
            else:
                extra_on_pass = pending.get("extra_on_pass", [])
                pass_note = "; gain Melee (Natural) 1" if extra_on_pass else ""
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Melee"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 2}] + extra_on_pass,
                    "on_fail": [{"type": "forfeit_benefit"}],
                    "prompt": f"Accepted duel — roll Melee 8+: pass DM+2 Advancement{pass_note}; fail forfeit Benefit roll",
                }

        elif choice_id == "noble_ev9_enemy":
            # noble ev9: choose enemy type (jealous relative vs unhappy subject) + auto DM+2 advancement
            desc = "Enemy [Jealous Relative]" if selected == "relative" else "Enemy [Unhappy Subject]"
            character.associates.append(Associate(kind="enemy", description=desc))
            character.dm_next_advancement += 2
            auto_applied.append(f"Gained {desc}; DM+2 to next Advancement roll")
            character.log(f"Noble ev9: gained {desc}, DM+2 advancement")
            character.pending_career_mishap_choice = None

        elif choice_id == "vargr_loner_patron":
            # vargr_loner ev3: accept (DM+4 qual + Contact) or decline
            if selected == "accept":
                character.dm_next_qualification += 4
                character.associates.append(Associate(kind="contact", description="Contact [Patron]"))
                auto_applied.append("Accepted job — DM+4 to next Qualification roll; gained Contact [Patron]")
                character.log("Loner ev3: accepted patron job, qual DM+4, Contact added")
            else:
                auto_applied.append("Declined patron's offer — no effect")
                character.log("Loner ev3: declined patron offer")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_skill_or_stat":
            # Generic: choose one skill from list OR a stat boost (e.g. "Admin 1 / Investigate 1 / SOC+1")
            stat = pending.get("stat", "SOC")
            stat_amount = pending.get("stat_amount", 1)
            if selected == stat:
                old = character.characteristics.get(stat)
                character.characteristics.set(stat, old + stat_amount)
                auto_applied.append(f"{stat} {old}→{old + stat_amount} (+{stat_amount})")
                character.log(f"Event skill_or_stat: {stat} +{stat_amount}")
            else:
                sn, spec = _split_skill_speciality(selected)
                msg = character.add_skill(sn, level=1, speciality=spec)
                auto_applied.append(msg)
            character.pending_career_mishap_choice = None

        elif choice_id == "event_aslan_envoy_fight":
            # aslan_envoy ev3: flee (SOC−1) or fight (Diplomat/Investigate/Stealth 8+)
            if selected == "flee":
                old = character.characteristics.SOC
                character.characteristics.set("SOC", max(0, old - 1))
                auto_applied.append(f"Fled — SOC {old}→{max(0, old-1)} (−1)")
                character.log("Envoy ev3: fled, SOC−1")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Diplomat"}, {"name": "Investigate"}, {"name": "Stealth"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 2}],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1},
                                {"type": "dm_advancement", "amount": -2}],
                    "prompt": "Stay and fight — roll Diplomat, Investigate or Stealth 8+: pass DM+2 Advancement; fail SOC−1 + DM−2 Advancement",
                }

        elif choice_id == "event_aslan_envoy_duel":
            # aslan_envoy ev9: refuse (SOC−2) or challenge (Melee Natural 9+)
            if selected == "refuse":
                old = character.characteristics.SOC
                character.characteristics.set("SOC", max(0, old - 2))
                auto_applied.append(f"Refused — SOC {old}→{max(0, old-2)} (−2)")
                character.log("Envoy ev9: refused insult, SOC−2")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Melee (natural)"}],
                    "target": 9,
                    "on_nat2": [],
                    "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1},
                                {"type": "dm_advancement", "amount": 2}],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -2},
                                {"type": "dm_advancement", "amount": -2}],
                    "prompt": "Challenge to a duel — roll Melee (Natural) 9+: pass SOC+1 + DM+2 Advancement; fail SOC−2 + DM−2 Advancement",
                }

        elif choice_id == "event_aslan_envoy_conspiracy":
            # aslan_envoy ev10: refuse (Enemy) or accept (Deception/Persuade 8+; fail mishap; pass 4-way)
            if selected == "refuse":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Upper-Clan Conspiracy]")
                )
                auto_applied.append("Refused conspiracy — gained Enemy [Upper-Clan Conspiracy]")
                character.log("Envoy ev10: refused, enemy gained")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Deception"}, {"name": "Persuade"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "pending_choice", "id": "event_aslan_conspiracy_reward",
                                 "prompt": "Conspiracy succeeded — choose your reward:",
                                 "options": [
                                     {"id": "Deception", "label": "Deception 1"},
                                     {"id": "Persuade",  "label": "Persuade 1"},
                                     {"id": "SOC",       "label": "SOC +1"},
                                     {"id": "TER",       "label": "TER +1"},
                                 ]}],
                    "on_fail": [{"type": "trigger_disaster_mishap", "career_continues": False}],
                    "prompt": "Joined conspiracy — roll Deception or Persuade 8+: pass choose reward; fail roll on Mishap table (career ends)",
                }

        elif choice_id == "event_aslan_conspiracy_reward":
            # 4-way: Deception 1 / Persuade 1 / SOC+1 / TER+1
            if selected in ("Deception", "Persuade"):
                msg = character.add_skill(selected, level=1)
                auto_applied.append(msg)
                character.log(f"Conspiracy reward: {selected} 1")
            elif selected == "SOC":
                old = character.characteristics.SOC
                character.characteristics.set("SOC", old + 1)
                auto_applied.append(f"SOC {old}→{old+1} (+1)")
                character.log("Conspiracy reward: SOC+1")
            elif selected == "TER":
                old = character.extra_characteristics.get("TER", 0)
                character.extra_characteristics["TER"] = old + 1
                auto_applied.append(f"TER {old}→{old+1} (+1)")
                character.log("Conspiracy reward: TER+1")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_aslan_redemption":
            # aslan_outcast ev11 / ge_landless_one ev11: accept/decline redemption
            if selected == "accept":
                character.dm_next_qualification += 99
                # Restore SOC to pre-outcast value (stored when SOC was first capped to 2)
                restore_soc = character.pre_outcast_soc if character.pre_outcast_soc > 0 else None
                if restore_soc is not None:
                    old_soc = character.characteristics.SOC
                    character.characteristics.set("SOC", restore_soc)
                    auto_applied.append(f"SOC restored {old_soc}→{restore_soc} (pre-outcast value)")
                    character.log(f"Redemption: SOC restored to pre-outcast {restore_soc}")
                else:
                    auto_applied.append("SOC not restored — pre-outcast SOC unknown (no disgrace entry recorded)")
                    character.log("Redemption: pre_outcast_soc not recorded, SOC unchanged")
                character.associates.append(
                    Associate(kind="contact", description="Contact [Clan Elder — Debt of Redemption]")
                )
                auto_applied.append("Gained Contact [Clan Elder — Debt of Redemption]; DM+99 to next Qualification roll")
                character.log("Redemption: accepted, qual DM+99, Contact added")
            else:
                auto_applied.append("Redemption declined — no effect")
                character.log("Redemption: declined")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_aslan_smuggle":
            # aslan_space_officer/spacer/ge_fleet_officer ev4: decline or accept smuggling
            if selected == "decline":
                auto_applied.append("Declined to smuggle — no effect")
                character.log("Smuggle ev4: declined")
                character.pending_career_mishap_choice = None
            else:
                skills = pending.get("skills", [{"name": "Deception"}])
                target = pending.get("target", 8)
                benefit_count = pending.get("benefit_count", 3)
                benefit_dice = pending.get("benefit_dice", "")   # e.g. "1D" for fleet_officer
                fail_soc_cap = pending.get("fail_soc_cap", 0)    # 2 if ejected to SOC 2, else 0
                fail_dm_adv = pending.get("fail_dm_adv", 0)      # e.g. -6 for spacer
                fail_eject = pending.get("fail_eject", False)    # True = career ends
                fail_career_choice = pending.get("fail_career_choice", False)  # True = ge_forced_career_choice
                skill_labels = " or ".join(s["name"] for s in skills)

                on_pass_effects: list[dict] = []
                if benefit_dice:
                    br = dice.roll(benefit_dice)
                    benefit_count = br.total
                    auto_applied.append(f"Smuggle dice: {benefit_dice}={benefit_count} Benefit rolls")
                on_pass_effects.append({"type": "extra_benefit", "amount": benefit_count})

                on_fail_effects: list[dict] = []
                if fail_dm_adv:
                    on_fail_effects.append({"type": "dm_advancement", "amount": fail_dm_adv})
                if fail_soc_cap:
                    on_fail_effects.append({"type": "stat_cap", "stat": "SOC", "cap": fail_soc_cap})
                if fail_eject:
                    on_fail_effects.append({"type": "force_career_end"})
                if fail_career_choice:
                    on_fail_effects.append({"type": "pending_choice",
                                            "id": "ge_forced_career_choice",
                                            "prompt": "Ejected — choose your next career:",
                                            "options": [
                                                {"id": "landless_one", "label": "Landless One"},
                                                {"id": "outlaw",       "label": "Outlaw"},
                                            ]})

                fail_parts = []
                if fail_soc_cap:
                    fail_parts.append(f"SOC→{fail_soc_cap}")
                if fail_eject:
                    fail_parts.append("career ended")
                if fail_career_choice:
                    fail_parts.append("choose Landless One or Outlaw next")
                if fail_dm_adv:
                    fail_parts.append(f"DM{fail_dm_adv} Advancement")
                fail_str = "; ".join(fail_parts) or "no effect"

                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": skills,
                    "target": target,
                    "on_nat2": [],
                    "on_pass": on_pass_effects,
                    "on_fail": on_fail_effects,
                    "prompt": f"Smuggling run — roll {skill_labels} {target}+: pass {benefit_count} Benefit rolls; fail: {fail_str}",
                }

        elif choice_id == "event_aslan_heroism_or_prudence":
            # aslan_spacer ev9 / ge_fleet ev9: heroism (stat 9+ avoid injury + DM+2) or prudence (Stealth 8+, avoid SOC-1)
            heroism_stat = pending.get("heroism_stat", "END")
            if selected == "heroism":
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": heroism_stat, "is_stat": True}],
                    "target": 9,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 2}],
                    "on_fail": [{"type": "injury"}],
                    "prompt": f"Heroism — roll {heroism_stat} 9+: pass DM+2 Advancement; fail roll on Injury table",
                }
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Stealth"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
                    "prompt": "Prudence — roll Stealth 8+: pass nothing; fail SOC−1",
                }

        elif choice_id == "event_ge_officer_merc":
            # ge_warrior_officer event 12: skill_choice then check then reward
            sn, spec = _split_skill_speciality(selected)
            msg = character.add_skill(sn, level=1, speciality=spec)
            auto_applied.append(msg)
            character.pending_career_mishap_choice = {
                "type": "skill_check",
                "skills": [{"name": selected}],
                "target": 8,
                "on_nat2": [],
                "on_pass": [{"type": "pending_choice", "id": "event_ge_warrior_battle_reward",
                             "prompt": "Mercenary victory! Choose reward:",
                             "options": [
                                 {"id": "soc",     "label": "SOC +1"},
                                 {"id": "benefit", "label": "DM+2 to next Advancement roll"},
                             ]}],
                "on_fail": [],
                "prompt": f"Roll {selected} 8+: pass SOC+1 or DM+2 Advancement; fail nothing",
            }

        # ── Vargr new handlers ────────────────────────────────────────────────

        elif choice_id == "event_stat_or_dm":
            # Generic: choose between a stat boost and a DM to a roll (or auto_advance)
            stat = pending.get("stat", "SOC")
            stat_amount = pending.get("stat_amount", 1)
            dm_field = pending.get("dm_field", "advancement")
            dm_amount = pending.get("dm_amount", 1)
            if selected == stat:
                old = character.characteristics.get(stat)
                character.characteristics.set(stat, old + stat_amount)
                auto_applied.append(f"{stat} {old}→{old+stat_amount} (+{stat_amount})")
                character.log(f"Event stat_or_dm: {stat} +{stat_amount}")
            elif selected == "auto":
                if pending.get("stat_check_promote"):
                    # Roll SOC 8+ for promotion
                    soc_dm = dice.characteristic_dm(character.characteristics.get("SOC"))
                    r2d = dice.roll("2D", modifier=soc_dm)
                    if r2d.total >= 8:
                        character.dm_next_advancement += 12
                        auto_applied.append(f"SOC 8+ check passed (2D{soc_dm:+d}={r2d.total}) — automatic promotion")
                        character.log("Event: SOC 8+ for pack leader promotion — passed")
                    else:
                        auto_applied.append(f"SOC 8+ check failed (2D{soc_dm:+d}={r2d.total}) — no promotion")
                        character.log("Event: SOC 8+ for pack leader promotion — failed")
                else:
                    character.dm_next_advancement += 12
                    auto_applied.append("Automatic promotion (DM+12 to Advancement roll)")
                    character.log("Event stat_or_dm: auto advance")
            elif dm_field == "benefit":
                character.dm_next_benefit += dm_amount
                auto_applied.append(f"DM+{dm_amount} to next Benefit roll")
                character.log(f"Event stat_or_dm: dm_benefit +{dm_amount}")
            elif dm_field == "advancement":
                character.dm_next_advancement += dm_amount
                auto_applied.append(f"DM+{dm_amount} to next Advancement roll")
                character.log(f"Event stat_or_dm: dm_advancement +{dm_amount}")
            else:
                auto_applied.append("No additional effect")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_loner_stat_choice":
            # vargr_loner event 10 pass: choose STR, DEX or END +1
            if selected in ("STR", "DEX", "END"):
                old = character.characteristics.get(selected)
                character.characteristics.set(selected, old + 1)
                auto_applied.append(f"{selected} {old}→{old+1} (+1)")
                character.log(f"Loner event 10: {selected}+1")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_emissary_negot":
            # vargr_emissary event 3: cut losses (SOC-1) or roll Broker/Diplomat/Persuade 10+
            if selected == "cut":
                old_soc = character.characteristics.SOC
                character.characteristics.set("SOC", max(0, old_soc - 1))
                auto_applied.append(f"Cut losses — SOC {old_soc}→{max(0, old_soc-1)} (−1)")
                character.log("Emissary event 3: cut losses, SOC-1")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Broker"}, {"name": "Diplomat"}, {"name": "Persuade"}],
                    "target": 10,
                    "on_nat2": [],
                    "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1},
                                {"type": "dm_advancement", "amount": 2}],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1},
                                {"type": "forfeit_benefit"},
                                {"type": "dm_advancement", "amount": -2}],
                    "prompt": "Roll Broker, Diplomat or Persuade 10+: pass SOC+1+DM+2 Adv; fail SOC−1+forfeit benefit+DM−2 Adv",
                }

        elif choice_id == "event_benefit_or_dm4":
            # vargr_emissary event 11: extra benefit roll or DM+4 advancement
            if selected == "benefit":
                character.pending_benefit_rolls += 1
                auto_applied.append("Gained 1 extra Benefit roll")
                character.log("Emissary event 11: extra benefit roll")
            else:
                dm = pending.get("dm_amount", 4)
                character.dm_next_advancement += dm
                auto_applied.append(f"DM+{dm} to next Advancement roll")
                character.log(f"Emissary event 11: DM+{dm} advancement")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_citizen_scandal":
            # vargr_citizen event 8: profit (Deception 8+: pass DM+2+DM+1 benefit+SOC-1+skill/contact;
            #                                        fail SOC-1+DM-2 surv) or don't
            if selected == "profit":
                old_soc = character.characteristics.SOC
                character.characteristics.set("SOC", max(0, old_soc - 1))
                auto_applied.append(f"Chose to profit — SOC {old_soc}→{max(0, old_soc-1)} (−1)")
                character.dm_next_advancement += 2
                auto_applied.append("DM+2 to next Advancement roll")
                character.dm_next_benefit += 1
                auto_applied.append("DM+1 to next Benefit roll")
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Streetwise", "Deception"],
                    "prompt": "Gain a skill or criminal Contact — choose Streetwise 1, Deception 1:",
                    "_add_contact_option": True,
                }
                # Simpler: just give a skill_choice; contact is "or" so we do skill_choice
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Streetwise", "Deception", "Contact [Criminal]"],
                    "prompt": "Choose Streetwise 1, Deception 1, or a criminal Contact:",
                }
                character.log("Citizen event 8: profited, SOC-1, DM+2 adv, DM+1 benefit, skill/contact choice")
            else:
                auto_applied.append("Did not profit — no effect")
                character.log("Citizen event 8: did not profit")
                character.pending_career_mishap_choice = None

        elif choice_id == "event_emissary_switch":
            # vargr_emissary event 9: accept deal (benefit + rival) or refuse (ally + DM+2 survival)
            if selected == "accept":
                character.pending_benefit_rolls += 1
                auto_applied.append("Accepted deal — gained 1 Benefit roll")
                character.associates.append(
                    Associate(kind="rival", description="Rival [Previous Employer]")
                )
                auto_applied.append("Gained Rival [Previous Employer]")
                character.log("Emissary event 9: accepted deal, benefit, rival")
            else:
                character.associates.append(
                    Associate(kind="ally", description="Ally [Current Employer]")
                )
                auto_applied.append("Refused deal — gained Ally [Current Employer]")
                character.dm_next_survival += 2
                auto_applied.append("DM+2 to next Survival roll")
                character.log("Emissary event 9: refused deal, ally, DM+2 survival")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_law_profit":
            # vargr_law_enforcement event 8: profit (Deception 8+) or don't
            if selected == "profit":
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Deception"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "extra_benefit", "amount": 1}],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1},
                                {"type": "dm_survival", "amount": -4}],
                    "prompt": "Profit from illegal goods — roll Deception 8+: pass 1 Benefit; fail SOC−1 + DM−4 Survival",
                }
            else:
                auto_applied.append("Did not profit — no effect")
                character.log("Law enforcement event 8: did not profit")
                character.pending_career_mishap_choice = None

        elif choice_id == "event_loner_corsair":
            # vargr_loner event 6: boarded (no value). If SOC 6+: auto-qualify Corsair; else injury
            # Actually the event auto-rolls SOC 6+ already — we present the result-dependent choice
            # Re-reading: "Roll SOC 6+. If you succeed, the Corsairs offer you a position in their
            # band and you automatically qualify for the Corsair career."
            # So this is a pending_choice presenting the auto-roll result as a choice: join or refuse
            if selected == "join":
                auto_applied.append("Joined corsair band — automatic qualification for Vargr Corsair career")
                character.log("Loner event 6: joined corsair band, auto-qualify noted")
            else:
                auto_applied.append("Refused corsair offer — no effect")
                character.log("Loner event 6: refused corsair offer")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_merchant_smuggle":
            # vargr_merchant event 3: accept (Deception 8+: pass benefit+1; fail SOC-1) or refuse (enemy)
            if selected == "accept":
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Deception"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_benefit", "amount": 1},
                                {"type": "extra_benefit", "amount": 1}],
                    "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
                    "prompt": "Smuggle — roll Deception 8+: pass Benefit roll (DM+1); fail SOC−1 + arrested",
                }
            else:
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Smuggling Contact — refused]")
                )
                auto_applied.append("Refused deal — gained Enemy [Smuggling Contact]")
                character.log("Merchant event 3: refused smuggling, enemy")
                character.pending_career_mishap_choice = None

        # ── Zhodani new event handlers ─────────────────────────────────────────

        elif choice_id == "event_army_guard_transfer":
            # zhodani_army event 5: leave and auto-qualify Guard, or stay
            if selected == "transfer":
                character.force_career_end = True
                character.pending_transfer_career_id = "zhodani_guard"
                auto_applied.append("Left Army — will auto-qualify for Zhodani Guard next term (no Qualification roll).")
                character.log("Army event 5: force career end, auto-qualify zhodani_guard")
            else:
                auto_applied.append("Stayed in Army — no transfer")
                character.log("Army event 5: stayed in Army")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_guard_tp_transfer":
            # zhodani_guard event 5: leave and auto-qualify Thought Police, or stay
            if selected == "transfer":
                character.force_career_end = True
                character.pending_transfer_career_id = "zhodani_agent"
                auto_applied.append("Left Guard — will auto-qualify for Thought Police (Agent) next term (no Qualification roll).")
                character.log("Guard event 5: force career end, auto-qualify thought police")
            else:
                auto_applied.append("Stayed in Guard — no transfer")
                character.log("Guard event 5: stayed in Guard")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_entertainer_controversial":
            # zhodani_entertainer event 3: refuse (nothing) or accept (Art/Persuade 8+)
            if selected == "refuse":
                auto_applied.append("Refused the controversial event — no effect")
                character.log("Entertainer event 3: refused")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Art"}, {"name": "Persuade"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "extra_benefit", "amount": 1}],
                    "on_fail": [{"type": "trigger_disaster_mishap"}],
                    "prompt": "Controversial event — roll Art or Persuade 8+: pass extra Benefit; fail roll on Mishap table",
                }

        elif choice_id == "event_zhodani_entertainer_counsel":
            # zhodani_entertainer event 11: refuse (DM+2 adv) or accept/expose (Art/Persuade 8+)
            if selected == "support":
                character.dm_next_advancement += 2
                auto_applied.append("Supported leader — DM+2 to next Advancement roll")
                character.log("Entertainer event 11: supported leader, DM+2 advancement")
                character.pending_career_mishap_choice = None
            else:  # expose
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Exposed Council Leader]")
                )
                auto_applied.append("Chose to expose leader — gained Enemy [Exposed Council Leader]")
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Art"}, {"name": "Persuade"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "auto_advance"}],
                    "on_fail": [{"type": "free_skill_choice",
                                 "prompt": "Increase any skill you already have by one level:"},
                                {"type": "trigger_disaster_mishap"}],
                    "prompt": "Expose leader — roll Art or Persuade 8+: pass auto-promotion; fail increase a skill + roll on Mishaps",
                }

        elif choice_id == "event_govt_conspiracy":
            # zhodani_government event 9: refuse (enemy) or accept (Diplomat/Persuade 8+)
            if selected == "refuse":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Noble Conspiracy]")
                )
                auto_applied.append("Refused — gained Enemy [Noble Conspiracy]")
                character.log("Government event 9: refused, enemy")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Diplomat"}, {"name": "Persuade"}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "skill_choice",
                                 "options": ["Carouse", "Persuade", "Tactics"]}],
                    "on_fail": [{"type": "trigger_disaster_mishap"}],
                    "prompt": "Join conspiracy — roll Diplomat or Persuade 8+: pass skill choice; fail roll on Mishaps",
                }

        elif choice_id == "event_guard_rescue":
            # zhodani_guard event 9: refuse (nothing) or accept (Survival/END 8+)
            if selected == "refuse":
                auto_applied.append("Refused volunteer mission — no effect")
                character.log("Guard event 9: refused")
                character.pending_career_mishap_choice = None
            else:
                character.pending_career_mishap_choice = {
                    "type": "skill_check",
                    "skills": [{"name": "Survival"}, {"name": "END", "is_stat": True}],
                    "target": 8,
                    "on_nat2": [],
                    "on_pass": [{"type": "dm_advancement", "amount": 2},
                                {"type": "extra_benefit", "amount": 1}],
                    "on_fail": [{"type": "injury"}],
                    "prompt": "Volunteer rescue mission — roll Survival or END 8+: pass DM+2 Adv + extra Benefit; fail injury",
                }

        elif choice_id == "event_guard_report":
            # zhodani_guard event 10: report CO (DM+2 adv) or protect CO (ally)
            if selected == "report":
                character.dm_next_advancement += 2
                auto_applied.append("Reported commanding officer — DM+2 to next Advancement roll")
                character.log("Guard event 10: reported CO, DM+2 advancement")
            else:
                character.associates.append(
                    Associate(kind="ally", description="Ally [Commanding Officer — protected]")
                )
                auto_applied.append("Protected commander — gained Ally [Commanding Officer]")
                character.log("Guard event 10: protected CO, ally")
            character.pending_career_mishap_choice = None

        elif choice_id == "event_zhodani_merchant_drafted":
            # zhodani_merchant event 3: leave merchant + auto-qualify Zhodani Navy at same rank
            current_rank = character.current_term.rank if character.current_term else 0
            character.force_career_end = True
            character.pending_transfer_career_id = "zhodani_navy"
            character.pending_transfer_rank = current_rank
            auto_applied.append(
                f"Government drafted your ship — must leave Merchant career. "
                f"Auto-qualifies for Zhodani Navy next term at Rank {current_rank}."
            )
            character.log(
                f"Merchant event 3: drafted, leaving merchant, auto-qualify Zhodani Navy at rank {current_rank}"
            )
            character.pending_career_mishap_choice = None

        elif choice_id == "event_scholar_conscience":
            # zhodani_scholar event 3: accept (benefit + 2 Science skills + D3 enemies) or refuse (ally)
            if selected == "accept":
                character.pending_benefit_rolls += 1
                auto_applied.append("Accepted research — gained 1 extra Benefit roll")
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": [],
                    "prompt": "Gain one level in any Science skill (first of two):",
                }
                # After resolving, another Science choice is needed — handled via a note
                auto_applied.append("Will gain one level in each of two Science skills — choose first now")
                r_enemies = (dice.roll("1D").total + 1) // 2  # D3
                for _ in range(r_enemies):
                    character.associates.append(
                        Associate(kind="enemy", description="Enemy [Ethics Committee / Rival Researcher]")
                    )
                auto_applied.append(f"Gained {r_enemies}× Enemy [Ethics Committee / Rival Researcher]")
                character.log(f"Scholar event 3: accepted, +benefit, {r_enemies} enemies, science skills pending")
            else:
                character.associates.append(
                    Associate(kind="ally", description="Ally [Grateful Subject / Ethics Advocate]")
                )
                auto_applied.append("Refused — gained Ally [Grateful Subject / Ethics Advocate]")
                character.log("Scholar event 3: refused, ally")
                character.pending_career_mishap_choice = None

        # ── Droyne pending choices ────────────────────────────────────────────

        elif choice_id == "droyne_take_streetwise":
            if selected == "yes":
                msg = character.add_skill("Streetwise", level=1)
                auto_applied.append(f"Took Streetwise 1 (Black Skill): {msg}")
                character.log("Droyne mishap: took Streetwise 1 (Black Skill)")
            else:
                auto_applied.append("Declined Streetwise — no Black Skill taken")
                character.log("Droyne mishap: declined Streetwise (Black Skill)")
            character.pending_career_mishap_choice = None

        elif choice_id in ("droyne_worker_sacrifice", "droyne_warrior_sacrifice", "droyne_tech_sacrifice"):
            if selected == "correct":
                for _stat in ("STR", "DEX", "END"):
                    _old = character.characteristics.get(_stat) or 0
                    character.characteristics.set(_stat, _old - 1)
                    auto_applied.append(f"{_stat} {_old}→{_old - 1} (−1)")
                character.log(f"{choice_id}: behaved correctly — STR/DEX/END each −1; continuation check remains")
            else:
                character.force_career_end = True
                auto_applied.append("Behaved incorrectly — ejected from Oytrip")
                character.log(f"{choice_id}: behaved incorrectly — ejected")
            character.pending_career_mishap_choice = None

        elif choice_id in ("droyne_worker_black_or_eject", "droyne_tech_black_or_eject"):
            if selected == "obey":
                _black_skills = ["Carouse", "Deception", "Gambler", "Persuade", "Streetwise"]
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": _black_skills,
                    "prompt": "Choose a Black Skill to gain at level 1 (you are diminished by knowing it):",
                }
                auto_applied.append("Obeying Leader — choose a Black Skill below")
                character.log(f"Droyne event ({choice_id}): chose to obey — Black Skill choice pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }
            else:
                character.force_career_end = True
                auto_applied.append("Refused Leader's orders — ejected from Oytrip")
                character.log(f"Droyne event ({choice_id}): refused — ejected")
                character.pending_career_mishap_choice = None

        elif choice_id == "droyne_worker_idea":
            if selected == "dare":
                _skill_dm = 0
                for _sk in character.skills:
                    if _sk.name == "Appeal" and _sk.speciality is None:
                        _skill_dm = _sk.level
                        break
                _r = dice.roll("2D", modifier=_skill_dm)
                _term = character.current_term
                if _r.total >= 8:
                    if _term is not None:
                        _old_rank = _term.rank
                        _term.rank = min(_term.rank + 1, 6)
                        auto_applied.append(f"Appeal 8+ passed (2D{_skill_dm:+d}={_r.total}) — rank {_old_rank}→{_term.rank} (+1)")
                    character.log(f"Worker idea: Appeal passed ({_r.total}), rank+1")
                else:
                    if _term is not None:
                        _old_rank = _term.rank
                        _term.rank = max(0, _term.rank - 1)
                        auto_applied.append(f"Appeal 8+ failed (2D{_skill_dm:+d}={_r.total}) — rank {_old_rank}→{_term.rank} (−1)")
                    character.log(f"Worker idea: Appeal failed ({_r.total}), rank-1")
                character.pending_career_mishap_choice = None
            else:  # quiet
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Profession", "Caste"],
                    "prompt": "Kept quiet — gain Profession or Caste 1:",
                }
                auto_applied.append("Kept quiet — choose Profession or Caste 1 below")
                character.log("Worker idea: kept quiet — skill choice pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }

        elif choice_id == "droyne_drone_sacrifice":
            if selected == "risk":
                for _stat in ("STR", "DEX", "END"):
                    _old = character.characteristics.get(_stat) or 0
                    character.characteristics.set(_stat, _old - 1)
                    auto_applied.append(f"{_stat} {_old}→{_old - 1} (−1)")
                character.log("Drone mishap: took risks — STR/DEX/END each −1")
            else:  # shirk
                _term = character.current_term
                if _term is not None:
                    _old_rank = _term.rank
                    _term.rank = max(0, _term.rank - 1)
                    auto_applied.append(f"Shirked — rank {_old_rank}→{_term.rank} (−1)")
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Oytrip — shirked sacrifice]")
                )
                auto_applied.append("Gained Enemy [Oytrip — shirked sacrifice]")
                character.log("Drone mishap: shirked — rank-1, Enemy added")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_drone_prediction":
            # Roll Appeal/Prediction/Admin 8+ automatically
            _skill_dm = 0
            for _sk_name in ("Prediction", "Appeal", "Admin"):
                for _sk in character.skills:
                    if _sk.name == _sk_name and _sk.speciality is None:
                        if _sk.level > _skill_dm:
                            _skill_dm = _sk.level
            _r = dice.roll("2D", modifier=_skill_dm)
            if _r.total >= 8:
                auto_applied.append(f"Prediction check passed (2D{_skill_dm:+d}={_r.total}) — no rank change")
                character.log(f"Drone mishap 5: prediction check passed ({_r.total})")
            else:
                _term = character.current_term
                if _term is not None:
                    _old_rank = _term.rank
                    _term.rank = max(0, _term.rank - 1)
                    auto_applied.append(f"Prediction check failed (2D{_skill_dm:+d}={_r.total}) — rank {_old_rank}→{_term.rank} (−1)")
                _msg = character.add_skill("Outsider", level=1)
                auto_applied.append(f"Gained Outsider 1: {_msg}")
                character.log(f"Drone mishap 5: prediction check failed ({_r.total}), rank-1, Outsider 1")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_drone_appeal_pass":
            if selected == "rank":
                _term = character.current_term
                if _term is not None:
                    _old_rank = _term.rank
                    _term.rank = min(_term.rank + 1, 6)
                    auto_applied.append(f"Rank {_old_rank}→{_term.rank} (+1)")
                character.log("Drone event 4: appeal passed — chose rank+1")
            else:  # caste
                _caste_name = character.droyne_caste.capitalize() if character.droyne_caste else "Drone"
                _msg = character.add_skill("Caste", level=1, speciality=_caste_name)
                auto_applied.append(f"Gained Caste ({_caste_name}) 1: {_msg}")
                character.log(f"Drone event 4: appeal passed — chose Caste ({_caste_name}) 1")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_tech_emergency":
            if selected == "hardest":
                _d3_loss = (dice.roll("1D").total + 1) // 2
                _term = character.current_term
                if _term is not None:
                    _old_rank = _term.rank
                    _term.rank = min(_term.rank + 1, 6)
                    auto_applied.append(f"Tried hardest — rank {_old_rank}→{_term.rank} (+1)")
                character.pending_career_mishap_choice = {
                    "type": "stat_choice",
                    "options": ["STR", "DEX", "END"],
                    "amount": -_d3_loss,
                    "prompt": f"Emergency repairs — choose a physical stat to lose D3={_d3_loss} points:",
                }
                auto_applied.append(f"Lose D3={_d3_loss} from a chosen physical stat — choose below")
                character.log(f"Tech mishap 4: tried hardest — rank+1, D3={_d3_loss} stat loss pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }
            else:  # minimum
                _term = character.current_term
                if _term is not None:
                    _old_rank = _term.rank
                    _term.rank = max(0, _term.rank - 1)
                    auto_applied.append(f"Did minimum — rank {_old_rank}→{_term.rank} (−1)")
                character.log("Tech mishap 4: did minimum — rank-1, no injury")
                character.pending_career_mishap_choice = None

        elif choice_id == "droyne_tech_assignment_stat":
            _stat_map = {"fixing": "DEX", "artificer": "EDU", "dreaming": "INT"}
            _stat = _stat_map.get(selected, "INT")
            _old = character.characteristics.get(_stat) or 0
            character.characteristics.set(_stat, _old + 1)
            auto_applied.append(f"{_stat} {_old}→{_old + 1} (+1)")
            character.log(f"Tech event 9: assignment bonus — {_stat}+1")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_sport_attack":
            # Roll Appeal 8+ automatically
            _skill_dm = 0
            for _sk in character.skills:
                if _sk.name == "Appeal" and _sk.speciality is None:
                    _skill_dm = _sk.level
                    break
            _r = dice.roll("2D", modifier=_skill_dm)
            if _r.total >= 8:
                character.pending_career_mishap_choice = {
                    "type": "stat_choice",
                    "options": ["STR", "DEX", "END"],
                    "amount": -1,
                    "prompt": "Appeal passed — fighting ended quickly; choose a physical stat to lose 1 point:",
                }
                auto_applied.append(f"Appeal 8+ passed (2D{_skill_dm:+d}={_r.total}) — choose stat −1 below")
                character.log(f"Sport mishap 1: Appeal passed ({_r.total}), stat_choice pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }
            else:
                for _stat in ("STR", "DEX", "END"):
                    _old = character.characteristics.get(_stat) or 0
                    character.characteristics.set(_stat, _old - 1)
                    auto_applied.append(f"{_stat} {_old}→{_old - 1} (−1)")
                character.log(f"Sport mishap 1: Appeal failed ({_r.total}), STR/DEX/END each −1")
                character.pending_career_mishap_choice = None

        elif choice_id == "droyne_sport_kroyloss":
            if selected == "return":
                _end_val = character.characteristics.get("END") or 0
                _end_dm = dice.characteristic_dm(_end_val)
                _r = dice.roll("2D", modifier=_end_dm)
                if _r.total >= 8:
                    auto_applied.append(f"END 8+ passed (2D{_end_dm:+d}={_r.total}) — welcomed back, no ill effects")
                    character.log(f"Sport mishap 2: return — END check passed ({_r.total})")
                else:
                    for _stat in ("INT", "EDU"):
                        _old = character.characteristics.get(_stat) or 0
                        character.characteristics.set(_stat, _old - 1)
                        auto_applied.append(f"{_stat} {_old}→{_old - 1} (−1)")
                    _old_psi = character.psi
                    character.psi = max(0, _old_psi - 1)
                    auto_applied.append(f"PSI {_old_psi}→{character.psi} (−1)")
                    character.log(f"Sport mishap 2: return — END check failed ({_r.total}), INT/EDU/PSI each −1")
            else:  # adventure
                character.force_career_end = True
                auto_applied.append("Began adventuring outside the Oytrip — career ends now")
                character.log("Sport mishap 2: adventure — career end")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_sport_expose":
            if selected == "expose":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Kroyloss — exposed Leader]")
                )
                auto_applied.append("Gained Enemy [Kroyloss — exposed Leader]")
                _skill_dm = 0
                for _sk in character.skills:
                    if _sk.name == "Appeal" and _sk.speciality is None:
                        _skill_dm = _sk.level
                        break
                _r = dice.roll("2D", modifier=_skill_dm)
                _term = character.current_term
                if _r.total >= 8:
                    if _term is not None:
                        _old_rank = _term.rank
                        _term.rank = min(_term.rank + 1, 6)
                        auto_applied.append(f"Appeal 8+ passed (2D{_skill_dm:+d}={_r.total}) — rank {_old_rank}→{_term.rank} (+1)")
                    character.log(f"Sport mishap 3: expose — Appeal passed ({_r.total}), rank+1")
                else:
                    auto_applied.append(f"Appeal 8+ failed (2D{_skill_dm:+d}={_r.total}) — continuation check required")
                    character.log(f"Sport mishap 3: expose — Appeal failed ({_r.total}), continuation check")
            else:  # failed to deliver
                _term = character.current_term
                if _term is not None:
                    _old_rank = _term.rank
                    _term.rank = max(0, _term.rank - 1)
                    auto_applied.append(f"Failed to deliver in time — rank {_old_rank}→{_term.rank} (−1); continuation check required")
                character.log("Sport mishap 3: failed to deliver — rank-1")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_sport_outsider_rescue":
            # Roll Outsider 8+ automatically (Contact already added by the effect chain)
            _skill_dm = 0
            for _sk in character.skills:
                if _sk.name == "Outsider" and _sk.speciality is None:
                    _skill_dm = _sk.level
                    break
            _r = dice.roll("2D", modifier=_skill_dm)
            if _r.total >= 8:
                auto_applied.append(f"Outsider 8+ passed (2D{_skill_dm:+d}={_r.total}) — no ill effects")
                character.log(f"Sport mishap 5: Outsider check passed ({_r.total})")
            else:
                _term = character.current_term
                if _term is not None:
                    _old_rank = _term.rank
                    _term.rank = max(0, _term.rank - 1)
                    auto_applied.append(f"Outsider 8+ failed (2D{_skill_dm:+d}={_r.total}) — rank {_old_rank}→{_term.rank} (−1)")
                character.log(f"Sport mishap 5: Outsider check failed ({_r.total}), rank-1")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_sport_ancients":
            if selected == "pass":
                _old_psi = character.psi
                character.psi = _old_psi + 1
                auto_applied.append(f"PSI {_old_psi}→{character.psi} (+1)")
                _msg = character.add_skill("Ancients Tech", level=1)
                auto_applied.append(f"Gained Ancients Tech 1: {_msg}")
                character.log("Sport event 11: check passed — PSI+1, Ancients Tech 1")
            elif selected == "psi":
                _old_psi = character.psi
                character.psi = _old_psi + 1
                auto_applied.append(f"PSI {_old_psi}→{character.psi} (+1)")
                character.log("Sport event 11: check failed — chose PSI+1")
            else:  # tech
                _msg = character.add_skill("Ancients Tech", level=1)
                auto_applied.append(f"Gained Ancients Tech 1: {_msg}")
                character.log("Sport event 11: check failed — chose Ancients Tech 1")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_sport_outsider_or_black":
            if selected == "outsider":
                _msg = character.add_skill("Outsider", level=1)
                auto_applied.append(f"Gained Outsider 1: {_msg}")
                character.log("Sport event 9: chose Outsider 1")
                character.pending_career_mishap_choice = None
            else:  # black skill
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Carouse", "Deception", "Gambler", "Persuade", "Streetwise"],
                    "prompt": "Choose a Black Skill to gain at level 1:",
                }
                auto_applied.append("Chose a Black Skill — make your selection below")
                character.log("Sport event 9: chose Black Skill — skill_choice pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }

        elif choice_id == "droyne_leader_attack":
            # Roll Leadership 8+ automatically
            _skill_dm = 0
            for _sk in character.skills:
                if _sk.name == "Leadership" and _sk.speciality is None:
                    _skill_dm = _sk.level
                    break
            _r = dice.roll("2D", modifier=_skill_dm)
            if _r.total >= 8:
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Gun Combat", "Melee", "Tactics"],
                    "prompt": f"Leadership check passed (2D{_skill_dm:+d}={_r.total}) — gain Gun Combat, Melee or Tactics 1:",
                }
                auto_applied.append(f"Leadership 8+ passed (2D{_skill_dm:+d}={_r.total}) — choose a skill below")
                character.log(f"Leader mishap 1: Leadership passed ({_r.total}), skill choice pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }
            else:
                _d3_loss = (dice.roll("1D").total + 1) // 2
                character.pending_career_mishap_choice = {
                    "type": "stat_choice",
                    "options": ["STR", "DEX", "END"],
                    "amount": -_d3_loss,
                    "prompt": f"Leadership failed (2D{_skill_dm:+d}={_r.total}) — lose D3={_d3_loss} from a physical stat; continuation check required:",
                }
                auto_applied.append(f"Leadership 8+ failed (2D{_skill_dm:+d}={_r.total}) — lose D3={_d3_loss} from physical stat; choose stat below")
                character.log(f"Leader mishap 1: Leadership failed ({_r.total}), D3={_d3_loss} stat loss pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }

        elif choice_id == "droyne_leader_worker_concern":
            if selected == "support":
                _msg = character.add_skill("Leadership", level=1)
                auto_applied.append(f"Supported the worker — Leadership 1: {_msg}")
                character.associates.append(
                    Associate(kind="rival", description="Rival [Oytrip Member — disagreed with your support]")
                )
                auto_applied.append("Gained Rival [Oytrip Member]")
                character.log("Leader event 4: supported worker — Leadership 1, Rival added")
            else:  # discipline
                _caste_name = character.droyne_caste.capitalize() if character.droyne_caste else "Leader"
                _msg = character.add_skill("Caste", level=1, speciality=_caste_name)
                auto_applied.append(f"Put them in their place — Caste ({_caste_name}) 1: {_msg}")
                character.associates.append(
                    Associate(kind="ally", description="Ally [Oytrip Member — respects firm leadership]")
                )
                auto_applied.append("Gained Ally [Oytrip Member]")
                character.log("Leader event 4: disciplined — Caste 1, Ally added")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_leader_outsiders":
            if selected == "educate":
                character.force_career_end = True
                character.associates.append(
                    Associate(kind="ally", description="Ally [Outsider — educated by you]")
                )
                auto_applied.append("Chose to educate outsiders — ejected from Oytrip; gained Ally [Outsider]")
                character.log("Leader mishap 4: educated outsiders — ejected, Ally added")
            else:  # punish
                _d3_enemies = (dice.roll("1D").total + 1) // 2
                for _ in range(_d3_enemies):
                    character.associates.append(
                        Associate(kind="enemy", description="Enemy [Outsider — punished]")
                    )
                auto_applied.append(f"Punished outsiders — gained {_d3_enemies}× Enemy [Outsider]")
                character.log(f"Leader mishap 4: punished outsiders — {_d3_enemies} Enemies added")
            character.pending_career_mishap_choice = None

        elif choice_id == "droyne_leader_outsider_visit":
            if selected == "learn":
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": ["Carouse", "Deception", "Gambler", "Persuade", "Streetwise"],
                    "prompt": "Learnt from outsiders — choose a Black Skill to gain at level 1:",
                }
                auto_applied.append("Chose to learn from outsiders — choose a Black Skill below")
                character.log("Leader event 5: learn — Black Skill choice pending")
                return {
                    "applied": auto_applied,
                    "pending_choice": True,
                    "character": character.model_dump(),
                }
            else:  # abstain
                auto_applied.append("Abstained from outsider ways — no effect")
                character.log("Leader event 5: abstained — no effect")
                character.pending_career_mishap_choice = None

        elif choice_id == "droyne_leader_idea_support":
            if selected == "support":
                _msg = character.add_skill("Appeal", level=1)
                auto_applied.append(f"Supported the idea — Appeal 1: {_msg}")
                character.log("Leader event 9: supported idea — Appeal 1")
            else:  # discipline
                _caste_name = character.droyne_caste.capitalize() if character.droyne_caste else "Leader"
                _msg = character.add_skill("Caste", level=1, speciality=_caste_name)
                auto_applied.append(f"Put them in their place — Caste ({_caste_name}) 1: {_msg}")
                character.log("Leader event 9: disciplined — Caste 1")
            character.pending_career_mishap_choice = None

        # ── Hiver pending choices ─────────────────────────────────────────────

        elif choice_id in ("hiver_academic_disheartened", "hiver_generalist_threatened",
                           "hiver_manipulator_disheartened", "hiver_merchant_disheartened"):
            # Roll RES (SOC) check 8+ automatically
            _res_val = character.characteristics.SOC
            _res_dm = dice.characteristic_dm(_res_val)
            _r = dice.roll("2D", modifier=_res_dm)
            _passed = _r.total >= 8
            if _passed:
                _enemy_descs: dict[str, str] = {
                    "hiver_academic_disheartened":    "Enemy [Thwarted Planner — persists in attacking you]",
                    "hiver_generalist_threatened":    "Enemy [Even More Resentful Hiver]",
                    "hiver_manipulator_disheartened": "Enemy [Persistent Opponent]",
                    "hiver_merchant_disheartened":    "Enemy [Discrediting Party]",
                }
                _enemy_desc = _enemy_descs.get(choice_id, "Enemy [Opponent]")
                character.associates.append(Associate(kind="enemy", description=_enemy_desc))
                auto_applied.append(f"RES check passed (2D{_res_dm:+d}={_r.total}) — gained {_enemy_desc}")
                if choice_id == "hiver_manipulator_disheartened":
                    auto_applied.append("Manipulator mishap 2: check passed — you do NOT have to leave career")
                character.log(f"{choice_id}: RES check passed ({_r.total}), Enemy added")
            else:
                # Effect = total − 8 (negative since failed); magnitude = 8 − total
                _effect_mag = max(0, 8 - _r.total)
                if choice_id == "hiver_manipulator_disheartened":
                    # Lose RES (SOC) equal to negative Effect magnitude
                    _old_res = character.characteristics.SOC
                    character.characteristics.set("SOC", max(0, _old_res - _effect_mag))
                    auto_applied.append(
                        f"RES check failed (2D{_res_dm:+d}={_r.total}, effect −{_effect_mag}) "
                        f"— RES {_old_res}→{character.characteristics.SOC} (−{_effect_mag})"
                    )
                    character.log(f"{choice_id}: RES check failed ({_r.total}), RES -{_effect_mag}")
                else:
                    # Lose Benefit rolls equal to negative Effect magnitude
                    _lost = _effect_mag
                    character.pending_benefit_rolls = max(0, character.pending_benefit_rolls - _lost)
                    # If pending_benefit_rolls is depleted, drain from last career's earned rolls
                    _remaining = _lost - min(_lost, character.pending_benefit_rolls)
                    if _remaining > 0 and character.completed_careers:
                        _last = character.completed_careers[-1]
                        _drain = min(_remaining, _last.benefit_rolls_earned)
                        _last.benefit_rolls_earned = max(0, _last.benefit_rolls_earned - _drain)
                    auto_applied.append(
                        f"RES check failed (2D{_res_dm:+d}={_r.total}, effect −{_effect_mag}) "
                        f"— lost {_lost} Benefit roll(s)"
                    )
                    character.log(f"{choice_id}: RES check failed ({_r.total}), -{_lost} benefit rolls")
            character.pending_career_mishap_choice = None

        elif choice_id == "hiver_academic_alien_cash":
            if selected == "cash":
                character.pending_benefit_rolls += 1
                character.associates.append(
                    Associate(kind="rival", description="Rival [From Time Outside Federation]")
                )
                auto_applied.append("Took extra cash benefit roll; gained Rival [From Time Outside Federation]")
                character.log("Academic event 10: took extra cash roll, Rival added")
            else:  # ally_only
                auto_applied.append("Just the Ally — no extra cash roll taken")
                character.log("Academic event 10: ally only, no extra cash")
            character.pending_career_mishap_choice = None

        elif choice_id == "hiver_academic_nest_threat":
            if selected == "science_res":
                _msg = character.add_skill("Science", level=1, speciality="sociology")
                auto_applied.append(f"Gained Science (sociology) 1: {_msg}")
                _old_res = character.characteristics.SOC
                character.characteristics.set("SOC", _old_res + 1)
                auto_applied.append(f"RES {_old_res}→{_old_res + 1} (+1)")
                character.log("Academic event 12: chose Science (sociology) 1 + RES+1")
            else:  # persuade
                _msg = character.add_skill("Persuade", level=1)
                auto_applied.append(f"Gained Persuade 1: {_msg}")
                character.associates.append(Associate(kind="contact", description="Contact [Nest Ally]"))
                auto_applied.append("Gained Contact [Nest Ally]")
                character.log("Academic event 12: chose Persuade 1 + Contact [Nest Ally]")
            character.pending_career_mishap_choice = None

        elif choice_id == "hiver_merchant_big_score":
            if selected == "money":
                _r2d = dice.roll("2D")
                _credits_gained = _r2d.total * 100_000
                character.credits += _credits_gained
                auto_applied.append(
                    f"Took the money — 2D={_r2d.total} × Cr100,000 = Cr{_credits_gained:,} "
                    f"(total Cr{character.credits:,})"
                )
                character.log(f"Merchant event 5: took money, 2D={_r2d.total}, Cr{_credits_gained:,}")
            else:  # credit
                character.dm_permanent_advancement += 1
                character.associates.append(
                    Associate(kind="contact", description="Contact [Business Ally — shared big score]")
                )
                auto_applied.append("Claimed the credit — permanent DM+1 to ALL future Advancement rolls; gained Contact [Business Ally]")
                character.log("Merchant event 5: claimed credit, permanent adv DM+1, Contact added")
            character.pending_career_mishap_choice = None

        elif choice_id == "hiver_merchant_debt":
            if selected == "saved":
                character.associates.append(
                    Associate(kind="contact", description="Contact [Mysterious Benefactor — owe a huge favour]")
                )
                auto_applied.append("Saved by a benefactor — career continues; gained Contact [Mysterious Benefactor]")
                character.log("Merchant mishap 4: saved by benefactor, career continues, Contact added")
            else:  # not_saved
                _r2d = dice.roll("2D")
                _debt = _r2d.total * 1_000_000  # MCr1 per point → credits
                _cash_advance = _debt // 10
                character.medical_debt += _debt
                character.credits += _cash_advance
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Creditor — pursuing you for debt]")
                )
                auto_applied.append(
                    f"Not saved — 2D={_r2d.total}×MCr1 = Cr{_debt:,} debt; "
                    f"received 10% = Cr{_cash_advance:,} advance; gained Enemy [Creditor]"
                )
                character.log(f"Merchant mishap 4: not saved, Cr{_debt:,} debt, Cr{_cash_advance:,} cash, Enemy added")
            character.pending_career_mishap_choice = None

        # ── Psion mishap handlers ─────────────────────────────────────────────

        elif choice_id == "psion_mishap4":
            # Mishap 4: unethical use — accept (enemy + career continues) or refuse (ejected)
            if selected == "accept":
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Unethical Employer]")
                )
                auto_applied.append("Accepted — gained Enemy [Unethical Employer]; career continues (not ejected)")
                if term is not None:
                    term.survived = True
                    term.mishap = None
                character.log("Psion mishap 4: accepted, Enemy gained, career continues")
            else:  # refuse
                auto_applied.append("Refused — left this career")
                character.log("Psion mishap 4: refused, ejected")
            character.pending_career_mishap_choice = None

        elif choice_id == "psion_mishap6":
            # Mishap 6: a former friend turns enemy — pick Ally or Contact to become Enemy
            if selected == "skip":
                # No allies/contacts — just gain an Enemy generically
                character.associates.append(
                    Associate(kind="enemy", description="Enemy [Former Friend — Gift Caused Betrayal]")
                )
                auto_applied.append("No Allies or Contacts — gained generic Enemy [Former Friend]")
                character.log("Psion mishap 6: no associates, generic enemy added")
            else:
                try:
                    idx = int(selected)
                    if 0 <= idx < len(character.associates):
                        old = character.associates[idx]
                        old_desc = old.description or f"{old.kind.title()}"
                        character.associates[idx] = Associate(
                            kind="enemy",
                            description=f"Enemy [Former Friend — Gift Caused Betrayal] (was: {old_desc})"
                        )
                        auto_applied.append(f"'{old_desc}' ({old.kind}) converted to Enemy")
                        character.log(f"Psion mishap 6: converted {old.kind} '{old_desc}' to enemy")
                except (ValueError, IndexError):
                    pass
            character.pending_career_mishap_choice = None

        # ── Psion event choice handlers ───────────────────────────────────────

        elif choice_id == "psion_event3":
            # Event 3: psionic discomfort — pick Contact or Ally to become Rival
            if selected == "skip":
                # No eligible associates — just note it
                auto_applied.append("No Contacts or Allies to convert — no mechanical effect")
                character.log("Psion event 3: no associates to convert")
            else:
                try:
                    idx = int(selected)
                    if 0 <= idx < len(character.associates):
                        old = character.associates[idx]
                        old_desc = old.description or f"{old.kind.title()}"
                        character.associates[idx] = Associate(
                            kind="rival",
                            description=f"Rival [Psionic Discomfort] (was: {old_desc})"
                        )
                        auto_applied.append(f"'{old_desc}' converted to Rival")
                        character.log(f"Psion event 3: {old.kind} '{old_desc}' → Rival")
                except (ValueError, IndexError):
                    pass
            character.pending_career_mishap_choice = None

        elif choice_id == "psion_event5":
            # Event 5: accept (roll PSI 8+) or refuse
            if selected == "accept":
                psi_dm = dice.characteristic_dm(character.psi)
                r = dice.roll("2D", modifier=psi_dm, target=8)
                auto_applied.append(f"Accepted — rolled PSI 8+: 2D{psi_dm:+d} = {r.total}")
                if r.succeeded:
                    # Chain reward choice
                    character.pending_career_mishap_choice = {
                        "type": "pending_choice",
                        "id": "psion_event5_reward",
                        "prompt": f"PSI 8+ succeeded (2D{psi_dm:+d}={r.total}). Choose your reward:",
                        "options": [
                            {"id": "benefit", "label": "Extra Benefit roll"},
                            {"id": "soc", "label": "SOC +1"},
                        ],
                    }
                else:
                    sp_data = rules.species().get(character.species_id or "", {})
                    soc = character.characteristics.get("SOC")
                    character.characteristics.set("SOC", max(0, soc - 1))
                    auto_applied.append(
                        f"PSI 8+ failed — SOC {soc}→{character.characteristics.get('SOC')} (−1)"
                    )
                    character.log(f"Psion event 5: PSI roll failed, SOC {soc}→{character.characteristics.get('SOC')}")
                    character.pending_career_mishap_choice = None
            else:  # refuse
                auto_applied.append("Refused — declined the opportunity")
                character.log("Psion event 5: refused unethical opportunity")
                character.pending_career_mishap_choice = None

        elif choice_id == "psion_event5_reward":
            # Reward after successful PSI 8+ on event 5
            if selected == "benefit":
                character.pending_benefit_rolls += 1
                auto_applied.append("Chose extra Benefit roll — 1 Benefit roll added")
                character.log("Psion event 5 reward: extra benefit roll")
            else:  # soc
                sp_data = rules.species().get(character.species_id or "", {})
                soc = character.characteristics.get("SOC")
                max_soc = _stat_cap(sp_data, "SOC")
                character.characteristics.set("SOC", min(soc + 1, max_soc))
                auto_applied.append(f"Chose SOC +1 — SOC {soc}→{character.characteristics.get('SOC')}")
                character.log(f"Psion event 5 reward: SOC {soc}→{character.characteristics.get('SOC')}")
            character.pending_career_mishap_choice = None

        elif choice_id == "psion_event9":
            # Event 9: Roll EDU 8+ to gain any one skill except JoaT
            edu_dm = dice.characteristic_dm(character.characteristics.get("EDU"))
            r = dice.roll("2D", modifier=edu_dm, target=8)
            auto_applied.append(f"Rolled EDU 8+: 2D{edu_dm:+d} = {r.total}")
            if r.succeeded:
                character.pending_career_mishap_choice = {
                    "type": "free_skill_choice",
                    "prompt": "EDU 8+ passed — gain any one skill (except Jack-of-all-Trades):",
                    "exclude": ["Jack-of-all-Trades"],
                }
                auto_applied.append("EDU 8+ passed — choose any skill")
                character.log(f"Psion event 9: EDU roll succeeded ({r.total}), skill choice pending")
            else:
                auto_applied.append("EDU 8+ failed — no skill gained")
                character.log(f"Psion event 9: EDU roll failed ({r.total})")
                character.pending_career_mishap_choice = None

        elif choice_id == "believer_mishap4":
            # Lose 1 level in Profession (Religion) or Science (Belief)
            if selected == "profession":
                skill_name, spec = "Profession", "Religion"
            else:
                skill_name, spec = "Science", "Belief"
            for sk in character.skills:
                if sk.name == skill_name and (sk.speciality or "").lower() == spec.lower():
                    if sk.level > 0:
                        sk.level -= 1
                        auto_applied.append(f"{skill_name} ({spec}) reduced to {sk.level}")
                    else:
                        auto_applied.append(f"{skill_name} ({spec}) already at 0 — no further reduction")
                    break
            else:
                auto_applied.append(f"{skill_name} ({spec}) not found — no reduction possible")
            character.pending_career_mishap_choice = None

        elif choice_id == "truther_event3":
            if selected == "agree":
                character.pending_benefit_rolls += 1
                auto_applied.append("Agreed — gained 1 extra Benefit roll")
                # Gain 1 level in any Science skill (pending choice)
                sci_specs = rules.skill_specialities().get("Science", [])
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": [f"Science ({s})" for s in sci_specs] + ["Science"],
                    "prompt": "Gain one level in any Science skill:",
                }
                # D3 Enemies
                enemy_count = dice.roll("D3").total
                for _ in range(enemy_count):
                    character.associates.append(Associate(kind="enemy", description="Enemy [Knowledge Exploitation]"))
                auto_applied.append(f"Gained {enemy_count} Enemies")
                character.log(f"Truther event 3: agreed, +1 benefit, Science skill pending, {enemy_count} enemies")
            else:
                auto_applied.append("Declined — no effect")
                character.log("Truther event 3: declined")
                character.pending_career_mishap_choice = None

        elif choice_id == "truther_event5":
            # Choose an Electronics or Science specialty not already possessed
            existing = {(s.name, s.speciality) for s in character.skills}
            el_specs = rules.skill_specialities().get("Electronics", [])
            sci_specs = rules.skill_specialities().get("Science", [])
            options = []
            for sp in el_specs:
                if ("Electronics", sp) not in existing:
                    options.append(f"Electronics ({sp})")
            for sp in sci_specs:
                if ("Science", sp) not in existing:
                    options.append(f"Science ({sp})")
            if not options:
                options = ["Electronics (any)", "Science (any)"]  # fallback
            character.pending_career_mishap_choice = {
                "type": "skill_choice",
                "options": options,
                "prompt": "Choose an Electronics or Science skill you don't already possess (gain at level 1):",
            }
            auto_applied.append("Choose a new Electronics or Science skill")
            character.log("Truther event 5: skill choice pending (new Electronics/Science)")

        elif choice_id == "truther_event9":
            d3_enemies = dice.roll("D3").total
            if selected == "exploit_fol":
                fol_gain = dice.roll("D3").total
                character.extra_characteristics["FOL"] = character.extra_characteristics.get("FOL", 0) + fol_gain
                auto_applied.append(f"FOL +{fol_gain} (now {character.extra_characteristics['FOL']})")
                for _ in range(d3_enemies):
                    character.associates.append(Associate(kind="enemy", description="Enemy [Exploited Opportunity]"))
                auto_applied.append(f"Gained {d3_enemies} Enemies (exploitation)")
                character.log(f"Truther event 9: exploit FOL +{fol_gain}, {d3_enemies} enemies")
            elif selected == "exploit_soc":
                sp_data = rules.species().get(character.species_id or "", {})
                soc = character.characteristics.get("SOC")
                max_soc = _stat_cap(sp_data, "SOC")
                character.characteristics.set("SOC", min(soc + 1, max_soc))
                auto_applied.append(f"SOC {soc}→{character.characteristics.get('SOC')} (+1)")
                for _ in range(d3_enemies):
                    character.associates.append(Associate(kind="enemy", description="Enemy [Exploited Opportunity]"))
                auto_applied.append(f"Gained {d3_enemies} Enemies (exploitation)")
                character.log(f"Truther event 9: exploit SOC +1, {d3_enemies} enemies")
            elif selected == "exploit_skill":
                sci_specs = rules.skill_specialities().get("Science", [])
                el_specs = rules.skill_specialities().get("Electronics", [])
                options = [f"Science ({s})" for s in sci_specs] + [f"Electronics ({s})" for s in el_specs] + ["Medic"]
                character.pending_career_mishap_choice = {
                    "type": "skill_choice",
                    "options": options,
                    "level": 2,   # rulebook: "two levels in any of the following skills"
                    "prompt": "Choose Science/Medic/Electronics specialty to gain 2 levels in:",
                }
                for _ in range(d3_enemies):
                    character.associates.append(Associate(kind="enemy", description="Enemy [Exploited Opportunity]"))
                auto_applied.append(f"Gained {d3_enemies} Enemies; choose skill for +2 levels")
                character.log(f"Truther event 9: exploit skill, {d3_enemies} enemies, skill choice pending")
            else:  # decline
                character.associates.append(Associate(kind="ally", description="Ally [Declined Exploitation]"))
                auto_applied.append("Declined — gained Ally")
                character.log("Truther event 9: declined, ally gained")
                character.pending_career_mishap_choice = None

        elif choice_id == "believer_event6":
            # SOC -D3, D3 benefit rolls, permanent DM+1 benefits
            soc_loss = dice.roll("D3").total
            soc_old = character.characteristics.get("SOC")
            character.characteristics.set("SOC", max(0, soc_old - soc_loss))
            auto_applied.append(f"SOC {soc_old}→{character.characteristics.get('SOC')} (−{soc_loss})")
            benefit_gain = dice.roll("D3").total
            character.pending_benefit_rolls += benefit_gain
            auto_applied.append(f"Gained {benefit_gain} Benefit roll(s)")
            character.permanent_benefit_dm += 1
            auto_applied.append("Permanent DM+1 on all future Benefit rolls")
            character.log(f"Believer event 6: SOC -{soc_loss}, +{benefit_gain} benefits, permanent benefit DM+1")
            character.pending_career_mishap_choice = None

        elif choice_id == "believer_event9":
            if selected == "betray":
                # Leave career + lose all benefits + Cr2D×10000 per benefit roll lost
                lost_rolls = character.pending_benefit_rolls
                character.pending_benefit_rolls = 0
                cash_gain = sum(dice.roll("2D").total * 10000 for _ in range(max(1, lost_rolls)))
                character.credits += cash_gain
                character.force_career_end = True
                character.ejected_by_event = True
                auto_applied.append(f"Betrayed faith — left career, lost {lost_rolls} benefit roll(s), gained Cr{cash_gain:,}")
                character.log(f"Believer event 9: betrayed, lost {lost_rolls} benefits, gained Cr{cash_gain:,}, ejected")
            else:  # loyal
                enemy_count = dice.roll("1D").total
                for _ in range(enemy_count):
                    character.associates.append(Associate(kind="enemy", description="Enemy [Temptation Refused]"))
                auto_applied.append(f"Stayed loyal — gained {enemy_count} Enemies")
                character.log(f"Believer event 9: stayed loyal, {enemy_count} enemies")
            character.pending_career_mishap_choice = None

        elif choice_id == "believer_event10":
            if selected == "agree":
                character.associates.append(Associate(kind="ally", description="Ally [Noble's Household — secret rites]"))
                auto_applied.append("Agreed — gained Ally [Noble's Household]")
                character.associates.append(Associate(kind="rival", description="Rival [Own Faith — disapproves]"))
                auto_applied.append("Gained Rival [Own Faith — disapproves]")
                character.log("Believer event 10: agreed, ally + rival")
            else:
                auto_applied.append("Refused — no effect")
                character.log("Believer event 10: refused")
            character.pending_career_mishap_choice = None

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
            # Use _char_dm so RES→SOC, PSI→psi, REP→reputation all resolve correctly
            skill_dm = _char_dm(character, skill_name)
        else:
            # Parse the skill name — may be "Skill (Speciality)" or plain "Skill"
            _sk_base, _sk_spec = _split_skill_speciality(skill_name)
            _sk_spec_lower = _sk_spec.lower() if _sk_spec else None
            for s in character.skills:
                if s.name.lower() != _sk_base.lower():
                    continue
                if _sk_spec_lower:
                    # Speciality check — match stored speciality (case-insensitive)
                    if s.speciality and s.speciality.lower() == _sk_spec_lower:
                        skill_dm = s.level
                        break
                else:
                    # Plain skill name — match base skill (no speciality)
                    if s.speciality is None:
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

        # Apply consequences — clear the skill_check from the pending slot first so that
        # any pending-creating sub_effect (e.g. a chained skill_choice) can actually land.
        character.pending_career_mishap_choice = None
        consequences = on_nat2 if nat2 else (on_pass if passed else on_fail)
        new_pending_set = False
        disaster_mishap_result: Optional[dict] = None
        for sub_effect in consequences:
            if sub_effect.get("type") == "injury":
                # injury must be applied directly — _apply_mishap_effect only does `pass` for it
                inj = apply_injury(character)
                if inj:
                    auto_applied.append(f"Injury: {inj.get('description', 'injured')}")
            elif sub_effect.get("type") == "trigger_disaster_mishap":
                # Call mishap_roll directly so we can capture the full result dict and
                # correctly detect whether it set a new pending choice.
                career_continues = sub_effect.get("career_continues", True)
                try:
                    disaster_mishap_result = mishap_roll(character)
                    if career_continues and term is not None:
                        term.survived = True
                        term.mishap = None
                        auto_applied.append("Rolled on Mishap table — career continues")
                        character.log("Event skill-check fail: triggered mishap roll, career continues")
                    else:
                        character.force_career_end = True
                        character.ejected_by_event = True
                        auto_applied.append("Rolled on Mishap table — career ended")
                        character.log("Event skill-check fail: triggered mishap roll, career ended")
                    # If the mishap itself set a pending choice, preserve it
                    if character.pending_career_mishap_choice is not None:
                        new_pending_set = True
                except Exception as _exc:
                    auto_applied.append(f"Mishap roll (event on_fail) error: {_exc}")
            else:
                msgs, was_pending = _apply_mishap_effect(character, sub_effect, term)
                auto_applied.extend(msgs)
                if was_pending:
                    new_pending_set = True

        # Only clear pending if consequences didn't set a new one
        if not new_pending_set:
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
            "disaster_mishap": disaster_mishap_result,
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


def resolve_career_event_choice(character: "Character", choice_data: dict) -> dict:
    """Resolve a pending career event interactive choice.

    Uses the same effect types as mishap choices but reads/writes
    pending_career_event_choice instead of pending_career_mishap_choice.
    """
    pending = character.pending_career_event_choice
    if pending is None:
        raise ValueError("No pending career event choice to resolve")

    # Temporarily move event choice into mishap slot so we can reuse
    # resolve_career_mishap_choice's full logic
    character.pending_career_mishap_choice = pending
    character.pending_career_event_choice = None

    result = resolve_career_mishap_choice(character, choice_data)

    # If a new pending was created, move it back to event choice slot
    if character.pending_career_mishap_choice is not None:
        character.pending_career_event_choice = character.pending_career_mishap_choice
        character.pending_career_mishap_choice = None

    # Re-serialize AFTER the pending swap so the browser receives the correct
    # state (pending_career_event_choice set, pending_career_mishap_choice None).
    # Without this, resolve_career_mishap_choice's earlier serialization
    # captures the pre-swap state and the follow-up appears on the mishap screen.
    result["character"] = character.model_dump()

    # Explicitly surface pending_event_choice in the response so the JS can
    # render a chained follow-up (e.g. Conf. Navy event 4 "recreation" → skill pick).
    result["pending_event_choice"] = character.pending_career_event_choice

    return result


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


_COMMISSION_CAREER_IDS = {"army", "navy", "marine"}


def commission_roll(character: "Character") -> dict:
    """Attempt a Commission roll (Army, Navy, Marines only).

    RAW MgT 2e p.36:
    - Only eligible if career has a 'commission' key.
    - First term in career: free attempt.
    - Subsequent terms: only if SOC 9+, with DM−1 per term after the first.
    - On success: character becomes Rank 1 officer (term.commissioned = True),
      applies rank-1 officer bonus if defined, and may NOT roll advancement this term.
    - On failure: can still roll for advancement normally.
    """
    term = character.current_term
    if term is None:
        raise ValueError("No active term.")
    career = rules.careers()[term.career_id]
    comm_data = career.get("commission", {})
    if not comm_data:
        raise ValueError(f"{career.get('name', term.career_id)} does not have a commission table.")
    already = term.commissioned or any(
        t.career_id == term.career_id and t.commissioned
        for t in character.term_history
    )
    if already:
        raise ValueError("Already commissioned — officers do not re-roll commission.")

    # Eligibility: first term free; later terms need SOC 9+
    soc = character.characteristics.get("SOC")
    if term.term_number > 1 and soc < 9:
        raise ValueError(
            f"Commission attempt requires SOC 9+ after the first term (your SOC is {soc})."
        )

    char_key = comm_data.get("characteristic", "SOC")
    target = int(comm_data.get("target", 8))
    dm = dice.characteristic_dm(character.characteristics.get(char_key))

    # DM−1 for every term after the first in this career
    term_penalty = -(term.term_number - 1)
    if term_penalty:
        dm += term_penalty

    # Pre-career permanent DMs (School of Hard Knocks grants DM−2 to first commission)
    pdms = character.pre_career_permanent_dms or {}
    first_comm_dm = int(pdms.get("first_career_commission_dm", 0))
    if first_comm_dm and len(character.completed_careers) == 0:
        dm += first_comm_dm

    # Event/DM bonuses (dm_next_advancement applies to commission per RAW)
    pending_dm = character.dm_next_advancement
    dm += pending_dm
    dm += character.dm_permanent_advancement

    r = dice.roll("2D", modifier=dm, target=target)

    dm_notes: list[str] = [f"{char_key} DM{dice.characteristic_dm(character.characteristics.get(char_key)):+d}"]
    if term_penalty:
        dm_notes.append(f"Term penalty DM{term_penalty:+d}")
    if first_comm_dm:
        dm_notes.append(f"Hard Knocks DM{first_comm_dm:+d}")
    if pending_dm:
        dm_notes.append(f"Pending DM{pending_dm:+d}")
        character.dm_next_advancement = 0  # consumed
    if character.dm_permanent_advancement:
        dm_notes.append(f"Permanent DM{character.dm_permanent_advancement:+d}")

    new_rank_title = None
    rank_bonus_log = None

    if r.succeeded:
        # Commissioned: jump to Rank 1 officer regardless of current enlisted rank
        term.commissioned = True
        term.rank = 1
        new_rank_title = _rank_title(career, term.assignment_id, 1, commissioned=True)
        term.rank_title = new_rank_title
        rank_data = _rank_data(career, term.assignment_id, 1, commissioned=True)
        if rank_data and rank_data.get("bonus"):
            rank_bonus_log = _apply_rank_bonus(character, rank_data["bonus"])
            term.skills_gained.append(f"Commission rank bonus: {rank_data['bonus']}")
        character.log(
            f"Commission ({char_key} {target}+, {', '.join(dm_notes)}): "
            f"2D{dm:+d} = {r.total} — COMMISSIONED as Rank 1"
            + (f" ({new_rank_title})" if new_rank_title else "")
        )
    else:
        character.log(
            f"Commission ({char_key} {target}+, {', '.join(dm_notes)}): "
            f"2D{dm:+d} = {r.total} — FAILED (may still roll advancement)"
        )

    return {
        "roll": r.to_dict(),
        "succeeded": r.succeeded,
        "new_rank": term.rank,
        "new_rank_title": new_rank_title,
        "rank_bonus": rank_bonus_log,
        "dm_notes": dm_notes,
        "character": character.model_dump(),
    }


def _hiver_advancement_roll(character: "Character", career: dict, term) -> dict:
    """Hiver status-table advancement (Adult → Senior → Manipulator).

    Roll 2D + RES DM (RES stored as SOC):
      ≥ 15 → advance to Manipulator (rank 2) if not already
      10–14 → advance to Senior (rank 1) if Adult; no change if already Senior
      ≤ 9  → no advancement this term

    First time reaching Senior/Manipulator: apply the nest-type bonus from
    the species data and set the hiver_senior_bonus_awarded / _manipulator_bonus_awarded
    flags to prevent double-awarding.
    """
    res_dm = dice.characteristic_dm(character.characteristics.SOC)
    perm_dm = character.dm_permanent_advancement  # never consumed
    next_dm = character.dm_next_advancement
    character.dm_next_advancement = 0
    combined_dm = res_dm + perm_dm + next_dm
    r = dice.roll("2D", modifier=combined_dm)
    total = r.total
    current_rank = term.rank

    # Status thresholds from species data (fallback to standard values)
    sp_data = rules.species().get(character.species_id or "", {})
    adv_table = sp_data.get("hiver_advancement_table", {})
    senior_min   = int(adv_table.get("senior_min", 10))
    manipulator_min = int(adv_table.get("manipulator_min", 15))

    # Determine new status
    if total >= manipulator_min and current_rank < 2:
        new_rank = 2
    elif total >= senior_min and current_rank < 1:
        new_rank = 1
    else:
        new_rank = current_rank  # No advancement

    advanced = new_rank > current_rank
    rank_bonus_log = None

    if advanced:
        term.rank = new_rank
        term.advanced = True
        term.rank_title = _rank_title(career, term.assignment_id, new_rank)
        rank_data = _rank_data(career, term.assignment_id, new_rank)
        if rank_data and rank_data.get("bonus"):
            rank_bonus_log = _apply_rank_bonus(character, rank_data["bonus"])
            term.skills_gained.append(f"Rank bonus: {rank_data['bonus']}")
            character.log(f"  Rank bonus: {rank_bonus_log}")

        # First-time Senior bonus
        if new_rank == 1 and not character.hiver_senior_bonus_awarded:
            character.hiver_senior_bonus_awarded = True
            nest = character.hiver_nest_type or "generalist"
            nest_benefits = sp_data.get("hiver_nest_benefits", {})
            senior_bonus = nest_benefits.get(nest, {}).get("senior_bonus", "")
            if senior_bonus:
                bonus_log = _apply_rank_bonus(character, senior_bonus)
                character.log(f"Hiver Senior bonus ({nest} nest): {senior_bonus} — {bonus_log}")
                if rank_bonus_log:
                    rank_bonus_log += f"; Senior nest bonus: {bonus_log}"
                else:
                    rank_bonus_log = f"Senior nest bonus: {bonus_log}"

        # First-time Manipulator bonus
        if new_rank == 2 and not character.hiver_manipulator_bonus_awarded:
            character.hiver_manipulator_bonus_awarded = True
            nest = character.hiver_nest_type or "generalist"
            nest_benefits = sp_data.get("hiver_nest_benefits", {})
            manip_bonus = nest_benefits.get(nest, {}).get("manipulator_bonus", "")
            if manip_bonus:
                bonus_log = _apply_rank_bonus(character, manip_bonus)
                character.log(f"Hiver Manipulator bonus ({nest} nest): {manip_bonus} — {bonus_log}")
                if rank_bonus_log:
                    rank_bonus_log += f"; Manipulator nest bonus: {bonus_log}"
                else:
                    rank_bonus_log = f"Manipulator nest bonus: {bonus_log}"

        status_name = {0: "Adult", 1: "Senior", 2: "Manipulator"}.get(new_rank, f"Rank {new_rank}")
        _perm_note = f" + permanent DM{perm_dm:+d}" if perm_dm else ""
        character.log(
            f"Hiver advancement [2D+RES{res_dm:+d}{_perm_note}={total}]: "
            f"ADVANCED to {status_name} (rank {new_rank})"
        )
    else:
        term.advanced = False
        _perm_note = f" + permanent DM{perm_dm:+d}" if perm_dm else ""
        if current_rank >= 2:
            character.log(
                f"Hiver advancement [2D+RES{res_dm:+d}{_perm_note}={total}]: already Manipulator — no further advancement."
            )
        else:
            status_name = {0: "Adult", 1: "Senior"}.get(current_rank, f"Rank {current_rank}")
            threshold = senior_min if current_rank == 0 else manipulator_min
            character.log(
                f"Hiver advancement [2D+RES{res_dm:+d}{_perm_note}={total}]: "
                f"no advancement (needed {threshold}+ to advance from {status_name})."
            )

    return {
        "roll": r.to_dict(),
        "advanced": advanced,
        "new_rank": term.rank,
        "new_rank_title": term.rank_title,
        "rank_bonus": rank_bonus_log,
        "forced_from_career": False,
        "monitor_dm": 0,
        "monitor_rank_up": False,
        "monitor_rank": character.solsec_monitor_rank,
        "advancement_skill_roll": advanced,
        "character": character.model_dump(),
        "hiver_status_total": total,
    }


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

    # ── Hiver careers: status-table advancement ───────────────────────────────
    if career.get("hiver_career"):
        return _hiver_advancement_roll(character, career, term)

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
        adv = assignment.get("advancement")
        cover_dm = 0
        if adv is None:
            return {
                "no_advancement": True,
                "note": f"{career.get('name', 'This career')} has no advancement roll.",
                "character": character.model_dump(),
            }

    char_key = adv["characteristic"]
    target = adv["target"]

    # K'kree Patriarchy-based advancement (SOC rank degree)
    if char_key == "PATRIARCHY":
        patriarchy_level = next(
            (s.level for s in character.skills if s.name == "Patriarchy" and s.speciality is None),
            0
        )
        dm = patriarchy_level + cover_dm
        # Adjust target based on current SOC (higher SOC → harder check)
        soc = character.characteristics.SOC
        if soc <= 3:
            target = 2   # Simple
        elif soc <= 6:
            target = 4   # Easy
        elif soc <= 10:
            target = 6   # Routine
        elif soc == 11:
            # Automatic for Small Family Patriarch
            term.advanced = True
            term.rank += 1
            term.rank_title = _rank_title(career, term.assignment_id, term.rank, commissioned=term.commissioned)
            character.kkree_soc_rank_degree = "rankholder"
            character.log(f"K'kree SOC rank advancement: Automatic (SOC 11, Small Family Patriarch) — now Rankholder.")
            return {
                "roll": {"total": "Auto", "succeeded": True, "natural": 12},
                "advanced": True, "rank": term.rank,
                "new_rank": term.rank,
                "new_rank_title": term.rank_title,
                "rank_bonus": None,
                "forced_from_career": False,
                "monitor_dm": 0,
                "monitor_rank_up": False,
                "monitor_rank": character.solsec_monitor_rank,
                "advancement_skill_roll": True,
                "character": character.model_dump(),
                "note": "Automatic SOC rank advancement — Small Family Patriarch."
            }
        elif soc == 12:
            target = 8   # Average
        elif soc == 13:
            target = 10  # Difficult
        elif soc == 14:
            target = 12  # Very Difficult
        else:  # SOC 15
            target = 14  # Formidable
        char_display = f"Patriarchy (skill {patriarchy_level})"
    else:
        dm = _char_dm(character, char_key) + cover_dm
        char_display = None

    # ── Droyne: Black Skills DM (Carouse/Deception/Gambler/Persuade/Streetwise) ──
    # Highest Black Skill level is subtracted from advancement DM.
    if term.career_id in rules.DROYNE_CAREER_IDS:
        _black_skill_names = {"carouse", "deception", "gambler", "persuade", "streetwise"}
        _highest_black = max(
            (sk.level for sk in character.skills if sk.name.lower() in _black_skill_names),
            default=0
        )
        if _highest_black > 0:
            dm -= _highest_black

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
    dm += character.dm_permanent_advancement
    pending = character.dm_next_advancement
    character.dm_next_advancement = 0
    # dm_permanent_advancement is intentionally NOT zeroed — it applies every roll

    dm += character.permanent_advancement_dm
    # permanent_advancement_dm is intentionally NOT zeroed — it applies every roll

    # SolSec Monitor: DM+1 to advancement in any career except Drifter
    monitor_dm = 0
    if character.solsec_monitor and term.career_id != "drifter":
        monitor_dm = 1
        dm += monitor_dm

    # Zhodani Noble: DM+1 to all advancement rolls
    zhodani_noble_dm = 0
    if character.species_id == "zhodani":
        _zclass = _zhodani_class(character.characteristics.get("SOC") or 0)
        if _zclass == "noble":
            zhodani_noble_dm = 1
            dm += zhodani_noble_dm

    # Zhodani Noble auto-advance: automatically promoted at end of first term in any career.
    # (RAW: "second term if they were drafted" — we use term_number == 1 as first term.)
    zhodani_noble_auto = False
    if (character.species_id == "zhodani"
            and _zhodani_class(character.characteristics.get("SOC") or 0) == "noble"
            and term.term_number == 1
            and not term.advanced):
        zhodani_noble_auto = True

    if zhodani_noble_auto:
        # Fake a succeeded roll for logging purposes; forced_from_career still applies
        r = dice.roll("2D", modifier=dm, target=target)
        r_auto_note = " [Noble auto-advance]"
        term.advanced = True
    else:
        r = dice.roll("2D", modifier=dm, target=target)
        r_auto_note = ""
        term.advanced = bool(r.succeeded)

    monitor_rank_up = False
    rank_bonus_log = None
    if term.advanced:
        # Zhodani Prole/Intendant: career-specific rank cap (read from career JSON).
        _prole_max_rank = career.get("prole_intendant_max_rank")
        if _prole_max_rank is not None and character.species_id == "zhodani":
            _zclass_adv = _zhodani_class(character.characteristics.get("SOC") or 0)
            if _zclass_adv in ("prole", "intendant") and term.rank >= int(_prole_max_rank):
                term.advanced = False
                character.log(
                    f"Zhodani {_zclass_adv.capitalize()} rank cap: "
                    f"{career.get('name', term.career_id)} rank capped at {_prole_max_rank}."
                )
                r_auto_note += " [rank cap]"

        # Career soc_cap: SOC cannot rise above this value via rank bonuses in this career.
        _soc_cap = career.get("soc_cap")
        if _soc_cap is not None:
            current_soc = character.characteristics.get("SOC") or 0
            if current_soc > int(_soc_cap):
                character.characteristics.set("SOC", int(_soc_cap))
                character.log(
                    f"SOC capped at {_soc_cap} (career soc_cap). Was {current_soc}."
                )
    if term.advanced:
        term.rank += 1
        term.rank_title = _rank_title(career, term.assignment_id, term.rank, commissioned=term.commissioned)
        rank_data = _rank_data(career, term.assignment_id, term.rank, commissioned=term.commissioned)
        if rank_data and rank_data.get("bonus"):
            bonus = rank_data["bonus"]
            rank_bonus_log = _apply_rank_bonus(character, bonus)
            term.skills_gained.append(f"Rank bonus: {bonus}")
            character.log(f"  Rank bonus: {rank_bonus_log}")
        # Storm Knight Knight Commander By Rank progression.
        # Rank 6 = Storm Lord/Grand Navigator/Darkblade — reaching or passing it grants KC By Rank.
        # Passing advancement when already at rank 6 grants Knight Grand Cross.
        if term.career_id in _STORM_KNIGHT_IDS_HONOURS:
            if term.rank > 6:
                # Was already Storm Lord (rank 6), passed another advancement
                term.rank = 6  # clamp — rank never exceeds 6
                if not character.knight_commander_by_rank:
                    _kc_msgs = _grant_knight_commander_by_rank(character)
                    for _m in _kc_msgs:
                        rank_bonus_log = (_m if rank_bonus_log is None
                                          else f"{rank_bonus_log} | {_m}")
                elif not character.knight_grand_cross:
                    _kc_msgs = _grant_knight_grand_cross(character)
                    for _m in _kc_msgs:
                        rank_bonus_log = (_m if rank_bonus_log is None
                                          else f"{rank_bonus_log} | {_m}")
                else:
                    character.log("Storm Knight rank 6 already at maximum progression — no further honour.")
                    term.advanced = False  # nothing actually changed
            elif term.rank == 6 and not character.knight_commander_by_rank:
                # Just promoted to rank 6 for the first time
                _kc_msgs = _grant_knight_commander_by_rank(character)
                for _m in _kc_msgs:
                    rank_bonus_log = (_m if rank_bonus_log is None
                                      else f"{rank_bonus_log} | {_m}")

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

    # K'kree: track SOC rank degree advancement on success
    if char_key == "PATRIARCHY" and term.advanced:
        if character.kkree_soc_rank_degree == "servant_of_rankholder":
            character.kkree_soc_rank_degree = "kinsman_of_rankholder"
            character.log("K'kree SOC rank degree: advanced to Kinsman-of-Rankholder.")
        elif character.kkree_soc_rank_degree == "kinsman_of_rankholder":
            character.kkree_soc_rank_degree = "rankholder"
            character.log("K'kree SOC rank degree: advanced to Rankholder.")
        else:
            character.log("K'kree SOC rank degree: already Rankholder — no further advancement this way.")
            term.advanced = False

    _char_key_display = char_display if char_key == "PATRIARCHY" else char_key
    monitor_note = f" [Monitor DM+{monitor_dm}]" if monitor_dm else ""
    noble_note = f" [Noble DM+{zhodani_noble_dm}]" if zhodani_noble_dm else ""
    promoted_str = (
        "Noble AUTO-ADVANCE to rank " + str(term.rank) + (" — " + term.rank_title if term.rank_title else "")
        if zhodani_noble_auto and term.advanced
        else "PROMOTED to rank " + str(term.rank) + (" — " + term.rank_title if term.rank_title else "")
        if term.advanced
        else "no promotion"
    )
    msg = (
        f"Advancement ({_char_key_display} {target}+{'+' + str(pending) if pending else ''}){cover_note}{monitor_note}{noble_note}{r_auto_note}: "
        f"2D{dm:+d} = {r.total} "
        f"[{promoted_str}]"
    )
    character.log(msg)

    parole_info = None
    if term.career_id == "prisoner":
        # RAW Prisoner career: the generic forced-leave / natural-12 rules DO NOT
        # apply. Instead the character leaves only if the advancement roll is
        # GREATER than their Parole Threshold; otherwise the parole is denied and
        # they must serve another term. Mishaps cannot eject them either.
        threshold = character.parole_threshold if character.parole_threshold is not None else 12
        paroled = r.total > threshold
        forced_from_career = paroled          # released → leave the career
        must_continue_career = not paroled     # denied → must continue
        term.parole_released = paroled
        parole_info = {"released": paroled, "threshold": threshold, "roll": r.total}
        character.log(
            f"Parole check: advancement roll {r.total} vs Parole Threshold {threshold} — "
            + ("GREATER → sentence ends, released from prison."
               if paroled else "not greater → parole denied, must serve another term.")
        )
    else:
        # RAW: if the Advancement roll result is EQUAL TO OR LESS THAN the number
        # of terms served in this career, the character must leave the career at
        # the end of this term. (Noble auto-advance is exempt — roll always counts.)
        forced_from_career = (not zhodani_noble_auto) and (r.total <= term.term_number)
        if forced_from_career:
            character.log(
                f"Advancement roll {r.total} is equal to or less than terms served "
                f"({term.term_number}) — must leave this career at end of term."
            )

        # RAW: a natural 12 on the Advancement roll means the character MUST
        # continue in this career next term — "too valuable to lose". This
        # overrides a forced-leave (can't be strong-armed into staying AND out).
        must_continue_career = (r.raw_total == 12)
        if must_continue_career:
            forced_from_career = False
            character.log(
                "Advancement roll: natural 12 — too valuable to lose; "
                "must continue in this career next term."
            )

    # Persist on the term so every decision surface (advancement view, session
    # restore, the term-complete screen) agrees, not just the transient roll.
    term.forced_from_career = forced_from_career
    term.must_continue_career = must_continue_career

    # Imperial Guard: advancement required. If not promoted, must leave.
    if term.career_id == "imperial_guard" and not term.advanced:
        character.imperial_guard_must_leave = True
        character.log(
            "Imperial Guard: advancement required but not achieved — "
            "must leave the Guard at end of this term (return to Army/Marines or muster out)."
        )

    return {
        "roll": r.to_dict(),
        "advanced": term.advanced,
        "new_rank": term.rank,
        "new_rank_title": term.rank_title,
        "rank_bonus": rank_bonus_log,
        "monitor_dm": monitor_dm,
        "monitor_rank_up": monitor_rank_up,
        "monitor_rank": character.solsec_monitor_rank,
        "forced_from_career": forced_from_career,
        "must_continue_career": must_continue_career,
        "parole": parole_info,
        "advancement_skill_roll": term.advanced,
        "zhodani_noble_auto": zhodani_noble_auto,
        "zhodani_noble_dm": zhodani_noble_dm,
        "knight_commander_by_rank": character.knight_commander_by_rank,
        "knight_grand_cross": character.knight_grand_cross,
        "imperial_guard_must_leave": character.imperial_guard_must_leave,
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
    # Gate: INT threshold (Droyne advanced tables — requires_int: 6)
    if table.get("requires_int") and character.characteristics.INT < table["requires_int"]:
        raise ValueError(f"This table requires INT {table['requires_int']}+")
    # Gate: PSI threshold (Droyne Leader trusted_leader table — requires_psi: 8)
    if table.get("requires_psi") and character.psi < table["requires_psi"]:
        raise ValueError(f"This table requires PSI {table['requires_psi']}+")
    # Gate: RES (Resolve/SOC) threshold (Hiver active tables — requires_res: 7/10)
    if table.get("requires_res") and character.characteristics.SOC < table["requires_res"]:
        raise ValueError(f"This table requires RES {table['requires_res']}+")

    r = dice.roll("1D")
    result = table.get(str(r.total), "(Unknown)")

    # ── Droyne: "Caste" result → add Caste with the character's caste as speciality ──
    if result.strip().lower() == "caste" and character.droyne_caste:
        caste_name = character.droyne_caste.capitalize()
        applied = character.add_skill("Caste", level=1, speciality=caste_name)
        term.skills_gained.append(f"{table.get('name', table_key)}: Caste ({caste_name})")
        character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: Caste ({caste_name}) — {applied}")
        return {"roll": r.to_dict(), "result": f"Caste ({caste_name})", "applied": applied,
                "character": character.model_dump()}

    # ── "Any psionic skill" → set pending skill choice from psionic skills list ──
    if result.strip().lower() == "any psionic skill":
        _PSIONIC_SKILLS = ["Awareness", "Clairvoyance", "Telekinesis", "Telepathy", "Teleportation"]
        character.pending_career_event_choice = {
            "type": "skill_choice",
            "options": _PSIONIC_SKILLS,
            "prompt": "Choose a psionic skill to gain at level 1:",
        }
        term.skills_gained.append(f"{table.get('name', table_key)}: Any psionic skill")
        character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: Any psionic skill — choose below")
        return {"roll": r.to_dict(), "result": result, "applied": "Psionic skill choice pending",
                "pending_choice": True, "character": character.model_dump()}

    # ── "X or Y" skill table result → player picks one option ──
    # MUST come before the "(any)" check so "Pilot (any) or Flyer (any)" is treated
    # as a choice between two options, not mistaken for a single "Pilot (any) or Flyer" base skill.
    # Gender-conditional variants ("X (if male) or Y (if female)") are handled
    # by _apply_skill_result, so only catch plain "X or Y" here.
    # Only split on " or " that appears OUTSIDE parentheses (depth tracking), so
    # "Profession (Miner or Belter)" is NOT split into ["Profession (Miner", "Belter)"].
    _or_outside_parens_pos = -1
    if " or " in result and not re.search(r"\(if (male|female)\)", result, re.IGNORECASE):
        _depth = 0
        for _ci, _ch in enumerate(result):
            if _ch == "(":
                _depth += 1
            elif _ch == ")":
                _depth -= 1
            elif _depth == 0 and result[_ci: _ci + 4] == " or ":
                _or_outside_parens_pos = _ci
                break
    if _or_outside_parens_pos >= 0:
        # Collect ALL top-level " or " options, not just the first split.
        # Bug: splitting only at the first " or " made the second option carry the entire
        # remainder string (e.g. "Clairvoyance or Telekinesis or Awareness or Teleportation"),
        # which then got stored as a literal skill name if the player chose it.
        _or_parts = []
        _cur_start = 0
        _or_depth = 0
        for _ci2, _ch2 in enumerate(result):
            if _ch2 == "(":
                _or_depth += 1
            elif _ch2 == ")":
                _or_depth -= 1
            elif _or_depth == 0 and result[_ci2: _ci2 + 4] == " or ":
                _or_parts.append(result[_cur_start:_ci2].strip())
                _cur_start = _ci2 + 4
        _or_parts.append(result[_cur_start:].strip())
        _or_parts = [p for p in _or_parts if p]
        _prompt_str = " / ".join(_or_parts)
        character.pending_career_event_choice = {
            "type": "skill_choice",
            "options": _or_parts,
            "prompt": f"Choose one: {_prompt_str}:",
        }
        term.skills_gained.append(f"{table.get('name', table_key)}: {result}")
        character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: {result} — choice pending")
        return {"roll": r.to_dict(), "result": result, "applied": "Choice pending",
                "pending_choice": True, "character": character.model_dump()}

    # ── "Skill (A or B)" — speciality choice inside parens ──
    # e.g. "Profession (Miner or Belter)" — the " or " is inside parens, so the
    # top-level OR check above didn't fire. Present as a choice between specialities.
    _spec_or_m = re.match(r"^(.+?)\s*\((.+?\s+or\s+.+?)\)\s*$", result.strip(), re.IGNORECASE)
    if _spec_or_m and " or " not in _spec_or_m.group(1):  # guard: base skill has no top-level " or "
        _so_base = _spec_or_m.group(1).strip()
        _so_parts = [s.strip() for s in _spec_or_m.group(2).split(" or ") if s.strip()]
        character.pending_career_event_choice = {
            "type": "skill_choice",
            "options": [f"{_so_base} ({s})" for s in _so_parts],
            "prompt": f"Choose a {_so_base} speciality to gain at level 1:",
        }
        term.skills_gained.append(f"{table.get('name', table_key)}: {result}")
        character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: {result} — speciality choice pending")
        return {"roll": r.to_dict(), "result": result, "applied": "Speciality choice pending",
                "pending_choice": True, "character": character.model_dump()}

    # ── "SkillName (any)" or "Any Science" → player picks a speciality ──
    _any_spec_m = re.match(r"^(.+?)\s*\(any\)$", result.strip(), re.IGNORECASE)
    _any_skill_m = re.match(r"^Any\s+(.+)$", result.strip(), re.IGNORECASE) if not _any_spec_m else None
    if _any_spec_m or _any_skill_m:
        _base_skill = (_any_spec_m.group(1) if _any_spec_m else _any_skill_m.group(1)).strip()
        # Look up known specialities from skills.json
        _skills_specs = rules.skill_specialities()  # returns dict name→[specs]
        _spec_list = _skills_specs.get(_base_skill, [])
        if not _spec_list:
            # Fallback: add base skill at level 1 if no specialities known
            applied = _apply_skill_result(character, _base_skill)
            term.skills_gained.append(f"{table.get('name', table_key)}: {result} (added {_base_skill})")
            character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: {result} — {applied}")
            return {"roll": r.to_dict(), "result": result, "applied": applied,
                    "character": character.model_dump()}
        character.pending_career_event_choice = {
            "type": "skill_choice",
            "options": [f"{_base_skill} ({s})" for s in _spec_list],
            "prompt": f"Choose a {_base_skill} speciality to gain at level 1:",
        }
        term.skills_gained.append(f"{table.get('name', table_key)}: {result}")
        character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: {result} — speciality choice pending")
        return {"roll": r.to_dict(), "result": result, "applied": f"{_base_skill} speciality choice pending",
                "pending_choice": True, "character": character.model_dump()}

    # ── Bare skill name that has specialities → treat as "(any)" and prompt ──
    # e.g. career table entry "Gun Combat" should trigger a speciality picker,
    # not silently add "Gun Combat 1" with no spec.
    _bare_name, _bare_spec = _split_skill_speciality(result.strip())
    if not _bare_spec and not re.match(r"^(STR|DEX|END|INT|EDU|SOC|PSI|RES)\s*[+-]\d+", result.strip(), re.IGNORECASE):
        _bare_specs = rules.skill_specialities().get(_bare_name, [])
        if _bare_specs:
            character.pending_career_event_choice = {
                "type": "skill_choice",
                "options": [f"{_bare_name} ({s})" for s in _bare_specs],
                "prompt": f"Choose a {_bare_name} speciality to gain at level 1:",
            }
            term.skills_gained.append(f"{table.get('name', table_key)}: {result}")
            character.log(f"Skill roll ({table.get('name', table_key)}) [1D={r.total}]: {result} — speciality choice pending")
            return {"roll": r.to_dict(), "result": result, "applied": f"{_bare_name} speciality choice pending",
                    "pending_choice": True, "character": character.model_dump()}

    # The result is a specific skill, characteristic bonus, or associate grant.
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
#   • First access: roll SOC 10+ to establish a supply.
#     Natural 2 on this roll → must take Prisoner career this term.
#     Failure → cannot access this term; try again next term.
#   • Once active: supply continues automatically (no re-roll each term).
#   • While active: add anagathics_terms_used as a POSITIVE DM to aging rolls.
#   • Two survival checks required each term; either failing → Mishap.
#     (The two checks represent the risk of acquiring the drugs mid-career.)
#   • Cost: 1D × Cr25,000 per term → added to medical debt each term,
#     paid out of the character's eventual muster-out cash benefits.
#   • Stopping: immediately roll on the Aging table.


def attempt_anagathics(character: "Character") -> dict:
    """Obtain or continue anagathics at the start of a career term.

    RAW (MgT 2e p.47):
      • SOC 10+ is only rolled the FIRST time a character seeks anagathics.
        Once the supply chain is established it continues automatically.
      • Natural 2 on the initial access roll → forced into Prisoner career.
      • Cost: 1D × Cr25,000 per term, added to medical debt each term
        (paid out of eventual muster-out cash benefits).
      • Active penalty: two survival checks per term; either failing = Mishap.

    Returns:
        roll          – the SOC roll result (None if already active; no roll needed)
        succeeded     – True if active (either auto-continued or newly passed)
        nat2_prison   – True if natural 2 was rolled (first access only)
        already_active– True when no roll was needed (continuing use)
        cost_this_term– Cr cost rolled for this term (0 if failed/nat2)
        character     – updated character dict
    """
    if character.phase != "career":
        raise ValueError("Anagathics can only be attempted during the career phase.")

    # RAW: Travellers may not use anagathics while imprisoned.
    if character.current_term is not None and character.current_term.career_id == "prisoner":
        raise ValueError("Travellers may not use anagathics in prison.")

    # Species-level anagathics block (e.g. Hivers).
    _sp_data = rules.species().get(character.species_id or "", {})
    if _sp_data.get("no_anagathics"):
        raise ValueError(
            f"{_sp_data.get('name', 'This species')} cannot use anagathics."
        )

    already_active = character.anagathics_active

    # ── Already active: no SOC re-roll — supply is established ──────────────
    if already_active:
        character.anagathics_terms_used += 1
        cost_die = dice.roll("1D")
        cost_this_term = cost_die.total * 25_000
        character.anagathics_pending_cost += cost_this_term
        character.log(
            f"Anagathics continuing (term {character.anagathics_terms_used}): "
            f"+{character.anagathics_terms_used} DM on aging roll this term. "
            f"Cost: Cr{cost_this_term:,} (1D={cost_die.total} × Cr25,000) "
            "added to medical debt (paid at muster-out)."
        )
        return {
            "roll": None,
            "succeeded": True,
            "nat2_prison": False,
            "already_active": True,
            "cost_this_term": cost_this_term,
            "character": character.model_dump(),
        }

    # ── First access: roll SOC 10+ ───────────────────────────────────────────
    soc = character.characteristics.get("SOC")
    dm = dice.characteristic_dm(soc)
    r = dice.roll("2D", modifier=dm, target=10)

    nat2_prison = r.raw_total == 2
    succeeded = bool(r.succeeded) and not nat2_prison
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
        character.anagathics_active = True
        character.anagathics_terms_used += 1
        cost_die = dice.roll("1D")
        cost_this_term = cost_die.total * 25_000
        character.anagathics_pending_cost += cost_this_term
        character.log(
            f"Anagathics access roll SOC [2D{dm:+d}={r.total}]: SUCCESS. "
            f"Supply established (term {character.anagathics_terms_used}). "
            f"+{character.anagathics_terms_used} DM on aging roll this term. "
            f"Cost: Cr{cost_this_term:,} (1D={cost_die.total} × Cr25,000) added to medical debt."
        )
    else:
        character.anagathics_active = False
        character.log(
            f"Anagathics access roll SOC [2D{dm:+d}={r.total}]: FAILED "
            f"(need 10+). Unable to obtain a supply this term."
        )

    return {
        "roll": r.to_dict(),
        "succeeded": succeeded,
        "nat2_prison": nat2_prison,
        "already_active": False,
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
# Full-time Solomani military careers are ineligible for the parallel Home Forces Reserves.
_HOME_FORCES_BARRED_CAREERS = frozenset({
    "drifter",
    "solomani_marine",
    "confederation_army",
    "confederation_navy",
})
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


def _home_forces_component_for(character: "Character", career_id: Optional[str] = None) -> str:
    """Return 'naval' or 'groundside' based on current career/assignment and history."""
    term = character.current_term
    effective_career = term.career_id if term else career_id
    effective_assignment = term.assignment_id if term else None
    if effective_career == "merchant" and effective_assignment in _NAVAL_MERCHANT_ASSIGNMENTS:
        return "naval"
    # Ex-Navy (any previous Navy career) may join naval component
    navy_career_ids = {"navy", "confederation_navy"}
    has_navy = any(c.career_id in navy_career_ids for c in character.completed_careers)
    if has_navy:
        return "naval"
    return "groundside"


def _home_forces_eligible(character: "Character", career_id: Optional[str] = None) -> bool:
    """Return True if the character may (re-)enroll in Home Forces Reserves.

    career_id may be supplied when current_term is not yet set (i.e. the player
    has just qualified for a career but hasn't called start_term yet).
    """
    if character.society_id != "solomani_confederation":
        return False
    # Use current_term if active; fall back to supplied career_id
    effective_career = None
    effective_assignment = None
    if character.current_term is not None:
        effective_career = character.current_term.career_id
        effective_assignment = character.current_term.assignment_id
    elif career_id is not None:
        effective_career = career_id
    else:
        return False
    if effective_career in _HOME_FORCES_BARRED_CAREERS:
        return False
    if effective_career == "rogue" and (effective_assignment or "") == "pirate":
        return False
    if effective_career == "solsec":
        return False
    return True


def enroll_home_forces(character: "Character", career_id: Optional[str] = None) -> dict:
    """Enroll the character in Home Forces Reserves and roll on the training table.

    career_id may be supplied when the character has qualified for a career but
    hasn't yet called start_term (so current_term is still None).

    Eligibility is checked here; raises ValueError if ineligible.
    The training roll is made once at initial enlistment only.
    """
    if character.phase != "career":
        raise ValueError("Home Forces enrollment is only available during the career phase.")
    if not _home_forces_eligible(character, career_id=career_id):
        eligible_reason = (
            "Not a Solomani Confederation character." if character.society_id != "solomani_confederation"
            else "Career is barred from Home Forces (full-time Solomani military, Drifter, Rogue/Pirate, or SolSec)."
        )
        raise ValueError(f"Not eligible for Home Forces Reserves — {eligible_reason}")

    component = _home_forces_component_for(character, career_id=career_id)
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


def purchase_solomani_documents(character: "Character") -> dict:
    """Purchase falsified Solomani genetic records (30,000 Cr debt).

    Only available to solomani_mixed characters in the Solomani Confederation.
    While passing status is held the character is treated as Racial Solomani for
    all career qualification purposes:
      - Party Patronage DM (SOC DM) applies to all qualification rolls.
      - Mixed Heritage DM-1/-3 penalties are suppressed.
    Passing status is revoked — and SOC halved — if a natural 2 is rolled on a
    survival check in any military or Party career.
    """
    if character.society_id != "solomani_confederation":
        raise ValueError(
            "Only Solomani Confederation characters can purchase passing documents."
        )
    if character.species_id != "solomani_mixed":
        raise ValueError(
            "Only Mixed Heritage characters require passing documents."
        )
    if character.solomani_passing:
        raise ValueError(
            "Character already holds passing documents."
        )

    cost = 30_000
    character.credits -= cost
    character.solomani_passing = True
    character.log(
        f"Purchased Solomani passing documents — 30,000 Cr debt incurred "
        f"(credits now {character.credits:+,}). "
        f"Character now treated as Racial Solomani for career qualification."
    )
    return {
        "solomani_passing": True,
        "credits": character.credits,
        "character": character.model_dump(),
    }


# ============================================================
# Event effects table (Aslan careers)
# ============================================================

_EVENT_EFFECTS: dict[str, dict[int, list[dict]]] = {
    # ---- Aslan Hierate careers ----
    "aslan_ceremonial": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_ceremonial_secret",
              "prompt": "You uncover an embarrassing secret — trade it for 1D Clan Shares (gain Elder as Enemy) or keep it in reserve?",
              "options": [
                  {"id": "trade", "label": "Trade for 1D Clan Shares (gain Enemy [Clan Elder] when used)"},
                  {"id": "keep",  "label": "Keep in reserve (note: gain Enemy if ever used)"},
              ]}],
        4:  [{"type": "skill_choice", "options": ["Melee (natural)", "Athletics (strength)", "Carouse", "Medic"]}],
        5:  [{"type": "skill_check", "skills": [{"name": "Art"}, {"name": "Investigate"}, {"name": "Persuade"}],
              "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "dm_advancement", "amount": -2}],
              "prompt": "Roll Art, Investigate or Persuade 8+ — pass: DM+2 to next advancement; fail: DM-2"}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_choice", "options": ["Carouse", "Survival", "Admin", "Independence"]}],
        9:  [{"type": "stat", "stat": "TER", "amount": 1},
             {"type": "free_skill_choice", "prompt": "Rise in clan influence — gain any one skill at level 1:"}],
        10: [{"type": "pending_choice", "id": "event_aslan_kinfolk_honour",
              "prompt": "A kinfolk acted dishonourably — cover up (gain Ally) or expose (Melee 8+)?",
              "options": [
                  {"id": "cover",  "label": "Cover up — gain them as an Ally"},
                  {"id": "expose", "label": "Expose them — duel! Roll Melee 8+"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_ter_or_dm4",
              "prompt": "Trusted by the great lords — choose your reward:",
              "options": [
                  {"id": "ter",  "label": "Gain TER +2"},
                  {"id": "dm4",  "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_envoy": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_aslan_envoy_fight",
              "prompt": "Your clan places you in a difficult situation — flee (SOC−1) or stay and fight (Diplomat/Investigate/Stealth 8+)?",
              "options": [
                  {"id": "flee",  "label": "Flee — lose SOC −1"},
                  {"id": "fight", "label": "Fight — roll Diplomat, Investigate or Stealth 8+"},
              ]}],
        4:  [{"type": "skill_choice", "options": ["Animals (training)", "Survival", "Stealth", "Athletics (dexterity)"]}],
        5:  [{"type": "contact", "desc": "Contact [Clan Council Member]"}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_check", "skills": [{"name": "Carouse"}, {"name": "Persuade"}], "target": 8,
              "on_pass": [{"type": "ally", "desc": "Ally [Diplomatic Circles]"}],
              "on_fail": [{"type": "rival", "desc": "Rival [Diplomatic Circles]"}],
              "prompt": "Roll Carouse or Persuade 8+ — pass: Ally; fail: Rival"}],
        9:  [{"type": "pending_choice", "id": "event_aslan_envoy_duel",
              "prompt": "Insulted by a rival clan noble — refuse the challenge (SOC−2) or duel them (Melee (Natural) 9+)?",
              "options": [
                  {"id": "refuse",    "label": "Refuse — lose SOC −2"},
                  {"id": "challenge", "label": "Challenge — roll Melee (Natural) 9+"},
              ]}],
        10: [{"type": "pending_choice", "id": "event_aslan_envoy_conspiracy",
              "prompt": "Offered membership in a clan conspiracy — refuse (gain them as an Enemy) or accept (Deception/Persuade 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — gain Enemy [Conspiracy]"},
                  {"id": "accept", "label": "Accept — roll Deception or Persuade 8+"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_ter_or_dm4",
              "prompt": "Trusted by the great lords — choose your reward:",
              "options": [
                  {"id": "ter",  "label": "Gain TER +2"},
                  {"id": "dm4",  "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_military": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "Recon"}, {"name": "Gun Combat"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "injury"}],
              "prompt": "Roll Recon or Gun Combat 8+ — fail: roll on Injury table"},
             {"type": "skill_choice", "options": ["Stealth", "Medic", "Heavy Weapons", "Leadership"]}],
        4:  [{"type": "skill_choice", "options": ["Streetwise", "Electronics (comms)", "Mechanic"]}],
        5:  [{"type": "skill_choice", "options": ["Carouse", "Streetwise", "Independence", "Survival"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_choice", "options": ["Gun Combat", "Language", "Melee", "Recon", "Survival"]}],
        10: [{"type": "dm_qualification_terms_in_career"}],
        9:  [{"type": "pending_choice", "id": "event_aslan_military_insult",
              "prompt": "An officer insults your courage — duel (Melee Natural 8+) or prove them wrong (1D: 1–3 injured; 4+ SOC+1+DM+4+Rival)?",
              "options": [
                  {"id": "duel",  "label": "Duel them — roll Melee (natural) 8+"},
                  {"id": "prove", "label": "Prove them wrong — roll 1D"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Hero of the clan aids you — choose your reward:",
              "options": [
                  {"id": "skill", "label": "Gain Tactics (military) 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Tactics (military)"}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_military_officer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Stealth", "Heavy Weapons", "Vacc Suit", "Drive"]}],
        8:  [{"type": "skill_choice", "options": ["Gun Combat", "Recon", "Melee (natural)", "Tactics (military)"]}],
        4:  [{"type": "skill_check", "skills": [{"name": "Persuade"}, {"name": "Melee (natural)"}], "target": 8,
              "on_pass": [{"type": "ally", "desc": "Ally [Junior Officer]"}],
              "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1},
                          {"type": "rival", "desc": "Rival [Disobedient Junior Officer]"}],
              "prompt": "Roll Persuade or Melee (natural) 8+ — pass: Ally; fail: SOC-1 + Rival"}],
        5:  [{"type": "skill_choice", "options": ["Carouse", "Streetwise", "Independence", "Survival"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        9:  [{"type": "pending_choice", "id": "event_ransom_or_free",
              "prompt": "You captured an enemy commander — ransom them (TER +2) or free them (gain as Ally)?",
              "options": [
                  {"id": "ransom", "label": "Ransom them — gain TER +2"},
                  {"id": "free",   "label": "Free them — gain as a trusted Ally"},
              ]}],
        10: [{"type": "pending_choice", "id": "event_ge_officer_duel",
              "prompt": "Challenged to a duel by a rival — refuse (lose 1D SOC) or accept (Melee 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — lose 1D SOC"},
                  {"id": "accept", "label": "Accept — roll Melee 8+"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Your deeds are legend — choose your reward:",
              "options": [
                  {"id": "skill", "label": "Gain Tactics (military) 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Tactics (military)"}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_spacer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "Pilot"}, {"name": "Gunner"}, {"name": "Mechanic"}],
              "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "enemy", "desc": "Enemy [Pirate Captain]"},
                          {"type": "forfeit_all_benefits"}],
              "prompt": "Roll Pilot, Gunner or Mechanic 8+ vs pirates — fail: Enemy + lose all Benefits"}],
        4:  [{"type": "pending_choice", "id": "event_aslan_smuggle",
              "prompt": "Opportunity to smuggle illegal goods — decline (no effect) or accept (Deception 8+)?",
              "options": [
                  {"id": "decline", "label": "Decline — no effect"},
                  {"id": "accept",  "label": "Accept — roll Deception 8+: pass 3 Benefit rolls; fail DM−6 Advancement"},
              ],
              "skills": [{"name": "Deception"}], "target": 8,
              "benefit_count": 3, "fail_dm_adv": -6, "fail_eject": False}],
        5:  [{"type": "dm_qualification_terms_in_career"}],
        6:  [{"type": "skill_choice", "options": ["Survival", "Streetwise", "Science", "Tolerance"]}],
        8:  [{"type": "contact", "desc": "Contact [Aslan Colonist]"}],
        9:  [{"type": "pending_choice", "id": "event_aslan_heroism_or_prudence",
              "prompt": "Vicious battles against clan enemies — demonstrate heroism (END 9+) or prudence (Stealth 8+)?",
              "options": [
                  {"id": "heroism",  "label": "Heroism — roll END 9+: pass DM+2 Advancement; fail roll on Injury table"},
                  {"id": "prudence", "label": "Prudence — roll Stealth 8+: pass nothing lost; fail SOC−1"},
              ],
              "heroism_stat": "END"}],
        10: [{"type": "dm_qualification_terms_in_career"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Captain entrusts you with an important duty — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Steward 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Steward"}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_space_officer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "Tactics"}, {"name": "Engineer"}], "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "enemy", "desc": "Enemy [Pirate Captain]"},
                          {"type": "forfeit_all_benefits"}],
              "prompt": "Roll Tactics or Engineer 8+ vs pirates — fail: Enemy + lose all Benefits"}],
        4:  [{"type": "pending_choice", "id": "event_aslan_smuggle",
              "prompt": "Opportunity to smuggle illegal goods — decline (no effect) or accept (Deception 8+)?",
              "options": [
                  {"id": "decline", "label": "Decline — no effect"},
                  {"id": "accept",  "label": "Accept — roll Deception 8+: pass 6 Benefit rolls; fail SOC→2 + career ended"},
              ],
              "skills": [{"name": "Deception"}], "target": 8,
              "benefit_count": 6, "fail_soc_cap": 2, "fail_eject": True}],
        5:  [{"type": "skill_choice", "options": ["Tolerance", "Diplomat", "Language", "Science"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_choice", "options": ["Astrogation", "Electronics (sensors)", "Gunner", "Pilot"]}],
        9:  [{"type": "pending_choice", "id": "event_ransom_or_free",
              "prompt": "You captured an enemy commander — ransom them (TER +2) or free them (gain as Ally)?",
              "options": [
                  {"id": "ransom", "label": "Ransom them — gain TER +2"},
                  {"id": "free",   "label": "Free them — gain as a trusted Ally"},
              ]}],
        10: [{"type": "pending_choice", "id": "event_ge_officer_duel",
              "prompt": "Challenged to a duel by a rival — refuse (lose 1D SOC) or accept (Melee 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — lose 1D SOC"},
                  {"id": "accept", "label": "Accept — roll Melee 8+"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "You befriend an old admiral — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Tactics (naval) 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Tactics (naval)"}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_management": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Melee (natural)"}, {"name": "Stealth"}, {"name": "Gun Combat"}],
              "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Survived the assault — gain any skill at level 1"}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Roll Melee, Stealth or Gun Combat 8+ — pass: gain any skill; fail: Injury"}],
        4:  [{"type": "skill_choice", "options": ["Pilot", "Mechanic", "Electronics", "Drive"]}],
        5:  [{"type": "skill_choice", "options": ["Broker", "Admin", "Persuade"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_choice", "options": ["Broker", "Profession", "Streetwise"]}],
        9:  [{"type": "skill_check", "skills": [{"name": "Diplomat"}, {"name": "Admin"}], "target": 8,
              "on_pass": [{"type": "rival", "desc": "Rival [Foolish Clan Member]"}],
              "on_fail": [{"type": "dm_advancement", "amount": -2}],
              "prompt": "Roll Diplomat or Admin 8+ to fix the damage — pass: Rival [Foolish Clan Member]; fail: DM−2 next advancement"}],
        10: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "contact", "desc": "Contact [Inter-Clan Merchant]"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "You trade with aliens — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Tolerance 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Tolerance"}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_scientist": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Carouse", "Survival", "Streetwise"]}],
        4:  [{"type": "skill_choice", "options": ["Science", "Engineer", "Gunner", "Gun Combat"]}],
        5:  [{"type": "skill", "name": "Tolerance", "level": 1},
             {"type": "contact", "desc": "Contact [Alien Scientist]"}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_choice", "options": ["Admin", "Art", "Science"]}],
        9:  [{"type": "pending_choice", "id": "event_aslan_scientist_rival",
              "prompt": "A rival researcher is close to a breakthrough — research first (Science 10+), sabotage them (Stealth/Deception 8+), or do nothing?",
              "options": [
                  {"id": "research", "label": "Research first — roll Science 10+"},
                  {"id": "sabotage", "label": "Sabotage rival — roll Stealth or Deception 8+"},
                  {"id": "nothing",  "label": "Do nothing — gain a Rival"},
              ]}],
        10: [{"type": "skill_check", "skills": [{"name": "Science"}], "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "dm_advancement", "amount": -2}],
              "prompt": "Rare artefact study — roll Science 8+: pass DM+2 Advancement; fail DM−2 Advancement"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "You study at a great university — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Investigate 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Investigate"}],
        12: [{"type": "auto_advance"}],
    },
    "aslan_wanderer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Survival", "Recon", "Streetwise"]}],
        4:  [{"type": "skill", "name": "Tolerance", "level": 1},
             {"type": "skill_choice", "options": ["Broker", "Diplomat", "Independence"]}],
        5:  [{"type": "skill_check", "skills": [{"name": "Independence"}], "target": 8,
              "on_pass": [{"type": "extra_benefit", "amount": 1}],
              "on_fail": [], "prompt": "Roll Independence 8+ — pass: gain an extra Benefit roll"}],
        6:  [{"type": "contact", "desc": "Contact [Distant Spaceport Trader]"}],
        8:  [{"type": "skill_choice", "options": ["Pilot (spacecraft)", "Gunner (turret)", "Engineer", "Mechanic"]}],
        9:  [{"type": "skill_check", "skills": [{"name": "Carouse"}, {"name": "Streetwise"}], "target": 8,
              "on_pass": [{"type": "ally", "desc": "Ally [Loyal Crew Member]"}],
              "on_fail": [{"type": "forfeit_benefit"},
                          {"type": "enemy", "desc": "Enemy [Thieving New Crew]"}],
              "prompt": "Roll Carouse or Streetwise 8+ for new crew — pass: Ally; fail: forfeit benefit + Enemy"}],
        10: [{"type": "skill_check", "skills": [{"name": "Survival"}, {"name": "Pilot"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "contact", "desc": "Contact [Fringe of Aslan Space]"},
                          {"type": "free_skill_choice",
                           "prompt": "Survived on the fringes — gain any one skill at level 1:"}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Fringes of Aslan space — roll Survival or Pilot 8+: pass Contact + any skill; fail roll on Mishap table (career continues)"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "A veteran explorer shares their knowledge — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Independence 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Independence"}],
        12: [{"type": "auto_advance"}],
    },
    # ---- GE Aslan careers ----
    "ge_fleet": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "Pilot"}, {"name": "Gunner"}, {"name": "Mechanic"}],
              "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "forfeit_all_benefits"}],
              "prompt": "Roll Pilot, Gunner or Mechanic 8+ vs Hierate attack — fail: lose all Benefits"}],
        4:  [{"type": "skill_choice", "options": ["Steward", "Mechanic", "Electronics"]}],
        5:  [{"type": "dm_qualification_terms_in_career"}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_choice", "options": ["Language", "Streetwise", "Tolerance"]}],
        9:  [{"type": "pending_choice", "id": "event_aslan_heroism_or_prudence",
              "prompt": "Vicious battles against the Hierate — demonstrate heroism (DEX 9+) or prudence (Stealth 8+)?",
              "options": [
                  {"id": "heroism",  "label": "Heroism — roll DEX 9+: pass DM+2 Advancement; fail roll on Injury table"},
                  {"id": "prudence", "label": "Prudence — roll Stealth 8+: pass nothing lost; fail SOC−1"},
              ],
              "heroism_stat": "DEX"}],
        10: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Captain entrusts you with a ceremonial duty — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Steward 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Steward"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "You serve under a hero of the Empire — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Tactics (naval) 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Tactics (naval)"}],
        12: [{"type": "auto_advance"}],
    },
    "ge_fleet_officer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}, {"type": "forfeit_all_benefits"}],
        3:  [{"type": "skill_check", "skills": [{"name": "Tactics"}, {"name": "Engineer"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "enemy", "desc": "Enemy [Hierate Corsair Captain]"},
                          {"type": "forfeit_all_benefits"}],
              "prompt": "Roll Tactics or Engineer 8+ vs Hierate corsairs — fail: Enemy + lose all Benefits"}],
        4:  [{"type": "pending_choice", "id": "event_aslan_smuggle",
              "prompt": "Opportunity to skim profits from commerce raiding — decline (no effect) or accept (Deception/Admin 8+)?",
              "options": [
                  {"id": "decline", "label": "Decline — no effect"},
                  {"id": "accept",  "label": "Accept — roll Deception or Admin 8+: pass 1D Benefit rolls; fail SOC→2 + career ended (Landless One or Outlaw only)"},
              ],
              "skills": [{"name": "Deception"}, {"name": "Admin"}], "target": 8,
              "benefit_dice": "1D", "fail_soc_cap": 2, "fail_eject": True, "fail_career_choice": True}],
        5:  [{"type": "skill_choice", "options": ["Tolerance", "Diplomat", "Language", "Science"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Increase any skill you have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase a skill"}],
        8:  [{"type": "skill_choice", "options": ["Astrogation", "Electronics (sensors)", "Gunner", "Pilot"]}],
        9:  [{"type": "pending_choice", "id": "event_ransom_or_free",
              "prompt": "You captured an enemy commander — ransom them (TER +2) or free them (gain as Ally)?",
              "options": [
                  {"id": "ransom", "label": "Ransom them — gain TER +2"},
                  {"id": "free",   "label": "Free them — gain as a trusted Ally"},
              ]}],
        10: [{"type": "pending_choice", "id": "event_ge_officer_duel",
              "prompt": "Challenged to a duel by a rival — refuse (lose 1D SOC) or accept (Melee 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — lose 1D SOC"},
                  {"id": "accept", "label": "Accept — roll Melee 8+; pass DM+2 Advancement + Melee (Natural) 1"},
              ],
              "extra_on_pass": [{"type": "skill", "name": "Melee (Natural)", "level": 1}]}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "You befriend an admiral — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Tactics (naval) 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Tactics (naval)"}],
        12: [{"type": "auto_advance"}],
    },
    "ge_warrior": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "Recon"}, {"name": "Gun Combat"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "injury"}],
              "prompt": "Roll Recon or Gun Combat 8+ — fail: roll on Injury table"},
             {"type": "skill_choice", "options": ["Stealth", "Medic", "Explosives"]}],
        4:  [{"type": "skill_choice", "options": ["Melee (natural)", "Electronics", "Mechanic"]},
             {"type": "contact", "desc": "Contact [Clan Outpost]"}],
        5:  [{"type": "pending_choice", "id": "event_ge_warrior_battle",
              "prompt": "Battle outside the Empire — choose a skill to gain and test:",
              "options": [
                  {"id": "Melee (natural)", "label": "Melee (natural) 1 then roll it 8+"},
                  {"id": "Gun Combat",      "label": "Gun Combat 1 then roll it 8+"},
                  {"id": "Independence",    "label": "Independence 1 then roll it 8+"},
                  {"id": "Survival",        "label": "Survival 1 then roll it 8+"},
              ]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Increase any skill you have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase a skill"}],
        8:  [{"type": "skill_choice", "options": ["Language", "Tolerance"]}],
        9:  [{"type": "skill_check", "skills": [{"name": "Melee (natural)"}], "target": 8,
              "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1}],
              "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
              "prompt": "Roll Melee (natural) 8+ to defend the ahriy's honour — pass: SOC+1; fail: SOC-1"},
             {"type": "rival", "desc": "Rival [Rival Who Questioned Your Honour]"}],
        10: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "contact", "desc": "Contact [Clan Elder]"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Mercenary event — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain Tactics (military) 1"},
                  {"id": "dm4",   "label": "DM+3 to next Advancement roll"},
              ],
              "skill_option": "Tactics (military)",
              "dm_amount": 3}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },
    "ge_warrior_officer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Recon", "Heavy Weapons", "Vacc Suit", "Drive"]}],
        4:  [{"type": "skill_choice", "options": ["Independence", "Admin", "Diplomat", "Streetwise", "Deception"]},
             {"type": "ally", "desc": "Ally [Empire Capital Contact]"}],
        5:  [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Increase any skill you have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase a skill"}],
        8:  [{"type": "stat", "stat": "TER", "amount": 2}],
        9:  [{"type": "pending_choice", "id": "event_ransom_or_free",
              "prompt": "You captured an enemy commander — ransom them (TER +1) or free them (gain as Ally)?",
              "options": [
                  {"id": "ransom", "label": "Ransom them — gain TER +1"},
                  {"id": "free",   "label": "Free them — gain as an Ally"},
              ],
              "ransom_ter_amount": 1}],
        10: [{"type": "pending_choice", "id": "event_ge_officer_duel",
              "prompt": "Challenged to a duel by a rival — refuse (lose 1D SOC) or accept (Melee 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — lose 1D SOC"},
                  {"id": "accept", "label": "Accept — roll Melee 8+"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Mercenary event — choose reward:",
              "options": [
                  {"id": "Tactics (military)", "label": "Tactics (military) 1 (if male)"},
                  {"id": "Electronics",        "label": "Electronics 1 (if female)"},
                  {"id": "dm4",                "label": "DM+3 to next Advancement roll"},
              ],
              "dm_amount": 3}],
        12: [{"type": "pending_choice", "id": "event_ge_officer_merc",
              "prompt": "Mercenary battle outside the Empire — choose a skill to gain and test:",
              "options": [
                  {"id": "Gun Combat",      "label": "Gun Combat 1 then roll it 8+"},
                  {"id": "Melee (natural)", "label": "Melee (natural) 1 then roll it 8+"},
                  {"id": "Independence",    "label": "Independence 1 then roll it 8+"},
                  {"id": "Vacc Suit",       "label": "Vacc Suit 1 then roll it 8+"},
              ]}],
    },
    "ge_landless_one": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}, {"type": "forfeit_all_benefits"}],
        3:  [{"type": "extra_benefit", "amount": 1},
             {"type": "skill_choice", "options": ["Streetwise", "Broker"]}],
        4:  [{"type": "skill", "name": "Jack-of-All-Trades", "level": 1}],
        5:  [{"type": "skill", "name": "Tolerance", "level": 1},
             {"type": "skill_choice", "options": ["Persuade", "Deception", "Independence"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any skill (except Jack-of-All-Trades) at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain any skill"}],
        8:  [{"type": "skill_choice", "options": ["Pilot (spacecraft)", "Gunner (turret)", "Engineer", "Mechanic"]}],
        9:  [{"type": "skill_choice", "options": ["Carouse", "Streetwise", "Persuade"]},
             {"type": "extra_benefit", "amount": 1}],
        10: [{"type": "skill_check", "skills": [{"name": "Melee"}, {"name": "Deception"}], "target": 8,
              "on_pass": [{"type": "ally", "desc": "Ally [Loyal Crew Member]"}],
              "on_fail": [{"type": "forfeit_benefit"},
                          {"type": "enemy", "desc": "Enemy [Rival Team]"}],
              "prompt": "Roll Melee or Deception 8+ vs rival team — pass: Ally; fail: forfeit benefit + Enemy"}],
        11: [{"type": "pending_choice", "id": "event_aslan_redemption",
              "prompt": "Your clan offers redemption — restore SOC and qualify for another career, but owe a debt to a clan elder?",
              "options": [
                  {"id": "accept",  "label": "Accept — restore SOC to pre-outcast value, DM+99 to Qualification, gain Contact [Clan Elder]"},
                  {"id": "decline", "label": "Decline — no effect"},
              ]}],
        12: [{"type": "force_next_career", "career_id": "ge_warrior"}],
    },
    "ge_slave": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "enemy", "desc": "Enemy [Brutal Overseer]"}],
        4:  [{"type": "skill", "name": "Jack-of-All-Trades", "level": 1}],
        5:  [{"type": "skill_choice", "options": ["Deception", "Mechanic", "Streetwise"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Increase any skill you already have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase a skill you have"}],
        8:  [{"type": "skill_check", "skills": [{"name": "Melee"}, {"name": "Stealth"}], "target": 8,
              "on_pass": [{"type": "extra_benefit", "amount": 1}],
              "on_fail": [{"type": "forfeit_all_benefits"}],
              "prompt": "Roll Melee or Stealth 8+ vs attackers — pass: extra Benefit; fail: lose all Benefits"}],
        9:  [{"type": "skill_choice", "options": ["Deception", "Stealth", "Streetwise"]}],
        10: [{"type": "ally", "desc": "Ally [Fellow Slave / Shrine Community]"},
             {"type": "skill_choice", "options": ["Carouse", "Art", "Language"]}],
        11: [{"type": "skill_choice", "options": ["Leadership", "Admin", "Diplomat"]}],
        12: [{"type": "auto_advance"}],
    },

    # ---- K'kree careers ----
    "kkree_pastoral": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "enemy", "desc": "Enemy [K'kree Herd Rival]"}],
        4:  [{"type": "skill_choice", "options": ["Diplomat", "Contact (non-K'kree)"]}],
        5:  [{"type": "free_skill_choice", "prompt": "Gain 1 level in any skill"}],
        6:  [{"type": "skill_choice", "options": ["Navigation", "Survival"]}],
        8:  [{"type": "skill", "name": "Profession (K'kree Ritual)", "level": 1},
             {"type": "contact", "desc": "Contact [K'kree outside herd]"}],
        9:  [{"type": "stat", "stat": "END", "amount": -1},
             {"type": "skill_choice", "options": ["Melee", "Gun Combat"]}],
        10: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "contact", "desc": "Contact [Steppelord's Court]"}],
        11: [{"type": "skill_choice", "options": ["Patriarchy", "Profession (K'kree Ritual)", "Survival"]}],
        12: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "ally", "desc": "Ally [Herd Elder]"}],
    },
    "kkree_servant": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "extra_benefit", "amount": 1},
             {"type": "enemy", "desc": "Enemy [Herd Rival]"}],
        4:  [{"type": "skill_choice", "options": ["Melee", "Stealth", "Deception"]}],
        5:  [{"type": "skill_check", "skills": [{"name": "INT", "is_stat": True}], "target": 10,
              "on_pass": [{"type": "skill", "name": "Jack-of-all-Trades", "level": 1},
                          {"type": "rival", "desc": "Rival [Made to Look Stupid]"}],
              "on_fail": [],
              "prompt": "Roll INT 10+ — pass: Jack-of-all-Trades 1 + Rival; fail: humiliation"}],
        6:  [{"type": "skill_choice", "options": ["Melee", "Gun Combat"]}],
        8:  [{"type": "skill", "name": "Profession (K'kree Ritual)", "level": 1},
             {"type": "contact", "desc": "Contact [K'kree outside herd]"}],
        9:  [{"type": "skill", "name": "Vacc Suit", "level": 1}],
        10: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "contact", "desc": "Contact [Steppelord's Court]"}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1}],
        12: [{"type": "stat", "stat": "SOC", "amount": 1}],
    },
    "kkree_merchant": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "rival", "desc": "Rival [Herd Competitor]"}],
        4:  [{"type": "free_skill_choice", "prompt": "Gain one roll on any skill table available to Merchant caste"}],
        5:  [{"type": "skill", "name": "Jack-of-all-Trades", "level": 1}],
        6:  [{"type": "skill_choice", "options": ["Electronics (remote ops)", "Gun Combat"]}],
        8:  [{"type": "skill", "name": "Profession (K'kree Ritual)", "level": 1},
             {"type": "contact", "desc": "Contact [K'kree outside herd]"}],
        9:  [{"type": "skill_choice", "options": ["Engineer", "Astrogation", "Electronics"]}],
        10: [{"type": "skill", "name": "Steward", "level": 1}],
        11: [{"type": "skill_choice", "options": ["Pilot", "Electronics (remote ops)", "Gunner"]}],
        12: [{"type": "stat", "stat": "SOC", "amount": 1}],
    },
    "kkree_noble": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "ally", "desc": "Ally [Loyal Rankholder]"}],
              "on_fail": [{"type": "rival", "desc": "Rival [Disgruntled Vassal]"}],
              "prompt": "Rally your herd followers — roll SOC 8+: pass Ally [Loyal Rankholder]; fail Rival [Disgruntled Vassal]"}],
        4:  [{"type": "skill_choice", "options": ["Diplomat", "Leadership"]}],
        5:  [{"type": "skill_check", "skills": [{"name": "Melee"}], "target": 8,
              "on_pass": [{"type": "ally", "desc": "Ally [Admiring Rival]"}],
              "on_fail": [],
              "prompt": "Roll Melee 8+ in contest of martial prowess — pass: gain Ally"}],
        6:  [{"type": "skill_choice", "options": ["Melee", "Gun Combat", "Tactics"]}],
        8:  [{"type": "skill", "name": "Profession (K'kree Ritual)", "level": 1},
             {"type": "contact", "desc": "Contact [K'kree outside herd]"}],
        9:  [{"type": "skill_choice", "options": ["Astrogation", "Pilot"]}],
        10: [{"type": "skill_choice", "options": ["Diplomat", "Persuade", "Streetwise"]}],
        11: [{"type": "skill", "name": "Carouse", "level": 1},
             {"type": "ally", "desc": "Ally [Superior Noble]"}],
        12: [{"type": "stat", "stat": "SOC", "amount": 1}],
    },
    "girug_kagh_translator": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "Diplomat"}], "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "rival", "desc": "Rival [Negotiation Fallout]"}],
              "prompt": "Tricky negotiation — roll Diplomat 8+: pass DM+2 advancement; fail Rival"}],
        4:  [{"type": "skill_choice", "options": ["Vacc Suit", "Pilot (spacecraft)"]}],
        5:  [{"type": "skill_choice", "options": ["Language", "Survival"]}],
        6:  [{"type": "skill_choice", "options": ["Steward", "Admin"]}],
        8:  [{"type": "contact", "desc": "Contact [K'kree Dignitaries]"},
             {"type": "stat", "stat": "SOC", "amount": 1}],
        9:  [{"type": "ally", "desc": "Ally [Foreign Dignitary]"}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "skill", "name": "Diplomat", "level": 1}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    # ---- Core Imperial careers ----
    "agent": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Investigate"}, {"name": "Streetwise"}], "target": 8,
              "on_pass": [{"type": "skill_choice",
                           "options": ["Deception", "Jack-of-All-Trades", "Persuade", "Tactics"]}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Roll Investigate or Streetwise 8+ — pass: skill choice; fail: Mishap (career continues)"}],
        4:  [{"type": "dm_benefit", "amount": 1}],
        5:  [{"type": "d_associates", "kind": "contact", "dice": "D3"}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Increase any one skill you already have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase any one existing skill"}],
        8:  [{"type": "skill_check", "skills": [{"name": "Deception"}], "target": 8,
              "on_pass": [{"type": "skill_choice",
                           "options": ["Deception", "Jack-of-All-Trades", "Persuade", "Streetwise"]}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Undercover op — roll Deception 8+: pass skill choice; fail Mishap. Also roll on Rogue/Citizen table (manual)"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_choice", "options": ["Drive", "Flyer", "Pilot", "Gunner"]}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Befriended by senior agent — choose reward:",
              "options": [
                  {"id": "skill", "label": "Increase Investigate by one level"},
                  {"id": "dm4",  "label": "DM+4 to next Advancement roll"},
              ], "skill_option": "Investigate"}],
        12: [{"type": "auto_advance"}],
    },
    "army": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice",
              "options": ["Vacc Suit", "Engineer", "Animals (riding)", "Recon"]}],
        4:  [{"type": "skill_choice",
              "options": ["Stealth", "Streetwise", "Persuade", "Recon"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Gun Combat", "Leadership"]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Brutal ground war — roll EDU 8+: pass gain Gun Combat or Leadership; fail injury"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Increase any one skill you already have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase any one existing skill"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_choice",
              "options": ["Admin", "Investigate", "Deception", "Recon"]}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Specialist training — choose reward:",
              "options": [
                  {"id": "Heavy Weapons",  "label": "Heavy Weapons 1"},
                  {"id": "Electronics",    "label": "Electronics 1"},
                  {"id": "Engineer",       "label": "Engineer 1"},
                  {"id": "dm4",            "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}],
    },
    "citizen": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "free_skill_choice",
              "prompt": "Gain any one Service Skill at level 1"}],
        4:  [{"type": "rival", "desc": "Rival [Co-worker/Competitor]"},
             {"type": "free_skill_choice",
              "prompt": "Gain one level in any skill you already have"}],
        5:  [{"type": "contact", "desc": "Contact [Workplace Friend]"},
             {"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Increase any one skill you already have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase any one existing skill"}],
        8:  [{"type": "skill_choice",
              "options": ["Admin", "Profession", "Steward", "Survival"]}],
        9:  [{"type": "dm_advancement", "amount": 2},
             {"type": "dm_survival", "amount": -2}],
        10: [{"type": "pending_choice", "id": "event_dm_type_choice",
              "prompt": "Singled out for exemplary work — choose reward:",
              "options": [
                  {"id": "advancement", "label": "DM+2 to next Advancement roll"},
                  {"id": "benefit",     "label": "DM+1 to any one Benefit roll"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_citizen_free_transfer",
              "prompt": "Specialist training — choose reward:",
              "options": [
                  {"id": "skill",    "label": "Gain one Service Skill at level 1"},
                  {"id": "transfer", "label": "Transfer to any non-military career (no Qualification roll)"},
              ]}],
        12: [{"type": "auto_advance"}, {"type": "dm_benefit", "amount": 2}],
    },
    "drifter": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Melee", "Gun Combat", "Athletics"]}],
        4:  [{"type": "skill_choice",
              "options": ["Steward", "Vacc Suit", "Mechanic", "Astrogation"]}],
        5:  [{"type": "ally", "desc": "Ally [Fellow Drifter]"},
             {"type": "skill_choice", "options": ["Streetwise", "Deception", "Persuade"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "dm_benefit", "amount": 2}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Dangerous job — roll END 8+: pass DM+2 Benefit; fail Mishap (career continues)"}],
        8:  [{"type": "enemy_if_none", "desc": "Enemy [Attacker]"},
             {"type": "skill_check",
              "skills": [{"name": "Melee"}, {"name": "Gun Combat"}, {"name": "Stealth"}],
              "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "injury"}],
              "prompt": "Attacked by enemies (Enemy added if you have none) — roll Melee/Gun Combat/Stealth 8+ to avoid injury"}],
        9:  [{"type": "dm_benefit", "amount": 2}],
        10: [{"type": "ally", "desc": "Ally [Local in Trouble — helped]"},
             {"type": "dm_advancement", "amount": 2}],
        11: [{"type": "pending_choice", "id": "event_drifter_skill_or_transfer",
              "prompt": "Wanderer's opportunity — choose:",
              "options": [
                  {"id": "skill",    "label": "Gain one level in any skill of your choice"},
                  {"id": "transfer", "label": "Transfer to any career (no Qualification roll)"},
              ]}],
        12: [{"type": "auto_advance"}],
    },
    "entertainer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rival", "desc": "Rival [Critic/Corporate Backer]"}],
        4:  [{"type": "skill_choice",
              "options": ["Art", "Persuade", "Deception", "Carouse"]}],
        5:  [{"type": "dm_benefit", "amount": 2}],
        6:  [{"type": "pending_choice", "id": "event_entertainer_celebrity",
              "prompt": "Brush with a celebrity, noble or criminal — what relationship develops?",
              "desc": "Contact/Ally/Rival/Enemy [Celebrity/Noble/Criminal Figure]",
              "options": [
                  {"id": "contact", "label": "Contact"},
                  {"id": "ally",    "label": "Ally"},
                  {"id": "rival",   "label": "Rival"},
                  {"id": "enemy",   "label": "Enemy"},
              ]}],
        8:  [{"type": "skill_check",
              "skills": [{"name": "Art"}, {"name": "Persuade"}], "target": 8,
              "on_pass": [{"type": "skill", "name": "Art", "level": 1},
                          {"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
              "prompt": "Prestigious venue — roll Art or Persuade 8+: pass Art+1 + DM+2 Adv; fail SOC−1"}],
        9:  [{"type": "skill_choice",
              "options": ["Streetwise", "Language", "Pilot (small craft)", "Steward"]}],
        10: [{"type": "dm_benefit", "amount": 2},
             {"type": "dm_advancement", "amount": 1}],
        11: [{"type": "pending_choice", "id": "entertainer_patronage",
              "prompt": "Major patronage — choose reward:",
              "options": [
                  {"id": "skill", "label": "Gain one level in any skill of your choice"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },
    "marine": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice",
              "options": ["Vacc Suit", "Gun Combat", "Melee", "Tactics (military)"]}],
        4:  [{"type": "skill_choice",
              "options": ["Recon", "Survival", "Stealth", "Gun Combat"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_choice", "options": ["Vacc Suit", "Athletics (dexterity)"]}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain any one skill from the Service or Advanced Education tables at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain a skill from Service/Advanced Education tables"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "pending_choice", "id": "event_marine_rescue",
              "prompt": "You rescued a fellow Marine under fire:",
              "ally_desc": "Ally [Rescued Marine]",
              "options": [
                  {"id": "benefit",  "label": "Gain Ally + DM+1 to any one Benefit roll"},
                  {"id": "transfer", "label": "Gain Ally + transfer to Army (no Qualification roll)"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Specialist training — choose reward:",
              "options": [
                  {"id": "Battle Dress",       "label": "Battle Dress 1"},
                  {"id": "Heavy Weapons",      "label": "Heavy Weapons 1"},
                  {"id": "Explosives",         "label": "Explosives 1"},
                  {"id": "Tactics (military)", "label": "Tactics (military) 1"},
                  {"id": "dm4",                "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"},
             {"type": "equipment", "name": "Imperial Service Medal",
              "notes": "Awarded for actions in a critical operation"}],
    },
    "merchant": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "enemy", "desc": "Enemy [Attacker]"},
             {"type": "skill_check",
              "skills": [{"name": "Gun Combat"}, {"name": "Gunner"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Ship attacked (Enemy gained regardless) — roll Gun Combat/Gunner 8+ to escape; fail Mishap (career continues)"}],
        4:  [{"type": "skill_choice",
              "options": ["Streetwise", "Broker", "Diplomat", "Carouse"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_choice",
              "options": ["Language", "Pilot (spacecraft)", "Astrogation", "Steward"]}],
        8:  [{"type": "pending_choice", "id": "event_merchant_agreement",
              "prompt": "Long-term cargo agreement with major client — Ally gained either way:",
              "options": [
                  {"id": "benefit",     "label": "Ally + DM+1 to any one Benefit roll"},
                  {"id": "advancement", "label": "Ally + DM+2 to next Advancement roll"},
              ]}],
        9:  [{"type": "skill_check",
              "skills": [{"name": "Pilot"}, {"name": "Deception"}], "target": 8,
              "on_pass": [{"type": "contact", "desc": "Contact [Imperial Starport Authority]"}],
              "on_fail": [{"type": "enemy", "desc": "Enemy [Creditor/Pirate/Authority]"},
                          {"type": "trigger_disaster_mishap"}],
              "prompt": "Pursued — roll Pilot or Deception 8+: pass Contact [ISA]; fail Enemy + Mishap (career continues)"}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Valuable cargo entrusted — choose reward:",
              "options": [
                  {"id": "Diplomat", "label": "Diplomat 1"},
                  {"id": "Broker",   "label": "Broker 1"},
                  {"id": "Advocate", "label": "Advocate 1"},
                  {"id": "dm4",      "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}, {"type": "dm_benefit", "amount": 2}],
    },
    "navy": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Gunner"}, {"name": "Tactics (naval)"}], "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Gunner", "Tactics (naval)"]},
                          {"type": "dm_advancement", "amount": 1}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Ship engages enemy — roll Gunner or Tactics (naval) 8+: pass skill + DM+1 Adv; fail Mishap (career continues)"}],
        4:  [{"type": "skill_choice",
              "options": ["Astrogation", "Survival", "Electronics", "Vacc Suit"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "pending_choice", "id": "event_contact_or_ally",
              "prompt": "Served aboard ship with an excellent captain — how do they regard you?",
              "contact_desc": "Contact [Excellent Naval Captain]",
              "ally_desc": "Ally [Excellent Naval Captain]",
              "options": [
                  {"id": "contact", "label": "Contact"},
                  {"id": "ally",    "label": "Ally"},
              ]}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain any one skill from the Officer or Advanced Education tables at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain a skill from Officer/Advanced Education tables"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "pending_choice", "id": "event_navy_transfer",
              "prompt": "Transferred to elite unit — choose reward:",
              "options": [
                  {"id": "skill",    "label": "Gain a skill (Gun Combat, Melee (blade), Vacc Suit or Leadership)"},
                  {"id": "transfer", "label": "Transfer to Marines (no Qualification roll)"},
              ]}],
        11: [{"type": "pending_choice", "id": "navy_specialist_training",
              "prompt": "Advanced specialist training — choose reward:",
              "options": [
                  {"id": "skill", "label": "Increase any one skill you already have by one level"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"},
             {"type": "equipment", "name": "Imperial Service Medal",
              "notes": "Awarded for heroism in a major fleet action"}],
    },
    "noble": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_noble_duel",
              "prompt": "Challenged to a duel for your honour — accept or refuse?",
              "options": [
                  {"id": "refuse", "label": "Refuse — lose SOC −1"},
                  {"id": "accept", "label": "Accept — roll Melee (blade) 8+: pass SOC+1; fail injury+SOC−1"},
              ]}],
        4:  [{"type": "skill_choice",
              "options": ["Animals (riding)", "Art", "Carouse", "Streetwise"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_choice",
              "options": ["Advocate", "Admin", "Diplomat", "Persuade"]},
             {"type": "rival", "desc": "Rival [Political Opponent]"}],
        8:  [{"type": "pending_choice", "id": "event_noble_conspiracy",
              "prompt": "A conspiracy of nobles tries to recruit you — accept or refuse?",
              "options": [
                  {"id": "refuse", "label": "Refuse — gain the conspiracy as an Enemy"},
                  {"id": "accept", "label": "Accept — roll Deception or Persuade 8+: pass skill; fail Mishap"},
              ]}],
        9:  [{"type": "pending_choice", "id": "noble_ev9_enemy",
              "prompt": "Acclaimed reign — choose which Enemy you gain (+ automatic DM+2 Advancement):",
              "options": [
                  {"id": "relative", "label": "Enemy [Jealous Relative]"},
                  {"id": "subject",  "label": "Enemy [Unhappy Subject]"},
              ]}],
        10: [{"type": "skill_choice",
              "options": ["Carouse", "Diplomat", "Persuade", "Steward"]},
             {"type": "rival", "desc": "Rival [Society Rival]"},
             {"type": "ally",  "desc": "Ally [Society Ally]"}],
        11: [{"type": "ally", "desc": "Ally [Powerful Noble]"},
             {"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Noble alliance — choose reward:",
              "options": [
                  {"id": "skill", "label": "Leadership 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ], "skill_option": "Leadership"}],
        12: [{"type": "auto_advance"}],
    },
    "prisoner": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Melee (unarmed)"}, {"name": "Stealth"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "injury"}],
              "prompt": "Riot — roll Melee (unarmed) or Stealth 8+ to survive unharmed; fail injury"}],
        4:  [{"type": "contact", "desc": "Contact [Criminal Underworld/Political Dissident]"}],
        5:  [{"type": "pending_choice", "id": "prisoner_contraband",
              "prompt": "Smuggling/side operation — choose reward:",
              "options": [
                  {"id": "Streetwise", "label": "Streetwise 1"},
                  {"id": "Deception",  "label": "Deception 1"},
                  {"id": "Gambler",    "label": "Gambler 1"},
                  {"id": "benefit",    "label": "DM+2 to next Benefit roll"},
              ]}],
        6:  [{"type": "skill_choice",
              "options": ["Athletics", "Melee (unarmed)", "Streetwise", "Deception"]}],
        8:  [{"type": "skill_check",
              "skills": [{"name": "SOC", "is_stat": True}, {"name": "Advocate"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "dm_advancement", "amount": -2}],
              "prompt": "Parole hearing — roll SOC or Advocate 8+: pass leave normally; fail DM−2 Advancement"}],
        9:  [{"type": "skill_check",
              "skills": [{"name": "END", "is_stat": True}, {"name": "Melee"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "injury"}, {"type": "enemy", "desc": "Enemy [Guard/Gang]"}],
              "prompt": "Crossed guard/gang — roll END or Melee 8+: fail injury + Enemy"}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "skill_choice",
              "options": ["Admin", "Medic", "Advocate", "Mechanic", "Language"]}],
        12: [{"type": "auto_advance"}, {"type": "ally", "desc": "Ally [Fellow Prisoner]"}],
    },
    "rogue": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "enemy", "desc": "Enemy [Law Enforcement]"},
             {"type": "skill_check",
              "skills": [{"name": "Stealth"}, {"name": "Deception"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Job goes wrong (Enemy gained regardless) — roll Stealth/Deception 8+: fail Mishap (career continues)"}],
        4:  [{"type": "pending_choice", "id": "event_contact_or_ally",
              "prompt": "Made a connection in the underworld — how close?",
              "contact_desc": "Contact [Criminal Underworld]",
              "ally_desc": "Ally [Criminal Underworld]",
              "options": [
                  {"id": "contact", "label": "Contact"},
                  {"id": "ally",    "label": "Ally"},
              ]}],
        5:  [{"type": "dm_benefit", "amount": 2}],
        6:  [{"type": "skill_choice",
              "options": ["Streetwise", "Stealth", "Deception", "Persuade"]}],
        8:  [{"type": "skill_check",
              "skills": [{"name": "Stealth"}, {"name": "Deception"}], "target": 8,
              "on_pass": [{"type": "contact", "desc": "Contact [Major Criminal Syndicate]"},
                          {"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "enemy", "desc": "Enemy [Crime Syndicate]"},
                          {"type": "trigger_disaster_mishap"}],
              "prompt": "Syndicate job — roll Stealth or Deception 8+: pass Contact + DM+2 Adv; fail Enemy + Mishap (career continues)"}],
        9:  [{"type": "skill_check",
              "skills": [{"name": "Streetwise"}, {"name": "Gun Combat"}], "target": 8,
              "on_pass": [],
              "on_fail": [{"type": "enemy", "desc": "Enemy [Law Enforcement Agent]"},
                          {"type": "rival", "desc": "Rival [Street Criminal]"}],
              "prompt": "Clash with law — roll Streetwise or Gun Combat 8+: fail Enemy [Agent] + Rival [Streets]"}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Specialist knowledge/equipment — choose reward:",
              "options": [
                  {"id": "Gun Combat",  "label": "Gun Combat 1"},
                  {"id": "Stealth",     "label": "Stealth 1"},
                  {"id": "Electronics", "label": "Electronics 1"},
                  {"id": "Melee",       "label": "Melee 1"},
                  {"id": "dm4",         "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}, {"type": "dm_benefit", "amount": 2}],
    },
    "scholar": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Survival"}, {"name": "Medic"}], "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Survival", "Medic"]}],
              "on_fail": [{"type": "stat", "stat": "END", "amount": -1}],
              "prompt": "Expedition goes wrong — roll Survival or Medic 8+: pass gain that skill; fail END−1"}],
        4:  [{"type": "skill_choice",
              "options": ["Science", "Engineer", "Medic", "Electronics"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "contact", "desc": "Contact [Academia/Industry/Government]"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any Science specialty of your choice"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain a Science specialty at level 1"}],
        9:  [{"type": "skill_check", "skills": [{"name": "INT", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "rival", "desc": "Rival [Rival Researcher]"}],
              "prompt": "Rival tries to scoop your work — roll INT 8+: pass DM+2 Adv; fail Rival [Researcher]"}],
        10: [{"type": "ally", "desc": "Ally [Powerful Patron — Academia/Industry/Government]"},
             {"type": "dm_advancement", "amount": 2}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Major institution or expedition — choose reward:",
              "options": [
                  {"id": "Admin",    "label": "Admin 1"},
                  {"id": "Advocate", "label": "Advocate 1"},
                  {"id": "Diplomat", "label": "Diplomat 1"},
                  {"id": "dm4",      "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}, {"type": "dm_benefit", "amount": 2}],
    },
    "scout": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "enemy", "desc": "Enemy [Attacker]"},
             {"type": "skill_check",
              "skills": [{"name": "Pilot"}, {"name": "Persuade"}], "target": 8,
              "on_pass": [{"type": "skill", "name": "Electronics (sensors)", "level": 1}],
              "on_fail": [{"type": "force_career_end"}],
              "prompt": "Ambushed (Enemy gained regardless) — roll Pilot 8+ (run) or Persuade 10+ (treat); "
                        "fail: cannot continue in career this term; pass: gain Electronics (sensors) 1"}],
        4:  [{"type": "skill_choice",
              "options": ["Animals (riding)", "Survival", "Recon", "Science"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_choice",
              "options": ["Astrogation", "Electronics", "Navigation",
                          "Pilot (small craft)", "Mechanic"]}],
        8:  [{"type": "skill_check",
              "skills": [{"name": "Electronics (sensors)"}, {"name": "Deception"}], "target": 8,
              "on_pass": [{"type": "ally", "desc": "Ally [Imperial Intelligence]"},
                          {"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Gather alien intelligence — roll Electronics (sensors) or Deception 8+: pass Ally + DM+2 Adv; fail Mishap (career continues)"}],
        9:  [{"type": "skill_check",
              "skills": [{"name": "Medic"}, {"name": "Engineer"}], "target": 8,
              "on_pass": [{"type": "contact", "desc": "Contact [Disaster Survivors]"},
                          {"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "enemy", "desc": "Enemy [Disaster Survivor — blamed you]"}],
              "prompt": "Rescue survivors — roll Medic or Engineer 8+: pass Contact + DM+2 Adv; fail Enemy"}],
        10: [{"type": "skill_check",
              "skills": [{"name": "Survival"}, {"name": "Pilot"}], "target": 8,
              "on_pass": [{"type": "contact", "desc": "Contact [Alien Race]"},
                          {"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill of your choice"}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Fringe of Charted Space — roll Survival or Pilot 8+: pass Contact [Alien] + free skill; fail Mishap (career continues)"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Courier mission for the Imperium — choose reward:",
              "options": [
                  {"id": "skill", "label": "Diplomat 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ], "skill_option": "Diplomat"}],
        12: [{"type": "auto_advance"}],
    },

    # ---- Bounty Hunter ----
    "bounty_hunter": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rival", "desc": "Rival [Competing Bounty Hunter]"},
             {"type": "skill_check",
              "skills": [{"name": "Investigate"}], "target": 8,
              "on_pass": [{"type": "stat", "stat": "REP", "amount": 1},
                          {"type": "skill_choice",
                           "options": ["Athletics", "Deception", "Gun Combat",
                                       "Investigate", "Persuade", "Stealth", "Streetwise"]}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "High-profile bounty race (Rival gained regardless) — roll Investigate 8+: pass REP+1 + skill; fail Mishap (career continues)"}],
        4:  [{"type": "stat", "stat": "REP", "amount": 1},
             {"type": "dm_benefit", "amount": 1}],
        5:  [{"type": "d_associates", "kind": "contact", "dice": "D3"}],
        6:  [{"type": "skill_check", "skills": [{"name": "INT", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "skill_choice",
                           "options": ["Engineer", "Explosives", "Gunner",
                                       "Pilot", "Survival", "Vacc Suit"]}],
              "on_fail": [{"type": "skill_choice",
                           "options": ["Engineer", "Explosives", "Gunner",
                                       "Pilot", "Survival", "Vacc Suit"]}],
              "prompt": "Advanced training — roll INT 8+: pass gain chosen skill (existing +1 or new 1); either way gain skill"}],
        8:  [{"type": "skill_choice", "options": ["Gun Combat", "Heavy Weapons"]}],
        9:  [{"type": "stat", "stat": "REP", "amount": 1},
             {"type": "skill_check",
              "skills": [{"name": "Investigate"}, {"name": "Streetwise"}], "target": 8,
              "on_pass": [{"type": "dm_benefit", "amount": 1}],
              "on_fail": [{"type": "trigger_disaster_mishap"},
                          {"type": "enemy", "desc": "Enemy [Corrupt Politician]"}],
              "prompt": "Corrupt politician bounty (REP+1 always) — roll Investigate/Streetwise 8+: pass DM+1 Benefit; fail Mishap + Enemy"}],
        10: [{"type": "stat", "stat": "REP", "amount": 2}],
        11: [{"type": "ally", "desc": "Ally [Accomplished Bounty Hunter]"},
             {"type": "stat", "stat": "REP", "amount": 1}],
        12: [{"type": "stat", "stat": "REP", "amount": 2},
             {"type": "extra_benefit", "amount": 2}],
    },

    # ---- Dolphin Civilian ----
    "dolphin_civilian": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "cetacean_conflict_choice",
              "prompt": "Ocean resource conflict — diplomacy or violence?",
              "diplomacy_skills": ["Advocate", "Diplomat"],
              "violence_skills": ["Explosives", "Gun Combat", "Tactics"],
              "options": [
                  {"id": "diplomacy", "label": "Diplomacy — roll Advocate/Diplomat 8+: pass DM+2 Adv; fail lose Benefit"},
                  {"id": "violence",  "label": "Violence — roll Explosives/Gun Combat/Tactics 8+: fail DM−2 Adv + injury"},
              ]}],
        4:  [{"type": "contact", "desc": "Contact [Research Field]"},
             {"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 7,
              "on_pass": [{"type": "skill", "name": "Science (cybernetics)", "level": 1}],
              "on_fail": [], "prompt": "Roll EDU 7+ to gain Science (cybernetics) 1"}],
        5:  [{"type": "skill_choice",
              "options": ["Athletics (dexterity)", "Electronics (comms)",
                          "Electronics (sensors)", "Pilot"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "STR", "is_stat": True}], "target": 7,
              "on_pass": [{"type": "ally", "desc": "Ally [High-Status Sophont — rescued]"}],
              "on_fail": [], "prompt": "Rescue high-status swimmer — roll STR 7+: pass Ally"}],
        8:  [{"type": "skill_choice", "options": ["Vacc Suit", "Diplomat"]}],
        9:  [{"type": "pending_choice", "id": "cetacean_fight_or_flee",
              "prompt": "Companions attacked by sea creatures — fight or flee?",
              "fight_skills": ["Melee (natural)", "Gun Combat"],
              "target": 7,
              "options": [
                  {"id": "flee",  "label": "Flee — one survivor becomes Enemy"},
                  {"id": "fight", "label": "Fight — roll Melee (natural)/Gun Combat 7+: pass Ally; fail injury"},
              ]}],
        10: [{"type": "skill_check",
              "skills": [{"name": "Survival"}, {"name": "END", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2},
                          {"type": "extra_benefit", "amount": 1}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Dangerous rescue mission — roll Survival or END 8+: pass DM+2 Adv + extra Benefit; fail injury"}],
        11: [{"type": "extra_benefit", "amount": 1}],
        12: [{"type": "auto_advance"}],
    },

    # ---- Dolphin Military ----
    "dolphin_military": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "dm_advancement", "amount": 2},
             {"type": "contact", "desc": "Contact [Elite Military Unit]"}],
        4:  [{"type": "skill_check", "skills": [{"name": "Vacc Suit"}], "target": 4,
              "on_pass": [{"type": "skill", "name": "Explosives", "level": 1}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Mine disposal training — roll Vacc Suit 4+: pass Explosives+1; fail injury"}],
        5:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 7,
              "on_pass": [{"type": "skill_choice",
                           "options": ["Pilot (small craft)", "Electronics (sensors)"]}],
              "on_fail": [], "prompt": "Roll EDU 7+ to gain Pilot or Electronics (sensors) 1"}],
        6:  [{"type": "skill_check", "skills": [{"name": "Vacc Suit"}], "target": 7,
              "on_pass": [{"type": "skill_choice",
                           "options": ["Gun Combat", "Leadership", "Tactics (military)"]}],
              "on_fail": [], "prompt": "Amphibious campaign — roll Vacc Suit 7+ to gain Gun Combat/Leadership/Tactics 1"}],
        8:  [{"type": "skill_choice",
              "options": ["Vacc Suit", "Melee", "Gun Combat", "Tactics (military)"]}],
        9:  [{"type": "contact", "desc": "Contact [Intelligence Agent]"},
             {"type": "skill_check", "skills": [{"name": "INT", "is_stat": True}], "target": 7,
              "on_pass": [{"type": "skill_choice", "options": ["Recon", "Stealth"]}],
              "on_fail": [], "prompt": "Intelligence joint mission — roll 7+ to gain Recon or Stealth 1"}],
        10: [{"type": "pending_choice", "id": "cetacean_accept_or_protest",
              "prompt": "Unjustly blamed by human leader — accept blame or protest?",
              "options": [
                  {"id": "accept",  "label": "Accept — DM−1 to next Advancement roll"},
                  {"id": "protest", "label": "Protest — roll Advocate/SOC 8+: pass DM+1 Adv + skill; fail DM−2 Adv"},
              ]}],
        11: [{"type": "dm_advancement", "amount": 2},
             {"type": "skill_choice", "options": ["Admin", "Tactics (military)"]}],
        12: [{"type": "auto_advance"}],
    },

    # ---- Philosopher-Elder (Uplifted Orca) ----
    "philosopher_elder": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "cetacean_conflict_choice",
              "prompt": "Ocean resource conflict — diplomacy or violence?",
              "diplomacy_skills": ["Advocate", "Diplomat"],
              "violence_skills": ["Explosives", "Gun Combat", "Tactics"],
              "options": [
                  {"id": "diplomacy", "label": "Diplomacy — roll Advocate/Diplomat 8+: pass DM+2 Adv; fail lose Benefit"},
                  {"id": "violence",  "label": "Violence — roll Explosives/Gun Combat/Tactics 8+: fail DM−2 Adv + injury"},
              ]}],
        4:  [{"type": "contact", "desc": "Contact [Research Field]"},
             {"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 7,
              "on_pass": [{"type": "skill", "name": "Science (cybernetics)", "level": 1}],
              "on_fail": [], "prompt": "Roll EDU 7+ to gain Science (cybernetics) 1"}],
        5:  [{"type": "skill_choice",
              "options": ["Athletics (dexterity)", "Electronics (comms)",
                          "Electronics (sensors)", "Pilot"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "STR", "is_stat": True}], "target": 7,
              "on_pass": [{"type": "ally", "desc": "Ally [High-Status Sophont — rescued]"}],
              "on_fail": [], "prompt": "Rescue high-status swimmer — roll STR 7+: pass Ally"}],
        8:  [{"type": "skill_choice", "options": ["Vacc Suit", "Diplomat"]}],
        9:  [{"type": "pending_choice", "id": "cetacean_fight_or_flee",
              "prompt": "Companions attacked by sea creatures — fight or flee?",
              "fight_skills": ["Melee (natural)", "Gun Combat"],
              "target": 7,
              "options": [
                  {"id": "flee",  "label": "Flee — one survivor becomes Enemy"},
                  {"id": "fight", "label": "Fight — roll Melee (natural)/Gun Combat 7+: pass Ally; fail injury"},
              ]}],
        10: [{"type": "skill_check",
              "skills": [{"name": "Survival"}, {"name": "END", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 2},
                          {"type": "extra_benefit", "amount": 1}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Dangerous rescue mission — roll Survival or END 8+: pass DM+2 Adv + extra Benefit; fail injury"}],
        11: [{"type": "extra_benefit", "amount": 1}],
        12: [{"type": "auto_advance"}],
    },

    # ---- Spirit Singer (Orca) ----
    "spirit_singer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "ally", "desc": "Ally [Clan Elder — proved your guidance]"}],
        4:  [{"type": "contact", "desc": "Contact [Matriarch — spiritual consultation]"}],
        5:  [{"type": "skill_choice", "options": ["Survival", "Persuade"]}],
        6:  [{"type": "stat", "stat": "SOC", "amount": -3},
             {"type": "d_extra_benefit", "dice": "D3"},
             {"type": "dm_benefit", "amount": 3}],
        8:  [{"type": "skill_choice", "options": ["Carouse", "Persuade"]}],
        9:  [{"type": "pending_choice", "id": "cetacean_fight_or_flee",
              "prompt": "Companions attacked by sea creatures — fight or flee?",
              "fight_skills": ["Melee (natural)"],
              "target": 7,
              "options": [
                  {"id": "flee",  "label": "Flee — one survivor becomes Enemy"},
                  {"id": "fight", "label": "Fight — roll Melee (natural) 7+: pass Ally; fail injury"},
              ]}],
        10: [{"type": "pending_choice", "id": "spirit_singer_matriarch",
              "prompt": "Secretly consult the spirits for a dying matriarch of another faith — agree or decline?",
              "options": [
                  {"id": "agree",   "label": "Agree — Ally in her Pod + Rival in own faith"},
                  {"id": "decline", "label": "Decline — no effect"},
              ]}],
        11: [{"type": "dm_permanent_advancement", "amount": -2}],
        12: [{"type": "auto_advance"}, {"type": "dm_permanent_advancement", "amount": 1}],
    },

    # ---- Aslan Outcast ----
    "aslan_outcast": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}, {"type": "forfeit_all_benefits"}],
        3:  [{"type": "dm_qualification", "amount": 4}],
        4:  [{"type": "skill", "name": "Jack-of-All-Trades", "level": 1}],
        5:  [{"type": "skill_choice",
              "options": ["Mechanic", "Vacc Suit", "Engineer", "Tolerance"]}],
        6:  [{"type": "contact", "desc": "Contact [Underworld/Fringer]"}],
        8:  [{"type": "skill_check",
              "skills": [{"name": "Melee"}, {"name": "Stealth"}], "target": 8,
              "on_pass": [{"type": "extra_benefit", "amount": 1}],
              "on_fail": [{"type": "forfeit_all_benefits"}],
              "prompt": "Attacked by thieves — roll Melee 10+ or Stealth 8+ to fight/escape: pass extra Benefit; fail lose all Benefits"}],
        9:  [{"type": "pending_choice", "id": "aslan_outcast_join_ihatei",
              "prompt": "An ihatei offers you a place in their retinue — join or decline?",
              "options": [
                  {"id": "join",    "label": "Join — gain Ally [Ihatei] (must attempt Core career qualification next term)"},
                  {"id": "decline", "label": "Decline — no effect"},
              ]}],
        10: [{"type": "dm_qualification", "amount": 99}],
        11: [{"type": "pending_choice", "id": "event_aslan_redemption",
              "prompt": "Your clan offers redemption — restore SOC and qualify for another career, but owe a debt to a clan elder?",
              "options": [
                  {"id": "accept",  "label": "Accept — restore SOC to pre-outcast value, DM+99 to Qualification, gain Contact [Clan Elder]"},
                  {"id": "decline", "label": "Decline — no effect"},
              ]}],
        12: [{"type": "auto_advance"}],
    },

    # ---- Aslan Outlaw ----
    "aslan_outlaw": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "stat", "stat": "END", "amount": -1},
             {"type": "free_skill_choice", "prompt": "Barely survived — gain any one skill at level 1"}],
        4:  [{"type": "extra_benefit", "amount": 1}],
        5:  [{"type": "pending_choice", "id": "aslan_outlaw_bounty",
              "prompt": "A clan has put a price on your head — take the normal path or claim the reward yourself?",
              "options": [
                  {"id": "normal", "label": "Normal path — Enemy [Clan] + skill choice"},
                  {"id": "risky",  "label": "Claim reward yourself — Enemy [Clan] + Deception 8+: pass 3 Benefits; fail END−2 + ejected"},
              ]}],
        6:  [{"type": "contact", "desc": "Contact [Criminal Sphere]"}],
        8:  [{"type": "skill_choice",
              "options": ["Electronics", "Independence", "Stealth", "Gun Combat"]}],
        9:  [{"type": "skill_check",
              "skills": [{"name": "Pilot"}, {"name": "Stealth"}, {"name": "Gun Combat"}],
              "target": 8,
              "on_pass": [{"type": "pending_choice", "id": "aslan_outlaw_pass_reward",
                           "prompt": "Audacious raid succeeded — choose reward:",
                           "options": [
                               {"id": "benefit", "label": "1 extra Benefit roll"},
                               {"id": "soc",     "label": "SOC +1"},
                           ]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Audacious raid — roll Pilot/Stealth/Gun Combat 8+: pass extra Benefit or SOC+1; fail injury"}],
        10: [{"type": "pending_choice", "id": "aslan_outlaw_mission",
              "prompt": "Clan offers covert mission — accept (Stealth 8+ for extra Benefit) or inform enemies (Benefit + Enemy)?",
              "options": [
                  {"id": "accept", "label": "Accept mission — roll Stealth 8+: pass extra Benefit; fail nothing"},
                  {"id": "inform", "label": "Inform enemies — gain extra Benefit + Enemy [Clan]"},
              ]}],
        11: [{"type": "pending_choice", "id": "aslan_outlaw_redemption",
              "prompt": "Chance at redemption (career ends after this term) — choose your path:",
              "options": [
                  {"id": "male",   "label": "Male: TER+1 + restore SOC (note SOC manually)"},
                  {"id": "female", "label": "Female (unmarried): reroll SOC (2D auto-rolled)"},
                  {"id": "none",   "label": "Decline — no effect"},
              ]}],
        12: [{"type": "auto_advance"}],
    },

    # ---- Solomani careers ----
    "confederation_army": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice",
              "options": ["Vacc Suit", "Engineer", "Animals (riding)", "Recon"]}],
        4:  [{"type": "skill_choice",
              "options": ["Stealth", "Streetwise", "Persuade", "Recon"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Gun Combat", "Leadership"]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Brutal ground war — roll EDU 8+: pass gain Gun Combat or Leadership; fail injury"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Increase any one skill you already have by one level"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to increase any one existing skill"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_choice",
              "options": ["Admin", "Investigate", "Deception", "Recon"]}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Specialist training — choose reward:",
              "options": [
                  {"id": "Heavy Weapons",  "label": "Heavy Weapons 1"},
                  {"id": "Electronics",    "label": "Electronics 1"},
                  {"id": "Engineer",       "label": "Engineer 1"},
                  {"id": "dm4",            "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}],
    },
    "confederation_navy": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice",
              "options": ["Animals (riding)", "Survival", "Recon", "Science"]}],
        4:  [{"type": "pending_choice", "id": "event_confnav_recreation",
              "prompt": "Off-duty time — recreation or Party study group?",
              "options": [
                  {"id": "recreation",  "label": "Recreation — gain Carouse 1 or Gambler 1"},
                  {"id": "study",       "label": "Study group — DM+2 to next Advancement roll"},
                  {"id": "study_int",   "label": "Study group — Roll INT 8+ for Advocate / History / Science"},
              ]}],
        5:  [{"type": "contact", "desc": "Contact [Party Corp/Confederation]"},
             {"type": "skill_check",
              "skills": [{"name": "EDU", "is_stat": True}],
              "target": 8,
              "on_pass": [{"type": "skill_choice",
                           "options": ["Tactics (naval)", "Electronics", "Astrogation"]}],
              "on_fail": [],
              "prompt": "Specialised training — roll EDU 8+ to gain Tactics (naval), Electronics, or Astrogation"}],
        6:  [{"type": "skill_choice",
              "options": ["Electronics (sensors)", "Engineer", "Gunner",
                          "Pilot", "Tactics (naval)"]}],
        8:  [{"type": "skill_choice",
              "options": ["Language", "Recon", "Diplomat", "Steward"]}],
        9:  [{"type": "skill_choice", "options": ["Astrogation", "Science"]}],
        10: [{"type": "skill_choice",
              "options": ["Electronics (comms)", "Deception", "Recon"]},
             {"type": "contact", "desc": "Contact [Solomani Guerrillas]"}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Commanding officer mentors you — choose reward:",
              "options": [
                  {"id": "skill", "label": "Tactics (naval) 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ], "skill_option": "Tactics (naval)"}],
        12: [{"type": "auto_advance"}],
    },
    "party": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "auto_qualify_careers", "career_ids": ["citizen", "merchant"]}],
        4:  [{"type": "skill_check",
              "skills": [{"name": "Advocate"}, {"name": "Art"}], "target": 7,
              "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1}],
              "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
              "prompt": "Party Congress speech — roll Advocate or Art 7+: pass SOC+1; fail SOC−1"}],
        5:  [{"type": "pending_choice", "id": "event_party_takebane",
              "prompt": "Asked to take blame for a senior Party member — agree or refuse?",
              "options": [
                  {"id": "accept", "label": "Agree — gain Ally + DM+1 Benefit roll"},
                  {"id": "refuse", "label": "Refuse — DM−2 Advancement + Rival"},
              ]}],
        6:  [{"type": "skill_check",
              "skills": [{"name": "Advocate"}, {"name": "Gun Combat"}, {"name": "Explosives"},
                         {"name": "Leadership"}, {"name": "Streetwise"}],
              "target": 8,
              "on_pass": [{"type": "dm_survival", "amount": 2}],
              "on_fail": [{"type": "dm_survival", "amount": -2}],
              "prompt": "Violent political struggle — roll Advocate, Gun Combat, Explosives, Leadership or Streetwise 8+: pass DM+2 next Survival; fail DM-2 next Survival"}],
        8:  [{"type": "pending_choice", "id": "event_party_evidence",
              "prompt": "Evidence of superior's disloyalty — expose or suppress?",
              "options": [
                  {"id": "expose",   "label": "Expose — DM+2 Advancement"},
                  {"id": "suppress", "label": "Suppress — gain them as Ally"},
              ]}],
        9:  [{"type": "skill_choice",
              "options": ["Advocate", "Diplomat", "Persuade", "Science (philosophy)"]},
             {"type": "rival", "desc": "Rival [Opposing Party Faction]"}],
        10: [{"type": "skill_choice", "options": ["Art", "Carouse"]},
             {"type": "contact", "desc": "Contact [Media/Entertainment Industry]"}],
        11: [{"type": "ally", "desc": "Ally [Senior Party Member]"},
             {"type": "rival", "desc": "Rival [Rival Party Faction]"},
             {"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Befriended senior Party figure — choose reward:",
              "options": [
                  {"id": "Advocate",             "label": "Advocate 1"},
                  {"id": "Diplomat",             "label": "Diplomat 1"},
                  {"id": "Science (philosophy)", "label": "Science (philosophy) 1"},
                  {"id": "dm4",                  "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}],
    },
    "solsec": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_report_or_suppress",
              "prompt": "Evidence of SolSec corruption — report or suppress?",
              "ally_desc": "Ally [Corrupt SolSec Contact]",
              "enemy_desc": "Enemy [Reported Corrupt Officer]",
              "options": [
                  {"id": "report",   "label": "Report up the chain — DM+2 Advancement + Enemy"},
                  {"id": "suppress", "label": "Suppress the evidence — gain Ally inside SolSec"},
              ]}],
        4:  [{"type": "pending_choice", "id": "event_surveil_or_rapport",
              "prompt": "Assigned to monitor a prominent citizen — approach?",
              "contact_desc": "Contact [Monitored Prominent Citizen]",
              "options": [
                  {"id": "surveil", "label": "Aggressive surveillance — gain Investigate or Stealth 1"},
                  {"id": "rapport", "label": "Friendly rapport — gain Contact"},
              ]}],
        5:  [{"type": "skill_check",
              "skills": [{"name": "Deception"}, {"name": "Stealth"}], "target": 8,
              "on_pass": [{"type": "skill_choice",
                           "options": ["Electronics (comms)", "Deception", "Recon", "Stealth"]},
                          {"type": "contact", "desc": "Contact [Solomani Underground]"}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Cross-border operation — roll Deception or Stealth 8+: pass skill + Contact; fail Mishap (career continues)"}],
        6:  [{"type": "skill_choice",
              "options": ["Advocate", "Investigate", "Persuade", "Streetwise"]}],
        8:  [{"type": "skill_choice",
              "options": ["Astrogation", "Electronics (sensors)", "Gunner",
                          "Pilot", "Tactics (naval)"]},
             {"type": "contact", "desc": "Contact [Confederation Navy Intelligence]"}],
        9:  [{"type": "skill_choice", "options": ["Streetwise", "Carouse"]},
             {"type": "d_associates", "kind": "contact", "dice": "1D"}],
        10: [{"type": "pending_choice", "id": "event_solsec_leverage",
              "prompt": "Discovered disloyal Party official — expose or leverage?",
              "options": [
                  {"id": "expose",   "label": "Expose — DM+2 Advancement + Enemy [Official]"},
                  {"id": "leverage", "label": "Leverage — Ally [Official] + Rival [SolSec Faction]"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Senior SolSec mentor — choose reward:",
              "options": [
                  {"id": "Deception",           "label": "Deception 1"},
                  {"id": "Investigate",         "label": "Investigate 1"},
                  {"id": "Science (psychology)", "label": "Science (psychology) 1"},
                  {"id": "dm4",                 "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}],
    },
    "solomani_marine": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice",
              "options": ["Vacc Suit", "Gun Combat", "Melee", "Tactics (military)"]}],
        4:  [{"type": "skill_choice",
              "options": ["Recon", "Survival", "Stealth", "Gun Combat"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_choice", "options": ["Vacc Suit", "Athletics (dexterity)"]}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain any one skill from the Service or Advanced Education tables at level 1"}],
              "on_fail": [], "prompt": "Roll EDU 8+ to gain a skill from Service/Advanced Education tables"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "pending_choice", "id": "event_marine_rescue",
              "prompt": "Rescued a fellow Star Marine under heavy fire:",
              "ally_desc": "Ally [Rescued Star Marine]",
              "options": [
                  {"id": "benefit",  "label": "Ally + DM+1 to any one Benefit roll"},
                  {"id": "transfer", "label": "Ally + transfer to Confederation Army (no Qualification roll)"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Advanced specialist training — choose reward:",
              "options": [
                  {"id": "Battle Dress",       "label": "Battle Dress 1"},
                  {"id": "Heavy Weapons",      "label": "Heavy Weapons 1"},
                  {"id": "Explosives",         "label": "Explosives 1"},
                  {"id": "Tactics (military)", "label": "Tactics (military) 1"},
                  {"id": "dm4",                "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}],
    },

    # ================================================================
    # Vargr Extents careers
    # ================================================================

    "vargr_army": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Vacc Suit", "Engineer", "Survival"]}],
        4:  [{"type": "skill_choice", "options": ["Stealth", "Streetwise", "Persuade", "Recon"]}],
        5:  [{"type": "pending_choice", "id": "event_stat_or_dm",
              "prompt": "Special assignment — choose your reward:",
              "options": [
                  {"id": "benefit", "label": "DM+1 to one Benefit roll"},
                  {"id": "SOC",     "label": "SOC +1"},
              ],
              "stat": "SOC", "stat_amount": 1, "dm_field": "benefit", "dm_amount": 1}],
        6:  [{"type": "skill_check",
              "skills": [{"name": "END", "is_stat": True}],
              "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "skill_choice", "options": ["Gun Combat", "Leadership"]},
                          {"type": "pending_choice", "id": "event_stat_or_dm",
                           "prompt": "Ground war survived — roll for promotion or choose reward:",
                           "options": [
                               {"id": "auto", "label": "Roll SOC 8+ for automatic promotion"},
                               {"id": "none", "label": "No promotion attempt"},
                           ],
                           "stat": "SOC", "stat_check_promote": True, "dm_field": "none", "dm_amount": 0}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Ground war, leader killed — roll END 8+: survive + skill + maybe promoted; fail: injury"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Increase any one skill you already have by one level:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "pending_choice", "id": "event_stat_or_dm",
              "prompt": "Held out until relief arrives — choose reward:",
              "options": [
                  {"id": "advancement", "label": "DM+1 to next Advancement roll"},
                  {"id": "SOC",         "label": "SOC +1"},
              ],
              "stat": "SOC", "stat_amount": 1, "dm_field": "advancement", "dm_amount": 1}],
        10: [{"type": "pending_choice", "id": "event_skill_or_stat",
              "prompt": "Peacekeeping assignment — choose your reward:",
              "options": [
                  {"id": "Admin",       "label": "Admin 1"},
                  {"id": "Investigate", "label": "Investigate 1"},
                  {"id": "Recon",       "label": "Recon 1"},
                  {"id": "SOC",         "label": "SOC +1"},
              ],
              "stat": "SOC", "stat_amount": 1}],
        11: [{"type": "ally", "desc": "Ally [Pack Leader — Saved Life]"},
             {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "stat", "stat": "SOC", "amount": 1}, {"type": "auto_advance"}],
    },

    "vargr_citizen": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "dm_survival", "amount": -2}],
              "prompt": "Power struggle — roll SOC 8+: pass DM+2 Advancement; fail DM−2 next Survival"}],
        4:  [{"type": "free_skill_choice",
              "prompt": "Further education — roll on any Advanced Education table for one skill:"}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Increase one skill you already have by one level:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        8:  [{"type": "pending_choice", "id": "event_citizen_scandal",
              "prompt": "You learn a corporate secret or political scandal — profit from it or stay quiet?",
              "options": [
                  {"id": "profit", "label": "Profit — DM+2 Adv, DM+1 Benefit, SOC−1, then choose skill/Contact"},
                  {"id": "quiet",  "label": "Stay quiet — no effect"},
              ]}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 10,
              "on_nat2": [],
              "on_pass": [{"type": "auto_advance"}],
              "on_fail": [],
              "prompt": "Roll SOC 10+ to become new pack leader — pass: automatic promotion"}],
        11: [{"type": "ally", "desc": "Ally [New Pack Leader — You Supported]"},
             {"type": "dm_advancement", "amount": 4}],
        12: [{"type": "pending_choice", "id": "event_stat_or_dm",
              "prompt": "Well respected by pack — choose reward:",
              "options": [
                  {"id": "SOC",  "label": "SOC +1"},
                  {"id": "auto", "label": "Automatic promotion"},
              ],
              "stat": "SOC", "stat_amount": 1, "dm_field": "auto_advance", "dm_amount": 0}],
    },

    "vargr_corsair": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "forfeit_benefit"},
             {"type": "contact", "desc": "Contact [Lawyer Who Got Charges Dropped]"}],
        4:  [{"type": "skill", "name": "Survival", "level": 1}],
        5:  [{"type": "contact", "desc": "Contact [Criminal Underworld]"}],
        6:  [{"type": "extra_benefit", "amount": 1}],
        8:  [{"type": "skill_choice", "options": ["Streetwise", "Stealth", "Melee", "Gun Combat"]}],
        9:  [{"type": "skill_check", "skills": [{"name": "Gun Combat"}, {"name": "Melee"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Territorial war vs rival band — roll Gun Combat or Melee 8+: pass SOC+1; fail injury"}],
        10: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 10,
              "on_nat2": [],
              "on_pass": [{"type": "auto_advance"}],
              "on_fail": [],
              "prompt": "Roll SOC 10+ to become new pack leader — pass: automatic promotion"}],
        11: [{"type": "ally", "desc": "Ally [New Pack Leader — You Supported]"},
             {"type": "dm_advancement", "amount": 4}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    "vargr_emissary": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_emissary_negot",
              "prompt": "Negotiations going badly — cut your losses (SOC−1) or roll Broker/Diplomat/Persuade 10+?",
              "options": [
                  {"id": "cut",  "label": "Cut losses — SOC −1"},
                  {"id": "roll", "label": "Roll Broker, Diplomat or Persuade 10+"},
              ]}],
        4:  [{"type": "dm_benefit", "amount": 1}],
        5:  [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "ally", "desc": "Ally [Influential Contact]"}],
              "on_fail": [{"type": "contact", "desc": "Contact [Influential Figure]"}],
              "prompt": "Roll SOC 8+ to gain an Ally; fail: gain a Contact instead"}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any eligible career skill at level 1:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to gain a career skill"}],
        8:  [{"type": "skill_choice", "options": ["Advocate", "Broker", "Diplomat"]}],
        9:  [{"type": "pending_choice", "id": "event_emissary_switch",
              "prompt": "A charismatic pack leader from the opposing side offers you a lucrative deal to switch sides:",
              "options": [
                  {"id": "accept", "label": "Accept — gain 1 Benefit roll, previous employer becomes Rival"},
                  {"id": "refuse", "label": "Refuse — current employer becomes Ally, DM+2 to next Survival roll"},
              ]}],
        10: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 10,
              "on_nat2": [],
              "on_pass": [{"type": "auto_advance"}],
              "on_fail": [],
              "prompt": "Roll SOC 10+ to become pack leader — pass: automatic promotion"}],
        11: [{"type": "pending_choice", "id": "event_benefit_or_dm4",
              "prompt": "Favourable career position — choose reward:",
              "options": [
                  {"id": "benefit", "label": "Gain 1 extra Benefit roll"},
                  {"id": "dm4",     "label": "DM+4 to next Advancement roll"},
              ]}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    "vargr_law_enforcement": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Investigate"}, {"name": "Streetwise"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
                           "prompt": "Dangerous investigation succeeded — choose reward:",
                           "options": [
                               {"id": "SOC +1",              "label": "SOC +1"},
                               {"id": "Deception",           "label": "Deception 1"},
                               {"id": "Jack-of-all-Trades",  "label": "Jack-of-all-Trades 1"},
                               {"id": "Stealth",             "label": "Stealth 1"},
                               {"id": "Streetwise",          "label": "Streetwise 1"},
                               {"id": "Tactics (military)",  "label": "Tactics (Military) 1"},
                           ]}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Dangerous investigation — roll Investigate or Streetwise 8+: pass SOC+1 or skill; fail roll on Mishap table"}],
        4:  [{"type": "contacts_soc_dm_min1", "desc": "Contact [Network]"}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any eligible career skill at level 1:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to gain a career skill"}],
        8:  [{"type": "pending_choice", "id": "event_law_profit",
              "prompt": "Illegal goods found in warehouse — profit from discovery (Deception 8+) or ignore it?",
              "options": [
                  {"id": "profit", "label": "Profit — roll Deception 8+ (pass: 1 Benefit; fail: SOC−1 + DM−4 Survival)"},
                  {"id": "ignore", "label": "Ignore it — no effect"},
              ]}],
        9:  [{"type": "skill_check", "skills": [{"name": "Deception"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Undercover success — roll on any Specialist skills table for cover career:"},
                          {"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Undercover investigation — roll Deception 8+: pass skill + DM+2 Adv; fail roll on Mishap table for cover career"}],
        10: [{"type": "ally", "desc": "Ally [Saved Pack Member]"}],
        11: [{"type": "dm_advancement", "amount": 4}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    "vargr_loner": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "vargr_loner_patron",
              "prompt": "A patron offers you a job — accept (DM+4 Qualification + Contact) or decline?",
              "options": [
                  {"id": "accept",  "label": "Accept — gain DM+4 to next Qualification roll + Contact [Patron]"},
                  {"id": "decline", "label": "Decline — no effect"},
              ]}],
        4:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 6,
              "on_nat2": [],
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Roll on your specialist skill table for one skill:"}],
              "on_fail": [], "prompt": "Self-reliance — roll EDU 6+ to gain a specialist skill"}],
        5:  [{"type": "skill", "name": "Jack-of-all-Trades", "level": 1}],
        6:  [{"type": "pending_choice", "id": "event_loner_corsair",
              "prompt": "Corsairs board you — nothing of value. They offer you a place in their band. Join or refuse?",
              "options": [
                  {"id": "join",   "label": "Join — automatic qualification for Vargr Corsair next term"},
                  {"id": "refuse", "label": "Refuse (or SOC failed) — roll on Injury table"},
              ]}],
        8:  [{"type": "extra_benefit", "amount": 1}],
        9:  [{"type": "dm_benefit", "amount": 1}],
        10: [{"type": "skill_check", "skills": [{"name": "Survival"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "pending_choice", "id": "event_loner_stat_choice",
                           "prompt": "Thrive on adversity — choose stat to increase by 1:",
                           "options": [
                               {"id": "STR", "label": "STR +1"},
                               {"id": "DEX", "label": "DEX +1"},
                               {"id": "END", "label": "END +1"},
                           ]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Roll Survival 8+: pass +1 to STR, DEX or END; fail injury"}],
        11: [{"type": "dm_survival", "amount": 2}, {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    "vargr_marines": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "stat", "stat": "END", "amount": 1}],
        4:  [{"type": "skill_choice", "options": ["Vacc Suit", "Athletics (dexterity)"]}],
        5:  [{"type": "skill_choice", "options": ["Gun Combat", "Melee", "Recon"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Gain any eligible career skill at level 1:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to gain a career skill"}],
        8:  [{"type": "ally", "desc": "Ally [Saved Pack Member]"}],
        9:  [{"type": "skill", "name": "Tactics", "level": 1}, {"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "auto_advance"}],
              "on_fail": [],
              "prompt": "Leader killed — roll SOC 8+ to take command: pass automatic promotion; fail nothing"}],
        11: [{"type": "dm_advancement", "amount": 4}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    "vargr_merchant": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_merchant_smuggle",
              "prompt": "You are approached to buy or smuggle illegal goods — accept or refuse?",
              "options": [
                  {"id": "accept", "label": "Accept — roll Deception 8+ (pass: Benefit DM+1; fail: arrested SOC−1)"},
                  {"id": "refuse", "label": "Refuse — gain an Enemy"},
              ]}],
        4:  [{"type": "dm_benefit", "amount": 1}],
        5:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "Training course — gain any skill at level 1:"}],
              "on_fail": [], "prompt": "Training course — roll EDU 8+ to gain any skill"}],
        6:  [{"type": "skill_choice", "options": ["Advocate", "Admin", "Diplomat", "Investigate", "Persuade"]}],
        8:  [{"type": "extra_benefit", "amount": 1}],
        9:  [{"type": "ally", "desc": "Ally [Saved Company]"}],
        10: [{"type": "contacts_soc_dm_min1", "desc": "Contact [Business Network]"}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1}, {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    "vargr_navy": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "dm_benefit", "amount": 1}],
        4:  [{"type": "contact", "desc": "Contact [Crew Member]"}],
        5:  [{"type": "skill_choice", "options": ["Vacc Suit", "Athletics (dexterity)"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any eligible career skill:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to gain a career skill"}],
        8:  [{"type": "skill_choice", "options": ["Astrogation", "Electronics", "Pilot"]}],
        9:  [{"type": "skill", "name": "Jack-of-all-Trades", "level": 1}],
        10: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "auto_advance"}],
              "on_fail": [],
              "prompt": "Leader killed — roll SOC 8+ to take command: pass automatic promotion; fail nothing"}],
        11: [{"type": "dm_advancement", "amount": 4}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    "vargr_psion": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "d6_result",
              "ranges": [
                  {"min": 1, "max": 4, "effects": []},
                  {"min": 5, "max": 6, "effects": [{"type": "psi_adjust", "amount": -1}]},
              ]}],
        4:  [{"type": "d6_result",
              "ranges": [
                  {"min": 1, "max": 2, "effects": [{"type": "injury"}]},
                  {"min": 3, "max": 4, "effects": [{"type": "free_skill_choice",
                                                    "prompt": "Alien device — gain one level in a Talent you already know:"}]},
                  {"min": 5, "max": 6, "effects": [{"type": "psi_adjust", "amount": 1}]},
              ]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any non-psionic skill:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to gain a non-psionic skill"}],
        8:  [{"type": "skill_check", "skills": [{"name": "PSI", "is_stat": True}], "target": 10,
              "on_nat2": [],
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Psionic training success — gain a new psionic Talent:"}],
              "on_fail": [{"type": "skill", "name": "Science (Psionicology)", "level": 1}],
              "prompt": "Psionic training — roll PSI 10+: pass new Talent; fail Science (Psionicology) 1"}],
        9:  [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "ally", "desc": "Ally [Saved Pack Member]"}],
        10: [{"type": "psi_adjust", "amount": 1}],
        11: [{"type": "contact", "desc": "Contact [Psionic Mentor]"},
             {"type": "dm_advancement", "amount": 4}],
        12: [{"type": "auto_advance"}],
    },

    "vargr_scientist": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "contact", "desc": "Contact [Military Project]"},
             {"type": "skill_choice", "options": ["Gun Combat", "Engineer", "Heavy Weapons", "Science"]}],
        4:  [{"type": "skill", "name": "Deception", "level": 1}],
        5:  [{"type": "skill_choice", "options": ["Vacc Suit", "Athletics (dexterity)"]}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any eligible career skill:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to gain a career skill"}],
        8:  [{"type": "contacts_soc_dm_min1", "desc": "Contact [Research Institute]"}],
        9:  [{"type": "ally", "desc": "Ally [Eccentric Mentor]"},
             {"type": "free_skill_choice", "prompt": "Gain one level in any Science skill:"}],
        10: [{"type": "stat", "stat": "SOC", "amount": 1}, {"type": "dm_benefit", "amount": 1}],
        11: [{"type": "dm_benefit", "amount": 1}, {"type": "dm_advancement", "amount": 4}],
        12: [{"type": "auto_advance"}, {"type": "stat", "stat": "SOC", "amount": 1}],
    },

    # ================================================================
    # Zhodani Consulate careers
    # ================================================================

    "zhodani_agent": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Drive", "Flyer", "Pilot", "Seafarer"]}],
        4:  [{"type": "d6_result",
              "ranges": [
                  {"min": 1, "max": 1, "effects": [{"type": "injury"}]},
                  {"min": 2, "max": 6, "effects": [{"type": "skill_choice",
                                                    "options": ["Survival", "Medic"]}]},
              ]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "d_extra_benefit", "dice": "D3"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "skill_check", "skills": [{"name": "Investigate"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Undercover success — roll on any Prole Specialist skill table:"},
                          {"type": "dm_benefit", "amount": 1}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Undercover investigation — roll Investigate 8+: pass Prole skill + benefit roll; fail roll on Prole Mishap table"}],
        10: [{"type": "skill_choice", "options": ["Admin", "Electronics (computers)", "Electronics (comms)"]}],
        11: [{"type": "ally", "desc": "Ally [Superior — Took Interest]"},
             {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_army": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Stealth", "Persuade", "Recon"]}],
        4:  [{"type": "skill_choice", "options": ["Vacc Suit", "Engineer", "Animals", "Recon"]}],
        5:  [{"type": "skill_choice", "options": ["Vacc Suit", "Heavy Weapons", "Athletics (dexterity)"]},
             {"type": "pending_choice", "id": "event_army_guard_transfer",
              "prompt": "Commando training — if SOC 10+, you may leave and auto-qualify for the Guard career:",
              "options": [
                  {"id": "transfer", "label": "Leave and auto-qualify for Guard (SOC 10+ required)"},
                  {"id": "stay",     "label": "Stay in Army career"},
              ]}],
        6:  [{"type": "skill_check",
              "skills": [{"name": "Gun Combat"}, {"name": "Stealth"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "skill_choice",
                           "options": ["Gun Combat", "Leadership", "Tactics (military)"]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Brutal ground war — roll Gun Combat or Stealth 8+: pass skill choice; fail injury"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_choice", "options": ["Admin", "Investigate", "Recon"]}],
        11: [{"type": "ally", "desc": "Ally [Commanding Officer]"},
             {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_entertainer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_entertainer_controversial",
              "prompt": "Invited to a controversial event — refuse (nothing) or accept (Art/Persuade 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — nothing happens"},
                  {"id": "accept", "label": "Accept — roll Art or Persuade 8+ (pass: extra Benefit; fail: Mishap table)"},
              ]}],
        4:  [{"type": "skill_choice", "options": ["Carouse", "Persuade", "Steward"]}],
        5:  [{"type": "extra_benefit", "amount": 1}],
        6:  [{"type": "dm_advancement", "amount": 2}, {"type": "ally", "desc": "Ally [Arts Patron]"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "d_extra_benefit", "dice": "D3"}],
        10: [{"type": "skill_check", "skills": [{"name": "Art"}, {"name": "Persuade"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "dm_advancement", "amount": -2}],
              "prompt": "Challenging task — roll Art or Persuade 8+: pass DM+2 Advancement; fail DM−2 Advancement"}],
        11: [{"type": "pending_choice", "id": "event_zhodani_entertainer_counsel",
              "prompt": "Opportunity to expose a questionable council leader — support them or expose them?",
              "options": [
                  {"id": "support", "label": "Support leader — DM+2 to next Advancement roll"},
                  {"id": "expose",  "label": "Expose leader — gain Enemy, then roll Art/Persuade 8+"},
              ]}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_government": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Animals (riding)", "Art", "Carouse"]}],
        4:  [{"type": "free_skill_choice",
              "prompt": "Special advisor to another Zhodani career — roll on any other career's Service Skills table:"},
             {"type": "extra_benefit", "amount": 1}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_choice", "options": ["Admin", "Advocate", "Diplomat", "Persuade"]},
             {"type": "rival", "desc": "Rival [Political Rival]"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "pending_choice", "id": "event_govt_conspiracy",
              "prompt": "A group of conspiring Nobles attempts to recruit you — refuse (Enemy) or accept (Diplomat/Persuade 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — gain Enemy [Noble Conspiracy]"},
                  {"id": "accept", "label": "Accept — roll Diplomat or Persuade 8+"},
              ]}],
        10: [{"type": "skill_choice", "options": ["Advocate", "Diplomat", "Leadership"]}],
        11: [{"type": "ally", "desc": "Ally [Powerful Noble]"},
             {"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Alliance with powerful Noble — choose your reward:",
              "options": [
                  {"id": "skill", "label": "Gain Leadership 1"},
                  {"id": "dm4",   "label": "DM+2 to next Advancement roll"},
              ],
              "skill_option": "Leadership",
              "dm_amount": 2}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_guard": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Vacc Suit", "Athletics (dexterity)"]}],
        4:  [{"type": "skill_choice", "options": ["Recon", "Gun Combat", "Leadership", "Electronics (comms)"]}],
        5:  [{"type": "skill_choice", "options": ["Advocate", "Investigate", "Persuade"]},
             {"type": "pending_choice", "id": "event_guard_tp_transfer",
              "prompt": "Thought Police training — if SOC 10+, you may leave and auto-qualify for Agent (Thought Police):",
              "options": [
                  {"id": "transfer", "label": "Leave and auto-qualify for Agent (Thought Police) — SOC 10+ required"},
                  {"id": "stay",     "label": "Stay in Guard career"},
              ]}],
        6:  [{"type": "skill_check", "skills": [{"name": "Melee"}, {"name": "Gun Combat"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "skill_choice", "options": ["Tactics (military)", "Leadership"]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Fortress assault — roll Melee or Gun Combat 8+: pass skill choice; fail injury"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "pending_choice", "id": "event_guard_rescue",
              "prompt": "Volunteer for deadly rescue mission — refuse (nothing) or accept (Survival/END 8+)?",
              "options": [
                  {"id": "refuse", "label": "Refuse — nothing happens"},
                  {"id": "accept", "label": "Accept — roll Survival or END 8+ (pass: DM+2 Adv + extra Benefit; fail: injury)"},
              ]}],
        10: [{"type": "pending_choice", "id": "event_guard_report",
              "prompt": "Mission went wrong due to commander's error — report CO (DM+2 Adv) or protect CO (Ally)?",
              "options": [
                  {"id": "report",  "label": "Report CO — DM+2 to next Advancement roll"},
                  {"id": "protect", "label": "Protect CO — gain them as an Ally"},
              ]}],
        11: [{"type": "pending_choice", "id": "event_skillmulti_or_dm4",
              "prompt": "Commanding officer takes an interest — choose your reward:",
              "options": [
                  {"id": "Leadership",         "label": "Leadership 1"},
                  {"id": "Tactics (military)", "label": "Tactics (Military) 1"},
                  {"id": "dm4",                "label": "DM+2 to next Advancement roll"},
              ],
              "dm_amount": 2}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_merchant": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_zhodani_merchant_drafted",
              "prompt": "Government drafts your ship — must leave Merchant career.",
              "options": [
                  {"id": "noted", "label": "Acknowledged — may auto-qualify for Zhodani Navy next term"},
              ]}],
        4:  [{"type": "skill_choice", "options": ["Animals", "Engineer", "Science", "Profession"]}],
        5:  [{"type": "skill_choice", "options": ["Admin", "Broker", "Electronics (computers)"]}],
        6:  [{"type": "skill_choice", "options": ["Broker", "Diplomat", "Profession"]},
             {"type": "contact", "desc": "Contact [New Territory]"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "dm_benefit", "amount": 1}],
        10: [{"type": "extra_benefit", "amount": 1}],
        11: [{"type": "ally", "desc": "Ally [Superior — Took Interest]"},
             {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_navy": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Diplomat", "Recon", "Steward"]},
             {"type": "contact", "desc": "Contact [Diplomatic Mission]"}],
        4:  [{"type": "skill_choice", "options": ["Engineer", "Gunner", "Pilot", "Electronics (sensors)"]}],
        5:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to gain a skill"}],
        6:  [{"type": "skill_choice", "options": ["Engineer", "Mechanic", "Science"]}],
        8:  [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "skill_choice",
                           "options": ["Animals", "Recon", "Survival", "Contact [Border World]"]}],
              "on_fail": [],
              "prompt": "Tour of border worlds — roll SOC 8+: pass choose one (Animals/Recon/Survival or Contact); fail nothing"}],
        9:  [{"type": "skill_choice", "options": ["Athletics (dexterity)", "Electronics (sensors)", "Vacc Suit"]}],
        10: [{"type": "skill_check", "skills": [{"name": "Mechanic"}, {"name": "Engineer"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "dm_advancement", "amount": 2}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Explosion — roll Mechanic or Engineer 8+: pass DM+2 Advancement; fail injury"}],
        11: [{"type": "ally", "desc": "Ally [Commanding Officer]"},
             {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_prole": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Investigate"}, {"name": "Streetwise"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "skill_choice",
                           "options": ["Deception", "Jack-of-all-Trades", "Persuade", "Tactics"]}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Dangerous investigation — roll Investigate or Streetwise 8+: pass skill choice; fail roll on Mishap table"}],
        4:  [{"type": "dm_benefit", "amount": 1}],
        5:  [{"type": "d_extra_benefit", "dice": "D3"}],
        6:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already have:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        8:  [{"type": "skill_check", "skills": [{"name": "Deception"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Undercover success — roll on any Rogue or Citizen Specialist skill table:"},
                          {"type": "dm_benefit", "amount": 1}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Undercover investigation — roll Deception 8+: pass skill + benefit; fail roll on Rogue/Citizen Mishap table"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_choice", "options": ["Drive", "Flyer", "Pilot", "Gunner"]}],
        11: [{"type": "pending_choice", "id": "event_skill_or_dm4",
              "prompt": "Befriended by a senior agent — choose reward:",
              "options": [
                  {"id": "skill", "label": "Investigate 1"},
                  {"id": "dm4",   "label": "DM+4 to next Advancement roll"},
              ],
              "skill_option": "Investigate"}],
        12: [{"type": "auto_advance"}],
    },

    "zhodani_scholar": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "event_scholar_conscience",
              "prompt": "Called to perform research against your conscience — accept (benefit + 2 Science skills + D3 Enemies) or refuse (Ally)?",
              "options": [
                  {"id": "accept", "label": "Accept — extra Benefit, two Science skill levels, D3 Enemies"},
                  {"id": "refuse", "label": "Refuse — gain an Ally"},
              ]}],
        4:  [{"type": "skill_choice",
              "options": ["Electronics", "Engineer", "Investigate", "Medic", "Science"]}],
        5:  [{"type": "dm_benefit", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "Survival"}, {"name": "Pilot"}], "target": 8,
              "on_nat2": [],
              "on_pass": [{"type": "contact", "desc": "Contact [Alien Race]"},
                          {"type": "free_skill_choice", "prompt": "Gain one level in any selected skill:"}],
              "on_fail": [{"type": "trigger_disaster_mishap"}],
              "prompt": "Fringe of known space — roll Survival or Pilot 8+: pass alien Contact + skill; fail roll on Mishap table"}],
        8:  [{"type": "skill_check", "skills": [{"name": "EDU", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice",
                           "prompt": "Gain one level in any skill you already possess:"}],
              "on_fail": [], "prompt": "Advanced training — roll EDU 8+ to increase a skill"}],
        9:  [{"type": "dm_advancement", "amount": 2}],
        10: [{"type": "skill_choice", "options": ["Admin", "Advocate", "Diplomat", "Persuade"]}],
        11: [{"type": "ally", "desc": "Ally [Eccentric Noble Mentor]"},
             {"type": "free_skill_choice", "prompt": "Increase any one Science skill by one level:"},
             {"type": "dm_advancement", "amount": 2}],
        12: [{"type": "auto_advance"}],
    },

    # ---- Droyne careers ----
    # Events 2 = Disaster (→ mishap); 7 = nothing; 12 = Ancients Tech 1
    # All events 3 = rank+1; 8 = Recon or Survival
    # Career-specific events follow below.
    "droyne_worker": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rank_adjustment", "amount": 1}],
        4:  [{"type": "skill_check", "skills": [{"name": "Appeal"}], "target": 8,
              "on_pass": [{"type": "rank_adjustment", "amount": 1}],
              "on_fail": [],
              "prompt": "Appeal 8+ — success: rank +1. Either way, gain Appeal 1."},
             {"type": "skill", "name": "Appeal", "level": 1}],
        5:  [{"type": "pending_choice", "id": "droyne_worker_black_or_eject",
              "prompt": "Follow Leader's orders (gain a Black Skill) or refuse and be ejected?",
              "options": [
                  {"id": "obey",  "label": "Obey — gain one Black Skill (Carouse/Deception/Gambler/Persuade/Streetwise)"},
                  {"id": "refuse","label": "Refuse — ejected from the Oytrip"},
              ]}],
        6:  [{"type": "skill_choice", "options": ["Profession", "Drive", "Flyer", "Appeal"]}],
        7:  [],  # Narrative event
        8:  [{"type": "skill_choice", "options": ["Recon", "Survival"]}],
        9:  [{"type": "pending_choice", "id": "droyne_worker_idea",
              "prompt": "Dare to suggest your idea (Appeal 8+) or keep quiet (gain Profession/Caste)?",
              "options": [
                  {"id": "dare",  "label": "Dare — Appeal 8+: rank+1 on pass, rank−1 on fail"},
                  {"id": "quiet", "label": "Keep quiet — gain Profession or Caste 1"},
              ]}],
        10: [{"type": "skill", "name": "Outsider", "level": 1},
             {"type": "contact", "desc": "Contact [Outside Oytrip]"}],
        11: [{"type": "skill_choice", "options": ["Electronics", "Engineer", "Gunner", "Vacc Suit"]}],
        12: [{"type": "skill", "name": "Ancients Tech", "level": 1}],
    },
    "droyne_warrior": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rank_adjustment", "amount": 1}],
        4:  [{"type": "skill", "name": "Ancients Tech", "level": 1}],
        5:  [{"type": "skill_check", "skills": [{"name": "Gun Combat"}], "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Gun Combat", "Melee", "Heavy Weapons"]}],
              "on_fail": [{"type": "skill", "name": "Medic", "level": 1}],
              "prompt": "Gun Combat 8+ — pass: gain Gun Combat/Melee/Heavy Weapons; fail: gain Medic"}],
        6:  [{"type": "skill_choice", "options": ["Gun Combat", "Heavy Weapons", "Vacc Suit", "Leadership"]}],
        7:  [],  # Narrative event
        8:  [{"type": "skill_choice", "options": ["Recon", "Survival"]}],
        9:  [{"type": "skill_check", "skills": [{"name": "Tactics"}], "target": 8,
              "on_pass": [{"type": "rank_adjustment", "amount": 1}],
              "on_fail": [{"type": "rank_adjustment", "amount": -1},
                          {"type": "skill", "name": "Tactics", "level": 1}],
              "prompt": "Tactics 8+ — pass: rank+1; fail: rank−1 and gain Tactics"}],
        10: [{"type": "skill", "name": "Outsider", "level": 1},
             {"type": "contact", "desc": "Contact [Outside Oytrip]"}],
        11: [{"type": "skill_choice", "options": ["Electronics", "Engineer", "Gunner", "Vacc Suit", "Pilot"]}],
        12: [{"type": "skill", "name": "Ancients Tech", "level": 1}],
    },
    "droyne_drone": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rank_adjustment", "amount": 1}],
        4:  [{"type": "skill_check", "skills": [{"name": "Appeal"}], "target": 8,
              "on_pass": [{"type": "pending_choice", "id": "droyne_drone_appeal_pass",
                           "prompt": "Appeal succeeded — choose rank+1 or Caste 1:",
                           "options": [
                               {"id": "rank", "label": "Rank +1"},
                               {"id": "caste","label": "Caste 1"},
                           ]}],
              "on_fail": [{"type": "skill", "name": "Appeal", "level": 1}],
              "prompt": "Appeal 8+ — pass: rank+1 or Caste 1; fail: gain Appeal 1"}],
        5:  [{"type": "skill_choice", "options": ["Outsider", "Science", "Vacc Suit"]}],
        6:  [{"type": "skill_choice", "options": ["Profession", "Admin", "Art", "Appeal"]}],
        7:  [],  # Narrative event
        8:  [{"type": "skill_choice", "options": ["Recon", "Survival"]}],
        9:  [{"type": "skill_check", "skills": [{"name": "Appeal"}], "target": 8,
              "on_pass": [{"type": "rank_adjustment", "amount": 1}],
              "on_fail": [{"type": "rank_adjustment", "amount": -1}],
              "prompt": "Reveal alarming prediction: Appeal 8+ — pass: rank+1; fail: rank−1"}],
        10: [{"type": "skill", "name": "Outsider", "level": 1},
             {"type": "contact", "desc": "Contact [Outside Oytrip]"}],
        11: [{"type": "skill_choice", "options": ["Admin", "Appeal", "Leadership"]}],
        12: [{"type": "skill", "name": "Ancients Tech", "level": 1}],
    },
    "droyne_technician": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rank_adjustment", "amount": 1}],
        4:  [{"type": "skill_check", "skills": [{"name": "Appeal"}], "target": 8,
              "on_pass": [{"type": "rank_adjustment", "amount": 1}],
              "on_fail": [{"type": "skill", "name": "Caste", "level": 1}],
              "prompt": "Appeal 8+ — pass: rank+1; fail: Caste (technician) 1"}],
        5:  [{"type": "pending_choice", "id": "droyne_tech_black_or_eject",
              "prompt": "Follow Leader's orders (gain a Black Skill) or refuse and be ejected?",
              "options": [
                  {"id": "obey",  "label": "Obey — gain one Black Skill (Carouse/Deception/Gambler/Persuade/Streetwise)"},
                  {"id": "refuse","label": "Refuse — ejected from the Oytrip"},
              ]}],
        6:  [{"type": "skill_choice", "options": ["Profession", "Drive", "Flyer", "Appeal"]}],
        7:  [],  # Narrative event
        8:  [{"type": "skill_choice", "options": ["Recon", "Survival"]}],
        9:  [{"type": "pending_choice", "id": "droyne_tech_assignment_stat",
              "prompt": "Proved adept — choose your assignment bonus stat:",
              "options": [
                  {"id": "fixing",    "label": "Fixing — DEX +1"},
                  {"id": "artificer", "label": "Artificer — EDU +1"},
                  {"id": "dreaming",  "label": "Dreaming — INT +1"},
              ]}],
        10: [{"type": "skill", "name": "Outsider", "level": 1},
             {"type": "contact", "desc": "Contact [Outside Oytrip]"}],
        11: [{"type": "skill_choice", "options": ["Electronics", "Engineer", "Gunner", "Pilot", "Vacc Suit"]}],
        12: [{"type": "skill", "name": "Ancients Tech", "level": 1}],
    },
    "droyne_sport": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rank_adjustment", "amount": 1}],
        4:  [{"type": "skill_check", "skills": [{"name": "Appeal"}], "target": 8,
              "on_pass": [{"type": "rank_adjustment", "amount": 1}],
              "on_fail": [],
              "prompt": "Workers ask you to raise concerns: Appeal 8+ — pass: rank+1. Either way: gain Appeal 1."},
             {"type": "skill", "name": "Appeal", "level": 1}],
        5:  [{"type": "skill_choice",
              "options": ["Carouse", "Deception", "Gambler", "Persuade", "Streetwise"],
              "prompt": "Sent to live among non-Droyne — gain a Black Skill (you are diminished by knowing it):"}],
        6:  [{"type": "free_skill_choice", "prompt": "Work outside normal expertise — gain any skill from your career tables:"}],
        7:  [],  # Narrative event
        8:  [{"type": "skill_choice", "options": ["Recon", "Survival"]}],
        9:  [{"type": "pending_choice", "id": "droyne_sport_outsider_or_black",
              "prompt": "Interact with non-Droyne — gain Outsider or a Black Skill?",
              "options": [
                  {"id": "outsider", "label": "Outsider 1"},
                  {"id": "black",    "label": "A Black Skill (Carouse/Deception/Gambler/Persuade/Streetwise)"},
              ]}],
        10: [{"type": "skill_choice", "options": ["Astrogation", "Electronics", "Engineer", "Gunner", "Pilot", "Vacc Suit"]}],
        11: [{"type": "pending_choice", "id": "droyne_sport_ancients",
              "prompt": "Ancients Tech or Art (Droyne) 8+ — success: PSI+1 AND Ancients Tech; fail: choose one:",
              "options": [
                  {"id": "pass", "label": "Checked passed — PSI+1 and Ancients Tech 1"},
                  {"id": "psi",  "label": "Check failed — choose PSI+1"},
                  {"id": "tech", "label": "Check failed — choose Ancients Tech 1"},
              ]}],
        12: [{"type": "skill", "name": "Ancients Tech", "level": 1}],
    },
    "droyne_leader": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "rank_adjustment", "amount": 1}],
        4:  [{"type": "pending_choice", "id": "droyne_leader_worker_concern",
              "prompt": "A Worker brings concerns. Support them or put them in their place?",
              "options": [
                  {"id": "support",   "label": "Support — gain Leadership 1 but a Rival [Oytrip member]"},
                  {"id": "discipline","label": "Discipline — gain Caste (leader) 1 and an Ally [Oytrip member]"},
              ]}],
        5:  [{"type": "pending_choice", "id": "droyne_leader_outsider_visit",
              "prompt": "Sent with a diplomatic party to a non-Droyne installation — learn their ways?",
              "options": [
                  {"id": "learn",   "label": "Learn — gain one Black Skill (Carouse/Deception/Gambler/Persuade/Streetwise)"},
                  {"id": "abstain", "label": "Abstain — gain nothing"},
              ]}],
        6:  [{"type": "skill_choice", "options": ["Appeal", "Diplomat", "Leadership"]}],
        7:  [],  # Narrative event
        8:  [{"type": "skill_choice", "options": ["Recon", "Survival"]}],
        9:  [{"type": "pending_choice", "id": "droyne_leader_idea_support",
              "prompt": "A non-Leader brings an idea with merit. Raise it to senior Leaders or discipline them?",
              "options": [
                  {"id": "support",   "label": "Support the idea — gain Appeal 1"},
                  {"id": "discipline","label": "Put them in their place — gain Caste (leader) 1"},
              ]}],
        10: [{"type": "skill", "name": "Outsider", "level": 1},
             {"type": "contact", "desc": "Contact [Outside Oytrip]"}],
        11: [{"type": "skill_choice", "options": ["Astrogation", "Tactics", "Vacc Suit"]}],
        12: [{"type": "skill", "name": "Ancients Tech", "level": 1}],
    },

    # ---- Hiver Federation careers ----
    # Event 7 = Life Event; Event 8 = starship skills (Pilot/Astrogation/Engineer)
    # Event 9 = Ally + Contact; common events shared across all 4 careers
    "hiver_academic": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "free_skill_choice", "prompt": "Roll on any Service Skills table for any career:"}],
        4:  [{"type": "dm_advancement", "amount": 4}],
        5:  [{"type": "contact", "desc": "Contact [Possible Enemy — one of 3 is secretly an Enemy]"},
             {"type": "contact", "desc": "Contact [Possible Enemy — one of 3 is secretly an Enemy]"},
             {"type": "contact", "desc": "Contact [Possible Enemy — one of 3 is secretly an Enemy]"},
             {"type": "skill", "name": "Gun Combat", "level": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "RES", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "RES check passed — gain a level in any skill you possess:"}],
              "on_fail": [],
              "prompt": "RES 8+ to gain a level in any skill you already have"}],
        7:  [],  # Life Event — handled by API /life-event endpoint
        8:  [{"type": "skill_choice", "options": ["Pilot", "Astrogation", "Engineer"]}],
        9:  [{"type": "ally", "desc": "Ally [Embassy/Other Nests]"},
             {"type": "contact", "desc": "Contact [Embassy/Other Nests]"}],
        10: [{"type": "ally", "desc": "Ally [Alien Races]"},
             {"type": "pending_choice", "id": "hiver_academic_alien_cash",
              "prompt": "Spend time outside Federation — take extra cash roll (but gain Rival) or just the Ally?",
              "options": [
                  {"id": "cash",      "label": "Take extra cash benefit roll (gain Rival)"},
                  {"id": "ally_only", "label": "Just the Ally"},
              ]}],
        11: [{"type": "skill_choice", "options": ["Animals", "Recon", "Survival"]}],
        12: [{"type": "pending_choice", "id": "hiver_academic_nest_threat",
              "prompt": "Nest threatened — choose reward for helping:",
              "options": [
                  {"id": "science_res", "label": "Science (sociology) 1 and RES +1"},
                  {"id": "persuade",    "label": "Persuade 1 and a Contact"},
              ]}],
    },
    "hiver_generalist": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "free_skill_choice", "prompt": "Roll on any Service Skills table for any career:"}],
        4:  [{"type": "dm_advancement", "amount": 4}],
        5:  [{"type": "d_associates", "kind": "contact", "dice": "D3", "desc_prefix": "Contact"}],
        6:  [{"type": "skill_check", "skills": [{"name": "RES", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "RES check passed — gain a level in any skill you possess:"}],
              "on_fail": [],
              "prompt": "RES 8+ to gain a level in any skill you already have"}],
        7:  [],  # Life Event
        8:  [{"type": "skill_choice", "options": ["Pilot", "Astrogation", "Engineer"]}],
        9:  [{"type": "ally", "desc": "Ally [Embassy/Other Nests]"},
             {"type": "contact", "desc": "Contact [Embassy/Other Nests]"}],
        10: [{"type": "skill_choice", "options": ["Deception", "Streetwise"]}],
        11: [{"type": "skill_choice", "options": ["Animals", "Recon", "Survival"]}],
        12: [{"type": "skill_choice", "options": ["Gun Combat", "Heavy Weapons"]}],
    },
    "hiver_manipulator": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "free_skill_choice", "prompt": "Roll on any Service Skills table for any career:"}],
        4:  [{"type": "dm_advancement", "amount": 4}],
        5:  [{"type": "dm_permanent_advancement", "amount": 1}],
        6:  [{"type": "skill_check", "skills": [{"name": "RES", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "RES check passed — gain a level in any skill you possess:"}],
              "on_fail": [],
              "prompt": "RES 8+ to gain a level in any skill you already have"}],
        7:  [],  # Life Event
        8:  [{"type": "skill_choice", "options": ["Pilot", "Astrogation", "Engineer"]}],
        9:  [{"type": "ally", "desc": "Ally [Embassy/Other Nests]"},
             {"type": "contact", "desc": "Contact [Embassy/Other Nests]"}],
        10: [{"type": "skill", "name": "Streetwise", "level": 1},
             {"type": "contact", "desc": "Contact [Alien/Non-Hiver]"}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "ally", "desc": "Ally [Major Endeavour]"}],
        12: [{"type": "skill_check", "skills": [{"name": "RES", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "dm_advancement", "amount": 4},
                          {"type": "free_skill_choice", "prompt": "Choose any skill:"},
                          {"type": "contact", "desc": "Contact [Outside Hiver Society]"}],
              "on_fail": [{"type": "free_skill_choice", "prompt": "Choose any skill:"},
                          {"type": "contact", "desc": "Contact [Outside Hiver Society]"}],
              "prompt": "RES 8+ — pass: immediate DM+4 advancement check + skill + Contact; fail: skill + Contact"}],
    },
    "hiver_merchant": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "free_skill_choice", "prompt": "Roll on any Service Skills table for any career:"}],
        4:  [{"type": "dm_advancement", "amount": 4}],
        5:  [{"type": "pending_choice", "id": "hiver_merchant_big_score",
              "prompt": "Big score — take the money or claim the credit?",
              "options": [
                  {"id": "money",  "label": "Take the money — roll 2D×Cr100,000"},
                  {"id": "credit", "label": "Claim the credit — DM+1 to all advancement in this career, gain Contact"},
              ]}],
        6:  [{"type": "skill_check", "skills": [{"name": "RES", "is_stat": True}], "target": 8,
              "on_pass": [{"type": "free_skill_choice", "prompt": "RES check passed — gain a level in any skill you possess (level 0+):"}],
              "on_fail": [],
              "prompt": "RES 8+ to gain a level in any skill you have at level 0 or higher"}],
        7:  [],  # Life Event
        8:  [{"type": "skill_choice", "options": ["Pilot", "Astrogation", "Engineer"]}],
        9:  [{"type": "ally", "desc": "Ally [Embassy/Other Nests]"},
             {"type": "contact", "desc": "Contact [Embassy/Other Nests]"}],
        10: [{"type": "skill", "name": "Streetwise", "level": 1},
             {"type": "contact", "desc": "Contact [Alien/Non-Hiver]"}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "ally", "desc": "Ally [Major Organisation]"}],
        12: [{"type": "skill", "name": "Tactics", "level": 1},
             {"type": "contact", "desc": "Contact [Outside Hiver Society]"}],
    },
    # ---- Imperial Guard ----
    "imperial_guard": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "END", "is_stat": True}, {"name": "STR", "is_stat": True}],
              "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Athletics", "Gun Combat"]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Suppress planetary uprising — roll END 8+ or STR 8+: pass skill; fail Injury"}],
        4:  [{"type": "skill_choice", "options": ["Admin", "Carouse"]}],
        5:  [{"type": "skill", "name": "Melee", "level": 1, "speciality": "Blade"},
             {"type": "contact", "desc": "Contact [Imperial Nobility]"}],
        6:  [{"type": "skill_choice", "options": ["Gun Combat", "Tactics (Military)"]}],
        7:  [],  # Life Event
        8:  [{"type": "skill_choice", "options": ["Diplomat", "Carouse"]},
             {"type": "d_associates", "kind": "contact", "dice": "D3",
              "desc_prefix": "Contact [Imperial Nobility]"}],
        9:  [{"type": "skill_choice", "options": ["Stealth", "Recon"]}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "auto_advance"}],
        12: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "extra_benefit", "amount": 2}],
    },

    # ---- INI (Imperial Naval Intelligence) ----
    "ini": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "INT", "is_stat": True}],
              "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Deception", "Stealth"]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Network compromised — roll INT 8+: pass skill; fail Injury"}],
        4:  [{"type": "skill_choice", "options": ["Admin", "Electronics"]}],
        5:  [{"type": "skill", "name": "Persuade", "level": 1},
             {"type": "contact", "desc": "Contact [Asset in Enemy Organisation]"}],
        6:  [{"type": "skill_choice", "options": ["Streetwise", "Deception"]}],
        7:  [],  # Life Event
        8:  [{"type": "skill_choice", "options": ["Electronics", "Investigate"]},
             {"type": "d_associates", "kind": "contact", "dice": "D3",
              "desc_prefix": "Contact [Intelligence Network]"}],
        9:  [{"type": "skill_choice", "options": ["Stealth", "Gun Combat"]}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "auto_advance"}],
        12: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "extra_benefit", "amount": 2}],
    },

    # ---- Storm Knight careers ----
    "storm_knight_thunder": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Recon"}, {"name": "Survival"}],
              "target": 8,
              "on_pass": [{"type": "skill_choice", "options": ["Recon", "Survival", "Stealth"]}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Roll Recon or Survival 8+ — pass: gain Recon/Survival/Stealth 1; fail: Injury"}],
        4:  [{"type": "skill_choice", "options": ["Leadership", "Tactics (Military)"]}],
        5:  [{"type": "skill_choice", "options": ["Awareness", "Clairvoyance"]}],
        6:  [{"type": "stat", "stat": "SOC", "amount": 1}],
        7:  [],  # Life Event — handled automatically
        8:  [{"type": "skill_check",
              "skills": [{"name": "Melee"}],
              "target": 9,
              "on_pass": [{"type": "extra_benefit", "amount": 1}],
              "on_fail": [{"type": "rival", "desc": "Rival [Enemy Knight]"}],
              "prompt": "Roll Melee 9+ — pass: extra Benefit roll; fail: gain a Rival"}],
        9:  [{"type": "skill_choice", "options": ["Gun Combat", "Recon", "Tactics (Military)"]}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "knight_commander_deed"},
             {"type": "ally", "desc": "Ally [Allied World Hero/Noble]"}],
        12: [{"type": "auto_advance"},
             {"type": "knight_commander_deed"}],
    },
    "storm_knight_inconstant_star": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_choice", "options": ["Astrogation", "Navigation"]},
             {"type": "dm_benefit", "amount": 1}],
        4:  [{"type": "skill_choice", "options": ["Science", "Electronics"]}],
        5:  [{"type": "skill", "name": "Telepathy", "level": 1},
             {"type": "contact", "desc": "Contact [Psionic Confidant]"}],
        6:  [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "d_associates", "kind": "contact", "dice": "D3", "desc_prefix": "Contact [Conclave Delegate]"}],
        7:  [],  # Life Event — handled automatically
        8:  [{"type": "stat", "stat": "EDU", "amount": 1},
             {"type": "extra_benefit", "amount": 1}],
        9:  [{"type": "skill_choice", "options": ["Diplomat", "Persuade"]},
             {"type": "ally", "desc": "Ally [Noble — Diplomatic Crisis]"}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "knight_commander_deed"},
             {"type": "auto_advance"}],
        12: [{"type": "stat", "stat": "EDU", "amount": 2},
             {"type": "knight_commander_deed"}],
    },
    "storm_knight_shadows": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "skill_check",
              "skills": [{"name": "Stealth"}, {"name": "Deception"}],
              "target": 9,
              "on_pass": [{"type": "d_associates", "kind": "contact", "dice": "D3", "desc_prefix": "Contact [Spy Ring Asset]"}],
              "on_fail": [{"type": "injury"}],
              "prompt": "Roll Stealth or Deception 9+ — pass: D3 Contacts; fail: Injury"}],
        4:  [{"type": "skill_choice", "options": ["Recon", "Stealth"]}],
        5:  [{"type": "skill_choice", "options": ["Telepathy", "Awareness"]}],
        6:  [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "dm_benefit", "amount": 1}],
        7:  [],  # Life Event — handled automatically
        8:  [{"type": "contact", "desc": "Contact [Turned Enemy Officer]"},
             {"type": "skill", "name": "Persuade", "level": 1}],
        9:  [{"type": "stat", "stat": "END", "amount": 1}],
        10: [{"type": "dm_advancement", "amount": 2}],
        11: [{"type": "knight_commander_deed"},
             {"type": "auto_advance"}],
        12: [{"type": "knight_commander_deed"},
             {"type": "extra_benefit", "amount": 2}],
    },

    # ---- Psion ----
    "psion": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        # Event 3: Contact or Ally → Rival (interactive choice)
        3:  [{"type": "pending_choice", "id": "psion_event3",
              "prompt": "Your psionic abilities make you uncomfortable to be around. "
                        "Choose a Contact or Ally to become a Rival.",
              "options": []}],  # populated dynamically
        # Event 4: skill choice
        4:  [{"type": "skill_choice",
              "options": ["Athletics 1", "Stealth 1", "Survival 1", "Art 1"],
              "prompt": "Gain one of these skills:"}],
        # Event 5: accept/refuse unethical use (multi-step — first stage sets pending)
        5:  [{"type": "pending_choice", "id": "psion_event5",
              "prompt": "You have a chance to use your powers unethically to better your standing. Accept?",
              "options": [
                  {"id": "accept", "label": "Accept — roll PSI 8+ for reward (success: extra Benefit or SOC+1; fail: SOC−1)"},
                  {"id": "refuse", "label": "Refuse — decline the opportunity"},
              ]}],
        6:  [{"type": "contact", "desc": "Contact [Unexpected Connection]"}],
        7:  [],  # Life Event — auto-handled by text parsing
        # Event 8: PSI +1 (handled via d6_subtable wrapper to avoid text-parser miss)
        8:  [{"type": "stat", "stat": "PSI", "amount": 1}],
        # Event 9: Roll EDU 8+ for any skill except JoaT
        9:  [{"type": "pending_choice", "id": "psion_event9",
              "prompt": "Advanced training — roll EDU 8+ to gain any one skill except Jack-of-all-Trades:",
              "options": [{"id": "roll", "label": "Roll EDU 8+"}]}],
        # Event 10: DM+1 to one Benefit roll
        10: [{"type": "good_fortune_benefit_dm", "amount": 1}],
        # Event 11: Ally + DM+4 to next Advancement
        11: [{"type": "ally", "desc": "Ally [Mentor]"},
             {"type": "dm_next_advancement", "amount": 4}],
        # Event 12: auto-promotion (handled by text parser _AUTO_PROMOTE_RE)
        12: [],
    },
    "truther": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "pending_choice", "id": "truther_event3",
              "prompt": "A body wants to use your knowledge questionably. Agree (extra Benefit + any Science + D3 Enemies) or decline?",
              "options": [
                  {"id": "agree",   "label": "Agree — extra Benefit roll, +1 any Science skill, D3 Enemies"},
                  {"id": "decline", "label": "Decline — no effect"},
              ]}],
        4:  [{"type": "contact", "desc": "Contact [Secret Research Project]"},
             {"type": "dm_benefit", "amount": 1}],
        5:  [{"type": "pending_choice", "id": "truther_event5",
              "prompt": "Crash course — gain 1 level in an Electronics or Science skill you don't already have:",
              "options": [{"id": "pick", "label": "Choose Electronics or Science specialty you don't possess"}]}],
        6:  [{"type": "skill_choice", "options": ["Survival", "Recon"]}],
        7:  [],
        8:  [{"type": "skill_choice", "options": ["Carouse", "Persuade"]},
             {"type": "stat", "stat": "FOL", "amount": 1}],
        9:  [{"type": "pending_choice", "id": "truther_event9",
              "prompt": "Golden opportunity — exploit it (FOL+D3 OR SOC+1 OR 2 skill levels + D3 Enemies) or decline (Ally)?",
              "options": [
                  {"id": "exploit_fol",   "label": "Exploit: FOL +D3 + D3 Enemies"},
                  {"id": "exploit_soc",   "label": "Exploit: SOC +1 + D3 Enemies"},
                  {"id": "exploit_skill", "label": "Exploit: choose Science/Medic/Electronics +2 levels + D3 Enemies"},
                  {"id": "decline",       "label": "Decline: gain an Ally"},
              ]}],
        10: [{"type": "skill_choice", "options": ["Streetwise", "Recon", "Carouse"]},
             {"type": "d_associates", "kind": "contact", "dice": "D3",
              "desc_prefix": "Contact [Mysterious Group]"}],
        11: [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "rival", "desc": "Rival [Public Disagreement]"}],
        12: [{"type": "d_stat", "stat": "FOL", "dice": "D3", "negative": False}],
    },
    "believer": {
        2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],
        3:  [{"type": "stat", "stat": "SOC", "amount": 1},
             {"type": "ally", "desc": "Ally [Community]"}],
        4:  [{"type": "contact", "desc": "Contact [Academic]"}],
        5:  [{"type": "skill_choice", "options": ["Streetwise", "Persuade"]}],
        6:  [{"type": "pending_choice", "id": "believer_event6",
              "prompt": "Retreat from worldly concerns — lose SOC D3, gain D3 Benefit rolls and permanent DM+1 on all future Benefit rolls.",
              "options": [{"id": "retreat", "label": "Accept — SOC −D3, gain D3 Benefit rolls + permanent DM+1 benefits"}]}],
        7:  [],
        8:  [{"type": "skill_choice", "options": ["Carouse", "Persuade"]}],
        9:  [{"type": "pending_choice", "id": "believer_event9",
              "prompt": "Offered inducements to betray your faith. Betray (leave + lose all benefits + Cr2D×10,000 per benefit) or stay loyal (1D Enemies)?",
              "options": [
                  {"id": "betray", "label": "Betray — leave career, lose all benefits, gain cash"},
                  {"id": "loyal",  "label": "Stay loyal — gain 1D Enemies"},
              ]}],
        10: [{"type": "pending_choice", "id": "believer_event10",
              "prompt": "Secretly provide rites for a dying noble not of your faith. Agree (Ally in their household + Rival in your own faith) or refuse?",
              "options": [
                  {"id": "agree",  "label": "Agree — Ally [Noble's Household] + Rival [Own Faith Dissenter]"},
                  {"id": "refuse", "label": "Refuse — no effect"},
              ]}],
        11: [{"type": "permanent_advancement_dm", "amount": -2}],
        12: [{"type": "auto_advance"},
             {"type": "permanent_advancement_dm", "amount": 1}],
    },
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
             "on_pass": [],
             "prompt": "Investigation goes critically wrong — roll Advocate 8+: pass keep Benefit; fail forfeit Benefit; nat-2: must take Prisoner next term"}],
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
        2: [{"type": "enemy", "desc": "Enemy [Kidnapper/Enslaver]"}],
        3: [{"type": "stat_choice", "options": ["STR", "DEX", "END"], "amount": -1}],
        4: [{"type": "rival", "desc": "Rival [Local Criminals/Police]"}],
        # Mishap 5: "Lose all Benefit rolls from this term" — not just one.
        5: [{"type": "forfeit_all_benefits"}],
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
        2: [{"type": "enemy", "desc": "Enemy [Disaster Engagement]"}, {"type": "skill_choice", "options": [], "prompt": "Gain one level of any skill you choose:"}],
        3: [{"type": "stat_choice", "options": ["INT", "SOC"], "amount": -1}],
        4: [{"type": "contact", "desc": "Contact [Fellow Prisoner]"}, {"type": "enemy", "desc": "Enemy [Captors]"}],
        5: [{"type": "rival", "desc": "Rival [Commander]"}],
        6: [{"type": "injury"}],
    },
    "merchant": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "enemy", "desc": "Enemy [Pirates/Corsairs]"}, {"type": "forfeit_all_benefits"}],
        3: [{"type": "forfeit_all_benefits"}],   # "Benefit rolls from this term are forfeit"
        4: [{"type": "rival", "desc": "Rival [Political/Legal Dispute]"}],
        5: [{"type": "forfeit_benefit"}],         # "one less Benefit roll" — single roll only
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
             "on_fail": [{"type": "injury"}], "on_pass": [],
             "prompt": "A disaster or war strikes — roll Stealth or Deception 8+: pass escape unhurt; fail roll on Injury table"}],
        4: [{"type": "skill_choice", "options": ["Diplomat", "Advocate"]}, {"type": "rival", "desc": "Rival [Political Maneuverer]"}],
        5: [{"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_fail": [{"type": "injury"}], "on_pass": [],
             "prompt": "An assassin attempts to end your life — roll END 8+: pass escape unhurt; fail roll on Injury table"}],
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
        3: [{"type": "enemy", "desc": "Enemy [Crime Job]"}, {"type": "forfeit_all_benefits"}],
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
             "on_pass": [], "on_fail": [{"type": "forfeit_benefit"}],
             "prompt": "Political purge sweeps through SolSec — roll END 8+: pass saw it coming (keep Benefit); fail lucky to escape (forfeit Benefit)"}],
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
        5: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "d6_result",
             "ranges": [
                 {"min": 1, "max": 3, "effects": []},
                 {"min": 4, "max": 6, "effects": [
                     {"type": "pending_choice", "id": "party_mishap5_ally",
                      "prompt": "You were tainted by association — a fellow sufferer offers solidarity. Gain them as an Ally?",
                      "options": [
                          {"id": "accept",  "label": "Accept — gain Ally [Fellow Sufferer]"},
                          {"id": "decline", "label": "Decline — no effect"},
                      ]},
                 ]},
             ]}],
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
             "target": 8, "on_pass": [], "on_fail": [{"type": "forfeit_benefit"}],
             "prompt": "Ship's safety hinges on your actions in a crisis — roll Electronics/Gunner/Pilot/Tactics 8+: pass survive; fail forfeit Benefit roll"}],
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
    # ---- Aslan Hierate / Glorious Empire careers ----
    "aslan_ceremonial": {
        1: [{"type": "injury"}],
        2: [{"type": "stat_cap", "stat": "SOC", "cap": 2},
            {"type": "force_next_career", "career_id": "aslan_outcast"}],
        3: [{"type": "skill_choice", "options": ["Survival", "Pilot", "Independence", "Streetwise"]}],
        4: [{"type": "skill_check", "skills": [{"name": "Melee (natural)"}], "target": 8,
             "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1}],
             "on_fail": [{"type": "injury"}],
             "prompt": "Roll Melee 8+ — win the duel (SOC +1) or suffer injury"}],
        5: [{"type": "skill_check", "skills": [{"name": "Advocate"}], "target": 8,
             "on_pass": [{"type": "career_continues"}],
             "on_fail": [],
             "prompt": "Roll Advocate 8+ to stay in the career"}],
        6: [{"type": "rival", "desc": "Rival [Career-Ending Official]"}],
    },
    "aslan_envoy": {
        1: [{"type": "injury"}],
        2: [{"type": "stat_cap", "stat": "SOC", "cap": 2},
            {"type": "force_next_career", "career_id": "aslan_outcast"}],
        3: [{"type": "rival", "desc": "Rival [Other Envoy]"}],
        4: [{"type": "skill_check",
             "skills": [{"name": "Melee (natural)"}, {"name": "Recon"}], "target": 8,
             "on_pass": [{"type": "career_continues"}],
             "on_fail": [{"type": "injury"}],
             "prompt": "Roll Melee (natural) or Recon 8+ to evade the assassin"}],
        5: [{"type": "skill_choice", "options": ["Survival", "Pilot", "Carouse", "Independence"]}],
        6: [{"type": "skill_check", "skills": [{"name": "Tolerance"}], "target": 8,
             "on_pass": [{"type": "career_continues"}],
             "on_fail": [{"type": "enemy", "desc": "Enemy [Human Ambassador's Ally]"}],
             "prompt": "Roll Tolerance 8+ — pass to stay in the career, fail to gain an Enemy"}],
    },
    "aslan_military": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "rival", "desc": "Rival [Superior Officer]"}],
        3: [{"type": "skill_choice", "options": ["Stealth", "Survival", "Streetwise", "Gun Combat"]}],
        4: [{"type": "stat", "stat": "SOC", "amount": -1}],
        5: [{"type": "pending_choice", "id": "aslan_brave_fight",
             "prompt": "Fight bravely (roll Gun Combat or Athletics 8+ to stay) or refuse and leave?",
             "options": [
                 {"id": "fight",  "label": "Fight bravely — roll Gun Combat or Athletics 8+"},
                 {"id": "refuse", "label": "Refuse — accept career ending"},
             ]}],
        6: [{"type": "injury"}],
    },
    "aslan_military_officer": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat_cap", "stat": "SOC", "cap": 2},
            {"type": "force_next_career", "career_id": "aslan_outcast"}],
        3: [{"type": "stat", "stat": "SOC", "amount": -2}],
        4: [{"type": "rival", "desc": "Rival [Foe Who Defeated You]"}],
        5: [{"type": "contact", "desc": "Contact [Rival Clan Member]"}],
        6: [{"type": "injury"}],
    },
    "aslan_spacer": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "rival", "desc": "Rival [Superior Officer]"}],
        3: [{"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "stat", "stat": "END", "amount": -1}],
             "prompt": "Roll END 8+ — fail and lose END -1 from the alien parasite"}],
        4: [{"type": "stat", "stat": "SOC", "amount": -2}],
        5: [{"type": "skill_check", "skills": [{"name": "Tolerance"}], "target": 8,
             "on_pass": [{"type": "career_continues"}, {"type": "forfeit_benefit"}],
             "on_fail": [],
             "prompt": "Roll Tolerance 8+ to stay (losing this term's benefit roll) or be ejected"}],
        6: [{"type": "injury"}],
    },
    "aslan_space_officer": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "skill_check",
             "skills": [{"name": "Advocate"}, {"name": "Melee (natural)"}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "forfeit_benefit"}],
             "prompt": "Roll Advocate or Melee 8+ — pass keeps your Benefit rolls"}],
        3: [{"type": "stat", "stat": "SOC", "amount": -2}],
        4: [{"type": "rival", "desc": "Rival [Foe Who Destroyed Your Vessel]"}],
        5: [{"type": "contact", "desc": "Contact [Rival Clan Member]"}],
        6: [{"type": "injury"}],
    },
    "aslan_management": {
        1: [{"type": "injury"}],
        2: [{"type": "pending_choice", "id": "aslan_mgmt_accused",
             "prompt": "You are accused of stealing from your employer. Is this true?",
             "options": [
                 {"id": "guilty",   "label": "Yes, I stole — gain 3 Benefit rolls, become Outcast (SOC 2)"},
                 {"id": "innocent", "label": "I'm innocent — Roll Advocate 8+ to defend yourself"},
             ]}],
        3: [{"type": "contact", "desc": "Contact [Clan Member Who Stays in Touch]"}],
        4: [{"type": "career_continues"}, {"type": "forfeit_benefit"}],
        5: [{"type": "skill_choice", "options": ["Survival", "Flyer", "Profession", "Navigation"]}],
        6: [{"type": "rival", "desc": "Rival [Clan Elder]"}],
    },
    "aslan_scientist": {
        1: [{"type": "injury"}],
        2: [{"type": "stat", "stat": "END", "amount": -1}],
        3: [{"type": "rival", "desc": "Rival [Other Researcher]"}, {"type": "career_continues"},
            {"type": "forfeit_benefit"}],
        4: [{"type": "skill_choice", "options": ["Survival", "Astrogation", "Mechanic", "Science"]}],
        5: [{"type": "skill_check", "skills": [{"name": "Melee (natural)"}], "target": 8,
             "on_pass": [{"type": "stat", "stat": "SOC", "amount": 1},
                         {"type": "career_continues"}],
             "on_fail": [{"type": "stat", "stat": "SOC", "amount": -2}],
             "prompt": "Roll Melee (natural) 8+ to challenge the elder — pass: SOC +1, stay; fail: SOC -2, leave"}],
        6: [{"type": "pending_choice", "id": "aslan_scientist_leave",
             "prompt": "Your research is cancelled. Leave for human space (auto-qualify for Scholar) or accept career end?",
             "options": [
                 {"id": "leave",  "label": "Leave for human space — auto-qualify for Scholar next term"},
                 {"id": "accept", "label": "Accept career end"},
             ]}],
    },
    "aslan_wanderer": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "skill_choice", "options": ["Survival", "Mechanic", "Animals", "Recon"]}],
        3: [{"type": "stat", "stat": "END", "amount": -1}],
        4: [{"type": "skill_check", "skills": [{"name": "Pilot"}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "injury"}],
             "prompt": "Roll Pilot 8+ to avoid rolling on the Injury table"}],
        5: [{"type": "skill", "name": "Mechanic", "level": 1},
            {"type": "rival", "desc": "Rival [Saboteur ihatei]"}],
        6: [{"type": "injury"}],
    },
    # ---- GE Aslan careers ----
    "ge_fleet": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "rank_loss", "amount": 1}, {"type": "rival", "desc": "Rival [Superior Officer]"},
            {"type": "career_continues"}],
        3: [{"type": "skill_check",
             "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "stat", "stat": "END", "amount": -1}],
             "prompt": "Roll END 8+ — fail and lose END -1 from the alien parasite"}],
        4: [{"type": "stat", "stat": "SOC", "amount": -2},
            {"type": "pending_choice", "id": "ge_forced_career_choice",
             "prompt": "Ejected for smuggling — you may only continue in one of these careers:",
             "options": [
                 {"id": "landless_one", "label": "Landless One"},
                 {"id": "outlaw",       "label": "Outlaw"},
             ]}],
        5: [{"type": "stat", "stat": "SOC", "amount": -1}, {"type": "forfeit_benefit"},
            {"type": "career_continues"}],
        6: [{"type": "injury"}],
    },
    "ge_fleet_officer": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "skill_check",
             "skills": [{"name": "Advocate"}, {"name": "Melee (natural)"}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "forfeit_benefit"}],
             "prompt": "Roll Advocate or Melee 8+ — pass keeps your Benefit rolls"}],
        3: [{"type": "rank_loss", "amount": 1}, {"type": "stat", "stat": "SOC", "amount": -2},
            {"type": "enemy", "desc": "Enemy [Rival Officer]"}, {"type": "career_continues"}],
        4: [{"type": "rival", "desc": "Rival [Hierate Foe]"}, {"type": "career_continues"}],
        5: [{"type": "stat_cap", "stat": "SOC", "cap": 0},
            {"type": "stat_cap", "stat": "TER", "cap": 0},
            {"type": "pending_choice", "id": "ge_hierate_capture",
             "prompt": "Captured and exchanged — return to Empire (Landless One/Outlaw) or stay in Hierate (SOC 2, Contact)?",
             "options": [
                 {"id": "return", "label": "Return to Empire — Landless One or Outlaw career only"},
                 {"id": "stay",   "label": "Stay in Hierate — SOC set to 2, gain a Contact"},
             ]}],
        6: [{"type": "injury"}],
    },
    "ge_warrior": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "rank_loss", "amount": 1}, {"type": "rival", "desc": "Rival [Superior Officer]"},
            {"type": "career_continues"}],
        3: [{"type": "skill_choice", "options": ["Stealth", "Survival", "Streetwise", "Gun Combat"]},
            {"type": "career_continues"}],
        4: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "pending_choice", "id": "ge_forced_career_choice",
             "prompt": "Captured and ransomed — you may only continue in one of these careers:",
             "options": [
                 {"id": "landless_one", "label": "Landless One"},
                 {"id": "outlaw",       "label": "Outlaw"},
             ]}],
        5: [{"type": "pending_choice", "id": "aslan_brave_fight",
             "prompt": "Fight bravely (roll Gun Combat or Athletics 8+ to stay) or refuse and leave?",
             "options": [
                 {"id": "fight",  "label": "Fight bravely — roll Gun Combat or Athletics 8+"},
                 {"id": "refuse", "label": "Refuse — accept career ending"},
             ]}],
        6: [{"type": "injury"}],
    },
    "ge_warrior_officer": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "injury"}, {"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "rank_loss", "amount": 1}, {"type": "stat", "stat": "SOC", "amount": -2},
            {"type": "career_continues"}],
        4: [{"type": "injury"}, {"type": "rival", "desc": "Rival [Foe Who Defeated You]"},
            {"type": "career_continues"}],
        5: [{"type": "pending_choice", "id": "ge_hierate_capture",
             "prompt": "Captured by Hierate — return to Empire (Landless One/Outlaw) or stay in Hierate (SOC 2, Contact)?",
             "options": [
                 {"id": "return", "label": "Return to Empire — Landless One or Outlaw only"},
                 {"id": "stay",   "label": "Stay in Hierate — SOC set to 2, gain a Contact"},
             ]}],
        6: [{"type": "injury"}],
    },
    "ge_landless_one": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "pending_choice", "id": "ge_lose_associate_or_forfeit",
             "prompt": "Your friends desert you. Lose an Ally or Contact, or forfeit your Benefit roll if you have none.",
             "options": []}],  # options populated dynamically
        3: [{"type": "skill_choice", "options": ["Survival", "Mechanic", "Animals", "Recon"]}],
        4: [{"type": "stat", "stat": "END", "amount": -1}],
        5: [{"type": "skill", "name": "Mechanic", "level": 1},
            {"type": "rival", "desc": "Rival [Saboteur]"}],
        6: [{"type": "injury"}],
    },
    "ge_slave": {
        1: [{"type": "injury_severity_choice"}, {"type": "career_continues"}],
        2: [{"type": "enemy", "desc": "Enemy [Rival Slave]"}, {"type": "career_continues"}],
        3: [{"type": "stat", "stat": "END", "amount": -1}],
        4: [{"type": "pending_choice", "id": "ge_slave_revolt",
             "prompt": "You discover an impending slave revolt. Do you report it to your Aslan masters?",
             "options": [
                 {"id": "report", "label": "Report — automatic promotion, gain Enemy [Revolt Leader]"},
                 {"id": "allow",  "label": "Allow it — roll Injury, forced to Prisoner career"},
             ]}],
        5: [{"type": "skill_check",
             "skills": [{"name": "Stealth"}, {"name": "Persuade"}], "target": 8,
             "on_pass": [{"type": "career_continues"}],
             "on_fail": [{"type": "force_next_career", "career_id": "prisoner"}],
             "prompt": "Roll Stealth or Persuade 8+ to escape capture — pass: stay free; fail: Prisoner career next"}],
        6: [{"type": "career_continues"}],
    },

    # ---- Imperial Guard ----
    "imperial_guard": {
        1: [{"type": "injury"}, {"type": "forfeit_benefit"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "rank_adjustment", "amount": -1}, {"type": "career_continues"}],
        4: [{"type": "forfeit_benefit"}],
        5: [{"type": "enemy", "desc": "Enemy [Off-world Contact]"}, {"type": "forfeit_benefit"}],
        6: [{"type": "stat", "stat": "SOC", "amount": -1}],
    },

    # ---- Imperial Naval Intelligence (INI) ----
    "ini": {
        1: [{"type": "injury"}, {"type": "forfeit_benefit"}],
        2: [{"type": "enemy", "desc": "Enemy [Double Agent]"}, {"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "rank_adjustment", "amount": -1}],
        4: [{"type": "forfeit_benefit"}],
        5: [{"type": "career_continues"}],  # "You are extracted — cannot continue in this role"
        6: [{"type": "rival", "desc": "Rival [Intelligence Community]"}],
    },

    # ---- K'kree careers ----
    # Most K'kree mishaps 1-5 say "you do not leave the career" — hence career_continues.
    # Mishap 6 is standard ejection (no career_continues).
    "kkree_pastoral": {
        1: [{"type": "injury"}, {"type": "career_continues"}],
        2: [{"type": "skill", "name": "Outsider", "level": 1},
            {"type": "career_continues"}],
        3: [{"type": "kkree_wife_loss"},
            {"type": "d_associates", "kind": "rival", "dice": "D3", "desc_prefix": "Rival [K'kree — Grief Offence]"},
            {"type": "career_continues"}],
        4: [{"type": "enemy", "desc": "Enemy [Rival Herd]"}, {"type": "career_continues"}],
        5: [{"type": "skill_check", "skills": [{"name": "Melee"}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "stat", "stat": "STR", "amount": -1}],
             "prompt": "Roll Melee 8+ — fail: lose STR -1"},
            {"type": "career_continues"}],
        6: [{"type": "skill", "name": "Outsider", "level": 1}],  # ejected from herd
    },
    "kkree_servant": {
        1: [{"type": "injury"}, {"type": "career_continues"}],
        2: [{"type": "career_continues"}],
        3: [{"type": "rival", "desc": "Rival [K'kree Herdmate]"}, {"type": "career_continues"}],
        4: [{"type": "pending_choice", "id": "kkree_servant_mishap4",
             "prompt": "You are publicly humiliated. Accept with grace or refuse in honour?",
             "options": [
                 {"id": "accept", "label": "Accept — lose SOC −1, gain Ally [Showed Mercy]"},
                 {"id": "refuse", "label": "Refuse — gain Enemy + Outsider 1"},
             ]},
            {"type": "career_continues"}],
        5: [{"type": "stat", "stat": "SOC", "amount": 1}, {"type": "career_continues"}],
        6: [{"type": "skill", "name": "Outsider", "level": 1}],  # ejected from herd
    },
    "kkree_merchant": {
        1: [{"type": "injury"}, {"type": "career_continues"}],
        2: [{"type": "d_stat", "stat": "SOC", "dice": "D3", "negative": True},
            {"type": "career_continues"}],
        3: [{"type": "kkree_wife_loss"},
            {"type": "d_associates", "kind": "rival", "dice": "D3", "desc_prefix": "Rival [K'kree — Grief Offence]"},
            {"type": "career_continues"}],
        4: [{"type": "forfeit_benefit"}, {"type": "rival", "desc": "Rival [Profited from Eclipse]"},
            {"type": "career_continues"}],
        5: [{"type": "skill_check", "skills": [{"name": "Patriarchy"}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
             "prompt": "War kills family — Patriarchy 8+: pass marry quickly (no embarrassment); fail SOC −1"},
            {"type": "career_continues"}],
        6: [{"type": "skill", "name": "Outsider", "level": 1}],  # ejected from herd
    },
    "kkree_noble": {
        1: [{"type": "injury"}, {"type": "career_continues"}],
        2: [{"type": "skill_check", "skills": [{"name": "Patriarchy"}], "target": 10,
             "on_pass": [{"type": "kkree_wife_loss"}],
             "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1},
                         {"type": "kkree_degree_reset"}],
             "prompt": "Revolt in household — Patriarchy 10+: pass dismiss wife (Patriarchy −1 note); "
                       "fail SOC −1 + revert to Servant-of-Rankholder"},
            {"type": "career_continues"}],
        3: [{"type": "skill_check", "skills": [{"name": "Patriarchy"}], "target": 8,
             "on_pass": [{"type": "d_associates", "kind": "enemy", "dice": "D3",
                          "desc_prefix": "Enemy [Vengeance Taken]"}],
             "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1},
                         {"type": "kkree_degree_reset"}],
             "prompt": "Wife killed by enemies — Patriarchy 8+: pass earn respect via vengeance (D3 Enemies); "
                       "fail SOC −1 + revert to Servant-of-Rankholder"},
            {"type": "career_continues"}],
        4: [{"type": "pending_choice", "id": "kkree_noble_mishap4",
             "prompt": "Superior suffers a setback — click to roll 1D and resolve outcome automatically.",
             "options": [{"id": "auto", "label": "Roll 1D to determine outcome"}]}],
        5: [{"type": "d_stat", "stat": "SOC", "dice": "D3", "negative": True},
            {"type": "career_continues"}],
        6: [{"type": "skill", "name": "Outsider", "level": 1}],  # ejected from herd
    },
    "girug_kagh_translator": {
        1: [{"type": "contact", "desc": "Contact [Alien Culture]"}],
        2: [{"type": "enemy", "desc": "Enemy [Foreign Delegation]"}],
        3: [{"type": "injury"}],
        4: [{"type": "contact", "desc": "Contact [Old Patron's Household]"}],
        5: [{"type": "enemy", "desc": "Enemy [Patron's Rivals]"}],
        6: [{"type": "enemy", "desc": "Enemy [K'kree Patron]"}],
    },

    # ---- Bounty Hunter ----
    "bounty_hunter": {
        1: [{"type": "injury_severity_choice"},
            {"type": "stat", "stat": "REP", "amount": -1}],
        2: [{"type": "pending_choice", "id": "bounty_hunter_deal",
             "prompt": "Your mark offers you a deal — accept (lose bounty + REP−1, gain Cr50k) or refuse (Enemy + D3 Enemies + REP−1)?",
             "options": [
                 {"id": "accept", "label": "Accept — lose bounty, REP−1, gain Cr50,000"},
                 {"id": "refuse", "label": "Refuse — Enemy + D3 more Enemies, REP−1"},
             ]}],
        3: [{"type": "skill_check",
             "skills": [{"name": "Broker"}, {"name": "Diplomat"}, {"name": "Persuade"}],
             "target": 8,
             "on_nat2": [],
             "on_pass": [],
             "on_fail": [{"type": "stat", "stat": "REP", "amount": -1}],
             "prompt": "Complicit client — roll Broker/Diplomat/Persuade 8+: fail REP−1"}],
        4: [{"type": "enemy", "desc": "Enemy [Abandoned Contract]"},
            {"type": "stat", "stat": "REP", "amount": -1}],
        5: [{"type": "injury"},
            {"type": "stat", "stat": "REP", "amount": -1}],
        6: [{"type": "pending_choice", "id": "bounty_hunter_rep_or_debt",
             "prompt": "Something went terribly wrong — accept REP hit or take on criminal debt?",
             "options": [
                 {"id": "rep",  "label": "Lose REP −1"},
                 {"id": "debt", "label": "Owe MCr1 to a crime lord (20% annual interest)"},
             ]}],
    },

    # ---- Dolphin Civilian ----
    "dolphin_civilian": {
        1: [{"type": "injury"}],
        2: [],  # political investigation — ejection only, no additional mechanical effect
        3: [{"type": "skill_check",
             "skills": [{"name": "Gun Combat"}, {"name": "Melee"}], "target": 8,
             "on_nat2": [],
             "on_pass": [{"type": "force_next_career", "career_id": "dolphin_military"}],
             "on_fail": [{"type": "force_career_end"}],
             "prompt": "War/insurgency — roll Gun Combat or Melee 8+: pass auto-drafted into Dolphin Military next term; fail exile (ejected from career)"}],
        4: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "enemy", "desc": "Enemy [Purist Political Militant]"}],
        5: [{"type": "stat", "stat": "END", "amount": -2}],
        6: [{"type": "injury"},
            {"type": "skill_check",
             "skills": [{"name": "SOC", "is_stat": True}, {"name": "Advocate"}], "target": 8,
             "on_nat2": [],
             "on_pass": [{"type": "extra_benefit", "amount": 1}],
             "on_fail": [{"type": "forfeit_benefit"}],
             "prompt": "Trapped by fishermen (Injury always) — roll SOC or Advocate 8+: pass extra Benefit (settlement); fail forfeit Benefit"}],
    },

    # ---- Dolphin Military ----
    "dolphin_military": {
        1: [{"type": "injury"}],
        2: [],  # anti-Dolphin prejudice — resigned in disgust, ejection only
        3: [{"type": "pending_choice", "id": "dolphin_mil_massacre",
             "prompt": "Ordered to participate in massacre of indigenous aquatic aliens — refuse (ejected) or participate (Enemy, career continues)?",
             "options": [
                 {"id": "refuse",      "label": "Refuse — ejected from career"},
                 {"id": "participate", "label": "Participate — gain Enemy, career continues"},
             ]}],
        4: [{"type": "stat", "stat": "END", "amount": -2}],
        5: [{"type": "pending_choice", "id": "dolphin_mil_denounce",
             "prompt": "Commander linked to radical faction — denounce them (career continues, Enemy) or stay silent (ejected)?",
             "options": [
                 {"id": "denounce", "label": "Denounce commander — career continues, gain Enemy"},
                 {"id": "silent",   "label": "Stay silent — ejected from career"},
             ]}],
        6: [{"type": "injury"}],
    },

    # ---- Philosopher-Elder (Uplifted Orca) ----
    "philosopher_elder": {
        1: [{"type": "injury"}],
        2: [],  # political investigation (Orca rights) — ejection only, no additional mechanical effect
        3: [{"type": "skill_check",
             "skills": [{"name": "Gun Combat"}, {"name": "Melee"}], "target": 8,
             "on_nat2": [],
             "on_pass": [{"type": "force_next_career", "career_id": "dolphin_military"}],
             "on_fail": [{"type": "force_career_end"}],
             "prompt": "War/insurgency — roll Gun Combat or Melee 8+: pass auto-drafted into Dolphin Military next term; fail exile (ejected from career)"}],
        4: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "enemy", "desc": "Enemy [Purist Political Militant]"}],
        5: [{"type": "stat", "stat": "END", "amount": -2}],
        6: [{"type": "injury"},
            {"type": "skill_check",
             "skills": [{"name": "SOC", "is_stat": True}, {"name": "Advocate"}], "target": 8,
             "on_nat2": [],
             "on_pass": [{"type": "extra_benefit", "amount": 1}],
             "on_fail": [{"type": "forfeit_benefit"}],
             "prompt": "Trapped by fishermen (Injury always) — roll SOC or Advocate 8+: pass extra Benefit (settlement); fail forfeit Benefit"}],
    },

    # ---- Spirit Singer (Orca) ----
    "spirit_singer": {
        1: [{"type": "injury"}],
        2: [{"type": "enemy", "desc": "Enemy [Opponent of the Way]"}],
        3: [{"type": "rank_loss", "amount": 1},
            {"type": "forfeit_benefit"},
            {"type": "career_continues"}],
        4: [{"type": "skill_loss_choice",
             "prompt": "Your training suffered — lose one level in a skill you possess (choose which):"},
            {"type": "career_continues"}],
        5: [{"type": "forfeit_all_benefits"},
            {"type": "career_continues"}],
        6: [{"type": "d_associates", "kind": "rival", "dice": "D3"}],
    },

    # ---- Aslan Outcast ----
    "aslan_outcast": {
        1: [{"type": "injury_severity_choice"}],   # roll twice, take lower (same mechanic)
        2: [{"type": "pending_choice", "id": "ge_lose_associate_or_forfeit",
             "prompt": "Your friends desert you. Lose an Ally or Contact (or forfeit Benefit if you have none)."}],
        3: [{"type": "injury"},
            {"type": "enemy", "desc": "Enemy [Thug Leader]"}],
        4: [{"type": "stat", "stat": "END", "amount": -1}],
        5: [{"type": "forfeit_benefit"}],
        6: [{"type": "injury"}],
    },

    # ---- Aslan Outlaw ----
    "aslan_outlaw": {
        1: [{"type": "injury_severity_choice"}],   # roll twice, take lower
        2: [{"type": "stat", "stat": "END", "amount": -2},
            {"type": "enemy", "desc": "Enemy [Clan Member — captured you]"}],
        3: [{"type": "injury"},
            {"type": "forfeit_benefit"}],
        4: [{"type": "skill_choice",
             "options": ["Deception", "Pilot", "Independence", "Streetwise"]}],
        5: [{"type": "pending_choice", "id": "ge_lose_associate_or_forfeit",
             "prompt": "A friend betrays you. One Ally or Contact becomes a Rival (if none, gain a Rival anyway)."}],
        6: [{"type": "injury"}],
    },

    # ════════════════════════════════════════════════════════════
    # Zhodani Consulate careers
    # ════════════════════════════════════════════════════════════

    # ---- Zhodani Navy ----
    "zhodani_navy": {
        1: [{"type": "injury_severity_choice"}],
        # 2: Frozen watch — injured, then SOC 8+ to stay
        2: [{"type": "injury"},
            {"type": "skill_check",
             "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
             "on_nat2": [],
             "on_fail": [],
             "on_pass": [{"type": "career_continues"}],
             "prompt": "Revived improperly from frozen watch (injury already applied) — roll SOC 8+: pass stay in career; fail leave career"}],
        # 3: Problems with officer — SOC 10+ Rival, else Re-education
        3: [{"type": "zhodani_soc_conditional",
             "if_soc_gte_10": [{"type": "rival", "desc": "Rival [Difficult Officer/Crewman]"}]}],
        # 4: Ship damaged, injured twice lower, but heroism earns extra benefit
        4: [{"type": "injury_severity_choice"},
            {"type": "extra_benefit"}],
        # 5: Serious accident blamed on you — SOC 10+ DM-2 adv + Enemy, else Re-education
        5: [{"type": "zhodani_soc_conditional",
             "if_soc_gte_10": [
                 {"type": "dm_advancement", "amount": -2},
                 {"type": "enemy", "desc": "Enemy [Negligent Crewman Who Blamed You]"},
             ]}],
        6: [{"type": "injury"}],
    },

    # ---- Zhodani Army ----
    "zhodani_army": {
        1: [{"type": "injury_severity_choice"}],
        # 2: Disastrous campaign — D3 Contacts, roll Re-education
        2: [{"type": "d_associates", "kind": "contact", "dice": "D3", "desc_prefix": "Contact [Fellow Veteran]"},
            {"type": "zhodani_re_education"}],
        # 3: Battle against insurgents — gain Recon or Survival, SOC conditional
        3: [{"type": "zhodani_soc_conditional",
             "if_soc_gte_10": [{"type": "enemy", "desc": "Enemy [Government — buried incident]"}]},
            {"type": "skill_choice", "options": ["Recon", "Survival"]}],
        # 4: CO engaged in illegal activity — join (Ally + Re-ed) or cooperate (keep benefit)
        4: [{"type": "pending_choice", "id": "zhodani_army_illegal_co",
             "prompt": "Your CO is engaged in illegal activity. What do you do?",
             "options": [
                 {"id": "join",      "label": "Join the ring — gain an Ally (then roll Re-education Events)"},
                 {"id": "cooperate", "label": "Co-operate with Thought Police — keep Benefit roll, leave career"},
             ]}],
        # 5: Problems with officer — SOC 10+ Rival, else Re-education
        5: [{"type": "zhodani_soc_conditional",
             "if_soc_gte_10": [{"type": "rival", "desc": "Rival [Difficult Officer/Fellow Soldier]"}]}],
        6: [{"type": "injury"}],
    },

    # ---- Zhodani Guard ----
    "zhodani_guard": {
        1: [{"type": "injury_severity_choice"}],
        # 2: Ship self-destruct scramble — DM-2 advancement + Enemy (unconditional)
        2: [{"type": "dm_advancement", "amount": -2},
            {"type": "enemy", "desc": "Enemy [Guard Blaming You For Casualties]"}],
        # 3: Hostile environment insurgents — skill choice + Enemy
        3: [{"type": "enemy", "desc": "Enemy [Local Insurgent Leader]"},
            {"type": "skill_choice", "options": ["Recon", "Survival", "Vacc Suit"]}],
        # 4: Mission against conscience — accept (stay, Enemy) or refuse (Re-education)
        4: [{"type": "pending_choice", "id": "zhodani_guard_conscience",
             "prompt": "You are ordered on a mission against your conscience. What do you do?",
             "options": [
                 {"id": "accept", "label": "Accept mission — stay in Guards but gain Enemy [Lone Survivor]"},
                 {"id": "refuse", "label": "Refuse — roll on Re-education Events table, leave Guards"},
             ]}],
        # 5: Captured and mistreated — Enemy + STR-1 + DEX-1 (keep all benefits from term)
        5: [{"type": "enemy", "desc": "Enemy [Captor]"},
            {"type": "stat", "stat": "STR", "amount": -1},
            {"type": "stat", "stat": "DEX", "amount": -1}],
        6: [{"type": "injury"}],
    },

    # ---- Zhodani Agent ----
    "zhodani_agent": {
        1: [{"type": "injury_severity_choice"}],
        # 2: Investigation goes critically wrong — Advocate 8+ to keep benefit, else Re-education
        2: [{"type": "skill_check",
             "skills": [{"name": "Advocate"}], "target": 8,
             "on_nat2": [],
             "on_pass": [],
             "on_fail": [{"type": "zhodani_re_education"}],
             "prompt": "Investigation goes critically wrong — roll Advocate 8+: pass no further effect; fail undergo Re-education"}],
        # 3: Mission goes wrong — accept fate (extra benefit) or contest (Advocate 8+)
        3: [{"type": "pending_choice", "id": "zhodani_agent_contest",
             "prompt": "A mission goes wrong and you are held responsible. What do you do?",
             "options": [
                 {"id": "accept",  "label": "Accept fate — leave with an extra Benefit roll as compensation"},
                 {"id": "contest", "label": "Contest the accusation — roll Advocate 8+ (pass: stay; fail: Re-education)"},
             ]}],
        # 4: Psychological stress — Re-education
        4: [{"type": "zhodani_re_education"}],
        # 5: Injured in sabotage — injury + Contact in medical field
        5: [{"type": "injury"},
            {"type": "contact", "desc": "Contact [Medical Professional]"}],
        6: [{"type": "injury"}],
    },

    # ---- Zhodani Prole ----
    "zhodani_prole": {
        1: [{"type": "injury_severity_choice"}],
        # 2: Co-worker sabotage — Enemy + Re-education
        2: [{"type": "enemy", "desc": "Enemy [Sabotaging Co-worker]"},
            {"type": "zhodani_re_education"}],
        # 3: Economic hardship — "Lose all Benefit rolls for this term"
        3: [{"type": "forfeit_all_benefits"}],
        # 4: Attack or unusual event — Re-education
        4: [{"type": "zhodani_re_education"}],
        # 5: Family member/lover killed — lose Ally/Contact + Re-education
        5: [{"type": "zhodani_re_education"},
            {"type": "pending_choice", "id": "zhodani_lose_associate",
             "prompt": "A family member or lover is killed. Lose one Ally or Contact.",
             "options": []}],  # options populated dynamically in pending_choice handler
        6: [{"type": "injury"}],
    },

    # ---- Zhodani Government ----
    "zhodani_government": {
        # 1: Error of judgement — discharged in disgrace, forfeit all but one benefit
        1: [{"type": "forfeit_all_benefits_except_one"}],
        # 2: Backfired diplomacy — stay in career but no advancement
        2: [{"type": "career_continues"},
            {"type": "dm_advancement", "amount": -12}],
        # 3: Posting loses diplomatic status — gain Rival, leave
        3: [{"type": "rival", "desc": "Rival [Rival Government/Faction]"}],
        # 4: Assassination attempt — PSI/Melee/Recon 8+ to avoid, fail → injury, pass → stay
        4: [{"type": "skill_check",
             "skills": [{"name": "PSI", "is_stat": True},
                        {"name": "Melee"},
                        {"name": "Recon"}], "target": 8,
             "on_nat2": [],
             "on_fail": [{"type": "injury"}],
             "on_pass": [{"type": "career_continues"}],
             "prompt": "Someone attempts to murder you — roll PSI/Melee/Recon 8+: pass avoid the attempt and stay; fail roll on Injury table"}],
        # 5: Ambassador insult — Diplomat 8+ to avoid; fail → Re-education; pass → extra benefit
        5: [{"type": "skill_check",
             "skills": [{"name": "Diplomat"}], "target": 8,
             "on_nat2": [],
             "on_fail": [{"type": "zhodani_re_education"}],
             "on_pass": [{"type": "extra_benefit"}],
             "prompt": "A foreign ambassador insults you — roll Diplomat 8+: pass extra Benefit roll; fail undergo Re-education"}],
        6: [{"type": "injury"}],
    },

    # ---- Zhodani Merchant ----
    "zhodani_merchant": {
        1: [{"type": "injury_severity_choice"}],
        # 2: Employer bankruptcy — extra benefit for salvaging what you can
        2: [{"type": "extra_benefit"}],
        # 3: Fine — pay (stay) or don't pay (SOC 9- → Re-education)
        3: [{"type": "pending_choice", "id": "zhodani_merchant_fine",
             "prompt": "You are fined Cr1,000×1D for poorly filed paperwork. Pay to stay in career?",
             "options": [
                 {"id": "pay",      "label": "Pay the fine — remain in career"},
                 {"id": "dont_pay", "label": "Refuse to pay — leave career (SOC 9- also rolls Re-education Events)"},
             ]}],
        # 4: Declining fortunes — may continue but no benefits this or next term
        4: [{"type": "pending_choice", "id": "zhodani_merchant_decline",
             "prompt": "Your company faces declining fortunes. Continue in career but forfeit this term's Benefit roll?",
             "options": [
                 {"id": "continue", "label": "Continue — career continues but no Benefit roll this term"},
                 {"id": "leave",    "label": "Leave the career (keep Benefit roll)"},
             ]}],
        # 5: Paid off with Cr1000 × 1D
        5: [{"type": "d_cash", "dice": "1D", "multiplier": 1000}],
        6: [{"type": "injury"}],
    },

    # ---- Zhodani Scholar ----
    "zhodani_scholar": {
        1: [{"type": "injury_severity_choice"}],
        # 2: Disaster — injury table twice higher + Re-education
        2: [{"type": "injury_twice_higher"},
            {"type": "zhodani_re_education"}],
        # 3: Government interference — SOC 9- → Re-education; SOC 10+ → choice openly/secretly
        3: [{"type": "zhodani_soc_conditional",
             "if_soc_gte_10": [
                 {"type": "pending_choice", "id": "zhodani_scholar_research",
                  "prompt": "Government interferes with your research. How do you continue?",
                  "options": [
                      {"id": "openly",   "label": "Continue openly — gain one Science skill level"},
                      {"id": "secretly", "label": "Continue secretly — gain one Science skill level but forfeit Benefit roll"},
                  ]}
             ]}],
        # 4: Stranded expedition — skill choice Survival or Athletics (career ends)
        4: [{"type": "skill_choice", "options": ["Survival", "Athletics"]}],
        # 5: Work sabotaged — give up (leave, keep benefit) or restart (stay, forfeit benefit)
        5: [{"type": "pending_choice", "id": "zhodani_scholar_sabotage",
             "prompt": "Your work is sabotaged by unknown parties. What do you do?",
             "options": [
                 {"id": "give_up", "label": "Give up — leave career, retain this term's Benefit roll"},
                 {"id": "restart", "label": "Start again from scratch — career continues but forfeit all Benefit rolls this term"},
             ]}],
        # 6: Ship crash en route — gain Survival 1, then END 8+ or injury
        6: [{"type": "skill", "name": "Survival", "level": 1},
            {"type": "skill_check",
             "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_nat2": [],
             "on_fail": [{"type": "injury"}],
             "on_pass": [],
             "prompt": "Ship crash en route (Survival 1 gained regardless) — roll END 8+: pass escape unhurt; fail roll on Injury table"}],
    },

    # ---- Zhodani Entertainer ----
    "zhodani_entertainer": {
        # 1: Just injury
        1: [{"type": "injury"}],
        # 2: Art scandal — gain skill, SOC 10+ forced to move, Re-education, but STAY in career
        2: [{"type": "career_continues"},
            {"type": "zhodani_re_education"},
            {"type": "skill_choice", "options": ["Carouse", "Diplomat", "Persuade"]}],
        # 3: Grievous breach — Persuade 8+ to keep benefit, else Re-education
        3: [{"type": "skill_check",
             "skills": [{"name": "Persuade"}], "target": 8,
             "on_nat2": [],
             "on_fail": [{"type": "zhodani_re_education"}],
             "on_pass": [],
             "prompt": "Grievous breach of protocol ruins your career — roll Persuade 8+: pass keep Benefit roll; fail undergo Re-education"}],
        # 4: Contact/Ally betrays you — they become Rival
        4: [{"type": "pending_choice", "id": "mishap_victim",
             "prompt": "One of your Contacts or Allies betrays you, ending your career. Choose who.",
             "options": []}],  # populated dynamically
        # 5: Stranded far from home — D3 Contacts as you return
        5: [{"type": "d_associates", "kind": "contact", "dice": "D3",
             "desc_prefix": "Contact [Met While Stranded]"}],
        # 6: Quarrel with Entertainer — SOC 10+ Rival, else Re-education
        6: [{"type": "zhodani_soc_conditional",
             "if_soc_gte_10": [{"type": "rival", "desc": "Rival [Rival Entertainer]"}]}],
    },

    # ---- Droyne careers ----
    # Mishap 1: combat injury — skill choice + stat loss; continuation check (auto)
    # Mishap 6: always rank −1 (Leader: rank −2)
    "droyne_worker": {
        1: [{"type": "skill_choice", "options": ["Gun Combat", "Melee", "Medic"]},
            {"type": "stat_choice", "options": ["STR", "DEX", "END"], "amount": -2}],
        2: [],  # Junior Leader challenge — narrative, no fixed mechanical effect
        3: [{"type": "pending_choice", "id": "droyne_worker_sacrifice",
             "prompt": "Ordered to make great sacrifices. Behave correctly (−1 each physical stat) or incorrectly (ejected)?",
             "options": [
                 {"id": "correct",   "label": "Behave correctly — lose STR/DEX/END −1 each; continuation check"},
                 {"id": "incorrect", "label": "Behave incorrectly — ejected from Oytrip"},
             ]}],
        4: [],  # Bad things — narrative, continuation check only (auto)
        5: [{"type": "skill", "name": "Outsider", "level": 1},
            {"type": "pending_choice", "id": "droyne_take_streetwise",
             "prompt": "Stranded outside Droyne society. Take Streetwise 1 (a Black Skill)?",
             "options": [
                 {"id": "yes", "label": "Take Streetwise 1 (Black Skill — diminishes you)"},
                 {"id": "no",  "label": "Decline"},
             ]}],
        6: [{"type": "rank_adjustment", "amount": -1}],
    },
    "droyne_warrior": {
        1: [{"type": "skill_choice", "options": ["Gun Combat", "Melee", "Medic"]},
            {"type": "stat_choice", "options": ["STR", "DEX", "END"], "amount": -2}],
        2: [],  # Junior Leader challenge — narrative
        3: [{"type": "pending_choice", "id": "droyne_warrior_sacrifice",
             "prompt": "Warriors took heavy losses. Behave correctly (−1 each physical stat) or betray (ejected)?",
             "options": [
                 {"id": "correct", "label": "Behave correctly — lose STR/DEX/END −1 each; continuation check"},
                 {"id": "betray",  "label": "Betray your role — ejected (or commit ritual suicide)"},
             ]}],
        4: [],  # Bad things — narrative, continuation check only (auto)
        5: [{"type": "skill", "name": "Outsider", "level": 1},
            {"type": "pending_choice", "id": "droyne_take_streetwise",
             "prompt": "Expedition gone wrong. Take Streetwise 1 (a Black Skill)?",
             "options": [
                 {"id": "yes", "label": "Take Streetwise 1 (Black Skill — diminishes you)"},
                 {"id": "no",  "label": "Decline"},
             ]}],
        6: [{"type": "rank_adjustment", "amount": -1}],
    },
    "droyne_drone": {
        1: [{"type": "skill", "name": "Medic", "level": 1},
            {"type": "stat_choice", "options": ["STR", "DEX", "END"], "amount": -2}],
        2: [],  # Prediction/Leadership/Survival situation — narrative, complex
        3: [{"type": "pending_choice", "id": "droyne_drone_sacrifice",
             "prompt": "Get the young to safety: take extraordinary risks (−1 all physical stats) or let others sacrifice?",
             "options": [
                 {"id": "risk",  "label": "Take risks — lose STR/DEX/END −1 each; continuation check"},
                 {"id": "shirk", "label": "Let others sacrifice — rank −1; gain Enemy [Oytrip]"},
             ]}],
        4: [],  # Leadership/Admin check — narrative with continuation check
        5: [{"type": "pending_choice", "id": "droyne_drone_prediction",
             "prompt": "Prediction check (Appeal/Prediction/Admin) 8+ — pass: rank unchanged; fail: rank −1 + Outsider 1",
             "options": [
                 {"id": "pass", "label": "Check passed — no rank change"},
                 {"id": "fail", "label": "Check failed — rank −1 and Outsider 1"},
             ]}],
        6: [{"type": "rank_adjustment", "amount": -1}],
    },
    "droyne_technician": {
        1: [{"type": "skill_choice", "options": ["Gun Combat", "Melee", "Medic"]},
            {"type": "stat_choice", "options": ["STR", "DEX", "END"], "amount": -2}],
        2: [{"type": "rank_adjustment", "amount": -1}],  # Disrupted project — rank −1 (or eject)
        3: [{"type": "pending_choice", "id": "droyne_tech_sacrifice",
             "prompt": "Work under hazardous conditions: behave correctly (−1 all physical) or incorrectly (ejected)?",
             "options": [
                 {"id": "correct",   "label": "Behave correctly — lose STR/DEX/END −1 each; continuation check"},
                 {"id": "incorrect", "label": "Behave incorrectly — ejected from Oytrip"},
             ]}],
        4: [{"type": "pending_choice", "id": "droyne_tech_emergency",
             "prompt": "Emergency repairs — try hardest (−D3 stat, rank+1) or do minimum (no injury, rank−1)?",
             "options": [
                 {"id": "hardest", "label": "Try hardest — lose D3 from a physical stat, but rank+1"},
                 {"id": "minimum", "label": "Do minimum — no injury, but rank−1"},
             ]}],
        5: [{"type": "skill", "name": "Outsider", "level": 1},
            {"type": "pending_choice", "id": "droyne_take_streetwise",
             "prompt": "Expedition gone wrong. Take Streetwise 1 (a Black Skill)?",
             "options": [
                 {"id": "yes", "label": "Take Streetwise 1 (Black Skill — diminishes you)"},
                 {"id": "no",  "label": "Decline"},
             ]}],
        6: [{"type": "rank_adjustment", "amount": -1}],
    },
    "droyne_sport": {
        1: [{"type": "pending_choice", "id": "droyne_sport_attack",
             "prompt": "Attack during negotiations. Appeal 8+ outcome:",
             "options": [
                 {"id": "pass", "label": "Appeal passed — fighting ended quickly; lose −1 from one physical stat"},
                 {"id": "fail", "label": "Appeal failed — lose −1 from each physical stat"},
             ]}],
        2: [{"type": "pending_choice", "id": "droyne_sport_kroyloss",
             "prompt": "Sent to monitor ejected Leader's Kroyloss — return home or begin adventuring?",
             "options": [
                 {"id": "return",    "label": "Try to return: END 8+ — pass: welcome back; fail: INT/EDU/PSI −1 each"},
                 {"id": "adventure", "label": "Begin adventuring now"},
             ]}],
        3: [{"type": "pending_choice", "id": "droyne_sport_expose",
             "prompt": "Expose a Leader's incorrect actions: Appeal 8+?",
             "options": [
                 {"id": "expose", "label": "Expose them — gain Enemy [Kroyloss]; must roll Appeal 8+"},
                 {"id": "fail",   "label": "Failed to deliver in time — rank −1; continuation check"},
             ]}],
        4: [],  # Narrative — go on a quest or be expelled
        5: [{"type": "pending_choice", "id": "droyne_sport_outsider_rescue",
             "prompt": "Outsider 8+ to rescue expedition members:",
             "options": [
                 {"id": "pass", "label": "Outsider passed — no ill effects; gained Contact [Outside Oytrip]"},
                 {"id": "fail", "label": "Outsider failed — rank −1; gained Contact [Outside Oytrip]"},
             ]},
            {"type": "contact", "desc": "Contact [Outside Oytrip]"}],
        6: [{"type": "rank_adjustment", "amount": -1}],
    },
    "droyne_leader": {
        1: [{"type": "pending_choice", "id": "droyne_leader_attack",
             "prompt": "Leadership check 8+ to respond correctly to attack:",
             "options": [
                 {"id": "pass", "label": "Leadership passed — gain Gun Combat/Melee/Tactics"},
                 {"id": "fail", "label": "Leadership failed — lose D3 from a physical stat; continuation check"},
             ]}],
        2: [{"type": "enemy", "desc": "Enemy [Old Oytrip]"}],  # Always ejected; gain Enemy
        3: [{"type": "stat", "stat": "STR", "amount": -1},
            {"type": "stat", "stat": "DEX", "amount": -1},
            {"type": "stat", "stat": "END", "amount": -1},
            {"type": "ally", "desc": "Ally [Oytrip member]"}],
        4: [{"type": "pending_choice", "id": "droyne_leader_outsiders",
             "prompt": "Non-Droyne invaded. Educate them (ejected, gain Ally [Outsider]) or punish (3 Enemies)?",
             "options": [
                 {"id": "educate", "label": "Educate — ejected; gain Ally [Outsider]"},
                 {"id": "punish",  "label": "Punish — gain D3 Enemies [Outsiders]"},
             ]}],
        5: [{"type": "skill", "name": "Outsider", "level": 1},
            {"type": "pending_choice", "id": "droyne_take_streetwise",
             "prompt": "Expedition gone wrong. Take Streetwise 1 (a Black Skill)?",
             "options": [
                 {"id": "yes", "label": "Take Streetwise 1 (Black Skill — diminishes you)"},
                 {"id": "no",  "label": "Decline"},
             ]}],
        6: [{"type": "rank_adjustment", "amount": -2}],  # Leaders: rank −2
    },

    # ---- Hiver Federation careers ----
    # Mishap 1: serious injury (roll-2 equivalent)
    # Mishaps are broadly similar across all 4 Hiver careers
    "hiver_academic": {
        1: [{"type": "injury"}],  # Serious injury (equivalent to roll of 2 on Hiver Injury table)
        2: [{"type": "pending_choice", "id": "hiver_academic_disheartened",
             "prompt": "Repeated failures. RES check — pass: Enemy; fail: lose Benefit rolls equal to negative Effect.",
             "options": [
                 {"id": "pass", "label": "RES check passed — gain Enemy [Thwarted Planner]"},
                 {"id": "fail", "label": "RES check failed — lose Benefit rolls equal to negative Effect"},
             ]}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1}],  # RES (SOC) −1
        4: [{"type": "contact", "desc": "Contact [Mysterious Benefactor — owe a huge favour; become Enemy or Ally]"}],
        5: [],  # Narrative — reputation blackened
        6: [],  # Narrative — nest ceased to exist
    },
    "hiver_generalist": {
        1: [{"type": "injury"}],
        2: [{"type": "pending_choice", "id": "hiver_generalist_threatened",
             "prompt": "Threatened with violence. RES check — pass: Enemy; fail: lose Benefit rolls equal to negative Effect.",
             "options": [
                 {"id": "pass", "label": "RES check passed — gain Enemy [Even More Resentful]"},
                 {"id": "fail", "label": "RES check failed — lose Benefit rolls equal to negative Effect"},
             ]}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1}],
        4: [{"type": "contact", "desc": "Contact [Mysterious Benefactor — owe a huge favour; become Enemy or Ally]"}],
        5: [],  # Narrative
        6: [],  # Narrative
    },
    "hiver_manipulator": {
        1: [{"type": "injury"}],
        2: [{"type": "pending_choice", "id": "hiver_manipulator_disheartened",
             "prompt": "Repeated failures. RES check — pass: Enemy (must leave career); fail: lose RES equal to negative Effect.",
             "options": [
                 {"id": "pass", "label": "RES check passed — gain Enemy; but do NOT have to leave career"},
                 {"id": "fail", "label": "RES check failed — lose RES (SOC) equal to negative Effect"},
             ]}],
        3: [{"type": "stat", "stat": "SOC", "amount": 1},   # RES +1
            {"type": "d_associates", "kind": "rival", "dice": "D3"}],
        4: [{"type": "rival", "desc": "Rival [Manipulator Who Helped — owe enormous favour]"}],
        5: [],  # Narrative — ejected from home nest
        6: [{"type": "d_associates", "kind": "rival", "dice": "D3"}],
    },
    "hiver_merchant": {
        1: [{"type": "injury"}],
        2: [{"type": "pending_choice", "id": "hiver_merchant_disheartened",
             "prompt": "Repeated failures. RES check — pass: Enemy; fail: lose Benefit rolls equal to negative Effect.",
             "options": [
                 {"id": "pass", "label": "RES check passed — gain Enemy [Discrediting Party]"},
                 {"id": "fail", "label": "RES check failed — lose Benefit rolls equal to negative Effect"},
             ]}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1}],
        4: [{"type": "pending_choice", "id": "hiver_merchant_debt",
             "prompt": "Financial sinkhole — in debt MCr2D×1. Mysterious benefactor saves you (stay in career, owe favour) or not?",
             "options": [
                 {"id": "saved",     "label": "Saved — do not leave career; gain Contact [Benefactor — owe favour]"},
                 {"id": "not_saved", "label": "Not saved — still in debt (gain Enemy pursuing you + 10% of debt as cash)"},
             ]}],
        5: [],  # Narrative
        6: [],  # Narrative
    },

    # ================================================================
    # Vargr Extents careers
    # ================================================================

    "vargr_army": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "enemy", "desc": "Enemy [Pack Leader — blamed for casualties]"}],
        3: [{"type": "skill_choice", "options": ["Recon", "Survival"]},
            {"type": "stat", "stat": "SOC", "amount": -1}],
        4: [{"type": "pending_choice", "id": "vargr_army_illegal_leader",
             "prompt": "Your pack leader is involved in weapon/drug smuggling — join their ring (Ally + SOC−1) or testify against them (SOC+1 + Enemy)?",
             "options": [
                 {"id": "join",    "label": "Join ring — gain Ally [Corrupt Pack Leader] + SOC −1"},
                 {"id": "testify", "label": "Testify — gain SOC +1 + Enemy [Reported Pack Leader]"},
             ]}],
        5: [{"type": "stat", "stat": "SOC", "amount": -1}],
        6: [{"type": "injury"}],
    },

    "vargr_citizen": {
        1: [{"type": "injury"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "dm_advancement", "amount": -2}],
        3: [],  # Hard times — career ends; no additional mechanical effect
        4: [{"type": "pending_choice", "id": "vargr_citizen_cooperate",
             "prompt": "The company is suspected of illegal activities — aid the investigation (DM+2 next Qualification) or refuse (gain Ally)?",
             "options": [
                 {"id": "aid",    "label": "Aid investigations — DM+2 to next Qualification roll"},
                 {"id": "refuse", "label": "Refuse — gain Ally [Criminal Company Contact]"},
             ]}],
        5: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 7,
             "on_pass": [],
             "on_fail": [{"type": "dm_qualification", "amount": -2}],
             "prompt": "Roll SOC 7+ to find a new pack — fail: DM−2 to next Qualification roll"}],
        6: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "rival", "desc": "Rival [Power Struggle — Pack Rival]"}],
    },

    "vargr_corsair": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "forfeit_benefit"},
            {"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "pending_choice", "id": "vargr_corsair_betrayal",
             "prompt": "Betrayed by a band member — pick an Ally or Contact in the band to become an Enemy (or gain an Enemy if you have none).",
             "options": []}],  # options populated dynamically
        4: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
             "on_pass": [{"type": "career_continues"}],
             "on_fail": [{"type": "rival", "desc": "Rival [Rival Band Member]"}],
             "prompt": "Pack looks for new leadership — roll SOC 8+ to back the winner: pass stay in career; fail Rival and leave"}],
        5: [{"type": "stat", "stat": "SOC", "amount": -1}],
        6: [{"type": "injury"}],
    },

    "vargr_emissary": {
        1: [{"type": "injury"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "rival", "desc": "Rival [Superior Rival Emissary]"},
            {"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 6,
             "on_pass": [],
             "on_fail": [{"type": "stat", "stat": "SOC", "amount": -1}],
             "prompt": "Outclassed by rival Emissary (Rival gained always) — roll SOC 6+ or also lose SOC −1"}],
        4: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "dm_survival", "amount": -2}],
             "prompt": "Pack power struggle — roll SOC 8+ to back the winner: fail DM−2 to next Survival roll"}],
        5: [{"type": "skill_check", "skills": [{"name": "END", "is_stat": True},
                                                {"name": "Melee (infighting)"}], "target": 8,
             "on_pass": [{"type": "career_continues"}],
             "on_fail": [{"type": "injury"}],
             "prompt": "Assassin attacks — roll END or Melee (infighting) 8+: pass survive and stay in career; fail injury"}],
        6: [{"type": "skill_check", "skills": [{"name": "Broker"}, {"name": "Diplomat"}, {"name": "Persuade"}],
             "target": 10,
             "on_pass": [{"type": "career_continues"},
                         {"type": "rival", "desc": "Rival [Rival Emissary]"}],
             "on_fail": [{"type": "enemy", "desc": "Enemy [Rival Emissary]"}],
             "prompt": "Rival Emissary tries to humiliate you — roll Broker/Diplomat/Persuade 10+: pass stay + Rival; fail Enemy and leave"}],
    },

    "vargr_law_enforcement": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "pending_choice", "id": "vargr_law_deal",
             "prompt": "Criminal under investigation offers you a deal — accept (forced out + SOC−1) or refuse (injury + Enemy)?",
             "options": [
                 {"id": "accept", "label": "Accept deal — forced out of career + SOC −1"},
                 {"id": "refuse", "label": "Refuse — roll on Injury table + gain Enemy [Criminal]"},
             ]}],
        3: [{"type": "skill_check", "skills": [{"name": "Advocate"}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "forfeit_benefit"}, {"type": "stat", "stat": "SOC", "amount": -1}],
             "prompt": "Investigation goes critically wrong — roll Advocate 8+: pass keep Benefit; fail forfeit Benefit + SOC −1"}],
        4: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
             "on_pass": [{"type": "career_continues"}],
             "on_fail": [],
             "prompt": "Pack power struggle — roll SOC 8+ to back the winner: pass stay in career; fail leave"}],
        5: [{"type": "enemy", "desc": "Enemy [Target of Uncovered Information]"},
            {"type": "dm_survival", "amount": -2}],
        6: [{"type": "injury"}],
    },

    "vargr_loner": {
        1: [{"type": "injury"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "enemy", "desc": "Enemy [Rival Loner]"}],
        # Mishap 4: "you may remain in this career but you lose all Benefit rolls"
        4: [{"type": "skill_choice", "options": ["Animals (handling)", "Recon", "Survival"]},
            {"type": "forfeit_all_benefits"},
            {"type": "career_continues"}],
        5: [{"type": "forfeit_all_benefits"},
            {"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 6,
             "on_pass": [],
             "on_fail": [{"type": "injury"}],
             "prompt": "Ambushed by corsairs (all benefits forfeited) — roll END 6+: fail also roll on Injury table"}],
        6: [],  # Gap in memory — no mechanical effect
    },

    "vargr_marines": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "injury"}],
             "prompt": "Captured and tortured (SOC−1 always) — roll END 8+: fail also roll on Injury table"}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "enemy", "desc": "Enemy [Opposing Force / Corsair Band]"}],
        4: [{"type": "skill_choice", "options": ["Stealth", "Survival"]},
            {"type": "stat", "stat": "SOC", "amount": -1}],
        5: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
             "on_pass": [{"type": "career_continues"},
                         {"type": "rival", "desc": "Rival [Contested Pack Leader]"},
                         {"type": "dm_advancement", "amount": -2}],
             "on_fail": [],
             "prompt": "Oppose pack leader — roll SOC 8+: pass stay + Rival + DM−2 Advancement; fail ejected from career"}],
        6: [{"type": "injury"}],
    },

    "vargr_merchant": {
        1: [{"type": "injury"}],
        2: [{"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "injury"}],
             "prompt": "Trade routes blocked by war — roll END 8+: fail roll on Injury table"}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1}],
        4: [{"type": "rival", "desc": "Rival [Rival Merchant Company]"}],
        5: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
             "on_pass": [{"type": "career_continues"},
                         {"type": "rival", "desc": "Rival [Ambitious Employee]"}],
             "on_fail": [{"type": "enemy", "desc": "Enemy [Ambitious Employee — ousted you]"}],
             "prompt": "Employee bids for pack leadership — roll SOC 8+: pass stay + Rival; fail Enemy and lose business"}],
        6: [{"type": "forfeit_all_benefits"}],
    },

    "vargr_navy": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "rival", "desc": "Rival [Competing Pack Member]"}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "enemy", "desc": "Enemy [Opposing Force / Corsair Band]"}],
        4: [{"type": "stat", "stat": "SOC", "amount": -1}],
        5: [{"type": "skill_check", "skills": [{"name": "SOC", "is_stat": True}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "dm_advancement", "amount": -2}],
             "prompt": "Back the losing side in pack power struggle — roll SOC 8+: fail DM−2 next Advancement roll"}],
        6: [{"type": "injury"}],
    },

    "vargr_psion": {
        1: [{"type": "injury"}],
        2: [{"type": "d6_result",
             "ranges": [
                 {"min": 1, "max": 4, "effects": []},
                 {"min": 5, "max": 6, "effects": [{"type": "psi_adjust", "amount": -1}]},
             ]}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "dm_survival", "amount": -2}],
        4: [],  # Arrested and imprisoned — career ends; no extra mechanical effect
        5: [{"type": "rival", "desc": "Rival [Pack Psion Who Won Leadership]"}],
        6: [{"type": "d6_result",
             "ranges": [
                 {"min": 1, "max": 2, "effects": [{"type": "injury"}]},
                 {"min": 3, "max": 4, "effects": [{"type": "psi_adjust", "amount": -1}]},
                 {"min": 5, "max": 6, "effects": []},
             ]}],
    },

    "vargr_scientist": {
        1: [{"type": "injury"}],
        2: [{"type": "stat", "stat": "END", "amount": -1}],
        3: [{"type": "stat", "stat": "SOC", "amount": -1}],
        4: [{"type": "skill", "name": "Survival", "level": 1},
            {"type": "skill_check", "skills": [{"name": "END", "is_stat": True}], "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "injury"}],
             "prompt": "Ship crashed en route (Survival gained always) — roll END 8+: fail also roll on Injury table"}],
        5: [{"type": "pending_choice", "id": "vargr_scientist_funding",
             "prompt": "Employers cancelled your research — stay without benefit (career continues, no benefit roll this term) or roll SOC 8+ to continue with another pack?",
             "options": [
                 {"id": "stay",     "label": "Stay quietly — career continues, forfeit this term's Benefit roll"},
                 {"id": "roll_soc", "label": "Roll SOC 8+ — pass: career continues + Enemy [Former Pack]; fail: forced out"},
             ]}],
        6: [{"type": "rival", "desc": "Rival [Discrediting Scientist]"},
            {"type": "stat", "stat": "SOC", "amount": -1},
            {"type": "dm_survival", "amount": -2}],
    },
    # Storm Knights — only specific mishaps are non-ejecting
    "storm_knight_thunder": {
        1: [{"type": "injury"},
            {"type": "forfeit_benefit"}],
        2: [{"type": "enemy", "desc": "Enemy [Psionic Incident Victim]"},
            {"type": "stat", "stat": "SOC", "amount": -1}],
        3: [{"type": "forfeit_benefit"}],
        4: [{"type": "career_continues"},   # rival sabotages standing — lose rank, stay
            {"type": "rank_loss", "amount": 1}],
        5: [{"type": "forfeit_benefit"},
            {"type": "skill_check",
             "skills": [{"name": "END", "is_stat": True}],
             "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "stat", "stat": "END", "amount": -1}],
             "prompt": "Captured: Roll END 8+ — fail: lose END −1"}],
        6: [{"type": "career_continues"},   # psionic burnout — lose PSI, stay
            {"type": "stat", "stat": "PSI", "amount": -1},
            {"type": "forfeit_benefit"}],
    },
    "storm_knight_inconstant_star": {
        1: [{"type": "forfeit_benefit"},
            {"type": "skill_check",
             "skills": [{"name": "END", "is_stat": True}],
             "target": 8,
             "on_pass": [],
             "on_fail": [{"type": "injury"}],
             "prompt": "Misjump: Roll END 8+ — fail: roll on Injury table"}],
        2: [{"type": "forfeit_benefit"},
            {"type": "pending_choice", "id": "mishap_victim",
             "prompt": "An Ally becomes a Rival — choose which associate turns against you:",
             "options": []}],
        3: [{"type": "career_continues"},   # rival Order claims credit — lose rank, stay
            {"type": "rank_loss", "amount": 1}],
        4: [{"type": "career_continues"},   # stranded — gain Survival 1, lose Benefit, stay
            {"type": "skill", "name": "Survival", "level": 1},
            {"type": "forfeit_benefit"}],
        5: [{"type": "enemy", "desc": "Enemy [Broken Negotiation]"}],
        6: [{"type": "stat", "stat": "EDU", "amount": -1}],
    },
    "storm_knight_shadows": {
        1: [{"type": "injury"},
            {"type": "forfeit_benefit"}],
        2: [{"type": "enemy", "desc": "Enemy [Double Agent]"},
            {"type": "forfeit_benefit"}],
        3: [{"type": "career_continues"},   # psionic scan exposes mission — lose rank, stay
            {"type": "rank_loss", "amount": 1}],
        4: [{"type": "stat", "stat": "END", "amount": -1}],
        5: [{"type": "rival", "desc": "Rival [Order Betrayer]"}],
        6: [{"type": "career_continues"},   # identity burned — lose ALL Benefits + SOC, stay
            {"type": "forfeit_all_benefits"},
            {"type": "stat", "stat": "SOC", "amount": -1}],
    },

    # ---- Psion ----
    "psion": {
        1: [{"type": "injury_severity_choice"}],
        2: [{"type": "stat", "stat": "PSI", "amount": -1}],
        # Mishap 3: anti-psi encounter — roll 1D automatically: 1-2 injury, 3-4 SOC-1, 5-6 nothing
        3: [{"type": "d6_subtable", "ranges": [
                {"min": 1, "max": 2, "effects": [{"type": "injury"}]},
                {"min": 3, "max": 4, "effects": [{"type": "stat", "stat": "SOC", "amount": -1}]},
                {"min": 5, "max": 6, "effects": []},
            ]}],
        # Mishap 4: accept (enemy + NOT ejected) or refuse (ejected)
        4: [{"type": "pending_choice", "id": "psion_mishap4",
             "prompt": "You are asked to use your psionic powers in an unethical fashion. "
                       "Accept and you may continue in this career but gain an Enemy. "
                       "Refuse and you must leave the career.",
             "options": [
                 {"id": "accept", "label": "Accept — gain an Enemy but remain in career (not ejected)"},
                 {"id": "refuse", "label": "Refuse — leave this career"},
             ]}],
        5: [],  # Experimented on — narrative only; ejected by normal mishap flow
        # Mishap 6: a former friend becomes an Enemy (Ally or Contact)
        6: [{"type": "pending_choice", "id": "psion_mishap6",
             "prompt": "Your gift causes a former friend to betray you. "
                       "Choose an Ally or Contact to become an Enemy.",
             "options": []}],  # populated dynamically from character associates
    },
    "truther": {
        1: [{"type": "injury"}],
        2: [{"type": "enemy", "desc": "Enemy [Offended by Truth]"}],
        3: [{"type": "stat", "stat": "SOC", "amount": -2},
            {"type": "d_stat", "stat": "FOL", "dice": "D3", "negative": True},
            {"type": "career_continues"}],
        4: [{"type": "skill_loss_choice",
             "filter": "Science",
             "prompt": "Lose 1 skill level from any Science skill you possess:"},
            {"type": "career_continues"}],
        5: [{"type": "forfeit_all_benefits"},
            {"type": "career_continues"}],
        6: [{"type": "d_associates", "kind": "rival", "dice": "D3",
             "desc_prefix": "Rival [Alienated by Truthing]"}],
    },
    "believer": {
        1: [{"type": "injury"}],
        2: [{"type": "enemy", "desc": "Enemy [Offended by Belief]"}],
        3: [{"type": "rank_loss", "amount": 1},
            {"type": "forfeit_benefit"},
            {"type": "career_continues"}],
        4: [{"type": "pending_choice", "id": "believer_mishap4",
             "prompt": "Lose 1 skill level from Profession (Religion) or Science (Belief) — choose:",
             "options": [
                 {"id": "profession", "label": "Profession (Religion) — lose 1 level"},
                 {"id": "science",    "label": "Science (Belief) — lose 1 level"},
             ]},
            {"type": "career_continues"}],
        5: [{"type": "forfeit_all_benefits"},
            {"type": "career_continues"}],
        6: [{"type": "d_associates", "kind": "rival", "dice": "D3",
             "desc_prefix": "Rival [Splinter Group]"}],
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

    After resolve_injury_choice() the player must call resolve_injury_payment()
    to either accept stat loss (pay=False) or pay medical debt (pay=True).
    """
    r = dice.roll("1D")
    result = _apply_injury_for_result(character, r.total)
    # Override the roll dict with the actual dice roll object
    result["roll"] = r.to_dict()
    return result


def resolve_injury_choice(character: "Character", chosen_stat: str) -> dict:
    """Player has picked which stat absorbs the hit.

    Does NOT apply damage yet. Instead calculates what the stat loss would be
    and what medical treatment would cost (after career coverage), then stores
    the result in pending_injury_treatment_choice so the player can pick:
      • Accept the injury  — stat goes down, no debt.
      • Pay for treatment  — medical debt (career-reduced), stat stays intact.
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
    amount = pending["damage_to_chosen"]
    auto = pending.get("auto_reduce_others", 0)
    others = [s for s in physical if s != chosen_stat]

    # Calculate how many points would be lost (primary + secondaries).
    primary_old = character.characteristics.get(chosen_stat)
    primary_new = max(0, primary_old - amount)
    primary_loss = primary_old - primary_new
    total_loss = primary_loss

    secondary_losses: list[dict] = []
    if auto > 0:
        for stat in others:
            old_v = character.characteristics.get(stat)
            new_v = max(0, old_v - auto)
            loss = old_v - new_v
            total_loss += loss
            secondary_losses.append({"stat": stat, "old": old_v, "new": new_v, "loss": loss})

    # Calculate treatment cost (Cr 5,000/point) with career coverage.
    gross_debt = total_loss * 5000
    medical_bills_info: dict | None = None
    net_debt = 0
    covered = 0
    coverage_pct = 0
    if gross_debt > 0:
        medical_bills_info = _medical_bills_roll(character, gross_debt)
        net_debt = medical_bills_info["remaining"]
        covered = medical_bills_info["covered"]
        coverage_pct = medical_bills_info["coverage_pct"]

    character.pending_injury_treatment_choice = {
        "chosen_stat": chosen_stat,
        "damage_to_chosen": amount,
        "primary_old": primary_old,
        "primary_new": primary_new,
        "primary_loss": primary_loss,
        "auto_reduce_others": auto,
        "secondary_losses": secondary_losses,
        "total_loss": total_loss,
        "gross_debt": gross_debt,
        "net_debt": net_debt,
        "covered": covered,
        "coverage_pct": coverage_pct,
        "medical_bills_roll": medical_bills_info,
        "title": pending.get("title", "Injury"),
    }
    character.pending_injury_choice = None

    return {
        "treatment_choice_pending": True,
        "chosen_stat": chosen_stat,
        "primary_loss": primary_loss,
        "secondary_losses": secondary_losses,
        "total_loss": total_loss,
        "gross_debt": gross_debt,
        "net_debt": net_debt,
        "covered": covered,
        "coverage_pct": coverage_pct,
        "medical_bills_roll": medical_bills_info,
        "character": character.model_dump(),
    }


def resolve_injury_payment(character: "Character", pay: bool) -> dict:
    """Apply the treatment choice.

    pay=True  → add medical debt (net after career coverage); stats stay intact.
    pay=False → reduce stats as calculated; no debt added.
    """
    pending = character.pending_injury_treatment_choice
    if not pending:
        raise ValueError("No pending injury treatment choice to resolve.")

    chosen_stat = pending["chosen_stat"]
    applied: list[str] = []

    if pay:
        net_debt = pending["net_debt"]
        covered = pending["covered"]
        gross_debt = pending["gross_debt"]
        coverage_pct = pending["coverage_pct"]
        character.medical_debt += net_debt
        applied.append(
            f"Treatment paid: Cr{gross_debt:,} gross; career covers "
            f"{coverage_pct}% (Cr{covered:,}); Cr{net_debt:,} added to debt."
        )
        character.log(
            f"Injury ({pending['title']}): paid for treatment — "
            f"Cr{gross_debt:,} gross, Cr{covered:,} covered ({coverage_pct}%), "
            f"Cr{net_debt:,} owed. {chosen_stat} unchanged."
        )
    else:
        # Apply stat loss.
        old = character.characteristics.get(chosen_stat)
        new_val = max(0, old - pending["damage_to_chosen"])
        character.characteristics.set(chosen_stat, new_val)
        applied.append(f"{chosen_stat} {old}→{new_val} (-{old - new_val})")
        for sec in pending.get("secondary_losses", []):
            old_v = character.characteristics.get(sec["stat"])
            new_v = max(0, old_v - pending["auto_reduce_others"])
            character.characteristics.set(sec["stat"], new_v)
            applied.append(f"{sec['stat']} {old_v}→{new_v} (-{old_v - new_v})")
        character.log(
            f"Injury ({pending['title']}): accepted stat loss — "
            + ", ".join(applied) + ". No medical debt."
        )

    character.pending_injury_treatment_choice = None

    return {
        "pay": pay,
        "applied": applied,
        "medical_debt_total": character.medical_debt,
        "character": character.model_dump(),
    }


def end_term(character: Character, leaving: bool = False, reason: str = "voluntary") -> dict:
    """Close out the current term — apply aging if needed, commit the term record."""
    term = character.current_term
    if term is None:
        raise ValueError("No active term")

    # Guard: cannot voluntarily muster out when a mandatory career is pending.
    if leaving and reason == "voluntary" and character.forced_next_career_id:
        forced = character.forced_next_career_id
        raise ValueError(
            f"Cannot muster out: you must serve a term as {forced.capitalize()} first."
        )

    # Guard: a prisoner cannot leave the Prisoner career voluntarily — release
    # only happens via the Parole Threshold check (term.parole_released).
    if leaving and term.career_id == "prisoner" and term.parole_released is not True:
        raise ValueError(
            "You cannot leave the Prisoner career voluntarily — your advancement roll "
            "must exceed your Parole Threshold to be released."
        )

    # Released from prison: clear the Parole Threshold so a future sentence rerolls it.
    if leaving and term.career_id == "prisoner" and term.parole_released:
        character.parole_threshold = None

    character.age += 4
    character.total_terms += 1
    character.term_history.append(term)
    character.failed_qualifications_this_term = 0  # reset for next career-selection round

    aging_log = None
    anagathics_cost_paid = 0
    anagathics_debt = 0
    # Species may have a different aging threshold (e.g. Dolphins age from term 2, Orca from term 4)
    _sp_aging_data = rules.species().get(character.species_id or "", {})
    _aging_starts_term = int(_sp_aging_data.get("aging_starts_term", 4))
    if character.total_terms >= _aging_starts_term:
        # ── Anagathics cost settlement (RAW: 1D×Cr25,000 per term) ────────
        # Costs accrue as medical debt — paid out of eventual muster-out cash.
        if character.anagathics_active and character.anagathics_pending_cost > 0:
            cost = character.anagathics_pending_cost
            character.anagathics_pending_cost = 0
            character.medical_debt += cost
            anagathics_debt = cost
            character.log(
                f"Anagathics cost: Cr{cost:,} added to medical debt "
                "(paid from muster-out cash benefits)."
            )

        # ── Aging roll (anagathics DM already counted — incremented at term start) ──
        if character.anagathics_active:
            character.log(
                f"Aging roll with anagathics DM +{character.anagathics_terms_used}."
            )
        aging_log = _apply_aging(character)

    if leaving:
        # Record career completion
        # Find previous terms in this career to count
        terms_in_career = sum(
            1 for h in character.term_history if h.career_id == term.career_id
        )
        # Benefit rolls = (N per full term) + rank bonus, where N is 1 for standard careers
        # and career.mustering_out_rolls_per_term for careers like Hiver (2 rolls/term).
        _leaving_career = rules.careers().get(term.career_id, {})
        _rolls_per_term = _leaving_career.get("mustering_out_rolls_per_term", 1)
        rank_bonus = _benefit_rolls_from_rank(term.rank)
        # Careers with mustering_out=null explicitly grant no benefit rolls (e.g. kkree_pastoral).
        if _leaving_career.get("mustering_out") is None and "mustering_out" in _leaving_career:
            earned = 0
        else:
            earned = terms_in_career * _rolls_per_term + rank_bonus
        forfeit_note = ""
        if term.benefit_forfeited:
            earned = max(0, earned - 1)
            forfeit_note = " (−1 forfeited by mishap)"
        character.completed_careers.append(
            CareerRecord(
                career_id=term.career_id,
                assignment_id=term.assignment_id,
                terms_served=terms_in_career,
                final_rank=term.rank,
                final_rank_title=term.rank_title,
                commissioned=term.commissioned,
                left_due_to=reason,
                benefit_rolls_earned=earned,
            )
        )
        character.pending_benefit_rolls += earned
        character.current_term = None

        # Storm Knight cross-Order ejection flag: set when ejected by mishap.
        _STORM_KNIGHT_IDS = {"storm_knight_thunder", "storm_knight_inconstant_star", "storm_knight_shadows"}
        if reason == "mishap" and term.career_id in _STORM_KNIGHT_IDS:
            character.storm_knight_ejected = True
            character.log("Storm Knight career ended by mishap — all other Orders are now barred.")

        # Retirement pension (MgT 2e p.53 / Solomani Conf. p.XX).
        # Scout, Rogue, Prisoner, Drifter do not count toward pension eligibility.
        # 9+ qualifying terms earn +Cr2,000 per term beyond 8 (no cap).
        #
        # Solomani Confederation rule: pension is HALF the Imperial rate unless the
        # character served at least one term in the Solomani Party or SolSec, which
        # restores the full pension.
        _SOLOMANI_FULL_PENSION_CAREERS: frozenset[str] = frozenset({"party", "solsec"})
        pension_note = ""
        if term.career_id not in _PENSION_EXEMPT_CAREERS:
            qualifying_terms = sum(
                1 for h in character.term_history
                if h.career_id not in _PENSION_EXEMPT_CAREERS
            )
            new_pension = _pension_for_terms(qualifying_terms)
            # Apply Solomani half-pension rule
            if character.society_id == "solomani_confederation" and new_pension > 0:
                has_full_pension_career = any(
                    h.career_id in _SOLOMANI_FULL_PENSION_CAREERS
                    for h in character.term_history
                    if h.career_id not in _PENSION_EXEMPT_CAREERS
                )
                if not has_full_pension_career:
                    new_pension = new_pension // 2
            old_pension = character.pension_per_year
            character.pension_per_year = new_pension
            if new_pension > 0 and new_pension != old_pension:
                pension_note = (
                    f" Pension updated: Cr{new_pension:,}/year"
                    f" ({qualifying_terms} qualifying terms)."
                )

        # SolSec Monitor rank 3+: one extra benefit roll at final muster-out.
        # IMPORTANT: also credit it to the most recent CareerRecord so the muster-out
        # picker can consume it from that career's table — without this the roll
        # increments pending_benefit_rolls but no career has slots left for it, which
        # permanently blocks the "All Benefits Claimed" screen (and the pension display).
        monitor_bonus_note = ""
        if character.solsec_monitor and character.solsec_monitor_rank >= 3:
            character.pending_benefit_rolls += 1
            if character.completed_careers:
                character.completed_careers[-1].benefit_rolls_earned += 1
            monitor_bonus_note = " SolSec Monitor (rank 3+): +1 extra Benefit roll."

        # Imperial Guard 2+ terms service bonuses:
        # SOC +2, DM+1 on non-cash benefit rolls, doubled material budget, auto TAS Membership.
        ig_service_bonus_note = ""
        if term.career_id == "imperial_guard" and terms_in_career >= 2:
            # SOC +2
            _ig_soc = character.characteristics.get("SOC") or 0
            character.characteristics.set("SOC", _ig_soc + 2)
            character.log(f"Imperial Guard service honour (2+ terms): SOC +2 (now {_ig_soc + 2}).")
            # Benefit DM and doubled budget
            character.imperial_guard_benefit_dm = 1
            character.imperial_guard_doubled_budget = True
            # TAS Membership
            if not character.tas_member:
                character.tas_member = True
                character.log("Imperial Guard service honour (2+ terms): TAS Membership granted automatically.")
            ig_service_bonus_note = (
                f" Imperial Guard: SOC+2, DM+1 on non-cash benefit rolls, "
                f"doubled equipment budget, TAS Membership."
            )
        # Clear the must-leave flag now that they've actually left
        if term.career_id == "imperial_guard":
            character.imperial_guard_must_leave = False

        # INI: grant return-to-Navy token when leaving the career
        if term.career_id == "ini":
            character.ini_can_return_to_navy = True
            character.log(
                "Leaving INI — may return to Navy at held rank without a qualification roll. "
                "Select your Navy career in the career picker to trigger the automatic return."
            )

        character.log(
            f"Left {rules.careers()[term.career_id]['name']} "
            f"({reason}). {terms_in_career} terms served. "
            f"Earns {earned} benefit rolls ({terms_in_career} base + {rank_bonus} rank bonus{forfeit_note}).{pension_note}{monitor_bonus_note}{ig_service_bonus_note}"
        )
    else:
        character.log(f"Completed term {term.overall_term_number}, age now {character.age}.")

    # ── Droyne end-of-term life event check (2D + caste_number ≥ 10) ────────
    # Per Aliens of Charted Space Vol. 2 RAW: at the end of every term roll
    # 2D with the character's caste number as a positive DM. On 10+, a life
    # event occurs (rolled on the Droyne Life Events table).
    droyne_life_event_result: dict | None = None
    if term is not None and term.career_id in rules.DROYNE_CAREER_IDS:
        _caste_num = character.droyne_caste_number or 0
        _det_r = dice.roll("2D")
        _det_total = _det_r.total + _caste_num
        character.log(
            f"Droyne end-of-term check: 2D{_caste_num:+d} = {_det_total} "
            f"{'≥ 10 — Life Event!' if _det_total >= 10 else '< 10 — no life event'}"
        )
        if _det_total >= 10:
            droyne_life_event_result = _apply_droyne_life_event(character)

    # ── K'kree wife acquisition roll (Average 8+ Patriarchy) ─────────────────
    # Each term in a K'kree career the patriarch rolls Patriarchy 8+ to acquire
    # a new wife. Success adds her as an Associate(kind="wife").
    wife_roll_result: dict | None = None
    _sp_data = rules.species().get(character.species_id or "", {})
    if _sp_data.get("uses_kkree_family") and term is not None:
        _pat_level = next(
            (s.level for s in character.skills if s.name.lower() == "patriarchy"),
            0,
        )
        _pat_dm = _pat_level  # Patriarchy is the skill DM directly
        _wife_r = dice.roll("2D", modifier=_pat_dm, target=8)
        _current_wives = sum(1 for a in character.associates if a.kind == "wife")
        if _wife_r.succeeded:
            _wife_label = f"Wife (acquired term {term.overall_term_number})"
            character.associates.append(Associate(kind="wife", description=_wife_label))
            _current_wives += 1
            character.log(
                f"K'kree wife acquisition — Patriarchy {_pat_dm:+d}: "
                f"2D{_pat_dm:+d}={_wife_r.total} ≥ 8 — SUCCESS. "
                f"Now {_current_wives} wife(s)."
            )
        else:
            character.log(
                f"K'kree wife acquisition — Patriarchy {_pat_dm:+d}: "
                f"2D{_pat_dm:+d}={_wife_r.total} < 8 — no new wife this term. "
                f"({_current_wives} wife(s) total)"
            )
        wife_roll_result = {
            "roll": _wife_r.to_dict(),
            "succeeded": _wife_r.succeeded,
            "wives_total": _current_wives,
        }

    # ── Barnai (Floriani) end-of-term Noble obligation check ─────────────────
    # Each term the Barnai rolls 2D. On a straight 12 they must serve one term
    # as Noble before choosing their next career. Only fires when continuing.
    barnai_noble_result: dict | None = None
    if _sp_data.get("barnai_noble_check") and not leaving:
        _barnai_r = dice.roll("2D")
        if _barnai_r.total >= 12:
            character.pending_transfer_career_id = "noble"
            character.log(
                f"Barnai social obligation: 2D={_barnai_r.total} — 12+! "
                f"Must serve one term as Noble before next career."
            )
        else:
            character.log(
                f"Barnai social obligation check: 2D={_barnai_r.total} — no obligation this term."
            )
        barnai_noble_result = {
            "roll": _barnai_r.to_dict(),
            "obligated": _barnai_r.total >= 12,
        }

    # Enforce per-stat characteristic caps at the end of every term.
    # Any stat that has grown above its species cap during this term is reduced.
    _sp_caps_data = rules.species().get(character.species_id or "", {})
    _cap_clamped = _enforce_characteristic_caps(character, _sp_caps_data)
    for msg in _cap_clamped:
        character.log(f"Characteristic cap enforced (end of term): {msg}")

    return {
        "aging": aging_log,
        "anagathics_active": character.anagathics_active,
        "anagathics_terms_used": character.anagathics_terms_used,
        "anagathics_cost_paid": anagathics_cost_paid,
        "anagathics_debt": anagathics_debt,
        "age": character.age,
        "total_terms": character.total_terms,
        "pending_benefit_rolls": character.pending_benefit_rolls,
        "wife_roll": wife_roll_result,
        "droyne_life_event": droyne_life_event_result,
        "barnai_noble": barnai_noble_result,
        "character": character.model_dump(),
    }


# ============================================================
# Phase 3: Aging
# ============================================================


def _apply_aging(character: Character) -> dict:
    """Roll on the aging table: 2D - (multiplier × total_terms) + anagathics_bonus.

    Physical stat reductions are returned as ``pending_reductions`` for the
    player to choose which characteristics to reduce.  Mental reductions are
    applied automatically (random, per RAW).

    Anagathics positive DM: +anagathics_terms_used (RAW p.155).
    Aslan: aging_dm_multiplier=2 → DM = −2 × total_terms (per Aliens of Charted Space 1 p.21).
    """
    _sp_data = rules.species().get(character.species_id or "", {})
    _aging_mult = int(_sp_data.get("aging_dm_multiplier", 1))
    dm = -(_aging_mult * character.total_terms)  # "the older you are, the heavier the effects"
    dm += max(0, character.anagathics_terms_used)
    # Species aging bonus (e.g. Irklan Age Resistance: DM+1). An optional
    # "aging_bonus_dm_until_term" caps how long the bonus applies — the Aezorgh
    # get DM+4 only until age 82 / 16 terms (AoCS Vol.1 Vargr section), after
    # which it no longer helps.
    _aging_bonus = int(_sp_data.get("aging_bonus_dm", 0))
    _aging_bonus_until = _sp_data.get("aging_bonus_dm_until_term")
    if _aging_bonus and (_aging_bonus_until is None or character.total_terms <= int(_aging_bonus_until)):
        dm += _aging_bonus
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
    character: Character, career_id: str, column: str, use_good_fortune: bool = False,
    career_index: Optional[int] = None,
) -> dict:
    """Roll on the mustering-out table (1D), applying the chosen column: cash or benefits."""
    if character.pending_benefit_rolls <= 0:
        raise ValueError("No benefit rolls remaining")
    if column not in ("cash", "benefit"):
        raise ValueError("Column must be 'cash' or 'benefit'")
    if column == "cash" and character.cash_rolls_used >= 3:
        raise ValueError("Cash column maxed out (3 rolls total across all careers)")

    # Aslan male cash restriction: can only consult cash column up to Independence skill level times
    # and receive only half the cash amount.
    _sp_data_muster = rules.species().get(character.species_id or "", {})
    _is_aslan_male = (
        _sp_data_muster.get("uses_clan_shares")
        and character.gender == "male"
    )
    if column == "cash" and _is_aslan_male:
        indep_skill = next((s for s in character.skills if s.name.lower() == "independence"), None)
        indep_level = indep_skill.level if indep_skill else 0
        if character.cash_rolls_used >= indep_level:
            raise ValueError(
                f"Aslan male cash limit: can only roll cash {indep_level} time(s) "
                f"(Independence {indep_level}). Current used: {character.cash_rolls_used}."
            )

    career = rules.careers().get(career_id)
    if career is None:
        raise ValueError(f"Unknown career: {career_id}")
    _mo_raw = career.get("mustering_out")
    if "mustering_out" in career and _mo_raw is None:
        raise ValueError(
            f"{career['name']} grants no mustering-out benefits "
            f"(pastoral/permanent career with no benefit table)."
        )
    table = _mo_raw or {}
    if not table:
        raise ValueError(f"{career['name']} has no mustering-out table encoded yet")

    # Enforce: at most one roll per term served in this career.
    # Prefer the explicit index (disambiguates duplicate stints of the same
    # career_id, e.g. two Bounty Hunter careers); fall back to first match.
    career_rec = None
    if career_index is not None:
        if 0 <= career_index < len(character.completed_careers):
            _rec = character.completed_careers[career_index]
            if _rec.career_id == career_id:
                career_rec = _rec
    if career_rec is None:
        career_rec = next(
            (c for c in character.completed_careers if c.career_id == career_id), None
        )
    if career_rec is None:
        raise ValueError(f"You have no completed terms in {career['name']}")
    max_rolls = career_rec.benefit_rolls_earned or career_rec.terms_served
    if career_rec.benefit_rolls_used >= max_rolls:
        raise ValueError(
            f"Already used all {max_rolls} benefit roll(s) for "
            f"{career['name']} ({max_rolls} total including rank bonus)."
        )

    # Hiver careers use a 2D table with RES (SOC) DM; enforce half-must-be-cash rule.
    _is_hiver_career = career.get("hiver_career", False)
    _muster_dm_char = career.get("mustering_out_dm_characteristic", "")
    _min_cash_fraction = career.get("mustering_out_min_cash_fraction", 0.0)

    # Rank 5-6 bonus: DM+1 to ALL benefit rolls in this career (RAW p.53)
    # (Hiver ranks top at 2, so this never triggers for Hiver)
    dm = 0
    rank_dm = 0
    if career_rec.final_rank >= 5:
        dm += 1
        rank_dm = 1

    # Hiver: add RES (SOC) characteristic DM to every roll
    hiver_res_dm = 0
    if _is_hiver_career and _muster_dm_char:
        _res_val = character.characteristics.get(_muster_dm_char) or 0
        hiver_res_dm = dice.characteristic_dm(_res_val)
        dm += hiver_res_dm

    # Hiver half-cash rule: block cash if already at/above 50% of total rolls
    if _is_hiver_career and _min_cash_fraction > 0 and column == "cash":
        _total_rolls = career_rec.benefit_rolls_earned
        _max_cash = int(_total_rolls * _min_cash_fraction)
        # Cash used for this career = benefit_rolls_used_cash; approximate from global cash_rolls_used
        # (Simple approach: only enforce if we'd exceed 50% — future improvement can track per-career)
        if character.cash_rolls_used >= _max_cash > 0:
            raise ValueError(
                f"Hiver benefit rules: at most {_max_cash} of your {_total_rolls} rolls "
                f"({int(_min_cash_fraction * 100)}%) may be cash rolls. Already used {character.cash_rolls_used}."
            )

    # Gambler bonus on cash rolls (not applicable for Hiver)
    if column == "cash" and not _is_hiver_career:
        if any(s.name.lower() == "gambler" for s in character.skills):
            dm += 1
    # Species cash benefit DM (e.g. Sylean Wealth and Prosperity: DM+1 on all cash rolls)
    _sp_cash_dm = int(_sp_data_muster.get("cash_muster_dm", 0))
    if column == "cash" and _sp_cash_dm:
        dm += _sp_cash_dm
    # Imperial Guard 2+ terms: DM+1 on non-cash benefit rolls
    ig_benefit_dm = 0
    if column == "benefit" and character.imperial_guard_benefit_dm > 0:
        ig_benefit_dm = character.imperial_guard_benefit_dm
        dm += ig_benefit_dm
    dm += character.dm_next_benefit
    pending_dm = character.dm_next_benefit
    character.dm_next_benefit = 0

    # Permanent benefit DM (e.g. Believer event 6)
    if character.permanent_benefit_dm:
        dm += character.permanent_benefit_dm
    # Career benefit roll DM condition (e.g. Truther FOL 10+ → DM+1)
    _fol_dm_cond = career.get("benefit_roll_dm_condition", {})
    if _fol_dm_cond:
        _cond_stat = _fol_dm_cond.get("stat", "")
        _cond_thresh = int(_fol_dm_cond.get("threshold", 999))
        _cond_dm = int(_fol_dm_cond.get("dm", 0))
        if _cond_stat and _get_stat(character, _cond_stat) >= _cond_thresh:
            dm += _cond_dm

    # Good Fortune token (Life Event 10) — voluntary DM+2 on benefit rolls.
    good_fortune_used = False
    if use_good_fortune and character.good_fortune_benefit_dm > 0:
        dm += 2
        character.good_fortune_benefit_dm -= 2
        good_fortune_used = True

    # Roll: 2D for Hiver (table keyed "2"–"12"), 1D for everyone else (keyed "1"–"6"+)
    if _is_hiver_career:
        r = dice.roll("2D", modifier=dm)
        min_row = 2
    else:
        r = dice.roll("1D", modifier=dm)
        min_row = 1
    max_row = max(int(k) for k in table.keys() if k.isdigit())
    key = str(max(min_row, min(max_row, r.total)))
    row = table.get(key)
    if row is None:
        raise ValueError(f"No row for result {key}")

    new_associates: list[dict] = []
    if column == "cash":
        raw_cash_value = row["cash"]
        if raw_cash_value < 0:
            # Negative Hiver cash = debt reduction
            debt_reduction = abs(raw_cash_value)
            actually_reduced = min(debt_reduction, character.medical_debt)
            character.medical_debt = max(0, character.medical_debt - actually_reduced)
            result_text = (
                f"Reduced debt by Cr{actually_reduced:,} "
                f"(Cr{character.medical_debt:,} still owed)"
            )
            character.cash_rolls_used += 1
            character.log(
                f"Muster out (cash)[{r.total}]: Hiver debt reduction Cr{debt_reduction:,}; "
                f"reduced Cr{actually_reduced:,}, Cr{character.medical_debt:,} remaining."
            )
        else:
            gross_cash = raw_cash_value
            # Aslan male: receive only half the cash amount
            aslan_half_note = ""
            if _is_aslan_male:
                gross_cash = gross_cash // 2
                aslan_half_note = " (half, Aslan male)"
            cash = gross_cash
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
                + aslan_half_note
            )
            character.log(
                f"Muster out (cash)[{r.total}]: gross Cr{gross_cash:,}{aslan_half_note}, "
                f"medical Cr{debt_paid:,}, net Cr{cash:,}."
            )
    else:
        benefit = row["benefit"]
        skill_options = _is_skill_choice_benefit(benefit)
        if skill_options:
            # Skill-choice benefit: don't apply yet — let the player pick.
            character.pending_muster_benefit_choice = {
                "options": skill_options,
                "raw": benefit,
            }
            character.log(f"Muster out (benefit)[{r.total}]: {benefit} — PENDING player choice")
        else:
            _assoc_before = len(character.associates)
            _apply_benefit(character, benefit)
            # Surface any associates this benefit added so the UI can offer the
            # same type+name generator used elsewhere in the generator.
            new_associates = [
                {"index": _assoc_before + j, "kind": a.kind, "description": a.description}
                for j, a in enumerate(character.associates[_assoc_before:])
            ]
            character.log(f"Muster out (benefit)[{r.total}]: {benefit}")
        result_text = benefit

    career_rec.benefit_rolls_used += 1
    character.pending_benefit_rolls -= 1
    return {
        "roll": r.to_dict(),
        "result": result_text,
        "remaining_rolls": character.pending_benefit_rolls,
        "rank_dm": rank_dm,
        "ig_benefit_dm": ig_benefit_dm,
        "species_cash_dm": _sp_cash_dm,
        "good_fortune_used": good_fortune_used,
        "good_fortune_remaining": character.good_fortune_benefit_dm,
        "pending_skill_choice": character.pending_muster_benefit_choice,
        "new_associates": new_associates,
        "character": character.model_dump(),
    }


def resolve_muster_benefit_choice(character: Character, chosen: str) -> dict:
    """Resolve a pending mustering-out benefit choice.

    Handles two pending choice types:
      - "skill": classic 'X or Y or ...' benefit — apply chosen as a benefit string.
      - "reroll": rolled-again equipment choice — apply with _is_reroll=True to
        bypass the second-level rolled-again detection.
    """
    pending = character.pending_muster_benefit_choice
    if pending is None:
        raise ValueError("No pending mustering-out benefit choice to resolve.")
    options = pending.get("options", [])
    if chosen not in options:
        raise ValueError(
            f"'{chosen}' is not a valid option. Choose one of: {', '.join(options)}"
        )
    choice_type = pending.get("type", "skill")
    if choice_type == "reroll":
        _apply_benefit(character, chosen, _is_reroll=True)
    else:
        _apply_benefit(character, chosen)
    character.pending_muster_benefit_choice = None
    character.log(f"Muster benefit choice resolved: {chosen}")
    return {
        "chosen": chosen,
        "character": character.model_dump(),
    }


def _apply_benefit(character: Character, benefit: str, _is_reroll: bool = False) -> None:
    """Apply a mustering-out benefit to the character.

    _is_reroll=True suppresses the "rolled again" detection for equipment
    benefits — used when the player has already chosen an option from a
    pending_muster_benefit_choice of type "reroll".
    """
    b = benefit.strip()

    # REP bonus (Bounty Hunter career)
    if b == "REP +1":
        character.reputation += 1
        character.log(f"Muster benefit: REP increased to {character.reputation}.")
        return

    # TER bonuses (Aslan Territory characteristic)
    m_ter = re.match(r"^TER\s*\+(\d+)$", b, re.IGNORECASE)
    if m_ter:
        gain = int(m_ter.group(1))
        current = character.extra_characteristics.get("TER", 0)
        character.extra_characteristics["TER"] = current + gain
        character.log(f"Muster benefit: TER +{gain} (now {current + gain}).")
        return

    # Clan Shares (Aslan — N Clan Shares)
    m_cs = re.match(r"^(\d+)\s+Clan\s+Shares?$", b, re.IGNORECASE)
    if m_cs:
        gained = int(m_cs.group(1))
        character.clan_shares += gained
        character.log(f"Muster benefit: {gained} Clan Share(s) (total {character.clan_shares}).")
        return
    if re.match(r"^1\s+Clan\s+Share$", b, re.IGNORECASE):
        character.clan_shares += 1
        character.log(f"Muster benefit: 1 Clan Share (total {character.clan_shares}).")
        return

    # FOL benefits (Truther)
    if b.lower() == "minor following":
        fol_gain = dice.roll("D3").total
        character.extra_characteristics["FOL"] = character.extra_characteristics.get("FOL", 0) + fol_gain
        character.associates.append(Associate(kind="contact", description="Contact [Minor Following]"))
        character.log(f"Muster benefit: Minor Following — Contact + FOL +{fol_gain} (now {character.extra_characteristics['FOL']}).")
        return
    if b.lower() == "major following":
        fol_gain = dice.roll("1D").total + 1
        character.extra_characteristics["FOL"] = character.extra_characteristics.get("FOL", 0) + fol_gain
        character.associates.append(Associate(kind="ally", description="Ally [Major Following]"))
        character.log(f"Muster benefit: Major Following — Ally + FOL +{fol_gain} (now {character.extra_characteristics['FOL']}).")
        return
    if b.lower() == "patronage":
        character.equipment.append(Equipment(name="Patronage", notes="Cr10,000/year stipend from patron"))
        character.associates.append(Associate(kind="contact", description="Contact [Patron]"))
        character.log("Muster benefit: Patronage — Patron Contact + Cr10,000/year stipend.")
        return
    # "A prominent statue and SOC +1"
    if "prominent statue" in b.lower():
        species_data = rules.species().get(character.species_id, {})
        max_stat = _stat_cap(species_data, "SOC")
        current = character.characteristics.get("SOC")
        character.characteristics.set("SOC", min(current + 1, max_stat))
        character.equipment.append(Equipment(name="Prominent Statue", notes="Public statue — social recognition"))
        character.log(f"Muster benefit: Prominent Statue + SOC +1 (now {character.characteristics.get('SOC')}).")
        return
    if b.lower() == "sainthood candidacy":
        character.equipment.append(Equipment(name="Sainthood Candidacy", notes="Recognized as a sainthood candidate — DM+2 on interactions with members of same belief system"))
        character.log("Muster benefit: Sainthood Candidacy.")
        return
    # "The knowledge that your soul is saved" / "You will be rewarded in the next life" — narrative only
    if "soul is saved" in b.lower() or "next life" in b.lower():
        character.notes.append(f"Muster benefit: {b} (narrative benefit)")
        return

    # Hiver RES +1 = SOC +1 (Resolve is displayed as RES but stored as SOC)
    if b == "RES +1":
        species_data = rules.species().get(character.species_id, {})
        max_stat = species_data.get("characteristic_maximum", 15)
        current = character.characteristics.SOC
        if current < max_stat:
            character.characteristics.set("SOC", current + 1)
            character.log(f"Muster benefit: RES (SOC) +1 (now {current + 1}).")
        return

    # PSI +1 (Droyne, Vargr Psion careers)
    if b == "PSI +1":
        species_data = rules.species().get(character.species_id, {})
        max_stat = species_data.get("characteristic_maximum", 15)
        character.psi = min(character.psi + 1, max_stat)
        character.log(f"Muster benefit: PSI +1 (now {character.psi}).")
        return

    # Hiver debt reduction benefits (amounts match the cash-column negatives in hiver career files:
    #   "Reduce Large Debt" → Cr700,000; "Reduce Small Debt" → Cr70,000)
    if b.lower() == "reduce large debt":
        reduction = 700000
        actually_reduced = min(reduction, character.medical_debt)
        character.medical_debt = max(0, character.medical_debt - actually_reduced)
        character.log(f"Muster benefit: Reduce Large Debt — Cr{actually_reduced:,} off "
                      f"(Cr{character.medical_debt:,} remaining).")
        return
    if b.lower() == "reduce small debt":
        reduction = 70000
        actually_reduced = min(reduction, character.medical_debt)
        character.medical_debt = max(0, character.medical_debt - actually_reduced)
        character.log(f"Muster benefit: Reduce Small Debt — Cr{actually_reduced:,} off "
                      f"(Cr{character.medical_debt:,} remaining).")
        return

    # "D3 Contacts" / "D6 Contacts" — roll dice and add that many contacts
    m_dice_assoc = re.match(r"^(D\d+)\s+(Contact|Ally|Rival|Enemy)s?$", b, re.IGNORECASE)
    if m_dice_assoc:
        dice_expr = m_dice_assoc.group(1).upper()
        kind = m_dice_assoc.group(2).lower()
        count = dice.roll(dice_expr).total
        for _ in range(count):
            character.associates.append(
                Associate(kind=kind, description=f"{kind.capitalize()} [From mustering out]")
            )
        character.log(f"Muster benefit: {dice_expr} {kind.capitalize()}s — rolled {count}.")
        return

    # "D3 Ship Shares" / "D6 Ship Shares"
    m_dice_ss = re.match(r"^(D\d+)\s+[Ss]hip\s+[Ss]hares?$", b, re.IGNORECASE)
    if m_dice_ss:
        dice_expr = m_dice_ss.group(1).upper()
        count = dice.roll(dice_expr).total
        character.ship_shares += count
        character.log(f"Muster benefit: {dice_expr} Ship Shares — rolled {count} (total {character.ship_shares}).")
        return

    # Compound "STAT +N, X or Y" — apply stat first, then add choice to equipment
    m_stat_then_choice = re.match(
        r"^(STR|DEX|END|INT|EDU|SOC|PSI|RES|TER)\s*\+(\d+),\s*(.+)$", b, re.IGNORECASE
    )
    if m_stat_then_choice:
        _apply_benefit(character, m_stat_then_choice.group(1) + " +" + m_stat_then_choice.group(2))
        rest = m_stat_then_choice.group(3).strip()
        # Rest may be "X or Y" — add as equipment choice
        character.equipment.append(Equipment(name=rest, notes="Player choice: pick one (from mustering out compound benefit)"))
        character.log(f"Muster benefit: {m_stat_then_choice.group(1)} +{m_stat_then_choice.group(2)} applied; '{rest}' → player choice")
        return

    # Characteristic bonuses
    for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
        if b == f"{stat} +1":
            species_data = rules.species().get(character.species_id, {})
            max_stat = _stat_cap(species_data, stat)
            current = character.characteristics.get(stat)
            if current < max_stat:
                character.characteristics.set(stat, current + 1)
            else:
                if stat == "SOC":
                    character.ship_shares += 1
            return
        if b == f"{stat} +2":
            species_data = rules.species().get(character.species_id, {})
            max_stat = _stat_cap(species_data, stat)
            for _ in range(2):
                current = character.characteristics.get(stat)
                if current < max_stat:
                    character.characteristics.set(stat, current + 1)
            return

    # Ship shares — handle both digit ("5 Ship Shares") and written-number ("two Ship Shares")
    _word_to_n = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    _m_ss_digit = re.match(r"^(\d+)\s+[Ss]hip\s+[Ss]hares?$", b, re.IGNORECASE)
    if _m_ss_digit:
        character.ship_shares += int(_m_ss_digit.group(1))
        character.log(f"Muster benefit: {_m_ss_digit.group(1)} Ship Share(s) (total {character.ship_shares}).")
        return
    _m_ss_word = re.match(
        r"^(one|two|three|four|five|six|seven|eight|nine|ten)\s+[Ss]hip\s+[Ss]hares?$", b, re.IGNORECASE
    )
    if _m_ss_word:
        n = _word_to_n[_m_ss_word.group(1).lower()]
        character.ship_shares += n
        character.log(f"Muster benefit: {n} Ship Share(s) (total {character.ship_shares}).")
        return
    if re.match(r"^[Ss]hip\s+[Ss]hare$", b, re.IGNORECASE):
        character.ship_shares += 1
        return
    if b == "1D Ship Shares":
        character.ship_shares += dice.roll("1D").total
        return
    if b == "2D Ship Shares":
        character.ship_shares += dice.roll("2D").total
        return

    # Skill grant — "Skill N" or "Skill (Spec) N", e.g. "Advocate 1", "Gun Combat 2"
    if _SKILL_LEVEL_RE.match(b):
        # Split off the trailing integer level
        m_skill = re.match(r"^(.+?)\s+(\d+)$", b)
        if m_skill:
            skill_str = m_skill.group(1).strip()
            level = int(m_skill.group(2))
            sn, spec = _split_skill_speciality(skill_str)
            character.add_skill(sn, level=level, speciality=spec)
            character.log(
                f"Muster benefit skill: {skill_str} → level {level}"
            )
            return

    # Associates — Ally, Contact, Rival, Enemy (with optional leading article: "an Ally", "a Contact")
    b_lower = b.lower()
    # Strip leading article so "a Contact" → "contact", "an Ally" → "ally"
    _b_no_article = re.sub(r"^(?:an?\s+)", "", b_lower).strip()
    if _b_no_article in _BENEFIT_ASSOC_KINDS:
        character.associates.append(
            Associate(kind=_b_no_article, description="From mustering out")
        )
        return

    # "Two Contacts" / "Two Allies" — word-count multi-associate (e.g. vargr_merchant)
    _multi_assoc_m = re.match(
        r"^(two|three|four)\s+(contact|ally|rival|enemy)s?$", b_lower
    )
    if _multi_assoc_m:
        _word_count = {"two": 2, "three": 3, "four": 4}
        _count = _word_count[_multi_assoc_m.group(1)]
        _kind = _multi_assoc_m.group(2)
        for _ in range(_count):
            character.associates.append(
                Associate(kind=_kind, description="From mustering out")
            )
        character.log(f"Muster benefit: {_count} {_kind.capitalize()}s added.")
        return

    # Multi-part "SOC +1 and Yacht" / "Weapon and a Contact" / "Ship Share and an Ally"
    # MUST come before the descriptive-associate regex so "SOC +1 and a Contact" is split
    # correctly rather than being mistaken for a single "contact" benefit.
    if " and " in b:
        for part in b.split(" and "):
            _apply_benefit(character, part.strip())
        return

    # "Aslan Contact", "External Ally" etc — descriptive prefix + associate kind.
    # Safe here because compound " and " benefits are already handled above.
    _desc_assoc_m = re.match(
        r"^(.+?)\s+(contact|ally|rival|enemy)s?$", b_lower
    )
    if _desc_assoc_m:
        _kind = _desc_assoc_m.group(2)
        _desc = b.strip()  # keep original capitalisation for description
        character.associates.append(
            Associate(kind=_kind, description=_desc)
        )
        character.log(f"Muster benefit: {_desc} added as {_kind}.")
        return

    # "X or Y" — if either side is an associate, keep both options visible as a note;
    # if both sides are concrete items, add as equipment with a choice note
    if " or " in b:
        parts = [p.strip() for p in b.split(" or ")]
        # Check if any part is an associate kind
        assoc_parts = [p for p in parts if p.lower() in _BENEFIT_ASSOC_KINDS]
        non_assoc_parts = [p for p in parts if p.lower() not in _BENEFIT_ASSOC_KINDS]
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

    # ============================================================
    # Equipment benefits — proper notes with budget/TL limits and
    # interactive "rolled again" choices via pending_muster_benefit_choice.
    # ============================================================

    # Imperial Guard 2+ terms: doubled equipment budgets
    _ig_db = character.imperial_guard_doubled_budget
    _w_budget   = "Cr6,000"   if _ig_db else "Cr3,000"    # Weapon / Gun
    _bl_budget  = "Cr2,000"   if _ig_db else "Cr1,000"    # Blade
    _ar_budget  = "Cr20,000"  if _ig_db else "Cr10,000"   # Armour
    _ar_up_bud  = "Cr50,000"  if _ig_db else "Cr25,000"   # Armour (upgraded)
    _ci_budget  = "Cr150,000" if _ig_db else "Cr75,000"   # Combat/Cybernetic Implant
    _se_budget  = "Cr4,000"   if _ig_db else "Cr2,000"    # Scientific Equipment

    # TAS Membership — lifetime flag; rolled again → 2 Ship Shares
    if re.match(r'^tas\s+membership$', b, re.IGNORECASE):
        if character.tas_member:
            character.ship_shares += 2
            character.log("Muster benefit: TAS Membership (already a member) → 2 Ship Shares.")
        else:
            character.tas_member = True
            character.log("Muster benefit: TAS Membership — lifetime; Class A&B starport access, high passage every 2 months.")
        return

    # Scout Ship — on detached duty; rolled again → extra benefit roll (book says re-roll)
    if re.match(r'^scout\s+ship$', b, re.IGNORECASE):
        already_has = any(re.match(r'^scout\s+ship$', eq.name, re.IGNORECASE) for eq in character.equipment)
        if already_has and not _is_reroll:
            character.pending_benefit_rolls += 1
            character.log("Muster benefit: Scout Ship (already on detached duty) → 1 extra benefit roll (re-roll rule).")
        else:
            character.equipment.append(Equipment(
                name="Scout Ship",
                notes="On detached duty — still owned by the Scout Service. Expect recall missions. Cannot be sold."
            ))
            character.log("Muster benefit: Scout Ship (detached duty, service obligation).")
        return

    # -- Mortgage ship helpers --
    # Reads the current roll count for a ship from its equipment notes rather
    # than counting entries (there is always exactly one entry after the first roll).
    def _mortgage_rolls(name_pattern: str) -> int:
        for _eq in character.equipment:
            if re.match(name_pattern, _eq.name, re.IGNORECASE):
                if _eq.notes:
                    _m = re.search(r'(\d+) of 4 benefit rolls', _eq.notes)
                    if _m:
                        return int(_m.group(1))
                    if re.search(r'PAID OFF', _eq.notes):
                        return 4
                return 1  # entry exists, notes unparseable → assume 1
        return 0  # no entry

    def _update_mortgage(name_pattern: str, extra_note: str) -> int:
        """Increment and update the mortgage notes for a ship. Returns new roll count."""
        current = _mortgage_rolls(name_pattern)
        new_rolls = current + 1
        for _eq in character.equipment:
            if re.match(name_pattern, _eq.name, re.IGNORECASE):
                if new_rolls >= 4:
                    _eq.notes = f"Mortgage PAID OFF ({new_rolls} benefit rolls).{extra_note}"
                else:
                    _eq.notes = (
                        f"Mortgage: {new_rolls} of 4 benefit rolls paid ({new_rolls * 25}%).{extra_note}"
                    )
                break
        return new_rolls

    # Free Trader — 25% mortgage per roll; 4 rolls = owned; can substitute Far Trader
    if re.match(r'^free\s+trader$', b, re.IGNORECASE):
        _ft_rolls = _mortgage_rolls(r'^free\s+trader$')
        if _ft_rolls == 0:
            character.equipment.append(Equipment(
                name="Free Trader",
                notes="Mortgage: 1 of 4 benefit rolls paid (25%). Can substitute Far Trader. Roll 1D on Spacecraft Quirks."
            ))
            character.log("Muster benefit: Free Trader (1/4 mortgage rolls — 25% paid).")
        else:
            _nr = _update_mortgage(r'^free\s+trader$', " Can substitute Far Trader. Roll 1D on Spacecraft Quirks.")
            character.log(f"Muster benefit: Free Trader ({_nr}/4 rolls — {min(_nr * 25, 100)}% paid).")
        return

    # Lab Ship — 25% mortgage per roll; 4 rolls = owned
    if re.match(r'^lab\s+ship$', b, re.IGNORECASE):
        _ls_rolls = _mortgage_rolls(r'^lab\s+ship$')
        if _ls_rolls == 0:
            character.equipment.append(Equipment(
                name="Lab Ship",
                notes="Mortgage: 1 of 4 benefit rolls paid (25%). Roll 1D on Old Ships."
            ))
            character.log("Muster benefit: Lab Ship (1/4 mortgage rolls — 25% paid).")
        else:
            _nr = _update_mortgage(r'^lab\s+ship$', " Roll 1D on Old Ships.")
            character.log(f"Muster benefit: Lab Ship ({_nr}/4 rolls — {min(_nr * 25, 100)}% paid).")
        return

    # Yacht — 25% mortgage per roll; 4 rolls = owned
    if re.match(r'^yacht$', b, re.IGNORECASE):
        _yt_rolls = _mortgage_rolls(r'^yacht$')
        if _yt_rolls == 0:
            character.equipment.append(Equipment(
                name="Yacht",
                notes="Mortgage: 1 of 4 benefit rolls paid (25%). Roll 1D on Old Ships."
            ))
            character.log("Muster benefit: Yacht (1/4 mortgage rolls — 25% paid).")
        else:
            _nr = _update_mortgage(r'^yacht$', " Roll 1D on Old Ships.")
            character.log(f"Muster benefit: Yacht ({_nr}/4 rolls — {min(_nr * 25, 100)}% paid).")
        return

    # Weapon — any weapon up to Cr3,000 / TL 12 (doubled for Imperial Guard); rolled again → another OR weapon skill
    if re.match(r'^weapon$', b, re.IGNORECASE):
        if not _is_reroll:
            _w_count = sum(1 for eq in character.equipment if re.match(r'^weapon$', eq.name, re.IGNORECASE))
            if _w_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Weapon",
                    "prompt": "You already have a weapon. Choose one:",
                    "options": ["Weapon", "Gun Combat 1", "Melee 1"],
                    "labels": [f"Another weapon ({_w_budget} / TL 12)", "Gun Combat +1", "Melee +1"],
                }
                character.log("Muster benefit: Weapon (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Weapon",
            notes=f"Select any weapon worth up to {_w_budget} at TL 12 or below."
            + (" [2nd weapon]" if _is_reroll else "")
        ))
        character.log(f"Muster benefit: Weapon (select any weapon, up to {_w_budget} / TL 12).")
        return

    # Gun — ranged weapon up to Cr3,000 / TL 12 (doubled for Imperial Guard); rolled again → another OR Gun Combat 1
    if re.match(r'^gun$', b, re.IGNORECASE):
        if not _is_reroll:
            _g_count = sum(1 for eq in character.equipment if re.match(r'^gun$', eq.name, re.IGNORECASE))
            if _g_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Gun",
                    "prompt": "You already have a gun. Choose one:",
                    "options": ["Gun", "Gun Combat 1"],
                    "labels": [f"Another gun ({_w_budget} / TL 12)", "Gun Combat +1"],
                }
                character.log("Muster benefit: Gun (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Gun",
            notes=f"Select any common or military ranged weapon worth up to {_w_budget} at TL 12 or below."
            + (" [2nd gun]" if _is_reroll else "")
        ))
        character.log(f"Muster benefit: Gun (select any ranged weapon, up to {_w_budget} / TL 12).")
        return

    # Blade — any blade up to Cr1,000 / TL 12 (doubled for Imperial Guard); rolled again → another OR Melee (blade) 1
    if re.match(r'^blade$', b, re.IGNORECASE):
        if not _is_reroll:
            _bl_count = sum(1 for eq in character.equipment if re.match(r'^blade$', eq.name, re.IGNORECASE))
            if _bl_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Blade",
                    "prompt": "You already have a blade. Choose one:",
                    "options": ["Blade", "Melee (blade) 1"],
                    "labels": [f"Another blade ({_bl_budget} / TL 12)", "Melee (blade) +1"],
                }
                character.log("Muster benefit: Blade (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Blade",
            notes=f"Select any blade worth up to {_bl_budget} at TL 12 or below."
            + (" [2nd blade]" if _is_reroll else "")
        ))
        character.log(f"Muster benefit: Blade (select any blade, up to {_bl_budget} / TL 12).")
        return

    # Armour (upgraded) — from "rolled again" choice; trade-up budget of Cr25,000 (doubled for Imperial Guard)
    if re.match(r'^armou?r\s*\(upgraded\)$', b, re.IGNORECASE):
        character.equipment.append(Equipment(
            name="Armour (upgraded)",
            notes=f"Rolled again: select armour worth up to {_ar_up_bud} at TL 12 or below."
        ))
        character.log(f"Muster benefit: Armour (upgraded) — trade up to {_ar_up_bud} / TL 12.")
        return

    # Armour — up to Cr10,000 / TL 12 (doubled for Imperial Guard); rolled again → another OR trade up to Cr25,000
    if re.match(r'^armou?r$', b, re.IGNORECASE):
        if not _is_reroll:
            _ar_count = sum(1 for eq in character.equipment if re.match(r'^armou?r$', eq.name, re.IGNORECASE))
            if _ar_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Armour",
                    "prompt": "You already have armour. Choose one:",
                    "options": ["Armour", "Armour (upgraded)"],
                    "labels": [f"Another set of armour ({_ar_budget} / TL 12)", f"Trade up to better armour ({_ar_up_bud} / TL 12)"],
                }
                character.log("Muster benefit: Armour (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Armour",
            notes=f"Select any armour worth up to {_ar_budget} at TL 12 or below."
            + (" [2nd armour]" if _is_reroll else "")
        ))
        character.log(f"Muster benefit: Armour (select any armour, up to {_ar_budget} / TL 12).")
        return

    # Combat Implant (improve) — from "rolled again" choice; upgrade existing (doubled for Imperial Guard)
    if re.match(r'^(combat|cybernetic)\s+implant\s*\(improve\)$', b, re.IGNORECASE):
        character.equipment.append(Equipment(
            name="Combat Implant (improve)",
            notes=f"Rolled again: improve or upgrade an existing augmentation (up to {_ci_budget} budget / TL 12)."
        ))
        character.log(f"Muster benefit: Combat Implant (improve) — upgrade existing augmentation up to {_ci_budget}.")
        return

    # Combat Implant / Cybernetic Implant — up to Cr75,000 / TL 12 (doubled for Imperial Guard); rolled again → another OR improve
    if re.match(r'^(combat|cybernetic)\s+implant$', b, re.IGNORECASE):
        if not _is_reroll:
            _ci_count = sum(
                1 for eq in character.equipment
                if re.match(r'^(combat|cybernetic)\s+implant', eq.name, re.IGNORECASE)
            )
            if _ci_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Combat Implant",
                    "prompt": "You already have a cybernetic implant. Choose one:",
                    "options": ["Combat Implant", "Combat Implant (improve)"],
                    "labels": [
                        f"A different cybernetic implant ({_ci_budget} / TL 12)",
                        f"Improve your existing implant ({_ci_budget} budget / TL 12)",
                    ],
                }
                character.log("Muster benefit: Combat Implant (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Combat Implant",
            notes=f"Select any augmentation (cybernetic implant) worth up to {_ci_budget} at TL 12 or below."
            + (" [2nd implant]" if _is_reroll else "")
        ))
        character.log(f"Muster benefit: Combat Implant (select any augmentation, up to {_ci_budget} / TL 12).")
        return

    # Scientific Equipment — up to Cr2,000 / TL 12; rolled again → another OR Electronics/Science 1
    if re.match(r'^scientific\s+equipment$', b, re.IGNORECASE):
        if not _is_reroll:
            _se_count = sum(1 for eq in character.equipment if re.match(r'^scientific\s+equipment$', eq.name, re.IGNORECASE))
            if _se_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Scientific Equipment",
                    "prompt": "You already have scientific equipment. Choose one:",
                    "options": ["Scientific Equipment", "Electronics 1", "Science 1"],
                    "labels": [f"More scientific equipment ({_se_budget} / TL 12)", "Electronics +1", "Science +1"],
                }
                character.log("Muster benefit: Scientific Equipment (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Scientific Equipment",
            notes=f"Select any scientific equipment worth up to {_se_budget} at TL 12 or below."
            + (" [more equipment]" if _is_reroll else "")
        ))
        character.log(f"Muster benefit: Scientific Equipment (select any, up to {_se_budget} / TL 12).")
        return

    # Personal Vehicle — up to Cr300,000 / TL 10; rolled again → Drive 1 or Flyer 1
    if re.match(r'^personal\s+vehicle$', b, re.IGNORECASE):
        if not _is_reroll:
            _pv_count = sum(1 for eq in character.equipment if re.match(r'^personal\s+vehicle$', eq.name, re.IGNORECASE))
            if _pv_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Personal Vehicle",
                    "prompt": "You already have a personal vehicle. Choose one:",
                    "options": ["Drive 1", "Flyer 1"],
                    "labels": ["Drive +1", "Flyer +1"],
                }
                character.log("Muster benefit: Personal Vehicle (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Personal Vehicle",
            notes="Select any ground car or air/raft worth up to Cr300,000 at TL 10 or below."
        ))
        character.log("Muster benefit: Personal Vehicle (select ground car or air/raft, up to Cr300,000 / TL 10).")
        return

    # Ship's Boat — any small craft up to MCr10 / TL 12; rolled again → Pilot (small craft) 1 or Ship Share
    if re.match(r"^ship'?s\s+boat$", b, re.IGNORECASE):
        if not _is_reroll:
            _sb_count = sum(1 for eq in character.equipment if re.match(r"^ship'?s\s+boat$", eq.name, re.IGNORECASE))
            if _sb_count > 0:
                character.pending_muster_benefit_choice = {
                    "type": "reroll",
                    "benefit": "Ship's Boat",
                    "prompt": "You already have a ship's boat. Choose one:",
                    "options": ["Pilot (small craft) 1", "Ship Share"],
                    "labels": ["Pilot (small craft) +1", "1 Ship Share"],
                }
                character.log("Muster benefit: Ship's Boat (rolled again) — PENDING player choice.")
                return
        character.equipment.append(Equipment(
            name="Ship's Boat",
            notes="Select any small craft worth up to MCr10 at TL 12 or below."
        ))
        character.log("Muster benefit: Ship's Boat (select any small craft, up to MCr10 / TL 12).")
        return

    # Everything else → equipment/reference
    character.equipment.append(Equipment(name=b, notes="From mustering out"))


# ============================================================
# Helpers
# ============================================================


def _officer_rank_table(ranks_data: dict) -> Optional[dict]:
    """Return the officer rank table from a career's ranks dict, handling both
    'officer' (Army/Marine/Navy/Conf-Army/Sol-Marine) and '_officer' (Conf-Navy)."""
    return ranks_data.get("officer") or ranks_data.get("_officer")


def _rank_title(career: dict, assignment_id: str, rank: int,
                commissioned: bool = False) -> Optional[str]:
    """Look up rank title for a career+assignment.

    For commissioned characters the officer rank table is checked first.
    Careers use various key structures:
      - by assignment ("law_enforcement", "intelligence"…)
      - single "default" (Scout)
      - "enlisted" + "officer" / "_officer" (Army / Navy / Marines)
    """
    ranks_data = career.get("ranks", {})
    if commissioned:
        officer_table = _officer_rank_table(ranks_data)
        if officer_table is not None:
            entry = officer_table.get(str(rank))
            return entry.get("title") if entry else None
    rank_table = (
        ranks_data.get(assignment_id)
        or ranks_data.get("default")
        or ranks_data.get("enlisted")
    )
    if rank_table is None:
        return None
    entry = rank_table.get(str(rank))
    return entry.get("title") if entry else None


def _rank_data(career: dict, assignment_id: str, rank: int,
               commissioned: bool = False) -> Optional[dict]:
    """Return the full rank entry dict (title + bonus).

    For commissioned characters the officer rank table is used when present.
    """
    ranks_data = career.get("ranks", {})
    if commissioned:
        officer_table = _officer_rank_table(ranks_data)
        if officer_table is not None:
            return officer_table.get(str(rank))
    rank_table = (
        ranks_data.get(assignment_id)
        or ranks_data.get("default")
        or ranks_data.get("enlisted")
    )
    if rank_table is None:
        return None
    return rank_table.get(str(rank))


def _get_stat(character: "Character", stat: str) -> int:
    """Get a characteristic value by name, handling PSI, RES, TER, and FOL."""
    k = stat.upper()
    if k == "PSI":
        return character.psi
    if k == "RES":
        return character.characteristics.SOC
    if k == "TER":
        return character.extra_characteristics.get("TER", 0)
    if k == "FOL":
        return character.extra_characteristics.get("FOL", 0)
    return character.characteristics.get(k) or 0


def _set_stat(character: "Character", stat: str, value: int) -> None:
    """Set a characteristic value by name, handling PSI, RES, TER, and FOL."""
    k = stat.upper()
    if k == "PSI":
        character.psi = max(0, value)
        return
    if k == "RES":
        character.characteristics.SOC = max(0, value)
        return
    if k == "TER":
        character.extra_characteristics["TER"] = max(0, value)
        return
    if k == "FOL":
        character.extra_characteristics["FOL"] = max(0, value)
        return
    character.characteristics.set(k, value)


def _apply_rank_bonus(character: "Character", bonus_str: str) -> str:
    """Parse and apply a rank-bonus string to the character.

    Handles:
      - "STAT +N"                         e.g. "SOC +2", "TER +2"
      - "STAT -N"                         e.g. "SOC -1"  (penalty)
      - "STAT N"                          e.g. "SOC 15"  (raise to floor)
      - "STAT N or STAT +M"               e.g. "SOC 10 or SOC +1" (floor-or-increment)
      - "STAT N or STAT +M, whichever is higher"
      - "N Clan Shares"                   e.g. "3 Clan Shares" — adds to clan_shares
      - "Contact" / "Ally" / "Rival"      bare associate word — adds that associate
      - "SkillName N"                     e.g. "Gun Combat 1"
      - "Skill (spec) N"                  e.g. "Tactics (military) 1"
      - "Skill N and STAT M"              e.g. "Admin 1 and SOC 10"  (compound via " and ")
      - "Skill N, STAT +M"                e.g. "RES +1, Science (sociology) 1" (compound via ", ")
      - "Skill N and STAT M or STAT +P"   e.g. "Leadership 1 and SOC 8 or SOC +1"
      - "Skill N or Skill2 M"             e.g. "Advocate 1 or Science 1" (auto-pick first)
      - Plain skill name                  e.g. "Jack-of-All-Trades" (treated as level 1)

    Returns a human-readable log string.
    """
    if not bonus_str:
        return "no bonus"
    text = bonus_str.strip()

    # --- Compound "X and Y" bonuses (e.g. "Admin 1 and SOC 10", "TER +2 and SOC 10") ---
    # Split on " and " only when it appears outside parentheses.
    and_pos = -1
    depth = 0
    i = 0
    while i < len(text) - 4:
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and text[i: i + 5] == " and ":
            and_pos = i
            break
        i += 1
    if and_pos >= 0:
        part1 = text[:and_pos].strip()
        part2 = text[and_pos + 5:].strip()
        log1 = _apply_rank_bonus(character, part1)
        log2 = _apply_rank_bonus(character, part2)
        return f"{log1}; {log2}"

    # --- Compound "X, Y" bonuses (e.g. "RES +1, Science (sociology) 1") ---
    # Split on ", " outside parentheses.
    comma_pos = -1
    depth = 0
    i = 0
    while i < len(text) - 1:
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and text[i: i + 2] == ", ":
            comma_pos = i
            break
        i += 1
    if comma_pos >= 0:
        part1 = text[:comma_pos].strip()
        part2 = text[comma_pos + 2:].strip()
        log1 = _apply_rank_bonus(character, part1)
        log2 = _apply_rank_bonus(character, part2)
        return f"{log1}; {log2}"

    # "STAT N or STAT +M" — floor-or-increment (with optional trailing text)
    _STAT_PAT = r"(SOC|STR|DEX|END|INT|EDU|PSI|RES|TER)"
    m_complex = re.match(
        rf"^{_STAT_PAT}\s+(\d+)\s+or\s+\1\s*\+(\d+)",
        text, re.IGNORECASE
    )
    if m_complex:
        stat = m_complex.group(1).upper()
        floor_val = int(m_complex.group(2))
        bonus_n = int(m_complex.group(3))
        current = _get_stat(character, stat)
        new_val = max(floor_val, current + bonus_n)
        _set_stat(character, stat, new_val)
        return f"{stat} {current}→{new_val} (rank bonus)"

    # "REP +N" — reputation characteristic used by Bounty Hunter career
    m_rep = re.match(r"^REP\s*\+(\d+)$", text, re.IGNORECASE)
    if m_rep:
        n = int(m_rep.group(1))
        old_rep = character.reputation
        character.reputation += n
        return f"REP {old_rep}→{character.reputation} (rank bonus)"

    # "BOL +N" — Za'tachk Boldness characteristic
    m_bol = re.match(r"^BOL\s*\+(\d+)$", text, re.IGNORECASE)
    if m_bol:
        n = int(m_bol.group(1))
        old_bol = character.boldness
        character.boldness += n
        return f"BOL {old_bol}→{character.boldness} (rank bonus)"

    # "STAT +N" or "STAT+N" (positive increment, includes TER and FOL)
    m_stat = re.match(r"^(STR|DEX|END|INT|EDU|SOC|PSI|RES|TER|FOL)\s*\+(\d+)$", text, re.IGNORECASE)
    if m_stat:
        stat = m_stat.group(1).upper()
        n = int(m_stat.group(2))
        if stat == "FOL":
            old = character.extra_characteristics.get("FOL", 0)
            character.extra_characteristics["FOL"] = old + n
            return f"FOL {old}→{old + n} (rank bonus)"
        if stat == "TER":
            old = character.extra_characteristics.get("TER", 0)
            character.extra_characteristics["TER"] = old + n
            return f"TER {old}→{old + n} (rank bonus)"
        species_data = rules.species().get(character.species_id, {})
        max_stat = _stat_cap(species_data, stat)
        current = _get_stat(character, stat)
        new_val = min(max_stat, current + n)
        _set_stat(character, stat, new_val)
        return f"{stat} {current}→{new_val} (rank bonus)"

    # "STAT -N" — stat penalty (e.g. "SOC -1" for Prisoner rank 6)
    m_stat_neg = re.match(r"^(STR|DEX|END|INT|EDU|SOC|PSI|RES|TER|FOL)\s*-(\d+)$", text, re.IGNORECASE)
    if m_stat_neg:
        stat = m_stat_neg.group(1).upper()
        n = int(m_stat_neg.group(2))
        if stat == "FOL":
            old = character.extra_characteristics.get("FOL", 0)
            new_val = max(0, old - n)
            character.extra_characteristics["FOL"] = new_val
            return f"FOL {old}→{new_val} (rank penalty)"
        if stat == "TER":
            old = character.extra_characteristics.get("TER", 0)
            new_val = max(0, old - n)
            character.extra_characteristics["TER"] = new_val
            return f"TER {old}→{new_val} (rank penalty)"
        current = _get_stat(character, stat)
        new_val = max(0, current - n)
        _set_stat(character, stat, new_val)
        return f"{stat} {current}→{new_val} (rank penalty)"

    # "STAT N" — raise stat to floor value (e.g. "SOC 15")
    m_stat_floor = re.match(r"^(STR|DEX|END|INT|EDU|SOC|PSI|RES|TER)\s+(\d+)$", text, re.IGNORECASE)
    if m_stat_floor:
        stat = m_stat_floor.group(1).upper()
        floor_val = int(m_stat_floor.group(2))
        if stat == "TER":
            old = character.extra_characteristics.get("TER", 0)
            new_val = max(floor_val, old)
            character.extra_characteristics["TER"] = new_val
            return f"TER {old}→{new_val} (floor {floor_val})"
        current = _get_stat(character, stat)
        new_val = max(floor_val, current)
        _set_stat(character, stat, new_val)
        return f"{stat} {current}→{new_val} (floor {floor_val})"

    # "N Clan Shares" or "N Clan Share" — Aslan/GE career rank reward
    m_clan = re.match(r"^(\d+)\s+Clan\s+Shares?$", text, re.IGNORECASE)
    if m_clan:
        n = int(m_clan.group(1))
        character.clan_shares = (character.clan_shares or 0) + n
        return f"Gained {n} Clan Share{'s' if n != 1 else ''} (total: {character.clan_shares})"

    # Bare associate words — "Contact", "Ally", "Rival", "Enemy"
    bare_assoc = re.match(r"^(Contact|Ally|Rival|Enemy)$", text, re.IGNORECASE)
    if bare_assoc:
        kind = bare_assoc.group(1).lower()
        character.associates.append(Associate(kind=kind, description=f"{kind.capitalize()} [Rank bonus]"))
        return f"Gained {kind.capitalize()} [Rank bonus]"

    # "Skill N (male) or Skill2 M (female)" — gender-conditional rank bonus
    _gc_rank_m = re.match(
        r"^(.+?)\s+(\d+)\s*\((?:if\s+)?male\)\s+or\s+(.+?)\s+(\d+)\s*\((?:if\s+)?female\)\s*$",
        text, re.IGNORECASE
    )
    if _gc_rank_m:
        gender = (character.gender or "").lower()
        if gender == "female":
            return _apply_rank_bonus(character, f"{_gc_rank_m.group(3)} {_gc_rank_m.group(4)}")
        else:
            return _apply_rank_bonus(character, f"{_gc_rank_m.group(1)} {_gc_rank_m.group(2)}")

    # "Skill N or Skill2 M" — player choice; auto-pick the first option
    # Only trigger when "or" appears outside parentheses and neither side is a handled stat pattern.
    or_pos = -1
    depth = 0
    i = 0
    while i < len(text) - 3:
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and text[i: i + 4] == " or ":
            or_pos = i
            break
        i += 1
    if or_pos >= 0:
        # Collect ALL top-level "or" options and present a pending player choice.
        # Previously this auto-picked the first option without player input.
        _rb_parts: list[str] = []
        _rb_cur = 0
        _rb_depth = 0
        for _rbi, _rbc in enumerate(text):
            if _rbc == "(":
                _rb_depth += 1
            elif _rbc == ")":
                _rb_depth -= 1
            elif _rb_depth == 0 and text[_rbi: _rbi + 4] == " or ":
                _rb_parts.append(text[_rb_cur:_rbi].strip())
                _rb_cur = _rbi + 4
        _rb_parts.append(text[_rb_cur:].strip())
        _rb_parts = [p for p in _rb_parts if p]
        if len(_rb_parts) == 1:
            return _apply_rank_bonus(character, _rb_parts[0])
        character.pending_career_event_choice = {
            "type": "skill_choice",
            "options": _rb_parts,
            "prompt": f"Rank bonus: choose one of: {' / '.join(_rb_parts)}",
        }
        return f"Rank bonus: {bonus_str} — choice pending"

    # "Skill (spec) N" or "Skill N" or plain "Skill"
    # Try to strip a trailing digit as the level
    level = 1
    m_level = re.search(r"\s+(\d+)\s*$", text)
    if m_level:
        level = int(m_level.group(1))
        text = text[: m_level.start()].strip()

    name, speciality = _split_skill_speciality(text)
    # "(any)" is not a real speciality — create a pending choice for the player
    if speciality and speciality.lower() == "any":
        _spec_list = rules.skill_specialities().get(name, [])
        if _spec_list:
            character.pending_career_event_choice = {
                "type": "skill_choice",
                "options": [f"{name} ({s})" for s in _spec_list],
                "prompt": f"Rank bonus: choose a {name} speciality to gain at level {level}:",
            }
            return f"Rank bonus: {name} (any) {level} — speciality choice pending"
        else:
            speciality = None  # no specialities known — add base skill
    # "Skill (A or B)" — speciality is a choice between two options
    elif speciality and " or " in speciality:
        _spec_options = [s.strip() for s in speciality.split(" or ") if s.strip()]
        character.pending_career_event_choice = {
            "type": "skill_choice",
            "options": [f"{name} ({s})" for s in _spec_options],
            "prompt": f"Rank bonus: choose a {name} speciality ({speciality}) to gain at level {level}:",
        }
        return f"Rank bonus: {name} ({speciality}) {level} — speciality choice pending"
    applied_msg = character.add_skill(name, level=level, speciality=speciality, fixed_level=True)
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

    # Associate grants from skill tables ("Contact", "Ally")
    if stripped == "Contact":
        character.associates.append(Associate(kind="contact", description="Met during career"))
        return "Gained a Contact"
    if stripped == "Ally":
        character.associates.append(Associate(kind="ally", description="Met during career"))
        return "Gained an Ally"

    # FOL +N (Truther Following characteristic)
    m_fol_sr = re.match(r"^FOL\s*\+(\d+)$", stripped, re.IGNORECASE)
    if m_fol_sr:
        n = int(m_fol_sr.group(1))
        old = character.extra_characteristics.get("FOL", 0)
        character.extra_characteristics["FOL"] = old + n
        return f"FOL {old}→{old + n}"

    # BOL +N (Za'tachk Boldness characteristic)
    m_bol_sr = re.match(r"^BOL\s*\+(\d+)$", stripped, re.IGNORECASE)
    if m_bol_sr:
        n = int(m_bol_sr.group(1))
        old = character.boldness
        character.boldness = old + n
        return f"BOL {old}→{old + n}"

    # Characteristic bonuses ("STR +1", "DEX +1", "PSI +1", "RES +1", etc.)
    for stat in ("STR", "DEX", "END", "INT", "EDU", "SOC", "PSI", "RES"):
        if stripped == f"{stat} +1":
            species_data = rules.species().get(character.species_id, {})
            max_stat = _stat_cap(species_data, stat)
            if stat == "PSI":
                current = character.psi
                character.psi = min(current + 1, max_stat)
                return f"PSI {current}→{character.psi}"
            # RES is an alias for SOC (Hiver Resolve)
            real_stat = "SOC" if stat == "RES" else stat
            current = character.characteristics.get(real_stat)
            if current < max_stat:
                character.characteristics.set(real_stat, current + 1)
                label = stat  # keep "RES" label for Hivers
                return f"{label} {current}→{current + 1}"
            return f"{stat} already at max ({max_stat})"

    # "X (if male) or Y (if female)" — gender-conditional (Aslan skill tables)
    _gender_m = re.match(
        r"^(.+?)\s*\(if male\)\s*or\s*(.+?)\s*\(if female\)\s*$",
        stripped, re.IGNORECASE
    )
    if _gender_m:
        male_skill = _gender_m.group(1).strip()
        female_skill = _gender_m.group(2).strip()
        gender = (character.gender or "").lower()
        chosen = female_skill if gender == "female" else male_skill
        name_g, spec_g = _split_skill_speciality(chosen)
        msg_g = character.add_skill(name_g, level=1, speciality=spec_g)
        disp_g = f"{name_g} ({spec_g})" if spec_g else name_g
        note = f" (gender: {gender or 'unknown → defaulted to male'}, alt: {female_skill if gender != 'female' else male_skill})"
        if msg_g.startswith("Increased "):
            return f"+1 {disp_g} → now level {msg_g.rsplit(' ', 1)[-1]}{note}"
        return f"+1 {disp_g} (level 1){note}"

    # "X or Y" where " or " appears OUTSIDE parentheses — auto-pick first option
    # Depth-aware check to avoid splitting "Profession (Miner or Belter)" incorrectly.
    _top_or_pos = -1
    if " or " in stripped:
        _d = 0
        for _ci, _ch in enumerate(stripped):
            if _ch == "(":
                _d += 1
            elif _ch == ")":
                _d -= 1
            elif _d == 0 and stripped[_ci: _ci + 4] == " or ":
                _top_or_pos = _ci
                break
    if _top_or_pos >= 0:
        first = stripped[:_top_or_pos].strip()
        name_first, spec_first = _split_skill_speciality(first)
        # "(any)" is not a real speciality — strip it and add the base skill
        if spec_first and spec_first.lower() == "any":
            spec_first = None
        msg = character.add_skill(name_first, level=1, speciality=spec_first)
        disp_first = f"{name_first} ({spec_first})" if spec_first else name_first
        if msg.startswith("Increased "):
            new_level = msg.rsplit(" ", 1)[-1]
            return f"+1 {disp_first} → now level {new_level} (from choice: {stripped})"
        return f"+1 {disp_first} (level 1) (from choice: {stripped})"

    # Skill with optional speciality: "Melee (blade)", "Pilot (small craft)", "Recon"
    name, spec = _split_skill_speciality(stripped)
    # "(any)" is not a real speciality — strip it and add the base skill
    if spec and spec.lower() == "any":
        spec = None
    msg = character.add_skill(name, level=1, speciality=spec)
    display = f"{name} ({spec})" if spec else name
    # Return "+1 SkillName → level N" so players clearly see it's an increment
    if msg.startswith("Increased "):
        # "Increased Gun Combat (blade) to 2" → "+1 Gun Combat (blade) → now level 2"
        new_level = msg.rsplit(" ", 1)[-1]
        return f"+1 {display} → now level {new_level}"
    else:
        # New skill at level 1
        return f"+1 {display} (level 1)"


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

    name, speciality = _split_skill_speciality(text)
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


def update_associate(character: Character, index: int, description: str) -> dict:
    """Rename an existing Associate (e.g. naming a mustering-out Contact/Ally).

    Lets the player attach the generated type+name to an associate that was
    added with a placeholder description.
    """
    if index < 0 or index >= len(character.associates):
        raise ValueError(
            f"Associate index {index} out of range (have {len(character.associates)})"
        )
    desc = (description or "").strip()
    if not desc:
        raise ValueError("Associate description cannot be empty.")
    a = character.associates[index]
    a.description = desc
    character.log(f"Renamed {a.kind.capitalize()} → {desc}")
    return {
        "updated": {"kind": a.kind, "description": desc, "index": index},
        "character": character.model_dump(),
    }


def resolve_equipment_choice(character: Character, index: int, chosen: str) -> dict:
    """Resolve an 'X or Y' equipment entry (an unresolved benefit choice).

    Compound mustering-out benefits like "Combat Implant or two Ship Shares" or
    rank-bonus gear like "Rifle or Carbine" are stored as a single equipment
    item whose name carries the whole choice. This removes that item and applies
    the chosen option through _apply_benefit, so ship shares, stats, associates,
    weapons and plain gear all land in the right place.
    """
    if index < 0 or index >= len(character.equipment):
        raise ValueError(
            f"Equipment index {index} out of range (have {len(character.equipment)})"
        )
    item = character.equipment[index]
    # Strip a trailing instruction like "(choose one)" / "(pick one)" so it is
    # never mistaken for an option, then split on commas AND "or" so a list such
    # as "Blade, Club or Dagger (choose one)" yields Blade / Club / Dagger.
    _name = re.sub(r"\s*\(\s*(?:choose|pick|select)[^)]*\)\s*$", "", item.name or "", flags=re.IGNORECASE)
    options = [o.strip() for o in re.split(r"\s*,\s*|\s+or\s+", _name, flags=re.IGNORECASE) if o.strip()]
    if len(options) < 2:
        raise ValueError(f"'{item.name}' is not an unresolved choice.")
    pick = (chosen or "").strip()
    if pick not in options:
        raise ValueError(f"'{pick}' is not one of: {' / '.join(options)}")

    del character.equipment[index]
    # _apply_benefit handles every option shape — ship shares, implants, stats,
    # associates, skills — and its catch-all stores anything else as equipment,
    # so the chosen option is never silently lost.
    _apply_benefit(character, pick)
    character.log(f"Benefit choice resolved: '{item.name}' → {pick}")
    return {"chosen": pick, "character": character.model_dump()}


def cleanup_cascade_specialties(character: Character, choices: dict[str, str]) -> dict:
    """Move levels held on a bare cascade parent skill into a chosen specialty.

    Cascade skills (Gun Combat, Pilot, Melee, Science, …) may only be held at
    level 0 as the parent — any level 1+ must live in a specialty. This takes a
    {parent_skill_name: speciality} map and, for each bare parent skill with
    level > 0, moves that level into the chosen speciality and drops the parent
    back to level 0 (per MgT 2e p.59).
    """
    specs_map = rules.skill_specialities()
    applied: list[str] = []
    for name, spec in (choices or {}).items():
        if not specs_map.get(name):
            raise ValueError(f"'{name}' is not a cascade skill.")
        spec = (spec or "").strip()
        if not spec:
            raise ValueError(f"Choose a {name} speciality.")
        # The UI's cascade-specialty lists don't always match the canonical
        # skills table (e.g. Profession, Language), so trust the player's pick
        # from the curated picker rather than rejecting it.
        parent = next(
            (s for s in character.skills
             if s.name == name and s.speciality is None and (s.level or 0) > 0),
            None,
        )
        if parent is None:
            continue  # nothing to move (already clean or not present)
        level = parent.level
        parent.level = 0  # parent stays, dropped to 0
        msg = character.add_skill(name, level=level, speciality=spec, fixed_level=True)
        applied.append(f"{name} {level} → {name} ({spec}) {level}")
        character.log(f"Cleanup: moved {name} {level} into {name} ({spec}) — {msg}")
    return {"applied": applied, "character": character.model_dump()}


# ============================================================
# NPC Auto-generation
# ============================================================

# Random specialty pools for cascade skills used in packages.
_NPC_CASCADE_SPECS: dict[str, list[str]] = {
    "Animals":       ["handling", "training", "veterinary"],
    "Art":           ["performer", "holography", "write", "visual media", "instrument"],
    "Athletics":     ["dexterity", "endurance", "strength"],
    "Drive":         ["wheeled", "walker", "tracked", "hover", "mole"],
    "Electronics":   ["computers", "comms", "sensors", "remote ops"],
    "Engineer":      ["j-drive", "m-drive", "power", "life support"],
    "Flyer":         ["grav", "ornithopter", "rotor", "winged"],
    "Gun Combat":    ["slug", "archaic", "energy"],
    "Gunner":        ["turret", "ortillery", "capital", "screens"],
    "Heavy Weapons": ["man-portable", "vehicle", "artillery"],
    "Language":      ["anglic", "vilani", "zdetl"],
    "Melee":         ["blade", "bludgeon", "unarmed"],
    "Pilot":         ["small craft", "spacecraft", "capital ships"],
    "Profession":    ["merchant", "farmer", "hunter", "belter", "colonist"],
    "Science":       ["physics", "chemistry", "biology", "robotics", "genetics", "xenology"],
    "Seafarer":      ["ocean ships", "personal", "sail", "submarine"],
    "Tactics":       ["military", "naval"],
}


def _npc_random_spec(skill_name: str, exclude: list[str] | None = None) -> str:
    """Return a random specialty for a cascade skill, avoiding `exclude` entries."""
    pool = [s for s in _NPC_CASCADE_SPECS.get(skill_name, ["general"])
            if not exclude or s not in exclude]
    return random.choice(pool) if pool else "general"


def _npc_random_skill_choices(pkg: dict) -> dict[str, str]:
    """Build random skill_choices dict for all 'any' skills in a package."""
    choices: dict[str, str] = {}
    used_per_name: dict[str, list[str]] = {}
    for sk in pkg.get("skills", []):
        if sk.get("any") and sk["level"] >= 1:
            name = sk["name"]
            key  = sk.get("key", name)
            exclude = used_per_name.get(name, [])
            spec = _npc_random_spec(name, exclude=exclude)
            choices[key] = spec
            used_per_name.setdefault(name, []).append(spec)
    return choices


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


# NPC generation options ─────────────────────────────────────────────────────
# Species offered in the NPC generator UI (ordered). "uplifted" and
# "random_alien" are meta-options resolved to a concrete species at generation
# time by _npc_resolve_species.
NPC_SPECIES_OPTIONS: list[dict] = [
    {"id": "imperial_human", "label": "Imperial Human"},
    {"id": "solomani_human", "label": "Solomani Human"},
    {"id": "uplifted",       "label": "Uplifted (Ape / Dolphin)"},
    {"id": "aslan",          "label": "Aslan"},
    {"id": "vargr",          "label": "Vargr"},
    {"id": "zhodani",        "label": "Zhodani"},
    {"id": "random_alien",   "label": "Random Alien"},
]

# Concrete species pools backing the meta-options.
_NPC_HUMAN_SPECIES    = ["imperial_human", "solomani_human"]
_NPC_UPLIFTED_SPECIES = ["uplifted_ape_chimp", "uplifted_ape_gorilla", "dolphin"]
_NPC_ALIEN_SPECIES    = ["aslan", "vargr", "zhodani",
                         "uplifted_ape_chimp", "uplifted_ape_gorilla",
                         "dolphin", "uplifted_orca"]
# Legacy alias retained for any external callers.
NPC_SPECIES_CHOICES = _NPC_HUMAN_SPECIES + ["vargr", "aslan", "bwap"]


def _npc_resolve_species(species_id: Optional[str]) -> str:
    """Resolve a UI species selection (incl. meta-options) to a concrete id."""
    if species_id in (None, "", "random"):
        return random.choice(_NPC_HUMAN_SPECIES + _NPC_ALIEN_SPECIES)
    if species_id == "uplifted":
        return random.choice(_NPC_UPLIFTED_SPECIES)
    if species_id == "random_alien":
        return random.choice(_NPC_ALIEN_SPECIES)
    return species_id


def _npc_resolve_species_pendings(char: Character) -> None:
    """Auto-resolve any pending choice apply_species left on an NPC (e.g. the
    Zhodani PSI ruleset, or a species skill-grant choice)."""
    pend = char.pending_life_event_choice
    if not pend:
        return
    kind = pend.get("kind")
    if kind == "zhodani_psi_ruleset":
        # NPCs use the standard Sourcebook rule (all Zhodani have PSI).
        resolve_zhodani_psi_choice(char, "sourcebook")
    elif pend.get("options"):
        # Generic species skill-grant choice — pick one at random and clear it.
        choice = random.choice(pend["options"])
        skill = choice.get("name") or choice.get("id") or choice.get("label")
        if skill:
            try:
                char.add_skill(str(skill), 0)
            except Exception:
                pass
        char.pending_life_event_choice = None
    else:
        char.pending_life_event_choice = None

# Role/archetype → career-package candidates. Generation biases the random
# career-package pick toward these; falls back to any eligible package.
NPC_ROLE_PACKAGES: dict[str, list[str]] = {
    "soldier":     ["military_enlisted", "marine", "barbarian"],
    "officer":     ["military_officer", "spacer_command"],
    "pilot":       ["spacer_crew", "scout"],
    "scout":       ["scout"],
    "agent":       ["agent", "rogue"],
    "criminal":    ["rogue", "corsair", "barbarian"],
    "scholar":     ["scholar"],
    "medic":       ["medic"],
    "noble":       ["noble"],
    "trader":      ["administrator", "citizen"],
    "entertainer": ["performer"],
    "drifter":     ["wanderer"],
    # Ship crew positions — biased toward spacer packages, each guarantees its
    # signature skill via NPC_ROLE_SKILLS.
    "captain":     ["spacer_command", "military_officer"],
    "astrogator":  ["spacer_crew", "scout"],
    "engineer":    ["spacer_crew", "scout"],
    "gunner":      ["spacer_crew", "marine"],
    "sensors":     ["spacer_crew", "scout"],
    "comms":       ["spacer_crew", "scout"],
    "steward":     ["spacer_crew", "citizen"],
}

NPC_ROLE_LABELS: dict[str, str] = {
    "soldier": "Soldier", "officer": "Officer", "pilot": "Pilot (ship)",
    "scout": "Scout", "agent": "Agent/Spy", "criminal": "Criminal",
    "scholar": "Scholar/Scientist", "medic": "Medic", "noble": "Noble",
    "trader": "Trader/Official", "entertainer": "Entertainer", "drifter": "Drifter",
    "captain": "Ship's Captain", "astrogator": "Astrogator (ship)",
    "engineer": "Engineer (ship)", "gunner": "Gunner (ship)",
    "sensors": "Sensor Operator (ship)", "comms": "Comms Operator (ship)",
    "steward": "Steward (ship)",
}

# A role's signature skill, guaranteed trained on every NPC of that role
# (name, optional speciality). Use the Primary Skill field to make them expert.
NPC_ROLE_SKILLS: dict[str, tuple[str, Optional[str]]] = {
    "pilot":      ("Pilot", None),
    "captain":    ("Leadership", None),
    "astrogator": ("Astrogation", None),
    "engineer":   ("Engineer", None),
    "gunner":     ("Gunner", None),
    "sensors":    ("Electronics", "sensors"),
    "comms":      ("Electronics", "comms"),
    "steward":    ("Steward", None),
    "medic":      ("Medic", None),
}

# Experience tier → extra skill bumps, extra age (years), and a stat boost.
# "stat_bump" = how many distinct characteristics get +1.
# "terms" (optional) = (min, max) career terms; sets age directly instead of
# extra_years. "second_career" grafts a second career package's skills.
NPC_EXPERIENCE: dict[str, dict] = {
    "rookie":  {"label": "Rookie",  "skill_bumps": 0,  "extra_years": 0,  "stat_bump": 0},
    "regular": {"label": "Regular", "skill_bumps": 2,  "extra_years": 4,  "stat_bump": 0},
    "veteran": {"label": "Veteran", "skill_bumps": 4,  "extra_years": 12, "stat_bump": 0},
    "elite":   {"label": "Elite",   "skill_bumps": 6,  "extra_years": 20, "stat_bump": 1},
    "patron":  {"label": "Patron (7–10 terms)", "skill_bumps": 12, "extra_years": 0,
                "stat_bump": 2, "terms": (7, 10), "second_career": True},
}

# Cascade parents must never hold a level above 0 (levels live on specialities).
_NPC_CASCADE_PARENTS = frozenset(_NPC_CASCADE_SPECS.keys())

# D66 Character Quirks (MgT2e) — every NPC gets one.
NPC_QUIRKS: dict[str, str] = {
    "11": "Loyal", "12": "Distracted by other worries", "13": "In debt to criminals",
    "14": "Makes very bad jokes", "15": "Will betray characters", "16": "Aggressive",
    "21": "Has secret allies", "22": "Secret anagathic user", "23": "Looking for something",
    "24": "Helpful", "25": "Forgetful", "26": "Wants to hire the Travellers",
    "31": "Has useful contacts", "32": "Artistic", "33": "Easily confused",
    "34": "Unusually ugly", "35": "Worried about current situation",
    "36": "Shows pictures of their children",
    "41": "Rumour-monger", "42": "Unusually provincial", "43": "Drunkard or drug addict",
    "44": "Government informant", "45": "Mistakes a Traveller for someone else",
    "46": "Possesses unusually advanced technology",
    "51": "Unusually handsome or beautiful", "52": "Spying on the Travellers",
    "53": "Possesses TAS membership", "54": "Is secretly hostile towards the Travellers",
    "55": "Wants to borrow money", "56": "Is convinced the Travellers are dangerous",
    "61": "Involved in political intrigue", "62": "Has a dangerous secret",
    "63": "Wants to get off planet as soon as possible", "64": "Attracted to a Traveller",
    "65": "From offworld", "66": "Possesses telepathy or other unusual quality",
}

# D66 Random Patrons (MgT2e) — the patron tier rolls its type here.
NPC_PATRON_TYPES: dict[str, str] = {
    "11": "Assassin", "12": "Smuggler", "13": "Terrorist", "14": "Embezzler",
    "15": "Thief", "16": "Revolutionary", "21": "Clerk", "22": "Administrator",
    "23": "Mayor", "24": "Minor Noble", "25": "Physician", "26": "Tribal Leader",
    "31": "Diplomat", "32": "Courier", "33": "Spy", "34": "Ambassador",
    "35": "Noble", "36": "Police Officer", "41": "Merchant", "42": "Free Trader",
    "43": "Broker", "44": "Corporate Executive", "45": "Corporate Agent",
    "46": "Financier", "51": "Belter", "52": "Researcher", "53": "Naval Officer",
    "54": "Pilot", "55": "Starport Administrator", "56": "Scout", "61": "Alien",
    "62": "Playboy", "63": "Stowaway", "64": "Family Relative",
    "65": "Agent of a Foreign Power", "66": "Imperial Agent",
}


def _d66_key() -> str:
    """Roll D66 (two dice read as tens+units): '11'..'66'."""
    return f"{random.randint(1, 6)}{random.randint(1, 6)}"


def npc_skill_options() -> list[str]:
    """All pickable skill names for the NPC generator (core + cascade parents)."""
    sk = rules.skills()
    names = list(sk.get("core", [])) + list((sk.get("speciality") or {}).keys())
    return sorted(names)


def _npc_ensure_skill(char: Character, skill_name: Optional[str], min_level: int = 2,
                      speciality: Optional[str] = None) -> None:
    """Guarantee the NPC has `skill_name` at >= min_level. Cascade parents get a
    speciality — the one given, else an existing/random one (parents can't hold
    levels); existing higher levels are kept."""
    from .character import Skill
    if not skill_name:
        return
    spec_map = rules.skills().get("speciality") or {}
    if skill_name in spec_map:
        if speciality:
            target = next((s for s in char.skills if s.name == skill_name and s.speciality
                           and s.speciality.lower() == speciality.lower()), None)
            if target:
                target.level = max(target.level, min_level)
            else:
                char.skills.append(Skill(name=skill_name, level=min_level, speciality=speciality))
        else:
            specs = [s for s in char.skills if s.name == skill_name and s.speciality]
            if specs:
                top = max(specs, key=lambda s: s.level)
                if top.level < min_level:
                    top.level = min_level
            else:
                char.skills.append(Skill(name=skill_name, level=min_level,
                                         speciality=_npc_random_spec(skill_name)))
        if not any(s.name == skill_name and s.speciality is None for s in char.skills):
            char.skills.append(Skill(name=skill_name, level=0, speciality=None))
    else:
        existing = next((s for s in char.skills
                         if s.name == skill_name and s.speciality is None), None)
        if existing:
            if existing.level < min_level:
                existing.level = min_level
        else:
            char.skills.append(Skill(name=skill_name, level=min_level, speciality=None))


def _npc_graft_second_career(char: Character, primary_pkg_id: str) -> None:
    """Merge a second (different) career package's skills onto the NPC to
    represent a long, multi-career history. Skills merge by max level (cap 4);
    'any' skills resolve to a random speciality."""
    from .character import Skill
    cp_pkgs = rules.career_packages().get("packages", {})
    candidates = [
        pid for pid, pkg in cp_pkgs.items()
        if pid != primary_pkg_id
        and not (pkg.get("min_soc") and (char.characteristics.SOC or 0) < pkg["min_soc"])
    ]
    if not candidates:
        return
    pkg = cp_pkgs[random.choice(candidates)]
    for sk in pkg.get("skills", []):
        if sk["level"] < 1:
            continue
        name = sk["name"]
        spec = sk.get("speciality")
        if sk.get("any"):
            used = [s.speciality for s in char.skills if s.name == name and s.speciality]
            spec = _npc_random_spec(name, exclude=[u for u in used if u])
        lvl = min(int(sk["level"]), 4)
        existing = next(
            (s for s in char.skills if s.name == name
             and (s.speciality or None) == (spec or None)), None)
        if existing:
            existing.level = max(existing.level, lvl)
        else:
            char.skills.append(Skill(name=name, level=lvl, speciality=spec))


def _npc_apply_experience(char: Character, experience: str,
                          primary_pkg_id: Optional[str] = None) -> None:
    """Layer an experience tier onto a freshly package-built NPC: bump existing
    skills, age the character, and nudge characteristics. The Patron tier also
    grafts a second career and sets age to a 7–10 term lifetime."""
    cfg = NPC_EXPERIENCE.get(experience, NPC_EXPERIENCE["regular"])

    # Patron: a second career's worth of skills before bumping.
    if cfg.get("second_career") and primary_pkg_id:
        _npc_graft_second_career(char, primary_pkg_id)

    # Bump existing trained skills by +1 (cap 4). Bare cascade parents only ever
    # hold level 0, so the level>=1 filter already excludes them — speciality
    # skills (e.g. "Melee (blade)") remain bumpable.
    bumpable = [sk for sk in char.skills if 1 <= sk.level < 4]
    random.shuffle(bumpable)
    for sk in bumpable[: cfg["skill_bumps"]]:
        sk.level += 1

    # Age: a "terms" tier sets a full career lifetime; otherwise add extra_years.
    if cfg.get("terms"):
        lo, hi = cfg["terms"]
        char.age = 18 + random.randint(lo, hi) * 4
    elif cfg["extra_years"]:
        char.age += cfg["extra_years"]

    # Nudge N distinct characteristics up by 1, respecting species caps.
    if cfg["stat_bump"]:
        sp_data = rules.species().get(char.species_id or "", {})
        stats = ["STR", "DEX", "END", "INT", "EDU", "SOC"]
        random.shuffle(stats)
        bumped = 0
        for st in stats:
            if bumped >= cfg["stat_bump"]:
                break
            cur = char.characteristics.get(st) or 0
            if cur < _stat_cap(sp_data, st):
                char.characteristics.set(st, cur + 1)
                bumped += 1


def _npc_resolve_cascade_parents(char: Character) -> None:
    """Package builds can leave a cascade parent (e.g. "Gunner") trained at
    level>0 with no speciality. Cascade parents may only hold level 0, so give
    each such skill a random speciality (merging if that speciality exists)."""
    from .character import Skill
    for sk in list(char.skills):
        if sk.name in _NPC_CASCADE_PARENTS and sk.speciality is None and sk.level > 0:
            used = [s.speciality for s in char.skills
                    if s.name == sk.name and s.speciality]
            spec = _npc_random_spec(sk.name, exclude=[u for u in used if u])
            existing = next((s for s in char.skills
                             if s.name == sk.name and s.speciality
                             and s.speciality.lower() == spec.lower()), None)
            if existing:
                existing.level = max(existing.level, sk.level)
                char.skills.remove(sk)
            else:
                sk.speciality = spec
            # Ensure a bare parent-at-0 entry exists for the cascade structure.
            if not any(s.name == sk.name and s.speciality is None for s in char.skills):
                char.skills.append(Skill(name=sk.name, level=0, speciality=None))


def generate_npc(species_id: Optional[str] = None,
                 role: Optional[str] = None,
                 experience: str = "regular",
                 primary_skill: Optional[str] = None,
                 secondary_skill: Optional[str] = None) -> dict:
    """Generate a complete NPC character automatically using background + career packages.

    1. Rolls characteristics and applies the chosen (or random) species.
    2. Applies a random background package (filters by min SOC).
    3. Applies a career package biased toward the chosen role (or random).
    4. Layers the experience tier (skill depth, age, elite stat bump).
    5. Guarantees any chosen primary/secondary skill at level 2+.
    6. Sets phase = 'done'.
    """
    char = Character()

    # ── Characteristics ───────────────────────────────────────────────────
    for stat, val in dice.roll_characteristics().items():
        setattr(char.characteristics, stat, val)

    # ── Species (resolve meta-options to a concrete species) ──────────────
    species_id = _npc_resolve_species(species_id)
    char.phase = "setup"
    try:
        apply_species(char, species_id)
        _npc_resolve_species_pendings(char)
    except Exception:
        # Fall back to Imperial Human if the chosen species needs interaction.
        char = Character()
        for stat, val in dice.roll_characteristics().items():
            setattr(char.characteristics, stat, val)
        species_id = "imperial_human"
        char.phase = "setup"
        apply_species(char, species_id)
    char.phase = "background"

    # ── Background package (random) ───────────────────────────────────────
    bg_packages = rules.background_packages()
    eligible_bg = [
        pkg for pkg in bg_packages.values()
        if not (pkg.get("min_soc") and char.characteristics.SOC < pkg["min_soc"])
    ]
    bg_pkg = random.choice(eligible_bg)
    bg_skill_choices = _npc_random_skill_choices(bg_pkg)

    # apply_background_package expects phase == "background"
    apply_background_package(char, bg_pkg["id"], skill_choices=bg_skill_choices)
    # phase is now "career"

    # ── Career package (random, weighted by stat fit) ─────────────────────
    cp_data   = rules.career_packages()
    cp_pkgs   = cp_data.get("packages", {})
    cp_fin    = cp_data.get("finalising", {})

    eligible_cp = [
        pkg for pkg in cp_pkgs.values()
        if not (pkg.get("min_soc") and char.characteristics.SOC < pkg["min_soc"])
    ]
    # Bias toward the chosen role's career packages (if any are eligible).
    if role and role != "random":
        role_ids = NPC_ROLE_PACKAGES.get(role, [])
        role_eligible = [pkg for pkg in eligible_cp if pkg["id"] in role_ids]
        if role_eligible:
            eligible_cp = role_eligible
    cp_pkg = random.choice(eligible_cp)
    cp_skill_choices = _npc_random_skill_choices(cp_pkg)

    # ── Finalising — CAREER choice (random) ──────────────────────────────
    career_choices = [opt["id"] for opt in cp_fin.get("career", [])]
    career_choice  = random.choice(career_choices) if career_choices else "rank_4_only"

    career_skill           = None
    career_skill_speciality = None
    career_3skills: list[dict] = []

    if career_choice == "boost_one_to_4":
        # Pick a random skill from the package at level 1+
        eligible_boost = [sk for sk in cp_pkg["skills"] if sk["level"] >= 1]
        if eligible_boost:
            pick = random.choice(eligible_boost)
            career_skill = pick["name"]
            # Resolve the speciality that was actually assigned
            if pick.get("any"):
                key = pick.get("key", pick["name"])
                career_skill_speciality = cp_skill_choices.get(key)
            else:
                career_skill_speciality = pick.get("speciality")

    elif career_choice == "boost_three_by_1":
        # Pick 3 distinct skills from the package
        pool = list(cp_pkg["skills"])
        random.shuffle(pool)
        for pick in pool[:3]:
            spec = None
            if pick.get("any"):
                key  = pick.get("key", pick["name"])
                spec = cp_skill_choices.get(key)
            else:
                spec = pick.get("speciality")
            career_3skills.append({"name": pick["name"], "speciality": spec})

    # ── Finalising — TRAVELLER SKILLS (random) ────────────────────────────
    ts_pairs = cp_fin.get("traveller_skills", [])
    ts_pair  = random.choice(ts_pairs) if ts_pairs else {"id": 1, "skills": []}
    traveller_pair_id = ts_pair["id"]
    traveller_specialties: dict[str, str] = {}
    for ts_sk in ts_pair.get("skills", []):
        if ts_sk.get("any"):
            key  = ts_sk.get("key", ts_sk["name"])
            spec = _npc_random_spec(ts_sk["name"])
            traveller_specialties[key] = spec

    # ── Finalising — BENEFIT (random) ─────────────────────────────────────
    benefits = cp_fin.get("benefits", [])
    benefit_id = random.choice(benefits)["id"] if benefits else 1

    # ── Apply career package ──────────────────────────────────────────────
    # A random finalising pick (e.g. boost a skill that resolved to a speciality)
    # can be unapplicable. Snapshot the clean pre-package character so we can
    # restore and fall back to the no-input choice without double-applying.
    _pre_pkg = char.model_copy(deep=True)
    try:
        apply_career_package(
            char,
            package_id=cp_pkg["id"],
            skill_choices=cp_skill_choices,
            career_choice=career_choice,
            career_skill=career_skill,
            career_skill_speciality=career_skill_speciality,
            career_3skills=career_3skills,
            traveller_pair_id=traveller_pair_id,
            traveller_specialties=traveller_specialties,
            benefit_id=benefit_id,
        )
    except ValueError:
        char = _pre_pkg
        apply_career_package(
            char,
            package_id=cp_pkg["id"],
            skill_choices=cp_skill_choices,
            career_choice="rank_4_only",
            traveller_pair_id=traveller_pair_id,
            traveller_specialties=traveller_specialties,
            benefit_id=benefit_id,
        )
    # phase is now "skill_package" — skip it for NPC

    # ── Experience tier (skill depth, age, stat bumps, patron 2nd career) ─
    _npc_apply_experience(char, experience, primary_pkg_id=cp_pkg["id"])

    # ── Resolve any generic cascade parents to real specialities ──────────
    _npc_resolve_cascade_parents(char)

    # ── Role signature skill (trained), then chosen primary/secondary (2+) ─
    _role_skill = NPC_ROLE_SKILLS.get(role or "")
    if _role_skill:
        _npc_ensure_skill(char, _role_skill[0], min_level=1, speciality=_role_skill[1])
    _npc_ensure_skill(char, primary_skill, min_level=2)
    _npc_ensure_skill(char, secondary_skill, min_level=2)

    # ── Character Quirk (every NPC) + Patron type (patron tier) ───────────
    char.npc_quirk = NPC_QUIRKS[_d66_key()]
    _note_lines = [f"Quirk: {char.npc_quirk}"]
    if experience == "patron":
        char.npc_patron_type = NPC_PATRON_TYPES[_d66_key()]
        _note_lines.insert(0, f"Patron: {char.npc_patron_type}")
    char.user_notes = ("\n".join(_note_lines) + ("\n\n" + char.user_notes if char.user_notes else "")).strip()

    char.phase = "done"
    _sp_name = rules.species().get(char.species_id or "", {}).get("name", char.species_id)
    _exp_label = NPC_EXPERIENCE.get(experience, NPC_EXPERIENCE["regular"])["label"]
    _patron_note = f", patron: {char.npc_patron_type}" if char.npc_patron_type else ""
    char.log(
        f"NPC generation complete — {_sp_name}, {_exp_label}, background: "
        f"{bg_pkg['name']}, career: {cp_pkg['name']}, age {char.age}, "
        f"quirk: {char.npc_quirk}{_patron_note}."
    )
    return {"character": char.model_dump()}


def generate_npc_batch(count: int = 1,
                       species_id: Optional[str] = None,
                       role: Optional[str] = None,
                       experience: str = "regular",
                       primary_skill: Optional[str] = None,
                       secondary_skill: Optional[str] = None) -> dict:
    """Generate a batch of NPCs. Returns {"npcs": [character_dict, ...]}.

    Each NPC re-rolls characteristics, species (if 'random'), role bias (if
    'random'), and finalising choices independently, so a group is varied.
    Any chosen primary/secondary skill is guaranteed at level 2+ on every NPC.
    """
    count = max(1, min(int(count or 1), 12))
    npcs = []
    for _ in range(count):
        npcs.append(generate_npc(species_id=species_id, role=role,
                                 experience=experience,
                                 primary_skill=primary_skill,
                                 secondary_skill=secondary_skill)["character"])
    return {"npcs": npcs}


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
        # Extract trailing level number (default 1 for packages)
        level = 1
        m = re.search(r"\s+(\d+)\s*$", text)
        if m:
            level = int(m.group(1))
            text = text[: m.start()].strip()
        name, speciality = _split_skill_speciality(text)
        msg = character.add_skill(name, level=level, speciality=speciality)
        disp = f"{name}{f' ({speciality})' if speciality else ''} {level}"
        applied.append(disp)
        character.log(f"Skill package '{package_id}': {disp} — {msg}")

    return {"applied": applied, "character": character.model_dump()}


# ============================================================
# Death survival (RAW p.48: spend 1D×Cr10,000 medical loan)
# ============================================================

def cheat_death(character: "Character") -> dict:
    """Survive death by incurring a medical loan (RAW MgT 2e p.48).

    - Roll 1D × Cr10,000 as medical debt.
    - Permanently reduce one physical characteristic (STR, DEX or END)
      by 1 — pick whichever is currently highest (auto-resolve to avoid
      an extra UI round-trip; player can adjust notes if desired).
    - Revive the character: dead = False, phase = 'career', current_term
      cleared so they return to career selection.
    """
    if not character.dead:
        raise ValueError("Character is not dead.")

    cost_roll = dice.roll("1D")
    cost = cost_roll.total * 10_000
    character.medical_debt += cost

    # Reduce the highest physical stat by 1 (auto-pick)
    physical = ["STR", "DEX", "END"]
    stat_reduced = max(physical, key=lambda s: character.characteristics.get(s))
    old_val = character.characteristics.get(stat_reduced)
    character.characteristics.set(stat_reduced, max(0, old_val - 1))

    character.log(
        f"Cheated death: medical loan Cr{cost:,} (1D={cost_roll.total}×Cr10,000). "
        f"{stat_reduced} reduced {old_val}→{max(0, old_val - 1)}."
    )

    character.dead = False
    character.death_reason = None
    character.current_term = None
    character.phase = "career"

    return {
        "cost": cost,
        "cost_roll": cost_roll.to_dict(),
        "stat_reduced": stat_reduced,
        "old_val": old_val,
        "new_val": max(0, old_val - 1),
        "character": character.model_dump(),
    }
