# Bug Reports

## Fixed Bugs

### v30.98: Aezorgh & Hhkar not appearing in the species picker
**Report:** Neither the Aezorgh (v30.95) nor the Hhkar (v30.96) showed up in the Third Imperium species picker.

**Root cause:** The species picker builds its list from each society's `species_ids` array in `app/data/tables/societies.json` (`filteredSpecies = SPECIES.filter(sp => society.species_ids.has(sp.id))`), **not** from the `societies` field on the species JSON. The new species set their own `societies` field (which drives career/API logic) but were never added to the societies' `species_ids` lists, so the picker never rendered them.

**Fix:** Added `"aezorgh"` and `"hhkar"` to the `species_ids` of `third_imperium`, `other`, and `vargr_extents` in `societies.json`.

**Verification:** Live — after a rules reload the Third Imperium picker renders both cards under the "Other alien races" expander (Aezorgh under *Aliens of Charted Space, Vol. 1*; Hhkar under *Aliens of Charted Space*); species_ids counts are now 44 / 52 / 3. Screenshot confirmed the Hhkar card (STR +3 · END +3). All 711 tests pass.

---

### v30.97: Hhkar — add the four mental states to Species Traits
**Request:** The Hhkar mental states need to appear in the Species Traits list.

**Change:** `app/data/species/hhkar.json` previously listed only Lucid Dreaming. Added the four mental states from the racial entry — **Learning** (eidetic memory), **Combat** (DM+2 Initiative, DM+6 Morale, DM-2 reactions), **Labourer** (no fatigue on repetitive work, DM-2 Recon), and **Oration** (DM+2 Carouse among Hhkar; DM+1 to others' reactions) — plus a short **Mental States** header trait describing the meditation/trigger requirement they share.

**Verification:** Live — the Hhkar now carries 14 Species Traits including all five "Mental State —" entries (Learning, Combat, Labourer, Oration, Lucid Dreaming); `/api/species` serves them. All 711 tests pass.

---

### v30.96: New species — Hhkar (Imperium / Other / Vargr)
**Request:** Add the Hhkar (Julian Protectorate dinosaur-like humanoids); available in the Third Imperium, Other / Far Domains, and Vargr Extents societies. Travellers assumed to be first-iteration males.

**Added:** `app/data/species/hhkar.json` with:
- **Characteristic modifiers** STR +3, END +3; **raised maxima** STR 18, END 18 (via `characteristic_maximum_overrides`).
- **Starting age 22** and aging starting **after the 5th term** (`aging_starts_term: 5`).
- **`no_psionics: true`** — Hhkar refuse psionic testing/training, so the psi test is blocked engine-side.
- **Childhood default skill** — an additional **Melee 0** granted automatically (`extra_background_skills`), reflecting that their childhood replaces pre-career education.
- **Natural armour** — Thick Hide `starting_equipment` granting **Protection +1**.
- Traits: Armour, Perception (magnetic sense; DM+2 Mechanic repairs of magnetic gear), Suspended Animation (ghraa!ks hibernation), Weapons (claws 1D+2, tail strike), Lucid Dreaming (DM+2 to prepared checks), plus referee notes for the Tolerance skill mechanic, ineligibility for pre-career education, the gender-transformation reset, and career restrictions (raaabr locked out of Noble until SOC 7+ / ssaaahk membership; no Julian scout service).

**Referee-adjudicated (documented as traits, not auto-applied):** the Tolerance-for-Carouse substitution and EDU+1→Tolerance option, the ssaaahk SOC bands, the gender-transformation stat/skill reset, and the raaabr Noble-career gate.

**Verification:** Live — `/api/species` serves the Hhkar in all three societies with STR/END +3, STR/END 18 caps, and `no_psionics`. Applying the species yields STR/END 10 (from a 7 base), grants Melee 0 and Thick Hide (Protection +1), sets age 22, loads nine traits, and the psi test raises "Hhkar cannot develop psionic ability." All 711 tests pass (3 new schema tests for the file).

---

### v30.95: New species — Aezorgh (Vargr / Imperial / Other)
**Request:** Add the Aezorgh (AoCS Vol. 1, Vargr section); available in the Vargr Extents, Third Imperium, and Other / Far Domains societies.

**Added:** `app/data/species/aezorgh.json` — small four-armed gecko-like sophonts with:
- **Custom characteristic rolls** for every stat: STR 1D, DEX 2D+3, END 1D+1, INT 2D+2, EDU 1D, SOC 1D (via `custom_characteristic_rolls`, which fully override the standard 2D rolls).
- **Raised per-stat maxima**: DEX 18, INT 16 (via `characteristic_maximum_overrides`); all others 15.
- **Fixed background skills** Athletics 0 / Mechanic 0 / Recon 0 / Stealth 0 (via `extra_background_skills`); the "one additional skill of choice" is taken in the normal background phase.
- **Starting age 18** and an **age-limited aging bonus** — DM+4 to aging checks until age 82 / 16 terms, then it stops.
- Traits: Gecko Travel, Heightened Senses (DM+1 Recon/Survival; IR negates darkness), Multi-limbed (two action-sets/round, universal tool use), plus referee notes for the Vargr CHA=½SOC rule and the DM-2 pre-career education penalty.

**Engine:** `_apply_aging` now honours an optional `aging_bonus_dm_until_term` cap on `aging_bonus_dm` (backward compatible — uncapped species bonuses still apply every term).

**Referee-adjudicated (documented as traits, not auto-applied):** Vargr-society CHA = ½ SOC, and the DM-2 to qualify/graduate pre-career education.

**Verification:** Live — `/api/species` serves the Aezorgh in all three societies with custom rolls and DEX 18 / INT 16 caps; applying the species rolls stats in the correct ranges, grants the four background skills, sets age 18, and loads six traits. Aging DM+4 confirmed to apply through term 16 and stop at 17. All 708 tests pass (3 new schema tests for the file).

---

### v30.93: Benefit choice parsing — split comma lists and drop the "(choose one)" instruction; B&W heritage block
**Requests:** The resolved benefit name was wrong — `Benefit choice resolved: 'Blade, Club or Dagger (choose one)' → Dagger (choose one)`; it should offer Blade and Club too. (Also bundles the prior, uncommitted Solomani-heritage B&W fix.)

**Root cause:** Unresolved benefit choices (e.g. the Barbarian background package's `"Blade, Club or Dagger (choose one)"`) were split on `" or "` only, so the options came out as `"Blade, Club"` and `"Dagger (choose one)"` — the comma list wasn't separated and the trailing `(choose one)` instruction leaked into the option name.

**Changes:**
- **`app.js`** — new `splitBenefitOptions()` helper strips a trailing `(choose one)` / `(pick one)` / `(select …)` instruction and splits on commas **and** `or`, so the picker shows three clean chips: `Blade` / `Club` / `Dagger`. `unresolvedBenefitChoices()` now also detects comma-list choices that carry a `(choose …)` instruction.
- **`lifepath.py`** — `resolve_equipment_choice()` parses options the same way, so the chosen option (`Blade`) is validated and applied without the stray suffix and the log reads `… → Blade`.
- **`style.css`** (carried from prior session) — `.roll-result-block` referenced a typo'd CSS var `--panel-bg`; corrected to `--bg-panel` so the Solomani heritage roll block renders on the panel background instead of a solid black box on the light/mono themes.

**Verification:** Live — `splitBenefitOptions('Blade, Club or Dagger (choose one)')` → `["Blade","Club","Dagger"]`; existing `or`-only benefits (`Combat Implant or two Ship Shares`, `Rifle or Carbine`) unchanged. `.roll-result-block` background is `rgb(255,255,255)` under the mono theme. No console errors; all 705 tests pass.

---

### v30.92: Show AI background in the NPC card; remove duplicate footer GM button
**Requests:** The generated AI background should show next to the NPC; the footer GM MODE button is redundant with the top one.

**Changes:**
- **`app.js`** — NPC roster cards now render the generated AI background **inline** (a scrollable `capsule-box` with the story text), in addition to the "✓ AI background — included in export" note, so you can read it next to the character instead of only knowing it exists.
- **`index.html`** — removed the footer `GM MODE` button. It was a **duplicate `id="btn-gm-mode"`** of the top GM toggle (so its handler never bound anyway); the top `GM` toggle is unaffected.

**Verification:** Live — generating an AI background renders the story in the NPC card (text shown); exactly one `#btn-gm-mode` remains (the top toggle), footer has none. All 705 tests pass.

---

### v30.91: Career picker — comprehensive unavailable-card sort (all societies)
**Request:** Apply the bottom-sort for Solomani and Other as well.

**Finding/Change:** v30.90's species-locked sort was already society-agnostic (it works for Solomani and Other — they just need the deploy). Broadened it into a tiered sort so **every** unavailable card type sinks, in any society: available → ejected (already served) → rite-locked (Aslan) → race/species-locked. Stable sort preserves order within each tier.

**Verification:** Live — Solomani (cetacean careers) and Other / Far Domains (19 species-specific careers) both render available careers first and locked ones grouped at the bottom; tier order is monotonic in both. JS-only; all 705 tests pass.

---

### v30.90: Career picker — sort race-restricted careers to the bottom
**Request:** Careers locked by race fill up the list; push them to the bottom.

**Change (`app.js`):** In the career picker, careers the character can't enter due to species (`allowed_species` excludes them, or `blocked_species` lists them) are now sorted to the **bottom** of the list (stable sort, so order within each group is preserved). Available careers stay at the top; the locked cards still render with their reason, just out of the way. Especially helps "Other / Far Domains" characters, where all the species-specific Vol. 4 / Dolphin / etc. careers previously interleaved with the available ones.

**Verification:** Live — an Imperial Human in Other/Far Domains shows 17 available careers first (Agent, Army, Believer…) then all 19 race-locked ones grouped at the bottom (Soulhunter, Za'tachk…); no locked card appears above an available one. JS-only; all 705 tests pass.

---

### v30.89: Vol. 4 species-specific careers (6 careers, species-locked)
**Request:** Add the special careers only the Vol. 4 species can have.

**Added 6 careers** (each `societies: ["other"]` + `allowed_species` so only that species can enter; they otherwise still use Core careers):
- **Suerrat** — Regional Criminal Police Organisation, Regional Security Force.
- **Za'tachk** (all three caste entries) — Interstellar Ground Force and Interstellar Space Force (both with a Commission/officer track; BOL gates noted in the description).
- **Tezcat** — Shaper Priest (per-assignment rank tracks: Academic/Ecclesiastic vs Partisan), Soulhunter (Commission + assignment rank tracks).

Each has full qualification (incl. per-previous-career and age-over DMs), assignments with survival/advancement, personal-development/service/advanced-education/officer/assignment skill tables, enlisted+officer or per-assignment rank tracks, events (2–12) and mishaps (1–6) as text, and mustering-out cash/benefits. Gurvin has no species career (Core careers with female business-career DM bonuses, per the book).

**Engine:** `BOL +N` now applies in both `_apply_skill_result` (skill tables) and `_apply_rank_bonus` (rank bonuses), mirroring REP, so Za'tachk Boldness gains from tables/ranks land on `character.boldness`.

**Verification:** All 6 load with correct assignments/restrictions; each qualifies, starts a term, and rolls every accessible skill table cleanly (incl. BOL gains). `/api/careers/full` shows correct `allowed_species`/`societies`. Engine smoke test 514 paths / 0 fail; full suite 705 passing.

---

### v30.88: Vol. 4 — Gurvin gendered entries + Za'tachk Boldness as a real characteristic
**Requests:** Gurvin should use the existing gendered-creation pattern (other Other-culture races split by sex); BOL should work like REP (a real characteristic shown up top), not a documented trait.

**Gurvin → split entries (Capry pattern):** replaced `gurvin.json` with **Gurvin — Female** (INT+1, EDU+1, free Broker 0) and **Gurvin — Male** (STR−1, DEX+1, INT/EDU rolled **1D+1** via `custom_characteristic_rolls`, Arm-Antlers). Both age 16; verified INT ranges (male 2–7, female 2D+1).

**BOL like REP:**
- `character.boldness` field (mirrors `reputation`).
- `apply_species` rolls `boldness_roll` (e.g. "1D+1") and applies a `boldness_modifier` (caste), min 1.
- `_char_dm` and JS `charDM` alias **BOL → boldness**; BOL renders in the characteristics bar (and DM) whenever > 0, exactly like REP.
- **Za'tachk** split into caste entries with their own modifiers: base (STR+1, BOL 1D+1), **Matriarch** (+INT/+EDU, BOL−1 → 1–6), **Scout** (−INT/−EDU, BOL+1 → 3–8).

**Verification:** Gurvin male/female roll correctly; Za'tachk BOL ranges per caste; live UI shows "BOL 6 DM 0" for a Za'tachk Scout in the top characteristics bar. Seven Vol. 4 entries total. All 681 tests pass.

---

### v30.87: Aliens of Charted Space Vol. 4 — Gurvin & Za'tachk (stage 2; all four now in)
**Request:** Add the rest of the Vol. 4 species; all are "Other" culture.

**Added (both `societies`-less → Other / Far Domains, source Vol. 4):**
- **Gurvin** (`gurvin.json`) — INT+1, EDU+1 (female line) + free Broker 0; traits Heightened Senses, Extra Limbs, and a **Sexual Dimorphism** trait documenting the male variant (STR−1, DEX+1, roll 1D+1 for INT/EDU, Arm-Antlers). Starting age 16.
- **Za'tachk** (`zatachk.json`) — STR+1; traits **Boldness (BOL)** (documents the 1D+1 seventh characteristic, BOL-check rule, and Matriarch/Scout caste modifiers), Brachiator, Coward. Starting age 18.

Pragmatic fidelity notes: Gurvin defaults to the female stat line (the typical adventuring sex) with the male variant captured in a trait rather than a separate gender-prompt; Za'tachk's BOL is documented in a trait (rolled/checked at the table) rather than added to the global optional-characteristics set. This keeps both data-only, consistent with Suerrat/Tezcat (v30.86).

With Suerrat and Tezcat (v30.86), **all four Vol. 4 species are now selectable.**

**Still open:** the species-specific careers (e.g. Suerrat's Regional Criminal Police Organisation / Regional Security Force) — Vol. 4 characters currently use Core Rulebook careers.

**Verification:** Both load/apply (Gurvin age 16 + Broker 0; Za'tachk age 18 + STR+1); all four appear under the Vol. 4 book group in `/api/species`; schema + full suite pass (672 tests).

---

### v30.86: Aliens of Charted Space Vol. 4 — Suerrat & Tezcat species (stage 1)
**Request:** Add the Vol. 4 aliens (not previously in the generator).

**Finding:** Vol. 4 has four species — **Suerrat, Za'tachk, Gurvin, Tezcat** — none present. Two fit the existing species schema cleanly; two need new engine support.

**Added now (schema-clean):**
- **Tezcat** (`tezcat.json`) — DEX+1, END−1; traits Chameleon (Stealth DM+2 / Deception DM−2 vs Tezcat), Fast Metabolism (Init DM+1), Heightened Senses, Manual Dexterity (DM+2), Natural Weapons (venom). Starting age 18.
- **Suerrat** (`suerrat.json`) — STR+1, DEX+2, SOC−1; traits Cold Resistance, Poor Senses, Radiation Resistance, plus an Accelerated-Ageing note (ageing rolls DM+1). Mandatory Athletics 0 background skill via `extra_background_skills`. Starting age 18.

Both carry `source: "Aliens of Charted Space Vol. 4, Mongoose Publishing"` (no `societies` → appear under **Other / Far Domains**, grouped by book) and use Core Rulebook careers.

**Deferred to stage 2 (need engine work):** **Gurvin** (gendered modifiers; males roll 1D+1 for INT/EDU) and **Za'tachk** (custom **Boldness (BOL)** characteristic + Matriarch/Scout caste variants + BOL checks). Plus the four species' **species-specific careers** (e.g. Suerrat's Regional Criminal Police Organisation and Regional Security Force).

**Verification:** Both load and apply (Tezcat DEX+1/END−1; Suerrat grants Athletics 0); appear in `/api/species` under the Vol. 4 book group; schema tests pass. All 666 tests pass.

---

### v30.85: First-load welcome popup (dismiss once)
**Request:** A one-time welcome popup on first load with an "ignore" button.

**Implementation:**
- **`index.html`** — `#welcome-modal` with the full welcome text (purpose, testing-site/bug-report note, self-hosting intent, possible future auth, Mongoose thanks, GitHub link) and an **IGNORE — DON'T SHOW AGAIN** button + close ×.
- **`app.js`** — on bootstrap, shows the modal once when `localStorage['traveller-welcome-seen']` is unset; dismiss (button, ×, or backdrop click) hides it and sets the flag so it never reappears.

**Verification:** Live — shows on first load, Ignore dismisses and sets the flag, stays hidden across reloads; renders on-theme with the GitHub link. All 660 tests pass.

---

### v30.84: NPC generator settings persist on change + README rebuild
**Request:** Hold the NPC generator settings in local cache so reopening keeps the last species (a Solomani run stays Solomani); rebuild the README.

**Changes:**
- **`app.js`** — `wireNpcModal` now persists every field (species/role/experience/count/primary/secondary) to `localStorage` on `change`, not only when GENERATE is clicked. Reopening the modal restores the last selections.
- **`README.md`** — rebuilt to current state: version badge → 30.84; full NPC generator section (species incl. uplifts/Zhodani/Random Alien, ship-crew roles, experience tiers incl. Patron, batch, primary/secondary skills, quirks, names, AI backgrounds, export); distinct-visitor badge; updated API table (`/npc-options`, batch `generate-npc`, `ai-narrative`); project structure (`visitors.py`, `ai_narrative.py`).

**Verification:** Live — changing species/role/experience without generating saves immediately and restores on reopen (Solomani→engineer→veteran round-tripped). All 660 tests pass.

---

### v30.83: NPC generator — full ship-crew roles
**Request:** The role list should include every ship position — engineers, gunners, astrogators, sensor teams (not just pilot).

**Implementation (`lifepath.py`):**
- Added ship-crew roles to `NPC_ROLE_PACKAGES` / `NPC_ROLE_LABELS`: **Ship's Captain, Astrogator, Engineer, Gunner, Sensor Operator, Comms Operator, Steward** (Pilot relabelled "Pilot (ship)"). All biased toward the spacer packages.
- New `NPC_ROLE_SKILLS` map gives each role a **guaranteed signature skill** (trained, level 1+): Pilot→Pilot, Captain→Leadership, Astrogator→Astrogation, Engineer→Engineer, Gunner→Gunner, Sensor Operator→Electronics (sensors), Comms→Electronics (comms), Steward→Steward, Medic→Medic. `_npc_ensure_skill` extended to accept a specific speciality (so sensor/comms operators get the right Electronics speciality). Use the Primary Skill field to make the signature skill expert (2+).
- `/npc-options` and the UI dropdown pick the new roles up automatically (they iterate `NPC_ROLE_PACKAGES`).

**Verification:** Every ship role guarantees its signature skill 8/8 (incl. Electronics sensors/comms specialities); 19 roles total. Live — dropdown lists all ship positions; an Engineer NPC came out with Engineer (Life Support). All 660 tests pass.

---

### v30.82: NPC generator — Primary / Secondary Skill fields (guaranteed ≥2)
**Request:** Add Primary Skill and Secondary Skill dropdowns (full skill list); the NPC will have each chosen skill at +2 or higher. If not picked, generate as normal.

**Implementation:**
- **`lifepath.py`** — `npc_skill_options()` returns all 39 pickable skills (22 core + 17 cascade parents). `generate_npc`/`generate_npc_batch` take `primary_skill`/`secondary_skill`; `_npc_ensure_skill` guarantees each at level 2+ **after** the package/experience build. Cascade parents (e.g. Gun Combat, Pilot) get a random speciality at the floor with the bare parent kept at 0; an already-higher level is never lowered.
- **`main.py`** — `NPCGenOptions` gains `primary_skill`/`secondary_skill`; `/npc-options` returns the `skills` list.
- **`app.js`** — two selects, **PRIMARY SKILL (≥2)** and **SECONDARY SKILL (≥2)**, default **(any)**; persisted in prefs and sent with generation. Empty = generate normally.

**Verification:** Backend — core skill (Medic) and cascade speciality (Gun Combat/Pilot) guaranteed ≥2; parent stays 0; already-high kept; no-pick generates normally. Live — both fields render (40 options incl. "(any)"); two scholars came out with Medic 2 + Pilot(spec) 2; "(any)" still generates a normal NPC. All 660 tests pass.

---

### v30.81: NPC roster — "roll a new name" button
**Request:** A button to keep scrolling through NPC names.

**Change (`app.js`):** Each NPC roster card now has a 🎲 button next to the name; clicking it rolls a fresh species-appropriate name (`generateSpeciesName`) for that NPC only, in place, so you can keep clicking until you like one. Affects just that NPC; the new name carries into LOAD / JSON / Foundry export.

**Verification:** Live — clicking cycles through distinct names for the target NPC (4 different Vargr names) while leaving other NPCs untouched. JS-only; all 660 tests pass.

---

### v30.80: Terminal-ID badge shows distinct-visitor count (replaces "9042")
**Request:** Replace the static `TAS-GEN-9042` number with the count of different IPs that have visited the site.

**Implementation:**
- **`app/visitors.py`** (new) — `VisitorCounter`: records distinct client IPs and returns the count. IPs are **salted + SHA-256 hashed** before storage (the JSON file holds only opaque hashes + a random salt, never raw IPs). Thread-locked, atomic temp-file write, best-effort (never breaks a page load).
- **`main.py`** — index route records the client IP (first `X-Forwarded-For` hop behind a proxy, else the direct peer) and passes `visitor_count` to the template. Store path is `VISITORS_FILE` (default `/code/data/visitors.json`).
- **`index.html`** — badge is now `TAS-GEN-{{ '%04d' % visitor_count }}-{{ app_version }}` (zero-padded to keep the terminal look) with a "Distinct visitors" tooltip.
- **`docker-compose.yml`** — added a `traveller-data` named volume mounted at `/code/data` + `VISITORS_FILE` env so the count survives container rebuilds. `.gitignore` excludes `/data/`.

**Verification:** Unit — dedup (same IP once), persistence across reloads, no raw IP in the file. Route — distinct `X-Forwarded-For` IPs increment, repeats don't; badge renders `TAS-GEN-0003-…`. Live — badge shows `TAS-GEN-0001-30.79` with tooltip. All 660 tests pass.

**Deploy notes:** The count starts at 0 (no historical data) and only persists across rebuilds if the new `traveller-data` volume is present — `docker compose up -d` will create it. If the app sits behind a reverse proxy, ensure it forwards `X-Forwarded-For` so real client IPs are counted rather than the proxy's.

---

### v30.79: "Do you need to make an NPC?" button on the first page
**Request:** Add an NPC button under the "I want to play a robot" button on the first page.

**Change (`app.js`):** Added a `DO YOU NEED TO MAKE AN NPC?` button directly under `I WANT TO PLAY A ROBOT` on the characteristics (first) page; it opens the same NPC Generator modal as the footer MAKE NPC button (`openNpcModal`).

**Verification:** Live — button present, ordered after the robot button, labelled correctly, opens the NPC modal with its controls. JS-only; all 660 tests pass.

---

### v30.78: AI backgrounds for NPCs (from the NPC generator) → Foundry bio
**Request:** If someone has an AI link configured, let them generate NPC backgrounds from the NPC generator, and have those go into the Foundry export.

**Implementation:**
- **`app.js`** — when an AI link is configured (the same `traveller-ai-config` used by the Career Narrative ✨ AI feature), each roster NPC gains **✨ AI BACKGROUND** (→ **✨ REGEN BACKGROUND** once written) plus a batch **✨ AI BACKGROUNDS (ALL)** (sequential, to respect rate limits). The story is stored on `npc.capsule_description`; a **✓ AI background ready** badge appears. When no link is configured the buttons are hidden and a tip points to ⚙ AI SETTINGS. Per-NPC and "all" exports (JSON + Foundry) carry the story since they serialise the NPC dict.
- **`ai_narrative.py`** — `build_story_prompt` now weaves in the NPC's Character Quirk and (for patrons) the Patron type, with guidance to reflect them in the prose.
- **`lifepath.py`** — made NPC generation resilient: a random package-finalising pick that can't be applied (e.g. a boost skill that resolved to a speciality) no longer aborts generation/batches — it snapshots the clean pre-package character and retries with the no-input career choice (no double-application).

**Verification:** Live with a mock AI endpoint — AI buttons appear only when configured; generating a background stores it on the NPC and shows the badge; the Foundry export for that NPC contains the story in `system.description` (the actor bio). Gating verified (buttons hidden + tip when no link). Resilience: 0 errors over 200 patron generations. `capsule_description → desc_html → actor description` confirmed in `foundry_export.py`. All 660 tests pass.

---

### v30.77: NPC Character Quirks (all NPCs) + Random Patrons table (patron tier)
**Request:** Every NPC should get a quirk from the D66 Character Quirks table; patron-tier NPCs roll their type from the D66 Random Patrons table.

**Implementation:**
- **`lifepath.py`** — added both full D66 tables (`NPC_QUIRKS`, `NPC_PATRON_TYPES`, 36 entries each) and a `_d66_key()` roller. In `generate_npc`: every NPC rolls a Character Quirk; patron-tier NPCs also roll a Patron type. Both are written to dedicated fields **and** mirrored into `user_notes` (the sheet's notes field) as `Patron: …` / `Quirk: …`, and into the generation log.
- **`character.py`** — `npc_quirk` and `npc_patron_type` fields.
- **`app.js`** — roster cards now show **★ Patron: <type>** (accent) and **Quirk: <quirk>** for each generated NPC.

**Verification:** 40/40 regular NPCs carry a valid quirk and no patron type; 30/30 patrons carry both, with `user_notes` showing `Patron:`/`Quirk:`; good D66 spread (24 distinct quirks, 21 distinct patron types in samples). Live roster shows both lines (e.g. "★ Patron: Starport Administrator / Quirk: Wants to borrow money"). All 660 tests pass.

---

### v30.76: NPC generator — "Patron" experience tier (7–10 terms)
**Request:** Add a patron-level NPC that gets 7 to 10 terms.

**Implementation (`lifepath.py`):** New `patron` experience tier above Elite.
- **Age:** set directly to a full career lifetime — `18 + randint(7,10)×4` (= 46–58).
- **Depth:** 12 skill bumps (cap 4), so several skills reach level 3–4 — a recognised expert.
- **Breadth:** `_npc_graft_second_career` merges a second (different) career package's skills onto the NPC, representing a long multi-career history; merges by max level, resolves 'any' to a random speciality, no duplicate specialities.
- **Characteristics:** 2 distinct stat bumps (species-cap aware). `stat_bump` now means "how many characteristics get +1" for all tiers.
- The experience dropdown and `/npc-options` pick the new tier up automatically (they iterate `NPC_EXPERIENCE`).

**Verification:** Patron NPCs land age 46–58, ~34 total skill levels (vs ~21 Elite) across ~15–17 trained skills with peaks at 3–4; zero cascade-parent violations, no duplicate specialities; tier progression veteran→elite→patron is monotonic. Live dropdown shows "Patron (7–10 terms)"; a generated patron came out age 46 with Astrogation 4 / Pilot 3. All 660 tests pass.

---

### v30.75: NPC generator species list revised (uplifts, Zhodani, Random Alien)
**Request:** NPC species options should be Imperial Human / Solomani Human / Uplifted (Ape/Dolphin) / Aslan / Vargr / Zhodani / Random Alien.

**Change (`lifepath.py` + `main.py` + `app.js`):**
- Replaced the curated id list with `NPC_SPECIES_OPTIONS` (ordered id/label) matching the request. "uplifted" and "random_alien" are **meta-options** resolved to a concrete species at generation time by `_npc_resolve_species`: uplifted → {chimp, gorilla, dolphin}; random_alien → {aslan, vargr, zhodani, ape×2, dolphin, orca}.
- `_npc_resolve_species_pendings` auto-resolves any pending choice `apply_species` leaves — notably the **Zhodani PSI ruleset** (NPCs use the Sourcebook rule, so Zhodani NPCs get PSI) — so no NPC is generated in a stuck/pending state.
- `/npc-options` now returns the new labelled list; the UI dropdown shows exactly the seven options (no extra generic "Random"; default Imperial Human).

**Verification:** Each option generates 12/12 with the expected concrete species and zero leftover pending choices; Zhodani NPCs roll PSI (e.g. 8–12); live dropdown shows the seven options; uplifted/random_alien resolve to varied species. All 660 tests pass.

---

### v30.74: Expanded NPC generator — species / role / experience / batch (feature)
**Request:** Expand the MAKE NPC button — generation controls, role archetypes, experience tiers, and batch/group generation.

**Implementation:**
- **`lifepath.py`** — `generate_npc(species_id, role, experience)` parameterized; new `generate_npc_batch(count, …)`.
  - **Species:** curated, clean-applying list (Imperial Human, Solomani, Vargr, Aslan, Bwap) via `apply_species`, or random; falls back to Imperial Human if a species needs interaction.
  - **Role/archetype:** `NPC_ROLE_PACKAGES` maps 12 roles (soldier, officer, pilot, scout, agent, criminal, scholar, medic, noble, trader, entertainer, drifter) onto career packages; biases the random pick.
  - **Experience:** rookie/regular/veteran/elite scale skill depth (+0/+2/+4/+6 bumps), age (+0/+4/+12/+20 yrs), and an Elite stat bump (respecting species caps). Bumps target trained skills, never bare cascade parents.
  - **Cascade cleanup:** `_npc_resolve_cascade_parents` converts generic package parents (e.g. "Gunner 1") into real specialities so NPCs export cleanly to VTT.
- **`main.py`** — `GET /api/character/npc-options` (UI lists); `POST /api/character/generate-npc` (options + count → `{npcs:[…]}`); legacy `GET` retained.
- **`app.js` + `index.html`** — MAKE NPC now opens an **NPC Generator modal**: species/role/experience/count, GENERATE, and a roster. Each NPC shows name (species-appropriate, auto-generated), UPP, age, top skills, with **LOAD / JSON / ⬇ FOUNDRY**; batches add **EXPORT ALL (JSON / FOUNDRY)**. Last-used options persist in localStorage.

**Verification:** Backend — species variants resolve, soldier role yields military skills 40/40, experience scales skills+age monotonically, batch varied, 0 cascade-parent violations / no duplicate specialities. Live browser — modal renders, 3 Vargr veteran soldiers generated with names + role-appropriate skills, per-NPC Foundry export returns a valid `traveller` actor, LOAD replaces the character. All 660 tests pass.

---

### v30.73: Naval Intelligence (INI) — no failure feedback + dead "back" button
**Report:** Trying out for Naval Intelligence "does not seem to trigger or tell you in the UI you failed."

**Findings (three bugs in `renderQualifyResult` / qualify flow):**
1. **Crash on a blocked attempt.** The INI eligibility gate (and every `_qual_block`: species restrictions, vacc-suit gates, "must be serving in the Navy") returns `roll: None`. The fail branch rendered `roll.roll.dice.join(...)` — a TypeError on `null` — so **nothing rendered**. That's the "doesn't tell you you failed."
2. **Misleading failure screen.** A *failed roll* on a semi-career posting (INI, Imperial Guard) showed the generic "Accept the Draft / Become a Drifter" options — wrong. RAW: a denied posting is not permanent; you remain in your source service.
3. **Dead back button.** `btn-back-careers` ("Try Another Career") was only wired in `wireDonePhase()`, never in `wireCareerPhase()`, so during career creation it had no handler — clicking did nothing. It also never cleared `subPhase`/`lastRoll`, so it would have re-shown the same screen anyway.

**Fixes (`app.js`):**
- `renderQualifyResult`: `roll === null` → a clean "Not Eligible" screen showing the block reason (no crash); a failed semi-career roll → a "Posting Denied" screen (no draft/drifter) explaining it isn't permanent; normal career failures keep the draft/drifter options.
- Wired `btn-back-careers` in `wireCareerPhase`, clearing `subPhase`/`lastRoll`/`selectedCareer` so the career picker reappears (lets the player re-pick their Navy service to continue, or choose another path).

**Verification:** Live browser — blocked INI renders the reason without throwing; failed INI roll shows "Posting Denied" with no draft/drifter; normal career failure still offers draft/drifter; back button returns to the 16-card picker (subPhase cleared). All 660 tests pass.

---

### v30.72: Prisoner career — Parole Threshold mechanic (was missing; generic rules mis-fired)
**Report:** The Prisoner career's defining rule — leave only when the advancement roll exceeds a Parole Threshold (1D+2, cap 12); mishaps can't eject; no anagathics in prison.

**Finding:** The Prisoner career existed (assignments, events, mishaps, muster benefits, forced entry) but the Parole Threshold mechanic was **not implemented**. Worse, the generic advancement-continuation rules (v30.69–71) ran on prisoners and were *backwards*: a low roll triggered "FORCED OUT → leave" (RAW: low roll = parole **denied**, stay) and a natural 12 triggered "MUST CONTINUE → stay" (RAW: a high roll should **end** the sentence). Prisoners could also muster out at will, be ejected by mishaps, and use anagathics.

**Implementation:**
- `character.py`: `parole_threshold` (character) + `parole_released` (CareerTerm).
- `lifepath.py start_term`: on first entry to `prisoner`, roll Parole Threshold = `min(1D+2, 12)`; persists across terms, cleared on release.
- `lifepath.py advancement_roll`: prisoner branch **replaces** the generic forced-leave / natural-12 logic — released iff `roll > threshold` (strictly), else parole denied → must continue. Returns a `parole` block.
- `lifepath.py end_term`: blocks voluntary muster-out from prison unless `parole_released`; clears the threshold on release.
- `lifepath.py attempt_anagathics` + `app.js anagathicsBoxHTML`: anagathics blocked/hidden while imprisoned.
- `prisoner.json`: `mishap_no_eject: true` (mishaps keep the prisoner inside).
- `app.js`: all decision surfaces (advancement result, session-restore `decideActions`, `renderDecideStep`) show 🔓 PAROLED (LEAVE PRISON) or 🔒 PAROLE DENIED (only ANOTHER TERM, threshold shown); a prisoner never sees a free MUSTER OUT.

**Verification:** Backend — threshold generation, strict `>` boundary (roll 8 vs threshold 8 = denied, 9 = released), natural-12-no-longer-forces-stay, voluntary-leave block + threshold clear on release, anagathics block, `mishap_no_eject` flag. Live browser — released/denied banners and button gating on `renderDecideStep`, anagathics box hidden in prison. All 660 tests pass.

---

### v30.71: Surface "forced out" / "must continue" prominently in the advancement result
**Request:** Make the UI tell the player what's happening when they're pushed out or forced to stay.

**Change:** In v30.70 the explanation only appeared at the decision buttons, so a natural-12 character who first hit the bonus-skill picker or a cascade-specialty choice didn't learn they were staying until later. Pulled the explanation into a standalone `continuationBanner` rendered high in `renderAdvanceStep` (immediately after the roll readout) for **every** sub-branch — the bonus-skill-roll step, the specialty-choice step, and the final decision. Wording expanded to explain the *why*: "⛓ MUST CONTINUE — NATURAL 12 … too valuable to lose … cannot muster out or change careers this term" and "FORCED OUT — TOO LONG IN SERVICE … your services are no longer required." The decision buttons still gate correctly (must-continue → only ANOTHER TERM; forced-out → only MUSTER OUT), and the banner now shows exactly once rather than being duplicated.

**Verification:** Live browser via the real `renderAdvanceStep` — banner present and ordered before the bonus-skill box; single banner with correct button set on both the must-continue and forced-out decision steps. All 660 tests pass.

---

### v30.70: Advancement natural-12 "must continue" rule (missing) + persist continuation flags
**Report (full RAW section):** "If you roll a natural 12, then you must continue in this career. You are too valuable to lose and will be strong-armed into staying." (Alongside the forced-leave rule fixed in v30.69.)

**Findings:**
1. The natural-12 "must continue" rule was **not implemented** — a natural 12 was treated as an ordinary success, so the player could still muster out or switch careers.
2. The continuation outcomes lived only on the transient `uiState.lastRoll`, so the two *other* term-end decision surfaces (the session-restore "Term N Complete" fallback and `renderDecideStep`) couldn't see them — a forced-out or must-continue character regained full options after a reload.

**Fix:**
- `lifepath.py advancement_roll`: added `must_continue_career = (r.raw_total == 12)`. A natural 12 forces continuation and **overrides** forced-leave (you can't be both forced out and strong-armed into staying). Both `must_continue_career` and `forced_from_career` are now **persisted on the term** (new `CareerTerm` fields in `character.py`), not just returned transiently.
- `app.js`: the advancement-result view, the `decideActions` block (session-restore fallback), and `renderDecideStep` all now read the persisted flags. **Must continue** → only ANOTHER TERM (blue ⛓ banner, no muster-out); **forced out** → only MUSTER OUT (red banner, no continue). Legal-conviction forced-career still outranks both.

**Verification:** Backend precedence unit-tested (natural 12 always sets must_continue and clears forced_out; persists through `model_dump`). Live browser: all three states (must-continue / forced-out / normal) render the correct banner and button set on `renderDecideStep`. All 660 tests pass.

---

### v30.69: Advancement "too long in this career" rule — off-by-one boundary
**Report:** "If your advancement roll is equal to or less than the number of terms you have spent in this career, then you cannot continue in this career after this term."

**Finding:** The rule *was* implemented (`advancement_roll` in `lifepath.py`), but with a strict `<` comparison (`r.total < term.term_number`) instead of RAW's "equal to or less than" (`<=`). This let a character who rolled *exactly* their terms-served stay in the career when they should have been forced out at end of term. `term.term_number` already correctly counts terms served **in the current career** (resets to 1 on a new career, line 6232), so the baseline was right — only the boundary was wrong.

**Fix:** Changed the comparison to `r.total <= term.term_number` and corrected the log wording to "equal to or less than terms served". Noble auto-advance remains exempt (its roll always counts). `forced_from_career` flows downstream unchanged.

**Verification:** Boundary unit-tested directly — roll total 2 with 2 terms served now forces out (was: stayed); total 3 still continues. All 660 tests pass.

---

### v30.68: ✨ AI Story — Bring Your Own AI for Narrative Prose (feature)
**Request:** Let players plug in their own AI to turn the factual career narrative into an actual story.

**Implementation:**
- **`app/engine/ai_narrative.py`** — builds a strict prompt from the v30.67 template capsule (the fact sheet: "stay faithful to the facts, don't invent events/ranks/names, no game mechanics, 400–600 words, chosen tone") and calls one of two providers:
  - **Claude** via the official `anthropic` SDK (default `claude-opus-4-8`, adaptive thinking, optional base-URL override for proxies); typed errors map to friendly 401/403/404/429/502 messages.
  - **OpenAI-compatible** via httpx → `{base_url}/chat/completions` — covers Ollama, LM Studio, OpenRouter, OpenAI, LiteLLM. Key optional (local models), generous 300s timeout, Docker `host.docker.internal` hint on connection failure.
- **`app/main.py`** — `POST /api/character/ai-narrative` (provider, api_key, model, base_url, tone). The key is passed through per-request and **never stored server-side**.
- **`app/static/js/app.js`** — Career Narrative card gains **✨ AI STORY** and **⚙ AI SETTINGS** (provider / key / model / base URL / tone, persisted in `localStorage` only). Unconfigured click opens settings. The story replaces the capsule, persists to `capsule_description`, and therefore flows into the Foundry actor bio and PDF; REGENERATE still restores the template rundown.
- `requirements.txt` — added `anthropic` (brings httpx).

**Verification:** Both provider paths exercised offline against mock servers through the real endpoint (adaptive thinking + default model asserted on the Claude path; markdown-fence stripping; 401/400/502/timeout error mapping). Live browser end-to-end: configure OpenAI-compatible → ✨ AI STORY → 3-paragraph story renders in the capsule box and persists to the character. All 660 tests pass.

---

### v30.67: Generate Narrative Produces Actual Prose (feature)
**Request:** The career narrative dumped raw rulebook/log text — dice mechanics ("Roll Investigate 8+… If you succeed, gain REP +1 and DM+1…"), second person, "Gained Contact: Unnamed Contact" repeated six times, and "Basic training: Electronics (Comms) 0, Basic training: Drive 0…" prefixes.

**Implementation (`app/engine/lifepath.py` `generate_capsule` + helpers):**
- **Mechanics stripped:** sentences containing roll/DM/dice/choice instructions are dropped (`_CAPSULE_MECH_RE`), with a fallback that keeps the narrative lead of an event cut at the first mechanics marker.
- **Third person:** "You develop a network…" → "They develop a network…" (`you/your/yourself` → `they/their/themselves`; identical verb forms make this safe).
- **Associates summarised:** per-term "Gained Contact: Unnamed Contact" spam becomes "The term left them with three contacts" — named ones are listed ("an enemy (Corrupt Politician)").
- **Training reads as a sentence:** prefixes stripped ("Basic training:", "Rank bonus:", "Gained", "Increased X to N"), deduped, with rotating openers; basic-training terms get "Basic training grounded them in …".
- **Promotions called out:** rank increases vs the previous term in the same career render as ", newly promoted to Captain" instead of "serving as a Captain".
- **Mishaps narrated:** "The term ended badly: they accept a contract that goes against their moral code…" (mechanics tail removed).
- **Richer opening/closing:** characteristic-driven adjectives ("sharp-minded, highly educated"), a retirement-rank sentence ("They left the SolSec as a Colonel."), and a closing grudge line ("Not everyone remembers them fondly — an enemy and a rival still hold a grudge, the Corrupt Politician chief among them.") or a well-liked line for ally-heavy characters.
- Career-package logs cleaned too ("Took the X career package" bookkeeping skipped; "Gained/Already has/Increased … to N" verbs normalised).

The capsule persists to `capsule_description`, so the improved prose flows into the Foundry export's actor bio and the PDF.

**Verification:** Emma-style fixture (SolSec, 3 terms, mishap, contact spam) and two random `generate_npc()` characters (incl. career packages) all render as clean prose; all 660 tests pass.

---

### v30.66: Finish-Stage Pre-Flight — Benefit Choices, Unnamed Associates, Lean Export (features)
**Request:** Before export, the finish screen should resolve leftover loose ends: (2) "X or Y" benefit choices stored as a single equipment string, (3) placeholder associates ("Unnamed Contact", "From mustering out"), and (4) an option to skip the embedded source character for a lean VTT-only Foundry file.

**Implementation:**
- **Benefit choices** — `lifepath.resolve_equipment_choice(index, chosen)` (+ `POST /api/character/resolve-equipment-choice`): validates the pick against the options split from the item name, removes the item, and applies the pick via `_apply_benefit` (so ship shares, implants, weapons, associates, skills all land correctly). Done screen shows an "⚖ Unresolved Benefit Choices (N)" card with one button per option.
- **Unnamed associates** — "👥 Unnamed Associates (N)" card with per-row input + 🎲 (reusing the D66 personage + species-name generator and the `op:"update"` associate endpoint) plus a **🎲 GENERATE ALL** button. Detection: empty / "unnamed" / "from mustering out" descriptions.
- **Lean export** — `character_to_foundry(include_source=False)` omits the `flags.tvgen` embed; `export-foundry` accepts `include_source` (default true); a checkbox under the export buttons controls it.

**Verification (live browser):** "Combat Implant or two Ship Shares" → two Ship Shares (ship_shares 0→2, item removed); "Rifle or Carbine" → Rifle in equipment; cards disappear when cleared. GENERATE ALL named both placeholders, left the real Ally untouched. Full export carries `flags.tvgen` (20.7KB), lean doesn't (15.8KB); checkbox drives the flag. All 660 tests pass.

---

### v30.65: Foundry Export — Full MGT2E Skill Structure (label/combat/default) for Weapon Dropdowns
**Request:** Foundry exports (Travellers, NPCs, **and robots**) must use the full MGT2E skill-speciality structure. Combat-skill specialities were missing `label` / `combat` / `default`, which breaks weapon-skill selection in Foundry.

**Implementation:**
- **`app/engine/foundry_export.py`** (biological + NPC): combat skills (Gun Combat, Melee, Heavy Weapons, Gunner) now always emit all core specialities, each with `id, label, combat:true, default, trained, value`; the parent carries `default`. Untrained = `value "0"` + `trained:false`; trained = level as a string (supersedes the v30.58 `-3` value). A trained speciality marks its parent trained at 0 (RAW). Non-combat specialities get `label`+`default` (no `combat`). Added `_COMBAT_SKILLS` and `_SKILL_DEFAULT_CHAR` (Gun Combat/Melee/Heavy Weapons → DEX, Gunner → INT, etc.).
- **`app/static/js/app.js`** `createRobotFoundryExport`: rebuilt robot skills with the identical structure (same maps/labels/defaults) so robots are not simplified.

**Verification:** Gun Combat (Energy) 2 exports as `guncombat` parent `trained:true value "0" default DEX` with energy `{label:"Energy", combat:true, default:"DEX", trained:true, value:"2"}` and slug/archaic present untrained; identical output from the robot path; round-trip import still drops untrained entries (no noise). All 660 tests pass.

---

### v30.64: Solomani Qualification-Failure Draft Used the Imperial Table
**Symptom:** A Solomani Confederation character who failed a career qualification and accepted the draft was drafted into **Imperial** services (Navy / Army / Marine / Scout / Agent) instead of Confederation ones.

**Root Cause:** `draft_into_service()` (the general qualification-failure draft) branched for Vargr Extents and Zhodani Consulate but had **no Solomani branch**, so it fell through to the generic Imperial `_DRAFT_TABLE`. (The pre-career education-event-11 draft already had a Solomani table; the qualification-failure path didn't.)

**Fix (`app/engine/lifepath.py`):** Added `_SOLOMANI_DRAFT_TABLE` and a `solomani_confederation` branch, mirroring the event-11 Solomani draft: 1 Confederation Navy (Line/Crew), 2 Confederation Army (Infantry), 3 Solomani Star Marines (Star Marine), 4 Merchant (Merchant Marine), 5 SolSec (Field Agent), 6 Agent (Law Enforcement).

**Verification:** All six entries resolve to valid careers/assignments; a Solomani accepting the draft now lands in Confederation Navy. All 660 tests pass.

---

### v30.63: Full-Page Sheet Colour Buttons Didn't Work
**Symptom:** On the standalone "⛶ FULL SCREEN" character sheet, the COLOUR buttons (Amber / Green / B&W Print / Dark Print) did nothing.

**Root Cause (two):**
1. The standalone window freezes the sheet's interactive controls with `button, input { pointer-events: none }` — which also disabled the colour/print **toolbar** buttons, so clicks never registered.
2. The GREEN button applied `gm-active` (the GM-panel class), not an actual theme.

**Fix (`app/static/js/app.js`, `openTASFullscreen`):**
- Added `#sheet-toolbar button { pointer-events: auto !important; opacity: 1 !important; cursor: pointer; }` so the toolbar stays clickable while the rest of the sheet stays inert.
- GREEN now applies `theme-light` (the real green theme, loaded via the page's stylesheets), and the script's theme-reset list was updated to match.

**Verification:** Generated standalone HTML now carries the pointer-events override and the corrected theme classes; JS parses; all 660 tests pass (no engine change).

---

### v30.62: Cascade Cleanup Rejected Valid Profession/Language Specialties
**Symptom:** Cleaning up a Profession (or Language) cascade skill at completion errored with e.g. `'Hostile Environment/High-g' is not a valid Profession speciality.`

**Root Cause:** The cleanup picker offers specialties from the frontend `CASCADE_SKILLS` map, but the backend validated the choice against `skills.json` — and the two lists differ (Profession entirely; Language partly: Bilanidin/Trokh). Also, the picker's Profession names were non-canonical/odd.

**Fix:**
- `app/engine/lifepath.py` `cleanup_cascade_specialties()`: still requires the parent to be a cascade skill, but **trusts the player's chosen specialty** from the curated picker instead of hard-rejecting names not in `skills.json` (fixes Profession and Language).
- `app/static/js/app.js` `CASCADE_SKILLS.Profession`: replaced the odd names (`Hostile Environment/High-g`, `Colonist/Farming`, …) with the canonical `skills.json` list (Belter, Biologicals, Civil Engineering, Construction, Hydroponics, K'kree Ritual, Miner, Polymers, Religion).

**Verification:** Cleanup with `Profession → Belter` applies (`Profession (Belter) 2`, parent → 0); the legacy name no longer errors; a non-cascade skill is still rejected. All 660 tests pass.

---

### v30.61: Characteristic DM Extends Above 15 (High & Low Characteristics)
**Request:** Characteristics above 15 (some species cap at 17–18) should follow the extended Characteristic Modifiers table — 15-17 → +3, 18-20 → +4, 21-23 → +5, +1 per +3 thereafter — instead of capping the DM at +3.

**Fix:** Replaced the capped DM ladders with the closed form `(score // 3) - 2` (0 stays the special case at -3), which reproduces the whole table including the extension, in all three implementations:
- `app/engine/dice.py` `characteristic_dm()` (used everywhere via `_char_dm`, incl. REP/PSI/RES/TER/FOL)
- `app/static/js/app.js` `charDM()` (sheet, rolls, DM displays)
- `app/engine/pdf_sheet.py` `char_dm()` (PDF export)

**Verification:** New test assertions: 15→+3, 17→+3, 18→+4, 20→+4, 21→+5, 23→+5, 24→+6. All 660 tests pass.

---

### v30.60: Foundry Import — Muster Benefit Associates Come In As Associates
**Request:** Muster-out benefits should import too. (Most already did — cash, pension, ship shares, medical debt via finance; gear via equipment items; benefit contacts/allies via associate items.) The wart: a muster-benefit associate exported as an equipment item (e.g. **"a Contact"**, "an Ally") imported as a piece of *gear* named "a Contact".

**Fix (`app/engine/foundry_export.py`):** In the item loop, an equipment item whose name is an associate type ("a Contact" / "an Ally" / "Rival" / "Enemy") is now added as an Associate (`[From mustering out]`) instead of equipment.

**Verification:** Emma Colbert (fully-updated) → the "a Contact" muster item now lands in Associates (18 contacts) and the equipment list holds only real gear (SC Courier ×3, Combat Implant choice); pension Cr10,000, etc. still import. All 660 tests pass.

---

### v30.59: Foundry Import Reconstructs Career History from Term Items
**Request:** Importing a third-party Foundry actor brought in contacts/equipment but not careers — even though the Foundry `term` items carry the career/assignment/rank (Foundry itself shows them as a Career Terms list).

**Implementation (`app/engine/foundry_export.py`):** `foundry_to_character()` now reconstructs `term_history` + `completed_careers` from the `term` items. Each term's `system.term.assignment` ("Career: Assignment (Rank Title)") is parsed and mapped: career name → career_id, assignment name → assignment_id, rank title → rank number (via the career's rank table). Consecutive same-career terms are grouped into one `CareerRecord` with terms_served, final_rank/title, and benefit_rolls_earned (terms + rank bonus). Per-term rolls/benefit counts aren't in a Foundry export, so those remain approximate.

**Verification:** Both supplied Emma Colbert actors → `solsec / secret_agent`, 5 terms, rank 5 (Colonel); a synthetic Darren Cogs (Scholar/Physician) → 7 terms, rank 6 (Dean) with per-term ranks (Researcher 1, Scientist 3, Professor 5, Dean 6). Contacts and equipment still import. All 660 tests pass.

---

### v30.58: Foundry Export Writes Untrained Skills as -3 (MGT2e convention)
**Request:** Our Foundry export wrote untrained skills as value `0`; the current Foundry MGT2e convention (and real-world actors) use `-3`. Re-exporting an older character should produce the full skill tree with untrained skills at `-3`.

**Fix (`app/engine/foundry_export.py`):** In the skills builder, trained skills/specialties keep their level as a string (`"0"/"1"/"2"`), and untrained ones are now written as `-3` (with `trained:false`) so Foundry shows the −3 unskilled DM instead of a misleading 0.

**Verification:** Export of a sample character shows trained skills (`admin "0"`, `guncombat "1"`, `carouse "2"`) and untrained skills (`astrogation/broker/melee/stealth = -3`); untrained specialties are `-3` while a trained `Pilot (Small Craft) 0` is kept. Round-trip import still drops all `-3` entries (no negative-level skills created). All 660 tests pass.

---

### v30.57: Foundry Import — Keep Trained Specialties Whose Entry Omits "trained":true
**Symptom:** Real third-party Foundry actors (e.g. Emma Colbert) imported via v30.56 but lost trained specialties — Electronics (Computers) 1, Science (Psychology) 1, Pilot (Small Craft), etc. (Separately, an import "failing right away" on the live site is a deploy-lag symptom: pre-v30.56 builds have no Foundry support, so importing a Foundry JSON just breaks — the fix is to deploy the new build.)

**Root Cause:** Many Foundry exports mark only *untrained* specialties (`trained:false`, value `-3`) and omit `trained:true` on the trained ones. `foundry_to_character()` required `sp.get("trained")` truthy, so trained specialties were skipped.

**Fix (`app/engine/foundry_export.py`):** A specialty/skill is now treated as trained unless explicitly `trained:false`; entries with a negative (`-3`) placeholder value are skipped. Parent skills follow the same rule.

**Verification:** Both supplied Emma Colbert actors convert with full skills (Electronics (Computers) 1, Science (Psychology) 1, Pilot (Small Craft) 0, …), 17 associates, equipment, and pension — confirmed directly and via the live `importCharacter` flow (lands on the finish screen). All 660 tests pass.

---

### v30.56: Import Reads Both Native and FoundryVTT JSON (feature)
**Request:** Let IMPORT JSON read both normal (native) exports and FoundryVTT actor JSON.

**Implementation (two tiers):**
- **Tier A — lossless round-trip for our own exports.** `character_to_foundry()` now stashes the full native character in `flags.tvgen.character` (Foundry ignores unknown flag namespaces, so it's inert there). On import, that character is restored verbatim.
- **Tier B — best-effort import of third-party Foundry actors.** `foundry_to_character()` reverse-maps a Mongoose `traveller` actor: characteristics, skills (via inverse skill-id/spec-id tables, seeding cascade parents at 0), finance (credits/pension/debt/ship shares), bio (species via reverse name lookup, age, gender, homeworld), and `items[]` → associates + equipment. The result is a finished character (phase `done`); career history and the lifepath log are not reconstructed (a one-time alert says so).
- `app/main.py`: `POST /api/character/import-foundry` (+ `FoundryImportAction`).
- `app/static/js/app.js`: `importCharacter()` detects a Foundry actor (`type:"traveller"` + `system`, unwrapping `[actor]` / `{actor:…}` shapes), routes it through the endpoint, and keeps native JSON on the existing client path.

**Verification:** Round-trip (export→import) is lossless; a stripped (third-party) actor reconstructs characteristics, skills with specialties, credits/pension, species_id, associates and equipment — verified both directly and through the live `importCharacter` flow. All 660 tests pass.

---

### v30.55: Re-Import Finished Characters to Clean Them Up at the Finish Stage
**Request:** Be able to pull a finished character back into the generator and clean it up (cascade specialties, etc.) at the finish stage.

**Implementation (`app/static/js/app.js`):** `importCharacter()` now resets transient navigation/selection state (`subPhase`, `lastRoll`, `lastAdvanceRoll`, `cascadeCleanupMode`/choices, `selectedMusterIndex`, `selectedCareer`/assignment, `pendingCareerSpecialty`, `pendingAdvancementSkill`) before rendering. A re-imported finished character (phase `done`) now reliably lands on the "Your Traveller Is Ready" screen — where the v30.54 **CLEAN UP SPECIALTIES** card appears for any over-leveled cascade skills — instead of inheriting the previous view's state. Mid-creation saves still resume at the correct step via the career sub-phase inference. (The always-visible **IMPORT JSON** header button is how characters are pulled back in.)

**Verification:** With a deliberately dirty UI state (mid-cleanup, stale event sub-phase), importing a finished character resets the state and the done screen renders the cleanup card + "CLEAN UP SPECIALTIES (2)" for its invalid cascade skills (Gun Combat 3, Melee 1). All 660 tests pass.

---

### v30.54: Cascade Cleanup Button on the Final "Your Traveller Is Ready" Screen
**Status:** FIXED  
**Symptom:** v30.53 added the CLEAN UP SPECIALTIES button to the muster-out "All Benefits Claimed" screen (PHASE 05), but the actual finalized **done** screen (PHASE 06 — "Your Traveller Is Ready") had no button, so a completed character with over-leveled cascade skills (Gun Combat 1, Pilot 1, Melee 1) couldn't reach the cleanup there.

**Fix (`app/static/js/app.js`):** The done screen now shows a "🧹 Cascade Skills Need Specialties" card with a **CLEAN UP SPECIALTIES (N)** button when `invalidCascadeParents()` finds any, routes into `renderCascadeCleanup()` while `uiState.cascadeCleanupMode` is set, and wires the picker via a shared `wireCascadeCleanup()` (used by both the muster and done screens). The cleanup panel header is now neutral ("SKILL CLEANUP") since it appears in both contexts.

**Verification:** Live UI on the done screen — card shows "CLEAN UP SPECIALTIES (3)"; picker assigns Gun Combat (Slug) / Pilot (Small Craft) / Melee (Blade); apply converts all, preserves a pre-existing Pilot (Capital Ships) specialty, returns to the done screen with the card gone and 0 invalid remaining. All 660 tests pass.

---

### v30.53: Clean-Up Button for Over-Leveled Cascade Skills (feature)
**Request:** At character completion ("Your Traveller is ready"), add a button to fix cascade skills held above level 0 with no specialty (e.g. "Gun Combat 2", "Pilot 1") — letting the player choose which specialty each level moves into.

**Implementation:**
- `app/engine/lifepath.py`: `cleanup_cascade_specialties(character, {parent: speciality})` moves each over-leveled bare cascade parent's level into the chosen specialty and drops the parent to 0 (MgT 2e p.59). Validates against `rules.skill_specialities()`.
- `app/main.py`: `POST /api/character/cleanup-cascade-specialties`.
- `app/static/js/app.js`: the muster-out "All Benefits Claimed" screen now warns when cascade parents are over-leveled and shows a **🧹 CLEAN UP SPECIALTIES (N)** button. It opens a picker listing each offending skill with its specialty options; APPLY is gated until every one is assigned. (`invalidCascadeParents()` detects them via `CASCADE_SKILLS`.)

**Verification:** Engine test — Gun Combat 2 → Gun Combat (Slug) 2 + Gun Combat 0; Admin (non-cascade) untouched. Live UI end-to-end — button appears with count, picker assigns Slug/Small Craft, APPLY converts both and clears the warning. All 660 tests pass.

---

### v30.52: Name/Type Generator for Mustering-Out Contacts & Allies (feature)
**Request:** Allow associates gained at muster-out (Contact / Ally / D3 Contacts, etc.) to use the same type+name generator already available earlier in the generator (the D66 personage table + species-name generator used for career-event associates).

**Implementation:**
- `app/engine/lifepath.py`: `muster_out_roll()` now returns `new_associates` (index/kind/description of any associates the benefit added). Added `update_associate(character, index, description)` to rename an associate.
- `app/main.py`: `AssociateAction` / `/api/character/associate` gained an `op: "update"` (rename by index).
- `app/static/js/app.js`: the muster-out result screen lists each newly granted associate with an editable field + a **🎲 Generate** button that fills a D66 personage type + a species-appropriate name (reusing `_SOL_CONTACTS` + `generateSpeciesName`). Edits save automatically via the update op without re-rendering (inputs keep focus while naming several in a row).
- `app/static/css/style.css`: styling for the naming rows.

**Verification:** Backend returns `new_associates` for a Contact benefit; live UI — Generate fills "Alien Ambassador or Trade Delegate — Abraham Balde" and persists to the associate; manual typing also persists. All 660 tests pass.

---

### v30.51: Muster-Out Couldn't Roll Benefits for a Second Stint in the Same Career
**Status:** FIXED  
**Symptom:** A character who served the **same career twice** (e.g. two separate Bounty Hunter careers) could not claim the second stint's mustering-out rolls. Selecting the later Bounty Hunter card showed the *first* one's table ("0 of 1 rolls remaining"), and the ROLL CASH / ROLL BENEFIT buttons were disabled.

**Root Cause:** The muster-out flow identified careers by `career_id` on both ends:
- Frontend: `data-muster-career="${career_id}"`, and `careers.find(x => x.career_id === selected)` always returned the **first** record.
- Backend: `muster_out_roll()` did `next(c for c in completed_careers if c.career_id == career_id)` — same first-match collapse.

So two stints of the same career collapsed onto the first record; once it was exhausted, the second could never be rolled.

**Fix:** Identify careers by their **index** in `completed_careers`:
- `app/static/js/app.js`: cards key on `data-muster-career-index`; selection stores `uiState.selectedMusterIndex`; the table and roll handlers resolve the record via `completed_careers[index]` and send `career_index` to the API; selected card now highlights.
- `app/main.py` / `app/engine/lifepath.py`: `MusterOutAction` and `muster_out_roll()` accept an optional `career_index` and use it to locate the exact record (validated against `career_id`), falling back to first-match for backward compatibility.

**Verification:** Engine test — rolling with `career_index=2` claims the 3-term Bounty Hunter stint and leaves the exhausted 1-term stint untouched; the exhausted index still correctly errors. Live UI: selecting the second Bounty Hunter shows "3 of 3 rolls remaining" with enabled buttons; rolling decrements that stint only and spends one of the shared 7 benefit rolls. All 660 tests pass.

---

### v30.50: Solomani "Racial Incident" Life Event Locked the Character
**Status:** FIXED  
**Symptom:** A Solomani character who rolled the **Racial Incident** life event during a career term (pending_life_event_choice = {kind: "racial_incident"}) could not progress. Choosing Rival or Enemy did nothing / errored, and reloading the save dropped the player back at Basic Training with no way to reach the choice.

**Root Causes (two):**
1. **Backend gap (the actual lock):** `resolve_life_event_choice()` handled `romantic_split` and `betrayal_no_associates` but had **no `racial_incident` branch** — yet `apply_life_event()` produces exactly that kind for Solomani characters. Clicking Rival/Enemy hit `POST /api/character/life-event-choice` and got **400 "Unknown pending life event kind: 'racial_incident'"**, so the choice could never resolve.
2. **Resume routing:** the career-loop sub-phase is stored only in `uiState`, never in the saved character. On reload/import, `renderActiveTerm` defaulted `subPhase === null` to the **training** step, stranding the pending life event (and, if continued, re-rolling survival/event).

**Fix:**
- `app/engine/lifepath.py`: added a `racial_incident` branch to `resolve_life_event_choice()` (Rival/Enemy → add the matching associate), mirroring `romantic_split`.
- `app/static/js/app.js`: `renderActiveTerm` now calls `inferResumeSubPhase(term)` when `subPhase === null`, routing to the correct step (event/mishap/advance/decide) based on term state and pending choices, and reconstructing the minimal event `lastRoll` so the pending picker renders on resume.

**Verification:** Audited all life-event kinds set vs. handled — `racial_incident` was the only genuine gap. Live end-to-end with the user's save: character resumes at the event step with the Rival/Enemy picker (advancement gated), choosing Rival adds "Rival [Racial Incident]", clears the pending choice, and enables ATTEMPT ADVANCEMENT. Backend resolve verified directly; all 660 tests pass.

---

### v30.48: Advancement Bonus Skill — Cascade Specialty Picker Never Appeared
**Status:** FIXED  
**Symptom:** On a successful advancement, the promotion's bonus skill roll could land on a cascade skill (e.g. Melee). The result screen showed "BONUS SKILL GAINED — Melee speciality choice pending", but **no specialty picker ever appeared**, so the player couldn't choose Blade/Bludgeon/Natural/Unarmed and the skill was left unresolved.

**Root Cause:** `skill_roll()` correctly stashed the cascade prompt in `pending_career_event_choice` and returned "… speciality choice pending", but the frontend's **advancement** skill-table handler (unlike the normal training handler) never set `uiState.pendingCareerSpecialty`, and the advancement result view had no specialty-picker UI. The pending choice was orphaned. Additionally, `/api/character/apply-specialty` never cleared `pending_career_event_choice`, so a resolved cascade could leak a stale skill picker into a later event.

**Fix:**
- `app/static/js/app.js`: the advancement bonus-skill handler now detects a bare cascade result and sets `uiState.pendingCareerSpecialty` (mirroring the training-phase flow); the advancement result view renders the existing "CHOOSE SPECIALTY" picker and **gates the Another-Term / Muster-Out buttons** until a specialty is chosen; the specialty-pick handler syncs `advancementSkillGained` so the resolved skill (e.g. "+1 Melee (Blade) (level 1)") displays.
- `app/main.py`: `/api/character/apply-specialty` now clears `pending_career_event_choice` after applying, preventing the stale-picker leak (also benefits the normal training cascade flow).

**Verification:** Live-preview end-to-end — promotion → bonus skill Melee → picker shows (Blade/Bludgeon/Natural/Unarmed) with term-decision buttons gated → choosing Blade applies "Melee (Blade) 1", reveals the decision buttons, updates the bonus-skill text, and clears the backend pending choice. All 660 tests pass.

---

### v30.47: Bounty Hunter Event 9 — Skill Check Resolved Twice (real root cause)
**Status:** FIXED  
**Symptom:** Bounty Hunter event 9 ("Roll Investigate 8+ or Streetwise 8+...") presented **two** skill pickers and let the player roll the check twice with conflicting outcomes. A user screenshot showed both branches applying at once: a "Failure" block (Streetwise rolled 4 → mishap + Enemy) **and** an "Auto-applied" block (Streetwise rolled 8 → PASS → REP+1, DM+1 Benefit), plus a stray "+ Add Enemy" associate op.

**Root Cause:** The frontend has **two** independent event skill-check systems that both reacted to the same event text:
1. The backend's authoritative structured `pending_event_choice` skill_check (proper on_pass/on_fail applied server-side).
2. A frontend text-parser (`parseEventContestedRoll`) that scrapes "Roll <Skill> N+" from the event text and renders its own picker (`eventContestedResolved`), resolving client-side.

Both rendered, so the player rolled the check twice. Separately, a third text-parser (`parseEventAssociateOps`) scraped "gain an Enemy" and offered a manual "+ Add Enemy" op, duplicating the skill_check's on_fail enemy. (The earlier v30.45 dm_grants fix addressed only one symptom — the stray DM+1 button — not the double roll.)

**Fix (`app/static/js/app.js`):**
- Gate the text-parsed contested roll on `!lr.pendingEventChoice` — when the backend supplies a structured skill_check, it is authoritative and the text-parsed picker stands down. Events that legitimately rely on the text-parser (navy[3], drifter[6], scholar[9], …) have no `pending_event_choice`, so they are unaffected.
- Extend `suppressAssocOps` to fire for **any** `pending_event_choice` (was only `pending_choice`), and guard the auto-add-ally block with the same flag, so structured effects own all associates and the text-parsed associate picker/auto-add cannot duplicate them.

**Verification:** Live-preview render test confirms event 9 now shows exactly one skill picker, no contested picker, and no stray associate op; a control event with no structured choice still renders its contested picker. All 660 tests pass.

---

### v30.44: Background Skills Duplicate Specialty + Parent Skill
**Status:** FIXED  
**Symptom:** When selecting a background skill with a specialty (e.g., "Science (Xenology)"), the character would end up with both:
- Science 0
- Science (Xenology) 0

**Root Cause:** In `character.py`, the `add_skill()` method was auto-seeding the parent skill whenever ANY speciality was added, including at level 0 (background training).

**Fix:** Modified condition at line 471 from `if speciality:` to `if speciality and new_level > 0:` to only auto-seed parent skills at level 1+.

**Rationale:** Background training (level 0) should only grant the chosen specialty, not the parent skill. The auto-seed at level 1+ prevents duplicate entries when a later career table adds the same skill.

---

### v30.45: Bounty Hunter Event 9 — Stray DM+1 Benefit Reward ("double prompt")
**Status:** FIXED  
**Symptom:** Bounty Hunter event 9 ("...gain REP +1 and DM+1 to one Benefit roll. If you fail, roll on the Mishaps table and gain an Enemy.") presented what looked like a second prompt alongside the Investigate/Streetwise skill check, and the player could end up with **DM+1 to their next Benefit roll even when the skill check FAILED**. (Confirmed via user save: `dm_next_benefit: 1` + log "Event DM chosen: DM+1 to next Benefit roll" despite "Mishap skill check (Investigate): 7 vs 8+ — fail".)

**Root Cause:** Two systems reacted to the same event text:
1. The backend `skill_check` pending choice, whose `on_pass` correctly grants `dm_benefit +1` **only on a pass**.
2. `_parse_event_dms()` independently scraped "DM+1 to one Benefit roll" into `dm_grants`, which the UI could surface as a **separately claimable** reward — decoupled from the skill check.

**Fix:** In `event_roll()` (`app/engine/lifepath.py`), when the event creates a `pending_career_event_choice`, drop all *unapplied* (conditional) text-parsed `dm_grants`. The conditional reward is owned by the skill_check's `on_pass`/`on_fail` and must never be grantable independently. (The frontend already display-gated these on `!lr.pendingEventChoice` since v24.11; this is the authoritative backend guard so the wrong reward can never be applied regardless of render path.)

**Rationale:** Verified the filter keeps `applied:True` (unconditional) grants intact, so events that legitimately auto-apply a DM plus offer a separate choice are unaffected.

---

## Known Bugs (Pending Fix)

### (Historical) Bounty Hunter Event 9: Double Skill Choice Prompt — superseded by v30.45 fix above
**Status:** FIXED (see v30.45)  
**Symptom:** Bounty Hunter event 9 triggers a skill check "Investigate 8+ or Streetwise 8+". The player sees a choice prompt to select which skill to roll, and this choice appears TWICE in the UI.

**Career:** bounty_hunter  
**Event:** 9  
**Effect Entry:** Lines 1068-1074 in `app/engine/lifepath.py` (_EVENT_EFFECTS section)
```json
{
  "type": "skill_check",
  "skills": [{"name": "Investigate"}, {"name": "Streetwise"}],
  "target": 8,
  "on_pass": [{"type": "dm_benefit", "amount": 1}],
  "on_fail": [{"type": "trigger_disaster_mishap"}, {"type": "enemy", "desc": "Enemy [Corrupt Politician]"}]
}
```

**Suspected Cause:** The skill choice prompt rendering code (app.js, lines 9831-9844) may be:
1. Being invoked twice by event loop/re-render
2. Having click handlers attached twice
3. An issue with how the pending_career_mishap_choice state is being managed

**Investigation Points:**
- Frontend skill_choice rendering at app.js lines 9831-9844
- Click handler wiring for `.event-choice-skillcheck` buttons
- Possible double-render in the event resolution phase

**Fix Approach:** Need to trace when the pending choice is rendered and ensure it's only shown once. May require:
- Check if skill_check with multiple skills inadvertently triggers a secondary choice creation
- Verify click handlers are wired only once per render
- Confirm `lr.eventChoiceResolved` flag is being set correctly after first choice

---

## Testing Checklist

When fixes are complete, verify:

- [ ] Background skill with specialty (e.g., Science (Xenology)) appears only once at level 0
- [ ] Background skill choice shows no duplicate parent skill entries
- [ ] Bounty Hunter event 9 shows skill choice prompt only once
- [ ] Selecting either Investigate or Streetwise in event 9 works without double-prompting
- [ ] Other multi-skill checks don't have the same double-prompt issue

