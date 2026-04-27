/* ============================================================
   TRAVELLER — Character Generation Terminal
   Client-side phase controller
   ============================================================ */

// ------------------------------------------------------------
// Boot data + state
// ------------------------------------------------------------

const SPECIES = JSON.parse(document.getElementById('bootstrap-species').textContent);
const CAREERS = JSON.parse(document.getElementById('bootstrap-careers').textContent);
const SKILLS_DATA = JSON.parse(document.getElementById('bootstrap-skills').textContent);
const SOCIETIES = JSON.parse(document.getElementById('bootstrap-societies').textContent);

// Flat list of all skills as "Skill" or "Skill (Speciality)" strings.
const ALL_SKILLS = [
  ...SKILLS_DATA.core,
  ...Object.entries(SKILLS_DATA.speciality).flatMap(([parent, specs]) =>
    specs.map(s => `${parent} (${s})`)
  )
];
const ALL_SKILLS_NO_JOT = ALL_SKILLS.filter(s => s !== 'Jack-of-All-Trades');

const STORAGE_KEY = 'traveller-character-v1';

let SKILL_PACKAGES = {};

let character = null;
let uiState = {
  // Transient selections that aren't part of the character yet
  selectedSpecies: null,
  selectedBgSkills: new Set(),
  selectedPreCareerSkills: new Set(),
  selectedCareer: null,
  selectedAssignment: null,
  selectedCoverCareer: null,   // SolSec Secret Agent cover career
  // After-roll dialog state
  lastRoll: null,
  // Stat-swap UI state (characteristics phase)
  swapPick: null,   // which tile the user clicked first (for 2-click swap)
  swapA: 'EDU',     // dropdown A default
  swapB: 'STR',     // dropdown B default
  // Current phase sub-state: 'qualify' | 'assign' | 'train' | 'survive' | 'event' | 'advance' | 'decide' | 'mishap' | 'muster'
  subPhase: null,
  pendingAge: false,
  // GM / cheat mode — unlocks direct stat editing, boon rolls, phase skipping.
  gmMode: (localStorage.getItem('traveller_gm_mode') === '1'),
  // Connections step (between muster-out and done).
  connectionsDone: false,
  connections: [],
  // Basic training skills auto-applied at start of first career term.
  basicTrainingSkills: null,
  // Skill package selection (post mustering-out).
  skillPackageApplied: false,
};

// ------------------------------------------------------------
// Persistence
// ------------------------------------------------------------

function saveCharacter() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(character));
}

function loadCharacter() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    try {
      character = JSON.parse(raw);
      return true;
    } catch (e) {
      console.warn('Corrupt saved character, starting fresh');
    }
  }
  return false;
}

async function freshCharacter() {
  const res = await fetch('/api/character/new', { method: 'POST' });
  const data = await res.json();
  character = data.character;
  uiState = { selectedSpecies: null, selectedBgSkills: new Set(), selectedPreCareerSkills: new Set(),
              selectedCareer: null, selectedAssignment: null, selectedCoverCareer: null, lastRoll: null,
              swapPick: null, swapA: 'EDU', swapB: 'STR',
              subPhase: null, pendingAge: false,
              gmMode: uiState.gmMode,
              connectionsDone: false, connections: [],
              basicTrainingSkills: null,
              skillPackageApplied: false };
  saveCharacter();
}

// ------------------------------------------------------------
// API helpers
// ------------------------------------------------------------

