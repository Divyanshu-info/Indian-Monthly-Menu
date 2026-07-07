// ---------- Recipe Library ----------
const MEAL_TABS = ['all', 'breakfast', 'lunch', 'dinner', 'dessert', 'beverage'];
const $ = (id) => document.getElementById(id);
const api = async (url, opts) => {
  const r = await fetch(url, opts);
  if (!r.ok) { let e; try { e = await r.json(); } catch { e = { detail: r.statusText }; } throw { status: r.status, ...e }; }
  return r.status === 204 ? null : r.json();
};
function toast(m) { const t = $('toast'); t.textContent = m; t.classList.remove('hidden'); setTimeout(() => t.classList.add('hidden'), 2200); }
function debounce(fn, ms) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

let recipes = [];
let activeMeal = 'all';
let editId = null;

// theme
function applyTheme(dark) {
  document.documentElement.classList.toggle('dark', dark);
  localStorage.setItem('menu-theme', dark ? 'dark' : 'light');
  $('themeBtn').innerHTML = `<i data-lucide="${dark ? 'sun' : 'moon'}" class="w-5 h-5"></i>`;
  lucide.createIcons();
}
$('themeBtn').onclick = () => applyTheme(!document.documentElement.classList.contains('dark'));

// modal helpers
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
window.closeModal = closeModal;
document.addEventListener('keydown', e => { if (e.key === 'Escape') ['formModal', 'blockModal'].forEach(closeModal); });

// tabs
function renderTabs() {
  $('mealTabs').innerHTML = MEAL_TABS.map(m =>
    `<button class="mtab px-3 py-1.5 rounded-lg text-sm font-medium capitalize surface brd border ${m === activeMeal ? 'tab-on' : ''}" data-m="${m}">${m}</button>`
  ).join('');
  document.querySelectorAll('.mtab').forEach(b => b.onclick = () => { activeMeal = b.dataset.m; renderTabs(); renderGrid(); });
}

const chilli = (s) => ({ Mild: '🌶️', Medium: '🌶️🌶️', Spicy: '🌶️🌶️🌶️' }[s] || '');
const TAG_EMOJI = { 'Festive': '🎉', 'Kids Friendly': '👨‍👩‍👧', 'Quick': '⚡', 'High Protein': '💪', 'Vegetarian': '🥬', 'Non-Veg': '🍗' };

function cardHTML(r) {
  const badge = (t, extra = '') => `<span class="text-[11px] px-2 py-0.5 rounded-full panel ${extra}">${t}</span>`;
  const tags = (r.tags || '').split(',').filter(Boolean).map(t => badge(`${TAG_EMOJI[t.trim()] || ''} ${t.trim()}`)).join('');
  return `<div class="surface brd border rounded-xl p-4 flex flex-col gap-2">
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0">
        <h3 class="font-bold truncate">${r.name} ${r.is_weekend_special ? '⭐' : ''}</h3>
        <p class="hindi text-sm truncate" style="color:var(--muted)">${r.name_hindi || ''}</p>
      </div>
      <div class="flex gap-1 shrink-0">
        <button class="edit-btn p-1.5 rounded-lg hover:bg-black/5 dark:hover:bg-white/10" data-id="${r.id}"><i data-lucide="pencil" class="w-4 h-4"></i></button>
        <button class="del-btn p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 text-red-600" data-id="${r.id}"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
      </div>
    </div>
    <div class="flex flex-wrap gap-1.5">
      ${badge(r.meal_type, 'capitalize')}${badge(r.season)}${badge(r.region)}${badge(`${chilli(r.spice_level)} ${r.spice_level}`)}${badge(`Serves ${r.servings}`)}
    </div>
    ${tags ? `<div class="flex flex-wrap gap-1.5">${tags}</div>` : ''}
    <p class="text-sm" style="color:var(--muted)">${r.description || ''}</p>
  </div>`;
}

function renderGrid() {
  const q = $('search').value.toLowerCase();
  const region = $('fRegion').value, season = $('fSeason').value, spice = $('fSpice').value, tag = $('fTag').value;
  const list = recipes.filter(r =>
    (activeMeal === 'all' || r.meal_type === activeMeal) &&
    (!q || r.name.toLowerCase().includes(q) || (r.name_hindi || '').includes(q)) &&
    (!region || r.region === region) && (!season || r.season === season) &&
    (!spice || r.spice_level === spice) && (!tag || (r.tags || '').includes(tag))
  );
  $('grid').innerHTML = list.map(cardHTML).join('');
  $('empty').classList.toggle('hidden', list.length > 0);
  const total = recipes.filter(r => activeMeal === 'all' || r.meal_type === activeMeal).length;
  $('resultCount').textContent = list.length < total
    ? `Showing ${list.length} of ${total} recipes`
    : `${total} recipe${total !== 1 ? 's' : ''}`;
  document.querySelectorAll('.edit-btn').forEach(b => b.onclick = () => openForm(+b.dataset.id));
  document.querySelectorAll('.del-btn').forEach(b => b.onclick = () => del(+b.dataset.id));
  lucide.createIcons();
}

