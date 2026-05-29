"""
Create species JSON files from The Spinward Extents / Vanguard Reaches.
Run from the TravllerCC_work directory.
"""
import json, os

BASE = r'C:\Users\patricthomas\TravllerCC_work\app\data\species'

def write(sp):
    path = os.path.join(BASE, sp['id'] + '.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(sp, f, indent=2, ensure_ascii=False)
    print(f"  Written: {sp['id']}.json")


# ─────────────────────────────────────────────────────────────────────────────
# ANIYUN
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "aniyun",
    "name": "Aniyun",
    "description": "A small beetle-like methane-breathing race native to Quatenon in the Corella subsector. Members of the Corellan League, most Aniyun remain on their steam-age homeworld. They stand barely one metre tall, mass under 30 kg, and breathe nitrogen-methane. Their iridescent keratin carapace unfolds into four-metre gliding wings usable only in their thick native atmosphere.",
    "characteristic_modifiers": {"STR": 0, "DEX": 0, "END": 0, "INT": 0, "EDU": -2, "SOC": 0},
    "custom_characteristic_rolls": {"STR": "1D"},
    "traits": [
        "Armour (+2): The rigid carapace provides Protection +2.",
        "Flight: In native nitrogen-methane atmosphere Aniyun can fly at Speed 6. Environmental suits prevent wing deployment in all other environments."
    ],
    "allowed_careers": ["citizen", "drifter"],
    "career_notes": "Aniyun native to Quatenon can only choose Citizen (Colonist) or Drifter (Barbarian). Aniyun outcasts may choose any Drifter assignment.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5100
})

# ─────────────────────────────────────────────────────────────────────────────
# GMINA
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "gmina",
    "name": "Gmina",
    "description": "A primitive tailless scorpion-like race confined to reservations on Yangikent, a tidally locked world orbiting a red dwarf. The Gmina never progressed beyond TL0 and are restricted by the human government. A small number have been smuggled off-world by Sophont Rights extremists and may have filtered into the wider population of Tartakover.",
    "characteristic_modifiers": {"STR": 0, "DEX": -1, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "custom_characteristic_rolls": {"STR": "2D+4", "EDU": "1D", "SOC": "fixed:2"},
    "traits": [
        "Infrared Vision: Gmina see into the infrared spectrum, conferring DM+1 to initiative and Recon checks.",
        "Multi-Limbed: May use up to two major items simultaneously and receive two sets of actions each round. DM-2 with equipment not manufactured or modified for their use."
    ],
    "allowed_careers": ["drifter"],
    "career_notes": "Gmina may only enter the Drifter (Barbarian) career. A Gmina who has escaped Yangikent may enter any Drifter assignment.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5110
})

# ─────────────────────────────────────────────────────────────────────────────
# KEMLAE
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "kemlae",
    "name": "Kemlae",
    "description": "Purple 12-tentacled worms from Kemlos, members of the Corellan League. They mass 80-100 kg over 2.0-2.5 m of length with six forward tentacle-limbs and six tail limbs. The Kemlae life cycle ends in the Kuftu — a metamorphosis into a short-lived flying Kessa reproductive stage — making very long careers impossible. A meritocracy of Lurush judges, they are enthusiastic members of the League.",
    "characteristic_modifiers": {"STR": 0, "DEX": 1, "END": 1, "INT": 0, "EDU": -1, "SOC": -1},
    "starting_age": 8,
    "max_terms": 8,
    "traits": [
        "IR Vision: Kemlae see 0.5-12 micrometres infrared (room-temperature objects visible in darkness). Blue appears grey; green barely discernible.",
        "Kuftu: No aging effects but starting at end of term 7 (age 36), must roll Term+ each term-end or undergo Kuftu — transformation and death.",
        "Multi-Limbed: May use up to three major items simultaneously and receive three sets of major actions each round. DM-2 with equipment not manufactured or modified for their use."
    ],
    "career_notes": "All Traveller Core Rulebook careers are suitable but Kemlae may not serve more than 8 terms total. The Noble career is only available to Lurush who have served 4+ prior terms with EDU 10+ and SOC 10+.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5120
})

