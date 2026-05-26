"""
foundry_export.py — Convert a TravllerCC Character into a FoundryVTT MGT2e actor JSON.

The output is a dict that can be JSON-serialised and imported directly into
FoundryVTT via the MGT2e system's "Import Actor" feature (or drag-dropped from
the file system).
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from .character import Character

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
    # We build a working dict: {foundry_skill_id: {"base": level, "specs": {spec_id: level}}}
    # then emit the Foundry skill object.

    _skill_work: dict[str, dict] = {}   # skill_id → {"base": int, "specs": {id: int}}

    for sk in (char.skills or []):
        skill_name = sk.get("name") if isinstance(sk, dict) else getattr(sk, "name", "")
        skill_level = sk.get("level", 0) if isinstance(sk, dict) else getattr(sk, "level", 0)
        skill_spec = sk.get("speciality") if isinstance(sk, dict) else getattr(sk, "speciality", None)

        sid = _skill_id(skill_name)
        if sid is None:
            continue  # unknown skill — skip

        if sid not in _skill_work:
            _skill_work[sid] = {"base": -1, "specs": {}}

        if not skill_spec or _norm(skill_spec) == "any":
            # Base skill entry
            cur = _skill_work[sid]["base"]
            _skill_work[sid]["base"] = max(cur, int(skill_level))
        else:
            spec_id = _spec_id(skill_spec)
            if spec_id is None:
                # Unknown speciality — use lowercased slug
                spec_id = re.sub(r"[^a-z0-9]", "", _norm(skill_spec))
            cur = _skill_work[sid]["specs"].get(spec_id, -1)
            _skill_work[sid]["specs"][spec_id] = max(cur, int(skill_level))

    # Build Foundry skills object
    skills: dict[str, Any] = {}
    for sid, data in _skill_work.items():
        base_val = data["base"] if data["base"] >= 0 else 0
        specs = data["specs"]

        entry: dict[str, Any] = {
            "id": sid,
            "value": str(base_val) if base_val > 0 else base_val,
            "trained": True,
        }
        if specs:
            entry["specialities"] = {
                sp_id: {"id": sp_id, "value": str(sp_lv)}
                for sp_id, sp_lv in specs.items()
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
    finance: dict[str, Any] = {
        "cash":        str(int(getattr(char, "credits", 0) or 0)),
        "pension":     str(int(getattr(char, "pension_per_year", 0) or 0)),
        "medicalDebt": str(int(getattr(char, "medical_debt", 0) or 0)),
        "mortgage":    "0",
        "livingCosts": "0",
        "otherIncome": "0",
        "description": "",
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
    # 7. Associates → items
    # ------------------------------------------------------------------
    items: list[dict] = []
    for assoc in (getattr(char, "associates", None) or []):
        if isinstance(assoc, dict):
            kind = str(assoc.get("kind", "contact")).lower()
            desc = str(assoc.get("description", ""))
        else:
            kind = str(getattr(assoc, "kind", "contact")).lower()
            desc = str(getattr(assoc, "description", ""))

        defaults = _ASSOCIATE_DEFAULTS.get(kind, _ASSOCIATE_DEFAULTS["contact"])
        display_name = desc if desc else f"Unnamed {kind.title()}"

        item_id = _short_id()
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
            "_id":      item_id,
            "img":      "systems/mgt2e/icons/items/item.svg",
            "effects":  [],
            "folder":   None,
            "sort":     0,
            "flags":    {},
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
            "terms":    total_terms,
            "startAge": 18,
            "termLength": 4,
            "entryYear": 1105,
            "entryAge":  18,
            "currentYear": 1105 + total_terms * 4,
            "birthYear":   1105 + total_terms * 4 - age,
        },
        "items":  items,
        "effects": [],
        "folder": None,
        "flags":  {"mgt2e": {}},
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