$('search').addEventListener('input', debounce(renderGrid, 200));
['fRegion', 'fSeason', 'fSpice', 'fTag'].forEach(id => $(id).addEventListener('input', renderGrid));

// form
function clearForm() {
  ['fName', 'fNameHi', 'fRegionIn', 'fBev', 'fDesc', 'fAccomp', 'fSides', 'fIng', 'fIns'].forEach(id => $(id).value = '');
  $('fRegionIn').value = 'Pan-Indian'; $('fServings').value = 4; $('fMeal').value = 'breakfast';
  $('fSeasonIn').value = 'All'; $('fSpiceIn').value = 'Medium'; $('fWeekend').checked = false;
  document.querySelectorAll('#fTags input[type=checkbox]').forEach(c => { if (c.id !== 'fWeekend') c.checked = false; });
}
function openForm(id) {
  editId = id || null;
  clearForm();
  if (id) {
    const r = recipes.find(x => x.id === id); if (!r) return;
    $('formTitle').textContent = 'Edit Recipe';
    $('fName').value = r.name; $('fNameHi').value = r.name_hindi || ''; $('fMeal').value = r.meal_type;
    $('fSeasonIn').value = r.season; $('fRegionIn').value = r.region; $('fSpiceIn').value = r.spice_level;
    $('fServings').value = r.servings; $('fBev').value = r.suggested_beverage || ''; $('fDesc').value = r.description || '';
    $('fAccomp').value = r.accompaniment || ''; $('fSides').value = r.suggested_sides || '';
    $('fIng').value = r.ingredients || ''; $('fIns').value = r.instructions || '';
    $('fWeekend').checked = !!r.is_weekend_special;
    const set = new Set((r.tags || '').split(',').map(t => t.trim()));
    document.querySelectorAll('#fTags input[type=checkbox]').forEach(c => { if (c.id !== 'fWeekend') c.checked = set.has(c.value); });
  } else {
    $('formTitle').textContent = 'Add Recipe';
  }
  showModal('formModal');
}
$('addBtn').onclick = () => openForm(null);

$('saveBtn').onclick = async () => {
  const tags = [...document.querySelectorAll('#fTags input[type=checkbox]')].filter(c => c.id !== 'fWeekend' && c.checked).map(c => c.value).join(',');
  const payload = {
    name: $('fName').value.trim(), name_hindi: $('fNameHi').value.trim(), meal_type: $('fMeal').value,
    season: $('fSeasonIn').value, region: $('fRegionIn').value.trim(), spice_level: $('fSpiceIn').value,
    servings: parseInt($('fServings').value) || 4, suggested_beverage: $('fBev').value.trim(),
    description: $('fDesc').value.trim(), accompaniment: $('fAccomp').value.trim(), suggested_sides: $('fSides').value.trim(),
    tags, is_weekend_special: $('fWeekend').checked, ingredients: $('fIng').value.trim(), instructions: $('fIns').value.trim(),
  };
  if (!payload.name || !payload.meal_type || !payload.season || !payload.ingredients) {
    toast('Name, meal type, season and ingredients are required'); return;
  }
  try {
    if (editId) await api(`/api/recipes/${editId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    else await api('/api/recipes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    closeModal('formModal');
    await load(); toast(editId ? 'Recipe updated' : 'Recipe added');
  } catch (e) { toast('Save failed: ' + (e.detail || e.status)); }
};

async function del(id) {
  const r = recipes.find(x => x.id === id);
  if (!confirm(`Delete "${r.name}"?`)) return;
  try {
    await api(`/api/recipes/${id}`, { method: 'DELETE' });
    await load(); toast('Recipe deleted');
  } catch (e) {
    if (e.status === 409 && e.detail && e.detail.days) {
      $('blockDays').innerHTML = e.detail.days.map(d => `<li>${d}</li>`).join('');
      showModal('blockModal');
    } else { toast('Delete failed'); }
  }
}

async function load() {
  recipes = await api('/api/recipes');
  const regions = [...new Set(recipes.map(r => r.region))].sort();
  const cur = $('fRegion').value;
  $('fRegion').innerHTML = '<option value="">All Regions</option>' + regions.map(r => `<option>${r}</option>`).join('');
  $('fRegion').value = cur;
  renderGrid();
}

(async function init() {
  applyTheme(localStorage.getItem('menu-theme') === 'dark');
  renderTabs();
  await load();
  lucide.createIcons();
  const params = new URLSearchParams(location.search);
  if (params.get('edit')) openForm(+params.get('edit'));
})();