# ─────────────────────────────────────────────────────────────────────────────
# KTIAUAO
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "ktiauao",
    "name": "Ktiauao",
    "description": "A reconstructed race from Ka'aheakh whose intelligence depends on symbiosis with the Kti fungoid woven through their central nervous system. Six-limbed arboreal omnivores massing 80-100 kg, the Ktiauao were stripped of their culture by the Tlasayoae Aslan clan in -680 and later restored by the Syoisuis. They now live as a vassal minor clan within the Aslan Hierate, following Aslan customs and gender roles. Neuter 'monks' comprise 15% of the population and enjoy extended lifespans.",
    "characteristic_modifiers": {"STR": 1, "DEX": 2, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "gender_roll": "2D: 2-6 Male; 7 Neuter; 8-12 Female",
    "traits": [
        "Aging: Gendered Ktiauao begin aging after seven terms (DM+2 on aging rolls). Neuter Ktiauao begin aging after ten terms (DM = Terms/2 on aging rolls). Only STR, DEX and END are affected by aging.",
        "Multi-Limbed: May use up to two major items simultaneously and receive two sets of major actions per round. May make two melee attacks with middle limbs doing 1D+2 damage. DM-2 with non-modified equipment.",
        "Peripheral Vision: 270-degree arc of vision, conferring DM+1 to initiative and Recon checks.",
        "TER Penalty: DM-1 on all Past Deeds TER rolls."
    ],
    "uses_aslan_careers": True,
    "aslan_setup_status": {"rite_score": 6, "complete": True},
    "career_notes": "Ktiauao follow Aslan careers from Aliens of Charted Space: Volume 1. Begin careers at age 18. Neuter Ktiauao are treated as female for gender role purposes.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5130
})

# ─────────────────────────────────────────────────────────────────────────────
# MAL'GNAR
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "mal_gnar",
    "name": "Mal'Gnar",
    "description": "A human Minor Race transplanted from Terra to Mal'Gnar El by the Ancients 300,000 years ago. Modified from cold-adapted Homo sapiens neanderthalensis, they stand up to two metres tall with pale albino-like features. Their rigid caste-based society has been frozen at a late Iron Age plateau for 10,000 years. The IISS maintains active interdiction around their homeworld.",
    "characteristic_modifiers": {"STR": 0, "DEX": 0, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "custom_characteristic_rolls": {"EDU": "1D+1"},
    "traits": [
        "No Galanglic: Mal'Gnar begin with no knowledge of Galanglic or any offworld language.",
        "Caste Society: Deviation from caste roles is punished by banishment or death on their homeworld."
    ],
    "allowed_careers": ["drifter"],
    "career_notes": "Drifter (Barbarian) is the only suitable career for a Mal'Gnar Traveller.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5140
})

# ─────────────────────────────────────────────────────────────────────────────
# TEAKHEA
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "teakhea",
    "name": "Teakhea",
    "description": "Amphibious snail-like sophonts from Tlankhu who accepted the Aslan as a master caste and adapted their caste system accordingly. Four metres long and massing over 300 kg, they move via a muscular foot and manipulate the world with two tentacle arms. Serially hermaphroditic, they change gender and matching caste role during their lives. Their population has fallen to 1.2 million — outnumbered five to one by Aslan on their own homeworld.",
    "characteristic_modifiers": {"STR": 1, "DEX": -1, "END": 1, "INT": 0, "EDU": 0, "SOC": -2},
    "starting_skills": ["Language (Trokh) 2"],
    "traits": [
        "Amphibious: Equally adept on land and in water; can stay submerged indefinitely in oxygenated water.",
        "Heightened Senses: DM+1 to Recon and Survival checks.",
        "IR and UV Vision: Extended electromagnetic range including infrared and ultraviolet; see clearly in darkness.",
        "Large (+2): All ranged attacks against a Teakhea gain DM+2.",
        "Shell: Protection +3. Damage applied to characteristics (after armour) is halved.",
        "Snail Foot: Speed reduced to 3 metres across rough or broken terrain.",
        "Language (Trokh) 2: All Teakhea start with this skill. Males do not need the Independence skill."
    ],
    "uses_aslan_careers": True,
    "blocked_aslan_careers": ["ceremonial", "envoy", "aslan_military_officer", "aslan_space_officer"],
    "career_notes": "All Aslan careers from Aliens of Charted Space Volume 1 are available except Ceremonial, Envoy, or Military/Space Officer. A Teakhea cannot change careers without changing gender. A new gender career should be as close in scope to the original as possible. A Teakhea begins as male. At the start of each term roll 8+ on 2D to initiate a gender change if desired. Any Mishap ending a career results in either ceasing character creation or becoming an Outcast.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5150
})

