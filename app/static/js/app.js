/* ============================================================
   TRAVELLER — Character Generation Terminal
   Client-side phase controller
   ============================================================ */

// ------------------------------------------------------------
// Boot data + state
// ------------------------------------------------------------

const SPECIES = JSON.parse(document.getElementById('bootstrap-species').textContent);
const CAREERS = JSON.parse(document.getElementById('bootstrap-careers').textContent);

const STORAGE_KEY = 'traveller-character-v1';

let character = null;
let uiState = {
  // Transient selections that aren't part of the character yet
  selectedSpecies: null,
  selectedBgSkills: new Set(),
  selectedPreCareerSkills: new Set(),
  selectedCareer: null,
  selectedAssignment: null,
  // After-roll dialog state
  lastRoll: null,
  // Stat-swap UI state (characteristics phase)
  swapPick: null,   // which tile the user clicked first (for 2-click swap)
  swapA: 'EDU',     // dropdown A default
  swapB: 'STR',     // dropdown B default
  // Current phase sub-state: 'qualify' | 'assign' | 'train' | 'survive' | 'event' | 'advance' | 'decide' | 'mishap' | 'muster'
  subPhase: null,
  pendingAge: false,
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
              selectedCareer: null, selectedAssignment: null, lastRoll: null,
              swapPick: null, swapA: 'EDU', swapB: 'STR',
              subPhase: null, pendingAge: false };
  saveCharacter();
}

// ------------------------------------------------------------
// API helpers
// ------------------------------------------------------------

async function apiCall(endpoint, extraData = {}) {
  const payload = { character, ...extraData };
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

  sheet.innerHTML = `
    <div class="panel-header"><span class="led"></span><span>CHARACTER FILE</span></div>
    <div class="sheet-scroll">
      <div class="sheet-header">
        <input type="text" class="sheet-name-input" id="char-name" placeholder="[ Unnamed Traveller ]" value="${character.name || ''}" />
        <input type="text" class="sheet-homeworld" id="char-homeworld" placeholder="Homeworld" value="${character.homeworld || ''}" />
        <div class="sheet-meta">
          <span>SPECIES<br><strong>${species.name}</strong></span>
          <span>AGE<br><strong>${character.age}</strong></span>
          <span>TERMS<br><strong>${character.total_terms}</strong></span>
          <span>CREDITS<br><strong>Cr${character.credits.toLocaleString()}</strong></span>
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
        <h3>Equipment</h3>
        <ul class="equipment-list">${equipList}</ul>
      </div>

      ${character.ship_shares > 0 ? `
      <div class="sheet-section">
        <h3>Ship Shares</h3>
        <div class="credits-line">${character.ship_shares} × MCr1</div>
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

function renderCharacteristicsPhase() {
  const hasRolled = Object.values(character.characteristics).some(v => v > 0);
  const STATS = ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC'];

  // Stat grid — each cell shows rolled value + DM, makes swap decisions concrete.
  const statGrid = hasRolled ? `
    <div class="stat-grid-rolled">
      ${STATS.map(stat => {
        const val = character.characteristics[stat];
        const dm = charDM(val);
        return `
          <div class="stat-cell-rolled ${uiState.swapPick === stat ? 'picked' : ''}"
               data-stat="${stat}">
            <span class="stat-label">${stat}</span>
            <span class="stat-value">${val}</span>
            <span class="stat-dm">DM ${formatDM(dm)}</span>
          </div>
        `;
      }).join('')}
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

      ${statGrid}
      ${swapRow}

      <div class="phase-actions">
        <button class="btn primary" id="btn-roll-stats">${hasRolled ? 'REROLL ALL' : 'ROLL 2D × 6'}</button>
        <button class="btn" id="btn-to-species" ${hasRolled ? '' : 'disabled'}>ADVANCE TO SPECIES →</button>
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
    character.phase = 'species';
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
}

// ============================================================
// PHASE 2: Species
// ============================================================

function renderSpeciesPhase() {
  const selected = uiState.selectedSpecies || character.species_id;
  const speciesApplied = character.species_id && character.traits && character.traits.length >= 0 && character.phase !== 'species';

  const cards = SPECIES.map(sp => {
    const modsText = Object.entries(sp.characteristic_modifiers)
      .filter(([, v]) => v !== 0)
      .map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`)
      .join(' · ') || 'No modifiers';
    return `
      <button class="card ${selected === sp.id ? 'selected' : ''}" data-species="${sp.id}">
        <div class="card-title">${sp.name}</div>
        <div class="card-meta">${modsText}</div>
        <div class="card-desc">${sp.description}</div>
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
    <div class="panel-header"><span class="led"></span><span>PHASE 02 — SPECIES SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Genetic Profile</div>
      <h2 class="phase-title">Choose Your Species</h2>
      <p class="phase-subtitle">Species modifiers apply immediately to your rolled characteristics.</p>

      <div class="card-grid">${cards}</div>

      ${traitsPanel}

      <div class="phase-actions">
        <button class="btn ghost" id="btn-back-stats">← BACK</button>
        <button class="btn primary" id="btn-apply-species" ${selected ? '' : 'disabled'}>
          APPLY ${selectedSp ? selectedSp.name.toUpperCase() : 'SPECIES'} →
        </button>
      </div>
    </div>
  `;
}

