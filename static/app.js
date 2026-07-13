// ---------- Indian Monthly Menu — Calendar SPA ----------
const MEALS = [
  { key: 'breakfast', icon: '🌅', cls: 'chip-breakfast', label: 'Breakfast' },
  { key: 'lunch',     icon: '☀️', cls: 'chip-lunch',     label: 'Lunch' },
  { key: 'dinner',    icon: '🌙', cls: 'chip-dinner',    label: 'Dinner' },
  { key: 'dessert',   icon: '🍮', cls: 'chip-dessert',   label: 'Dessert' },
];
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

const state = {
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1, // 1-12
  recipes: [],
  entries: {}, // key `y-m-d` -> { meal: entry }
  pick: null,  // { y, m, d, meal }
  household: 4,
};

// ---------- utils ----------
const $ = (id) => document.getElementById(id);
const api = async (url, opts) => {
  const r = await fetch(url, opts);
  if (!r.ok) { let e; try { e = await r.json(); } catch { e = { detail: r.statusText }; } throw e; }
  return r.status === 204 ? null : r.json();
};
function toast(msg) {
  const t = $('toast'); t.textContent = msg; t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 2200);
}
function debounce(fn, ms) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
const dkey = (y, m, d) => `${y}-${m}-${d}`;

function isoWeek(dt) {
  const date = new Date(Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate()));
  const dayNum = (date.getUTCDay() + 6) % 7;
  date.setUTCDate(date.getUTCDate() - dayNum + 3);
  const firstThursday = new Date(Date.UTC(date.getUTCFullYear(), 0, 4));
  const week = 1 + Math.round(((date - firstThursday) / 86400000 - 3 + ((firstThursday.getUTCDay() + 6) % 7)) / 7);
  return { week, year: date.getUTCFullYear() };
}
function mondayOf(dt) {
  const d = new Date(dt);
  const dayNum = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - dayNum);
  return d;
}
const isToday = (y, m, d) => { const n = new Date(); return n.getFullYear() === y && n.getMonth() + 1 === m && n.getDate() === d; };

// ---------- theme ----------
function applyTheme(dark) {
  document.documentElement.classList.toggle('dark', dark);
  localStorage.setItem('menu-theme', dark ? 'dark' : 'light');
  $('themeBtn').innerHTML = `<i data-lucide="${dark ? 'sun' : 'moon'}" class="w-5 h-5"></i>`;
  lucide.createIcons();
}
$('themeBtn').onclick = () => applyTheme(!document.documentElement.classList.contains('dark'));

// ---------- data loading ----------
async function loadRecipes() {
  state.recipes = await api('/api/recipes');
  const regions = [...new Set(state.recipes.map(r => r.region))].sort();
  $('pickerRegion').innerHTML = '<option value="">All Regions</option>' + regions.map(r => `<option>${r}</option>`).join('');
}
async function loadSettings() {
  const s = await api('/api/settings');
  const hs = s.find(x => x.key === 'household_size');
  state.household = hs ? parseInt(hs.value) || 4 : 4;
}
async function loadEntries() {
  state.entries = {};
  // fetch current + adjacent months to cover boundary weeks
  const months = [[state.year, state.month]];
  const prev = state.month === 1 ? [state.year - 1, 12] : [state.year, state.month - 1];
  const next = state.month === 12 ? [state.year + 1, 1] : [state.year, state.month + 1];
  months.push(prev, next);
  for (const [y, m] of months) {
    const list = await api(`/api/menu/${y}/${m}`);
    for (const e of list) {
      const k = dkey(e.year, e.month, e.day);
      (state.entries[k] ||= {})[e.meal_type] = e;
    }
  }
}
async function loadSeasonal() {
  const s = await api(`/api/seasonal/${state.month}`);
  const emoji = { Winter: '❄️', Summer: '🌞', Monsoon: '🌧️', All: '🍃' }[s.season] || '🍃';
  $('seasonBadge').textContent = `${emoji} ${s.season}`;
  $('vegList').innerHTML = s.vegetables.map(v => `<li>• ${v}</li>`).join('');
  $('fruitList').innerHTML = s.fruits.map(f => `<li>• ${f}</li>`).join('');
}

