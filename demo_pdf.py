"""Quick demo: generate a sample character sheet PDF to preview the new design."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.engine.character import Character, Characteristics
from app.engine.character import Skill, CareerRecord, Associate, Equipment, CareerTerm
from app.engine import pdf_sheet

char = Character(
    name="Franky",
    homeworld="Bowman",
    homeworld_uwp="B542697-9",
    species_id="solomani_human",
    society_id="solomani_confederation",
    age=38,
    total_terms=5,
    credits=12000,
    medical_debt=1250,
    ship_shares=4,
    pension_per_year=0,
    psi=0,
    user_notes=(
        "Owns 4 Ship Shares (worth Mcr 4)\n"
        "Member of the Traveller's Aid Society"
    ),
    characteristics=Characteristics(
        STR=10, DEX=11, END=4,
        INT=12, EDU=15, SOC=13,
    ),
    skills=[
        Skill(name="Science",    speciality="Linguistics", level=2),
        Skill(name="Leadership",                           level=1),
        Skill(name="Melee",      speciality="Blade",       level=1),
        Skill(name="Navigation",                           level=1),
        Skill(name="Athletics",                            level=0),
        Skill(name="Electronics",                          level=0),
        Skill(name="Gun Combat",                           level=0),
        Skill(name="Gunner",                               level=0),
        Skill(name="Mechanic",                             level=0),
        Skill(name="Melee",                                level=0),
        Skill(name="Pilot",                                level=0),
        Skill(name="Science",                              level=0),
        Skill(name="Vacc Suit",                            level=0),
    ],
    completed_careers=[
        CareerRecord(
            career_id="university", assignment_id="university",
            terms_served=1, final_rank=0, final_rank_title="",
            left_due_to="voluntary",
        ),
        CareerRecord(
            career_id="navy", assignment_id="flight",
            terms_served=4, final_rank=3, final_rank_title="Lieutenant",
            left_due_to="voluntary",
        ),
    ],
    equipment=[
        Equipment(name="Small spacecraft of your choice (price limit Mcr10) limited to Tech Level 12"),
    ],
    associates=[
        Associate(kind="ally",    description="Fellow clique member"),
        Associate(kind="ally",    description="Fellow clique member"),
        Associate(kind="contact", description="Random Contact"),
        Associate(kind="enemy",   description="Fellow crewmate whose crime you foiled"),
        Associate(kind="enemy",   description="Fellow crewmate whose crime you foiled"),
    ],
    term_history=[
        CareerTerm(
            career_id="university", assignment_id="university",
            term_number=1, overall_term_number=1,
            events=[
                "Age 18: Entered University",
                "Age 20: Joined a clique. Gained 2 allies",
                "Age 22: Graduated University with Honours",
            ],
        ),
        CareerTerm(
            career_id="navy", assignment_id="flight",
            term_number=1, overall_term_number=2,
            events=[
                "Age 22: Failed to get a commission on entry to the navy",
                "Age 22: Became Crewman (Navy, Flight)",
                "Age 24: New contact",
                "Age 26: Commissioned as an Ensign",
            ],
        ),
        CareerTerm(
            career_id="navy", assignment_id="flight",
            term_number=2, overall_term_number=3,
            events=[
                "Age 28: Took opportunity for personal profit",
            ],
        ),
        CareerTerm(
            career_id="navy", assignment_id="flight",
            term_number=3, overall_term_number=4,
            events=[
                "Age 32: Member of the frozen watch",
                "Age 32: Injured",
                "Age 32: Foiled an attempted crime",
                "Age 34: Promoted to Sublieutenant (rank 2)",
            ],
        ),
        CareerTerm(
            career_id="navy", assignment_id="flight",
            term_number=4, overall_term_number=5,
            events=[
                "Age 36: Foiled an attempted crime",
                "Age 38: Promoted to Lieutenant (rank 3)",
            ],
        ),
    ],
)

out_path = os.path.join(os.path.dirname(__file__), "demo_sheet.pdf")
pdf_bytes = pdf_sheet.generate_character_pdf(char)
with open(out_path, "wb") as f:
    f.write(pdf_bytes)

print(f"Written: {out_path}  ({len(pdf_bytes):,} bytes)")