async function apiCall(endpoint, extraData = {}) {
  // GM Mode: always prompt for roll overrides when panel input is empty.
  let gm_rolls = [];
  if (uiState.gmMode) {
    const input = document.getElementById('gm-roll-input');
    let raw = input ? input.value.trim() : '';
    if (!raw) {
      // Auto-prompt so every action can be overridden.
      const answer = window.prompt(
        '⚙ GM MODE — Enter roll total(s) for this action\n' +
        '(comma-separated for multiple rolls, or leave blank for random):',
        ''
      );
      raw = (answer || '').trim();
    }
    if (raw) {
      gm_rolls = raw.split(/[\s,]+/)
        .map(v => parseInt(v, 10))
        .filter(n => !isNaN(n));
      uiState.gmLastRolls = [...gm_rolls];
      if (input) input.value = '';
      renderGMPanel();
    }
  }

  const payload = { character, ...extraData, ...(gm_rolls.length ? { gm_rolls } : {}) };
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function applyResponse(response) {
  if (response.character) {
    character = response.character;
    saveCharacter();
  }
  return response;
}

// ------------------------------------------------------------
// DM calculator (mirror of dice.characteristic_dm)
// ------------------------------------------------------------

function charDM(score) {
  if (score <= 0) return -3;
  if (score <= 2) return -2;
  if (score <= 5) return -1;
  if (score <= 8) return 0;
  if (score <= 11) return 1;
  if (score <= 14) return 2;
  return 3;
}

function formatDM(dm) {
  if (dm > 0) return `+${dm}`;
  return `${dm}`;
}

// ------------------------------------------------------------
// Roll readout — shared across every phase so the dice are always visible
// ------------------------------------------------------------

// Cumulative percentile of the raw dice sum for n d6 — i.e. "this roll
// was better than or equal to X% of all possible rolls on this many d6."
// Probability-weighted so a 10 on 2d6 scores 92% (it really is lucky),
// not the naive 83% you'd get by dividing 10 by 12.
function diceLuckPercent(dice) {
  if (!Array.isArray(dice) || !dice.length) return null;
  const n = dice.length;
  const sum = dice.reduce((a, b) => a + b, 0);
  // Coefficients of (x + x^2 + ... + x^6)^n — dist[k] = # ways to roll total k.
  let dist = [0, 1, 1, 1, 1, 1, 1]; // 1d6
  for (let i = 1; i < n; i++) {
    const next = new Array(6 * (i + 1) + 1).fill(0);
    for (let j = 0; j < dist.length; j++) {
      if (!dist[j]) continue;
      for (let d = 1; d <= 6; d++) next[j + d] += dist[j];
    }
    dist = next;
  }
  const outcomes = Math.pow(6, n);
  let cumulative = 0;
  for (let j = 0; j <= sum && j < dist.length; j++) cumulative += dist[j] || 0;
  return Math.round((cumulative / outcomes) * 100);
}

function luckClass(pct) {
  if (pct === null || pct === undefined) return '';
  if (pct >= 85) return 'great';
  if (pct >= 60) return 'good';
  if (pct >= 30) return 'meh';
  return 'bad';
}

function rollReadoutHTML(r, opts = {}) {
  // r is the .to_dict() output from engine.dice.RollResult
  //   dice: [1..6, 1..6], raw_total, modifier, total, target?, succeeded?
  const { label = null, outcome = null, showTarget = true } = opts;
  if (!r) return '';
  const dicePart = Array.isArray(r.dice) && r.dice.length
    ? `<span class="dice">[${r.dice.join(' · ')}]</span>`
    : '';
  const luckPct = diceLuckPercent(r.dice);
  const luckPart = luckPct !== null
    ? `<span class="roll-luck ${luckClass(luckPct)}" title="You rolled at or above ${luckPct}% of all possible ${r.dice.length}d6 outcomes.">${luckPct}%</span>`
    : '';
  const modPart = (r.modifier && r.modifier !== 0)
    ? `<span class="eq">${r.modifier > 0 ? '+' : ''}${r.modifier} DM</span>`
    : '';
  const totalPart = `<span class="total">${r.total}</span>`;
  const targetPart = (showTarget && r.target !== null && r.target !== undefined)
    ? `<span class="eq">vs ${r.target}+</span>`
    : '';
  let outcomeClass = outcome;
  if (outcomeClass === null && r.succeeded !== null && r.succeeded !== undefined) {
    outcomeClass = r.succeeded ? 'pass' : 'fail';
  }
  const outcomePart = outcomeClass === 'pass' ? '<span class="outcome pass">PASS</span>'
                    : outcomeClass === 'fail' ? '<span class="outcome fail">FAIL</span>'
                    : '';
  const labelPart = label ? `<span class="roll-label">${label}</span>` : '';
  return `
    <div class="roll-readout">
      ${labelPart}
      ${dicePart}
      ${luckPart}
      ${modPart}
      <span class="eq">=</span>
      ${totalPart}
      ${targetPart}
      ${outcomePart}
    </div>
  `;
}

// ------------------------------------------------------------
// Rendering: Character Sheet (left panel)
// ------------------------------------------------------------

const NOBLE_TITLES = { 11: 'Knight', 12: 'Baron', 13: 'Marquis', 14: 'Count', 15: 'Duke' };
// Noble titles apply to Third Imperium citizens (check society_id first,
// fall back to legacy species-id list for old saved characters).
const IMPERIAL_SPECIES = new Set(['imperial_human', 'imperial_aslan', 'imperial_vargr',
  'imperial_bwap', 'jonkeereen', 'luriani', 'human', 'solomani', 'vilani', 'mixed_human']);

function nobleTitle(speciesId, soc) {
  const isImperial = (character.society_id === 'third_imperium' || !character.society_id)
                  || IMPERIAL_SPECIES.has(speciesId);
  if (!isImperial) return null;
  return NOBLE_TITLES[soc] || (soc > 15 ? 'Archduke' : null);
}

function renderSheet() {
  const sheet = document.getElementById('sheet');
  const stats = character.characteristics;
  const species = SPECIES.find((s) => s.id === character.species_id) || { name: '—' };

  const statCells = ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC']
    .map((stat) => {
      const val = stats[stat];
      const dm = charDM(val);
      return `
        <div class="stat-cell">
          <span class="stat-label">${stat}</span>
          <span class="stat-value">${val}</span>
          <span class="stat-dm">DM ${formatDM(dm)}</span>
        </div>
      `;
    }).join('');

  const skillsList = character.skills.length
    ? character.skills.map((s) => {
        const label = s.speciality ? `${s.name} (${s.speciality})` : s.name;
        return `<li><span>${label}</span><span class="skill-level">${s.level}</span></li>`;
      }).join('')
    : '<li class="empty">No skills yet</li>';

  const equipList = character.equipment.length
    ? character.equipment.map((e) => `<li>${e.name}${e.notes ? ` <span class="empty">— ${e.notes}</span>` : ''}</li>`).join('')
    : '<li class="empty">No equipment</li>';

  const traits = (character.traits || []);
  const traitsHTML = traits.length
    ? `<ul class="traits-list">${traits.map(t => `<li><strong>${t.name}</strong>${t.description}</li>`).join('')}</ul>`
    : '<p class="empty">No species traits</p>';

  const careersHTML = character.completed_careers.length
    ? `<ul class="skill-list">${character.completed_careers.map(c => {
        const careerDef = CAREERS.find(x => x.id === c.career_id);
        const asgnName = careerDef?.assignments?.[c.assignment_id]?.name || c.assignment_id;
        const rankStr = c.final_rank_title || (c.final_rank > 0 ? `Rank ${c.final_rank}` : 'No rank');
        return `<li><span>${careerDef?.name || c.career_id} — ${asgnName}</span><span class="skill-level">${c.terms_served}t</span></li><li style="border:none;padding:0 0 4px 8px;color:var(--muted);font-size:10px">${rankStr}, ${c.left_due_to}</li>`;
      }).join('')}</ul>`
    : '<p class="empty">No careers yet</p>';

  const associates = character.associates || [];
  const buckets = { contact: [], ally: [], rival: [], enemy: [] };
  associates.forEach((a, i) => {
    if (buckets[a.kind]) buckets[a.kind].push({ a, i });
  });
  const bucketOrder = [
    ['contact', 'Contacts'],
    ['ally', 'Allies'],
    ['rival', 'Rivals'],
    ['enemy', 'Enemies'],
  ];
  const associatesHTML = associates.length
    ? bucketOrder.map(([k, title]) => {
        const items = buckets[k];
        if (!items.length) return '';
        return `
          <div class="assoc-bucket assoc-kind-${k}">
            <div class="assoc-bucket-title">${title} <span class="assoc-count">${items.length}</span></div>
            <ul class="skill-list">
              ${items.map(({ a }) => `<li><span>${escapeHTML(a.description || '(unnamed)')}</span></li>`).join('')}
            </ul>
          </div>
        `;
      }).join('')
    : '<p class="empty">No associates yet</p>';

  sheet.innerHTML = `
    <div class="panel-header"><span class="led"></span><span>CHARACTER FILE</span></div>
    <div class="sheet-scroll">
      <div class="sheet-header">
        <input type="text" class="sheet-name-input" id="char-name" placeholder="[ Unnamed Traveller ]" value="${character.name || ''}" />
        <input type="text" class="sheet-homeworld" id="char-homeworld" placeholder="Homeworld" value="${character.homeworld || ''}" />
        <input type="text" class="sheet-uwp" id="char-uwp" placeholder="UWP — e.g. A788899-C" value="${character.homeworld_uwp || ''}" title="Universal World Profile (paste from travellermap.com)" />
        <div class="sheet-meta">
          <span>SPECIES<br><strong>${species.name}</strong></span>
          <span>AGE<br><strong>${character.age}</strong></span>
          <span>TERMS<br><strong>${character.total_terms}</strong></span>
          <span>CREDITS<br><strong>Cr${character.credits.toLocaleString()}</strong></span>
          ${nobleTitle(character.species_id, character.characteristics?.SOC) ? `<span class="noble-title-badge" title="Imperial Noble Title">TITLE<br><strong>${nobleTitle(character.species_id, character.characteristics?.SOC)}</strong></span>` : ''}
        </div>
      </div>

      <div class="sheet-section">
        <h3>Characteristics</h3>
        <div class="stat-grid">${statCells}</div>
      </div>

      <div class="sheet-section">
        <h3>Skills</h3>
        <ul class="skill-list">${skillsList}</ul>
      </div>

      <div class="sheet-section">
        <h3>Careers</h3>
        ${careersHTML}
      </div>

      <div class="sheet-section">
        <h3>Associates</h3>
        ${associatesHTML}
      </div>

      <div class="sheet-section">
        <h3>Equipment</h3>
        <ul class="equipment-list">${equipList}</ul>
      </div>

      ${character.ship_shares > 0 ? `
      <div class="sheet-section">
        <h3>Ship Shares</h3>
        <div class="credits-line">${character.ship_shares} × MCr1</div>
      </div>` : ''}

      ${character.pension_per_year > 0 ? `
      <div class="sheet-section">
        <h3>Retirement Pension</h3>
        <div class="credits-line">Cr${character.pension_per_year.toLocaleString()}/year</div>
        <p class="empty">Based on ${character.total_terms} terms served.</p>
      </div>` : ''}

      ${(character.dm_next_qualification || character.dm_next_advancement || character.dm_next_benefit) ? `
      <div class="sheet-section">
        <h3>Pending DMs</h3>
        <ul class="skill-list">
          ${character.dm_next_qualification ? `<li><span>Next qualification</span><span class="skill-level">${formatDM(character.dm_next_qualification)}</span></li>` : ''}
          ${character.dm_next_advancement ? `<li><span>Next advancement</span><span class="skill-level">${formatDM(character.dm_next_advancement)}</span></li>` : ''}
          ${character.dm_next_benefit ? `<li><span>Next benefit</span><span class="skill-level">${formatDM(character.dm_next_benefit)}</span></li>` : ''}
        </ul>
      </div>` : ''}

      <div class="sheet-section">
        <h3>Species Traits</h3>
        ${traitsHTML}
      </div>

      ${character.medical_debt > 0 ? `
      <div class="sheet-section warn">
        <h3>Medical Debt</h3>
        <div class="credits-line danger">Cr${character.medical_debt.toLocaleString()} owed</div>
        <p class="empty">Deducted automatically from mustering-out cash rolls.</p>
      </div>` : ''}

      ${(character.anagathics_purchased_terms > 0 || character.anagathics_addicted) ? `
      <div class="sheet-section">
        <h3>Anagathics</h3>
        <ul class="skill-list">
          ${character.anagathics_purchased_terms > 0 ? `<li><span>Treatments banked</span><span class="skill-level">${character.anagathics_purchased_terms}</span></li>` : ''}
          ${character.anagathics_addicted ? `<li><span style="color:var(--danger)">Addicted</span><span class="skill-level" style="color:var(--danger)">!</span></li>` : ''}
        </ul>
      </div>` : ''}

      ${character.home_forces_enrolled ? `
      <div class="sheet-section">
        <h3>Home Forces Reserves</h3>
        <ul class="skill-list">
          <li><span>Component</span><span class="skill-level">${(character.home_forces_component || 'groundside').replace('_',' ')}</span></li>
          <li><span>Reserve Rank</span><span class="skill-level">${character.home_forces_rank}</span></li>
        </ul>
        <p class="empty">Nat-2 survival → extra Reserve Mishap roll.</p>
      </div>` : ''}

      ${character.solsec_monitor ? `
      <div class="sheet-section">
        <h3>SolSec Monitor</h3>
        <ul class="skill-list">
          <li><span>Monitor Rank</span><span class="skill-level">${character.solsec_monitor_rank}</span></li>
        </ul>
        <p class="empty">DM+1 advancement · nat-2 → SolSec Mishap · nat-12 → SolSec Event${character.solsec_monitor_rank >= 3 ? ' · +1 Benefit roll' : ''}.</p>
      </div>` : ''}

      <div class="sheet-section">
        <h3>Notes</h3>
        <textarea id="char-notes" class="sheet-notes" placeholder="Personality, quirks, contacts, anything you want on the sheet…" rows="5">${(character.user_notes || '').replace(/</g, '&lt;')}</textarea>
      </div>
    </div>
  `;

  // Wire up name + homeworld
  document.getElementById('char-name').addEventListener('change', (e) => {
    character.name = e.target.value;
    saveCharacter();
  });
  document.getElementById('char-homeworld').addEventListener('change', (e) => {
    character.homeworld = e.target.value;
    saveCharacter();
  });
  const uwpEl = document.getElementById('char-uwp');
  if (uwpEl) uwpEl.addEventListener('change', (e) => {
    character.homeworld_uwp = e.target.value.trim();
    saveCharacter();
  });
  const notesEl = document.getElementById('char-notes');
  if (notesEl) notesEl.addEventListener('input', (e) => {
    character.user_notes = e.target.value;
    // Debounce the save so every keystroke doesn't hit localStorage
    clearTimeout(window._notesSaveTimer);
    window._notesSaveTimer = setTimeout(saveCharacter, 400);
  });
}

// ------------------------------------------------------------
// Rendering: Log (right panel)
// ------------------------------------------------------------

function renderLog() {
  const log = document.getElementById('log');
  log.innerHTML = (character.notes || []).slice(-80).map(n => `<li>${escapeHTML(n)}</li>`).join('');
  log.scrollTop = log.scrollHeight;
}

function escapeHTML(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Build a human-readable medical bills alert string from an injury-choice response.
 * Returns an empty string if no debt was incurred.
 */
function formatMedicalBillsMsg(response) {
  const gross = response.gross_debt || 0;
  if (gross <= 0) return '';
  const applied = response.applied || [];
  const bills = response.medical_bills_roll;
  const net = response.medical_debt_added || 0;
  const total = response.medical_debt_total || 0;

  let msg = `Injury applied: ${applied.join(', ') || 'resolved'}.`;
  msg += `\n\nMedical Bills (MgT2e p.47):`;
  msg += `\n  Gross debt: Cr${gross.toLocaleString()} (Cr5,000 × ${gross / 5000} pts)`;

  if (bills) {
    const rollStr = `2D(${bills.roll?.total ?? '?'}) + Rank ${bills.rank_dm} = ${bills.total}`;
    msg += `\n  Career category: ${bills.category}`;
    msg += `\n  Medical roll: ${rollStr}`;
    msg += `\n  Coverage: ${bills.coverage_pct}% — Cr${bills.covered.toLocaleString()} paid by career`;
    msg += `\n  You owe: Cr${net.toLocaleString()}`;
  } else {
    msg += `\n  You owe: Cr${net.toLocaleString()}`;
  }

  if (total > 0) {
    msg += `\n  Total medical debt: Cr${total.toLocaleString()} (deducted from mustering-out cash)`;
  }
  return msg;
}

// ------------------------------------------------------------
// Rendering: Stage (center panel — phase-specific UI)
// ------------------------------------------------------------

function renderStage() {
  const stage = document.getElementById('stage');

  if (character.dead) {
    stage.innerHTML = renderDeadStage();
    wireDeadStage();
    return;
  }

  switch (character.phase) {
    case 'characteristics':
      stage.innerHTML = renderCharacteristicsPhase();
      wireCharacteristicsPhase();
      break;
    case 'society':
      stage.innerHTML = renderSocietyPhase();
      wireSocietyPhase();
      break;
    case 'species':
      stage.innerHTML = renderSpeciesPhase();
      wireSpeciesPhase();
      break;
    case 'background':
      stage.innerHTML = renderBackgroundPhase();
      wireBackgroundPhase();
      break;
    case 'pre_career':
      stage.innerHTML = renderPreCareerPhase();
      wirePreCareerPhase();
      break;
    case 'career':
      stage.innerHTML = renderCareerPhase();
      wireCareerPhase();
      break;
    case 'mustering':
      stage.innerHTML = renderMusterPhase();
      wireMusterPhase();
      break;
    case 'skill_package':
      stage.innerHTML = renderSkillPackagePhase();
      wireSkillPackagePhase();
      break;
    case 'done':
      stage.innerHTML = renderDonePhase();
      wireDonePhase();
      break;
    default:
      stage.innerHTML = `<div class="stage-content"><p>Unknown phase: ${character.phase}</p></div>`;
  }
}

// ============================================================
// PHASE 1: Characteristics
// ============================================================

function rollQuality(total) {
  // Expected range for 6 * 2D: mean 42, SD ~5.9. Thresholds picked to give
  // descriptive names the player can parse at a glance.
  if (total >= 60) return { tier: 'Exceptional', note: 'elite rolls — very few Travellers have this starting material', cls: 'q-elite' };
  if (total >= 54) return { tier: 'Strong',      note: 'well above average — most careers will take you', cls: 'q-strong' };
  if (total >= 48) return { tier: 'Solid',       note: 'above average — a capable Traveller', cls: 'q-solid' };
  if (total >= 36) return { tier: 'Average',     note: 'typical 2D spread — expect some hard survival rolls', cls: 'q-average' };
  if (total >= 30) return { tier: 'Lean',        note: 'below average — consider a reroll or a rearrange', cls: 'q-lean' };
  return                    { tier: 'Rough',      note: 'brutal rolls — strongly consider rerolling', cls: 'q-rough' };
}

function renderCharacteristicsPhase() {
  const hasRolled = Object.values(character.characteristics).some(v => v > 0);
  const STATS = ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC'];

  // Compute best / worst stat so they can be highlighted in the grid and called out.
  let bestStat = null, worstStat = null, total = 0, totalDM = 0;
  if (hasRolled) {
    for (const s of STATS) {
      const v = character.characteristics[s];
      total += v;
      totalDM += charDM(v);
      if (bestStat === null || v > character.characteristics[bestStat]) bestStat = s;
      if (worstStat === null || v < character.characteristics[worstStat]) worstStat = s;
    }
  }
  const q = hasRolled ? rollQuality(total) : null;

  // Stat grid — each cell shows rolled value + DM, makes swap decisions concrete.
  const statGrid = hasRolled ? `
    <div class="stat-grid-rolled">
      ${STATS.map(stat => {
        const val = character.characteristics[stat];
        const dm = charDM(val);
        const extra = [];
        if (stat === bestStat && bestStat !== worstStat) extra.push('best');
        if (stat === worstStat && bestStat !== worstStat) extra.push('worst');
        if (uiState.swapPick === stat) extra.push('picked');
        return `
          <div class="stat-cell-rolled ${extra.join(' ')}"
               data-stat="${stat}">
            <span class="stat-label">${stat}</span>
            <span class="stat-value">${val}</span>
            <span class="stat-dm">DM ${formatDM(dm)}</span>
            ${(uiState.gmMode || character.boon_rolls_remaining > 0) ? `
              <button class="boon-btn" data-boon-stat="${stat}" title="Re-roll ${stat}, keep the higher value">BOON</button>
            ` : ''}
          </div>
        `;
      }).join('')}
    </div>
  ` : '';

  // Roll quality readout — sits between the dice banner and the stat grid
  // so the player can tell at a glance whether this is a keep or a reroll.
  const qualityReadout = hasRolled ? `
    <div class="roll-quality ${q.cls}">
      <div class="rq-header">
        <span class="rq-label">ROLL QUALITY</span>
        <span class="rq-tier">${q.tier}</span>
      </div>
      <div class="rq-stats">
        <span class="rq-stat"><span class="rq-k">TOTAL</span><span class="rq-v">${total}</span><span class="rq-cmp">of 72 avg 42</span></span>
        <span class="rq-stat"><span class="rq-k">NET DM</span><span class="rq-v">${formatDM(totalDM)}</span></span>
        <span class="rq-stat"><span class="rq-k">BEST</span><span class="rq-v">${bestStat} ${character.characteristics[bestStat]}</span></span>
        <span class="rq-stat"><span class="rq-k">WORST</span><span class="rq-v">${worstStat} ${character.characteristics[worstStat]}</span></span>
      </div>
      <div class="rq-note">${q.note}</div>
    </div>
  ` : '';

  // Swap controls — two dropdowns + a button. Pre-select the current
  // pick if the user clicked a tile.
  const swapRow = hasRolled ? `
    <div class="swap-row">
      <span class="swap-label">REARRANGE</span>
      <select id="swap-a" class="swap-select">
        ${STATS.map(s => `<option value="${s}" ${s === (uiState.swapA || 'EDU') ? 'selected' : ''}>${s} (${character.characteristics[s]})</option>`).join('')}
      </select>
      <span class="swap-arrow">↔</span>
      <select id="swap-b" class="swap-select">
        ${STATS.map(s => `<option value="${s}" ${s === (uiState.swapB || 'STR') ? 'selected' : ''}>${s} (${character.characteristics[s]})</option>`).join('')}
      </select>
      <button class="btn" id="btn-swap-stats">SWAP</button>
    </div>
    <p class="swap-hint">Click a tile above to quick-pick, or use the dropdowns. Example: moving EDU→STR to build a brawler.</p>
  ` : '';

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 01 — CHARACTERISTICS</span></div>
    <div class="stage-content">
      <div class="phase-label">Terminal Session Begin</div>
      <h2 class="phase-title">Roll Your Traveller</h2>
      <p class="phase-subtitle">Six characteristics define the bright-eyed 18-year-old about to take on the universe.</p>

      <div class="phase-body">
        <p>You are about to generate a Traveller. Each characteristic — <strong>STR</strong>, <strong>DEX</strong>, <strong>END</strong>, <strong>INT</strong>, <strong>EDU</strong>, <strong>SOC</strong> — is determined by rolling 2D. The resulting score yields a Dice Modifier that will govern almost every roll your Traveller makes across their life.</p>
        <p><em>After rolling, you can rearrange values between characteristics. You can keep rerolling and swapping until you commit to a species — then the numbers are locked in.</em></p>
      </div>

      ${hasRolled ? `
        <div class="roll-readout">
          <span class="dice">2D × 6</span>
          <span class="eq">—</span>
          <span class="total">ROLLED</span>
        </div>
      ` : `
        <div class="roll-readout" style="opacity:0.4">
          <span class="dice">—</span>
          <span class="eq">awaiting</span>
          <span class="total">input</span>
        </div>
      `}

      ${qualityReadout}
      ${statGrid}
      ${swapRow}

      ${uiState.gmMode ? `
        <div class="gm-panel">
          <span class="gm-badge">GM MODE</span>
          <label class="gm-field">
            BOON POOL
            <input type="number" id="gm-boon-pool" min="0" max="20" value="${character.boon_rolls_total}" />
            <button class="btn ghost" id="btn-set-boon-pool">SET</button>
          </label>
          <span class="gm-hint">Click any stat value to edit directly. BOON re-rolls keep the higher value.</span>
        </div>
      ` : ''}
      ${(!uiState.gmMode && character.boon_rolls_remaining > 0) ? `
        <div class="boon-banner">
          <strong>${character.boon_rolls_remaining}</strong> boon roll${character.boon_rolls_remaining === 1 ? '' : 's'} available. Click BOON on any stat to re-roll it — you keep the higher.
        </div>
      ` : ''}

      <div class="phase-actions">
        <button class="btn primary" id="btn-roll-stats">${hasRolled ? 'REROLL ALL' : 'ROLL 2D × 6'}</button>
        <button class="btn" id="btn-to-species" ${hasRolled ? '' : 'disabled'}>CHOOSE ORIGIN →</button>
      </div>
    </div>
  `;
}

function wireCharacteristicsPhase() {
  document.getElementById('btn-roll-stats').addEventListener('click', async () => {
    uiState.swapPick = null;
    const response = await apiCall('/api/character/roll-characteristics');
    await applyResponse(response);
    renderAll();
  });
  document.getElementById('btn-to-species').addEventListener('click', () => {
    uiState.swapPick = null;
    character.phase = 'society';
    saveCharacter();
    renderAll();
  });

  // Click-to-pick on stat tiles: first click sets slot A, second sets B
  // and auto-triggers a swap.
  document.querySelectorAll('.stat-cell-rolled').forEach(cell => {
    cell.addEventListener('click', async () => {
      const stat = cell.dataset.stat;
      if (!uiState.swapPick) {
        uiState.swapPick = stat;
        uiState.swapA = stat;
        renderAll();
        return;
      }
      if (uiState.swapPick === stat) {
        // Same tile clicked again — cancel pick.
        uiState.swapPick = null;
        renderAll();
        return;
      }
      // Second pick — perform the swap immediately.
      const a = uiState.swapPick;
      const b = stat;
      uiState.swapPick = null;
      uiState.swapA = a;
      uiState.swapB = b;
      try {
        const response = await apiCall('/api/character/swap-stats', { stat_a: a, stat_b: b });
        await applyResponse(response);
      } catch (e) {
        alert(e.message);
      }
      renderAll();
    });
  });

  // Dropdown swap
  const swapA = document.getElementById('swap-a');
  const swapB = document.getElementById('swap-b');
  const swapBtn = document.getElementById('btn-swap-stats');
  if (swapA) swapA.addEventListener('change', () => { uiState.swapA = swapA.value; });
  if (swapB) swapB.addEventListener('change', () => { uiState.swapB = swapB.value; });
  if (swapBtn) {
    swapBtn.addEventListener('click', async () => {
      const a = swapA.value;
      const b = swapB.value;
      if (a === b) {
        alert('Pick two different characteristics to swap.');
        return;
      }
      try {
        const response = await apiCall('/api/character/swap-stats', { stat_a: a, stat_b: b });
        await applyResponse(response);
      } catch (e) {
        alert(e.message);
      }
      renderAll();
    });
  }

  // Boon buttons per stat cell
  document.querySelectorAll('[data-boon-stat]').forEach(btn => {
    btn.addEventListener('click', async (ev) => {
      ev.stopPropagation();  // don't trigger the tile's swap-pick
      const stat = btn.dataset.boonStat;
      try {
        const response = await apiCall('/api/character/boon', { stat });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'boon',
          data: response.roll,
          stat: response.stat,
          old: response.old,
          new: response.new,
          kept: response.kept,
        };
      } catch (e) {
        alert(e.message);
      }
      renderAll();
    });
  });

  // GM: set boon pool
  const gmBoonPool = document.getElementById('btn-set-boon-pool');
  if (gmBoonPool) {
    gmBoonPool.addEventListener('click', async () => {
      const count = parseInt(document.getElementById('gm-boon-pool').value, 10) || 0;
      try {
        const response = await apiCall('/api/character/boon-pool', { count });
        await applyResponse(response);
      } catch (e) { alert(e.message); }
      renderAll();
    });
  }

  // GM: direct-edit a stat by double-clicking its value
  if (uiState.gmMode) {
    document.querySelectorAll('.stat-cell-rolled .stat-value').forEach(el => {
      el.addEventListener('dblclick', (ev) => {
        const cell = ev.target.closest('[data-stat]');
        const stat = cell?.dataset?.stat;
        if (!stat) return;
        const current = character.characteristics[stat];
        const nextStr = prompt(`Set ${stat} to:`, String(current));
        if (nextStr === null) return;
        const next = parseInt(nextStr, 10);
        if (isNaN(next) || next < 0 || next > 20) {
          alert('Enter a number between 0 and 20.');
          return;
        }
        character.characteristics[stat] = next;
        character.notes.push(`GM: set ${stat} to ${next} (was ${current}).`);
        saveCharacter();
        renderAll();
      });
    });
  }
}

// ============================================================
// PHASE 2a: Society of Origin
// ============================================================

function renderSocietyPhase() {
  const selected = character.society_id || '';
  const cards = SOCIETIES.map((soc, idx) => {
    const num = String(idx + 1).padStart(2, '0');
    const isSelected = selected === soc.id;
    const speciesCount = soc.species_ids.length;
    const speciesLabel = speciesCount === 1 ? '1 species' : `${speciesCount} species`;
    return `
      <button class="card ${isSelected ? 'selected' : ''}" data-society="${soc.id}">
        <div class="card-title">${num}. ${soc.name}</div>
        <div class="card-meta">${soc.subtitle} · ${speciesLabel}</div>
        <div class="card-desc">${soc.description}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02 — SOCIETY OF ORIGIN</span></div>
    <div class="stage-content">
      <div class="phase-label">Cultural Background</div>
      <h2 class="phase-title">Where Were You Raised?</h2>
      <p class="phase-subtitle">Your society of origin determines which species are available and shapes your cultural background. It does not restrict your career choices — Travellers move between polities.</p>

      <div class="card-grid">${cards}</div>

      <div class="phase-actions">
        <button class="btn ghost" id="btn-back-society">← BACK</button>
        <button class="btn primary" id="btn-confirm-society" ${selected ? '' : 'disabled'}>
          SELECT SPECIES →
        </button>
      </div>
    </div>
  `;
}

function wireSocietyPhase() {
  document.querySelectorAll('[data-society]').forEach(card => {
    card.addEventListener('click', () => {
      character.society_id = card.dataset.society;
      uiState.selectedSpecies = null; // reset any prior species pick when society changes
      saveCharacter();
      renderStage();
    });
  });

  document.getElementById('btn-back-society').addEventListener('click', () => {
    character.phase = 'characteristics';
    saveCharacter();
    renderAll();
  });

  const confirmBtn = document.getElementById('btn-confirm-society');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
      if (!character.society_id) return;
      character.phase = 'species';
      saveCharacter();
      renderAll();
    });
  }
}

// ============================================================
// PHASE 2b: Species
// ============================================================

function renderSpeciesPhase() {
  // If a Heritage Roll result is pending, show the result panel instead
  if (uiState.racialBackgroundResult) {
    return renderRacialBackgroundResult();
  }

  const selected = uiState.selectedSpecies || character.species_id;
  const speciesApplied = character.species_id && character.traits && character.traits.length >= 0 && character.phase !== 'species';

  // Filter species list by the selected society
  const activeSociety = SOCIETIES.find(s => s.id === (character.society_id || 'third_imperium'));
  const allowedIds = activeSociety ? new Set(activeSociety.species_ids) : null;
  const filteredSpecies = allowedIds ? SPECIES.filter(sp => allowedIds.has(sp.id)) : SPECIES;

  const cards = filteredSpecies.map(sp => {
    const isRollTrigger = !!sp.racial_background_roll;
    const modsText = isRollTrigger
      ? '2D Heritage Roll'
      : (Object.entries(sp.characteristic_modifiers)
          .filter(([, v]) => v !== 0)
          .map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`)
          .join(' · ') || 'No modifiers');
    return `
      <button class="card ${selected === sp.id ? 'selected' : ''}" data-species="${sp.id}">
        <div class="card-title">${sp.name}</div>
        <div class="card-meta">${modsText}</div>
        <div class="card-desc">${sp.description}</div>
        ${isRollTrigger ? '<div class="card-meta" style="color:var(--amber)">🎲 Roll determines your exact heritage</div>' : ''}
      </button>
    `;
  }).join('');

  const selectedSp = SPECIES.find(s => s.id === selected);
  const traitsPanel = selectedSp && selectedSp.traits.length ? `
    <div class="species-traits-panel">
      <h4>Species Traits — ${selectedSp.name}</h4>
      ${selectedSp.traits.map(t => `
        <div class="trait">
          <span class="trait-name">${t.name}</span>
          <span class="trait-desc">${t.description}</span>
        </div>
      `).join('')}
    </div>
  ` : (selectedSp ? '<p class="empty" style="margin-top:14px">No special traits. The baseline Traveller experience.</p>' : '');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — SPECIES SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Genetic Profile</div>
      <h2 class="phase-title">Choose Your Species</h2>
      <p class="phase-subtitle">Species modifiers apply immediately to your rolled characteristics.</p>

      <div class="species-intro">
        <p>
          ${activeSociety
            ? `Showing species available to characters raised in the <strong>${activeSociety.name}</strong>.`
            : 'Showing all available species.'
          }
          Species modifiers apply once, now, to the characteristics you just rolled.
        </p>
        <p class="species-intro-hint">
          <em>Pick whichever fits the character concept. The numbers balance out across a full career arc — flavor is
          usually the deciding factor.</em>
        </p>
      </div>

      <div class="card-grid">${cards}</div>

      ${traitsPanel}

      <div class="phase-actions">
        <button class="btn ghost" id="btn-back-stats">← ORIGIN</button>
        <button class="btn primary" id="btn-apply-species" ${selected ? '' : 'disabled'}>
          ${selectedSp?.racial_background_roll
            ? '🎲 ROLL HERITAGE →'
            : 'APPLY ' + (selectedSp ? selectedSp.name.toUpperCase() : 'SPECIES') + ' →'}
        </button>
      </div>
    </div>
  `;
}

function renderRacialBackgroundResult() {
  const result = uiState.racialBackgroundResult;
  const resolvedSp = SPECIES.find(s => s.id === character.species_id);
  const dice = result.heritage_roll?.dice || [];
  const total = result.heritage_roll?.total ?? '?';
  const mods = resolvedSp ? Object.entries(resolvedSp.characteristic_modifiers || {})
    .filter(([, v]) => v !== 0)
    .map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`)
    .join(' · ') : '';

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — HERITAGE ROLL</span></div>
    <div class="stage-content">
      <div class="phase-label">Solomani Heritage Determination</div>
      <h2 class="phase-title">Heritage Determined</h2>
      <p class="phase-subtitle">A 2D roll determines your ancestry within the Solomani Confederation.</p>

      <div class="roll-result-block" style="text-align:center;margin:24px 0">
        <div style="font-size:11px;letter-spacing:2px;color:var(--text-dim);margin-bottom:8px">HERITAGE ROLL</div>
        <div style="font-size:48px;font-weight:900;color:var(--accent)">${total}</div>
        <div style="font-size:13px;color:var(--text-dim)">(${dice.join(' + ')})</div>
      </div>

      <div class="result-block" style="border:1px solid var(--accent);border-radius:6px;padding:16px;margin-bottom:20px">
        <div style="font-size:11px;letter-spacing:2px;color:var(--accent);margin-bottom:6px">RESULT</div>
        <div style="font-size:20px;font-weight:700">${result.result_name}</div>
        ${mods ? `<div style="font-size:12px;color:var(--text-dim);margin-top:4px">Characteristic modifiers: ${mods}</div>` : ''}
        ${resolvedSp?.description ? `<p style="font-size:13px;margin-top:10px">${resolvedSp.description}</p>` : ''}
      </div>

      ${resolvedSp?.traits?.length ? `
        <div class="species-traits-panel">
          <h4>Heritage Traits — ${resolvedSp.name}</h4>
          ${resolvedSp.traits.map(t => `
            <div class="trait">
              <span class="trait-name">${t.name}</span>
              <span class="trait-desc">${t.description}</span>
            </div>
          `).join('')}
        </div>
      ` : ''}

      <div class="phase-actions">
        <button class="btn primary" id="btn-after-heritage">CONTINUE →</button>
      </div>
    </div>
  `;
}

function wireSpeciesPhase() {
  // Heritage roll result screen — just needs a Continue button
  if (uiState.racialBackgroundResult) {
    document.getElementById('btn-after-heritage').addEventListener('click', () => {
      uiState.racialBackgroundResult = null;
      character.phase = 'background';
      saveCharacter();
      renderAll();
    });
    return;
  }

  document.querySelectorAll('[data-species]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedSpecies = card.dataset.species;
      renderStage();
    });
  });
  document.getElementById('btn-back-stats').addEventListener('click', () => {
    character.phase = 'society';
    saveCharacter();
    renderAll();
  });
  document.getElementById('btn-apply-species').addEventListener('click', async () => {
    if (!uiState.selectedSpecies) return;
    const sp = SPECIES.find(s => s.id === uiState.selectedSpecies);
    if (sp?.racial_background_roll) {
      // Solomani heritage: roll 2D to determine subtype
      const response = await apiCall('/api/character/racial-background-roll', {});
      await applyResponse(response);
      uiState.racialBackgroundResult = response;
      renderStage();
      return;
    }
    const response = await apiCall('/api/character/apply-species', { species_id: uiState.selectedSpecies });
    await applyResponse(response);
    character.phase = 'background';
    saveCharacter();
    renderAll();
  });
}

// ============================================================
// PHASE 3: Background Skills
// ============================================================

function renderBackgroundPhase() {
  const eduDm = charDM(character.characteristics.EDU);
  const allowed = Math.max(0, eduDm + 3);
  const selected = uiState.selectedBgSkills;

  // Load skill list from bootstrap (we'll fetch lazily)
  const bgSkills = ['Admin', 'Animals', 'Art', 'Athletics', 'Carouse', 'Drive', 'Electronics',
    'Flyer', 'Language', 'Mechanic', 'Medic', 'Profession', 'Science', 'Seafarer',
    'Streetwise', 'Survival', 'Vacc Suit'];

  const chips = bgSkills.map(skill => {
    const isSelected = selected.has(skill);
    const disabled = !isSelected && selected.size >= allowed;
    return `
      <button class="skill-chip ${isSelected ? 'selected' : ''}" data-skill="${skill}" ${disabled ? 'disabled' : ''}>
        ${skill}
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 03 — BACKGROUND SKILLS</span></div>
    <div class="stage-content">
      <div class="phase-label">Adolescence · Pre-Career</div>
      <h2 class="phase-title">Formative Years</h2>
      <p class="phase-subtitle">Skills picked up during your upbringing, before the universe happened to you.</p>

      <div class="phase-body">
        <p>Your <strong>Education DM</strong> is <strong>${formatDM(eduDm)}</strong>, so you get <strong>${allowed}</strong> background skill${allowed === 1 ? '' : 's'} at level 0. Think about where your Traveller grew up — an agri-world? An asteroid belt? A starport slum? Pick skills that tell that story.</p>
      </div>

      <div class="skill-picker">${chips}</div>
      <div class="picker-status">SELECTED ${selected.size} / ${allowed}</div>

      <div class="phase-actions">
        <button class="btn ghost" id="btn-back-species">← BACK</button>
        <button class="btn primary" id="btn-confirm-bg" ${selected.size === allowed ? '' : 'disabled'}>
          CONFIRM BACKGROUND →
        </button>
        <button class="btn" id="btn-skip-bg" ${allowed > 0 ? 'disabled' : ''}>
          SKIP (NO SKILLS)
        </button>
      </div>
    </div>
  `;
}

function wireBackgroundPhase() {
  document.querySelectorAll('[data-skill]').forEach(chip => {
    chip.addEventListener('click', () => {
      const skill = chip.dataset.skill;
      if (uiState.selectedBgSkills.has(skill)) {
        uiState.selectedBgSkills.delete(skill);
      } else {
        uiState.selectedBgSkills.add(skill);
      }
      renderStage();
    });
  });
  document.getElementById('btn-back-species').addEventListener('click', () => {
    character.phase = 'species';
    saveCharacter();
    renderAll();
  });
  document.getElementById('btn-confirm-bg').addEventListener('click', async () => {
    const chosen = Array.from(uiState.selectedBgSkills);
    const response = await apiCall('/api/character/background-skills', { chosen });
    await applyResponse(response);
    renderAll();
  });
  const skipBtn = document.getElementById('btn-skip-bg');
  if (skipBtn) {
    skipBtn.addEventListener('click', async () => {
      const response = await apiCall('/api/character/background-skills', { chosen: [] });
      await applyResponse(response);
      renderAll();
    });
  }
}

// ============================================================
// PHASE 3.5: Pre-Career Education (optional)
// ============================================================

const PRE_CAREER_SERVICES = [
  { id: 'army',   name: 'Military Academy — Army',    career_id: 'army',
    desc: 'Officer track for the ground forces. Tough qualification, solid pay.' },
  { id: 'marine', name: 'Military Academy — Marines', career_id: 'marine',
    desc: 'Hardest qualification target. Commissioned marines lead boarding actions.' },
  { id: 'navy',   name: 'Military Academy — Navy',    career_id: 'navy',
    desc: 'The prestige track. INT-based qualification, ship-bound officer career.' },
];

function renderPreCareerPhase() {
  const status = character.pre_career_status || {};
  const stage = status.stage || 'none';

  // Skill picker screen — shown after enrollment (level 0) or graduation (level 1)
  if (uiState.lastRoll?.type === 'precareer_skill_pick') {
    const remaining = status.skill_picks_remaining || 0;
    const pool = status.skill_pool || [];
    const pickLevel = status.skill_pick_level ?? 1;
    const pickStage = status.skill_pick_stage ?? 'graduation';
    const stageLabel = pickStage === 'enrollment' ? 'Enrollment Skills' : 'Graduation Skills';
    const levelLabel = pickLevel === 0 ? 'level 0 (your majors — you can raise them later)' : 'level 1';
    const picked = Array.from(uiState.selectedPreCareerSkills || new Set());
    const picker = pool.map(s => {
      const sel = picked.includes(s);
      return `<button class="skill-chip ${sel ? 'selected' : ''}" data-pc-skill="${escapeHTML(s)}"
        ${!sel && picked.length >= remaining ? 'disabled' : ''}>${escapeHTML(s)}</button>`;
    }).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">${escapeHTML(stageLabel)}</div>
        <h2 class="phase-title">Pick ${remaining} Skill${remaining === 1 ? '' : 's'}</h2>
        <p class="phase-body">Choose <strong>${remaining}</strong> skill${remaining === 1 ? '' : 's'} at <strong>${levelLabel}</strong>.</p>
        <div class="skill-picker">${picker}</div>
        <div class="phase-actions">
          <button class="btn primary" id="btn-confirm-pc-skills"
            ${picked.length !== remaining ? 'disabled' : ''}>
            ${picked.length === remaining ? `CONFIRM ${remaining}/${remaining} →` : `PICK ${remaining - picked.length} MORE`}
          </button>
        </div>
      </div>
    `;
  }

  // Post-roll view: show the qualification roll outcome
  if (uiState.lastRoll?.type === 'precareer_qualify') {
    const lr = uiState.lastRoll;
    const passed = lr.passed;
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Qualification Roll — ${lr.trackName}</div>
        <h2 class="phase-title">${passed ? 'Qualified' : 'Did Not Qualify'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${lr.charLabel} ${lr.target}+` })}
        ${lr.enrollmentApplied?.length ? `
          <div class="dm-applied-box">
            <span class="event-label">Enrollment bonus</span>
            ${lr.enrollmentApplied.map(s => `<div class="dm-chip applied">${escapeHTML(s)}</div>`).join('')}
          </div>
        ` : ''}
        <p class="phase-body">${passed
          ? `Enrolled. ${lr.ageCost ? `${lr.ageCost} years pass while you study — one event per year, then graduation.` : 'Now roll events and then graduation.'}`
          : `Didn't meet the bar. You skip straight to your first career without any education bonus.`
        }</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-precareer-qualify">
            ${passed ? 'BEGIN STUDIES →' : 'CONTINUE TO CAREER →'}
          </button>
        </div>
      </div>
    `;
  }

  // Post-roll view: graduation outcome (event already rolled, shown inline)
  if (uiState.lastRoll?.type === 'precareer_graduate') {
    const lr = uiState.lastRoll;
    const labels = { pass: 'Graduated', honours: 'Graduated with Honours', fail: 'Failed to Graduate' };
    const ev = lr.event || {};
    const appliedHTML = lr.applied?.length ? `
      <div class="dm-applied-box">
        <span class="event-label">Graduation benefits</span>
        ${lr.applied.map(s => `<div class="dm-chip applied">${escapeHTML(s)}</div>`).join('')}
      </div>
    ` : '';
    const eventHTML = `
      <div class="event-box">
        <span class="event-label">Education Event [2D=${ev.roll?.total ?? '?'}]</span>
        ${escapeHTML(ev.event_text || 'Nothing remarkable happens.')}
      </div>
      ${ev.auto_applied?.length ? `
        <div class="dm-applied-box">
          <span class="event-label">Auto-applied</span>
          ${ev.auto_applied.map(s => `<div class="dm-chip applied">${escapeHTML(s)}</div>`).join('')}
        </div>` : ''}
      ${ev.forced_fail ? `<p class="phase-body" style="color:var(--danger)">This event overrides your graduation — you fail to graduate.</p>` : ''}
    `;
    const hasPicks = (status.skill_picks_remaining || 0) > 0;
    const pendingAnySkill = !!ev.pending_any_skill;
    const pendingEvent10 = !!ev.pending_event10;
    const pendingEvent11 = !!ev.pending_event11;
    const pendingLifeEvent = !!ev.pending_life_event;
    const lifeEventChoiceKind = ev.life_event_choice_kind || null;
    const pendingInjury = !!ev.pending_injury;
    const injuryData = ev.injury_pending_data || character.pending_injury_choice || null;
    const nextBtn = pendingEvent11
      ? `<button class="btn primary" id="btn-show-event11">RESPOND TO DRAFT →</button>`
      : pendingEvent10
        ? `<button class="btn primary" id="btn-show-event10">TAKE TUTOR CHALLENGE →</button>`
        : (pendingInjury || character.pending_injury_choice)
          ? `<button class="btn primary" id="btn-show-injury-choice">RESOLVE INJURY →</button>`
          : pendingLifeEvent
            ? `<button class="btn primary" id="btn-show-life-event-choice">RESOLVE LIFE EVENT →</button>`
            : pendingAnySkill
              ? `<button class="btn primary" id="btn-show-any-skill-pick">CHOOSE EVENT SKILL →</button>`
              : hasPicks
                ? `<button class="btn primary" id="btn-start-skill-pick">PICK GRADUATION SKILLS →</button>`
                : `<button class="btn primary" id="btn-post-precareer-graduate">CONTINUE TO CAREER →</button>`;
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Graduation — ${labels[lr.outcome]}</div>
        <h2 class="phase-title">${labels[lr.outcome]}</h2>
        ${rollReadoutHTML(lr.data, { label: `${lr.charLabel} ${lr.target}+` })}
        ${appliedHTML}
        ${eventHTML}
        <p class="picker-status"><em>Apply any additional event effects manually.</em></p>
        <div class="phase-actions">${nextBtn}</div>
      </div>
    `;
  }

  // Injury stat choice screen — shown when pending_injury_choice is set
  if (uiState.lastRoll?.type === 'precareer_injury_choice') {
    const inj = character.pending_injury_choice || uiState.lastRoll.injuryData || {};
    const choices = inj.choices || ['STR', 'DEX', 'END'];
    const prompt = inj.prompt || 'Choose a physical characteristic to absorb the damage.';
    const title = inj.title || 'Injury';
    const dmgAmount = inj.damage_to_chosen ?? '?';
    const autoOthers = inj.auto_reduce_others || 0;

    const statDescriptions = { STR: 'Strength', DEX: 'Dexterity', END: 'Endurance' };
    const cards = choices.map(stat => `
      <button class="card" id="btn-injury-stat-${stat}">
        <div class="card-title">${stat} — ${statDescriptions[stat] || stat}</div>
        <div class="card-meta">Current: ${character.characteristics[stat] ?? '?'}</div>
        <div class="card-desc">Reduce by ${dmgAmount}${autoOthers ? ` (other two: each -${autoOthers})` : ''}. Medical debt: Cr${(dmgAmount * 5000).toLocaleString()} + ${autoOthers ? `Cr${(autoOthers * 2 * 5000).toLocaleString()} others` : 'none'}.</div>
      </button>
    `).join('');

    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Injury — ${title}</div>
        <h2 class="phase-title">${title}</h2>
        <p class="phase-body">${prompt}</p>
        <p class="phase-body" style="color:var(--amber-dim);font-size:11px">Medical care costs Cr 5,000 per point lost. This will be recorded as debt and deducted from mustering-out cash.</p>
        <div class="card-grid">${cards}</div>
      </div>
    `;
  }

  // Life event interactive choice screen
  if (uiState.lastRoll?.type === 'precareer_life_event_choice') {
    const kind = uiState.lastRoll.choiceKind;
    const hasBenefitRolls = (character.pending_benefit_rolls || 0) > 0;

    let title, body, buttons;
    if (kind === 'romantic_split') {
      title = 'Life Event — Relationship Ends Badly';
      body = 'A romantic relationship involving you ends badly. Choose the consequence:';
      buttons = `
        <button class="card" id="btn-life-choice-rival">
          <div class="card-title">Rival [Romantic]</div>
          <div class="card-desc">They become a rival — someone who competes with or resents you.</div>
        </button>
        <button class="card" id="btn-life-choice-enemy">
          <div class="card-title">Enemy [Romantic]</div>
          <div class="card-desc">They become an enemy — actively working against you.</div>
        </button>`;
    } else if (kind === 'betrayal_no_associates') {
      title = 'Life Event — Betrayal';
      body = 'A friend has betrayed you. You have no existing Contacts or Allies to convert. Gain one of:';
      buttons = `
        <button class="card" id="btn-life-choice-rival">
          <div class="card-title">Rival [Betrayer]</div>
          <div class="card-desc">They become a rival — someone who resents or opposes you.</div>
        </button>
        <button class="card" id="btn-life-choice-enemy">
          <div class="card-title">Enemy [Betrayer]</div>
          <div class="card-desc">They become an active enemy — a serious, ongoing threat.</div>
        </button>`;
    } else if (kind === 'crime_choice') {
      title = 'Life Event — Crime';
      body = 'You commit or are accused of a crime. Choose your consequence:';
      buttons = `
        <button class="card ${hasBenefitRolls ? '' : 'locked'}" id="btn-life-choice-lose_benefit" ${hasBenefitRolls ? '' : 'disabled'}>
          <div class="card-title">Lose a Benefit Roll ${hasBenefitRolls ? '' : '(none available)'}</div>
          <div class="card-desc">You pay a fine or bribe. Lose one mustering-out benefit roll.</div>
        </button>
        <button class="card" id="btn-life-choice-prisoner">
          <div class="card-title">Take the Prisoner Career</div>
          <div class="card-desc">You serve time. Your next career must be Prisoner.</div>
        </button>`;
    } else {
      title = 'Life Event Choice';
      body = 'An unexpected event requires a decision.';
      buttons = '';
    }

    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Life Event — Choose</div>
        <h2 class="phase-title">${title}</h2>
        <p class="phase-body">${body}</p>
        <div class="card-grid">${buttons}</div>
      </div>
    `;
  }

  // Event 10 — tutor challenge skill picker
  if (uiState.lastRoll?.type === 'precareer_event10') {
    const lr = uiState.lastRoll;
    const pool = status.event10_skill_pool || [];
    const filter = uiState.event10Filter || '';
    const filtered = pool.filter(s => s.toLowerCase().includes(filter.toLowerCase()));
    const chips = filtered.map(s =>
      `<button class="skill-chip" data-event10-skill="${escapeHTML(s)}">${escapeHTML(s)}</button>`
    ).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Education Event 10 — Tutor Challenge</div>
        <h2 class="phase-title">Challenge Your Tutor</h2>
        <p class="phase-body">Pick a skill from your education curriculum, then roll 2D 9+. Success: +1 level in that skill and gain a Rival [Tutor].</p>
        <input class="skill-search" id="event10-skill-search" type="text" placeholder="Filter skills…" value="${escapeHTML(filter)}" autocomplete="off" />
        <div class="skill-picker">${chips}</div>
      </div>
    `;
  }

  // Event 11 — draft event: Drifter / Draft / Dodge
  if (uiState.lastRoll?.type === 'precareer_event11') {
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Education Event 11 — Draft!</div>
        <h2 class="phase-title">War Is Coming</h2>
        <p class="phase-body">A wide-ranging draft has been instigated. Choose your response:</p>
        <div class="card-grid">
          <button class="card" id="btn-event11-drifter">
            <div class="card-title">Flee — Drifter</div>
            <div class="card-desc">Avoid the draft by dropping out. You do not graduate. Your next career must be Drifter.</div>
          </button>
          <button class="card" id="btn-event11-draft">
            <div class="card-title">Accept the Draft</div>
            <div class="card-desc">Roll 1D: 1–3 Army, 4–5 Marine, 6 Navy. You do not graduate but enter that service directly.</div>
          </button>
          <button class="card" id="btn-event11-dodge">
            <div class="card-title">Pull Strings — Dodge (SOC 9+)</div>
            <div class="card-desc">Roll SOC 9+. Success: ignore the draft and continue to graduation. Failure: you do not graduate.</div>
          </button>
        </div>
      </div>
    `;
  }

  // Event 9 any-skill picker
  if (uiState.lastRoll?.type === 'precareer_any_skill_pick') {
    const lr = uiState.lastRoll;
    const filter = uiState.anySkillFilter || '';
    const filtered = ALL_SKILLS_NO_JOT.filter(s => s.toLowerCase().includes(filter.toLowerCase()));
    const chips = filtered.slice(0, 60).map(s =>
      `<button class="skill-chip" data-any-skill="${escapeHTML(s)}">${escapeHTML(s)}</button>`
    ).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Education Event — Free Skill</div>
        <h2 class="phase-title">Choose Any Skill (Level 0)</h2>
        <p class="phase-body">Pick any skill except Jack-of-All-Trades. It is gained at level 0.</p>
        <input class="skill-search" id="any-skill-search" type="text" placeholder="Filter skills…" value="${escapeHTML(filter)}" autocomplete="off" />
        <div class="skill-picker">${chips}</div>
      </div>
    `;
  }

  // Enrolled — always show graduate button immediately (events roll after graduation)
  if (stage === 'enrolled') {
    const track = status.track;
    const service = status.service;
    const trackName = trackDisplayName(track, service, status);
    const gradHint = trackGradHint(track);

    if (track === 'psionic_community' && status.pending_psionic_training) {
      const trainedTalents = character.psi_trained_talents || [];
      const talentsHTML = ['telepathy','clairvoyance','telekinesis','awareness','teleportation'].map(id => {
        const trained = trainedTalents.includes(id);
        const label = id.charAt(0).toUpperCase() + id.slice(1);
        return `<button class="btn ${trained ? 'ghost' : ''}" data-pc-psi-talent="${id}" ${trained ? 'disabled' : ''}>${trained ? '✓ ' : ''}${label}${trained ? '' : ' — free'}</button>`;
      }).join('');
      return `
        <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
        <div class="stage-content">
          <div class="phase-label">Enrolled · ${trackName}</div>
          <h2 class="phase-title">Psionic Training</h2>
          <p class="phase-body">Your community will train you at no cost. Train one or more talents, then graduate.</p>
          <div class="psi-talents">${talentsHTML}</div>
          <div class="phase-actions" style="margin-top:1rem">
            <button class="btn primary" id="btn-pc-graduate">ROLL GRADUATION</button>
          </div>
        </div>
      `;
    }

    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Enrolled · ${trackName}</div>
        <h2 class="phase-title">Time to Graduate</h2>
        <p class="phase-subtitle">${gradHint}</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-pc-graduate">ROLL GRADUATION</button>
        </div>
      </div>
    `;
  }

  // Track chosen but not yet qualified — show academy service picker if needed
  if (stage === 'choosing_service' && status.track === 'military_academy') {
    const cards = PRE_CAREER_SERVICES.map(s => `
      <button class="card" data-pc-service="${s.id}">
        <div class="card-title">${s.name}</div>
        <div class="card-desc">${s.desc}</div>
      </button>
    `).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Military Academy · Pick a Service</div>
        <h2 class="phase-title">Which Branch?</h2>
        <p class="phase-body">The academy you qualify into commits you to that service career. Commission on graduation means starting at Rank 1 instead of basic training.</p>
        <div class="card-grid">${cards}</div>
        <div class="phase-actions">
          <button class="btn" id="btn-pc-back-to-choose">← BACK</button>
        </div>
      </div>
    `;
  }

  // Merchant Academy: curriculum selection
  if (stage === 'choosing_curriculum' && status.track === 'merchant_academy') {
    const curricula = [
      { id: 'business', name: 'Business', desc: 'Commerce, brokerage, and trade. Enroll in the Broker skill table. Enter Merchant or Citizen at officer rank.' },
      { id: 'shipboard', name: 'Shipboard', desc: 'Freight hauling and ship operations. Enroll in the Merchant Marine skill table. Enter Merchant at officer rank.' },
    ];
    const cards = curricula.map(c => `
      <button class="card" data-pc-curriculum="${c.id}">
        <div class="card-title">${c.name}</div>
        <div class="card-desc">${c.desc}</div>
      </button>
    `).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Merchant Academy · Pick a Curriculum</div>
        <h2 class="phase-title">Which Programme?</h2>
        <p class="phase-body">INT 9+ to qualify (DM+1 if SOC 8+). 4 years. Graduate for +1 EDU and permanent advancement bonus in Merchant or Citizen.</p>
        <div class="card-grid">${cards}</div>
        <div class="phase-actions">
          <button class="btn" id="btn-pc-back-to-choose">← BACK</button>
        </div>
      </div>
    `;
  }

  // Default: pick a track
  const hwUwp = character.homeworld_uwp || '';
  const hwTL = hwUwp.includes('-') ? parseInt(hwUwp.split('-').pop(), 16) : 99;
  const hwSize = hwUwp.length >= 2 ? parseInt(hwUwp[1], 16) : -1;
  const soc = character.characteristics?.SOC ?? 0;
  const canColonial = hwTL <= 8;
  const canSpacer = hwSize === 0;
  const canHardKnocks = soc <= 6;

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
    <div class="stage-content">
      <div class="phase-label">Optional · Age ${character.age}</div>
      <h2 class="phase-title">Education Before Service?</h2>
      <p class="phase-subtitle">Before picking a career, you can spend a few years in education. Or skip and go straight to the job.</p>

      <div class="card-grid">
        <button class="card" id="btn-pc-university">
          <div class="card-title">University</div>
          <div class="card-desc">INT 6+ to qualify, 4 years, +1 EDU on enrollment. Graduate for +2 EDU and 2 skills at level 1. Honours at 10+ adds SOC +1 and DM+1 to your first career qualification.</div>
        </button>
        <button class="card" id="btn-pc-academy">
          <div class="card-title">Military Academy</div>
          <div class="card-desc">3 years. Qualification varies by service. Pass graduation to roll Commission 8+ with DM+2 — success starts you at officer rank. Graduated with Honours means automatic Rank 1 commission.</div>
        </button>
        <button class="card" id="btn-pc-merchant-academy">
          <div class="card-title">Merchant Academy</div>
          <div class="card-desc">INT 9+ to qualify, 4 years. Choose Business or Shipboard curriculum. Graduate for +1 EDU and start Merchant/Citizen at officer rank with a permanent advancement bonus.</div>
        </button>
        <button class="card${canColonial ? '' : ' card-disabled'}" id="btn-pc-colonial"${canColonial ? '' : ' disabled'}>
          <div class="card-title">Colonial Upbringing</div>
          <div class="card-desc">${canColonial
            ? `Homeworld TL ${hwTL} ≤ 8 — automatic. Broad survival skills (Survival 1 + 10 skills at 0). Graduate for END+1, JoaT 1, but EDU−D3 and permanent qualification penalties.`
            : `Requires homeworld TL 8 or less (your homeworld is TL ${hwTL === 99 ? 'unknown' : hwTL}).`
          }</div>
        </button>
        <button class="card${canHardKnocks ? '' : ' card-disabled'}" id="btn-pc-hard-knocks"${canHardKnocks ? '' : ' disabled'}>
          <div class="card-title">School of Hard Knocks</div>
          <div class="card-desc">${canHardKnocks
            ? `SOC ${soc} ≤ 6 — automatic. Street smarts: Streetwise 1 + 2 skill picks. Graduate for Gun Combat 0 and 3 more skills, but DM−2 commission in first career.`
            : `Requires SOC 6 or less (your SOC is ${soc}).`
          }</div>
        </button>
        <button class="card${canSpacer ? '' : ' card-disabled'}" id="btn-pc-spacer"${canSpacer ? '' : ' disabled'}>
          <div class="card-title">Spacer Community</div>
          <div class="card-desc">${canSpacer
            ? `Homeworld size 0 — automatic, INT 4+. 3 years. Vacc Suit 1 + 2 picks. Graduate for DEX+1, Pilot 0, and DM+1 to Merchant (Free Trader) advancement.`
            : `Requires a homeworld of size 0 (asteroid belt). Your homeworld size is ${hwSize === 99 ? 'unknown' : hwSize}.`
          }</div>
        </button>
        <button class="card" id="btn-pc-psionic">
          <div class="card-title">Psionic Community</div>
          <div class="card-desc">Tests PSI (if untested). Requires PSI 8+. 3 years. Psionic talent training during enrollment. Graduate for PSI+1 and permanent Psion career auto-entry.</div>
        </button>
        <button class="card" id="btn-pc-skip">
          <div class="card-title">Skip</div>
          <div class="card-desc">Age ${character.age} and hungry for a paycheck. Go straight to the career phase.</div>
        </button>
      </div>
    </div>
  `;
}

// Helper: human-readable track name from status
function trackDisplayName(track, service, status) {
  if (track === 'university') return 'University';
  if (track === 'military_academy') {
    return PRE_CAREER_SERVICES.find(s => s.id === service)?.name || 'Military Academy';
  }
  if (track === 'merchant_academy') {
    const curr = status?.curriculum_name || status?.curriculum || '';
    return curr ? `Merchant Academy (${curr})` : 'Merchant Academy';
  }
  const TRACK_NAMES = {
    colonial_upbringing: 'Colonial Upbringing',
    psionic_community: 'Psionic Community',
    school_of_hard_knocks: 'School of Hard Knocks',
    spacer_community: 'Spacer Community',
  };
  return TRACK_NAMES[track] || track;
}

// Helper: graduation hint text for enrolled view
function trackGradHint(track) {
  const HINTS = {
    university: 'Roll EDU 7+ to graduate (10+ for Honours). Then one education event.',
    military_academy: 'Roll INT 8+ to graduate (11+ for Honours). Then one education event.',
    merchant_academy: 'Roll INT 7+ to graduate (11+ for Honours). Then one education event.',
    colonial_upbringing: 'Roll INT 8+ to graduate (12+ for Honours, END 8+ gives DM+1). No age cost.',
    psionic_community: 'Roll PSI 6+ to graduate (12+ for Honours, INT 8+ gives DM+1). Then one education event.',
    school_of_hard_knocks: 'Roll INT 7+ to graduate (11+ for Honours, END 9+ gives DM+1). Then one education event.',
    spacer_community: 'Roll INT 8+ to graduate (12+ for Honours, DEX 6+ gives DM+1). Then one education event.',
  };
  return HINTS[track] || 'Roll for graduation — hit the honours target for even more.';
}

function wirePreCareerPhase() {
  // Helper: fire a simple pre-career qualify call and set lastRoll
  async function fireQualify(track, extraParams, trackName, charLabel, target, ageCost) {
    try {
      const response = await apiCall('/api/character/pre-career/qualify',
        { track, ...extraParams });
      await applyResponse(response);
      if (response.choosing_curriculum) { renderStage(); return; }
      // Automatic tracks (colonial, hard knocks) may not have a roll
      const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
      uiState.lastRoll = {
        type: hasPicks ? 'precareer_skill_pick' : 'precareer_qualify',
        data: response.roll || null,
        passed: response.passed ?? true,
        trackName,
        charLabel,
        target,
        ageCost: ageCost || 0,
        enrollmentApplied: response.enrollment_applied || [],
        // for automatic tracks that jump straight to skill picker
        psi: response.psi,
        psi_roll: response.psi_roll,
      };
      if (hasPicks) uiState.selectedPreCareerSkills = new Set();
      renderAll();
    } catch (e) { alert(e.message); }
  }

  // Main choice
  const uni = document.getElementById('btn-pc-university');
  if (uni) uni.addEventListener('click', () =>
    fireQualify('university', {}, 'University', 'INT', 6, 4)
  );

  const academy = document.getElementById('btn-pc-academy');
  if (academy) academy.addEventListener('click', () => {
    character.pre_career_status = {
      ...(character.pre_career_status || {}),
      track: 'military_academy',
      stage: 'choosing_service',
    };
    saveCharacter();
    renderStage();
  });

  const merchantAcademy = document.getElementById('btn-pc-merchant-academy');
  if (merchantAcademy) merchantAcademy.addEventListener('click', () => {
    character.pre_career_status = {
      ...(character.pre_career_status || {}),
      track: 'merchant_academy',
      stage: 'choosing_curriculum',
    };
    saveCharacter();
    renderStage();
  });

  const colonial = document.getElementById('btn-pc-colonial');
  if (colonial) colonial.addEventListener('click', () =>
    fireQualify('colonial_upbringing', {}, 'Colonial Upbringing', 'Auto', null, 0)
  );

  const hardKnocks = document.getElementById('btn-pc-hard-knocks');
  if (hardKnocks) hardKnocks.addEventListener('click', () =>
    fireQualify('school_of_hard_knocks', {}, 'School of Hard Knocks', 'Auto', null, 2)
  );

  const spacer = document.getElementById('btn-pc-spacer');
  if (spacer) spacer.addEventListener('click', () =>
    fireQualify('spacer_community', {}, 'Spacer Community', 'INT', 4, 3)
  );

  const psionic = document.getElementById('btn-pc-psionic');
  if (psionic) psionic.addEventListener('click', () =>
    fireQualify('psionic_community', {}, 'Psionic Community', 'PSI', 8, 3)
  );

  const skip = document.getElementById('btn-pc-skip');
  if (skip) skip.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/skip');
      await applyResponse(response);
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Military Academy service picker
  document.querySelectorAll('[data-pc-service]').forEach(card => {
    card.addEventListener('click', async () => {
      const service = card.dataset.pcService;
      const svc = PRE_CAREER_SERVICES.find(s => s.id === service);
      const charLabel = service === 'navy' ? 'INT' : 'END';
      const target = service === 'army' ? 8 : 9;
      try {
        const response = await apiCall('/api/character/pre-career/qualify',
          { track: 'military_academy', service });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'precareer_qualify',
          data: response.roll,
          passed: response.passed,
          trackName: svc?.name || 'Military Academy',
          charLabel,
          target,
          ageCost: 3,
          enrollmentApplied: response.enrollment_applied || [],
        };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  // Merchant Academy curriculum picker
  document.querySelectorAll('[data-pc-curriculum]').forEach(card => {
    card.addEventListener('click', async () => {
      const curriculum = card.dataset.pcCurriculum;
      try {
        const response = await apiCall('/api/character/pre-career/qualify',
          { track: 'merchant_academy', curriculum });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'precareer_qualify',
          data: response.roll,
          passed: response.passed,
          trackName: `Merchant Academy (${curriculum})`,
          charLabel: 'INT',
          target: 9,
          ageCost: 4,
          enrollmentApplied: response.enrollment_applied || [],
        };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  const backToChoose = document.getElementById('btn-pc-back-to-choose');
  if (backToChoose) backToChoose.addEventListener('click', () => {
    character.pre_career_status = {
      ...(character.pre_career_status || {}),
      track: null,
      stage: 'none',
    };
    saveCharacter();
    renderStage();
  });

  // Post-qualify continue button
  const postQualify = document.getElementById('btn-post-precareer-qualify');
  if (postQualify) postQualify.addEventListener('click', () => {
    const passed = uiState.lastRoll?.passed;
    if (passed) {
      // University enrollment: player picks 2 skills at level 0 before events
      const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
      if (hasPicks) {
        uiState.selectedPreCareerSkills = new Set();
        uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_skill_pick' };
        renderStage();
      } else {
        // Military academy or no enrollment picks — go straight to enrolled view
        uiState.lastRoll = null;
        renderStage();
      }
    } else {
      // Engine already set phase=career on failed qualification
      uiState.lastRoll = null;
      renderAll();
    }
  });

  // Graduation roll button — also auto-rolls the education event server-side
  const gradBtn = document.getElementById('btn-pc-graduate');
  if (gradBtn) gradBtn.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/graduate', { chosen_skills: [] });
      await applyResponse(response);
      const st = character.pre_career_status || {};
      const track = st.track;
      const service = st.service;
      const trackName = trackDisplayName(track, service, st);
      // Prefer server-supplied char_key/target (works for all tracks including PSI)
      const charLabel = response.char_key || (track === 'university' ? 'EDU' : 'INT');
      const target = response.target || (track === 'university' ? 7 : 8);
      uiState.selectedPreCareerSkills = new Set();
      uiState.lastRoll = {
        type: 'precareer_graduate',
        data: response.roll,
        outcome: response.outcome,
        applied: response.applied || [],
        event: response.event || null,
        trackName,
        charLabel,
        target,
      };
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Psionic community enrollment: free talent training buttons
  document.querySelectorAll('[data-pc-psi-talent]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const talent = btn.dataset.pcPsiTalent;
      try {
        const response = await apiCall('/api/character/psionics/train', { talent_id: talent });
        await applyResponse(response);
      } catch (e) { alert(e.message); }
      renderAll();
    });
  });

  // Event 9: show any-skill picker
  const showAnySkillBtn = document.getElementById('btn-show-any-skill-pick');
  if (showAnySkillBtn) showAnySkillBtn.addEventListener('click', () => {
    uiState.anySkillFilter = '';
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_any_skill_pick' };
    renderStage();
  });

  // Injury choice: navigate to injury stat picker
  const showInjuryBtn = document.getElementById('btn-show-injury-choice');
  if (showInjuryBtn) showInjuryBtn.addEventListener('click', () => {
    const inj = character.pending_injury_choice || uiState.lastRoll?.injury_pending_data;
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_injury_choice', injuryData: inj };
    renderStage();
  });

  // Injury stat buttons
  ['STR', 'DEX', 'END'].forEach(stat => {
    const btn = document.getElementById(`btn-injury-stat-${stat}`);
    if (btn) btn.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/injury-choice', { chosen_stat: stat });
        await applyResponse(response);
        const billsMsg = formatMedicalBillsMsg(response);
        if (billsMsg) alert(billsMsg);
        // After injury, check if life event choice is still pending
        const lr = uiState.lastRoll;
        if (character.pending_life_event_choice) {
          uiState.lastRoll = { ...lr, type: 'precareer_graduate', pending_injury: false };
        } else {
          const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
          uiState.lastRoll = hasPicks
            ? { ...lr, type: 'precareer_skill_pick' }
            : { ...lr, type: 'precareer_graduate', pending_injury: false };
        }
        renderStage();
      } catch (e) { alert(e.message); }
    });
  });

  // Life event choice: navigate to choice screen
  const showLifeEventBtn = document.getElementById('btn-show-life-event-choice');
  if (showLifeEventBtn) showLifeEventBtn.addEventListener('click', () => {
    const kind = character.pending_life_event_choice?.kind || uiState.lastRoll?.life_event_choice_kind;
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_life_event_choice', choiceKind: kind };
    renderStage();
  });

  // Life event choice buttons (rival / enemy / lose_benefit / prisoner)
  document.querySelectorAll('[id^="btn-life-choice-"]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const choice = btn.id.replace('btn-life-choice-', '');
      try {
        const response = await apiCall('/api/character/life-event-choice', { choice });
        await applyResponse(response);
        // After resolving, check if we can continue or need skill picks
        const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
        uiState.lastRoll = hasPicks
          ? { ...uiState.lastRoll, type: 'precareer_skill_pick', pending_life_event: false }
          : { ...uiState.lastRoll, type: 'precareer_graduate', event: { ...uiState.lastRoll?.event, pending_life_event: false } };
        renderStage();
      } catch (e) { alert(e.message); }
    });
  });

  // Event 10: show tutor challenge picker
  const showEvent10Btn = document.getElementById('btn-show-event10');
  if (showEvent10Btn) showEvent10Btn.addEventListener('click', () => {
    uiState.event10Filter = '';
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_event10' };
    renderStage();
  });

  // Event 10 search filter
  const event10Search = document.getElementById('event10-skill-search');
  if (event10Search) {
    event10Search.focus();
    event10Search.addEventListener('input', () => {
      uiState.event10Filter = event10Search.value;
      renderStage();
    });
  }

  // Event 10 skill chip click — roll 2D 9+ and resolve
  document.querySelectorAll('[data-event10-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const skill = chip.dataset.event10Skill;
      try {
        const response = await apiCall('/api/character/pre-career/event10-skill', { skill_text: skill });
        await applyResponse(response);
        const succeeded = response.roll?.succeeded;
        const msg = succeeded
          ? `Tutor challenge on ${skill}: SUCCESS! Gained +1 level and Rival [Tutor].`
          : `Tutor challenge on ${skill}: failed. No bonus.`;
        alert(msg);
        uiState.event10Filter = '';
        uiState.lastRoll = null;
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  // Event 11: show draft event screen
  const showEvent11Btn = document.getElementById('btn-show-event11');
  if (showEvent11Btn) showEvent11Btn.addEventListener('click', () => {
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_event11' };
    renderStage();
  });

  // Event 11 choice buttons
  const ev11Drifter = document.getElementById('btn-event11-drifter');
  if (ev11Drifter) ev11Drifter.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/event11-choice', { choice: 'drifter' });
      await applyResponse(response);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  const ev11Draft = document.getElementById('btn-event11-draft');
  if (ev11Draft) ev11Draft.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/event11-choice', { choice: 'draft' });
      await applyResponse(response);
      const career = response.draft_career || 'unknown';
      const d6 = response.roll?.dice?.[0] ?? '?';
      alert(`Drafted! D6=${d6} — you must enter the ${career.toUpperCase()} career.`);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  const ev11Dodge = document.getElementById('btn-event11-dodge');
  if (ev11Dodge) ev11Dodge.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/event11-choice', { choice: 'dodge' });
      await applyResponse(response);
      const roll = response.roll;
      const succeeded = roll?.succeeded;
      const msg = succeeded
        ? `Draft dodged! (SOC check: ${roll.total} vs 9+). Graduation stands.`
        : `Draft dodge failed (SOC check: ${roll.total} vs 9+). Did not graduate.`;
      alert(msg);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Any-skill search filter
  const anySkillSearch = document.getElementById('any-skill-search');
  if (anySkillSearch) {
    anySkillSearch.focus();
    anySkillSearch.addEventListener('input', () => {
      uiState.anySkillFilter = anySkillSearch.value;
      renderStage();
    });
  }

  // Any-skill chip click — apply and advance
  document.querySelectorAll('[data-any-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const skill = chip.dataset.anySkill;
      try {
        const response = await apiCall('/api/character/pre-career/any-skill', { skill_text: skill });
        await applyResponse(response);
        const lr = uiState.lastRoll;
        const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
        uiState.anySkillFilter = '';
        if (hasPicks) {
          uiState.selectedPreCareerSkills = new Set();
          uiState.lastRoll = { ...lr, type: 'precareer_skill_pick', pending_any_skill: false };
        } else {
          uiState.lastRoll = { ...lr, type: 'precareer_graduate', event: { ...lr.event, pending_any_skill: false } };
        }
        renderStage();
      } catch (e) { alert(e.message); }
    });
  });

  // Transition from graduation result screen to skill picker screen
  const startPickBtn = document.getElementById('btn-start-skill-pick');
  if (startPickBtn) startPickBtn.addEventListener('click', () => {
    uiState.selectedPreCareerSkills = new Set();
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_skill_pick' };
    renderStage();
  });

  // Skill picker chips
  document.querySelectorAll('[data-pc-skill]').forEach(chip => {
    chip.addEventListener('click', () => {
      const skill = chip.dataset.pcSkill;
      if (!uiState.selectedPreCareerSkills) uiState.selectedPreCareerSkills = new Set();
      if (uiState.selectedPreCareerSkills.has(skill)) {
        uiState.selectedPreCareerSkills.delete(skill);
      } else {
        uiState.selectedPreCareerSkills.add(skill);
      }
      renderStage();
    });
  });

  // Confirm skill picks
  const confirmPc = document.getElementById('btn-confirm-pc-skills');
  if (confirmPc) confirmPc.addEventListener('click', async () => {
    const chosen = Array.from(uiState.selectedPreCareerSkills || []);
    if (chosen.length === 0) return;
    try {
      const response = await apiCall('/api/character/pre-career/choose-skills',
        { chosen_skills: chosen });
      await applyResponse(response);
      uiState.selectedPreCareerSkills = new Set();
      if (response.skill_pick_stage === 'enrollment' && response.skill_picks_remaining === 0) {
        // Enrollment picks done: stay in pre_career for events/graduation
        uiState.lastRoll = null;
        renderStage();
      } else if (response.has_more_rounds || response.new_picks_remaining > 0) {
        // Next round queued — stay in skill pick screen with updated pool/level
        uiState.lastRoll = { ...(uiState.lastRoll || {}), type: 'precareer_skill_pick' };
        renderStage();
      } else {
        // All done — phase is 'career'
        uiState.lastRoll = null;
        renderAll();
      }
    } catch (e) { alert(e.message); }
  });

  // Post-graduate continue — advance phase client-side (server stays in pre_career to show the page)
  const postGrad = document.getElementById('btn-post-precareer-graduate');
  if (postGrad) postGrad.addEventListener('click', () => {
    character.phase = 'career';
    saveCharacter();
    uiState.lastRoll = null;
    renderAll();
  });

  // Post-qualify continue — clear lastRoll and route by phase
  // (already handled above by btn-post-precareer-qualify, kept for clarity)
}

// ============================================================
// PHASE 4: Career Loop
// ============================================================

function renderCareerPhase() {
  const term = character.current_term;

  // After clicking a career card we POST /api/character/qualify, which
  // returns a roll result but does NOT create a current_term (the term
  // only starts once the user picks an assignment and hits BEGIN TERM).
  // So between those two clicks we have: term === null, subPhase === 'qualify'.
  // Route that state to renderQualifyResult so the dice + assignment
  // picker actually render.
  if (!term && uiState.subPhase === 'qualify' && uiState.lastRoll) {
    return renderQualifyResult();
  }
  if (term && uiState.subPhase === 'draft_result' && uiState.lastRoll?.type === 'draft') {
    return renderDraftResult();
  }

  // Otherwise: no term means choose-a-career; term means active term loop.
  if (!term) {
    return renderChooseCareer();
  }
  return renderActiveTerm();
}

function renderChooseCareer() {
  const forcedId = character.forced_next_career_id || null;
  const banned = new Set(character.banned_career_ids || []);
  const soc = character.society_id || 'third_imperium';
  const careerList = forcedId
    ? CAREERS.filter(c => c.id === forcedId)
    : CAREERS.filter(c => {
        if (banned.has(c.id)) return false;
        // "societies" = whitelist: only show for these societies
        if (c.societies && c.societies.length > 0 && !c.societies.includes(soc)) return false;
        // "blocked_societies" = blacklist: hide for these societies
        if (c.blocked_societies && c.blocked_societies.includes(soc)) return false;
        return true;
      });
  const forcedBanner = forcedId ? `
    <p class="phase-body" style="color:var(--danger);font-weight:bold">
      ⚠ You must enter the ${forcedId.toUpperCase()} career this term (education event mandate).
    </p>` : '';
  const bannedBanner = banned.size && !forcedId ? `
    <p class="phase-body" style="color:var(--amber-dim);font-size:11px">
      Banned from re-entry: ${[...banned].map(id => id.toUpperCase()).join(', ')}
    </p>` : '';

  const cards = careerList.map(c => {
    const isComplete = c.complete;
    const qual = c.qualification || {};
    let qualText;
    if (qual.automatic) {
      qualText = 'AUTO';
    } else if (qual.characteristic === 'DEX_OR_INT') {
      qualText = `DEX or INT ${qual.target}+`;
    } else {
      qualText = `${qual.characteristic} ${qual.target}+`;
    }
    const classes = ['card'];
    if (!isComplete) classes.push('partial');
    return `
      <button class="${classes.join(' ')}" data-career="${c.id}">
        <div class="card-title">${c.name}</div>
        <div class="card-meta">${qualText}${qual.auto_qualify_if?.SOC ? ` · AUTO@SOC≥${qual.auto_qualify_if.SOC.replace('>=','')}` : ''}</div>
        <div class="card-desc">${c.description}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 04 — CAREER SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Term ${character.total_terms + 1} · Age ${character.age}</div>
      <h2 class="phase-title">Choose a Career</h2>
      ${forcedBanner}
      ${bannedBanner}
      <p class="phase-subtitle">${character.total_terms === 0
        ? 'Your first career defines the first four years of your adult life.'
        : 'You survived. Another four years await — continue, or try something new.'}</p>

      <div class="card-grid">${cards}</div>

      <p class="empty" style="font-size:11px;margin-top:8px">
        Careers marked <strong style="color:var(--amber-dim)">PARTIAL</strong> have basic qualification/survival/advancement rules
        encoded, but events/mishaps/skill tables are not yet filled in. See the README for how to complete them.
      </p>

      ${character.total_terms > 0 ? `
        <div class="phase-actions">
          <button class="btn" id="btn-finish-creation">FINISH CHARACTER CREATION →</button>
        </div>
      ` : ''}
    </div>
  `;
}

function wireCareerPhase() {
  // Choose career view
  document.querySelectorAll('[data-career]').forEach(card => {
    card.addEventListener('click', async () => {
      const careerId = card.dataset.career;
      uiState.selectedCareer = careerId;
      uiState.selectedAssignment = null;
      uiState.subPhase = 'qualify';
      // Consume forced_next_career_id so it doesn't restrict future terms.
      if (character.forced_next_career_id) {
        character.forced_next_career_id = null;
        saveCharacter();
      }
      const response = await apiCall('/api/character/qualify', { career_id: careerId });
      await applyResponse(response);
      uiState.lastRoll = response;
      renderAll();
    });
  });

  const finishBtn = document.getElementById('btn-finish-creation');
  if (finishBtn) {
    finishBtn.addEventListener('click', () => {
      character.phase = 'mustering';
      saveCharacter();
      renderAll();
    });
  }

  // Failed-qualification fallback options
  const btnDraft = document.getElementById('btn-accept-draft');
  if (btnDraft) {
    btnDraft.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/draft');
        await applyResponse(response);
        uiState.selectedCareer = response.career_id;
        uiState.selectedAssignment = response.assignment_id;
        uiState.subPhase = 'draft_result';
        uiState.lastRoll = {
          type: 'draft',
          roll: response.roll,
          career_name: response.career_name,
          assignment_name: response.assignment_name,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }

  const btnDrifter = document.getElementById('btn-drifter-auto');
  if (btnDrifter) {
    btnDrifter.addEventListener('click', async () => {
      uiState.selectedCareer = 'drifter';
      uiState.selectedAssignment = null;
      uiState.subPhase = 'qualify';
      const response = await apiCall('/api/character/qualify', { career_id: 'drifter' });
      await applyResponse(response);
      uiState.lastRoll = response;
      renderAll();
    });
  }

  const btnBeginDrafted = document.getElementById('btn-begin-drafted-term');
  if (btnBeginDrafted) {
    btnBeginDrafted.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'train';
      renderAll();
    });
  }

  // Active term view
  const btnAssign = document.getElementById('btn-start-term');
  if (btnAssign) {
    btnAssign.addEventListener('click', async () => {
      if (!uiState.selectedAssignment) return;
      const body = {
        career_id: uiState.selectedCareer,
        assignment_id: uiState.selectedAssignment,
      };
      // SolSec Secret Agent: pass the chosen cover career
      if (uiState.selectedCoverCareer) {
        body.cover_career_id = uiState.selectedCoverCareer;
      }
      const response = await apiCall('/api/character/start-term', body);
      await applyResponse(response);
      if (response.academy_commission_roll) {
        uiState.academyCommissionRoll = response.academy_commission_roll;
      }
      if (response.basic_training_skills) {
        uiState.basicTrainingSkills = response.basic_training_skills;
      }
      uiState.selectedCoverCareer = null;  // consumed
      uiState.subPhase = 'train';
      renderAll();
    });
  }

  document.querySelectorAll('[data-assignment]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedAssignment = card.dataset.assignment;
      // Reset cover career when switching assignments
      if (!(uiState.selectedCareer === 'solsec' && uiState.selectedAssignment === 'secret_agent')) {
        uiState.selectedCoverCareer = null;
      }
      renderStage();
    });
  });

  // SolSec Secret Agent: cover career picker
  document.querySelectorAll('[data-cover-career]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedCoverCareer = card.dataset.coverCareer;
      renderStage();
    });
  });

  // Home Forces Reserves: enroll / leave
  const btnHfEnroll = document.getElementById('btn-hf-enroll');
  if (btnHfEnroll) {
    btnHfEnroll.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/home-forces', { action: 'enroll' });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'home_forces_training',
          roll: response.training_roll,
          result: response.training_result,
          component: response.component,
          auto_skill: response.auto_skill,
          rank_transferred: response.rank_transferred,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnHfLeave = document.getElementById('btn-hf-leave');
  if (btnHfLeave) {
    btnHfLeave.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/home-forces', { action: 'leave' });
        await applyResponse(response);
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }

  // Home Forces training banner dismiss
  const btnHfDismiss = document.getElementById('btn-hf-training-dismiss');
  if (btnHfDismiss) {
    btnHfDismiss.addEventListener('click', () => {
      uiState.lastRoll = null;
      renderStage();
    });
  }

  // SolSec Monitor: join / leave
  const btnMonitorJoin = document.getElementById('btn-monitor-join');
  if (btnMonitorJoin) {
    btnMonitorJoin.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/solsec-monitor', { active: true });
        await applyResponse(response);
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnMonitorLeave = document.getElementById('btn-monitor-leave');
  if (btnMonitorLeave) {
    btnMonitorLeave.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/solsec-monitor', { active: false });
        await applyResponse(response);
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }

  document.querySelectorAll('[data-skill-table]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tableKey = btn.dataset.skillTable;
      try {
        const response = await apiCall('/api/character/skill-roll', { table_key: tableKey });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'skill',
          data: response.roll,
          tableName: (CAREERS.find(c => c.id === character.current_term.career_id)
                        ?.skill_tables?.[tableKey]?.name) || tableKey,
          result: response.result,
          applied: response.applied,
        };
        // Stay on 'train' subPhase so the user sees the 1D result
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  });

  const btnPostSkill = document.getElementById('btn-post-skill');
  if (btnPostSkill) {
    btnPostSkill.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'survive';
      renderStage();
    });
  }

  const btnBasicTrainingContinue = document.getElementById('btn-basic-training-continue');
  if (btnBasicTrainingContinue) {
    btnBasicTrainingContinue.addEventListener('click', () => {
      uiState.basicTrainingSkills = null;
      uiState.subPhase = 'survive';
      renderStage();
    });
  }

  const btnSurvive = document.getElementById('btn-survive');
  if (btnSurvive) {
    btnSurvive.addEventListener('click', async () => {
      const response = await apiCall('/api/character/survive');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'survive',
        data: response.roll,
        outcome: response.survived ? 'pass' : 'fail',
        parallel_event: response.parallel_event || null,
      };
      // Stay on 'survive' subPhase so dice readout renders before advancing
      renderAll();
    });
  }

  const btnPostSurvive = document.getElementById('btn-post-survive');
  if (btnPostSurvive) {
    btnPostSurvive.addEventListener('click', () => {
      const outcome = uiState.lastRoll?.outcome;
      uiState.lastRoll = null;
      uiState.subPhase = outcome === 'pass' ? 'event' : 'mishap';
      renderStage();
    });
  }

  const btnEvent = document.getElementById('btn-event');
  if (btnEvent) {
    btnEvent.addEventListener('click', async () => {
      const response = await apiCall('/api/character/event');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'event',
        data: response.roll,
        eventText: response.event,
        dmGrants: response.dm_grants || [],
        statBonuses: response.stat_bonuses || [],
        autoPromotion: response.auto_promotion || null,
        associateOpsDone: [],
      };

      // Auto-add unambiguous single Ally grants without requiring the picker.
      // "Allies should always be added to the associates" — only skip if
      // quantity ops are present (D3 Allies etc.) since those need a die roll
      // to determine count.
      const rawAssocOpsForEvent = parseEventAssociateOps(response.event || '');
      const hasQuantityOps = rawAssocOpsForEvent.some(op => op.type === 'quantity');
      if (!hasQuantityOps) {
        for (let rawIdx = 0; rawIdx < rawAssocOpsForEvent.length; rawIdx++) {
          const op = rawAssocOpsForEvent[rawIdx];
          if (op.type === 'add' && op.kinds.length === 1 && op.kinds[0] === 'ally') {
            try {
              const allyResp = await apiCall('/api/character/associate', { op: 'add', kind: 'ally', description: '' });
              await applyResponse(allyResp);
              const done = uiState.lastRoll.associateOpsDone;
              while (done.length <= rawIdx) done.push(null);
              done[rawIdx] = 'Ally auto-added to Associates';
            } catch (_e) { /* silently ignore — ally was at least flagged */ }
          }
        }
      }

      // Stay on 'event' so the dice + event text render together
      renderAll();
    });
  }

  const btnPostEvent = document.getElementById('btn-post-event');
  if (btnPostEvent) {
    btnPostEvent.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'advance';
      renderStage();
    });
  }

  // Prisoner event 7 parole — leave career immediately on success.
  const btnParole = document.getElementById('btn-prisoner-parole');
  if (btnParole) {
    btnParole.addEventListener('click', async () => {
      const endResp = await apiCall('/api/character/end-term', { leaving: true, reason: 'parole' });
      await applyResponse(endResp);
      uiState.lastRoll = null;
      uiState.subPhase = null;
      uiState.selectedCareer = null;
      uiState.selectedAssignment = null;
      renderAll();
    });
  }

  // Citizen event 8 — retroactive survival failure → trigger mishap flow.
  const btnCitizenEv8Mishap = document.getElementById('btn-citizen-ev8-mishap');
  if (btnCitizenEv8Mishap) {
    btnCitizenEv8Mishap.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'mishap';
      renderAll();
    });
  }

  // "Roll on the Mishap Table" event (non-ejecting disaster): roll the mishap
  // inline and display the result right inside the event panel.
  const btnForcedMishap = document.getElementById('btn-event-forced-mishap');
  if (btnForcedMishap) {
    btnForcedMishap.addEventListener('click', async () => {
      btnForcedMishap.disabled = true;
      try {
        const response = await apiCall('/api/character/mishap');
        await applyResponse(response);
        if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
          uiState.lastRoll.mishapFromEvent = {
            total: response.roll?.total,
            text: response.mishap,
          };
        }
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not roll the mishap table.');
        btnForcedMishap.disabled = false;
      }
    });
  }

  // Event-choice skill picker: clicking a chip applies the chosen skill.
  const disableAllEventChips = () => {
    document.querySelectorAll('[data-event-skill],[data-event-dm],[data-event-transfer]').forEach(c => { c.disabled = true; });
  };
  const enableAllEventChips = () => {
    document.querySelectorAll('[data-event-skill],[data-event-dm],[data-event-transfer]').forEach(c => { c.disabled = false; });
  };
  document.querySelectorAll('[data-event-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const pick = chip.getAttribute('data-event-skill');
      try {
        disableAllEventChips();
        const response = await apiCall('/api/character/event-skill-grant', { skill_text: pick });
        await applyResponse(response);
        if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
          uiState.lastRoll.eventSkillApplied = response.skill || pick;
          uiState.lastRoll.eventChoicePath = 'skill';
        }
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not apply that skill.');
        enableAllEventChips();
      }
    });
  });

  // Event-choice DM alternative: "Take DM+N to next Advancement roll instead."
  document.querySelectorAll('[data-event-dm]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const dm = parseInt(chip.getAttribute('data-event-dm'), 10);
      const target = chip.getAttribute('data-event-dm-target');
      try {
        disableAllEventChips();
        const response = await apiCall('/api/character/event-dm-grant', { dm, target });
        await applyResponse(response);
        if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
          uiState.lastRoll.eventDmApplied = { dm: response.dm ?? dm, target: response.target ?? target };
          uiState.lastRoll.eventChoicePath = 'dm';
        }
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not apply that DM grant.');
        enableAllEventChips();
      }
    });
  });

  // Event-choice career-transfer offer: "transfer to the Marines without a
  // Qualification roll." Sets pending_transfer_career_id on the character.
  document.querySelectorAll('[data-event-transfer]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const careerId = chip.getAttribute('data-event-transfer');
      try {
        disableAllEventChips();
        const response = await apiCall('/api/character/event-transfer-offer', { target_career_id: careerId });
        await applyResponse(response);
        if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
          uiState.lastRoll.eventTransferApplied = response.target_name || careerId;
          uiState.lastRoll.eventChoicePath = 'transfer';
        }
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not accept that transfer.');
        enableAllEventChips();
      }
    });
  });

  // Contested-roll: "Roll <Skill> 8+". On click, roll 2D + skill-level, compare
  // to target, and surface success/fail outcome. If success branch contains a
  // DM+N grant or skill grant, apply it via the existing event-dm-grant /
  // event-skill-grant endpoints.
  document.querySelectorAll('[data-contested-roll]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || lr.type !== 'event') return;
      const parsed = parseEventContestedRoll(lr.eventText || '');
      if (!parsed) return;
      const idx = parseInt(chip.getAttribute('data-contested-roll'), 10);
      const sk = parsed.skills[idx];
      if (!sk) return;
      const mod = getSkillLevelFor(sk.name, sk.speciality);
      const roll = rollD2(mod);
      const success = roll.total >= parsed.target;
      const skillLabel = sk.speciality ? `${sk.name} (${sk.speciality})` : sk.name;
      const branchText = success ? parsed.successText : parsed.failText;

      // Apply any DM+N grants from the resolved branch via the event-dm-grant
      // endpoint (same path used for the "either skill or DM+N" picker).
      const appliedMsgs = [];
      try {
        disableAllEventChips();
        if (branchText) {
          const dmRe = /DM\s*([+-]?\d+)\s+(?:to\s+(?:a|any|your|one|the|next)\s+)?(advancement|benefit|qualification)/gi;
          let m;
          while ((m = dmRe.exec(branchText)) !== null) {
            const dm = parseInt(m[1], 10);
            const target = m[2].toLowerCase();
            try {
              const resp = await apiCall('/api/character/event-dm-grant', { dm, target });
              await applyResponse(resp);
              appliedMsgs.push(`DM${dm >= 0 ? '+' : ''}${dm} to next ${target} roll`);
            } catch (_) { /* ignore */ }
          }
        }
      } catch (_) { /* ignore */ }

      // If the success branch offers a skill pick, store it for the picker UI.
      let pendingSkillPick = null;
      if (success && branchText) {
        const sOpts = parseEventSkillOptions(branchText);
        const sWild = !sOpts ? parseEventWildcardSkill(branchText) : null;
        if ((sOpts && sOpts.length) || sWild) {
          pendingSkillPick = { options: sOpts || null, wildcardSpec: sWild || null };
        }
      }

      if (lr) {
        lr.eventContestedResolved = {
          success, dice: roll.dice, mod: roll.mod, total: roll.total,
          target: parsed.target, skillLabel, branchText, appliedMsgs,
          pendingSkillPick,
        };

        // Citizen event 8: retroactive survival DM-2 check.
        // If DM-2 to survival would have caused a failure, flag it.
        if (!success && /DM-2 to your Survival roll this term/i.test(lr.eventText || '')) {
          const term = character.current_term;
          const career = CAREERS.find(c => c.id === term?.career_id);
          const asgn = career?.assignments?.[term?.assignment_id];
          const survTarget = asgn?.survival?.target ?? 99;
          const survTotal = term?.survival_roll_total ?? null;
          if (survTotal !== null && (survTotal - 2) < survTarget) {
            lr.citizenEv8SurvivalFailed = true;
          }
        }
        if (success && /DM-2 to your Survival roll this term/i.test(lr.eventText || '')) {
          const term = character.current_term;
          const career = CAREERS.find(c => c.id === term?.career_id);
          const asgn = career?.assignments?.[term?.assignment_id];
          const survTarget = asgn?.survival?.target ?? 99;
          const survTotal = term?.survival_roll_total ?? null;
          if (survTotal !== null && (survTotal - 2) < survTarget) {
            lr.citizenEv8SurvivalFailed = true;
          }
        }

        // Scout event 2: on failure, ban Scout from future careers.
        if (!success && /may not re-enlist in the Scouts/i.test(branchText || '')) {
          try {
            const resp = await apiCall('/api/character/ban-career', { career_id: 'scout' });
            await applyResponse(resp);
            lr.scoutBanned = true;
          } catch (_) {}
        }

        // Prisoner event 7: on success, mark parole granted.
        if (success && /you leave at the end of this term/i.test(branchText || '')) {
          lr.prisonerParoleGranted = true;
        }
      }
      renderAll();
    });
  });

  // "Skip — apply manually" for contested roll.
  document.querySelectorAll('[data-contested-skip]').forEach(chip => {
    chip.addEventListener('click', () => {
      const lr = uiState.lastRoll;
      if (!lr || lr.type !== 'event') return;
      lr.eventContestedResolved = {
        success: null, dice: [], mod: 0, total: 0,
        target: 0, skillLabel: 'Skipped', branchText: 'Resolve this check manually.',
        appliedMsgs: [],
      };
      renderAll();
    });
  });

  // Skill picker after a contested roll succeeds (e.g. navy[8], army[8]).
  document.querySelectorAll('[data-contested-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || !lr.eventContestedResolved) return;
      const pick = chip.getAttribute('data-contested-skill');
      try {
        chip.disabled = true;
        document.querySelectorAll('[data-contested-skill]').forEach(c => { c.disabled = true; });
        const resp = await apiCall('/api/character/event-skill-grant', { skill_text: pick });
        await applyResponse(resp);
        lr.eventContestedResolved.skillChosen = resp.skill || pick;
        lr.eventContestedResolved.appliedMsgs = [
          ...(lr.eventContestedResolved.appliedMsgs || []),
          `+ ${resp.skill || pick}`,
        ];
      } catch (err) {
        alert(err.message || 'Could not apply that skill.');
        document.querySelectorAll('[data-contested-skill]').forEach(c => { c.disabled = false; });
      }
      renderAll();
    });
  });
  // Refuse branch for noble[3] / noble[8]. On click, apply the parsed
  // consequence (SOC delta or associate gain) and resolve the contested-
  // roll widget with success=null so the post-resolution view shows only
  // the refusal outcome.
  document.querySelectorAll('[data-event-refuse]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || lr.type !== 'event') return;
      const opt = parseEventRefuseOption(lr.eventText || '');
      if (!opt) return;
      const appliedMsgs = [];
      try {
        disableAllEventChips();
        if (opt.stat && opt.delta) {
          try {
            const resp = await apiCall('/api/character/event-stat-change', {
              stat: opt.stat, delta: opt.delta, reason: 'Refused event challenge',
            });
            await applyResponse(resp);
            const sign = opt.delta >= 0 ? '+' : '';
            appliedMsgs.push(`${opt.stat} ${sign}${opt.delta}`);
          } catch (err) { /* fall through to manual */ }
        } else if (opt.associateKind) {
          try {
            const resp = await apiCall('/api/character/associate', {
              op: 'add', kind: opt.associateKind, description: opt.consequence,
            });
            await applyResponse(resp);
            appliedMsgs.push(`Gained ${opt.associateKind.charAt(0).toUpperCase() + opt.associateKind.slice(1)}`);
          } catch (err) { /* fall through */ }
        }
      } catch (_) { /* ignore */ }
      lr.eventContestedResolved = {
        success: null, dice: [], mod: 0, total: 0,
        target: 0, skillLabel: 'Refused',
        branchText: opt.consequence,
        appliedMsgs,
      };
      renderAll();
    });
  });


  // Agent event 8: cross-career roll on Rogue or Citizen table
  ['rogue', 'citizen'].forEach(careerId => {
    const btn = document.getElementById(`btn-cross-career-${careerId}`);
    if (!btn) return;
    btn.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr) return;
      const succeeded = lr.eventContestedResolved && lr.eventContestedResolved.success;
      const tbl = succeeded ? 'event' : 'mishap';
      btn.disabled = true;
      try {
        const response = await apiCall('/api/character/cross-career-roll', { career_id: careerId, table: tbl });
        await applyResponse(response);
        lr.crossCareerResult = response;
        renderAll();
      } catch (err) {
        alert(err.message || 'Cross-career roll failed.');
        btn.disabled = false;
      }
    });
  });

  // Entertainer event 5: two-stage associate picker (type → person).
  document.querySelectorAll('[data-ent-assoc-type]').forEach(btn => {
    btn.addEventListener('click', () => {
      const lr = uiState.lastRoll;
      if (!lr) return;
      lr.entertainerAssocType = btn.getAttribute('data-ent-assoc-type');
      renderAll();
    });
  });
  document.querySelectorAll('[data-ent-assoc-person]').forEach(btn => {
    btn.addEventListener('click', () => {
      const lr = uiState.lastRoll;
      if (!lr) return;
      lr.entertainerPersonType = btn.getAttribute('data-ent-assoc-person');
      renderAll();
    });
  });
  const btnEntConfirm = document.getElementById('btn-ent-assoc-confirm');
  if (btnEntConfirm) {
    btnEntConfirm.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || !lr.entertainerAssocType || !lr.entertainerPersonType) return;
      const kind = lr.entertainerAssocType;
      const person = lr.entertainerPersonType;
      const desc = `${person} [Entertainer event]`;
      try {
        const resp = await apiCall('/api/character/associate', { kind, description: desc });
        await applyResponse(resp);
        lr.entertainerAssocDone = `${kind.charAt(0).toUpperCase()+kind.slice(1)}: ${desc}`;
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not add associate.');
      }
    });
  }

  // Associate outcomes — "Gain a Contact/Ally/Rival/Enemy" or Betrayal convert.
  const labelAssoc = (k) => ({contact:'Contact', ally:'Ally', rival:'Rival', enemy:'Enemy'}[k] || k);
  const recordAssocDone = (opIdx, summary) => {
    if (!uiState.lastRoll || uiState.lastRoll.type !== 'event') return;
    const arr = Array.isArray(uiState.lastRoll.associateOpsDone) ? uiState.lastRoll.associateOpsDone.slice() : [];
    while (arr.length <= opIdx) arr.push(null);
    arr[opIdx] = summary;
    uiState.lastRoll.associateOpsDone = arr;
  };
  const disableAllAssocChips = () => {
    document.querySelectorAll('[data-assoc-add],[data-assoc-convert]').forEach(c => { c.disabled = true; });
  };
  const enableAllAssocChips = () => {
    document.querySelectorAll('[data-assoc-add],[data-assoc-convert]').forEach(c => { c.disabled = false; });
  };

  document.querySelectorAll('[data-assoc-add]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const opIdx = parseInt(chip.getAttribute('data-assoc-add'), 10);
      const kind = chip.getAttribute('data-assoc-kind');
      const descEl = document.querySelector(`[data-assoc-desc="${opIdx}"]`);
      const description = (descEl?.value || '').trim();
      try {
        disableAllAssocChips();
        const response = await apiCall('/api/character/associate', {
          op: 'add', kind, description,
        });
        await applyResponse(response);
        const summary = `Gained ${labelAssoc(kind)}${description ? `: ${description}` : ''}`;
        recordAssocDone(opIdx, summary);
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not add that associate.');
        enableAllAssocChips();
      }
    });
  });

  document.querySelectorAll('[data-assoc-convert]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const opIdx = parseInt(chip.getAttribute('data-assoc-convert'), 10);
      const index = parseInt(chip.getAttribute('data-assoc-index'), 10);
      const toKind = chip.getAttribute('data-assoc-to');
      try {
        disableAllAssocChips();
        const response = await apiCall('/api/character/associate', {
          op: 'convert', index, to_kind: toKind,
        });
        await applyResponse(response);
        const conv = response.converted || {};
        const summary = `Betrayal — ${labelAssoc(conv.from_kind || '')} → ${labelAssoc(conv.to_kind || toKind)}${conv.description ? `: ${conv.description}` : ''}`;
        recordAssocDone(opIdx, summary);
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not convert that associate.');
        enableAllAssocChips();
      }
    });
  });

  const btnMishap = document.getElementById('btn-mishap');
  if (btnMishap) {
    btnMishap.addEventListener('click', async () => {
      const response = await apiCall('/api/character/mishap');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'mishap',
        data: response.roll,
        mishapText: response.mishap,
        autoApplied: response.auto_applied || [],
        injuryPending: response.injury_pending || false,
        injuryTitle: response.injury_data?.title || null,
        injuryText: response.injury_data?.text || null,
        injuryRoll: response.injury_data?.roll?.total ?? null,
        frozenWatch: response.frozen_watch || false,
      };
      renderAll();
    });
  }

  const btnPostMishap = document.getElementById('btn-post-mishap');
  if (btnPostMishap) {
    btnPostMishap.addEventListener('click', async () => {
      const endResp = await apiCall('/api/character/end-term', { leaving: true, reason: 'mishap' });
      await applyResponse(endResp);
      uiState.lastRoll = null;
      uiState.subPhase = null;
      uiState.selectedCareer = null;
      uiState.selectedAssignment = null;
      renderAll();
    });
  }

  // Helper: call career-mishap-choice and refresh state
  async function resolveMishapChoice(choiceData) {
    const response = await apiCall('/api/character/career-mishap-choice', { choice_data: choiceData });
    await applyResponse(response);
    if (uiState.lastRoll) {
      uiState.lastRoll.autoApplied = [
        ...(uiState.lastRoll.autoApplied || []),
        ...(response.auto_applied || []),
      ];
      uiState.lastRoll.injuryPending = response.injury_pending || false;
      if (response.injury_data) {
        uiState.lastRoll.injuryTitle = response.injury_data.title;
        uiState.lastRoll.injuryText = response.injury_data.text;
        uiState.lastRoll.injuryRoll = response.injury_data?.roll?.total ?? null;
      }
      if (response.skill_check) {
        uiState.lastRoll.skillCheckResult = response.skill_check;
      }
    }
    renderAll();
  }

  // Injury severity choice buttons
  const btnSeverityResult2 = document.getElementById('btn-mishap-choice-result2');
  if (btnSeverityResult2) {
    btnSeverityResult2.addEventListener('click', () => resolveMishapChoice({ choice: 'result_2' }));
  }
  const btnSeverityRollTwice = document.getElementById('btn-mishap-choice-roll-twice');
  if (btnSeverityRollTwice) {
    btnSeverityRollTwice.addEventListener('click', () => resolveMishapChoice({ choice: 'roll_twice' }));
  }

  // Stat choice buttons
  document.querySelectorAll('[id^="btn-mishap-statchoice-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const stat = btn.id.replace('btn-mishap-statchoice-', '');
      resolveMishapChoice({ stat });
    });
  });

  // Skill choice buttons
  document.querySelectorAll('[id^="btn-mishap-skillchoice-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const skill = btn.id.replace('btn-mishap-skillchoice-', '');
      resolveMishapChoice({ skill });
    });
  });

  // Free skill choice
  const btnFreeSkillConfirm = document.getElementById('btn-mishap-freeskill-confirm');
  if (btnFreeSkillConfirm) {
    btnFreeSkillConfirm.addEventListener('click', () => {
      const input = document.getElementById('input-mishap-freeskill');
      const skill = input ? input.value.trim() : '';
      if (!skill) { alert('Enter a skill name.'); return; }
      resolveMishapChoice({ skill });
    });
  }

  // Deal choice buttons
  const btnDealAccept = document.getElementById('btn-mishap-deal-accept');
  if (btnDealAccept) {
    btnDealAccept.addEventListener('click', () => resolveMishapChoice({ option_id: 'accept' }));
  }
  const btnDealRefuse = document.getElementById('btn-mishap-deal-refuse');
  if (btnDealRefuse) {
    btnDealRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));
  }

  // Army join/cooperate buttons
  const btnArmyJoin = document.getElementById('btn-mishap-armyjoin-join');
  if (btnArmyJoin) {
    btnArmyJoin.addEventListener('click', () => resolveMishapChoice({ option_id: 'join' }));
  }
  const btnArmyCooperate = document.getElementById('btn-mishap-armyjoin-cooperate');
  if (btnArmyCooperate) {
    btnArmyCooperate.addEventListener('click', () => resolveMishapChoice({ option_id: 'cooperate' }));
  }

  // SolSec blame choice
  const btnBlamePin = document.getElementById('btn-mishap-blame-pin');
  if (btnBlamePin) btnBlamePin.addEventListener('click', () => resolveMishapChoice({ option_id: 'pin' }));
  const btnBlameFall = document.getElementById('btn-mishap-blame-fall');
  if (btnBlameFall) btnBlameFall.addEventListener('click', () => resolveMishapChoice({ option_id: 'fall' }));

  // SolSec expose choice
  const btnExposeYes = document.getElementById('btn-mishap-expose-yes');
  if (btnExposeYes) btnExposeYes.addEventListener('click', () => resolveMishapChoice({ option_id: 'expose' }));
  const btnExposeNo = document.getElementById('btn-mishap-expose-no');
  if (btnExposeNo) btnExposeNo.addEventListener('click', () => resolveMishapChoice({ option_id: 'quiet' }));

  // Party denounce choice
  const btnDenounceYes = document.getElementById('btn-mishap-denounce-yes');
  if (btnDenounceYes) btnDenounceYes.addEventListener('click', () => resolveMishapChoice({ option_id: 'denounce' }));
  const btnDenounceNo = document.getElementById('btn-mishap-denounce-no');
  if (btnDenounceNo) btnDenounceNo.addEventListener('click', () => resolveMishapChoice({ option_id: 'silent' }));

  // SolSec interrogation choice
  const btnIntSubmit = document.getElementById('btn-mishap-interrogation-submit');
  if (btnIntSubmit) btnIntSubmit.addEventListener('click', () => resolveMishapChoice({ option_id: 'submit' }));
  const btnIntRefuse = document.getElementById('btn-mishap-interrogation-refuse');
  if (btnIntRefuse) btnIntRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));

  // Mishap victim buttons
  document.querySelectorAll('[id^="btn-mishap-victim-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.id === 'btn-mishap-victim-skip') {
        // No contacts/allies — clear pending
        resolveMishapChoice({ option_id: 'skip' });
        return;
      }
      const idx = parseInt(btn.getAttribute('data-assoc-idx'), 10);
      resolveMishapChoice({ associate_index: idx });
    });
  });

  // Skill check buttons
  document.querySelectorAll('[id^="btn-mishap-skillcheck-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const skillName = btn.getAttribute('data-skill');
      resolveMishapChoice({ skill_name: skillName });
    });
  });

  const btnAdvance = document.getElementById('btn-advance');
  if (btnAdvance) {
    btnAdvance.addEventListener('click', async () => {
      const response = await apiCall('/api/character/advance');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'advance',
        data: response.roll,
        outcome: response.advanced ? 'pass' : 'fail',
        newRank: response.new_rank,
        newRankTitle: response.new_rank_title,
      };
      // Stay on 'advance' — render already handles the post-roll view
      renderAll();
    });
  }

  const btnSkipAdvance = document.getElementById('btn-skip-advance');
  if (btnSkipAdvance) {
    btnSkipAdvance.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'decide';
      renderStage();
    });
  }

  const btnContinue = document.getElementById('btn-continue-career');
  if (btnContinue) {
    btnContinue.addEventListener('click', async () => {
      const endResp = await apiCall('/api/character/end-term', { leaving: false });
      await applyResponse(endResp);
      // Start next term of same career+assignment
      const startResp = await apiCall('/api/character/start-term', {
        career_id: character.current_term?.career_id || uiState.selectedCareer,
        assignment_id: character.current_term?.assignment_id || uiState.selectedAssignment,
      });
      // ... but current_term is already null after end_term. We need the last one.
      // Simpler: remember values before clearing.
    });
  }

  const btnNextTerm = document.getElementById('btn-next-term');
  if (btnNextTerm) {
    btnNextTerm.addEventListener('click', async () => {
      const careerId = character.current_term.career_id;
      const assignmentId = character.current_term.assignment_id;
      const endResp = await apiCall('/api/character/end-term', { leaving: false });
      await applyResponse(endResp);
      const startResp = await apiCall('/api/character/start-term', {
        career_id: careerId,
        assignment_id: assignmentId,
      });
      await applyResponse(startResp);
      uiState.subPhase = 'train';
      renderAll();
    });
  }

  const btnLeaveCareer = document.getElementById('btn-leave-career');
  if (btnLeaveCareer) {
    btnLeaveCareer.addEventListener('click', async () => {
      const response = await apiCall('/api/character/end-term', { leaving: true, reason: 'voluntary' });
      await applyResponse(response);
      uiState.subPhase = null;
      uiState.selectedCareer = null;
      uiState.selectedAssignment = null;
      renderAll();
    });
  }

  // Frozen Watch — stay in service, start next term of same career/assignment
  const btnFrozenWatch = document.getElementById('btn-frozen-watch-continue');
  if (btnFrozenWatch) {
    btnFrozenWatch.addEventListener('click', async () => {
      try {
        const careerId = character.current_term.career_id;
        const assignmentId = character.current_term.assignment_id;
        const endResp = await apiCall('/api/character/end-term', { leaving: false });
        await applyResponse(endResp);
        const startResp = await apiCall('/api/character/start-term', {
          career_id: careerId,
          assignment_id: assignmentId,
        });
        await applyResponse(startResp);
        uiState.lastRoll = null;
        uiState.subPhase = 'train';
        renderAll();
      } catch (e) { alert(e.message); }
    });
  }

  // Injury roll (from mishap screen)
  const btnRollInjury = document.getElementById('btn-roll-injury');
  if (btnRollInjury) {
    btnRollInjury.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/injury');
        await applyResponse(response);
        uiState.lastRoll = {
          ...uiState.lastRoll,
          type: 'mishap',
          injuryTitle: response.title,
          injuryText: response.text,
          injuryPending: !!response.pending_choice,
          injuryData: response.pending_choice,
        };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  }

  // Injury stat choice buttons (career phase)
  ['STR', 'DEX', 'END'].forEach(stat => {
    const btn = document.getElementById(`btn-career-injury-stat-${stat}`);
    if (btn) btn.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/injury-choice', { chosen_stat: stat });
        await applyResponse(response);
        const billsMsg = formatMedicalBillsMsg(response);
        if (billsMsg) alert(billsMsg);
        uiState.lastRoll = { ...uiState.lastRoll, injuryPending: false };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });
}

function renderActiveTerm() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const assignment = career.assignments[term.assignment_id];

  const banner = `
    <div class="term-banner">
      <span class="term-part"><strong>${career.name}</strong> · ${assignment.name}</span>
      <span class="term-part">TERM <strong>${term.overall_term_number}</strong> · AGE <strong>${character.age}</strong></span>
      <span class="term-part">RANK <strong>${term.rank}</strong>${term.rank_title ? ` — ${term.rank_title}` : ''}</span>
    </div>
  `;

  // Sub-phase dispatcher
  if (uiState.subPhase === 'qualify') {
    return renderQualifyResult();
  }
  if (uiState.subPhase === 'train' || uiState.subPhase === null) {
    return banner + renderSkillChoice();
  }
  if (uiState.subPhase === 'survive') {
    return banner + renderSurviveStep();
  }
  if (uiState.subPhase === 'event') {
    return banner + renderEventStep();
  }
  if (uiState.subPhase === 'mishap') {
    return banner + renderMishapStep();
  }
  if (uiState.subPhase === 'advance') {
    return banner + renderAdvanceStep();
  }
  if (uiState.subPhase === 'decide') {
    return banner + renderDecideStep();
  }
  return banner + '<div class="stage-content"><p>Unknown sub-phase</p></div>';
}

function renderQualifyResult() {
  // User clicked a career card, qualification was rolled.
  const roll = uiState.lastRoll;
  const career = CAREERS.find(c => c.id === uiState.selectedCareer);

  if (roll.automatic) {
    // Auto-qualify → go straight to assignment pick
    return `
      <div class="panel-header"><span class="led"></span><span>QUALIFICATION — AUTOMATIC</span></div>
      <div class="stage-content">
        <div class="phase-label">${career.name}</div>
        <h2 class="phase-title">Welcome Aboard</h2>
        <p class="phase-subtitle">Automatic qualification. No roll required.</p>
        ${renderAssignmentPicker(career)}
      </div>
    `;
  }

  const r = roll.roll;
  if (roll.succeeded) {
    return `
      <div class="panel-header"><span class="led"></span><span>QUALIFICATION — PASS</span></div>
      <div class="stage-content">
        <div class="phase-label">${career.name}</div>
        <h2 class="phase-title">Accepted</h2>
        <div class="roll-readout">
          <span class="dice">[${r.dice.join(', ')}]</span>
          ${r.modifier !== 0 ? `<span class="eq">${r.modifier > 0 ? '+' : ''}${r.modifier}</span>` : ''}
          <span class="eq">=</span>
          <span class="total">${r.total}</span>
          <span class="eq">vs ${r.target}+</span>
          <span class="outcome pass">PASS</span>
        </div>
        ${renderAssignmentPicker(career)}
      </div>
    `;
  } else {
    return `
      <div class="panel-header"><span class="led"></span><span>QUALIFICATION — FAIL</span></div>
      <div class="stage-content">
        <div class="phase-label">${career.name}</div>
        <h2 class="phase-title">Rejected</h2>
        <div class="roll-readout">
          <span class="dice">[${r.dice.join(', ')}]</span>
          ${r.modifier !== 0 ? `<span class="eq">${r.modifier > 0 ? '+' : ''}${r.modifier}</span>` : ''}
          <span class="eq">=</span>
          <span class="total">${r.total}</span>
          <span class="eq">vs ${r.target}+</span>
          <span class="outcome fail">FAIL</span>
        </div>
        <p class="phase-body">You didn't qualify. The rules offer three options:</p>
        <ul class="phase-body" style="padding-left:20px;line-height:1.7">
          <li><strong>Accept the Draft</strong> — 1D determines which service takes you (Navy, Army, Marines, Merchant Marine, Scouts, or Agent). No choice in assignment, but you start a term immediately.</li>
          <li><strong>Become a Drifter</strong> — auto-qualifies, rough life, cheap mustering benefits.</li>
          <li><strong>Try Another Career</strong> — attempt a different qualification (each failed career should carry a DM-1 penalty; not yet modeled).</li>
        </ul>
        <div class="phase-actions">
          <button class="btn primary" id="btn-accept-draft">ACCEPT THE DRAFT</button>
          <button class="btn" id="btn-drifter-auto">BECOME A DRIFTER</button>
          <button class="btn" id="btn-back-careers">← TRY ANOTHER CAREER</button>
        </div>
      </div>
    `;
  }
}

function renderDraftResult() {
  const roll = uiState.lastRoll;
  const r = roll.roll;
  return `
    <div class="panel-header"><span class="led"></span><span>DRAFT — CONSCRIPTED</span></div>
    <div class="stage-content">
      <div class="phase-label">${roll.career_name}</div>
      <h2 class="phase-title">Drafted into ${roll.assignment_name}</h2>
      <div class="roll-readout">
        <span class="dice">[${r.dice.join(', ')}]</span>
        <span class="eq">=</span>
        <span class="total">${r.total}</span>
        <span class="outcome pass">DRAFT</span>
      </div>
      <p class="phase-body">The papers came through. You're now a ${roll.assignment_name} in the ${roll.career_name}. Basic training starts on arrival.</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-begin-drafted-term">BEGIN TERM →</button>
      </div>
    </div>
  `;
}

function renderAssignmentPicker(career) {
  // Home Forces training result banner (shown once after enrolling)
  let hfTrainingBanner = '';
  if (uiState.lastRoll?.type === 'home_forces_training') {
    const lr = uiState.lastRoll;
    hfTrainingBanner = `
      <div style="margin-bottom:14px;padding:12px 14px;border:1px solid var(--accent);border-radius:6px;background:rgba(0,255,170,0.04)">
        <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">HOME FORCES RESERVES — ENROLLED (${lr.component?.toUpperCase()})</div>
        <div style="margin-top:6px;font-size:13px;color:var(--text)">
          Training roll [1D=${lr.roll?.raw_total ?? '?'}]: <strong>${escapeHTML(lr.result || '')}</strong>
        </div>
        <div style="font-size:12px;color:var(--text-dim);margin-top:3px">
          Auto-skill: ${escapeHTML(lr.auto_skill || '')} 0
          ${lr.rank_transferred ? ` · Military rank ${lr.rank_transferred} transferred.` : ''}
        </div>
        <div class="phase-actions" style="margin-top:8px">
          <button class="btn ghost" id="btn-hf-training-dismiss" style="font-size:11px;padding:6px 12px">DISMISS →</button>
        </div>
      </div>
    `;
  }

  const isSecretAgentSelected = career.id === 'solsec' && uiState.selectedAssignment === 'secret_agent';
  const soc = character.society_id || 'third_imperium';

  // Cover career picker — only relevant for SolSec Secret Agent
  const COVER_CAREER_EXCLUDE = new Set(['solsec', 'party', 'drifter', 'prisoner']);
  const coverCareers = CAREERS.filter(c => {
    if (COVER_CAREER_EXCLUDE.has(c.id)) return false;
    if (c.societies && c.societies.length > 0 && !c.societies.includes(soc)) return false;
    if (c.blocked_societies && c.blocked_societies.includes(soc)) return false;
    return true;
  });

  const coverPickerHTML = isSecretAgentSelected ? `
    <div style="margin-top:20px;padding:14px;border:1px solid var(--amber-dim);border-radius:6px">
      <div style="font-size:11px;letter-spacing:0.2em;color:var(--amber-dim);margin-bottom:10px">
        SELECT COVER CAREER — Your public identity. Survival uses cover career stats DM-1; advancement uses cover career stats DM+1.
      </div>
      <div class="card-grid" style="grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px">
        ${coverCareers.map(c => `
          <button class="card${uiState.selectedCoverCareer === c.id ? ' selected' : ''}" data-cover-career="${c.id}"
            style="padding:10px 12px">
            <div class="card-title" style="font-size:12px">${c.name}</div>
          </button>
        `).join('')}
      </div>
      ${uiState.selectedCoverCareer ? `
        <p style="font-size:11px;color:var(--accent);margin-top:8px">
          ✓ Cover: <strong>${CAREERS.find(c=>c.id===uiState.selectedCoverCareer)?.name}</strong>
          — survival and advancement use this career's stats (DM-1 / DM+1).
        </p>` : `
        <p style="font-size:11px;color:var(--text-dim);margin-top:8px">Select a cover career above to continue.</p>
      `}
    </div>
  ` : '';

  const readyToStart = uiState.selectedAssignment &&
    (!isSecretAgentSelected || uiState.selectedCoverCareer);

  const cards = Object.entries(career.assignments).map(([id, a]) => `
    <button class="card ${uiState.selectedAssignment === id ? 'selected' : ''}" data-assignment="${id}">
      <div class="card-title">${a.name}</div>
      <div class="card-meta">SURV ${a.survival.characteristic} ${a.survival.target}+ · ADV ${a.advancement.characteristic} ${a.advancement.target}+</div>
      <div class="card-desc">${a.description}</div>
    </button>
  `).join('');

  // ---- Solomani parallel service panels ----
  const isSolomani = (character.society_id === 'solomani_confederation');
  const isBarredFromHF = (career.id === 'drifter')
    || (career.id === 'rogue' && uiState.selectedAssignment === 'pirate')
    || (career.id === 'solsec');
  const showHomeForces = isSolomani && !isBarredFromHF;
  const showMonitor = isSolomani && career.id !== 'solsec';

  // Determine which HF component this character would join
  const isNavalMerchant = career.id === 'merchant'
    && (uiState.selectedAssignment === 'merchant_marine' || uiState.selectedAssignment === 'free_trader');
  const hasExNavy = character.completed_careers && character.completed_careers.some(
    c => c.career_id === 'navy' || c.career_id === 'confederation_navy');
  const hfComponent = (isNavalMerchant || hasExNavy) ? 'naval' : 'groundside';
  const hfComponentLabel = hfComponent === 'naval' ? 'Naval' : 'Groundside';

  const homeForcesHTML = showHomeForces ? `
    <div style="margin-top:16px;padding:12px 14px;border:1px solid var(--border);border-radius:6px">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:200px">
          <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">HOME FORCES RESERVES (${hfComponentLabel})</div>
          <div style="font-size:12px;color:var(--text-dim);margin-top:3px">
            ${character.home_forces_enrolled
              ? `Enrolled · Rank ${character.home_forces_rank}`
              : 'Part-time planetary defence. Automatic enlistment — gains training skill + ' + (hfComponent === 'naval' ? 'Vacc Suit 0' : 'Gun Combat 0') + '.'}
          </div>
        </div>
        ${character.home_forces_enrolled
          ? `<button class="btn ghost" id="btn-hf-leave" style="font-size:11px;padding:6px 12px">RESIGN</button>`
          : `<button class="btn ghost" id="btn-hf-enroll" style="font-size:11px;padding:6px 12px">ENLIST (Roll Training)</button>`
        }
      </div>
      ${character.home_forces_enrolled ? `
        <p style="font-size:11px;color:var(--text-dim);margin:6px 0 0">
          Nat-2 on survival → also rolls ${hfComponent === 'naval' ? 'Confederation Navy' : 'Confederation Army'} Mishap table.
          ${character.home_forces_rank >= 3 ? 'Rank 3+ may use ' + hfComponentLabel + ' advancement.' : ''}
        </p>` : ''}
    </div>
  ` : '';

  const monitorStatusColor = character.solsec_monitor ? 'var(--amber)' : 'var(--text-dim)';
  const solsecMonitorHTML = showMonitor ? `
    <div style="margin-top:10px;padding:12px 14px;border:1px solid var(--border);border-radius:6px">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:200px">
          <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">
            SOLSEC MONITOR${character.solsec_monitor ? ` · RANK ${character.solsec_monitor_rank}` : ''}
          </div>
          <div style="font-size:12px;color:${monitorStatusColor};margin-top:3px">
            ${character.solsec_monitor
              ? 'Active informer — DM+1 advancement, nat-2→SolSec Mishap, nat-12→SolSec Event + Contact.'
              : 'Volunteer SolSec informer. DM+1 to all advancement rolls (not Drifter).'}
          </div>
        </div>
        ${character.solsec_monitor
          ? `<button class="btn ghost" id="btn-monitor-leave" style="font-size:11px;padding:6px 12px">CEASE MONITORING</button>`
          : `<button class="btn ghost" id="btn-monitor-join" style="font-size:11px;padding:6px 12px">BECOME MONITOR</button>`
        }
      </div>
      ${character.solsec_monitor && character.solsec_monitor_rank >= 3 ? `
        <p style="font-size:11px;color:var(--accent);margin:6px 0 0">
          Rank ${character.solsec_monitor_rank}: earns one extra Benefit roll at muster-out (own table or SolSec Benefits).
        </p>` : ''}
    </div>
  ` : '';

  return `
    ${hfTrainingBanner}
    <h3 style="margin-top:${hfTrainingBanner ? '0' : '28'}px;font-family:var(--font-mono);font-size:11px;letter-spacing:0.3em;color:var(--amber-dim);text-transform:uppercase">Choose an Assignment</h3>
    <div class="card-grid">${cards}</div>
    ${coverPickerHTML}
    ${homeForcesHTML}
    ${solsecMonitorHTML}
    <div class="phase-actions" style="margin-top:16px">
      <button class="btn primary" id="btn-start-term" ${readyToStart ? '' : 'disabled'}>
        BEGIN TERM →
      </button>
    </div>
  `;
}

function renderSkillChoice() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const tables = career.skill_tables || {};

  // Post-roll view: a skill-table roll just completed
  if (uiState.lastRoll?.type === 'skill') {
    const lr = uiState.lastRoll;
    return `
      <div class="stage-content">
        <div class="phase-label">Skill Training · 1D Result</div>
        <h2 class="phase-title">${lr.tableName}</h2>
        ${rollReadoutHTML(lr.data, { label: '1D', showTarget: false })}
        <div class="event-box">
          <span class="event-label">Rolled ${lr.data?.total ?? '?'} → ${escapeHTML(lr.result || '?')}</span>
          ${escapeHTML(lr.applied || '')}
        </div>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-skill">SURVIVAL ROLL →</button>
        </div>
      </div>
    `;
  }

  // Basic training: auto-applied by the backend — show a summary view.
  if (term.basic_training) {
    const btSkills = uiState.basicTrainingSkills || [];
    const skillItems = btSkills.length
      ? btSkills.map(s => `<li style="font-family:var(--font-mono);font-size:12px;color:var(--amber)">${escapeHTML(s)}</li>`).join('')
      : '<li style="color:var(--muted)">Skills applied — see character sheet.</li>';
    return `
      <div class="stage-content">
        <div class="phase-label">Basic Training — Auto-Applied</div>
        <h2 class="phase-title">Basic Training</h2>
        <p class="phase-subtitle">First term in this career — all Service Skills granted at level 0 automatically.</p>
        <ul style="list-style:none;padding:0;margin:12px 0">${skillItems}</ul>
        <div class="phase-actions">
          <button class="btn primary" id="btn-basic-training-continue">CONTINUE TO SURVIVAL →</button>
        </div>
      </div>
    `;
  }

  // Which tables can this character roll on?
  const available = Object.entries(tables).filter(([key, t]) => {
    if (t.assignment_only && t.assignment_only !== term.assignment_id) return false;
    if (t.requires_commission && !term.commissioned) return false;
    return true;
  });

  if (!available.length) {
    // Career has no skill tables encoded yet (stub career)
    return `
      <div class="stage-content">
        <div class="phase-label">Skill Training</div>
        <h2 class="phase-title">No Tables Encoded</h2>
        <p class="phase-body">This career's skill tables aren't in the JSON yet. You can skip the skill roll for this term and proceed to survival. (See the README for how to complete career data from the rulebook.)</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-skill">SURVIVAL ROLL →</button>
        </div>
      </div>
    `;
  }

  const eduGate = character.characteristics.EDU;
  const buttons = available.map(([key, t]) => {
    const gated = t.requires_edu && eduGate < t.requires_edu;
    return `
      <button class="btn ${gated ? 'ghost' : ''}" data-skill-table="${key}" ${gated ? 'disabled' : ''}>
        ${t.name || key}${t.requires_edu ? ` (REQ EDU ${t.requires_edu}+)` : ''}
      </button>
    `;
  }).join('');

  const acr = uiState.academyCommissionRoll;
  const commRollHTML = acr ? (() => {
    const outcome = acr.succeeded ? 'Commissioned at Rank 1' : 'Not commissioned — starting as enlisted';
    uiState.academyCommissionRoll = null; // show once
    return `
      <div class="dm-applied-box" style="margin-bottom:12px">
        <span class="event-label">Academy Commission Roll</span>
        <div class="dm-chip applied">2D [${(acr.dice || []).join(' · ')}] +${acr.modifier ?? acr.dm ?? 0} = ${acr.total} vs ${acr.target}+ — ${escapeHTML(outcome)}</div>
      </div>
    `;
  })() : '';

  return `
    <div class="stage-content">
      <div class="phase-label">Skill Training · 1D Roll</div>
      <h2 class="phase-title">Skills and Training</h2>
      <p class="phase-subtitle">Pick one skill table and roll 1D on it.</p>
      ${commRollHTML}
      <div class="phase-actions" style="flex-direction:column;align-items:stretch;gap:8px">
        ${buttons}
      </div>
    </div>
  `;
}

function renderSurviveStep() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const assignment = career.assignments[term.assignment_id];
  const s = assignment.survival;
  const dm = charDM(character.characteristics[s.characteristic]);

  // Post-roll view: show dice + outcome
  if (uiState.lastRoll?.type === 'survive') {
    const lr = uiState.lastRoll;
    const survived = lr.outcome === 'pass';

    // Build parallel service event notices
    const buildParallelNotice = (pe) => {
      if (!pe) return '';
      const items = Array.isArray(pe) ? pe : [pe];
      return items.map(p => {
        if (p.type === 'monitor_mishap') {
          return `<div class="event-box" style="border-color:var(--danger);margin-top:10px">
            <span class="event-label" style="color:var(--danger)">SolSec Monitor — Mishap [1D=${p.roll?.raw_total}]</span>
            ${escapeHTML(p.text)}
          </div>`;
        }
        if (p.type === 'monitor_event') {
          return `<div class="event-box" style="border-color:var(--accent);margin-top:10px">
            <span class="event-label" style="color:var(--accent)">SolSec Monitor — Event [2D=${p.roll?.raw_total}] + SolSec Contact gained</span>
            ${escapeHTML(p.text)}
          </div>`;
        }
        if (p.type === 'home_forces_mishap') {
          return `<div class="event-box" style="border-color:var(--amber);margin-top:10px">
            <span class="event-label" style="color:var(--amber)">Home Forces Reserves (${p.component}) — Mishap [1D=${p.roll?.raw_total}]</span>
            ${escapeHTML(p.text)}
          </div>`;
        }
        return '';
      }).join('');
    };

    const parallelNotice = buildParallelNotice(lr.parallel_event);

    return `
      <div class="stage-content">
        <div class="phase-label">Survival — ${survived ? 'Pass' : 'Fail'}</div>
        <h2 class="phase-title">${survived ? 'You Survived' : 'Career Mishap'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${s.characteristic} ${s.target}+` })}
        ${parallelNotice}
        <p class="phase-body">${survived
          ? 'Your term continues. Roll the Event table to see what the last four years brought.'
          : 'Your career is over. Roll on the Mishap table to see how it ended.'}</p>
        <div class="phase-actions">
          <button class="btn ${survived ? 'primary' : 'danger'}" id="btn-post-survive">
            ${survived ? 'ROLL EVENT →' : 'ROLL MISHAP →'}
          </button>
        </div>
      </div>
    `;
  }

  return `
    <div class="stage-content">
      <div class="phase-label">Will You Survive?</div>
      <h2 class="phase-title">Survival Roll</h2>
      <p class="phase-subtitle">${s.characteristic} ${s.target}+ (your DM is ${formatDM(dm)})</p>

      <p class="phase-body">Fail this roll and you suffer a career-ending mishap. Welcome to Traveller.</p>

      <div class="phase-actions">
        <button class="btn primary" id="btn-survive">ROLL 2D FOR SURVIVAL</button>
      </div>
    </div>
  `;
}