// ---------- render calendar ----------
function chipHTML(entry, meal) {
  const r = entry.recipe;
  return `<button class="chip ${meal.cls}" data-entry="${entry.id}" title="${r.name}">
    <span class="font-semibold truncate">${meal.icon} ${r.name}</span>
    ${r.name_hindi ? `<span class="hindi opacity-70 truncate">${r.name_hindi}</span>` : ''}
  </button>`;
}
function cellHTML(dt) {
  const y = dt.getFullYear(), m = dt.getMonth() + 1, d = dt.getDate();
  const inMonth = m === state.month;
  const weekend = dt.getDay() === 0 || dt.getDay() === 6;
  const dayEntries = state.entries[dkey(y, m, d)] || {};
  const cls = ['surface brd border rounded-xl p-2 min-h-[130px] flex flex-col gap-1'];
  if (weekend) cls.push('weekend-cell');
  if (isToday(y, m, d)) cls.push('today-cell');
  if (!inMonth) cls.push('opacity-45');
  const slots = MEALS.map(meal => {
    const e = dayEntries[meal.key];
    if (e) return chipHTML(e, meal);
    return `<button class="add-slot" data-add="${y}|${m}|${d}|${meal.key}">＋ ${meal.icon}</button>`;
  }).join('');
  const today = isToday(y, m, d);
  return `<div class="${cls.join(' ')}">
    <div class="flex items-baseline justify-between">
      <span class="text-sm ${today ? 'font-bold text-[var(--accent)]' : 'font-semibold'}">${d}</span>
      ${today ? '<span class="today-badge">Today</span>' : `<span class="text-[10px] uppercase" style="color:var(--muted)">${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][dt.getDay()]}</span>`}
    </div>
    ${slots}
  </div>`;
}
function weekHeaderHTML(monday) {
  const sunday = new Date(monday); sunday.setDate(sunday.getDate() + 6);
  const { week, year } = isoWeek(monday);
  const range = `${monday.getDate()} ${MONTHS[monday.getMonth()].slice(0,3)} – ${sunday.getDate()} ${MONTHS[sunday.getMonth()].slice(0,3)}`;
  return `<div class="no-print flex items-center gap-2 flex-wrap panel rounded-lg px-3 py-1.5 text-sm">
    <span class="font-semibold">Week ${week} · ${range}</span>
    <div class="ml-auto flex gap-1.5">
      <button class="wk-btn" data-af="${year}|${week}"><i data-lucide="wand-2" class="w-3.5 h-3.5"></i>Auto-Fill</button>
      <button class="wk-btn" data-shop="${year}|${week}"><i data-lucide="shopping-cart" class="w-3.5 h-3.5"></i>Shopping</button>
      <button class="wk-btn" data-pdf="${year}|${week}"><i data-lucide="file-down" class="w-3.5 h-3.5"></i>PDF</button>
      <button class="wk-btn" data-print="${year}|${week}"><i data-lucide="printer" class="w-3.5 h-3.5"></i>Print</button>
    </div>
  </div>`;
}
function render() {
  $('monthLabel').textContent = `${MONTHS[state.month - 1]} ${state.year}`;
  const first = new Date(state.year, state.month - 1, 1);
  const last = new Date(state.year, state.month, 0);
  let cur = mondayOf(first);
  let html = '';
  while (cur <= last) {
    const monday = new Date(cur);
    let cells = '';
    for (let i = 0; i < 7; i++) {
      const dt = new Date(monday); dt.setDate(dt.getDate() + i);
      cells += cellHTML(dt);
    }
    html += `<section>${weekHeaderHTML(monday)}
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-7 gap-1.5 mt-1.5">${cells}</div></section>`;
    cur.setDate(cur.getDate() + 7);
  }
  $('calendar').innerHTML = html;
  bindCalendar();
  lucide.createIcons();
}