# ─────────────────────────────────────────────────────────────────────────────
# KATANGAN (human variant)
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "katangan",
    "name": "Katangan",
    "description": "Fully human natives of Katanga, a high-gravity world in The Beyond. Their heavy-world upbringing gives them exceptional physical resilience but accelerated aging. Katangans are known for taciturn suspicion of outsiders and fierce loyalty to family and long-term associates. Despite a reputation for violence, an offended Katangan is more likely to deliver a cold stare than throw a punch.",
    "characteristic_modifiers": {"STR": 1, "DEX": -1, "END": 1, "INT": 0, "EDU": 0, "SOC": 0},
    "traits": [
        "Heavy Worlder Aging: DM-1 on all aging rolls even after leaving Katanga.",
        "Katangan Culture: DM+1 on interpersonal checks with familiar people (own culture or long-term Contacts/Allies). DM-1 with unfamiliar people or cultures. Always DM+1 for Persuade checks involving intimidation or bribery."
    ],
    "career_notes": "For the first term, all Katangans are subject to the Draft table but treat Scout results as Navy and Merchant results as Agent. A Katangan can attempt to avoid the draft on SOC 8+ (may check after seeing the result). The draft term does not apply a negative DM to subsequent qualification rolls.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5160
})

# ─────────────────────────────────────────────────────────────────────────────
# ESLYAT
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "eslyat",
    "name": "Eslyat",
    "description": "An amphibious sophont race with an advanced starfaring civilisation and the Eslyat Magistracy as their interstellar state in the Vanguard Reaches. Eslyat society is rigidly stratified into three sub-races: the Selyin upper caste (SOC 10+), the Chutin middle caste (SOC 7-9), and the Magsin lower caste (SOC 6-). Females hold the majority of leadership roles in modern Eslyat society.",
    "characteristic_modifiers": {"STR": 0, "DEX": 0, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "eslyat_subraces": {
        "selyin": {"soc_start": 10, "soc_min": 10, "description": "Upper caste. Can enter Army/Marines/Navy only as a commissioned officer after a pre-career option. Otherwise limited to Entertainer, Merchant, Noble, Scholar, Scout (Surveyor or Explorer)."},
        "chutin": {"soc_start": 7, "soc_range": [7, 9], "description": "Middle caste. Careers: Agent, Army, Citizen, Colonist, Drifter, Marine, Navy, Scout. Always begins military careers as enlisted; can earn commission but advancement limited to Rank 5."},
        "magsin": {"soc_start": 5, "soc_max": 6, "description": "Lower caste. Limited to Citizen, Drifter, Entertainer, Rogue."}
    },
    "gender_modifiers": {
        "male": {"STR_modifier": 1, "note": "DM-1 on advancement rolls for Rank 4 and above."},
        "female": {"note": "DM+1 on all advancement rolls."}
    },
    "traits": [
        "Amphibious: Equally adept on land and in water; can stay submerged indefinitely in oxygenated water.",
        "Heightened Hearing: DM+2 on Recon checks when sound is a relevant factor."
    ],
    "career_notes": "Career choices are strictly caste-limited. Only Selyin may undertake pre-career options. Gender affects advancement rolls.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5170
})