function parseEventSkillOptions(text) {
  // Find skill-grant patterns in event text. Returns an array of trimmed option
  // strings, or null if no such pattern is present. Handles:
  //   - "Gain one of X, Y, Z or W"
  //   - "Gain any one of ..."
  //   - "Either gain one level of X, Y or Z, or DM+4..."
  //   - "Gain one level of X, Y or Z"
  //   - "Gain one level of X" (single skill — still returned as an array)
  //   - "Increase X by one level" (single skill)
  if (!text) return null;

  const splitToParts = (raw) => {
    // Stop the skill-list at trailing continuations like ", as well as ..."
    // or ", and gain an Ally" so the last option isn't absorbed.
    let trimmed = raw.replace(/\s*,?\s*(?:as\s+well\s+as|and\s+(?:a|an|one|gain|then)|plus|by\s+\d+)\b.*$/i, '').trim();
    trimmed = trimmed.replace(/\s*by\s+(?:one|a|\d+)\s+level\s*$/i, '').trim();
    const lastOr = trimmed.toLowerCase().lastIndexOf(' or ');
    let parts;
    if (lastOr >= 0) {
      const head = trimmed.slice(0, lastOr);
      const tail = trimmed.slice(lastOr + 4);
      parts = head.split(',').map(s => s.trim()).filter(Boolean);
      parts.push(tail.trim());
    } else {
      parts = trimmed.split(',').map(s => s.trim()).filter(Boolean);
    }
    // Skill-name sanity: letters/spaces/parens/digits, under 40 chars.
    return parts.filter(p => /^[A-Za-z][A-Za-z0-9 ()\-/]*\d*\s*$/.test(p) && p.length < 40);
  };

  // Open-ended "any skill" grants are handled by parseEventWildcardSkill —
  // which returns a dynamic list based on character / career. Return null
  // here so the caller knows to try the wildcard parser instead.
  if (/any\s+(?:one\s+)?skill\s+you\s+already\s+have/i.test(text)
      || /any\s+skill\s+of\s+your\s+choice/i.test(text)
      || /gain\s+(?:one\s+level\s+(?:in|of)\s+)?any\s+(?:skill|service\s+skill)/i.test(text)
      || /any\s+(?:one\s+)?skill\s+from\s+the\s+(?:service|officer|advanced\s+education)/i.test(text)
      || /any\s+science\s+specialty/i.test(text)) {
    return null;
  }

  // Pattern 1: "Gain one of X, Y or Z" / "Gain any one of ..."
  let m = text.match(/Gain\s+(?:any\s+)?one\s+of\s+([^.]+?)(?:\.|$)/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 2) return parts;
  }

  // Pattern 2: "Either gain one level of X, Y or Z, or DM+N..."
  //           "Either gain a level of X or ..."  (comma before "or DM" is optional)
  m = text.match(/Either\s+gain\s+(?:one|a|\d+)\s+level\s+(?:of|in)\s+([^.]+?)(?:,?\s*or\s+DM|\.|$)/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 1) return parts;
  }

  // Pattern 3: "Gain one level of X, Y or Z" (without "Either")
  m = text.match(/Gain\s+(?:one|a|\d+)\s+level\s+(?:of|in)\s+([^.]+?)(?:,\s*or\s+DM|\.|$)/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 1) return parts;
  }

  // Pattern 4: "Increase X by one level" (single skill)
  m = text.match(/Increase\s+([A-Za-z][A-Za-z0-9 ()\-/]{0,35})\s+by\s+(?:one|a|\d+)\s+level/i);
  if (m) {
    const skill = m[1].trim();
    if (skill) return [skill];
  }

  // Pattern 4b: "increase one of X, Y or Z by 1" (drifter[5])
  m = text.match(/increase\s+one\s+of\s+([^.]+?)\s+by\s+(?:one|a|\d+)(?:\s+level)?\b/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 2) return parts;
  }

  // Pattern 4c: "pick up X 1, Y 1, or Z 1" (prisoner[5])
  m = text.match(/pick\s+up\s+([^.]+?)(?:\.|$)/i);
  if (m) {
    // Strip trailing level digits ("Streetwise 1" → "Streetwise")
    const cleaned = m[1].trim().replace(/\s+\d+\b/g, '');
    const parts = splitToParts(cleaned);
    if (parts.length >= 1) return parts;
  }

  // Pattern 5: "Gain Vacc Suit 1 or Athletics (dexterity) 1"
  // "Gain X <N> or Y <N> [or Z <N>]" — skill name(s) with levels, no "one of"
  // preamble. Splits on " or " / ",", keeps the trailing digit in each part.
  m = text.match(/Gain\s+([A-Z][A-Za-z ()\-/]+?\s+\d(?:\s*(?:,|or)\s+[A-Z][A-Za-z ()\-/]+?\s+\d)+)(?:\.|$)/);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 2) return parts;
  }

  return null;
}