// style week buttons
const styleTag = document.createElement('style');
styleTag.textContent = `.wk-btn{display:inline-flex;align-items:center;gap:4px;font-size:12px;padding:4px 8px;border-radius:8px;background:var(--surface);border:1px solid var(--border);}
.wk-btn:hover{color:var(--accent);border-color:var(--accent);}`;
document.head.appendChild(styleTag);

function bindCalendar() {
  document.querySelectorAll('[data-add]').forEach(b => b.onclick = () => {
    const [y, m, d, meal] = b.dataset.add.split('|');
    openPicker(+y, +m, +d, meal);
  });
  document.querySelectorAll('[data-entry]').forEach(b => b.onclick = () => openView(+b.dataset.entry));
  document.querySelectorAll('[data-af]').forEach(b => b.onclick = () => doAutofill(...b.dataset.af.split('|').map(Number)));
  document.querySelectorAll('[data-shop]').forEach(b => b.onclick = () => openShop(...b.dataset.shop.split('|').map(Number)));
  document.querySelectorAll('[data-pdf]').forEach(b => b.onclick = () => { const [y,w]=b.dataset.pdf.split('|'); window.open(`/api/export/pdf/${y}/${w}`, '_blank'); });
  document.querySelectorAll('[data-print]').forEach(b => b.onclick = () => { const [y,w]=b.dataset.print.split('|'); const win = window.open(`/api/export/print/${y}/${w}`, '_blank'); win.onload = () => win.print(); });
}

// ---------- picker ----------
function findEntry(id) {
  for (const k in state.entries) for (const meal in state.entries[k]) if (state.entries[k][meal].id === id) return state.entries[k][meal];
  return null;
}
function openPicker(y, m, d, meal) {
  state.pick = { y, m, d, meal };
  $('pickerMeal').textContent = meal;
  $('pickerSearch').value = ''; $('pickerSeason').value = ''; $('pickerRegion').value = ''; $('pickerTag').value = '';
  renderPicker();
  showModal('pickerModal');
  $('pickerSearch').focus();
}
function renderPicker() {
  const { meal } = state.pick;
  const q = $('pickerSearch').value.toLowerCase();
  const season = $('pickerSeason').value, region = $('pickerRegion').value, tag = $('pickerTag').value;
  const list = state.recipes.filter(r =>
    r.meal_type === meal &&
    (!q || r.name.toLowerCase().includes(q) || (r.name_hindi || '').includes(q)) &&
    (!season || r.season === season) &&
    (!region || r.region === region) &&
    (!tag || (r.tags || '').includes(tag))
  );
  const chilli = (s) => ({ Mild: '🌶️', Medium: '🌶️🌶️', Spicy: '🌶️🌶️🌶️' }[s] || '');
  $('pickerCount').textContent = list.length
    ? `${list.length} recipe${list.length !== 1 ? 's' : ''}`
    : '';
  $('pickerList').innerHTML = list.length ? list.map(r => `
    <button class="pick-row w-full text-left p-2.5 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 flex items-center gap-2" data-rid="${r.id}">
      <div class="flex-1 min-w-0">
        <div class="font-medium truncate">${r.name} ${r.is_weekend_special ? '⭐' : ''}</div>
        <div class="hindi text-sm truncate" style="color:var(--muted)">${r.name_hindi || ''}</div>
      </div>
      <span class="text-[11px] px-2 py-0.5 rounded-full panel whitespace-nowrap">${r.season}</span>
      <span class="text-[11px]" style="color:var(--muted)">${r.region}</span>
      <span class="text-xs">${chilli(r.spice_level)}</span>
    </button>`).join('') : `<p class="text-center text-sm p-6" style="color:var(--muted)">No recipes found.</p>`;
  document.querySelectorAll('.pick-row').forEach(b => b.onclick = () => assign(+b.dataset.rid));
}
$('pickerSearch').addEventListener('input', debounce(renderPicker, 200));
['pickerSeason','pickerRegion','pickerTag'].forEach(id => $(id).addEventListener('input', renderPicker));

async function assign(recipe_id) {
  const { y, m, d, meal } = state.pick;
  await api('/api/menu/entry', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ year: y, month: m, day: d, meal_type: meal, recipe_id }),
  });
  closeModal('pickerModal');
  await loadEntries(); render();
  toast('Meal assigned');
}

