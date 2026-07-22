"""
smoke_all_careers.py — Full engine smoke test.

Exercises every career × assignment × skill table × event × mishap combination,
forcing deterministic dice so all branches are hit. Reports any exception as a FAIL.

Run:  python tests/smoke_all_careers.py
"""

import sys
import copy
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.engine import dice, lifepath, rules
from app.engine.character import Character, Characteristics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SOCIETY_SPECIES = {
    "third_imperium": "imperial_human",
    "solomani_confederation": "solomani_human",
    "aslan_hierate": "hierate_aslan",
    "glorious_empire": "glorious_empire_aslan",
    "vargr_extents": "extents_vargr",
    "zhodani_consulate": "zhodani",
    "two_thousand_worlds": "kkree",
    "hiver_federation": "hiver",
}

# Droyne caste matching career suffix
DROYNE_CASTE = {
    "droyne_worker":     ("worker",      1),
    "droyne_warrior":    ("warrior",     2),
    "droyne_drone":      ("drone",       3),
    "droyne_technician": ("technician",  4),
    "droyne_sport":      ("sport",       5),
    "droyne_leader":     ("leader",      6),
}


def make_character(career_id: str, cdata: dict) -> Character:
    """Build a character with all stats at 12 and the right society/species/gender."""
    societies  = cdata.get("societies") or cdata.get("allowed_societies") or []
    allowed_sp = cdata.get("allowed_species", [])
    blocked_sp = cdata.get("blocked_species", [])

    # Pick society
    society_id = societies[0] if societies else "third_imperium"

    # Pick species
    if allowed_sp:
        species_id = allowed_sp[0]
    else:
        species_id = SOCIETY_SPECIES.get(society_id, "imperial_human")
        # Respect blocked_species
        if species_id in blocked_sp:
            species_id = "hierate_aslan" if "aslan" in career_id else "imperial_human"

    # Pick gender (Aslan careers care; always use male for military/officer, female for management)
    if "aslan" in career_id or "ge_" in career_id:
        if any(k in career_id for k in ("management", "scientist")):
            gender = "female"
        else:
            gender = "male"
    else:
        gender = "male"

    char = Character()
    char.phase = "career"
    char.society_id = society_id
    char.species_id = species_id
    char.gender = gender
    char.age = 18

    # Max out all stats
    char.characteristics = Characteristics(STR=12, DEX=12, END=12, INT=12, EDU=12, SOC=12)
    char.psi = 12
    char.psi_tested = True
    char.extra_characteristics = {"PSI": 12, "RES": 12}

    # Droyne-specific fields
    if career_id in DROYNE_CASTE:
        caste, caste_num = DROYNE_CASTE[career_id]
        char.droyne_caste = caste
        char.droyne_caste_number = caste_num
        char.droyne_caste_mods_applied = True

    # Hiver-specific
    if "hiver" in career_id:
        char.hiver_nest_type = "social"

    # Zhodani: proles have SOC ≤ 9
    if career_id == "zhodani_prole":
        char.characteristics.SOC = 7

    # K'kree: set required fields
    if "kkree" in career_id:
        char.kkree_wives = 2
        char.kkree_family_members = [
            {"role": "warrior", "description": "Smoke-test warrior"},
            {"role": "specialist", "description": "Smoke-test specialist"},
            {"role": "servant", "description": "Smoke-test servant"},
            {"role": "servant", "description": "Smoke-test servant"},
            {"role": "servant", "description": "Smoke-test servant"},
        ]

    # Aslan outcast needs pre_outcast_soc
    if "outcast" in career_id:
        char.pre_outcast_soc = 5
        char.characteristics.SOC = 1

    # aslan_setup_status: provide a completed rite dict so careers don't block on it
    if "aslan" in career_id or "ge_" in career_id:
        char.aslan_setup_status = {"rite_score": 6, "complete": True}

    return char


def force(val: int):
    """Pre-load a single forced roll."""
    dice.set_forced_rolls([val])


def force_n(vals: list):
    dice.set_forced_rolls(vals)


# ---------------------------------------------------------------------------
# Main smoke runner
# ---------------------------------------------------------------------------

PASSES = []
FAILS  = []


def run(label: str, fn, *args, **kwargs):
    """Call fn(*args, **kwargs), return result or None on exception."""
    try:
        result = fn(*args, **kwargs)
        return result
    except Exception as exc:
        FAILS.append((label, traceback.format_exc()))
        return None


def smoke_career(career_id: str, cdata: dict):
    assignments = cdata.get("assignments", {})
    if isinstance(assignments, list):
        assignment_ids = [a["id"] for a in assignments]
    else:
        assignment_ids = list(assignments.keys())

    for assign_id in assignment_ids:
        smoke_assignment(career_id, cdata, assign_id)