function wireSpeciesPhase() {
  document.querySelectorAll('[data-species]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedSpecies = card.dataset.species;
      renderStage();
    });
  });
  document.getElementById('btn-back-stats').addEventListener('click', () => {
    character.phase = 'characteristics';
    saveCharacter();
    renderAll();
  });
  document.getElementById('btn-apply-species').addEventListener('click', async () => {
    if (!uiState.selectedSpecies) return;
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
          ? `Enrolled. ${lr.ageCost ? `${lr.ageCost} years pass while you study.` : ''} Now roll for graduation.`
          : `Didn't meet the bar. You skip straight to your first career without any education bonus.`
        }</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-precareer-qualify">
            ${passed ? 'ROLL GRADUATION →' : 'CONTINUE TO CAREER →'}
          </button>
        </div>
      </div>
    `;
  }

  // Post-roll view: graduation outcome
  if (uiState.lastRoll?.type === 'precareer_graduate') {
    const lr = uiState.lastRoll;
    const labels = { pass: 'Graduated', honours: 'Graduated with Honours', fail: 'Failed to Graduate' };
    const remaining = status.skill_picks_remaining || 0;
    const pool = status.skill_pool || [];

    const appliedHTML = lr.applied?.length ? `
      <div class="dm-applied-box">
        <span class="event-label">Graduation benefits</span>
        ${lr.applied.map(s => `<div class="dm-chip applied">${escapeHTML(s)}</div>`).join('')}
      </div>
    ` : '';

    // If there are still skill picks to make, render the picker here
    if (remaining > 0) {
      const picked = Array.from(uiState.selectedPreCareerSkills || new Set());
      const picker = pool.map(s => {
        const sel = picked.includes(s);
        return `<button class="skill-chip ${sel ? 'selected' : ''}" data-pc-skill="${escapeHTML(s)}"
          ${!sel && picked.length >= remaining ? 'disabled' : ''}>${escapeHTML(s)}</button>`;
      }).join('');
      return `
        <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
        <div class="stage-content">
          <div class="phase-label">Graduation — ${labels[lr.outcome]}</div>
          <h2 class="phase-title">Pick Your Skills</h2>
          ${rollReadoutHTML(lr.data, { label: `${lr.charLabel} ${lr.target}+` })}
          ${appliedHTML}
          <p class="phase-body">Choose <strong>${remaining}</strong> skill${remaining === 1 ? '' : 's'} at level 1 from the ${lr.trackName} list.</p>
          <div class="skill-picker">${picker}</div>
          <div class="phase-actions">
            <button class="btn primary" id="btn-confirm-pc-skills"
              ${picked.length === 0 ? 'disabled' : ''}>
              CONFIRM ${picked.length}/${remaining} →
            </button>
          </div>
        </div>
      `;
    }

    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Graduation — ${labels[lr.outcome]}</div>
        <h2 class="phase-title">${labels[lr.outcome]}</h2>
        ${rollReadoutHTML(lr.data, { label: `${lr.charLabel} ${lr.target}+` })}
        ${appliedHTML}
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-precareer-graduate">CONTINUE TO CAREER →</button>
        </div>
      </div>
    `;
  }

  // Enrolled — show graduation roll button
  if (stage === 'enrolled') {
    const track = status.track;
    const service = status.service;
    const trackName = track === 'university'
      ? 'University'
      : (PRE_CAREER_SERVICES.find(s => s.id === service)?.name || 'Military Academy');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Enrolled · ${trackName}</div>
        <h2 class="phase-title">Time to Graduate</h2>
        <p class="phase-subtitle">Roll for graduation. Pass for bonuses, hit the Honours target for even more.</p>
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

  // Default: pick a track (University / Academy / Skip)
  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
    <div class="stage-content">
      <div class="phase-label">Optional · Age ${character.age}</div>
      <h2 class="phase-title">Education Before Service?</h2>
      <p class="phase-subtitle">Before picking a career, you can spend a few years at University or a Military Academy. Or skip and go straight to the job.</p>

      <div class="card-grid">
        <button class="card" id="btn-pc-university">
          <div class="card-title">University</div>
          <div class="card-desc">INT 6+ to qualify, 4 years, +1 EDU on enrollment. Graduate for +2 EDU and 2 skills at level 1. Honours at 10+ adds SOC +1 and DM+1 to your first career qualification.</div>
        </button>
        <button class="card" id="btn-pc-academy">
          <div class="card-title">Military Academy</div>
          <div class="card-desc">3 years. Qualification varies by service. Graduate and you start that career commissioned (Rank 1) with DM+1 to next advancement.</div>
        </button>
        <button class="card" id="btn-pc-skip">
          <div class="card-title">Skip</div>
          <div class="card-desc">Age ${character.age} and hungry for a paycheck. Go straight to the career phase.</div>
        </button>
      </div>
    </div>
  `;
}

function wirePreCareerPhase() {
  // Main choice
  const uni = document.getElementById('btn-pc-university');
  if (uni) uni.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/qualify',
        { track: 'university' });
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'precareer_qualify',
        data: response.roll,
        passed: response.passed,
        trackName: 'University',
        charLabel: 'INT',
        target: 6,
        ageCost: 4,
        enrollmentApplied: response.enrollment_applied || [],
      };
      renderAll();
    } catch (e) { alert(e.message); }
  });

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

  const skip = document.getElementById('btn-pc-skip');
  if (skip) skip.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/skip');
      await applyResponse(response);
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Academy service picker
  document.querySelectorAll('[data-pc-service]').forEach(card => {
    card.addEventListener('click', async () => {
      const service = card.dataset.pcService;
      const svc = PRE_CAREER_SERVICES.find(s => s.id === service);
      try {
        const response = await apiCall('/api/character/pre-career/qualify',
          { track: 'military_academy', service });
        await applyResponse(response);
        // Target + char key come from the engine response implicitly,
        // but for display we use the service's known values.
        const charLabel = service === 'navy' ? 'INT' : 'END';
        const target = service === 'army' ? 7 : 9;
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
    uiState.lastRoll = null;
    if (passed) {
      // Stay in pre_career, will show enrolled -> graduation button
      renderStage();
    } else {
      // Engine already set phase=career on failed qualification
      renderAll();
    }
  });

  // Graduation roll button
  const gradBtn = document.getElementById('btn-pc-graduate');
  if (gradBtn) gradBtn.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/graduate',
        { chosen_skills: [] });
      await applyResponse(response);
      const track = character.pre_career_status?.track;
      const service = character.pre_career_status?.service;
      const trackName = track === 'university'
        ? 'University'
        : (PRE_CAREER_SERVICES.find(s => s.id === service)?.name || 'Military Academy');
      const charLabel = 'EDU';
      const target = track === 'university' ? 7 : 7;
      uiState.selectedPreCareerSkills = new Set();
      uiState.lastRoll = {
        type: 'precareer_graduate',
        data: response.roll,
        outcome: response.outcome,
        applied: response.applied || [],
        trackName,
        charLabel,
        target,
      };
      renderAll();
    } catch (e) { alert(e.message); }
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
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Post-graduate continue (no picks path)
  const postGrad = document.getElementById('btn-post-precareer-graduate');
  if (postGrad) postGrad.addEventListener('click', () => {
    uiState.lastRoll = null;
    renderAll();
  });
}

// ============================================================
// PHASE 4: Career Loop
// ============================================================

function renderCareerPhase() {
  const term = character.current_term;
  const subPhase = uiState.subPhase;

  // If there's no active term, we're in the "choose career" state
  if (!term) {
    return renderChooseCareer();
  }

  // Active term - show the term walkthrough
  return renderActiveTerm();
}

function renderChooseCareer() {
  const cards = CAREERS.map(c => {
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

  // Active term view
  const btnAssign = document.getElementById('btn-start-term');
  if (btnAssign) {
    btnAssign.addEventListener('click', async () => {
      if (!uiState.selectedAssignment) return;
      const response = await apiCall('/api/character/start-term', {
        career_id: uiState.selectedCareer,
        assignment_id: uiState.selectedAssignment,
      });
      await applyResponse(response);
      uiState.subPhase = 'train';
      renderAll();
    });
  }

  document.querySelectorAll('[data-assignment]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedAssignment = card.dataset.assignment;
      renderStage();
    });
  });

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

  const btnSurvive = document.getElementById('btn-survive');
  if (btnSurvive) {
    btnSurvive.addEventListener('click', async () => {
      const response = await apiCall('/api/character/survive');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'survive',
        data: response.roll,
        outcome: response.survived ? 'pass' : 'fail',
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
      };
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

  const btnMishap = document.getElementById('btn-mishap');
  if (btnMishap) {
    btnMishap.addEventListener('click', async () => {
      const response = await apiCall('/api/character/mishap');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'mishap',
        data: response.roll,
        mishapText: response.mishap,
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
        <p class="phase-body">You didn't qualify. In the full rules you would now submit to the Draft or take the Drifter career. For now, <strong>choose another career to attempt</strong> (with a DM-1 penalty for each failed career, per the rules — not yet modeled). The Drifter career has automatic qualification.</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-back-careers">← TRY ANOTHER CAREER</button>
        </div>
      </div>
    `;
  }
}