// Curated Traveller skill catalog for "any skill of your choice" pickers.
// Kept short enough to fit a chip grid but covers every core-rulebook skill.
const ALL_TRAVELLER_SKILLS = [
  'Admin', 'Advocate', 'Animals', 'Art', 'Astrogation', 'Athletics',
  'Battle Dress', 'Broker', 'Carouse', 'Deception', 'Diplomat', 'Drive',
  'Electronics', 'Engineer', 'Explosives', 'Flyer', 'Gambler', 'Gun Combat',
  'Gunner', 'Heavy Weapons', 'Investigate', 'Jack-of-all-Trades', 'Language',
  'Leadership', 'Mechanic', 'Medic', 'Melee', 'Navigation', 'Persuade',
  'Pilot', 'Profession', 'Recon', 'Science', 'Seafarer', 'Stealth',
  'Steward', 'Streetwise', 'Survival', 'Tactics', 'Vacc Suit',
];

function parseEventWildcardSkill(text) {
  // Detect open-ended skill grants. Returns one of:
  //   { type: 'already-have' }  — "any skill you already have"
  //   { type: 'free' }          — "any skill of your choice"
  //   { type: 'service' }       — "any Service Skill (of your choice)"
  //   { type: 'service-or-advanced' } — "any skill from the Service or Advanced Education tables"
  //   { type: 'officer-or-advanced' } — "from the Officer or Advanced Education tables"
  //   { type: 'science' }       — "any Science specialty"
  // or null.
  if (!text) return null;
  if (/any\s+(?:one\s+)?skill\s+you\s+already\s+have/i.test(text)) {
    return { type: 'already-have' };
  }
  if (/any\s+science\s+specialty/i.test(text)) {
    return { type: 'science' };
  }
  if (/any\s+(?:one\s+)?skill\s+from\s+the\s+officer\s+or\s+advanced\s+education/i.test(text)) {
    return { type: 'officer-or-advanced' };
  }
  if (/any\s+(?:one\s+)?skill\s+from\s+the\s+service\s+or\s+advanced\s+education/i.test(text)
      || /any\s+(?:one\s+)?skill\s+listed\s+on\s+the\s+service\s+or\s+advanced\s+education/i.test(text)) {
    return { type: 'service-or-advanced' };
  }
  if (/any\s+service\s+skill/i.test(text)) {
    return { type: 'service' };
  }
  if (/any\s+skill\s+of\s+your\s+choice/i.test(text)) {
    return { type: 'free' };
  }
  return null;
}

