"""
foundry_export.py — Convert a TravllerCC Character into a FoundryVTT MGT2e actor JSON.

The output is a dict that can be JSON-serialised and imported directly into
FoundryVTT via the MGT2e system's "Import Actor" feature (or drag-dropped from
the file system).
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any

from .character import Character, Skill, Associate, Equipment, CareerTerm, CareerRecord
from . import rules


def _embed_source(char: Any) -> dict:
    """Serialise the source character for the lossless round-trip flag."""
    if hasattr(char, "model_dump"):
        return char.model_dump()
    return char if isinstance(char, dict) else {}


# ---------------------------------------------------------------------------
# Skill name → Foundry skill-ID lookup
# ---------------------------------------------------------------------------

_SKILL_NAME_TO_ID: dict[str, str] = {
    "admin": "admin",
    "advocate": "advocate",
    "animals": "animals",
    "art": "art",
    "astrogation": "astrogation",
    "athletics": "athletics",
    "broker": "broker",
    "carouse": "carouse",
    "deception": "deception",
    "diplomat": "diplomat",
    "drive": "drive",
    "electronics": "electronics",
    "engineer": "engineer",
    "explosives": "explosives",
    "flyer": "flyer",
    "gambler": "gambler",
    "gunner": "gunner",
    "gun combat": "guncombat",
    "guncombat": "guncombat",
    "heavy weapons": "heavyweapons",
    "heavyweapons": "heavyweapons",
    "independence": "independence",
    "investigate": "investigate",
    "jack of all trades": "jackofalltrades",
    "jack-of-all-trades": "jackofalltrades",
    "jackofalltrades": "jackofalltrades",
    "language": "language",
    "leadership": "leadership",
    "mechanic": "mechanic",
    "medic": "medic",
    "melee": "melee",
    "navigation": "navigation",
    "persuade": "persuade",
    "pilot": "pilot",
    "profession": "profession",
    "recon": "recon",
    "science": "science",
    "seafarer": "seafarer",
    "stealth": "stealth",
    "steward": "steward",
    "streetwise": "streetwise",
    "survival": "survival",
    "tactics": "tactics",
    "vacc suit": "vaccsuit",
    "vaccsuit": "vaccsuit",
    # Psionic talents
    "telepathy": "telepathy",
    "clairvoyance": "clairvoyance",
    "telekinesis": "telekinesis",
    "awareness": "awareness",
    "teleportation": "teleportation",
}

# ---------------------------------------------------------------------------
# Speciality name → Foundry speciality-ID lookup
# ---------------------------------------------------------------------------

_SPEC_NAME_TO_ID: dict[str, str] = {
    # Athletics
    "strength": "strength",
    "dexterity": "dexterity",
    "endurance": "endurance",
    # Animals
    "handling": "handling",
    "vetinary": "vetinary",
    "veterinary": "vetinary",
    "training": "training",
    # Art
    "performer": "performer",
    "holography": "holography",
    "instrument": "instrument",
    "visual media": "visualMedia",
    "write": "write",
    # Drive
    "hovercraft": "hovercraft",
    "mole": "mole",
    "track": "track",
    "walker": "walker",
    "wheel": "wheel",
    # Electronics
    "comms": "comms",
    "computers": "computers",
    "remote ops": "remoteOps",
    "remoteops": "remoteOps",
    "sensors": "sensors",
    # Engineer
    "m-drive": "mDrive",
    "mdrive": "mDrive",
    "j-drive": "jDrive",
    "jdrive": "jDrive",
    "life support": "lifeSupport",
    "lifesupport": "lifeSupport",
    "power": "power",
    # Flyer
    "airship": "airship",
    "grav": "grav",
    "ornithopter": "ornithopter",
    "rotor": "rotor",
    "wing": "wing",
    # Gunner
    "turret": "turret",
    "ortillery": "ortillery",
    "screen": "screen",
    "capital": "capital",
    # Gun Combat
    "archaic": "archaic",
    "energy": "energy",
    "slug": "slug",
    # Heavy Weapons
    "artillery": "artillery",
    "portable": "portable",
    "vehicle": "vehicle",
    # Language
    "galanglic": "galanglic",
    "anglic": "galanglic",      # TravllerCC uses "Anglic"; Foundry calls it "galanglic"
    "vilani": "vilani",
    "zdetl": "zdetl",
    "oynprith": "oynprith",
    "trokh": "trokh",
    "gvegh": "gvegh",
    "bilanidin": "vilani",       # close enough — map to vilani dialect slot
    # Melee
    "unarmed": "unarmed",
    "blade": "blade",
    "bludgeon": "bludgeon",
    "natural": "natural",
    # Pilot
    "small craft": "smallCraft",
    "smallcraft": "smallCraft",
    "spacecraft": "spacecraft",
    "capital ships": "capitalShips",
    "capitalships": "capitalShips",
    # Profession
    "belter": "belter",
    "biologicals": "biologicals",
    "civil engineering": "civilEngineering",
    "civilengineering": "civilEngineering",
    "construction": "construction",
    "hydroponics": "hydroponics",
    "polymers": "polymers",
    "robotics": "robotics",
    "farming": "biologicals",    # map farming → biologicals (closest fit)
    # Science
    "archaeology": "archaeology",
    "astronomy": "astronomy",
    "biology": "biology",
    "chemistry": "chemistry",
    "cosmology": "cosmology",
    "cybernetics": "cybernetics",
    "economics": "economics",
    "genetics": "genetics",
    "history": "history",
    "linguistics": "linquistics",
    "linquistics": "linquistics",
    "philosophy": "philosophy",
    "physics": "physics",
    "planetology": "planetology",
    "psionicology": "psionicology",
    "psychology": "psychology",
    "sophontology": "sophontology",
    "xenology": "xenology",
    # Seafarer
    "ocean ships": "oceanShips",
    "oceanships": "oceanShips",
    "personal": "personal",
    "sail": "sail",
    "submarine": "submarine",
    # Tactics
    "military": "military",
    "naval": "naval",
}


def _norm(s: str) -> str:
    """Lower-case, strip extra whitespace."""
    return s.strip().lower()


# ---------------------------------------------------------------------------
# Full MGT2e skill tree — every skill the sheet must show.
# Untrained skills are exported at value -3 / trained=False (the MGT2e
# "unskilled" DM) so Foundry shows the −3 penalty.
# Format: { parent_id: [spec_id, ...] }  — empty list = non-cascade skill.
# ---------------------------------------------------------------------------

_ALL_SKILL_TREE: dict[str, list[str]] = {
    "admin":           [],
    "advocate":        [],
    "animals":         ["handling", "training", "vetinary"],
    "art":             ["holography", "instrument", "performer", "visualMedia", "write"],
    "astrogation":     [],
    "athletics":       ["dexterity", "endurance", "strength"],
    "broker":          [],
    "carouse":         [],
    "deception":       [],
    "diplomat":        [],
    "drive":           ["hovercraft", "mole", "track", "walker", "wheel"],
    "electronics":     ["comms", "computers", "remoteOps", "sensors"],
    "engineer":        ["jDrive", "lifeSupport", "mDrive", "power"],
    "explosives":      [],
    "flyer":           ["airship", "grav", "ornithopter", "rotor", "wing"],
    "gambler":         [],
    "guncombat":       ["archaic", "energy", "slug"],
    "gunner":          ["capital", "ortillery", "screen", "turret"],
    "heavyweapons":    ["artillery", "portable", "vehicle"],
    "independence":    [],
    "investigate":     [],
    "jackofalltrades": [],
    "language":        ["galanglic", "gvegh", "oynprith", "trokh", "vilani", "zdetl"],
    "leadership":      [],
    "mechanic":        [],
    "medic":           [],
    "melee":           ["blade", "bludgeon", "natural", "unarmed"],
    "navigation":      [],
    "persuade":        [],
    "pilot":           ["capitalShips", "smallCraft", "spacecraft"],
    "profession":      ["belter", "biologicals", "civilEngineering",
                        "construction", "hydroponics", "polymers", "robotics"],
    "recon":           [],
    "science":         ["archaeology", "astronomy", "biology", "chemistry",
                        "cosmology", "cybernetics", "economics", "genetics",
                        "history", "linquistics", "philosophy", "physics",
                        "planetology", "psionicology", "psychology",
                        "sophontology", "xenology"],
    "seafarer":        ["oceanShips", "personal", "sail", "submarine"],
    "stealth":         [],
    "steward":         [],
    "streetwise":      [],
    "survival":        [],
    "tactics":         ["military", "naval"],
    "vaccsuit":        [],
}


def _skill_id(name: str) -> str | None:
    return _SKILL_NAME_TO_ID.get(_norm(name))


def _spec_id(name: str) -> str | None:
    if not name:
        return None
    return _SPEC_NAME_TO_ID.get(_norm(name))


# ---------------------------------------------------------------------------
# Associate defaults by relationship type
# ---------------------------------------------------------------------------

_ASSOCIATE_DEFAULTS: dict[str, dict] = {
    "ally":    {"affinity": 3, "enmity": 0,  "power": 2, "influence": 2},
    "contact": {"affinity": 3, "enmity": 0,  "power": 0, "influence": 4},
    "rival":   {"affinity": 1, "enmity": 0,  "power": 2, "influence": 1},
    "enemy":   {"affinity": 0, "enmity": -3, "power": 3, "influence": 1},
}


# ---------------------------------------------------------------------------
# Public conversion function
# ---------------------------------------------------------------------------

def character_to_foundry(character: Character) -> dict[str, Any]:
    """Return a FoundryVTT MGT2e-compatible actor dict for *character*."""

    char = character

    # ------------------------------------------------------------------
    # 1. Characteristics
    # ------------------------------------------------------------------
    chars_raw = char.characteristics  # Characteristics model — use _cval() helper
    psi_val  = int(getattr(char, "psi", 0) or 0)

    def _cval(key: str, default: int = 0) -> int:
        """Get a characteristic value, supporting both the Characteristics model and plain dicts."""
        if chars_raw is None:
            return default
        if isinstance(chars_raw, dict):
            return int(chars_raw.get(key, default) or default)
        # Characteristics model: .get() takes only the key, returns None for unknowns
        v = chars_raw.get(key)
        if v is None:
            # Also check extra_characteristics on the character
            extra = getattr(char, "extra_characteristics", {}) or {}
            v = extra.get(key)
        return int(v) if v is not None else default

    def _char_entry(val: int, show: bool = True) -> dict:
        return {"value": val, "current": val, "show": show, "default": False}

    characteristics: dict[str, Any] = {
        "STR": _char_entry(_cval("STR", 7)),
        "DEX": _char_entry(_cval("DEX", 7)),
        "END": _char_entry(_cval("END", 7)),
        "INT": _char_entry(_cval("INT", 7)),
        "EDU": _char_entry(_cval("EDU", 7)),
        "SOC": _char_entry(_cval("SOC", 7)),
        "CHA": _char_entry(_cval("CHA", 0), show=False),
        "TER": _char_entry(_cval("TER", 0), show=False),
        "PSI": _char_entry(psi_val, show=psi_val > 0),
        "WLT": _char_entry(_cval("WLT", 0), show=False),
        "LCK": _char_entry(_cval("LCK", 0), show=False),
        "MRL": _char_entry(_cval("MRL", 0), show=False),
        "STY": _char_entry(_cval("STY", 0), show=False),
        "RES": _char_entry(_cval("RES", 0), show=False),
        "FOL": _char_entry(0, show=False),
        "REP": _char_entry(0, show=False),
    }

    # ------------------------------------------------------------------
    # 2. Skills
    # ------------------------------------------------------------------
    # Pre-seed every skill in the MGT2e tree as untrained (value=0, trained=False)
    # so Foundry shows -3 for everything the character hasn't touched.
    # Then overlay with the character's actual trained skills.

    _skill_work: dict[str, dict] = {}   # skill_id → {"base": int, "trained": bool, "specs": {id: int}}

    # Seed all skills from the master tree
    for sid, spec_ids in _ALL_SKILL_TREE.items():
        _skill_work[sid] = {
            "base": 0,
            "trained": False,
            "specs": {sp: {"level": 0, "trained": False} for sp in spec_ids},
        }

    # Also include psionic skills if the character has them (not in core tree)
    _PSIONIC_SKILLS = {"telepathy", "clairvoyance", "telekinesis", "awareness", "teleportation"}

    # Overlay character's actual skills
    for sk in (char.skills or []):
        skill_name = sk.get("name") if isinstance(sk, dict) else getattr(sk, "name", "")
        skill_level = sk.get("level", 0) if isinstance(sk, dict) else getattr(sk, "level", 0)
        skill_spec = sk.get("speciality") if isinstance(sk, dict) else getattr(sk, "speciality", None)

        sid = _skill_id(skill_name)
        if sid is None:
            continue  # unknown skill — skip

        if sid not in _skill_work:
            # e.g. psionics, Independence — add dynamically
            _skill_work[sid] = {"base": 0, "trained": False, "specs": {}}

        if not skill_spec or _norm(skill_spec) == "any":
            cur = _skill_work[sid]["base"]
            _skill_work[sid]["base"] = max(cur, int(skill_level))
            _skill_work[sid]["trained"] = True
        else:
            spec_id = _spec_id(skill_spec)
            if spec_id is None:
                spec_id = re.sub(r"[^a-z0-9]", "", _norm(skill_spec))
            if spec_id not in _skill_work[sid]["specs"]:
                _skill_work[sid]["specs"][spec_id] = {"level": 0, "trained": False}
            cur = _skill_work[sid]["specs"][spec_id]["level"]
            _skill_work[sid]["specs"][spec_id]["level"] = max(cur, int(skill_level))
            _skill_work[sid]["specs"][spec_id]["trained"] = True
            # Mark parent as at least seen (but not trained unless character has base too)
            if not _skill_work[sid]["trained"]:
                pass  # parent stays untrained; Foundry shows -3 for parent, actual level for spec

    # Build Foundry skills object
    skills: dict[str, Any] = {}
    for sid, data in _skill_work.items():
        base_val = data["base"]
        is_trained = data["trained"]
        specs_raw = data["specs"]

        entry: dict[str, Any] = {
            "id": sid,
            # Trained skills carry their level as a string ("0", "1", …);
            # untrained skills are -3 (the MGT2e "unskilled" DM) so Foundry shows
            # the −3 penalty rather than a misleading 0.
            "value": str(base_val) if is_trained else -3,
            "trained": is_trained,
        }
        if specs_raw:
            entry["specialities"] = {}
            for sp_id, sp_data in specs_raw.items():
                sp_lv = sp_data["level"] if isinstance(sp_data, dict) else sp_data
                sp_trained = sp_data["trained"] if isinstance(sp_data, dict) else True
                entry["specialities"][sp_id] = {
                    "id": sp_id,
                    "value": str(sp_lv) if sp_trained else -3,
                    "trained": sp_trained,
                }
        skills[sid] = entry

    # ------------------------------------------------------------------
    # 3. Hits (STR + DEX + END)
    # ------------------------------------------------------------------
    str_v = _cval("STR", 7)
    dex_v = _cval("DEX", 7)
    end_v = _cval("END", 7)
    hits_max = str_v + dex_v + end_v

    # ------------------------------------------------------------------
    # 4. Finance
    # ------------------------------------------------------------------
    ship_shares = int(getattr(char, "ship_shares", 0) or 0)
    finance: dict[str, Any] = {
        "cash":        str(int(getattr(char, "credits", 0) or 0)),
        "pension":     str(int(getattr(char, "pension_per_year", 0) or 0)),
        "medicalDebt": str(int(getattr(char, "medical_debt", 0) or 0)),
        "mortgage":    "0",
        "livingCosts": "0",
        "otherIncome": "0",
        "shipShares":  ship_shares,
        "description": f"Ship Shares: {ship_shares}" if ship_shares else "",
    }

    # ------------------------------------------------------------------
    # 5. Sophont / bio
    # ------------------------------------------------------------------
    age = int(getattr(char, "age", 18) or 18)
    species_name = str(getattr(char, "species_id", "") or "").replace("_", " ").title()
    gender_raw = getattr(char, "gender", None) or ""
    homeworld = str(getattr(char, "homeworld", "") or "")

    sophont: dict[str, Any] = {
        "age":          str(age),
        "species":      species_name,
        "speciesTraits": "",
        "gender":       gender_raw or "Unknown",
        "weight":       0,
        "height":       0,
        "profession":   _career_summary(char),
        "homeworld":    homeworld,
    }

    # ------------------------------------------------------------------
    # 6. Description (capsule + career history)
    # ------------------------------------------------------------------
    capsule = getattr(char, "capsule_description", None) or ""
    desc_html = "<p>" + capsule.replace("\n\n", "</p>\n<p>").replace("\n", "<br>") + "</p>" if capsule else ""

    # ------------------------------------------------------------------
    # 7. Build items list (associates, terms, equipment)
    # ------------------------------------------------------------------
    items: list[dict] = []
    term_history = getattr(char, "term_history", None) or []

    _now_ms = int(time.time() * 1000)

    def _item_stats(with_timestamps: bool = False) -> dict:
        """_stats block that Foundry requires to accept imported items."""
        s: dict = {
            "compendiumSource": None,
            "duplicateSource":  None,
            "exportSource":     None,
            "coreVersion":      "13.351",
            "systemId":         "mgt2e",
            "systemVersion":    "0.21.0.0",
            "lastModifiedBy":   None,
        }
        if with_timestamps:
            s["createdTime"]  = _now_ms
            s["modifiedTime"] = _now_ms
        return s

    # Associates (contacts / allies / rivals / enemies)
    for assoc in (getattr(char, "associates", None) or []):
        if isinstance(assoc, dict):
            kind = str(assoc.get("kind", "contact")).lower()
            desc = str(assoc.get("description", ""))
        else:
            kind = str(getattr(assoc, "kind", "contact")).lower()
            desc = str(getattr(assoc, "description", ""))

        defaults = _ASSOCIATE_DEFAULTS.get(kind, _ASSOCIATE_DEFAULTS["contact"])
        display_name = desc if desc else f"Unnamed {kind.title()}"

        items.append({
            "name": display_name,
            "type": "associate",
            "system": {
                "associate": {
                    "relationship": kind,
                    "affinity":     defaults["affinity"],
                    "enmity":       defaults["enmity"],
                    "power":        defaults["power"],
                    "influence":    defaults["influence"],
                },
                "relation":    kind,
                "description": desc,
            },
            "_id":      _short_id(),
            "img":      "systems/mgt2e/icons/items/item.svg",
            "effects":  [],
            "folder":   None,
            "sort":     0,
            "flags":    {},
            "_stats":   _item_stats(),
            "ownership": {"default": 0},
        })

    # Career terms — use sequential 1-based index for Foundry's term.number
    for seq_idx, term in enumerate(term_history, start=1):
        if isinstance(term, dict):
            t_career = str(term.get("career_id", "") or "").replace("_", " ").title()
            t_assign = str(term.get("assignment_id", "") or "").replace("_", " ").title()
            t_rank   = str(term.get("rank_title", "") or "")
            t_events = term.get("events", []) or []
        else:
            t_career = str(getattr(term, "career_id", "") or "").replace("_", " ").title()
            t_assign = str(getattr(term, "assignment_id", "") or "").replace("_", " ").title()
            t_rank   = str(getattr(term, "rank_title", "") or "")
            t_events = getattr(term, "events", []) or []

        assignment_str = f"{t_career}: {t_assign}" if t_assign else t_career
        if t_rank:
            assignment_str += f" ({t_rank})"
        event_lines = "\n".join(f"• {e}" for e in t_events) if t_events else ""
        term_desc = assignment_str + ("\n" + event_lines if event_lines else "")

        items.append({
            "name": f"Term {seq_idx}: {assignment_str}",
            "type": "term",
            "system": {
                "term": {
                    "number":       seq_idx,
                    "termLength":   4,
                    "assignment":   assignment_str,
                    "randomTerm":   False,
                    "randomLength": "",
                },
                "name":        "Term",
                "description": term_desc,
            },
            "_id":      _short_id(),
            "img":      "systems/mgt2e/icons/misc/career.svg",
            "effects":  [],
            "folder":   None,
            "sort":     0,
            "flags":    {},
            "_stats":   _item_stats(with_timestamps=True),
            "ownership": {"default": 0},
        })

    # Equipment
    for eq in (getattr(char, "equipment", None) or []):
        if isinstance(eq, dict):
            eq_name  = str(eq.get("name", "Item"))
            eq_qty   = int(eq.get("quantity", 1) or 1)
            eq_notes = str(eq.get("notes", "") or "")
        else:
            eq_name  = str(getattr(eq, "name", "Item"))
            eq_qty   = int(getattr(eq, "quantity", 1) or 1)
            eq_notes = str(getattr(eq, "notes", "") or "")

        items.append({
            "name": eq_name,
            "type": "item",
            "system": {
                "tl":          0,
                "weight":      0,
                "cost":        0,
                "notes":       eq_notes,
                "active":      False,
                "quantity":    eq_qty,
                "status":      "carried",
                "legality":    9,
                "description": eq_notes,
            },
            "_id":      _short_id(),
            "img":      "systems/mgt2e/icons/items/item.svg",
            "effects":  [],
            "folder":   None,
            "sort":     0,
            "flags":    {},
            "_stats":   _item_stats(with_timestamps=True),
            "ownership": {"default": 0},
        })

    # ------------------------------------------------------------------
    # 8. Assemble actor
    # ------------------------------------------------------------------
    name = str(getattr(char, "name", None) or "Unnamed Traveller")
    total_terms = int(getattr(char, "total_terms", 0) or 0)

    actor: dict[str, Any] = {
        "name": name,
        "type": "traveller",
        "img":  "systems/mgt2e/icons/actors/traveller.svg",
        "system": {
            "speed":      {"base": 6, "value": 6},
            "initiative": {"base": 0, "value": 0},
            "size":       0,
            "rads":       0,
            "weightCarried": 0,
            "heavyLoad":  int(str_v) * 10,
            "maxLoad":    int(str_v) * 20,
            "modifiers": {},
            "hits": {
                "value":     hits_max,
                "max":       hits_max,
                "damage":    0,
                "tmpDamage": 0,
            },
            "description": desc_html,
            "settings": {
                "hideUntrained":     False,
                "onlyBackground":    False,
                "resetOnRoll":       False,
                "columns":           "3",
                "lockCharacteristics": False,
                "sortByCategory":    False,
                "lockSkills":        False,
                "autoAge":           True,
                "autoHits":          True,
            },
            "characteristics": characteristics,
            "skills":          skills,
            "damage": {
                "STR": {"value": 0},
                "DEX": {"value": 0},
                "END": {"value": 0, "tmp": 0},
            },
            "sophont":  sophont,
            "finance":  finance,
            "terms":      total_terms,
            "startAge":   18,
            "termLength": 4,
            "entryYear":  1105,
            "entryAge":   age,
            "currentYear": 1105,
            "birthYear":   1105 - age,
        },
        "items":  items,
        "effects": [],
        "folder": None,
        # Stash the full native character so a round-trip import is lossless.
        # Foundry ignores unknown flag namespaces, so this is inert there.
        "flags":  {"mgt2e": {}, "tvgen": {"app": "TravllerCC", "character": _embed_source(char)}},
        "prototypeToken": {
            "name":        name,
            "displayName": 0,
            "actorLink":   True,
            "width":       1,
            "height":      1,
        },
    }

    return actor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Foundry → native reverse maps (for importing third-party Foundry actors)
# ---------------------------------------------------------------------------

_ID_TO_SKILL: dict[str, str] = {
    "admin": "Admin", "advocate": "Advocate", "animals": "Animals", "art": "Art",
    "astrogation": "Astrogation", "athletics": "Athletics", "broker": "Broker",
    "carouse": "Carouse", "deception": "Deception", "diplomat": "Diplomat",
    "drive": "Drive", "electronics": "Electronics", "engineer": "Engineer",
    "explosives": "Explosives", "flyer": "Flyer", "gambler": "Gambler",
    "guncombat": "Gun Combat", "gunner": "Gunner", "heavyweapons": "Heavy Weapons",
    "independence": "Independence", "investigate": "Investigate",
    "jackofalltrades": "Jack-of-All-Trades", "language": "Language",
    "leadership": "Leadership", "mechanic": "Mechanic", "medic": "Medic",
    "melee": "Melee", "navigation": "Navigation", "persuade": "Persuade",
    "pilot": "Pilot", "profession": "Profession", "recon": "Recon",
    "science": "Science", "seafarer": "Seafarer", "stealth": "Stealth",
    "steward": "Steward", "streetwise": "Streetwise", "survival": "Survival",
    "tactics": "Tactics", "vaccsuit": "Vacc Suit",
    "telepathy": "Telepathy", "clairvoyance": "Clairvoyance",
    "telekinesis": "Telekinesis", "awareness": "Awareness", "teleportation": "Teleportation",
}

_ID_TO_SPEC: dict[str, str] = {
    "strength": "Strength", "dexterity": "Dexterity", "endurance": "Endurance",
    "handling": "Handling", "vetinary": "Veterinary", "training": "Training",
    "performer": "Performer", "holography": "Holography", "instrument": "Instrument",
    "visualMedia": "Visual Media", "write": "Write",
    "hovercraft": "Hovercraft", "mole": "Mole", "track": "Track", "walker": "Walker", "wheel": "Wheel",
    "comms": "Comms", "computers": "Computers", "remoteOps": "Remote Ops", "sensors": "Sensors",
    "mDrive": "M-drive", "jDrive": "J-drive", "lifeSupport": "Life Support", "power": "Power",
    "airship": "Airship", "grav": "Grav", "ornithopter": "Ornithopter", "rotor": "Rotor", "wing": "Wing",
    "turret": "Turret", "ortillery": "Ortillery", "screen": "Screen", "capital": "Capital",
    "archaic": "Archaic", "energy": "Energy", "slug": "Slug",
    "artillery": "Artillery", "portable": "Man Portable", "vehicle": "Vehicle",
    "galanglic": "Anglic", "vilani": "Vilani", "zdetl": "Zdetl", "oynprith": "Oynprith",
    "trokh": "Trokh", "gvegh": "Gvegh",
    "unarmed": "Unarmed", "blade": "Blade", "bludgeon": "Bludgeon", "natural": "Natural",
    "smallCraft": "Small Craft", "spacecraft": "Spacecraft", "capitalShips": "Capital Ships",
    "belter": "Belter", "biologicals": "Biologicals", "civilEngineering": "Civil Engineering",
    "construction": "Construction", "hydroponics": "Hydroponics", "polymers": "Polymers", "robotics": "Robotics",
    "archaeology": "Archaeology", "astronomy": "Astronomy", "biology": "Biology", "chemistry": "Chemistry",
    "cosmology": "Cosmology", "cybernetics": "Cybernetics", "economics": "Economics", "genetics": "Genetics",
    "history": "History", "linquistics": "Linguistics", "philosophy": "Philosophy", "physics": "Physics",
    "planetology": "Planetology", "psionicology": "Psionicology", "psychology": "Psychology",
    "sophontology": "Sophontology", "xenology": "Xenology",
    "oceanShips": "Ocean Ships", "personal": "Personal", "sail": "Sail", "submarine": "Submarine",
    "military": "Military", "naval": "Naval",
}


def _humanize_id(s: str) -> str:
    """Fallback: turn a camelCase/lowercase id into a readable name."""
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s or "")
    return s[:1].upper() + s[1:] if s else s


def _intish(v: Any, default: int = 0) -> int:
    try:
        return int(str(v).replace(",", "").strip() or default)
    except (TypeError, ValueError):
        return default


def _species_id_from_name(name: str) -> str:
    """Best-effort reverse of the export's species display name → a species_id."""
    raw = (name or "").strip()
    if not raw:
        return ""
    try:
        all_species = rules.species()
    except Exception:
        all_species = {}
    candidate = raw.lower().replace(" ", "_")
    if candidate in all_species:
        return candidate
    # Match by display name (the export title-cases the id)
    target = raw.lower()
    for sid, sdef in all_species.items():
        if str(sdef.get("name", "")).strip().lower() == target:
            return sdef.get("id", sid)
    if candidate.replace("_", " ").title() == raw and candidate:
        return candidate  # accept the round-tripped form even if unknown
    return ""