def smoke_assignment(career_id: str, cdata: dict, assign_id: str):
    label_base = f"{career_id}/{assign_id}"

    # Check if this assignment has a gender restriction — if so, override
    assignments = cdata.get("assignments", {})
    if isinstance(assignments, list):
        assign_data = next((a for a in assignments if a.get("id") == assign_id), {})
    else:
        assign_data = assignments.get(assign_id, {})
    allowed_genders = assign_data.get("allowed_genders", [])

    # ---- Pass path (survive + advance) ----
    char = make_character(career_id, cdata)
    if allowed_genders and char.gender not in allowed_genders:
        char.gender = allowed_genders[0]
    force(12)
    res = run(f"{label_base} qualify", lifepath.qualify_for_career, char, career_id)
    if res is None:
        return

    # If not qualified, try auto-qualify by forcing the character into it
    if not char.current_term:
        force_n([12, 12, 12])
        res = run(f"{label_base} start_term", lifepath.start_term, char, career_id, assign_id)
        if res is None:
            return
    else:
        # Was auto-qualified or already in a term; need start_term
        force_n([12, 12, 12])
        res = run(f"{label_base} start_term", lifepath.start_term, char, career_id, assign_id)
        if res is None:
            return

    # Smoke each skill table valid for this assignment
    skill_tables = cdata.get("skill_tables", {})
    for tbl_key, tbl_data in skill_tables.items():
        if not isinstance(tbl_data, dict):
            continue
        # Skip tables locked to a different assignment
        tbl_assign = tbl_data.get("assignment_only")
        if tbl_assign and tbl_assign != assign_id:
            continue
        # Skip officer table unless commissioned
        if tbl_key == "officer" and not (char.current_term and char.current_term.commissioned):
            continue
        for roll_val in range(1, 7):
            char_copy = copy.deepcopy(char)
            force(roll_val)
            run(f"{label_base} skill_table/{tbl_key}/{roll_val}",
                lifepath.roll_on_skill_table, char_copy, tbl_key)

    # Survival pass
    force(12)
    res_surv = run(f"{label_base} survival/pass", lifepath.survival_roll, char)
    if res_surv is None:
        return

    # Events 2–12
    for ev in range(2, 13):
        char_ev = copy.deepcopy(char)
        # Force the 2D event roll to ev; give 6 extra rolls for any sub-rolls
        force_n([ev, 6, 6, 6, 6, 6, 6, 6])
        run(f"{label_base} event/{ev}", lifepath.event_roll, char_ev)

    # Advancement
    force(12)
    run(f"{label_base} advancement", lifepath.advancement_roll, char)

    # End term
    force_n([6, 6, 6, 6])
    run(f"{label_base} end_term", lifepath.end_term, char)

    PASSES.append(label_base + " [pass path]")

    # ---- Fail path (mishap) ----
    char2 = make_character(career_id, cdata)
    if allowed_genders and char2.gender not in allowed_genders:
        char2.gender = allowed_genders[0]
    force(12)
    run(f"{label_base} qualify(mishap path)", lifepath.qualify_for_career, char2, career_id)
    force_n([12, 12, 12])
    res2 = run(f"{label_base} start_term(mishap path)", lifepath.start_term, char2, career_id, assign_id)
    if res2 is None:
        return

    force(2)  # fail survival
    res_surv2 = run(f"{label_base} survival/fail", lifepath.survival_roll, char2)
    if res_surv2 is None:
        return

    # If career has no_survival flag, skip mishap path
    if cdata.get("no_survival"):
        PASSES.append(label_base + " [no-survival skip]")
        return

    # Check if survival was actually failed
    if res_surv2.get("survived", True):
        # Hiver / no-survival careers — skip mishap
        PASSES.append(label_base + " [mishap path skipped — no fail possible]")
        return

    for mh in range(1, 7):
        char_mh = copy.deepcopy(char2)
        force_n([mh, 6, 6, 6, 6, 6])
        run(f"{label_base} mishap/{mh}", lifepath.mishap_roll, char_mh)

    PASSES.append(label_base + " [mishap path]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    all_careers = rules.careers()

    print(f"Smoking {len(all_careers)} careers...\n")

    for career_id, cdata in sorted(all_careers.items()):
        print(f"  {career_id}...", end="", flush=True)
        try:
            smoke_career(career_id, cdata)
            print(" ok")
        except Exception as exc:
            FAILS.append((f"{career_id} [outer]", traceback.format_exc()))
            print(f" OUTER EXCEPTION")

    print(f"\n{'='*60}")
    print(f"PASS paths:  {len(PASSES)}")
    print(f"FAIL paths:  {len(FAILS)}")

    if FAILS:
        print(f"\n{'='*60}")
        print("FAILURES:")
        for label, tb in FAILS:
            print(f"\n--- {label} ---")
            # Print just the last 5 lines of the traceback
            lines = tb.strip().split("\n")
            print("\n".join(lines[-5:]))

    sys.exit(0 if not FAILS else 1)