// Career-transfer offers, e.g. army[10] "transfer to the Marines (without a
// Qualification roll)". Returns { career_id: '...', career_name: '...' } or
// null. Maps mentioned career names to the JSON keys used by the backend.
function parseEventTransferOffer(text) {
  if (!text) return null;
  // Generic open transfer: "transfer to any other [non-military] career"
  if (/transfer\s+to\s+any\s+other\s+(?:non-military\s+)?career/i.test(text)) {
    const nonMilitary = /non-military/i.test(text);
    return { career_id: 'any', career_name: 'any career', nonMilitary };
  }
  // Named career transfer: "transfer to the Marines" / "transfer to the Army"
  const m = /transfer\s+to\s+(?:the\s+)?([A-Z][A-Za-z]+)/.exec(text);
  if (!m) return null;
  const name = m[1];
  const map = {
    Army: 'army',
    Marines: 'marine',
    Marine: 'marine',
    Navy: 'navy',
    Scouts: 'scout',
    Scout: 'scout',
    Agents: 'agent',
    Agent: 'agent',
    Nobility: 'noble',
    Noble: 'noble',
  };
  const careerId = map[name];
  if (!careerId) return null;
  return { career_id: careerId, career_name: name };
}

// Contested-roll parser. Detects "Roll <Skill> N+" patterns and returns
// { skills: [{name, parenthetical}], target: 8, successText, failText } or null.
// Handles: "Roll Art 8+ or Persuade 8+", "Roll SOC 8+", "Roll Tactics (naval) 8+",
// "Roll Stealth 8+ or Deception 8+; on success, ...", "If you succeed ... If you fail ..."

