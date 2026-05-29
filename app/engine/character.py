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

    def get(self, key: str) -> Optional[int]:
        """Return characteristic value, or None for unknown keys (e.g. PSI)."""
        k = key.upper()
        try:
            return getattr(self, k)
        except AttributeError:
            return None

    def set(self, key: str, value: int) -> None:
        k = key.upper()
        try:
            setattr(self, k, max(0, value))
        except AttributeError:
            pass  # Unknown characteristic — silently ignore


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
    benefit_forfeited: bool = False
    survival_roll_total: Optional[int] = None
    # SolSec Secret Agent: the cover career used for survival/advancement rolls
    cover_career_id: Optional[str] = None
    # Confederation Navy mishap 2: term spent in cryo, character stays in service
    frozen_watch: bool = False


class CareerRecord(BaseModel):
    """Summary of a completed career."""
    career_id: str
    assignment_id: str
    terms_served: int
    final_rank: int
    final_rank_title: Optional[str] = None
    commissioned: bool = False
    left_due_to: str = "voluntary"  # "voluntary" | "mishap" | "aged_out"
    benefit_rolls_used: int = 0     # rolls already spent on this career's muster table
    benefit_rolls_earned: int = 0   # total rolls granted (terms + rank bonus, after forfeit)


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
    society_id: str = "third_imperium"

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
    pre_career_terms: int = 0

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
    dm_permanent_advancement: int = 0  # never consumed — stacks every roll for life
    dm_next_qualification: int = 0
    dm_next_benefit: int = 0
    dm_next_survival: int = 0
    dm_next_events: int = 0            # consumed on the next events roll (Heroism Rule)

    # Storm Knight Heroism Rule: player chooses DM-1 or DM-2 on survival before rolling.
    # If they survive, the absolute value becomes dm_next_events. Resets each term.
    storm_knight_heroism_dm: int = 0   # 0 = none chosen, -1 or -2 = heroism level

    # Storm Knights: set True when a career-ending mishap ends a Storm Knight career.
    # Blocks entry to all other Orders for the remainder of character creation.
    storm_knight_ejected: bool = False

    # Storm Knight honours (accumulated across all Storm Knight terms).
    # By Deed: granted via specific heroic career events.
    # By Rank: granted upon reaching rank 6, or passing advancement at rank 6.
    # Grand Cross: granted by passing advancement when already Knight Commander By Rank.
    knight_commander_by_deed: bool = False
    knight_commander_by_rank: bool = False
    knight_grand_cross: bool = False

    # Career-transfer offer from an event (e.g. army[10] "transfer to the
    # Marines without a Qualification roll"). Set when the player elects the
    # transfer branch; consumed when the next career is chosen (qualification
    # is skipped for the matching target career).
    pending_transfer_career_id: Optional[str] = None

    # Rank to carry into the next career via a transfer (e.g. Zhodani Merchant
    # event 3 → Zhodani Navy at same rank). Consumed when start_term fires for
    # the new career immediately after pending_transfer_career_id is consumed.
    pending_transfer_rank: Optional[int] = None

    # Forced next career — set by pre-career education events (e.g. event 4
    # natural 2 → Prisoner, event 11 Drifter / Draft). The career picker will
    # only allow this career until it is consumed.
    forced_next_career_id: Optional[str] = None

    # Ihatei restriction — set when an Aslan joins the ihatei's retinue.
    # When True, the character must enter a Core Rulebook career next term
    # (one with no societies field, or societies includes "third_imperium").
    # Consumed when qualification for a core career succeeds.
    next_career_must_be_core: bool = False

    # Careers the character may auto-qualify for on next attempt (no roll needed).
    # Set by events like Party event 3 ("Citizen or Merchant next term, auto-qualify").
    # Each career ID is consumed when that career's qualification fires.
    auto_qualify_career_ids: list[str] = Field(default_factory=list)

    # Solomani Passing status: a solomani_mixed character who has purchased
    # falsified genetic records (30,000 Cr debt).  While True the character is
    # treated as Racial Solomani for career qualification — Party Patronage DM
    # applies; Mixed Heritage penalty is suppressed.
    # Exposed (set to False + SOC halved) on a natural 2 survival roll in any
    # military or Party career.
    solomani_passing: bool = False

    # Careers permanently banned from re-entry (e.g. Scout event 2 failure).
    banned_career_ids: list[str] = Field(default_factory=list)

    # Failed qualification attempts this career-selection round.
    # RAW: each failed career attempt carries DM-1 to subsequent qualification
    # rolls in the same round (resets when a term is completed).
    failed_qualifications_this_term: int = 0

    # Pending interactive choice from a Life Event roll. Cleared once the
    # player resolves it via /api/character/life-event-choice.
    # Shape: {"kind": str, ...context keys...}
    pending_life_event_choice: Optional[dict] = None

    # Pending injury stat choice. Set by apply_injury when the player must
    # choose which physical characteristic absorbs the damage.
    # Shape: {"roll": int, "title": str, "damage_to_chosen": int,
    #         "auto_reduce_others": int, "choices": [str], "prompt": str}
    pending_injury_choice: Optional[dict] = None

    # Pending treatment choice. Set by resolve_injury_choice after the player
    # picks which stat is hit but before the damage is actually applied.
    # Player then chooses: accept the stat loss (no cost) OR pay for treatment
    # (medical debt, stat stays intact). Shape:
    # {"chosen_stat": str, "damage_to_chosen": int, "auto_reduce_others": int,
    #  "others": [str], "gross_debt": int, "net_debt": int, "covered": int,
    #  "coverage_pct": int, "medical_bills_roll": dict, "title": str}
    pending_injury_treatment_choice: Optional[dict] = None

    # Pending interactive choice from a career mishap roll. Cleared once
    # the player resolves it via /api/character/career-mishap-choice.
    # Shape varies by type: "injury_severity_choice", "stat_choice",
    # "skill_choice", "pending_choice", "skill_check", "free_skill_choice"
    pending_career_mishap_choice: Optional[dict] = None

    # Pending interactive choice from a career event roll. Same shape as
    # pending_career_mishap_choice. Cleared once resolved via
    # /api/character/career-event-choice.
    pending_career_event_choice: Optional[dict] = None

    # Pending skill choice from a mustering-out benefit roll.
    # Set when the rolled benefit is "Skill A N or Skill B N or ..." and the
    # player must pick one. Shape: {"options": [str], "raw": str}
    # Cleared once the player resolves it via /api/character/muster-benefit-choice.
    pending_muster_benefit_choice: Optional[dict] = None

    # DM+2 tokens from Life Event 10 (Good Fortune). Each token can be
    # voluntarily applied to one mustering-out benefit roll.
    good_fortune_benefit_dm: int = 0

    # Pre-career education state
    pre_career_status: dict = Field(default_factory=dict)
    # Permanent career modifiers granted by pre-career education (e.g. colonial
    # upbringing −2 qualification DM, merchant academy +1 advancement DM).
    # Keys: qualification_dm, commission_dm, first_career_commission_dm,
    #       advancement_dm, advancement_dm_careers, auto_rank, auto_rank_careers,
    #       bonus_qualify_careers, bonus_qualify_dm, psion_career_auto_entry,
    #       spacer_career_dm, spacer_career_id, spacer_assignment_id.
    pre_career_permanent_dms: dict = Field(default_factory=dict)
    starts_commissioned_career_id: Optional[str] = None
    # Normal Military Academy grad: roll Commission 8+ with this DM before first term.
    academy_commission_career_id: Optional[str] = None
    academy_commission_dm: int = 0
    # Failed grad who didn't roll a natural 2: auto-entry into tied career, no commission roll.
    auto_entry_career_id: Optional[str] = None

    # Anagathics (MG2e RAW: SOC 10+ at start of each term ≥ 4)
    # Player's one-time interest setting: None=not yet asked, "yes"=show per-term prompt, "no"=never prompt
    anagathics_interest: Optional[str] = None
    anagathics_active: bool = False          # currently using anagathics
    anagathics_terms_used: int = 0           # terms already on anagathics (for positive aging DM)
    anagathics_pending_cost: int = 0         # Cr cost for this term (1D×25000), paid at end
    anagathics_addicted: bool = False

    # Home Forces Reserves (Solomani parallel service)
    # Eligible non-military Solomani may enlist alongside their main career.
    # component: "groundside" | "naval"
    home_forces_enrolled: bool = False
    home_forces_component: Optional[str] = None
    home_forces_rank: int = 0
    home_forces_trained: bool = False  # initial training roll done

    # Aslan Hierate character generation
    # gender: "male" | "female" | None (not yet chosen or not applicable)
    gender: Optional[str] = None
    # Clan Shares: Aslan equivalent of Ship Shares
    clan_shares: int = 0
    # Aslan background setup state: tracks clan, ancestry, family, rite
    # Keys: phase, clan_type, clan_dm_ancestral_deeds, ancestral_territory,
    #       family_position, rite_score, rite_doubles_roll, rite_doubles_result
    aslan_setup_status: Optional[dict] = None

    # K'kree family tracking (for K'kree species only)
    kkree_wives: int = 0
    kkree_family_members: list[dict] = Field(default_factory=list)
    # Role breakdown of family: [{"role": "warrior"|"specialist"|"servant", "description": str}, ...]
    kkree_soc_rank_degree: str = "servant_of_rankholder"
    # "servant_of_rankholder" | "kinsman_of_rankholder" | "rankholder"
    kkree_specialist_area: Optional[str] = None
    # The specialist area rolled at career start (e.g. "warrior", "mercantile", "technical", "naval")

    # SolSec Monitor (Solomani informer role, parallel to any non-SolSec career)
    # DM+1 to advancement; nat-2 survival → SolSec mishap instead of career mishap;
    # nat-12 survival → SolSec event + SolSec Contact.
    solsec_monitor: bool = False
    solsec_monitor_rank: int = 0

    # Free-form player notes (rendered on the sheet)
    user_notes: str = ""

    # Boon / re-roll pool (GM-configurable; zero = unlimited or unused)
    boon_rolls_total: int = 0
    boon_rolls_remaining: int = 0

    # Optional / house-rule extra characteristics (PSI, WLT, LCK, MRL, STY, TER).
    # Keys are the 3-letter stat ids; values are rolled integers.
    extra_characteristics: dict = Field(default_factory=dict)

    # Reputation (REP) — used by careers such as Bounty Hunter (Pirates of Drinax).
    # Starts at 0; modified by career events and mishaps; used as the DM base
    # for REP-keyed advancement rolls.
    reputation: int = 0

    # Psionics (MgT 2e Core p.176). Set when the optional test is performed.
    psi: int = 0
    psi_tested: bool = False
    psi_trained_talents: list[str] = Field(default_factory=list)

    # Skills this species can never gain (e.g. Broker, Gambler for Dolphins/Orca).
    # Populated from species JSON "forbidden_skills" field when species is applied.
    forbidden_skills: list[str] = Field(default_factory=list)

    # Career package (optional alternative to normal careers)
    career_package_id: Optional[str] = None
    career_package_taken: bool = False

    # Droyne caste system
    # droyne_caste: the string name of the caste ("worker", "warrior", etc.)
    # droyne_caste_number: the 1D roll result (1=Worker, 2=Warrior, 3=Drone,
    #   4=Technician, 5=Sport, 6=Leader) — used as a negative DM in continuation checks.
    droyne_caste: Optional[str] = None
    droyne_caste_number: int = 0
    # Tracks whether caste modifiers have already been applied to avoid double-applying.
    droyne_caste_mods_applied: bool = False

    # Hiver nest type ("industrial" | "economic" | "generalist" | "academic" | "social")
    # Also tracks whether the Hiver has attained Senior or Manipulator status (for one-time bonuses).
    hiver_nest_type: Optional[str] = None
    hiver_senior_bonus_awarded: bool = False
    hiver_manipulator_bonus_awarded: bool = False

    # Capsule description (generated in finalize phase, persisted for export)
    capsule_description: str = ""

    # Pre-outcast / pre-landless SOC snapshot.
    # Set automatically whenever SOC is first capped to ≤2 on disgrace-entry
    # (mishap stat_cap, aslan_mgmt_accused, ge_hierate_capture, smuggle fail).
    # Used by the redemption events to restore SOC without "apply manually".
    pre_outcast_soc: int = 0

    # Set by event on_fail effects that mean "you are ejected from this career".
    # force_career_end: checked in survival_roll → skip dice, auto-fail.
    # ejected_by_event:  survives into mishap_roll → skip mishap table, just end career.
    force_career_end: bool = False
    ejected_by_event: bool = False

    # Robot character type
    # "biological" — normal Traveller (default)
    # "robot"      — built via the robot construction phase; bypasses lifepath
    character_type: str = "biological"
    # Stored robot construction config (set during robot_build phase).
    # Structure mirrors ROBOT_DEFAULT_CONFIG on the client.
    robot_config: Optional[dict] = None

    # Creation flow state
    phase: str = "characteristics"
    # characteristics | robot_build | species | background | pre_career | career | mustering | finalize | done
    notes: list[str] = Field(default_factory=list)
    dead: bool = False
    death_reason: Optional[str] = None

    def add_skill(self, name: str, level: int = 0, speciality: Optional[str] = None,
                  fixed_level: bool = False) -> str:
        """Add or upgrade a skill. Returns a human-readable log message.

        Three gain modes (MgT 2e p.59):

        level == 0  (basic training, background skills)
            Grant at 0 if the character doesn't have it yet; do nothing if they do.

        level > 0, fixed_level=False  (table roll / "gain a level in X")
            Level 1 if new; increment by *level* if already trained.
            This is the "no rank listed" rule: "gains the skill at level 1 or increases
            the skill by one level if already trained."

        level > 0, fixed_level=True  (rank bonus / explicit-level event grant)
            The skill is gained at exactly *level* — take it only if it is better than
            the current value (i.e. max(current, level)).  "If a rank is listed, you gain
            it at that level only if it is better than your current level."

        Rulebook nuance (MgT 2e, p.59): when a character gains a
        speciality (e.g. "Gun Combat (Slug)") at level 1+, they also
        have the parent skill ("Gun Combat") at level 0. The parent
        is auto-seeded here so the sheet shows it.
        """
        # Species forbidden skills — silently skip rather than error, since the
        # grant may come from a generic table roll that the character can't avoid.
        if self.forbidden_skills:
            if name in self.forbidden_skills:
                return f"Skipped {name} (forbidden by species)"
            if speciality and f"{name} ({speciality})" in self.forbidden_skills:
                return f"Skipped {name} ({speciality}) (forbidden by species)"
        disp = f"{name}{f' ({speciality})' if speciality else ''}"
        for existing in self.skills:
            if existing.name == name and existing.speciality == speciality:
                if level == 0:
                    # Basic training / background: no-op if already present.
                    return f"Already has {disp} {existing.level}"
                if fixed_level:
                    # Rank bonus / explicit grant: take only if better.
                    if level > existing.level:
                        old = existing.level
                        existing.level = min(level, 4)
                        return f"Increased {disp} to {existing.level}"
                    return f"{disp} unchanged (already {existing.level})"
                else:
                    # Table roll / "gain a level": always increment.
                    if existing.level < 4:
                        existing.level = min(4, existing.level + level)
                        return f"Increased {disp} to {existing.level}"
                    return f"{disp} already at maximum level 4"

        new_level = max(level, 0)
        self.skills.append(Skill(name=name, level=new_level, speciality=speciality))

        # Auto-seed parent skill at level 0 when gaining a speciality at 1+.
        if speciality and new_level >= 1:
            has_parent = any(
                s.name == name and s.speciality is None for s in self.skills
            )
            if not has_parent:
                self.skills.append(Skill(name=name, level=0, speciality=None))

        # Keep the list A-Z: sort by name, then speciality (None sorts before any string).
        self.skills.sort(key=lambda s: (s.name.lower(), s.speciality or ""))

        return f"Gained {name}{f' ({speciality})' if speciality else ''} {new_level}"

    def log(self, message: str) -> None:
        self.notes.append(message)


def new_character() -> Character:
    return Character()