# ─────────────────────────────────────────────────────────────────────────────
# FRENI  (6 sub-types + hybrid)
# ─────────────────────────────────────────────────────────────────────────────
freni_types = [
    {"suffix": "type1", "label": "Type 1 (Light Grey)", "mods": {"STR": -1, "DEX": 2, "END": 0, "INT": -1, "EDU": 0, "SOC": 0}, "desc": "Light grey fur, taller and thinner build, straight antennae."},
    {"suffix": "type2", "label": "Type 2 (Brown)", "mods": {"STR": 0, "DEX": -2, "END": 1, "INT": 1, "EDU": 0, "SOC": 0}, "desc": "Brown fur, moderate build, curling antennae."},
    {"suffix": "type3", "label": "Type 3 (Yellow)", "mods": {"STR": 1, "DEX": -2, "END": 1, "INT": 0, "EDU": 0, "SOC": 0}, "desc": "Yellow fur, shorter and heavier build, straight antennae."},
    {"suffix": "type4", "label": "Type 4 (White)", "mods": {"STR": 0, "DEX": -1, "END": 2, "INT": -1, "EDU": 0, "SOC": 0}, "desc": "White fur, moderate build, straight antennae."},
    {"suffix": "type5", "label": "Type 5 (Orange)", "mods": {"STR": -1, "DEX": 0, "END": -1, "INT": 2, "EDU": 0, "SOC": 0}, "desc": "Orange fur, taller and thinner build, curling antennae."},
    {"suffix": "type6", "label": "Type 6 (Red)", "mods": {"STR": 1, "DEX": -1, "END": -1, "INT": 1, "EDU": 0, "SOC": 0}, "desc": "Red fur, shorter and heavier build, curling antennae."},
]
freni_base_desc = "The Freni are natives of Durnal, a garden world on the border between the Eslyat Magistracy and the Corellan League in the Vanguard Reaches. Multi-armed cook-like sophonts found throughout the Vanguard Reaches and The Beyond, living in large expatriate communities. EDU and SOC increase together: when either rises, the other rises by 1 for every 2 increases."
freni_traits = [
    "Flexible Digits: Freni hands (four mutually opposable tentacular fingers) can use the tools of most races without penalty. Other races suffer DM-2 to operate Freni equipment.",
    "Reputation as Cook: Freni employed as stewards grant DM+1 to checks to seek high passengers. Freni receive DM+2 to checks when hiring on as cooks or stewards.",
    "Starting Skills: Freni begin with Steward 1, Profession (Freeloading) 1, and Survival 0 (DM+2 on Durnal). Freni speak their own language first and may use one background skill for Language 0 (broken Galanglic) or two for Language 1."
]
freni_career = "All Traveller Core Rulebook careers are suitable. DM+1 to enter Entertainer and Merchant careers. DM-1 to enter Agent or Scholar careers."

for ft in freni_types:
    write({
        "id": f"freni_{ft['suffix']}",
        "name": f"Freni — {ft['label']}",
        "description": f"{freni_base_desc} {ft['desc']}",
        "characteristic_modifiers": ft["mods"],
        "traits": freni_traits,
        "career_notes": freni_career,
        "societies": ["other"],
        "source": "The Spinward Extents, Mongoose Publishing",
        "sort_order": 5180 + freni_types.index(ft)
    })

# Hybrid Freni
write({
    "id": "freni_hybrid",
    "name": "Freni — Hybrid",
    "description": f"{freni_base_desc} Rare spotted-pattern hybrids of two Types. Less fit than pure Types, with drooping antennae. Usually (1-5 on 1D) sterile.",
    "characteristic_modifiers": {"STR": 0, "DEX": 0, "END": -1, "INT": 1, "EDU": 0, "SOC": -2},
    "custom_characteristic_rolls": {},
    "traits": freni_traits + [
        "Hybrid: Receives only one increased characteristic from parents (max +1 if parent had +2) and all decreased characteristics from both parents. DM-1 on all aging rolls.",
        "Usually Sterile: 1-5 on 1D the Freni is sterile. If sterile, may be permanently of one gender (1=Male, 2-5=Neuter, 6=Female on 1D)."
    ],
    "career_notes": freni_career,
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5186
})