// Parse "If you refuse, <consequence>." branches (noble[3] duel, noble[8]
// conspiracy). Returns { consequence, stat, delta, associateKind } or null.
// We only attempt mechanics for SOC deltas and associate gains — anything
// else is surfaced as text-only for manual resolution.
function parseEventRefuseOption(text) {
  if (!text) return null;
  const m = text.match(/If you refuse,\s+([^.]+?)\./i);
  if (!m) return null;
  const consequence = m[1].trim();
  const out = { consequence, stat: null, delta: 0, associateKind: null };
  // "reduce your SOC by 1" / "reduce SOC by 2" / "lose 1 SOC"
  const statRe = /(?:reduce|lose)\s+(?:your\s+)?(\d+)?\s*(STR|DEX|END|INT|EDU|SOC)(?:\s+by\s+(\d+))?/i;
  const sm = consequence.match(statRe);
  if (sm) {
    const stat = sm[2].toUpperCase();
    const amount = parseInt(sm[3] || sm[1] || '1', 10);
    out.stat = stat;
    out.delta = -Math.abs(amount);
    return out;
  }
  // "gain the conspiracy as an Enemy" / "gain an Enemy" / "gain a Rival"
  const am = consequence.match(/gain\s+(?:the\s+\w+\s+as\s+)?(?:a|an|one)\s+(?:new\s+|another\s+)?(contact|ally|rival|enemy)/i);
  if (am) {
    out.associateKind = am[1].toLowerCase();
    return out;
  }
  // Manual fallback — still return the consequence text so UI can show it.
  return out;
}

function parseEventContestedRoll(text) {
  if (!text) return null;
  // Patterns handled:
  //   "Roll Art 8+ or Persuade 8+"  (target repeated per skill)
  //   "Roll Art or Persuade 8+"     (single target at end)
  //   "Roll Tactics (naval) 8+"     (speciality in parens)
  //   "Roll INT 8+"                 (characteristic check)
  const startIdx = text.search(/\bRoll\s+[A-Z]/);
  if (startIdx < 0) return null;
  let target = null;
  const skills = [];
  let scanEnd = startIdx;
  // Scan every "<Skill> N+" and "or <Skill> N+" at the start.
  // Allow optional second capitalized word to catch multi-word skills
  // like "Gun Combat", "Heavy Weapons", "Vacc Suit".
  const chunkRe = /(?:Roll\s+|\s+or\s+|\s+and\s+)([A-Z][A-Za-z]+(?:\s+[A-Z][a-z]+)?)(?:\s*\(([a-z]+)\))?(?:\s+(\d+)\s*\+)?/gy;
  chunkRe.lastIndex = startIdx;
  let mm;
  while ((mm = chunkRe.exec(text)) !== null) {
    if (mm[3]) target = parseInt(mm[3], 10);
    skills.push({ name: mm[1], speciality: mm[2] || null });
    scanEnd = chunkRe.lastIndex;
  }
  if (!skills.length || target == null) return null;
  // Slice off the roll prefix and find success/failure branches.
  const rest = text.slice(scanEnd);
  // Split into success and fail branches using positional ordering so
  // either branch can appear first.
  let successText = rest;
  let failText = '';
  const successMarkRe = /(?:^|[;.,\s])\s*(?:on success|if you succeed)\s*[,.]?\s*/i;
  const failMarkRe = /(?:^|[;.,\s])\s*(?:on failure|on failing|if you fail)\s*[,.]?\s*/i;
  const sMatch = successMarkRe.exec(rest);
  const fMatch = failMarkRe.exec(rest);
  const markers = [];
  if (sMatch) markers.push({ kind: 'success', start: sMatch.index, textStart: sMatch.index + sMatch[0].length });
  if (fMatch) markers.push({ kind: 'fail', start: fMatch.index, textStart: fMatch.index + fMatch[0].length });
  markers.sort((a, b) => a.start - b.start);
  if (markers.length) {
    for (let i = 0; i < markers.length; i++) {
      const ev = markers[i];
      const end = i + 1 < markers.length ? markers[i + 1].start : rest.length;
      const chunk = rest.slice(ev.textStart, end).trim();
      if (ev.kind === 'success') successText = chunk;
      else failText = chunk;
    }
    if (!sMatch) successText = '';
  }
  return { skills, target, successText: successText.replace(/^[;.,\s]+/, ''), failText };
}

// Get character's level for a named skill (returns -3 if untrained, matching
// Traveller's untrained penalty). Pass lower-cased skill name, optional speciality.
function getSkillLevelFor(skillName, speciality) {
  const skills = (character && character.skills) || [];
  const lname = (skillName || '').toLowerCase();
  const lspec = speciality ? speciality.toLowerCase() : null;
  for (const s of skills) {
    if (s.name.toLowerCase() !== lname) continue;
    if (lspec && s.speciality && s.speciality.toLowerCase() === lspec) return s.level;
    if (!lspec) return Math.max(s.level || 0, 0);
  }
  // Check if it's a characteristic name (STR/DEX/etc.) — use the stat DM.
  const CHAR_KEYS = ['STR','DEX','END','INT','EDU','SOC'];
  if (CHAR_KEYS.includes(skillName.toUpperCase())) {
    const stat = character?.characteristics?.[skillName.toUpperCase()] ?? 7;
    return charDM(stat);
  }
  return -3; // untrained
}

// Standard Traveller characteristic DM.
function charDM(val) {
  if (val == null || isNaN(val)) return 0;
  if (val <= 0) return -3;
  if (val <= 2) return -2;
  if (val <= 5) return -1;
  if (val <= 8) return 0;
  if (val <= 11) return 1;
  if (val <= 14) return 2;
  return 3;
}

// Roll 2D + mods and return {total, dice:[a,b], mod}.
function rollD2(mod) {
  const a = 1 + Math.floor(Math.random() * 6);
  const b = 1 + Math.floor(Math.random() * 6);
  return { dice: [a, b], mod: mod || 0, total: a + b + (mod || 0) };
}

function getCharacterSkillNames() {
  // Flat list of the character's current skills as display strings.
  // Parent skill with no speciality → bare name. With specialities → one
  // entry per speciality ("Tactics (military)").
  if (!character || !Array.isArray(character.skills)) return [];
  const out = [];
  const seen = new Set();
  for (const s of character.skills) {
    if (!s || !s.name) continue;
    if (Array.isArray(s.specialities) && s.specialities.length > 0) {
      for (const spec of s.specialities) {
        const display = `${s.name} (${spec.name})`;
        if (!seen.has(display)) { seen.add(display); out.push(display); }
      }
    } else {
      if (!seen.has(s.name)) { seen.add(s.name); out.push(s.name); }
    }
  }
  return out.sort();
}

function getCareerTableSkills(careerKey, tableNames) {
  // Read skill entries from a career's skill_tables and return a dedup'd list.
  // careerKey: 'navy', 'marine', etc. tableNames: ['service_skills', ...].
  const careerData = (window.__careerData && window.__careerData[careerKey]) || null;
  const tables = careerData && careerData.skill_tables;
  if (!tables) return [];
  const out = [];
  const seen = new Set();
  for (const t of tableNames) {
    const table = tables[t];
    if (!table) continue;
    for (const k of ['1', '2', '3', '4', '5', '6']) {
      const v = table[k];
      if (v && typeof v === 'string' && !seen.has(v)) {
        seen.add(v);
        out.push(v);
      }
    }
  }
  return out;
}

function resolveWildcardSkillOptions(wildcard, careerKey) {
  // Turn a wildcard descriptor into a concrete chip list.
  if (!wildcard) return null;
  switch (wildcard.type) {
    case 'already-have':
      return getCharacterSkillNames();
    case 'service':
      return getCareerTableSkills(careerKey, ['service_skills']);
    case 'service-or-advanced':
      return getCareerTableSkills(careerKey, ['service_skills', 'advanced_education']);
    case 'officer-or-advanced':
      return getCareerTableSkills(careerKey, ['officer', 'advanced_education']);
    case 'science':
      return ['Science (archaic)', 'Science (biology)', 'Science (chemistry)',
              'Science (cosmology)', 'Science (cybernetics)', 'Science (economics)',
              'Science (genetics)', 'Science (history)', 'Science (linguistics)',
              'Science (philosophy)', 'Science (physics)', 'Science (planetology)',
              'Science (psionicology)', 'Science (psychology)', 'Science (robotics)',
              'Science (sophontology)', 'Science (xenology)'];
    case 'free':
      return ALL_TRAVELLER_SKILLS.slice();
    default:
      return null;
  }
}

function parseEventDmAlternative(text) {
  // Detect "or DM+N to your next/an Advancement roll" as an alternative reward.
  // Returns { dm: 4, target: 'advancement' } or null.
  if (!text) return null;
  const m = text.match(/or\s+DM\s*([+-]?\d+)\s+to\s+(?:(?:your\s+)?next\s+|an?\s+)(Advancement|Qualification|Survival|Promotion)\s+roll/i);
  if (!m) return null;
  return { dm: parseInt(m[1], 10), target: m[2].toLowerCase() };
}

function rollAssocQuantity(expr) {
  // Resolve a Traveller-style dice expression to a count. D3 = 1-3, D6 = 1-6,
  // "1D" / "2D" = 1-6 / 2-12 (implicit d6), "NDN" = N dice of given sides,
  // bare integer = literal count.
  const e = String(expr || '').toUpperCase().trim();
  if (e === 'D3') return 1 + Math.floor(Math.random() * 3);
  if (e === 'D6') return 1 + Math.floor(Math.random() * 6);
  const ndm = e.match(/^(\d)D(\d?)$/);
  if (ndm) {
    const count = parseInt(ndm[1], 10);
    const sides = ndm[2] ? parseInt(ndm[2], 10) : 6;
    let total = 0;
    for (let i = 0; i < count; i++) total += 1 + Math.floor(Math.random() * sides);
    return total;
  }
  const n = parseInt(e, 10);
  return isNaN(n) ? 1 : Math.max(1, n);
}

function parseEventAssociateOps(text) {
  // Detect associate mutations in an event. Returns an array of ops, each
  // shaped:
  //   { type:'add',      kinds:['ally']                }           // unambiguous
  //   { type:'add',      kinds:['rival','enemy']       }           // "Gain a Rival or Enemy"
  //   { type:'add',      kinds:['contact','ally']      }           // "Gain a Contact or Ally"
  //   { type:'betrayal', fromKinds:['contact','ally'],
  //                      toKinds:['rival','enemy']     }           // life-event #8
  // Returns [] if no associate mechanics are present. Safe to call on any
  // event text.
  if (!text) return [];
  const ops = [];
  const raw = String(text);

  // Betrayal (life event #8) — highest priority since it mentions both.
  //   "If you have any Contacts or Allies, convert one into a Rival or Enemy.
  //    Otherwise, gain a Rival or an Enemy."
  if (/If you have any Contacts? or Allies?.*?convert one into a Rival or (?:an? )?Enemy/i.test(raw)) {
    ops.push({
      type: 'betrayal',
      fromKinds: ['contact', 'ally'],
      toKinds: ['rival', 'enemy'],
    });
    return ops;  // Betrayal covers the whole event — don't also match the "Otherwise, gain" clause.
  }

  // Pair-disjunction "Gain a Rival or Enemy" / "Gain a Contact or Ally" /
  // "Gain a Rival or an Enemy". The second article is optional because the
  // rulebook wording varies.
  const pairRe = /gain\s+(?:a|an|one)\s+(?:new\s+|another\s+)?(contact|ally|rival|enemy)\s+or\s+(?:a\s+|an\s+|one\s+)?(contact|ally|rival|enemy)/gi;
  let m;
  const consumedRanges = [];
  while ((m = pairRe.exec(raw)) !== null) {
    ops.push({
      type: 'add',
      kinds: [m[1].toLowerCase(), m[2].toLowerCase()],
    });
    consumedRanges.push([m.index, m.index + m[0].length]);
  }

  // Dice-quantity grants: "Gain D3 Contacts" (agent[5]), "Gain 1D Contacts and
  // D3 Enemies" (scout[3]). We accept D3, D6, 1D, 2D, NDN and bare integers.
  // Each match becomes a 'quantity' op; the render layer rolls the die once,
  // caches the result on lr.assocQtyRolls, and expands to N individual add ops.
  const qtyKindMap = {
    contact: 'contact', contacts: 'contact',
    ally: 'ally', allies: 'ally',
    rival: 'rival', rivals: 'rival',
    enemy: 'enemy', enemies: 'enemy',
  };
  const qtyRe = /(?:gain|and)\s+(d3|d6|\dd\d?|[2-6])\s+(contacts?|allies|rivals?|enemies|enemy)\b/gi;
  while ((m = qtyRe.exec(raw)) !== null) {
    const inPrior = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
    if (inPrior) continue;
    const diceExpr = m[1].toUpperCase();
    const kind = qtyKindMap[m[2].toLowerCase()];
    if (!kind) continue;
    ops.push({ type: 'quantity', kind, diceExpr });
    consumedRanges.push([m.index, m.index + m[0].length]);
  }

  // Single-kind "Gain a Contact" / "Gain an Ally" / "Gain a Rival" / "Gain an Enemy".
  // Allows filler like "new" ("You gain a new Contact.") and trailing
  // qualifiers ("Gain an Ally in the Imperium"). Skips offsets already
  // consumed by the pair regex.
  const singleRe = /gain\s+(?:a|an|one)\s+(?:new\s+|another\s+)?(contact|ally|rival|enemy)(?!\s+or\s+(?:a\s+|an\s+|one\s+)?(?:contact|ally|rival|enemy))/gi;
  while ((m = singleRe.exec(raw)) !== null) {
    const inPair = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
    if (inPair) continue;
    ops.push({ type: 'add', kinds: [m[1].toLowerCase()] });
  }

  // "as well as a Rival and an Ally" (noble[10]) — trailing grant after a
  // primary skill-level gain. Matches the first associate after the
  // connector; the subsequent "and a/an Y" is picked up by the conjunction
  // loop below.
  const trailRe = /\bas\s+well\s+as\s+(?:a\s+|an\s+|one\s+)(contact|ally|rival|enemy)\b/gi;
  while ((m = trailRe.exec(raw)) !== null) {
    const inPrior = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
    if (inPrior) continue;
    ops.push({ type: 'add', kinds: [m[1].toLowerCase()] });
    consumedRanges.push([m.index, m.index + m[0].length]);
  }

  // Conjunction pickup: "... and an Enemy" / "... and a Rival" following a
  // prior Gain clause. Covers marine[4] "Gain a Contact (fellow prisoner)
  // and an Enemy" and similar. Only runs if we already parsed something.
  if (ops.length > 0) {
    const andRe = /\band\s+(?:a\s+|an\s+)(contact|ally|rival|enemy)\b/gi;
    while ((m = andRe.exec(raw)) !== null) {
      // Skip if this "and a Contact" already lives inside a pair match
      // (e.g. "Contact or Ally" — we don't want to misread "or" as "and").
      const inPair = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
      if (inPair) continue;
      // Avoid duplicate: if the exact same kind was already added at a
      // nearby offset (within 12 chars), skip.
      ops.push({ type: 'add', kinds: [m[1].toLowerCase()] });
    }
  }

  return ops;
}

