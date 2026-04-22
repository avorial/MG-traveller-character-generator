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
    ship_shares: int = 0
    pension_per_year: int = 0
    equipment: list[Equipment] = Field(default_factory=list)
    associates: list[Associate] = Field(default_factory=list)
    traits: list[dict] = Field(default_factory=list)  # Species traits
    pending_benefit_rolls: int = 0
    cash_rolls_used: int = 0
    dm_next_advancement: int = 0
    dm_next_qualification: int = 0
    dm_next_benefit: int = 0

    # Pre-career education state
    pre_career_status: dict = Field(default_factory=dict)
    # {
    #   "track": "university" | "military_academy" | None,
    #   "service": "army" | "marine" | "navy" | None,
    #   "stage": "none" | "enrolled" | "graduated" | "failed_grad" | "not_qualified" | "skipped",
    #   "outcome": "pass" | "honours" | "fail" | "skipped" | "not_qualified" | None,
    #   "skill_picks_remaining": int,
    #   "skill_pool": [str, ...]
    # }
    # Set by the academy path when the character graduates and earns
    # a commission: first term in this career starts at Rank 1 commissioned.
    starts_commissioned_career_id: Optional[str] = None

    # Creation flow state
    phase: str = "characteristics"  # characteristics | species | background | pre_career | career | mustering | finalize | done
    notes: list[str] = Field(default_factory=list)
    dead: bool = False
    death_reason: Optional[str] = None

    def add_skill(self, name: str, level: int = 0, speciality: Optional[str] = None) -> str:
        """Add or upgrade a skill. Returns a human-readable log message."""
        # Check for existing skill with same name + speciality
        for existing in self.skills:
            if existing.name == name and existing.speciality == speciality:
                if existing.level < 4:  # max skill level in creation
                    existing.level += level if level > 0 else 1
                    if existing.level > 4:
                        existing.level = 4
                    return f"Increased {existing.name}{f' ({speciality})' if speciality else ''} to {existing.level}"
                else:
                    return f"{name} already at maximum level 4"
        # New skill
        self.skills.append(Skill(name=name, level=max(level, 0), speciality=speciality))
        return f"Gained {name}{f' ({speciality})' if speciality else ''} {max(level, 0)}"

    def log(self, message: str) -> None:
        self.notes.append(message)


def new_character() -> Character:
    return Character()
