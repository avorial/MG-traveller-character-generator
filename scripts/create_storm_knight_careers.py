"""
Create Storm Knight career JSON files from The Spinward Extents / Vanguard Reaches.
Run from the TravllerCC_work directory.

Three Orders:
  - Order of Thunder    (INT 6+)  — combat/warrior psions
  - Order of the Inconstant Star (INT 7+)  — navigator/explorer psions
  - Order of Shadows    (END 7+)  — covert/stealth psions
"""
import json, os

BASE = r'C:\Users\patricthomas\TravllerCC_work\app\data\careers'

def write(career):
    path = os.path.join(BASE, career['id'] + '.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(career, f, indent=2, ensure_ascii=False)
    print(f"  Written: {career['id']}.json")


# ─────────────────────────────────────────────────────────────────────────────
# STORM KNIGHT — ORDER OF THUNDER
# INT 6+  |  Assignments: Warrior, Outrider, Stormcaller
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "storm_knight_thunder",
    "name": "Storm Knight — Order of Thunder",
    "description": (
        "The Order of Thunder is the most militant of the Storm Knight orders. "
        "Its knights are trained as front-line warriors who channel raw psionic "
        "energy through their weapons and bodies. They serve as shock troops, "
        "battlefield commanders, and protectors of the Vanguard Reaches. "
        "Acceptance requires both martial aptitude and the mental discipline to "
        "harness the Storm."
    ),
    "qualification": {
        "characteristic": "INT",
        "target": 6,
        "modifiers": []
    },
    "societies": ["other"],
    "assignments": {
        "warrior": {
            "name": "Warrior",
            "description": "You serve as a front-line combat knight, leading charges and breaking enemy lines with psionic-enhanced strikes.",
            "survival": {"characteristic": "END", "target": 6},
            "advancement": {"characteristic": "STR", "target": 8}
        },
        "outrider": {
            "name": "Outrider",
            "description": "You range ahead of main forces, scouting enemy positions and conducting lightning raids.",
            "survival": {"characteristic": "DEX", "target": 7},
            "advancement": {"characteristic": "INT", "target": 6}
        },
        "stormcaller": {
            "name": "Stormcaller",
            "description": "You are trained in the offensive application of psionics, channelling telekinetic and clairvoyant powers to shape the battlefield.",
            "survival": {"characteristic": "INT", "target": 7},
            "advancement": {"characteristic": "END", "target": 6}
        }
    },
    "skill_tables": {
        "personal_development": {
            "name": "Personal Development",
            "1": "STR +1",
            "2": "DEX +1",
            "3": "END +1",
            "4": "INT +1",
            "5": "Athletics",
            "6": "Melee"
        },
        "service_skills": {
            "name": "Service Skills",
            "1": "Athletics",
            "2": "Gun Combat",
            "3": "Melee",
            "4": "Recon",
            "5": "Survival",
            "6": "Tactics (Military)"
        },
        "advanced_education": {
            "name": "Advanced Education",
            "requires_edu": 8,
            "1": "Explosives",
            "2": "Heavy Weapons",
            "3": "Medic",
            "4": "Navigation",
            "5": "Tactics (Military)",
            "6": "Telepathy"
        },
        "warrior": {
            "name": "Warrior",
            "assignment_only": "warrior",
            "1": "Athletics",
            "2": "Gun Combat",
            "3": "Melee",
            "4": "Recon",
            "5": "Telekinesis",
            "6": "Vacc Suit"
        },
        "outrider": {
            "name": "Outrider",
            "assignment_only": "outrider",
            "1": "Drive",
            "2": "Flyer",
            "3": "Gun Combat",
            "4": "Recon",
            "5": "Stealth",
            "6": "Survival"
        },
        "stormcaller": {
            "name": "Stormcaller",
            "assignment_only": "stormcaller",
            "1": "Awareness",
            "2": "Clairvoyance",
            "3": "Melee",
            "4": "Recon",
            "5": "Telekinesis",
            "6": "Telepathy"
        }
    },
    "ranks": {
        "warrior": {
            "0": {"title": "Squire", "bonus": "Melee 1"},
            "1": {"title": "Knight", "bonus": "Gun Combat 1"},
            "2": {"title": "Knight-Errant", "bonus": None},
            "3": {"title": "Knight-Commander", "bonus": "Tactics (Military) 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Knight-Captain", "bonus": "Leadership 1"},
            "6": {"title": "Storm Lord", "bonus": "SOC +1"}
        },
        "outrider": {
            "0": {"title": "Squire", "bonus": "Recon 1"},
            "1": {"title": "Knight", "bonus": "Stealth 1"},
            "2": {"title": "Knight-Errant", "bonus": None},
            "3": {"title": "Pathfinder", "bonus": "Navigation 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Knight-Captain", "bonus": "Survival 1"},
            "6": {"title": "Storm Lord", "bonus": "SOC +1"}
        },
        "stormcaller": {
            "0": {"title": "Squire", "bonus": "Awareness 1"},
            "1": {"title": "Knight", "bonus": "Telekinesis 1"},
            "2": {"title": "Knight-Adept", "bonus": None},
            "3": {"title": "Adept-Commander", "bonus": "Clairvoyance 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Adept-Captain", "bonus": "Telepathy 1"},
            "6": {"title": "Storm Lord", "bonus": "SOC +1"}
        }
    },
    "mishaps": {
        "1": "You are grievously wounded in battle. Roll on the Injury table.",
        "2": "A psionic surge overwhelms your control. You injure an ally. Gain an Enemy and lose SOC -1.",
        "3": "You fail a critical mission and your Order's honour is tarnished. Lose one Benefit roll.",
        "4": "A rival knight sabotages your standing. Lose one rank. You may remain in the career.",
        "5": "You are captured by enemies and held for a season. Roll END 8+; if you fail, lose END -1.",
        "6": "Your psionic abilities burn out during a desperate battle. Lose one PSI level (minimum 0). You are not ejected from the Order but lose all Benefit rolls this term."
    },
    "events": {
        "2": "Disaster! Roll on the Mishaps table but you are not ejected from the Order.",
        "3": "Your unit is ambushed in a swamp. Roll Recon 8+ or Survival 8+. If you fail, roll on the Injury table. If you succeed, gain one of Recon 1, Survival 1, or Stealth 1.",
        "4": "You are assigned to train new squires. Gain Leadership 1 or Tactics (Military) 1.",
        "5": "A psionic revelation sharpens your mind in battle. Gain Awareness 1 or Clairvoyance 1.",
        "6": "You participate in a major campaign that becomes legendary in the Order's history. Gain SOC +1.",
        "7": "Life Event. Roll on the Life Events table.",
        "8": "You cross blades with a renowned enemy knight. Roll Melee 9+ to defeat them; if you succeed, gain an extra Benefit roll. If you fail, gain a Rival.",
        "9": "You are sent on a long-range raid deep into hostile territory. Gain one of Gun Combat 1, Recon 1, or Tactics (Military) 1.",
        "10": "Your psionic skills attract the attention of an Order Elder. Gain DM+2 on your next advancement roll.",
        "11": "You distinguish yourself heroically in a battle that saves an allied world. Gain SOC +1 and an Ally.",
        "12": "Your deeds become the stuff of Order legend. Gain an immediate promotion and SOC +1."
    },
    "mustering_out": {
        "1": {"cash": 2000, "benefit": "Weapon"},
        "2": {"cash": 5000, "benefit": "Armour"},
        "3": {"cash": 10000, "benefit": "Contact"},
        "4": {"cash": 20000, "benefit": "Weapon (+1 quality)"},
        "5": {"cash": 40000, "benefit": "SOC +1"},
        "6": {"cash": 80000, "benefit": "Ally"},
        "7": {"cash": 100000, "benefit": "2 Ship Shares"}
    },
    "complete": True
})