function renderEventStep() {
  // Post-roll view with dice + event text
  if (uiState.lastRoll?.type === 'event') {
    const lr = uiState.lastRoll;
    const grants = Array.isArray(lr.dmGrants) ? lr.dmGrants : [];
    const appliedGrants = grants.filter(g => g.applied);
    const pendingGrants = grants.filter(g => !g.applied);

    const appliedHTML = appliedGrants.length ? `
      <div class="dm-applied-box">
        <span class="event-label">Auto-applied DMs</span>
        ${appliedGrants.map(g => `
          <div class="dm-chip applied">DM${g.dm >= 0 ? '+' : ''}${g.dm} → next ${g.target} roll</div>
        `).join('')}
      </div>
    ` : '';

    // Compute picker state early so pendingHTML knows whether DMs appear inside
    // the picker (reversed pattern: DM first, skill alt) or as a dual-DM choice.
    const _eSkillOpts = parseEventSkillOptions(lr.eventText || '');
    const _eWild = !_eSkillOpts ? parseEventWildcardSkill(lr.eventText || '') : null;
    const _eCareerKey = (character?.current_term?.career) || null;
    const _eWildOpts = _eWild ? resolveWildcardSkillOptions(_eWild, _eCareerKey) : null;
    const _eDmAlt = parseEventDmAlternative(lr.eventText || '');
    const _eTransfer = parseEventTransferOffer(lr.eventText || '');
    const _eChosen = lr.eventChoicePath;
    const _ePickerOpts = _eSkillOpts || _eWildOpts;
    const _eShowPicker = !_eChosen && (
      (_ePickerOpts && _ePickerOpts.length > 0) ||
      (_eWild && (_eDmAlt || pendingGrants.length > 0)) ||
      (_eTransfer && !pendingGrants.length)  // transfer alone (no competing DM)
    );
    // DMs embedded as alternatives in the skill picker (prisoner[5] pattern)
    const pendingGrantsInPicker = _eShowPicker && pendingGrants.length > 0 && !_eDmAlt;
    // Competing rewards with no skill picker: DM vs DM, or DM vs transfer
    const showDualChoice = !_eChosen && !_eShowPicker && (
      pendingGrants.length >= 2 ||
      (pendingGrants.length >= 1 && !!_eTransfer)
    );

    const pendingHTML = showDualChoice ? `
      <div class="event-skill-picker">
        <span class="event-label"><strong>PICK ONE</strong></span>
        <div class="skill-picker">
          ${pendingGrants.map(g => `
            <button class="skill-chip dm-alt" data-event-dm="${g.dm}" data-event-dm-target="${escapeHTML(g.target)}">DM${g.dm >= 0 ? '+' : ''}${g.dm} to next ${escapeHTML(g.target)} roll</button>
          `).join('')}
          ${_eTransfer ? `
            <button class="skill-chip dm-alt" data-event-transfer="${escapeHTML(_eTransfer.career_id)}">${
              _eTransfer.career_id === 'any'
                ? 'Transfer to a career of your choice (no qualification roll)'
                : `Transfer to ${escapeHTML(_eTransfer.career_name)} (no qualification roll)`
            }</button>
          ` : ''}
        </div>
      </div>
    ` : (!pendingGrantsInPicker && pendingGrants.length) ? `
      <div class="dm-pending-box">
        <span class="event-label">DM grants (conditional — resolve manually)</span>
        ${pendingGrants.map(g => `
          <div class="dm-chip pending">DM${g.dm >= 0 ? '+' : ''}${g.dm} to ${g.target} roll (if earned)</div>
        `).join('')}
      </div>
    ` : '';

    // Stat bonuses (e.g. entertainer[12] "SOC +1") — auto-applied unconditionally
    // when no conditional markers are present. Surface them so the player can
    // see the characteristic change.
    const statBonuses = Array.isArray(lr.statBonuses) ? lr.statBonuses : [];
    const statAppliedHTML = statBonuses.filter(s => s.applied).length ? `
      <div class="dm-applied-box">
        <span class="event-label">Auto-applied stat changes</span>
        ${statBonuses.filter(s => s.applied).map(s => `
          <div class="dm-chip applied">${s.stat} ${s.from} → ${s.to} (${s.amount >= 0 ? '+' : ''}${s.amount})</div>
        `).join('')}
      </div>
    ` : '';

    // Auto-promotion (event [12]). If the engine bumped rank, show a chip so
    // the player sees it and knows to skip the advancement roll this term.
    const autoProm = lr.autoPromotion || null;
    const autoPromHTML = (autoProm && !autoProm.skipped) ? `
      <div class="dm-applied-box">
        <span class="event-label">Auto-applied promotion</span>
        <div class="dm-chip applied">Rank ${autoProm.from_rank} → ${autoProm.to_rank}${autoProm.rank_title ? ` — ${autoProm.rank_title}` : ''}</div>
        ${autoProm.bonus ? `<div class="dm-chip applied">Rank bonus: ${autoProm.bonus}</div>` : ''}
        <div class="small-hint" style="margin-top:.35rem">No Advancement roll this term — you've already been promoted.</div>
      </div>
    ` : (autoProm && autoProm.skipped ? `
      <div class="dm-applied-box" style="border-color: var(--warning, #ff9); color: var(--warning, #ff9)">
        <span class="event-label">Promotion not applied</span>
        <div class="small-hint">${autoProm.reason === 'rankless_career' ? 'This career has no ranks — treat as "gain a skill instead" per the rulebook.' : autoProm.reason === 'rank_cap' ? `Already at maximum rank (${autoProm.rank}).` : 'Could not auto-promote; apply manually.'}</div>
      </div>
    ` : '');

    // Skill-choice picker — reuse variables computed above for pendingHTML.
    const skillOptions = _eSkillOpts;
    const wildcardSpec = _eWild;
    const wildcardOptions = _eWildOpts;
    const dmAlternative = _eDmAlt;
    const transferOffer = _eTransfer;
    const chosenPath = _eChosen;
    const pickerOptions = _ePickerOpts;
    const wildcardLabel = wildcardSpec ? ({
      'already-have': 'any skill you already have',
      'free': 'any skill of your choice',
      'service': 'any Service Skill',
      'service-or-advanced': 'Service or Advanced Education tables',
      'officer-or-advanced': 'Officer or Advanced Education tables',
      'science': 'any Science specialty',
    }[wildcardSpec.type]) : null;
    const showPicker = _eShowPicker;

    const pickerHTML = showPicker ? `
      <div class="event-skill-picker">
        <span class="event-label">Choose your reward</span>
        ${wildcardLabel ? `<p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>Pick ${escapeHTML(wildcardLabel)}${(pickerOptions && pickerOptions.length) ? '' : ' — none available, take the DM instead'}:</em></p>` : ''}
        <div class="skill-picker">
          ${(pickerOptions || []).map(opt => {
            const display = opt.replace(/\s+\d+\s*$/, '');
            return `<button class="skill-chip" data-event-skill="${escapeHTML(opt)}">+ ${escapeHTML(display)} 1</button>`;
          }).join('')}
          ${dmAlternative ? `
            <button class="skill-chip dm-alt" data-event-dm="${dmAlternative.dm}" data-event-dm-target="${escapeHTML(dmAlternative.target)}">DM${dmAlternative.dm >= 0 ? '+' : ''}${dmAlternative.dm} to next ${escapeHTML(dmAlternative.target)} roll</button>
          ` : ''}
          ${pendingGrantsInPicker ? pendingGrants.map(g =>
            `<button class="skill-chip dm-alt" data-event-dm="${g.dm}" data-event-dm-target="${escapeHTML(g.target)}">DM${g.dm >= 0 ? '+' : ''}${g.dm} to next ${escapeHTML(g.target)} roll</button>`
          ).join('') : ''}
          ${transferOffer ? `
            <button class="skill-chip dm-alt" data-event-transfer="${escapeHTML(transferOffer.career_id)}">${
              transferOffer.career_id === 'any'
                ? `Transfer to a career of your choice (no qualification roll)`
                : `Transfer to ${escapeHTML(transferOffer.career_name)} (no qualification)`
            }</button>
          ` : ''}
        </div>
        <p class="picker-status">Pick one to continue.</p>
      </div>
    ` : '';

    const transferAppliedHTML = lr.eventTransferApplied ? `
      <div class="dm-applied-box">
        <span class="event-label">Transfer accepted</span>
        <div class="dm-chip applied">Transferring to ${escapeHTML(lr.eventTransferApplied)} at term end — no qualification roll.</div>
      </div>
    ` : '';

    // Contested-roll picker: "Roll <Skill> 8+" branches (drifter[6], entertainer[8],
    // navy[3], scholar[9], scout[8]/[9]/[10], rogue[8], prisoner[8]).
    // We offer a button per skill option, and a "Skip — apply manually" fallback.
    const contested = !chosenPath && !lr.eventContestedResolved
      ? parseEventContestedRoll(lr.eventText || '')
      : null;
    // Refuse option (noble[3] duel, noble[8] conspiracy) — only surface alongside
    // a contested roll, since "If you refuse" is always paired with "If you accept, roll ...".
    const refuseOpt = contested && !lr.eventContestedResolved
      ? parseEventRefuseOption(lr.eventText || '')
      : null;
    const refuseChipHTML = refuseOpt ? `<button class="skill-chip dm-alt" data-event-refuse="1" title="${escapeHTML(refuseOpt.consequence)}">Refuse — ${escapeHTML(refuseOpt.consequence)}</button>` : '';
    const contestedHTML = contested ? `
      <div class="event-skill-picker">
        <span class="event-label">Make your check</span>
        <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)">
          <em>Target: ${contested.target}+ — pick which skill to roll:</em>
        </p>
        <div class="skill-picker">
          ${contested.skills.map((sk, i) => {
            const lvl = getSkillLevelFor(sk.name, sk.speciality);
            const lvlStr = lvl >= 0 ? `+${lvl}` : `${lvl}`;
            const label = sk.speciality ? `${sk.name} (${sk.speciality})` : sk.name;
            return `<button class="skill-chip" data-contested-roll="${i}">Roll ${escapeHTML(label)} ${contested.target}+ (your DM ${lvlStr})</button>`;
          }).join('')}
          ${refuseChipHTML}
          <button class="skill-chip dm-alt" data-contested-skip="1">Skip (apply manually)</button>
        </div>
      </div>
    ` : '';

    const contestedResultHTML = lr.eventContestedResolved ? `
      <div class="dm-applied-box">
        <span class="event-label">${lr.eventContestedResolved.success ? 'Success' : 'Failure'}</span>
        <div class="dm-chip applied">Rolled ${escapeHTML(lr.eventContestedResolved.skillLabel)}: 2D [${lr.eventContestedResolved.dice.join(' · ')}] + ${lr.eventContestedResolved.mod >= 0 ? '+' : ''}${lr.eventContestedResolved.mod} = ${lr.eventContestedResolved.total} vs ${lr.eventContestedResolved.target}+</div>
        ${lr.eventContestedResolved.branchText ? `<div class="small-hint" style="margin-top:.35rem"><em>${escapeHTML(lr.eventContestedResolved.branchText)}</em></div>` : ''}
        ${lr.eventContestedResolved.appliedMsgs && lr.eventContestedResolved.appliedMsgs.length ? lr.eventContestedResolved.appliedMsgs.map(m => `<div class="dm-chip applied">${escapeHTML(m)}</div>`).join('') : ''}
      </div>
    ` : '';

    // Skill picker that appears after a successful contested roll whose success
    // branch grants a skill choice (e.g. navy[8], army[8], marine[8]).
    const csr = lr.eventContestedResolved;
    const contestedSkillPickerHTML = (csr && csr.success && csr.pendingSkillPick && !csr.skillChosen) ? (() => {
      const psp = csr.pendingSkillPick;
      const ckCareer = (character && character.current_term && character.current_term.career_id) || null;
      const opts = psp.options || (psp.wildcardSpec ? resolveWildcardSkillOptions(psp.wildcardSpec, ckCareer) : null);
      const wLabel = psp.wildcardSpec ? ({
        'already-have': 'any skill you already have',
        'free': 'any skill of your choice',
        'service': 'any Service Skill',
        'service-or-advanced': 'Service or Advanced Education tables',
        'officer-or-advanced': 'Officer or Advanced Education tables',
        'science': 'any Science specialty',
      }[psp.wildcardSpec.type] || 'a skill') : null;
      if (!opts || !opts.length) return '';
      return `
        <div class="event-skill-picker">
          <span class="event-label">Choose your reward</span>
          ${wLabel ? `<p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>Pick ${escapeHTML(wLabel)}:</em></p>` : ''}
          <div class="skill-picker">
            ${opts.map(opt => { const dispOpt = opt.replace(/\s+\d+\s*$/, ''); return `<button class="skill-chip" data-contested-skill="${escapeHTML(opt)}">+ ${escapeHTML(dispOpt)} 1</button>`; }).join('')}
          </div>
          <p class="picker-status">Pick one to continue.</p>
        </div>
      `;
    })() : '';

    const skillAppliedHTML = lr.eventSkillApplied ? `
      <div class="dm-applied-box">
        <span class="event-label">Skill chosen</span>
        <div class="dm-chip applied">+ ${escapeHTML(lr.eventSkillApplied)}</div>
      </div>
    ` : '';

    const dmChosenHTML = (chosenPath === 'dm' && lr.eventDmApplied) ? `
      <div class="dm-applied-box">
        <span class="event-label">DM chosen</span>
        <div class="dm-chip applied">DM${lr.eventDmApplied.dm >= 0 ? '+' : ''}${lr.eventDmApplied.dm} → next ${escapeHTML(lr.eventDmApplied.target)} roll</div>
      </div>
    ` : '';

    // Associate outcomes (Gain a Contact/Ally/Rival/Enemy, Betrayal conversion,
    // or dice-quantity grants like "Gain D3 Contacts"). One picker per op;
    // resolved ops render as a "Gained ..." chip instead.
    // Quantity ops (D3/1D/etc.) are pre-rolled once and cached on lr so re-
    // renders don't re-roll. Each quantity op then expands into N add ops.
    // When a contested roll (skill check) has been resolved, only parse
    // associates from the relevant branch text. Parsing the full event text
    // would pick up associates from BOTH the success and failure branches,
    // awarding e.g. both a Contact (success) and an Enemy (failure) regardless
    // of the actual outcome. If no contested roll exists, parse the full text.
    const _csr = lr.eventContestedResolved;
    const _assocSourceText = (_csr && _csr.success !== null && _csr.success !== undefined)
      ? (_csr.branchText || '')
      : (lr.eventText || '');
    const rawAssociateOps = parseEventAssociateOps(_assocSourceText);
    if (!Array.isArray(lr.assocQtyRolls)) lr.assocQtyRolls = [];
    const associateOps = [];
    rawAssociateOps.forEach((op, rawIdx) => {
      if (op.type === 'quantity') {
        let n = lr.assocQtyRolls[rawIdx];
        if (n == null || n < 1) {
          n = rollAssocQuantity(op.diceExpr);
          lr.assocQtyRolls[rawIdx] = n;
        }
        for (let i = 0; i < n; i++) {
          associateOps.push({
            type: 'add',
            kinds: [op.kind],
            qtyMeta: { diceExpr: op.diceExpr, rolled: n, slot: i + 1, of: n },
          });
        }
      } else {
        associateOps.push(op);
      }
    });
    const assocDone = Array.isArray(lr.associateOpsDone) ? lr.associateOpsDone : [];
    const pendingAssocOps = associateOps.map((op, idx) => ({ op, idx })).filter(({ idx }) => !assocDone[idx]);

    const assocLabel = (k) => ({contact:'Contact', ally:'Ally', rival:'Rival', enemy:'Enemy'}[k] || k);

    const assocSummaryHTML = assocDone.filter(Boolean).length ? `
      <div class="dm-applied-box">
        <span class="event-label">Associates updated</span>
        ${assocDone.filter(Boolean).map(done => `
          <div class="dm-chip applied">${escapeHTML(done)}</div>
        `).join('')}
      </div>
    ` : '';

    const existingContactsAllies = (character.associates || [])
      .map((a, i) => ({ a, i }))
      .filter(({ a }) => a.kind === 'contact' || a.kind === 'ally');

    const associatePickerHTML = pendingAssocOps.length ? `
      <div class="event-skill-picker associate-picker">
        <span class="event-label">Resolve associate outcome${pendingAssocOps.length > 1 ? 's' : ''}</span>
        ${pendingAssocOps.map(({ op, idx }) => {
          if (op.type === 'add') {
            const qm = op.qtyMeta;
            const prompt = qm
              ? `Gain a ${assocLabel(op.kinds[0])} <span class="assoc-roll-badge">rolled ${qm.diceExpr} = ${qm.rolled} — ${qm.slot} of ${qm.of}</span>`
              : (op.kinds.length > 1
                  ? `Gain a ${op.kinds.map(assocLabel).join(' or ')} — pick one:`
                  : `Gain a ${assocLabel(op.kinds[0])}:`);
            return `
              <div class="assoc-op" data-assoc-op-idx="${idx}">
                <div class="assoc-op-prompt">${prompt}</div>
                <input type="text" class="assoc-desc-input" data-assoc-desc="${idx}" placeholder="Who are they? (name or short note — optional)" />
                <div class="skill-picker">
                  ${op.kinds.map(k => `
                    <button class="skill-chip" data-assoc-add="${idx}" data-assoc-kind="${k}">+ Add ${assocLabel(k)}</button>
                  `).join('')}
                </div>
              </div>
            `;
          }
          if (op.type === 'betrayal') {
            const hasAny = existingContactsAllies.length > 0;
            return `
              <div class="assoc-op" data-assoc-op-idx="${idx}">
                <div class="assoc-op-prompt">Betrayal — ${hasAny
                  ? `convert an existing Contact or Ally into a Rival or Enemy:`
                  : `no Contacts or Allies to convert — gain a Rival or Enemy instead:`}</div>
                ${hasAny ? `
                  <div class="assoc-convert-list">
                    ${existingContactsAllies.map(({ a, i }) => `
                      <div class="assoc-row">
                        <span class="assoc-label assoc-kind-${a.kind}">[${assocLabel(a.kind)}]</span>
                        <span class="assoc-desc">${escapeHTML(a.description || '(no description)')}</span>
                        <span class="skill-picker inline">
                          <button class="skill-chip danger" data-assoc-convert="${idx}" data-assoc-index="${i}" data-assoc-to="rival">→ Rival</button>
                          <button class="skill-chip danger" data-assoc-convert="${idx}" data-assoc-index="${i}" data-assoc-to="enemy">→ Enemy</button>
                        </span>
                      </div>
                    `).join('')}
                  </div>
                  <div class="assoc-op-prompt" style="margin-top:8px">…or instead, add a new one:</div>
                ` : ''}
                <input type="text" class="assoc-desc-input" data-assoc-desc="${idx}" placeholder="Who are they? (name or short note — optional)" />
                <div class="skill-picker">
                  <button class="skill-chip" data-assoc-add="${idx}" data-assoc-kind="rival">+ Add Rival</button>
                  <button class="skill-chip" data-assoc-add="${idx}" data-assoc-kind="enemy">+ Add Enemy</button>
                </div>
              </div>
            `;
          }
          return '';
        }).join('')}
        <p class="picker-status">Resolve each associate outcome to continue.</p>
      </div>
    ` : '';

    // Mishap-forcing events (e.g. "Disaster! Roll on the Mishap Table, but you
    // are not ejected from this career.") route the player into the mishap
    // table inline. If the text says "not ejected", they continue the career
    // after the mishap resolves; otherwise the normal end-career flow applies.
    // forcesMishap: the event involves a mishap-table roll, BUT only when there
    // is no contested roll that already succeeded. If the player passed the
    // Electronics check (or similar), the "If you fail, roll on the Mishap Table"
    // clause does NOT apply.
    const rawForcesMishap = /Roll on the Mishap Table/i.test(lr.eventText || '');
    const contestedSucceededForMishap = lr.eventContestedResolved && lr.eventContestedResolved.success === true;
    const forcesMishap = rawForcesMishap && !contestedSucceededForMishap;
    const stayInCareer = /not\s+ejected/i.test(lr.eventText || '');
    const pendingMishapRoll = forcesMishap && !lr.mishapFromEvent;
    const mishapRolledHTML = (forcesMishap && lr.mishapFromEvent) ? `
      <div class="mishap-box">
        <span class="event-label">Mishap [1D=${lr.mishapFromEvent.total ?? '?'}]</span>
        ${escapeHTML(lr.mishapFromEvent.text || '')}
        ${stayInCareer ? `
          <p class="empty" style="margin-top:8px;color:var(--amber-dim)"><em>You are not ejected from this career — keep going.</em></p>
        ` : ''}
      </div>
    ` : '';

    // Entertainer event 5: two-stage associate picker (type + person category).
    const isEntertainerEv5 = /Contact, Ally, Rival or Enemy \(your choice\)/i.test(lr.eventText || '');
    const entertainerAssocHTML = (isEntertainerEv5 && !lr.entertainerAssocDone) ? (() => {
      const stage1 = lr.entertainerAssocType || null;
      const stage2 = lr.entertainerPersonType || null;
      if (!stage1) return `
        <div class="event-skill-picker">
          <span class="event-label">What kind of relationship? (step 1 of 2)</span>
          <div class="skill-picker">
            ${['contact','ally','rival','enemy'].map(k =>
              `<button class="skill-chip" data-ent-assoc-type="${k}">${k.charAt(0).toUpperCase()+k.slice(1)}</button>`
            ).join('')}
          </div>
        </div>`;
      if (!stage2) return `
        <div class="event-skill-picker">
          <span class="event-label">Who are they? (step 2 of 2 — ${stage1})</span>
          <div class="skill-picker">
            ${['Celebrity','Noble','Criminal'].map(p =>
              `<button class="skill-chip" data-ent-assoc-person="${p}">${p}</button>`
            ).join('')}
          </div>
        </div>`;
      return `
        <div class="dm-applied-box">
          <span class="event-label">Ready to confirm</span>
          <div class="dm-chip applied">${stage1.charAt(0).toUpperCase()+stage1.slice(1)}: ${stage2} — Entertainer event</div>
          <div class="skill-picker" style="margin-top:6px">
            <button class="skill-chip" id="btn-ent-assoc-confirm">CONFIRM</button>
          </div>
        </div>`;
    })() : (isEntertainerEv5 && lr.entertainerAssocDone) ? `
      <div class="dm-applied-box">
        <span class="event-label">Associate added</span>
        <div class="dm-chip applied">${escapeHTML(lr.entertainerAssocDone)}</div>
      </div>` : '';

    // Citizen event 8: retroactive survival check warning.
    const citizenEv8HTML = lr.citizenEv8SurvivalFailed ? `
      <div class="mishap-box">
        <span class="event-label">Retroactive Survival Failure</span>
        <p style="margin:4px 0">DM-2 to your survival roll would have caused a failure. You must resolve a Mishap instead of continuing the event.</p>
        <div class="phase-actions" style="margin-top:8px">
          <button class="btn danger" id="btn-citizen-ev8-mishap">RESOLVE MISHAP INSTEAD →</button>
        </div>
      </div>` : '';

    // Prisoner event 7: parole button after successful contested roll.
    const prisonerParoleHTML = lr.prisonerParoleGranted && !lr.prisonerParoleTaken ? `
      <div class="dm-applied-box">
        <span class="event-label">Parole Granted</span>
        <p style="margin:4px 0 8px">You leave this career at the end of the term with no penalty.</p>
        <button class="btn primary" id="btn-prisoner-parole">ACCEPT PAROLE — LEAVE CAREER →</button>
      </div>` : '';

    // Scout event 2: show ban confirmation after failure.
    const scoutBanHTML = lr.scoutBanned ? `
      <div class="dm-applied-box" style="border-color:var(--danger)">
        <span class="event-label" style="color:var(--danger)">Re-enlistment Banned</span>
        <div class="dm-chip applied">SCOUT career removed from future options</div>
      </div>` : '';

    const entertainerPending = isEntertainerEv5 && !lr.entertainerAssocDone;
    const citizenMishapPending = !!lr.citizenEv8SurvivalFailed;

    const gateAdvance = !!(showPicker && !chosenPath) || pendingMishapRoll || pendingAssocOps.length > 0
      || !!(csr && csr.success && csr.pendingSkillPick && !csr.skillChosen)
      || entertainerPending || citizenMishapPending;

    // Action row varies by what's happening:
    // - Pending forced mishap roll: show ROLL MISHAP + skip
    // - Forced mishap already rolled, career ends: show END CAREER
    // - Citizen ev8 survival failed: show mishap button (handled inline above)
    // - Normal flow: show ATTEMPT/SKIP advancement
    const actionsHTML = pendingMishapRoll ? `
      <button class="btn danger" id="btn-event-forced-mishap">ROLL ON MISHAP TABLE →</button>
      <button class="btn" id="btn-skip-advance">SKIP ADVANCEMENT</button>
    ` : (forcesMishap && lr.mishapFromEvent && !stayInCareer) ? `
      <button class="btn danger" id="btn-post-mishap">END CAREER →</button>
    ` : `
      <button class="btn primary" id="btn-post-event"${gateAdvance ? ' disabled' : ''}>ATTEMPT ADVANCEMENT →</button>
      <button class="btn" id="btn-skip-advance">SKIP ADVANCEMENT</button>
    `;

    return `
      <div class="stage-content">
        <div class="phase-label">Event Roll</div>
        <h2 class="phase-title">Something Happened</h2>
        ${rollReadoutHTML(lr.data, { label: '2D', showTarget: false })}
        <div class="event-box">
          <span class="event-label">Event [2D=${lr.data?.total ?? '?'}]</span>
          ${escapeHTML(lr.eventText || '')}
        </div>
        ${appliedHTML}
        ${pendingHTML}
        ${statAppliedHTML}
        ${autoPromHTML}
        ${pickerHTML}
        ${contestedHTML}
        ${contestedResultHTML}
        ${contestedSkillPickerHTML}
        ${skillAppliedHTML}
        ${dmChosenHTML}
        ${transferAppliedHTML}
        ${associatePickerHTML}
        ${assocSummaryHTML}
        ${mishapRolledHTML}
        ${(() => {
          // Agent event 8: cross-career roll on Rogue or Citizen event/mishap table
          if (!(lr.eventText || '').includes('Rogue or Citizen')) return '';
          if (!lr.eventContestedResolved) return '';  // wait for contested roll first
          const succeeded = lr.eventContestedResolved.success;
          const tbl = succeeded ? 'event' : 'mishap';
          if (lr.crossCareerResult) {
            return `
              <div class="event-box" style="margin-top:12px">
                <span class="event-label">${escapeHTML(lr.crossCareerResult.career_name)} ${tbl === 'event' ? 'Event' : 'Mishap'} [${tbl === 'event' ? '2D' : '1D'}=${lr.crossCareerResult.roll?.total ?? '?'}]</span>
                ${escapeHTML(lr.crossCareerResult.text || '')}
              </div>`;
          }
          return `
            <div class="event-box" style="margin-top:12px">
              <p class="phase-body"><strong>Roll on which career's ${tbl} table?</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-cross-career-rogue">ROGUE</button>
                <button class="btn" id="btn-cross-career-citizen">CITIZEN</button>
              </div>
            </div>`;
        })()}
        ${entertainerAssocHTML}
        ${citizenEv8HTML}
        ${prisonerParoleHTML}
        ${scoutBanHTML}
        ${showPicker || forcesMishap || associateOps.length || (autoProm && !autoProm.skipped) || isEntertainerEv5 ? '' : `<p class="phase-body empty"><em>Apply any resulting benefits manually to your notes — only "DM+N to next X roll" grants and stat changes are auto-applied.</em></p>`}
        <div class="phase-actions">
          ${actionsHTML}
        </div>
      </div>
    `;
  }

  return `
    <div class="stage-content">
      <div class="phase-label">Event Table · 2D Roll</div>
      <h2 class="phase-title">What Happened This Term?</h2>
      <p class="phase-body">Roll 2D on the Events table. Could be anything from an ambush to a promotion.</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-event">ROLL EVENT</button>
      </div>
    </div>
  `;
}

function renderMishapStep() {
  if (uiState.lastRoll?.type === 'mishap') {
    const lr = uiState.lastRoll;

    // ---- Frozen Watch: character stays in service, continue to next term ----
    if (lr.frozenWatch) {
      return `
        <div class="stage-content">
          <div class="phase-label">Mishap [1D=${lr.data?.total ?? '?'}] — FROZEN WATCH</div>
          <h2 class="phase-title">Frozen Watch</h2>
          ${rollReadoutHTML(lr.data, { label: '1D', showTarget: false })}
          <div class="mishap-box">
            <span class="event-label">Mishap [1D=2] — Frozen Watch</span>
            ${escapeHTML(lr.mishapText || '')}
          </div>
          <div class="event-box" style="margin-top:12px;border-color:var(--accent)">
            <span class="event-label" style="color:var(--accent)">STAYING IN SERVICE</span>
            You are not ejected from the Confederation Navy. No skill or advancement roll
            this term. You may automatically re-enlist next term.
          </div>
          <div class="phase-actions" style="margin-top:16px">
            <button class="btn primary" id="btn-frozen-watch-continue">CONTINUE IN SERVICE →</button>
          </div>
        </div>
      `;
    }

    const pending = character.pending_career_mishap_choice;
    const injPending = character.pending_injury_choice;
    const statDescs = { STR: 'Strength', DEX: 'Dexterity', END: 'Endurance', INT: 'Intellect', EDU: 'Education', SOC: 'Social' };

    // Auto-applied chips
    let autoHtml = '';
    if (lr.autoApplied && lr.autoApplied.length) {
      const chips = lr.autoApplied.map(a => `<span class="skill-chip dm-chip">${escapeHTML(a)}</span>`).join('');
      autoHtml = `<div class="dm-applied-box" style="margin-top:10px">${chips}</div>`;
    }

    // Injury data box (from auto-resolved injury effect)
    let injDataHtml = '';
    if (lr.injuryTitle) {
      const injRollLabel = lr.injuryRoll != null ? ` [Injury Table 1D=${lr.injuryRoll}]` : '';
      injDataHtml = `
        <div class="event-box" style="margin-top:12px">
          <span class="event-label">Injury Table${injRollLabel} — ${escapeHTML(lr.injuryTitle)}</span>
          ${escapeHTML(lr.injuryText || '')}
        </div>`;
    }

    // Pending choice UI
    let pendingHtml = '';
    if (pending) {
      const ptype = pending.type;
      const pprompt = pending.prompt || '';

      if (ptype === 'injury_severity_choice') {
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>Choose how to handle this injury:</strong></p>
            <div class="phase-actions" style="margin-top:8px">
              <button class="btn" id="btn-mishap-choice-result2">TAKE RESULT 2 (GRIEVOUS INJURY)</button>
              <button class="btn" id="btn-mishap-choice-roll-twice">ROLL TWICE, TAKE LOWER</button>
            </div>
          </div>`;
      } else if (ptype === 'stat_choice') {
        const opts = (pending.options || []).map(stat => `
          <button class="card" id="btn-mishap-statchoice-${stat}">
            <div class="card-title">${stat} — ${statDescs[stat] || stat}</div>
            <div class="card-meta">Current: ${character.characteristics[stat] ?? '?'}</div>
            <div class="card-desc">Reduce by ${Math.abs(pending.amount || 1)}</div>
          </button>`).join('');
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
            <div class="card-grid">${opts}</div>
          </div>`;
      } else if (ptype === 'skill_choice') {
        const opts = (pending.options || []).map(sk => `
          <button class="btn" id="btn-mishap-skillchoice-${escapeHTML(sk)}">${escapeHTML(sk)}</button>`).join('');
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
            <div class="phase-actions" style="margin-top:8px">${opts}</div>
          </div>`;
      } else if (ptype === 'free_skill_choice') {
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
            <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
              <input type="text" id="input-mishap-freeskill" placeholder="Skill name…" style="flex:1;padding:6px 10px;background:var(--surface2);border:1px solid var(--amber-dim);color:var(--text);border-radius:4px"/>
              <button class="btn" id="btn-mishap-freeskill-confirm">CONFIRM</button>
            </div>
          </div>`;
      } else if (ptype === 'pending_choice') {
        const pid = pending.id || '';
        if (pid === 'mishap_deal') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-deal-accept">ACCEPT DEAL</button>
                <button class="btn danger" id="btn-mishap-deal-refuse">REFUSE — FIGHT BACK</button>
              </div>
            </div>`;
        } else if (pid === 'army_join_cooperate') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-armyjoin-join">JOIN THEIR RING</button>
                <button class="btn" id="btn-mishap-armyjoin-cooperate">CO-OPERATE WITH POLICE</button>
              </div>
            </div>`;
        } else if (pid === 'solsec_blame') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-blame-pin">PIN BLAME ON A COLLEAGUE</button>
                <button class="btn danger" id="btn-mishap-blame-fall">TAKE THE FALL</button>
              </div>
            </div>`;
        } else if (pid === 'solsec_expose') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-expose-yes">EXPOSE THE TRAITOR</button>
                <button class="btn danger" id="btn-mishap-expose-no">STAY QUIET</button>
              </div>
            </div>`;
        } else if (pid === 'party_denounce') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-denounce-yes">DENOUNCE PATRON</button>
                <button class="btn danger" id="btn-mishap-denounce-no">STAY SILENT</button>
              </div>
            </div>`;
        } else if (pid === 'solsec_interrogation') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn danger" id="btn-mishap-interrogation-submit">SUBMIT TO INTERROGATION</button>
                <button class="btn" id="btn-mishap-interrogation-refuse">REFUSE — ROLL END 8+</button>
              </div>
            </div>`;
        } else if (pid === 'mishap_victim') {
          const opts = (pending.options || []);
          if (opts.length === 0) {
            pendingHtml = `
              <div class="event-box" style="margin-top:14px">
                <p class="phase-body"><em>No contacts or allies to target — mishap effect skipped.</em></p>
                <div class="phase-actions" style="margin-top:8px">
                  <button class="btn" id="btn-mishap-victim-skip">CONTINUE</button>
                </div>
              </div>`;
          } else {
            const btns = opts.slice(0, 5).map(o => `
              <button class="btn" id="btn-mishap-victim-${o.associate_index}"
                data-assoc-idx="${o.associate_index}">${escapeHTML(o.label)}</button>`).join('');
            pendingHtml = `
              <div class="event-box" style="margin-top:14px">
                <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
                <div class="phase-actions" style="margin-top:8px;flex-direction:column;align-items:flex-start">${btns}</div>
              </div>`;
          }
        }
      } else if (ptype === 'skill_check') {
        const skills = (pending.skills || []).map(s => `
          <button class="btn" id="btn-mishap-skillcheck-${escapeHTML(s.name)}"
            data-skill="${escapeHTML(s.name)}">${escapeHTML(s.name)}</button>`).join('');
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
            <p style="font-size:11px;color:var(--amber-dim)">Choose the skill to roll with (2D + skill DM vs ${pending.target || 8}+).</p>
            <div class="phase-actions" style="margin-top:8px">${skills}</div>
          </div>`;
      }
    }

    // Skill check result (if stored after resolve)
    let skillCheckHtml = '';
    if (lr.skillCheckResult) {
      const sc = lr.skillCheckResult;
      skillCheckHtml = `
        <div class="event-box" style="margin-top:12px">
          <span class="event-label">Skill Check — ${escapeHTML(sc.skill)}</span>
          2D=${sc.raw_2d}, DM${sc.dm >= 0 ? '+' : ''}${sc.dm} = <strong>${sc.total}</strong> vs ${sc.target}+ —
          <strong style="color:${sc.passed ? 'var(--success,#4caf50)' : 'var(--danger)'}">${sc.passed ? 'PASS' : 'FAIL'}${sc.nat2 ? ' (Natural 2!)' : ''}</strong>
        </div>`;
    }

    // Injury stat picker (pending_injury_choice)
    let injPickerHtml = '';
    if (injPending) {
      const inj = injPending;
      const choices = inj.choices || ['STR', 'DEX', 'END'];
      const injTableRoll = lr.injuryRoll != null ? ` (Injury Table 1D=${lr.injuryRoll})` : '';
      const cards = choices.map(stat => `
        <button class="card" id="btn-career-injury-stat-${stat}">
          <div class="card-title">${stat} — ${statDescs[stat] || stat}</div>
          <div class="card-meta">Current: ${character.characteristics[stat] ?? '?'}</div>
          <div class="card-desc">Reduce by ${inj.damage_to_chosen}${inj.auto_reduce_others ? ` (others: -${inj.auto_reduce_others} each)` : ''}. Gross debt: Cr${((inj.damage_to_chosen || 0) * 5000).toLocaleString()} (career may cover a portion).</div>
        </button>`).join('');
      injPickerHtml = `
        <p class="phase-body" style="margin-top:14px"><strong>${escapeHTML(inj.prompt || 'Choose which stat takes the damage.')}${injTableRoll}</strong></p>
        <p style="font-size:11px;color:var(--amber-dim)">Cr 5,000 per point lost — a 2D+Rank roll determines how much your career covers.</p>
        <div class="card-grid">${cards}</div>`;
    }

    const canEnd = !pending && !injPending;

    return `
      <div class="stage-content">
        <div class="phase-label">Mishap</div>
        <h2 class="phase-title">What Went Wrong</h2>
        ${rollReadoutHTML(lr.data, { label: '1D', showTarget: false })}
        <div class="mishap-box">
          <span class="event-label">Mishap [1D=${lr.data?.total ?? '?'}]</span>
          ${escapeHTML(lr.mishapText || '')}
          ${(!lr.injuryPending && !character.pending_career_mishap_choice && !(lr.autoApplied && lr.autoApplied.length)) ? `
            <p class="small-hint" style="margin-top:8px;color:var(--muted)">Career ends — no further mechanical effects apply.</p>
          ` : ''}
        </div>
        ${autoHtml}
        ${injDataHtml}
        ${pendingHtml}
        ${skillCheckHtml}
        ${injPickerHtml}
        <div class="phase-actions" style="margin-top:16px">
          ${canEnd ? `<button class="btn danger" id="btn-post-mishap">END CAREER →</button>` : ''}
        </div>
      </div>
    `;
  }

  return `
    <div class="stage-content">
      <div class="phase-label">Mishap Table · 1D Roll</div>
      <h2 class="phase-title">You Failed to Survive</h2>
      <p class="phase-body">A mishap ends your career. Roll 1D to see what went wrong.</p>
      <div class="phase-actions">
        <button class="btn danger" id="btn-mishap">ROLL MISHAP</button>
      </div>
    </div>
  `;
}

function renderAdvanceStep() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const assignment = career.assignments[term.assignment_id];
  const a = assignment.advancement;
  const dm = charDM(character.characteristics[a.characteristic]);

  // Post-roll view — show dice readout
  if (uiState.lastRoll?.type === 'advance') {
    const lr = uiState.lastRoll;
    const advanced = lr.outcome === 'pass';
    return `
      <div class="stage-content">
        <div class="phase-label">Advancement — ${advanced ? 'Promoted' : 'No Change'}</div>
        <h2 class="phase-title">${advanced
          ? `Promoted to Rank ${lr.newRank}${lr.newRankTitle ? ` — ${lr.newRankTitle}` : ''}`
          : 'No Promotion This Term'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${a.characteristic} ${a.target}+` })}
        <p class="phase-body">You've completed Term ${term.overall_term_number}. Continue in this career or muster out?</p>
        ${character.total_terms + 1 >= 4 ? `
          <p class="phase-body" style="color:var(--danger);font-style:italic">
            ⚠ Ending this next term will trigger an Aging roll.
          </p>
        ` : ''}
        <div class="phase-actions">
          <button class="btn primary" id="btn-next-term">ANOTHER TERM →</button>
          <button class="btn" id="btn-leave-career">MUSTER OUT</button>
        </div>
      </div>
    `;
  }

  if (term.advanced === null || term.advanced === undefined) {
    // Not yet rolled
    return `
      <div class="stage-content">
        <div class="phase-label">Advancement · 2D Roll</div>
        <h2 class="phase-title">Promotion Check</h2>
        <p class="phase-subtitle">${a.characteristic} ${a.target}+ (your DM is ${formatDM(dm)})</p>
        <p class="phase-body">A successful roll promotes you by one rank. If you fail, your career continues — you just don't advance this term.</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-advance">ROLL FOR PROMOTION</button>
          <button class="btn" id="btn-skip-advance">SKIP</button>
        </div>
      </div>
    `;
  }

  // Already rolled (state restored from a prior session, no fresh roll) — show terminal view
  return `
    <div class="stage-content">
      <div class="phase-label">Term Complete</div>
      <h2 class="phase-title">${term.advanced ? `Promoted to Rank ${term.rank}` : 'No Promotion'}</h2>
      ${term.advanced && term.rank_title ? `<p class="phase-subtitle">${term.rank_title}</p>` : ''}
      <p class="phase-body">You've completed Term ${term.overall_term_number}. Continue in this career or leave?</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-next-term">ANOTHER TERM →</button>
        <button class="btn" id="btn-leave-career">MUSTER OUT</button>
      </div>
    </div>
  `;
}