# ─────────────────────────────────────────────────────────────────────────────
# GHENANI
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "ghenani",
    "name": "Ghenani",
    "description": "A sophont race encountered in the Vanguard Reaches. Powerfully built, with STR up to 17. Ghenani culture deeply rejects cybernetic augmentation and psionics — even to replace a lost limb, a Ghenani will refuse cybernetics. On their birthworld, mustering out benefits are limited to TL5 equipment. They can never speak other languages without gaining the Language skill.",
    "characteristic_modifiers": {"STR": 2, "DEX": -2, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "characteristic_maximum_overrides": {"STR": 17},
    "traits": [
        "No Cybernetics: Ghenani will not accept cybernetic augmentation of any kind, even to replace lost limbs.",
        "No Psionics: Ghenani refuse to learn or use psionic abilities.",
        "Aging: DM-1 on all aging rolls.",
        "Language Barrier: Cannot speak any language other than Ghenani without the Language skill."
    ],
    "blocked_careers": ["psion", "vargr_psion", "zhodani_agent", "zhodani_guard"],
    "career_notes": "Most Traveller Core Rulebook careers are suitable. Unless the Ghenani has emigrated from their birthworld, Scout, Navy, Marine and Merchant (except Broker assignment) careers are not available.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5190
})

# ─────────────────────────────────────────────────────────────────────────────
# MURIAN
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "murian",
    "name": "Murian",
    "description": "Bear-like sophonts native to Arcturus, a world orbiting the red dwarf Altarea with a 40-day year and near-90-degree axial tilt producing 'seasonal days'. Murians evolved to remain active through all phases of their short year. They have short limbs, thick hides, and retractable claws. Their STR and END can both reach 18. A natural lifespan of 60-80 years is now extended to 100-140 through medical treatment.",
    "characteristic_modifiers": {"STR": 1, "DEX": -2, "END": 2, "INT": 0, "EDU": 0, "SOC": 0},
    "custom_characteristic_rolls": {"SOC": "2D3+4"},
    "characteristic_maximum_overrides": {"STR": 18, "END": 18},
    "traits": [
        "Armour (+1): Thick hide and subcutaneous fat provide Protection +1.",
        "Claw: Attack with claws using Melee (natural); deals 1D+2 damage.",
        "Short Limbs: Base speed 4 metres per round. DM-1 when using tools and weapons not designed for Murian hands.",
        "Vision: See well in low light; sensitive to some infrared. Cannot distinguish green, blue, or violet colours. No penalty to Recon checks in low illumination.",
        "Weapon Benefits: Any Benefit roll providing a weapon may instead be taken as an augment or electronic device of up to TL14 and Cr100,000. All Murian augmentations have Natural-looking, Ruggedised and Self-repairing options at no extra charge. All Murian electronic devices are self-repairing."
    ],
    "career_notes": "All Traveller Core Rulebook careers are suitable for Murians.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5200
})

# ─────────────────────────────────────────────────────────────────────────────
# RESAVOLK
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "resavolk",
    "name": "Resavolk",
    "description": "Sophonts from Tumereng, an isolated world at the edge of the Helix Nebula orbiting a red dwarf, three parsecs from the nearest inhabited system. A monoculture of 60 million adults unified by common language and custom but without a monolithic government. The Resavolk are neither hostile nor awed by offworld visitors — merely indifferent. Those who leave are often confused or frightened by foreign cultures and quickly return home.",
    "characteristic_modifiers": {"STR": 0, "DEX": 0, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "custom_characteristic_rolls": {"SOC": "D3+5"},
    "traits": [
        "Language Barrier: Resavolk must gain the Language skill to speak any language other than their native tongue.",
        "Homeworld Instinct: Resavolk automatically qualify for Drifter (Barbarian) and must take this career in their first term if leaving their homeworld."
    ],
    "career_notes": "Most Resavolk follow Drifter (Barbarian) and automatically qualify for it. Resavolk who leave their homeworld must do so as a Drifter in their first term but may attempt any Traveller Core Rulebook career thereafter except Noble. Only a Resavolk who reaches SOC 10+ may qualify for Noble.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5210
})