# ─────────────────────────────────────────────────────────────────────────────
# STORM KNIGHT — ORDER OF THE INCONSTANT STAR
# INT 7+  |  Assignments: Wayfinder, Sage, Herald
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "storm_knight_inconstant_star",
    "name": "Storm Knight — Order of the Inconstant Star",
    "description": (
        "The Order of the Inconstant Star charts the unknown and preserves the "
        "accumulated wisdom of the Vanguard Reaches. Its knights serve as "
        "navigators, scholars, and ambassadors — using their psionic gifts to "
        "sense safe paths through jump space and to read the intentions of those "
        "they meet. Entry demands an exceptionally sharp mind."
    ),
    "qualification": {
        "characteristic": "INT",
        "target": 7,
        "modifiers": []
    },
    "societies": ["other"],
    "assignments": {
        "wayfinder": {
            "name": "Wayfinder",
            "description": "You pilot and navigate vessels across the Reaches, using psionic intuition to supplement conventional astrogation.",
            "survival": {"characteristic": "INT", "target": 6},
            "advancement": {"characteristic": "EDU", "target": 7}
        },
        "sage": {
            "name": "Sage",
            "description": "You compile, protect, and transmit the lore of the Order, conducting research and training new initiates.",
            "survival": {"characteristic": "EDU", "target": 6},
            "advancement": {"characteristic": "INT", "target": 8}
        },
        "herald": {
            "name": "Herald",
            "description": "You serve as an envoy and negotiator, travelling between star systems to broker treaties and gather intelligence.",
            "survival": {"characteristic": "SOC", "target": 6},
            "advancement": {"characteristic": "INT", "target": 7}
        }
    },
    "skill_tables": {
        "personal_development": {
            "name": "Personal Development",
            "1": "INT +1",
            "2": "EDU +1",
            "3": "SOC +1",
            "4": "DEX +1",
            "5": "Clairvoyance",
            "6": "Awareness"
        },
        "service_skills": {
            "name": "Service Skills",
            "1": "Astrogation",
            "2": "Clairvoyance",
            "3": "Electronics",
            "4": "Navigation",
            "5": "Pilot",
            "6": "Science"
        },
        "advanced_education": {
            "name": "Advanced Education",
            "requires_edu": 8,
            "1": "Astrogation",
            "2": "Engineer",
            "3": "Medic",
            "4": "Science",
            "5": "Telepathy",
            "6": "Teleportation"
        },
        "wayfinder": {
            "name": "Wayfinder",
            "assignment_only": "wayfinder",
            "1": "Astrogation",
            "2": "Clairvoyance",
            "3": "Electronics (Sensors)",
            "4": "Navigation",
            "5": "Pilot",
            "6": "Vacc Suit"
        },
        "sage": {
            "name": "Sage",
            "assignment_only": "sage",
            "1": "Admin",
            "2": "Awareness",
            "3": "Electronics (Computers)",
            "4": "Investigate",
            "5": "Science",
            "6": "Telepathy"
        },
        "herald": {
            "name": "Herald",
            "assignment_only": "herald",
            "1": "Carouse",
            "2": "Clairvoyance",
            "3": "Deception",
            "4": "Diplomat",
            "5": "Persuade",
            "6": "Telepathy"
        }
    },
    "ranks": {
        "wayfinder": {
            "0": {"title": "Initiate", "bonus": "Astrogation 1"},
            "1": {"title": "Pathfinder", "bonus": "Pilot 1"},
            "2": {"title": "Navigator", "bonus": None},
            "3": {"title": "Star-Seeker", "bonus": "Navigation 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Star-Master", "bonus": "Clairvoyance 1"},
            "6": {"title": "Grand Navigator", "bonus": "SOC +1"}
        },
        "sage": {
            "0": {"title": "Initiate", "bonus": "Science 1"},
            "1": {"title": "Scholar", "bonus": "Investigate 1"},
            "2": {"title": "Lorekeeper", "bonus": None},
            "3": {"title": "Archivist", "bonus": "Awareness 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "High Sage", "bonus": "Telepathy 1"},
            "6": {"title": "Grand Sage", "bonus": "SOC +1"}
        },
        "herald": {
            "0": {"title": "Initiate", "bonus": "Diplomat 1"},
            "1": {"title": "Voice", "bonus": "Persuade 1"},
            "2": {"title": "Herald", "bonus": None},
            "3": {"title": "Emissary", "bonus": "Telepathy 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Grand Herald", "bonus": "Carouse 1"},
            "6": {"title": "Voice of the Star", "bonus": "SOC +1"}
        }
    },
    "mishaps": {
        "1": "Your ship is lost in a misjump. Roll END 8+. If you fail, roll on the Injury table.",
        "2": "Your psionic readings prove catastrophically incorrect. Your reputation suffers. Lose one Benefit roll and an Ally becomes a Rival.",
        "3": "A rival Order manipulates your work to claim credit. Lose one rank but you are not ejected.",
        "4": "You are stranded on a hostile world and must survive alone for months. Gain Survival 1 but lose one Benefit roll.",
        "5": "Negotiations you conduct break down violently. Gain an Enemy.",
        "6": "Your accumulated research is destroyed by sabotage. Lose EDU -1."
    },
    "events": {
        "2": "Disaster! Roll on the Mishaps table but you are not ejected from the Order.",
        "3": "You discover a new jump route through a particularly hazardous region. Gain Astrogation 1 or Navigation 1 and DM+1 to one Benefit roll.",
        "4": "A lengthy voyage exposes you to alien cultures and technologies. Gain Science 1 or Electronics 1.",
        "5": "Your telepathic sensitivity warns you of a betrayal before it occurs. Gain Telepathy 1 and a Contact.",
        "6": "You are selected to present your research at an interstellar conclave. Gain SOC +1 and D3 Contacts.",
        "7": "Life Event. Roll on the Life Events table.",
        "8": "You discover a long-lost archive of pre-Collapse knowledge. Gain EDU +1 and an additional Benefit roll.",
        "9": "A noble of another polity seeks your guidance on a diplomatic crisis. Gain Diplomat 1 or Persuade 1, and the noble as an Ally.",
        "10": "You successfully navigate a region declared impossible by conventional astrogation. Gain DM+2 on your next advancement roll.",
        "11": "Your services to the Order earn you a position of honour. Gain SOC +1 and an immediate promotion.",
        "12": "You make a discovery that rewrites understanding of a major historical event. Gain EDU +2 and SOC +1."
    },
    "mustering_out": {
        "1": {"cash": 2000, "benefit": "Contact"},
        "2": {"cash": 5000, "benefit": "INT +1"},
        "3": {"cash": 10000, "benefit": "EDU +1"},
        "4": {"cash": 20000, "benefit": "Scout Ship (1 year)"},
        "5": {"cash": 40000, "benefit": "SOC +1"},
        "6": {"cash": 80000, "benefit": "Ally"},
        "7": {"cash": 150000, "benefit": "2 Ship Shares"}
    },
    "complete": True
})


