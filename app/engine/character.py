"""
Character state model.

The character is the single source of truth for a Traveller being built.
It's serializable to JSON and round-trips through the API — the client
holds it in localStorage, sends it with each action, and gets back the
updated version.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Characteristics(BaseModel):
    STR: int = 0
    DEX: int = 0
    END: int = 0
    INT: int = 0
    EDU: int = 0
    SOC: int = 0

    def get(self, key: str) -> int:
        return getattr(self, key.upper())

    def set(self, key: str, value: int) -> None:
        setattr(self, key.upper(), max(0, value))


class Skill(BaseModel):
    name: str
    level: int = 0
    speciality: Optional[str] = None


class Associate(BaseModel):
    """Allies, Contacts, Rivals, Enemies."""
    kind: str  # "ally" | "contact" | "rival" | "enemy"
    description: str = ""


class CareerTerm(BaseModel):
    """One term (4 years) in a career."""
    career_id: str
    assignment_id: str
    term_number: int  # 1-based within this career
    overall_term_number: int  # 1-based across the whole lifepath
    rank: int = 0
    rank_title: Optional[str] = None
    commissioned: bool = False
    events: list[str] = Field(default_factory=list)
    skills_gained: list[str] = Field(default_factory=list)
    survived: Optional[bool] = None
    advanced: Optional[bool] = None
    mishap: Optional[str] = None
    basic_training: bool = False


class CareerRecord(BaseModel):
    """Summary of a completed career."""
    career_id: str
    assignment_id: str
    terms_served: int
    final_rank: int
    final_rank_title: Optional[str] = None
    commissioned: bool = False
    left_due_to: str = "voluntary"  # "voluntary" | "mishap" | "aged_out"


class Equipment(BaseModel):
    name: str
    quantity: int = 1
    notes: Optional[str] = None


class Character(BaseModel):
    # Identity
    name: str = ""
    homeworld: str = ""
    homeworld_uwp: str = ""
    species_id: str = "imperial_human"

    # Core stats
    characteristics: Characteristics = Field(default_factory=Characteristics)
    age: int = 18

    # Skills
    skills: list[Skill] = Field(default_factory=list)

    # Career history
    current_term: Optional[CareerTerm] = None
    completed_careers: list[CareerRecord] = Field(default_factory=list)
    term_history: list[CareerTerm] = Field(default_factory=list)
    total_terms: int = 0

    # Goodies and baggage
    credits: int = 0
    medical_debt: int = 0
    ship_shares: int = 0
    pension_per_year: int = 0
    equipment: list[Equipment] = Field(default_factory=list)
    associates: list[Associate] = Field(default_factory=list)
    traits: list[dict] = Field(default_factory=list)
    pending_benefit_rolls: int = 0
    cash_rolls_used: int = 0
    dm_next_advancement: int = 0
    dm_next_qualification: int = 0
    dm_next_benefit: int = 0

    # Career-transfer offer from an event (e.g. army[10] "transfer to the
    # Marines without a Qualification roll"). Set when the player elects the
    # transfer branch; consumed when the next career is chosen (qualification
    # is skipped for the matching target career).
    pending_transfer_career_id: Optional[str] = None

    # Pre-career education state
    pre_career_status: dict = Field(default_factory=dict)
    starts_commissioned_career_id: Optional[str] = None

    # Anagathics
    anagathics_purchased_terms: int = 0
    anagathics_addicted: bool = False

    # Free-form player notes (rendered on the sheet)
    user_notes: str = ""

    # Boon / re-roll pool (GM-configurable; zero = unlimited or unused)
    boon_rolls_total: int = 0
    boon_rolls_remaining: int = 0

    # Psionics (MgT 2e Core p.176). Set when the optional test is performed.
    psi: int = 0
    psi_tested: bool = False
    psi_trained_talents: list[str] = Field(default_factory=list)

    # Capsule description (generated in finalize phase, persisted for export)
    capsule_description: str = ""

    # Creation flow state
    phase: str = "characteristics"
    # characteristics | species | background | pre_career | career | mustering | finalize | done
    notes: list[str] = Field(default_factory=list)
    dead: bool = False
    death_reason: Optional[str] = None

    def add_skill(self, name: str, level: int = 0, speciality: Optional[str] = None) -> str:
        """Add or upgrade a skill. Returns a human-readable log message.

        Rulebook nuance (MgT 2e, p.59): when a character gains a
        speciality (e.g. "Gun Combat (slug)") at level 1+, they also
        have the parent skill ("Gun Combat") at level 0. The parent
        is auto-seeded here so the sheet shows it.
        """
        for existing in self.skills:
            if existing.name == name and existing.speciality == speciality:
                if existing.level < 4:
                    existing.level += level if level > 0 else 1
                    if existing.level > 4:
                        existing.level = 4
                    return f"Increased {existing.name}{f' ({speciality})' if speciality else ''} to {existing.level}"
                else:
                    return f"{name} already at maximum level 4"

        new_level = max(level, 0)
        self.skills.append(Skill(name=name, level=new_level, speciality=speciality))

        # Auto-seed parent skill at level 0 when gaining a speciality at 1+.
        if speciality and new_level >= 1:
            has_parent = any(
                s.name == name and s.speciality is None for s in self.skills
            )
            if not has_parent:
                self.skills.append(Skill(name=name, level=0, speciality=None))

        return f"Gained {name}{f' ({speciality})' if speciality else ''} {new_level}"

    def log(self, message: str) -> None:
        self.notes.append(message)


def new_character() -> Character:
    return Character()