// ---------- view modal ----------
let curEntry = null;
function openView(id) {
  const e = findEntry(id); if (!e) return;
  curEntry = e; const r = e.recipe;
  $('vName').textContent = r.name;
  $('vHindi').textContent = r.name_hindi || '';
  const chilli = { Mild: '🌶️', Medium: '🌶️🌶️', Spicy: '🌶️🌶️🌶️' }[r.spice_level] || '';
  const badge = (t) => `<span class="text-xs px-2 py-0.5 rounded-full panel">${t}</span>`;
  const tagEmoji = { 'Festive': '🎉', 'Kids Friendly': '👨‍👩‍👧', 'Quick': '⚡', 'High Protein': '💪', 'Vegetarian': '🥬', 'Non-Veg': '🍗' };
  const tags = (r.tags || '').split(',').filter(Boolean).map(t => badge(`${tagEmoji[t.trim()] || ''} ${t.trim()}`)).join('');
  $('vBadges').innerHTML = badge(r.season) + badge(r.region) + badge(`${chilli} ${r.spice_level}`) + badge(`Serves ${r.servings}`) + (r.is_weekend_special ? badge('⭐ Weekend Special') : '') + tags;
  $('vAccomp').style.display = r.accompaniment ? 'block' : 'none';
  $('vAccomp').textContent = r.accompaniment || '';
  $('vBev').innerHTML = r.suggested_beverage ? `☕ ${r.suggested_beverage}` : '';
  $('vSides').innerHTML = r.suggested_sides ? `🥗 ${r.suggested_sides}` : '';
  $('vIng').innerHTML = (r.ingredients || '').split('\n').filter(Boolean).map(i => `<li>${i}</li>`).join('');
  $('vIns').innerHTML = (r.instructions || '').split('\n').filter(Boolean).map(i => `<li>${i.replace(/^\d+\.\s*/, '')}</li>`).join('');
  switchTab('ing');
  $('vAltPanel').classList.add('hidden');
  $('vSwap').setAttribute('aria-expanded', 'false');
  $('vLang').value = 'English';
  $('vLangStatus').textContent = '';
  $('vEdit').href = `/library?edit=${r.id}`;
  showModal('viewModal');
}
function switchTab(tab) {
  document.querySelectorAll('.vtab').forEach(b => {
    const on = b.dataset.tab === tab;
    b.style.borderColor = on ? 'var(--accent)' : 'transparent';
    b.style.color = on ? '' : 'var(--muted)';
  });
  $('vIng').classList.toggle('hidden', tab !== 'ing');
  $('vIns').classList.toggle('hidden', tab !== 'ins');
}
document.querySelectorAll('.vtab').forEach(b => b.onclick = () => switchTab(b.dataset.tab));
$('vRemove').onclick = async () => {
  if (!curEntry) return;
  await api(`/api/menu/entry/${curEntry.id}`, { method: 'DELETE' });
  closeModal('viewModal'); await loadEntries(); render(); toast('Removed from calendar');
};

// ---------- swap ----------
const chilliDots = (s) => ({ Mild: '🌶️', Medium: '🌶️🌶️', Spicy: '🌶️🌶️🌶️' }[s] || '');

async function performSwap(nextId, nextName) {
  if (!curEntry) return;
  const { year, month, day, meal_type } = curEntry;
  await api('/api/menu/entry', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ year, month, day, meal_type, recipe_id: nextId }),
  });
  await loadEntries(); render();
  const swapped = Object.values(state.entries[dkey(year, month, day)] || {}).find(e => e.meal_type === meal_type);
  if (swapped) openView(swapped.id); else closeModal('viewModal');
  toast(`Swapped to ${nextName}`);
}

async function loadAlternatives() {
  if (!curEntry) return [];
  const { year, month, day, recipe_id } = curEntry;
  return api(`/api/recipes/${recipe_id}/alternatives?year=${year}&month=${month}&day=${day}`);
}