# ─────────────────────────────────────────────────────────────────────────────
# STORM KNIGHT — ORDER OF SHADOWS
# END 7+  |  Assignments: Shadow, Warden, Inquisitor
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "storm_knight_shadows",
    "name": "Storm Knight — Order of Shadows",
    "description": (
        "The Order of Shadows operates in darkness, safeguarding the Order's "
        "secrets and eliminating its enemies through guile rather than force of "
        "arms. Its knights are spies, assassins, and wardens who employ psionic "
        "concealment and telepathic subterfuge. Membership demands exceptional "
        "physical endurance — to survive in places where no other knight can go."
    ),
    "qualification": {
        "characteristic": "END",
        "target": 7,
        "modifiers": []
    },
    "societies": ["other"],
    "assignments": {
        "shadow": {
            "name": "Shadow",
            "description": "You operate undercover, infiltrating hostile organisations and eliminating threats to the Order.",
            "survival": {"characteristic": "DEX", "target": 7},
            "advancement": {"characteristic": "INT", "target": 7}
        },
        "warden": {
            "name": "Warden",
            "description": "You guard the Order's strongholds and its most sensitive personnel, repelling infiltrators and would-be assassins.",
            "survival": {"characteristic": "END", "target": 6},
            "advancement": {"characteristic": "STR", "target": 7}
        },
        "inquisitor": {
            "name": "Inquisitor",
            "description": "You investigate treachery within the Order and interrogate captured enemies, using telepathy to extract truth.",
            "survival": {"characteristic": "INT", "target": 7},
            "advancement": {"characteristic": "SOC", "target": 6}
        }
    },
    "skill_tables": {
        "personal_development": {
            "name": "Personal Development",
            "1": "DEX +1",
            "2": "END +1",
            "3": "INT +1",
            "4": "STR +1",
            "5": "Stealth",
            "6": "Deception"
        },
        "service_skills": {
            "name": "Service Skills",
            "1": "Deception",
            "2": "Gun Combat",
            "3": "Melee",
            "4": "Recon",
            "5": "Stealth",
            "6": "Streetwise"
        },
        "advanced_education": {
            "name": "Advanced Education",
            "requires_edu": 8,
            "1": "Explosives",
            "2": "Investigate",
            "3": "Medic",
            "4": "Telepathy",
            "5": "Teleportation",
            "6": "Vacc Suit"
        },
        "shadow": {
            "name": "Shadow",
            "assignment_only": "shadow",
            "1": "Deception",
            "2": "Electronics (Sensors)",
            "3": "Melee",
            "4": "Recon",
            "5": "Stealth",
            "6": "Teleportation"
        },
        "warden": {
            "name": "Warden",
            "assignment_only": "warden",
            "1": "Athletics",
            "2": "Gun Combat",
            "3": "Melee",
            "4": "Recon",
            "5": "Telepathy",
            "6": "Vacc Suit"
        },
        "inquisitor": {
            "name": "Inquisitor",
            "assignment_only": "inquisitor",
            "1": "Advocate",
            "2": "Awareness",
            "3": "Deception",
            "4": "Investigate",
            "5": "Persuade",
            "6": "Telepathy"
        }
    },
    "ranks": {
        "shadow": {
            "0": {"title": "Shade", "bonus": "Stealth 1"},
            "1": {"title": "Shadow", "bonus": "Deception 1"},
            "2": {"title": "Deep Shadow", "bonus": None},
            "3": {"title": "Phantom", "bonus": "Recon 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Master of Shadows", "bonus": "Teleportation 1"},
            "6": {"title": "Darkblade", "bonus": "SOC +1"}
        },
        "warden": {
            "0": {"title": "Watch", "bonus": "Recon 1"},
            "1": {"title": "Warden", "bonus": "Melee 1"},
            "2": {"title": "Sentinel", "bonus": None},
            "3": {"title": "High Warden", "bonus": "Gun Combat 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Storm Warden", "bonus": "Telepathy 1"},
            "6": {"title": "Darkblade", "bonus": "SOC +1"}
        },
        "inquisitor": {
            "0": {"title": "Interrogator", "bonus": "Investigate 1"},
            "1": {"title": "Inquisitor", "bonus": "Telepathy 1"},
            "2": {"title": "High Inquisitor", "bonus": None},
            "3": {"title": "Truth-Seeker", "bonus": "Awareness 1"},
            "4": {"title": None, "bonus": None},
            "5": {"title": "Grand Inquisitor", "bonus": "Persuade 1"},
            "6": {"title": "Darkblade", "bonus": "SOC +1"}
        }
    },
    "mishaps": {
        "1": "Your cover is blown and you are captured. Roll on the Injury table. You escape but your usefulness as a field operative is finished for now.",
        "2": "An asset you recruited turns out to be a double agent. Gain an Enemy and lose one Benefit roll.",
        "3": "A psionic scan by a powerful telepath exposes part of your mission. Lose one rank but you are not ejected.",
        "4": "You are forced to eliminate a target who turns out to be innocent. Suffer nightmares — lose END -1.",
        "5": "You are betrayed by a member of your own Order. Gain a Rival within the Order.",
        "6": "Your identity is burned and you must go to ground for years. You are not ejected but lose all Benefit rolls this term and suffer SOC -1."
    },
    "events": {
        "2": "Disaster! Roll on the Mishaps table but you are not ejected from the Order.",
        "3": "You uncover a spy ring but it nearly costs you everything. Roll Stealth 9+ or Deception 9+. If you fail, roll on the Injury table. If you succeed, gain D3 Contacts.",
        "4": "Months of undercover work hone your instincts. Gain Recon 1 or Stealth 1.",
        "5": "Your telepathic abilities grow more refined under operational pressure. Gain Telepathy 1 or Awareness 1.",
        "6": "You eliminate a high-value target that had long eluded the Order. Gain SOC +1 and DM+1 to one Benefit roll.",
        "7": "Life Event. Roll on the Life Events table.",
        "8": "A captured enemy officer proves more useful as an asset than as a prisoner. Gain them as a Contact and gain Persuade 1.",
        "9": "You survive an assassination attempt on your own life through sheer endurance. Gain END +1.",
        "10": "Your investigation exposes a corrupt Order official. Gain the gratitude of the High Council — DM+2 on your next advancement roll.",
        "11": "A long-running mission comes to a successful conclusion, eliminating a major threat to the Reaches. Gain SOC +1 and an immediate promotion.",
        "12": "You retrieve intelligence that changes the political balance in the Vanguard Reaches. Gain SOC +1 and two extra Benefit rolls."
    },
    "mustering_out": {
        "1": {"cash": 2000, "benefit": "Weapon"},
        "2": {"cash": 5000, "benefit": "Contact"},
        "3": {"cash": 10000, "benefit": "Armour"},
        "4": {"cash": 20000, "benefit": "DEX +1"},
        "5": {"cash": 40000, "benefit": "SOC +1"},
        "6": {"cash": 80000, "benefit": "Ally"},
        "7": {"cash": 100000, "benefit": "2 Ship Shares"}
    },
    "complete": True
})

print("\nAll Storm Knight careers written successfully.")