# ─────────────────────────────────────────────────────────────────────────────
# THONANE (Snow Ghosts)
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "thonane",
    "name": "Thonane (Snow Ghost)",
    "description": "Also known as Snow Ghosts, the Thonane are manta-like flying sophonts. No Thonane are known to have voluntarily left their homeworld; those encountered off-world have typically been illegally taken by smugglers, corsairs, or hunters. They are fragile in STR but superbly agile, with white camouflage ideal for snowy terrain. Travel on the ground is slow — they are built to fly, not walk.",
    "characteristic_modifiers": {"STR": 0, "DEX": 0, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "custom_characteristic_rolls": {"STR": "1D", "DEX": "3D", "END": "2D", "INT": "2D", "EDU": "D3", "SOC": "D3"},
    "traits": [
        "Flyer: On worlds of Size 4 or less with Atmosphere 4+, Thonane can fly at Speed 9 after a 9-metre running start. Ground movement speed is 3 metres.",
        "Hunter: All Thonane possess Flyer (natural) 1, Melee 0, Recon 1, and Survival 1. DM+1 on all Recon checks and DM+2 on Stealth checks in snowy terrain."
    ],
    "allowed_careers": ["drifter"],
    "career_notes": "Thonane can only follow Drifter (Barbarian) but may substitute Flyer (natural) in lieu of any Animals, Seafarer, or Melee skills rolled.",
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5220
})

# ─────────────────────────────────────────────────────────────────────────────
# ZHDIANSHE
# ─────────────────────────────────────────────────────────────────────────────
write({
    "id": "zhdianshe",
    "name": "Zhdianshe",
    "description": "Psionic flying sophonts from the Colonnade Province in the Vanguard Reaches. Extremely frail physically — STR is always 1 — but superbly agile and naturally psionic. All Zhdianshe receive childhood psionic training, beginning with Telepathy 2. They are long-lived, not requiring aging rolls until term 8, and gain DM+6 on all aging rolls. Their echolocation and flight make them formidable in darkness and low-gravity environments. They wear darkened goggles in daylit conditions.",
    "characteristic_modifiers": {"STR": 0, "DEX": 0, "END": 0, "INT": 0, "EDU": 0, "SOC": 0},
    "custom_characteristic_rolls": {"STR": "fixed:1", "DEX": "2D+2", "PSI": "2D_min2"},
    "psi_linked_soc": True,
    "rolls_psi_at_start": True,
    "psi_roll": "2D_min2",
    "aging_starts_term": 8,
    "aging_dm_bonus": 6,
    "traits": [
        "Aging: No aging rolls until term 8. DM+6 on all aging rolls. PSI is treated as a mental characteristic for aging purposes.",
        "Echolocation: See well in low light with no penalty except in absolute darkness (DM-1, max 100m without Clairvoyance). Without darkened goggles in daylight, suffer DM-2 to vision checks or DM-1 if eyes closed and using echolocation.",
        "Flyer: Can fly on Size 5 or smaller worlds (thin atmosphere or denser), Size 6 (standard or dense), or Size 7 (dense). Flying speed 10 metres.",
        "Psionics: Telepathy 2 is automatically gained. Must next attempt Clairvoyance (trained to level 1 if gained). Further talents may be gained as normal but only developed to level 0 during initial training."
    ],
    "psionic_training_at_start": True,
    "psionic_training_table": {
        "note": "All Zhdianshe receive childhood psionic training. Telepathy 2 is automatic. Must next attempt Clairvoyance (trained to level 1 if gained). Additional talents follow standard rules but only reach level 0 during initial training.",
        "auto_talents": [{"name": "Telepathy", "level": 2}],
        "required_next": {"name": "Clairvoyance", "level": 1},
        "talents": [
            {"name": "Clairvoyance", "dm": 3},
            {"name": "Telekinesis", "dm": 2},
            {"name": "Awareness", "dm": 1},
            {"name": "Teleportation", "dm": 0}
        ]
    },
    "career_notes": "All Traveller Core Rulebook careers including Psion are suitable. DM-4 when attempting to qualify for Army or Marine careers (those organisations are not equipped for Zhdianshe).",
    "career_dms": {"army": -4, "marine": -4},
    "societies": ["other"],
    "source": "The Spinward Extents, Mongoose Publishing",
    "sort_order": 5230
})

print("\nAll species written successfully.")