function renderAssignmentPicker(career) {
  const cards = Object.entries(career.assignments).map(([id, a]) => `
    <button class="card ${uiState.selectedAssignment === id ? 'selected' : ''}" data-assignment="${id}">
      <div class="card-title">${a.name}</div>
      <div class="card-meta">SURV ${a.survival.characteristic} ${a.survival.target}+ · ADV ${a.advancement.characteristic} ${a.advancement.target}+</div>
      <div class="card-desc">${a.description}</div>
    </button>
  `).join('');

  return `
    <h3 style="margin-top:28px;font-family:var(--font-mono);font-size:11px;letter-spacing:0.3em;color:var(--amber-dim);text-transform:uppercase">Choose an Assignment</h3>
    <div class="card-grid">${cards}</div>
    <div class="phase-actions">
      <button class="btn primary" id="btn-start-term" ${uiState.selectedAssignment ? '' : 'disabled'}>
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

  return `
    <div class="stage-content">
      <div class="phase-label">Skill Training · 1D Roll</div>
      <h2 class="phase-title">${term.basic_training ? 'Basic Training' : 'Skills and Training'}</h2>
      <p class="phase-subtitle">${term.basic_training
        ? 'First term in this career — pick any table to roll 1D.'
        : 'Pick one skill table and roll 1D on it.'}</p>

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
    return `
      <div class="stage-content">
        <div class="phase-label">Survival — ${survived ? 'Pass' : 'Fail'}</div>
        <h2 class="phase-title">${survived ? 'You Survived' : 'Career Mishap'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${s.characteristic} ${s.target}+` })}
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

    const pendingHTML = pendingGrants.length ? `
      <div class="dm-pending-box">
        <span class="event-label">DM grants (conditional — resolve manually)</span>
        ${pendingGrants.map(g => `
          <div class="dm-chip pending">DM${g.dm >= 0 ? '+' : ''}${g.dm} to ${g.target} roll (if earned)</div>
        `).join('')}
      </div>
    ` : '';

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
        <p class="phase-body empty"><em>Apply any resulting skills, contacts, or benefits manually to your notes — only "DM+N to next X roll" grants are auto-applied.</em></p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-event">ATTEMPT ADVANCEMENT →</button>
          <button class="btn" id="btn-skip-advance">SKIP ADVANCEMENT</button>
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
    return `
      <div class="stage-content">
        <div class="phase-label">Mishap</div>
        <h2 class="phase-title">What Went Wrong</h2>
        ${rollReadoutHTML(lr.data, { label: '1D', showTarget: false })}
        <div class="mishap-box">
          <span class="event-label">Mishap [1D=${lr.data?.total ?? '?'}]</span>
          ${escapeHTML(lr.mishapText || '')}
        </div>
        <p class="phase-body empty"><em>Apply any stat reductions, allies/enemies, or ejection effects manually — automatic handling is not yet modeled.</em></p>
        <div class="phase-actions">
          <button class="btn danger" id="btn-post-mishap">END CAREER →</button>
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
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <h2 class="phase-title">All Benefits Claimed</h2>
        <p class="phase-body">You've rolled all your mustering-out benefits. Your Traveller is ready.</p>
        <div class="phase-actions">
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
        <div class="phase-actions">
          <button class="btn primary" id="btn-roll-cash" ${cashRolled >= 3 ? 'disabled' : ''}>ROLL CASH (1D)${cashRolled >= 3 ? ' — MAX' : ''}</button>
          <button class="btn" id="btn-roll-benefit">ROLL BENEFIT (1D)</button>
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
        const response = await apiCall('/api/character/muster-out',
          { career_id: careerId, column: 'benefit' });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'muster',
          column: 'benefit',
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
  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 06 — READY FOR ADVENTURE</span></div>
    <div class="stage-content">
      <div class="phase-label">Character Complete · Age ${character.age} · ${character.total_terms} Terms</div>
      <h2 class="phase-title">Your Traveller Is Ready</h2>
      <p class="phase-subtitle">${character.name || 'This Traveller'} has survived creation. Take the character sheet and meet your group at the starport.</p>

      <div class="phase-body">
        <p>Your character's full history is in the Mission Log. Export the JSON to save them, or import a different Traveller to continue work.</p>
        <p>To add another species or complete a stubbed career, edit the files in <code>app/data/</code>. The README has the full schema.</p>
      </div>

      <div class="phase-actions">
        <button class="btn primary" id="btn-export-prominent">EXPORT CHARACTER JSON</button>
        <button class="btn" id="btn-back-careers">← BACK TO CAREERS</button>
      </div>
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

function renderAll() {
  renderSheet();
  renderStage();
  renderLog();
}

async function bootstrap() {
  const hasSaved = loadCharacter();
  if (!hasSaved || !character) {
    await freshCharacter();
  }
  renderAll();

  // Footer wires
  document.getElementById('btn-export').addEventListener('click', exportCharacter);
  document.getElementById('import-file').addEventListener('change', (e) => {
    if (e.target.files[0]) importCharacter(e.target.files[0]);
  });
  document.getElementById('btn-reset').addEventListener('click', async () => {
    if (confirm('Discard current character and start fresh?')) {
      await freshCharacter();
      renderAll();
    }
  });
}

// Handle "back to careers" button for rejected qualification
document.addEventListener('click', (e) => {
  if (e.target && e.target.id === 'btn-back-careers') {
    uiState.selectedCareer = null;
    uiState.selectedAssignment = null;
    uiState.subPhase = null;
    uiState.lastRoll = null;
    renderAll();
  }
});

bootstrap();