def _rank_bonus_rolls(rank: int) -> int:
    """Muster-out roll bonus for the highest rank reached (MgT 2e p.53)."""
    if rank >= 5:
        return 3
    if rank >= 3:
        return 2
    if rank >= 1:
        return 1
    return 0


def _iter_rank_titles(ranks: Any):
    """Yield (rank_number, title) pairs from a career's ranks structure,
    which may be flat ({num: {...}}) or keyed by assignment ({aid: {num: {...}}})."""
    if not isinstance(ranks, dict):
        return
    for k, v in ranks.items():
        if not isinstance(v, dict):
            continue
        if "title" in v or "bonus" in v:
            ks = str(k).lstrip("-")
            if ks.isdigit():
                yield int(k), v.get("title")
        else:
            yield from _iter_rank_titles(v)


def _rank_num_from_title(cdef: dict, title: str) -> int:
    if not title:
        return 0
    tnorm = _norm(title)
    for num, rt in _iter_rank_titles(cdef.get("ranks") or {}):
        if rt and _norm(rt) == tnorm:
            return num
    return 0


def _reconstruct_careers(actor: dict, char: Character) -> None:
    """Best-effort: rebuild completed_careers + term_history from the Foundry
    'term' items. The term's `assignment` string ("Career: Assignment (Rank)")
    carries enough to map back to career_id / assignment_id / rank, even though
    per-term rolls and benefit counts aren't stored in a Foundry export.
    """
    careers_data = rules.careers()
    name_to_career = {_norm(cdef.get("name", cid)): cid for cid, cdef in careers_data.items()}

    term_items = [
        it for it in (actor.get("items") or [])
        if isinstance(it, dict) and it.get("type") == "term"
    ]
    if not term_items:
        return

    def _tnum(it):
        return _intish(((it.get("system") or {}).get("term") or {}).get("number"), 0)

    term_items.sort(key=_tnum)

    history: list[CareerTerm] = []
    for idx, it in enumerate(term_items, start=1):
        tsys = (it.get("system") or {}).get("term") or {}
        assignment_str = str(tsys.get("assignment") or it.get("name") or "")
        # Strip a leading "Term N: " if present (item names carry it).
        assignment_str = re.sub(r"^Term\s+\d+:\s*", "", assignment_str).strip()
        career_part, _, rest = assignment_str.partition(":")
        career_name = career_part.strip()
        assign_name = rest.strip()
        rank_title = ""
        m = re.search(r"\(([^)]*)\)\s*$", assign_name)
        if m:
            rank_title = m.group(1).strip()
            assign_name = assign_name[: m.start()].strip()

        cid = name_to_career.get(_norm(career_name), "")
        aid = ""
        rank_num = 0
        if cid and cid in careers_data:
            cdef = careers_data[cid]
            for akey, adef in (cdef.get("assignments") or {}).items():
                if _norm(adef.get("name", "")) == _norm(assign_name):
                    aid = akey
                    break
            rank_num = _rank_num_from_title(cdef, rank_title)

        desc = str((it.get("system") or {}).get("description") or "")
        history.append(CareerTerm(
            career_id=cid or (_norm(career_name).replace(" ", "_") or "unknown"),
            assignment_id=aid or (_norm(assign_name).replace(" ", "_")),
            term_number=idx,
            overall_term_number=_tnum(it) or idx,
            rank=rank_num,
            rank_title=rank_title or None,
            survived=True,
            basic_training=(idx == 1),
            events=[desc] if desc else [],
        ))

    # Group consecutive terms in the same career into a completed-career record.
    completed: list[CareerRecord] = []
    for th in history:
        if completed and completed[-1].career_id == th.career_id:
            rec = completed[-1]
            rec.terms_served += 1
            rec.assignment_id = th.assignment_id or rec.assignment_id
            if th.rank > rec.final_rank:
                rec.final_rank = th.rank
                rec.final_rank_title = th.rank_title
            rec.benefit_rolls_earned = rec.terms_served + _rank_bonus_rolls(rec.final_rank)
        else:
            completed.append(CareerRecord(
                career_id=th.career_id,
                assignment_id=th.assignment_id,
                terms_served=1,
                final_rank=th.rank,
                final_rank_title=th.rank_title,
                benefit_rolls_used=0,
                benefit_rolls_earned=1 + _rank_bonus_rolls(th.rank),
            ))

    char.term_history = history
    char.completed_careers = completed
    char.total_terms = len(history)