function renderDecideStep() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);

  return `
    <div class="stage-content">
      <div class="phase-label">Term ${term.overall_term_number} Complete</div>
      <h2 class="phase-title">Continue or Muster Out?</h2>
      <p class="phase-subtitle">You've survived your term. Another four years, or a new chapter?</p>
      <p class="phase-body">${term.advanced
        ? `You advanced to rank <strong>${term.rank}</strong>${term.rank_title ? ` — <strong>${term.rank_title}</strong>` : ''}.`
        : "You didn't advance this term."}</p>
      ${character.total_terms + 1 >= 4 ? `
        <p class="phase-body" style="color:var(--danger);font-style:italic">
          ⚠ Ending this next term will trigger an Aging roll. The older your Traveller, the heavier it hits.
        </p>
      ` : ''}
      <div class="phase-actions">
        <button class="btn primary" id="btn-next-term">ANOTHER TERM IN ${career.name.toUpperCase()}</button>
        <button class="btn" id="btn-leave-career">MUSTER OUT OF ${career.name.toUpperCase()}</button>
      </div>

      ${character.total_terms + 1 >= 4 ? `
        <div class="anagathics-box">
          <div class="anagathics-header">
            <strong>Anagathics available</strong>
            <span class="empty">Cr200,000 per 4-year term — skips the aging roll</span>
          </div>
          <div class="anagathics-status">
            Banked treatments: <strong>${character.anagathics_purchased_terms}</strong>
            ${character.anagathics_addicted ? ' · <span style="color:var(--danger)">ADDICTED</span>' : ''}
          </div>
          ${character.credits < 200000 ? `
            <p style="font-size:11px;color:var(--text-dim);margin:4px 0">
              Insufficient credits (Cr${character.credits.toLocaleString()} available) — shortfall added to medical debt.
            </p>` : ''}
          <div class="phase-actions" style="margin-top:6px">
            <button class="btn ghost" id="btn-buy-anagathics">
              PURCHASE (Cr200,000)
            </button>
          </div>
        </div>
      ` : ''}
    </div>
  `;
}

// ============================================================
// PHASE 5: Mustering Out
// ============================================================

function renderMusterPhase() {
  const careers = character.completed_careers;
  const rolls = character.pending_benefit_rolls;
  const cashRolled = character.cash_rolls_used;

  // Post-roll view: show dice readout + what was gained, then wait for "CONTINUE"
  if (uiState.lastRoll?.type === 'muster') {
    const lr = uiState.lastRoll;
    const colLabel = lr.column === 'cash' ? 'Cash Roll' : 'Benefit Roll';
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <div class="phase-label">${colLabel} — ${lr.careerName || lr.careerId}</div>
        <h2 class="phase-title">${lr.column === 'cash' ? `Gained ${lr.result}` : `Benefit: ${lr.result}`}</h2>
        ${rollReadoutHTML(lr.data, { label: `${colLabel} (1D)`, showTarget: false })}
        <p class="phase-body">${lr.remaining_rolls > 0
          ? `${lr.remaining_rolls} benefit roll${lr.remaining_rolls === 1 ? '' : 's'} remaining.`
          : `All benefits claimed.`}</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-muster">CONTINUE →</button>
        </div>
      </div>
    `;
  }

  if (rolls === 0) {
    const pensionNote = character.pension_per_year > 0
      ? `<div style="margin-top:14px;padding:10px 14px;border:1px solid var(--amber-dim);border-radius:6px">
           <span style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">RETIREMENT PENSION</span>
           <div style="font-size:18px;font-family:var(--font-mono);color:var(--accent);margin-top:4px">
             Cr${character.pension_per_year.toLocaleString()}/year
           </div>
           <p style="font-size:11px;color:var(--text-dim);margin:4px 0 0">
             Earned after ${character.total_terms} terms of service.
           </p>
         </div>` : '';
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <h2 class="phase-title">All Benefits Claimed</h2>
        <p class="phase-body">You've rolled all your mustering-out benefits. Your Traveller is ready.</p>
        ${pensionNote}
        <div class="phase-actions" style="margin-top:16px">
          <button class="btn primary" id="btn-finalize">FINALIZE CHARACTER →</button>
        </div>
      </div>
    `;
  }

  const careerPicker = careers.map(c => {
    const careerDef = CAREERS.find(x => x.id === c.career_id);
    const hasTable = careerDef?.mustering_out && Object.keys(careerDef.mustering_out).length > 0;
    return `
      <button class="card ${hasTable ? '' : 'locked'}" data-muster-career="${c.career_id}" ${hasTable ? '' : 'disabled'}>
        <div class="card-title">${careerDef?.name || c.career_id}</div>
        <div class="card-meta">${c.terms_served} TERMS · RANK ${c.final_rank}</div>
        <div class="card-desc">${hasTable ? 'Mustering-out table encoded. Choose this to roll.' : 'Mustering-out table not yet encoded for this career.'}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
    <div class="stage-content">
      <div class="phase-label">${rolls} Benefit Rolls Remaining · ${cashRolled}/3 Cash Rolls Used</div>
      <h2 class="phase-title">Muster Out</h2>
      <p class="phase-subtitle">Time to collect your severance. Credits, gear, contacts, maybe a ship.</p>

      <p class="phase-body">You have <strong>${rolls}</strong> benefit roll${rolls === 1 ? '' : 's'} to spend. For each, choose a career to roll against, then pick the Cash column or the Benefits column. You can only use the Cash column 3 times total across all careers.</p>

      <h3 style="margin-top:20px;font-family:var(--font-mono);font-size:11px;letter-spacing:0.3em;color:var(--amber-dim);text-transform:uppercase">Pick Career</h3>
      <div class="card-grid">${careerPicker}</div>

      ${uiState.selectedCareer ? `
        ${(character.good_fortune_benefit_dm || 0) > 0 ? `
          <div class="dm-applied-box" style="margin-top:12px">
            <span class="event-label">Good Fortune</span>
            <div class="dm-chip applied">DM+2 token available — click to toggle for your next benefit roll</div>
            <label style="display:flex;align-items:center;gap:8px;margin-top:6px;cursor:pointer">
              <input type="checkbox" id="chk-good-fortune" ${uiState.useGoodFortune ? 'checked' : ''} />
              <span style="font-family:var(--font-mono);font-size:11px;color:var(--amber)">Apply Good Fortune (+2) to next benefit roll</span>
            </label>
          </div>
        ` : ''}
        <div class="phase-actions">
          <button class="btn primary" id="btn-roll-cash" ${cashRolled >= 3 ? 'disabled' : ''}>ROLL CASH (1D)${cashRolled >= 3 ? ' — MAX' : ''}</button>
          <button class="btn" id="btn-roll-benefit">ROLL BENEFIT (1D)${uiState.useGoodFortune ? ' +GOOD FORTUNE' : ''}</button>
        </div>
      ` : ''}
    </div>
  `;
}

function wireMusterPhase() {
  document.querySelectorAll('[data-muster-career]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedCareer = card.dataset.musterCareer;
      renderStage();
    });
  });
  const chkGoodFortune = document.getElementById('chk-good-fortune');
  if (chkGoodFortune) chkGoodFortune.addEventListener('change', () => {
    uiState.useGoodFortune = chkGoodFortune.checked;
    renderStage();
  });
  const btnCash = document.getElementById('btn-roll-cash');
  if (btnCash) {
    btnCash.addEventListener('click', async () => {
      try {
        const careerId = uiState.selectedCareer;
        const careerDef = CAREERS.find(x => x.id === careerId);
        const response = await apiCall('/api/character/muster-out',
          { career_id: careerId, column: 'cash' });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'muster',
          column: 'cash',
          data: response.roll,
          result: response.result,
          remaining_rolls: response.remaining_rolls,
          careerId,
          careerName: careerDef?.name || careerId,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnBenefit = document.getElementById('btn-roll-benefit');
  if (btnBenefit) {
    btnBenefit.addEventListener('click', async () => {
      try {
        const careerId = uiState.selectedCareer;
        const careerDef = CAREERS.find(x => x.id === careerId);
        const useGoodFortune = !!(uiState.useGoodFortune && character.good_fortune_benefit_dm > 0);
        const response = await apiCall('/api/character/muster-out',
          { career_id: careerId, column: 'benefit', use_good_fortune: useGoodFortune });
        await applyResponse(response);
        uiState.useGoodFortune = false;
        uiState.lastRoll = {
          type: 'muster',
          column: 'benefit',
          data: response.roll,
          result: response.result,
          remaining_rolls: response.remaining_rolls,
          good_fortune_used: response.good_fortune_used,
          careerId,
          careerName: careerDef?.name || careerId,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnPostMuster = document.getElementById('btn-post-muster');
  if (btnPostMuster) {
    btnPostMuster.addEventListener('click', () => {
      uiState.lastRoll = null;
      renderStage();
    });
  }
  const btnFinalize = document.getElementById('btn-finalize');
  if (btnFinalize) {
    btnFinalize.addEventListener('click', () => {
      if (!uiState.skillPackageApplied) {
        character.phase = 'skill_package';
      } else {
        character.phase = 'done';
      }
      saveCharacter();
      renderAll();
    });
  }
}

// ============================================================
// PHASE 5b: Skill Package Selection
// ============================================================

function renderSkillPackagePhase() {
  const packages = Object.entries(SKILL_PACKAGES);
  const cards = packages.map(([id, pkg]) => {
    const skillList = (pkg.skills || []).join(', ');
    return `
      <button class="card" data-package-id="${escapeHTML(id)}">
        <div class="card-title">${escapeHTML(pkg.name || id)}</div>
        <div class="card-desc" style="margin-bottom:6px">${escapeHTML(pkg.description || '')}</div>
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--amber-dim)">${escapeHTML(skillList)}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>SKILL PACKAGE</span></div>
    <div class="stage-content">
      <div class="phase-label">Optional · MgT2e p.42</div>
      <h2 class="phase-title">Choose a Skill Package</h2>
      <p class="phase-subtitle">Before your Traveller takes to the stars, select one skill package that reflects the kind of campaign you'll be playing. Each skill is granted at level 1 (or +1 if you already have it).</p>
      <div class="card-grid">${cards}</div>
      <div class="phase-actions" style="margin-top:16px">
        <button class="btn ghost" id="btn-skip-skill-package">SKIP — NO PACKAGE →</button>
      </div>
    </div>
  `;
}

function wireSkillPackagePhase() {
  document.querySelectorAll('[data-package-id]').forEach(card => {
    card.addEventListener('click', async () => {
      const packageId = card.dataset.packageId;
      try {
        const response = await apiCall('/api/character/apply-skill-package', { package_id: packageId });
        await applyResponse(response);
        uiState.skillPackageApplied = true;
        character.phase = 'done';
        saveCharacter();
        renderAll();
      } catch (e) {
        alert(e.message || 'Could not apply skill package.');
      }
    });
  });

  const btnSkip = document.getElementById('btn-skip-skill-package');
  if (btnSkip) {
    btnSkip.addEventListener('click', () => {
      uiState.skillPackageApplied = true;
      character.phase = 'done';
      saveCharacter();
      renderAll();
    });
  }
}

// ============================================================
// PHASE 6: Done
// ============================================================

function renderDonePhase() {
  const existingConns = (character.associates || []).filter(a => (a.description || '').startsWith('Connection: '));

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 06 — READY FOR ADVENTURE</span></div>
    <div class="stage-content">
      <div class="phase-label">Character Complete · Age ${character.age} · ${character.total_terms} Terms</div>
      <h2 class="phase-title">Your Traveller Is Ready</h2>
      <p class="phase-subtitle">${character.name || 'This Traveller'} has survived creation. Take the character sheet and meet your group at the starport.</p>

      <div class="phase-body">
        <p>Your character's full history is in the Mission Log. Export the JSON to save them, or import a different Traveller to continue work.</p>
      </div>

      <div class="done-card">
        <h3 class="done-card-title">Capsule Description</h3>
        <p class="empty" style="margin-bottom:10px">A one-paragraph elevator pitch built from your stats, careers, and skills.</p>
        ${uiState.lastCapsule ? `
          <blockquote class="capsule-box">${escapeHTML(uiState.lastCapsule)}</blockquote>
          <div class="phase-actions" style="gap:6px;margin-top:6px">
            <button class="btn ghost" id="btn-regen-capsule">REGENERATE</button>
            <button class="btn ghost" id="btn-copy-capsule">COPY</button>
          </div>
        ` : `
          <div class="phase-actions">
            <button class="btn" id="btn-gen-capsule">GENERATE CAPSULE</button>
          </div>
        `}
      </div>

      <div class="done-card">
        <h3 class="done-card-title">Connections</h3>
        <p class="empty" style="margin-bottom:10px">Link this Traveller to another PC or NPC from the group. Each connection can grant +1 in any skill, per GM approval.</p>
        ${existingConns.length ? `
          <ul class="connection-list">
            ${existingConns.map(c => `<li>${escapeHTML(c.description.replace(/^Connection: /, ''))}</li>`).join('')}
          </ul>
        ` : ''}
        <div class="connection-form">
          <input type="text" id="conn-desc" placeholder="e.g. Khadi Voss, my old Scout-Service buddy" />
          <input type="text" id="conn-skill" placeholder="Skill to bump (optional): e.g. Deception" />
          <button class="btn ghost" id="btn-add-connection">ADD CONNECTION</button>
        </div>
      </div>

      ${renderPsionicsCard()}

      <div class="phase-actions">
        <button class="btn primary" id="btn-export-prominent">EXPORT CHARACTER JSON</button>
        <button class="btn" id="btn-back-careers">← BACK TO CAREERS</button>
      </div>
    </div>
  `;
}

// Psionics is optional and GM-approved — only visible once the Traveller
// reaches the finalize/done phase. Player can decline, test, and if the
// Psi score is positive, train each of the five core talents.
function renderPsionicsCard() {
  if (!uiState.gmMode && !character.psi_tested && !uiState.psionicsOpen) {
    return `
      <div class="done-card">
        <h3 class="done-card-title">Psionics <span class="empty" style="font-weight:normal">(optional)</span></h3>
        <p class="empty" style="margin-bottom:10px">Psionic testing is normally restricted — ask your Referee before opening this panel.</p>
        <div class="phase-actions">
          <button class="btn ghost" id="btn-open-psionics">OPEN PSIONICS PANEL</button>
        </div>
      </div>
    `;
  }

  const testedHTML = character.psi_tested ? (
    character.psi > 0 ? `
      <div class="psi-result pass">
        <strong>Psi ${character.psi}</strong>
        <span class="empty">— psionic ability confirmed</span>
      </div>
    ` : `
      <div class="psi-result fail">
        <strong>No psionic potential.</strong>
        <span class="empty">The test came back flat. There is no talent to train.</span>
      </div>
    `
  ) : '';

  const talentsHTML = (character.psi > 0) ? `
    <div class="psi-talents">
      ${['telepathy','clairvoyance','telekinesis','awareness','teleportation'].map(id => {
        const trained = (character.psi_trained_talents || []).includes(id);
        const label = id.charAt(0).toUpperCase() + id.slice(1);
        return `
          <button class="btn ${trained ? 'ghost' : ''}" data-talent="${id}" ${trained ? 'disabled' : ''}>
            ${trained ? '✓ ' : ''}${label}${trained ? '' : ' — Cr200k'}
          </button>
        `;
      }).join('')}
    </div>
  ` : '';

  return `
    <div class="done-card">
      <h3 class="done-card-title">Psionics</h3>
      <p class="empty" style="margin-bottom:10px">Psionic potential test (2D 9+, DM-1 per term). On success, Psi = 2D – terms. Each talent trained costs Cr200,000 and rolls against Psi.</p>
      ${testedHTML}
      ${!character.psi_tested ? `
        <div class="phase-actions">
          <button class="btn" id="btn-test-psionics">TEST FOR POTENTIAL</button>
        </div>
      ` : ''}
      ${talentsHTML}
    </div>
  `;
}

function wireDonePhase() {
  const btnExport = document.getElementById('btn-export-prominent');
  if (btnExport) btnExport.addEventListener('click', exportCharacter);
  const btnBack = document.getElementById('btn-back-careers');
  if (btnBack) btnBack.addEventListener('click', () => {
    character.phase = 'career';
    saveCharacter();
    renderAll();
  });

  const generateCapsule = async () => {
    try {
      const response = await apiCall('/api/character/capsule');
      uiState.lastCapsule = response.capsule;
      // Persist capsule on the character for export
      character.capsule_description = response.capsule;
      saveCharacter();
    } catch (e) { alert(e.message); }
    renderAll();
  };

  const btnGen = document.getElementById('btn-gen-capsule');
  if (btnGen) btnGen.addEventListener('click', generateCapsule);
  const btnRegen = document.getElementById('btn-regen-capsule');
  if (btnRegen) btnRegen.addEventListener('click', generateCapsule);
  const btnCopy = document.getElementById('btn-copy-capsule');
  if (btnCopy) btnCopy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(uiState.lastCapsule || '');
      btnCopy.textContent = 'COPIED';
      setTimeout(() => { btnCopy.textContent = 'COPY'; }, 1200);
    } catch (e) { alert('Copy failed: ' + e.message); }
  });

  const btnAddConn = document.getElementById('btn-add-connection');
  if (btnAddConn) btnAddConn.addEventListener('click', async () => {
    const descEl = document.getElementById('conn-desc');
    const skillEl = document.getElementById('conn-skill');
    const desc = (descEl?.value || '').trim();
    const skill = (skillEl?.value || '').trim() || null;
    if (!desc) { alert('Enter a connection description first.'); return; }
    try {
      const response = await apiCall('/api/character/connection', { description: desc, skill });
      await applyResponse(response);
      if (descEl) descEl.value = '';
      if (skillEl) skillEl.value = '';
    } catch (e) { alert(e.message); }
    renderAll();
  });

  // Psionics
  const btnOpenPsi = document.getElementById('btn-open-psionics');
  if (btnOpenPsi) btnOpenPsi.addEventListener('click', () => {
    uiState.psionicsOpen = true;
    renderAll();
  });

  const btnTestPsi = document.getElementById('btn-test-psionics');
  if (btnTestPsi) btnTestPsi.addEventListener('click', async () => {
    if (!confirm('Test for psionic potential? Your Referee must approve this in most campaigns.')) return;
    try {
      const response = await apiCall('/api/character/psionics/test');
      await applyResponse(response);
    } catch (e) { alert(e.message); }
    renderAll();
  });

  document.querySelectorAll('[data-talent]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const talent = btn.dataset.talent;
      try {
        const response = await apiCall('/api/character/psionics/train', { talent_id: talent });
        await applyResponse(response);
      } catch (e) { alert(e.message); }
      renderAll();
    });
  });
}

// ============================================================
// Death overlay
// ============================================================

function renderDeadStage() {
  return `
    <div class="panel-header"><span class="led" style="background:var(--danger);box-shadow:0 0 6px var(--danger)"></span><span>DECEASED</span></div>
    <div class="stage-content">
      <div class="death-banner">
        <h2>TRAVELLER EXPIRED</h2>
        <p>${character.death_reason || 'Unknown cause.'}</p>
      </div>
      <p class="phase-body">Welcome to Traveller. Your character died during creation — it happens. You can revive them via medical care (not yet modeled in this creator — edit the JSON manually if you want to cheat death), or start over.</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-new-char">NEW CHARACTER</button>
      </div>
    </div>
  `;
}

function wireDeadStage() {
  document.getElementById('btn-new-char').addEventListener('click', async () => {
    await freshCharacter();
    renderAll();
  });
}

// ============================================================
// Export / Import / Reset
// ============================================================

function exportCharacter() {
  const blob = new Blob([JSON.stringify(character, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${(character.name || 'traveller').replace(/\s+/g, '_')}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function importCharacter(file) {
  const text = await file.text();
  try {
    const imported = JSON.parse(text);
    character = imported;
    saveCharacter();
    renderAll();
  } catch (e) {
    alert('Invalid character JSON: ' + e.message);
  }
}

// ============================================================
// Initial render
// ============================================================

function renderGMPanel() {
  const panel = document.getElementById('gm-panel');
  if (!panel) return;
  panel.style.display = uiState.gmMode ? 'block' : 'none';
  if (!uiState.gmMode) return;
  const lastEl = document.getElementById('gm-last-rolls');
  if (lastEl) {
    const rolls = uiState.gmLastRolls;
    lastEl.textContent = rolls?.length
      ? `Last sent: [${rolls.join(', ')}]`
      : '';
  }
}

function renderAll() {
  renderSheet();
  renderStage();
  renderLog();
  renderGMPanel();
}

async function bootstrap() {
  const hasSaved = loadCharacter();
  if (!hasSaved || !character) {
    await freshCharacter();
  }

  try {
    const res = await fetch('/api/careers/full');
    if (res.ok) {
      const data = await res.json();
      window.__careerData = data.careers || {};
    }
  } catch (e) { /* network error — picker will degrade gracefully */ }

  try {
    const pkgRes = await fetch('/api/skill-packages');
    if (pkgRes.ok) {
      const pkgData = await pkgRes.json();
      SKILL_PACKAGES = pkgData.packages || {};
    }
  } catch (e) { /* non-fatal */ }

  renderAll();

  document.getElementById('btn-export').addEventListener('click', exportCharacter);
  document.getElementById('import-file').addEventListener('change', (e) => {
    if (e.target.files[0]) importCharacter(e.target.files[0]);
  });

  document.getElementById('btn-reset').addEventListener('click', async () => {
    if (!confirm('Start a new character? This will wipe the current character and log.')) return;
    try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* ignore */ }
    await freshCharacter();
    renderAll();
  });

  document.getElementById('btn-make-npc').addEventListener('click', async () => {
    if (!confirm('Generate a complete NPC? This will replace the current character.')) return;
    const btn = document.getElementById('btn-make-npc');
    btn.textContent = 'GENERATING…';
    btn.disabled = true;
    try {
      const res = await fetch('/api/character/generate-npc');
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      character = data.character;
      uiState.log = data.log || [];
      saveCharacter();
      renderAll();
    } catch (e) {
      alert('NPC generation failed: ' + e.message);
    } finally {
      btn.textContent = 'MAKE NPC';
      btn.disabled = false;
    }
  });

  const btnGm = document.getElementById('btn-gm-mode');
  if (btnGm) {
    const paintGm = () => {
      btnGm.classList.toggle('active', !!uiState.gmMode);
      btnGm.textContent = uiState.gmMode ? 'GM ●' : 'GM';
      document.body.classList.toggle('gm-mode', !!uiState.gmMode);
      renderGMPanel();
    };
    paintGm();
    btnGm.addEventListener('click', () => {
      uiState.gmMode = !uiState.gmMode;
      uiState.gmLastRolls = [];
      try { localStorage.setItem('traveller_gm_mode', uiState.gmMode ? '1' : '0'); } catch (e) { /* ignore */ }
      paintGm();
    });
  }

  const fairBtn = document.getElementById('btn-fair-use');
  const fairModal = document.getElementById('fair-use-modal');
  const fairClose = document.getElementById('btn-close-fair-use');
  if (fairBtn && fairModal) {
    fairBtn.addEventListener('click', () => { fairModal.hidden = false; });
  }
  if (fairClose && fairModal) {
    fairClose.addEventListener('click', () => { fairModal.hidden = true; });
    fairModal.addEventListener('click', (e) => {
      if (e.target === fairModal) fairModal.hidden = true;
    });
  }
}

bootstrap();