function renderAltList(alts) {
  if (!alts.length) {
    $('vAltList').innerHTML = `<p class="text-center text-sm p-4" style="color:var(--muted)">No alternatives available.</p>`;
    return;
  }
  $('vAltList').innerHTML = alts.map(r => `
    <button class="alt-row w-full text-left p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 flex items-center gap-2" role="option" data-rid="${r.id}" data-name="${r.name.replace(/"/g, '&quot;')}">
      <div class="flex-1 min-w-0">
        <div class="font-medium truncate text-sm">${r.name} ${r.is_weekend_special ? '⭐' : ''}</div>
        <div class="hindi text-xs truncate" style="color:var(--muted)">${r.name_hindi || ''}</div>
      </div>
      <span class="text-[11px] px-2 py-0.5 rounded-full panel whitespace-nowrap">${r.region}</span>
      <span class="text-xs">${chilliDots(r.spice_level)}</span>
    </button>`).join('');
  document.querySelectorAll('.alt-row').forEach(b => b.onclick = () => performSwap(+b.dataset.rid, b.dataset.name));
}

$('vSwap').onclick = async () => {
  if (!curEntry) return;
  const panel = $('vAltPanel');
  const isHidden = panel.classList.contains('hidden');
  if (!isHidden) {
    panel.classList.add('hidden');
    $('vSwap').setAttribute('aria-expanded', 'false');
    return;
  }
  panel.classList.remove('hidden');
  $('vSwap').setAttribute('aria-expanded', 'true');
  $('vAltList').innerHTML = `<p class="text-center text-sm p-4" style="color:var(--muted)">Loading…</p>`;
  try {
    const alts = await loadAlternatives();
    curEntry._alts = alts;
    renderAltList(alts);
    lucide.createIcons();
  } catch { $('vAltList').innerHTML = `<p class="text-center text-sm p-4" style="color:var(--muted)">Could not load alternatives.</p>`; }
};

$('vAltShuffle').onclick = () => {
  const alts = (curEntry && curEntry._alts) || [];
  if (!alts.length) { toast('No alternative recipe available'); return; }
  const next = alts[Math.floor(Math.random() * alts.length)];
  performSwap(next.id, next.name);
};

// ---------- translation ----------
async function loadLanguages() {
  try {
    const data = await api('/api/translate/languages');
    $('vLang').innerHTML = data.languages.map(l => `<option>${l}</option>`).join('');
  } catch { /* keep English-only fallback */ }
}
function applyRecipeFields(f) {
  if (f.name) $('vName').textContent = f.name;
  $('vAccomp').style.display = f.accompaniment ? 'block' : 'none';
  $('vAccomp').textContent = f.accompaniment || '';
  $('vSides').innerHTML = f.suggested_sides ? `🥗 ${f.suggested_sides}` : '';
  $('vIng').innerHTML = (f.ingredients || '').split('\n').filter(Boolean).map(i => `<li>${i}</li>`).join('');
  $('vIns').innerHTML = (f.instructions || '').split('\n').filter(Boolean).map(i => `<li>${i.replace(/^\d+\.\s*/, '')}</li>`).join('');
}
$('vLang').onchange = async () => {
  if (!curEntry) return;
  const lang = $('vLang').value;
  const r = curEntry.recipe;
  if (lang === 'English') { applyRecipeFields(r); $('vLangStatus').textContent = ''; return; }
  $('vLangStatus').textContent = 'Translating…';
  try {
    const data = await api(`/api/translate/recipe/${r.id}?lang=${encodeURIComponent(lang)}`, { method: 'POST' });
    applyRecipeFields(data.fields);
    $('vLangStatus').textContent = '';
  } catch (e) {
    $('vLangStatus').textContent = '⚠️ ' + (e.detail || 'Translation unavailable');
    $('vLang').value = 'English';
  }
};