def foundry_to_character(actor: Any) -> dict:
    """Convert a FoundryVTT MGT2e 'traveller' actor into a native character.

    Two paths:
      • If the actor carries our `flags.tvgen.character` (an actor exported by
        this app), restore that native character verbatim — lossless.
      • Otherwise reverse-map the Foundry actor (characteristics, skills,
        finance, associates, equipment, bio) into a finished character. Career
        history and the lifepath log are NOT reconstructed.

    Returns {"character": <native dict>, "lossless": bool}.
    """
    # Unwrap common export wrappers: [actor], {"actor": actor}.
    if isinstance(actor, list) and actor:
        actor = actor[0]
    if isinstance(actor, dict) and isinstance(actor.get("actor"), dict):
        actor = actor["actor"]
    if not isinstance(actor, dict):
        raise ValueError("Not a recognised Foundry actor (expected a JSON object).")

    # ── Tier A: our embedded source character ─────────────────────────────
    flags = actor.get("flags") or {}
    embedded = (flags.get("tvgen") or {}).get("character")
    if isinstance(embedded, dict) and embedded:
        char = Character(**embedded)
        return {"character": char.model_dump(), "lossless": True}

    # ── Tier B: reverse-map a third-party Foundry actor ───────────────────
    if actor.get("type") != "traveller":
        raise ValueError("Not a Mongoose Traveller actor (system 'mgt2e', type 'traveller').")
    system = actor.get("system") or {}
    char = Character()
    char.name = str(actor.get("name") or "")

    # Characteristics
    fc = system.get("characteristics") or {}

    def _cv(key: str) -> int:
        return _intish((fc.get(key) or {}).get("value"))

    for key in ("STR", "DEX", "END", "INT", "EDU", "SOC"):
        char.characteristics.set(key, _cv(key))
    if _cv("PSI"):
        char.psi = _cv("PSI")
        char.psi_tested = True
    if _cv("REP"):
        char.reputation = _cv("REP")
    for key in ("TER", "WLT", "LCK", "MRL", "STY", "CHA", "FOL"):
        if _cv(key):
            char.extra_characteristics[key] = _cv(key)

    # Skills
    out_skills: list[Skill] = []
    for sid, entry in (system.get("skills") or {}).items():
        if not isinstance(entry, dict):
            continue
        name = _ID_TO_SKILL.get(sid)
        if name is None:
            continue  # unknown/custom skill — skip
        specs = entry.get("specialities") or entry.get("specialties") or {}
        had_spec = False
        for spid, sp in specs.items():
            if not isinstance(sp, dict):
                continue
            # A specialty is trained unless explicitly flagged untrained. Many
            # Foundry exports omit "trained":true on trained specialties and only
            # mark untrained ones with trained:false + value -3, so treat a
            # non-negative value as trained.
            if sp.get("trained") is False:
                continue
            lv = _intish(sp.get("value"), -99)
            if lv < 0:
                continue  # -3 placeholder = untrained
            spec_name = _ID_TO_SPEC.get(spid) or _humanize_id(spid)
            out_skills.append(Skill(name=name, level=lv, speciality=spec_name))
            had_spec = True
        parent_lv = _intish(entry.get("value"), -99)
        if entry.get("trained") is not False and parent_lv >= 0:
            out_skills.append(Skill(name=name, level=parent_lv, speciality=None))
        elif had_spec and not any(s.name == name and s.speciality is None for s in out_skills):
            # Parent sits at 0 when only specialties are trained (cascade rule).
            out_skills.append(Skill(name=name, level=0, speciality=None))
    char.skills = out_skills

    # Finance
    fin = system.get("finance") or {}
    char.credits = _intish(fin.get("cash"))
    char.pension_per_year = _intish(fin.get("pension"))
    char.medical_debt = _intish(fin.get("medicalDebt"))
    char.ship_shares = _intish(fin.get("shipShares"))

    # Bio
    soph = system.get("sophont") or {}
    char.age = _intish(soph.get("age")) or _intish(system.get("entryAge"), 18)
    char.homeworld = str(soph.get("homeworld") or "")
    gender = str(soph.get("gender") or "").strip().lower()
    if gender in ("male", "female"):
        char.gender = gender
    char.species_id = _species_id_from_name(str(soph.get("species") or ""))

    # Items → associates + equipment
    _assoc_kinds = {"ally", "contact", "rival", "enemy"}
    for it in (actor.get("items") or []):
        if not isinstance(it, dict):
            continue
        isys = it.get("system") or {}
        if it.get("type") == "associate":
            kind = str(isys.get("relation")
                       or (isys.get("associate") or {}).get("relationship")
                       or "contact").lower()
            if kind not in _assoc_kinds:
                kind = "contact"
            desc = str(isys.get("description") or it.get("name") or "").strip()
            char.associates.append(Associate(kind=kind, description=desc or f"Unnamed {kind.title()}"))
        elif it.get("type") == "item":
            char.equipment.append(Equipment(
                name=str(it.get("name") or "Item"),
                notes=str(isys.get("notes") or "") or None,
            ))

    # Career history — best-effort from the Foundry "term" items.
    _reconstruct_careers(actor, char)

    char.phase = "done"
    char.log("Imported from a FoundryVTT MGT2e actor — career history reconstructed from term records; "
             "per-term rolls and benefit counts are approximate.")
    return {"character": char.model_dump(), "lossless": False}


def _career_summary(char: Character) -> str:
    """Return a short career/profession string, e.g. 'Scholar: Physician'."""
    completed = getattr(char, "completed_careers", None) or []
    if not completed:
        return ""
    last = completed[-1]
    if isinstance(last, dict):
        cid = last.get("career_id", "")
        aid = last.get("assignment_id") or ""
    else:
        cid = getattr(last, "career_id", "")
        aid = getattr(last, "assignment_id", "") or ""
    parts = [cid.replace("_", " ").title()]
    if aid:
        parts.append(aid.replace("_", " ").title())
    return ": ".join(parts)


def _short_id() -> str:
    """Generate a short random ID compatible with Foundry's ID format."""
    raw = uuid.uuid4().hex[:16]
    return raw