// ---------- autofill ----------
function confirmDialog(title, msg) {
  return new Promise(res => {
    $('confirmTitle').textContent = title; $('confirmMsg').textContent = msg;
    showModal('confirmModal');
    $('confirmOk').onclick = () => { closeModal('confirmModal'); res(true); };
    $('confirmCancel').onclick = () => { closeModal('confirmModal'); res(false); };
  });
}
async function doAutofill(year, week) {
  const chk = await api(`/api/menu/autofill/${year}/${week}/check`);
  if (chk.has_existing) {
    const ok = await confirmDialog('Auto-Fill Week', 'This will replace all existing meals for this week. Continue?');
    if (!ok) return;
  }
  const res = await api(`/api/menu/autofill/${year}/${week}`, { method: 'POST' });
  await loadEntries(); render();
  toast(`Auto-filled ${res.created} meals`);
}

// ---------- shopping ----------
let shopCtx = null;
async function openShop(year, week) {
  shopCtx = { year, week };
  $('householdInput').value = state.household;
  showDrawer();
  await refreshShop();
}
async function refreshShop() {
  const { year, week } = shopCtx;
  const data = await api(`/api/export/shopping-list/${year}/${week}`);
  $('shopList').innerHTML = data.items.length ? data.items.map((it, i) => `
    <label class="flex items-center gap-2 text-sm py-1 border-b brd">
      <input type="checkbox" class="w-4 h-4 accent-[var(--accent)]"><span>${it}</span>
    </label>`).join('') : `<p class="text-sm" style="color:var(--muted)">No meals assigned this week yet.</p>`;
}
$('householdInput').onchange = async (e) => {
  const v = Math.max(1, parseInt(e.target.value) || 4);
  state.household = v;
  await api(`/api/settings/household_size`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: String(v) }) });
  await refreshShop();
};
$('shopPrint').onclick = () => {
  const items = [...document.querySelectorAll('#shopList span')].map(s => s.textContent);
  const w = window.open('', '_blank');
  w.document.write(`<h2 style="font-family:Georgia">Shopping List (household ${state.household})</h2><ul style="font-family:Georgia;font-size:14px">${items.map(i => `<li>${i}</li>`).join('')}</ul>`);
  w.document.close(); w.print();
};
function showDrawer() { $('shopDrawer').classList.remove('hidden'); }
function closeShop() { $('shopDrawer').classList.add('hidden'); }

// ---------- modal helpers ----------
let _prevFocus = null;
function showModal(id) {
  _prevFocus = document.activeElement;
  const m = $(id); m.classList.remove('hidden'); m.classList.add('flex');
  requestAnimationFrame(() => {
    const first = m.querySelector('button:not([disabled]), input, select, a[href]');
    if (first) first.focus();
  });
}
function closeModal(id) {
  const m = $(id); m.classList.add('hidden'); m.classList.remove('flex');
  if (_prevFocus) { _prevFocus.focus(); _prevFocus = null; }
}
window.closeModal = closeModal; window.closeShop = closeShop;
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { ['pickerModal','viewModal','confirmModal'].forEach(closeModal); closeShop(); }
});

// ---------- nav ----------
function changeMonth(delta) {
  state.month += delta;
  if (state.month < 1) { state.month = 12; state.year--; }
  if (state.month > 12) { state.month = 1; state.year++; }
  refresh();
}
$('prevBtn').onclick = () => changeMonth(-1);
$('nextBtn').onclick = () => changeMonth(1);
function scrollToToday() {
  requestAnimationFrame(() => {
    const cell = document.querySelector('.today-cell');
    if (cell) cell.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
  });
}
$('todayBtn').onclick = async () => { const n = new Date(); state.year = n.getFullYear(); state.month = n.getMonth() + 1; await refresh(); scrollToToday(); };
$('jsonBtn').onclick = () => window.open('/api/export/json', '_blank');
$('sidebarToggle').onclick = () => $('sidebar').classList.toggle('hidden');
$('sidebarClose').onclick = () => $('sidebar').classList.add('hidden');

async function refresh() {
  $('loader').classList.remove('hidden');
  try {
    await loadEntries();
    await loadSeasonal();
    render();
  } finally {
    $('loader').classList.add('hidden');
  }
}

// ---------- init ----------
(async function init() {
  applyTheme(localStorage.getItem('menu-theme') === 'dark');
  await Promise.all([loadRecipes(), loadSettings(), loadLanguages()]);
  await refresh();
  lucide.createIcons();
})();
