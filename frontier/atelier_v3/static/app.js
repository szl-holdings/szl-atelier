/* SPDX-License-Identifier: Apache-2.0 */
'use strict';

const state = {
  items: [],
  mode: 'user',
  group: '',
  query: '',
  selected: null,
};

const modeCopy = {
  user: 'A clear public view of what each artifact does and where its source lives.',
  developer: 'Source repositories, artifact kinds, evidence states, and deterministic receipt boundaries.',
  investor: 'Commercial flagships remain distinct from laboratories, capabilities, and inventory-only research.',
  operator: 'Runtime and provider evidence stays unavailable until explicitly measured and read back.',
};

const byId = (id) => document.getElementById(id);
const grid = byId('catalog-grid');
const constellation = byId('constellation');
const dialog = byId('artifact-dialog');
const providerButton = byId('provider-readback');
const providerResult = byId('provider-result');

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function evidenceBadge(item) {
  const badge = node('span', `evidence-badge state-${String(item.evidence_state).toLowerCase()}`);
  badge.textContent = item.evidence_state;
  return badge;
}

function filteredItems() {
  const query = state.query.trim().toLocaleLowerCase();
  return state.items.filter((item) => {
    if (state.group && item.group !== state.group) return false;
    if (!query) return true;
    const haystack = `${item.slug} ${item.title} ${item.summary} ${item.source_repository} ${item.group}`.toLocaleLowerCase();
    return haystack.includes(query);
  });
}

function modeLine(item) {
  if (state.mode === 'developer') return `${item.kind} · ${item.source_repository}`;
  if (state.mode === 'investor') return item.commercial_flagship ? 'Commercial flagship' : (item.inventory_only ? 'Inventory / research' : 'Platform capability');
  if (state.mode === 'operator') return `${item.evidence_state} evidence · no implicit runtime claim`;
  return item.summary;
}

function artifactButton(item, compact = false) {
  const button = node('button', compact ? 'orbit-node' : 'artifact-card');
  button.type = 'button';
  button.dataset.slug = item.slug;
  button.setAttribute('aria-label', `Open ${item.title} evidence`);

  if (compact) {
    const pulse = node('span', 'orbit-pulse');
    pulse.setAttribute('aria-hidden', 'true');
    button.append(pulse, node('span', 'orbit-label', item.title));
  } else {
    const meta = node('div', 'card-meta');
    meta.append(node('span', 'kind-label', item.kind), evidenceBadge(item));
    const title = node('h3', '', item.title);
    const summary = node('p', 'card-summary', modeLine(item));
    const source = node('p', 'card-source', item.source_repository);
    button.append(meta, title, summary, source);
    if (item.commercial_flagship) button.dataset.flagship = 'true';
    if (item.inventory_only) button.dataset.inventory = 'true';
  }
  button.addEventListener('click', () => openArtifact(item));
  return button;
}

function render() {
  const items = filteredItems();
  grid.replaceChildren(...items.map((item) => artifactButton(item)));
  constellation.replaceChildren(...items.slice(0, 12).map((item) => artifactButton(item, true)));
  byId('artifact-count').textContent = String(state.items.length);
  byId('collection-count').textContent = String(new Set(state.items.map((item) => item.group)).size);
  byId('result-summary').textContent = `${items.length} of ${state.items.length} artifacts shown`;
  byId('empty-state').hidden = items.length !== 0;
  byId('view-description').textContent = modeCopy[state.mode];
}

function addEvidence(term, value) {
  const list = byId('dialog-evidence');
  const dt = node('dt', '', term);
  const dd = node('dd', '', value === null || value === undefined || value === '' ? 'UNAVAILABLE' : String(value));
  list.append(dt, dd);
}

function safeSourceUrl(repository) {
  return /^szl-holdings\/[A-Za-z0-9._-]+$/.test(repository)
    ? `https://github.com/${repository}`
    : 'https://github.com/szl-holdings';
}

function openArtifact(item) {
  state.selected = item;
  byId('dialog-kind').textContent = `${item.group} / ${item.kind}`.toUpperCase();
  byId('dialog-title').textContent = item.title;
  byId('dialog-summary').textContent = item.summary;
  byId('dialog-evidence').replaceChildren();
  addEvidence('Source owner', item.source_repository);
  addEvidence('Hub identity', item.hub_slug);
  addEvidence('Evidence state', item.evidence_state);
  addEvidence('Commercial flagship', item.commercial_flagship ? 'YES' : 'NO');
  addEvidence('Inventory only', item.inventory_only ? 'YES' : 'NO');
  byId('dialog-source').href = safeSourceUrl(item.source_repository);
  providerButton.hidden = !item.hub_slug || !['model', 'dataset', 'space'].includes(item.kind);
  providerButton.disabled = false;
  providerButton.textContent = 'Measure public Hub state';
  providerResult.hidden = true;
  providerResult.textContent = '';
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else dialog.setAttribute('open', '');
}

async function measureProvider() {
  const item = state.selected;
  if (!item || !item.hub_slug) return;
  providerButton.disabled = true;
  providerButton.textContent = 'Measuring…';
  providerResult.hidden = false;
  providerResult.textContent = 'Public provider readback in progress.';
  try {
    const response = await fetch(`/api/catalog/${encodeURIComponent(item.kind)}/${encodeURIComponent(item.slug)}?live=true`, {
      method: 'GET',
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
    providerResult.textContent = JSON.stringify(payload.provider, null, 2);
  } catch (error) {
    providerResult.textContent = JSON.stringify({ state: 'UNAVAILABLE', error: String(error.message || error) }, null, 2);
  } finally {
    providerButton.disabled = false;
    providerButton.textContent = 'Measure again';
  }
}

async function loadSource() {
  try {
    const response = await fetch('/api/source', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const source = payload.source || {};
    byId('source-state').textContent = source.state === 'MEASURED'
      ? `Source ${String(source.revision).slice(0, 12)} verified locally`
      : 'Source revision unavailable — no runtime claim';
  } catch (_error) {
    byId('source-state').textContent = 'Source evidence unavailable';
  }
}

async function loadCatalog() {
  try {
    const response = await fetch('/api/catalog', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    state.items = Array.isArray(payload.items) ? payload.items : [];
    const groups = [...new Set(state.items.map((item) => item.group))].sort();
    const select = byId('group-filter');
    groups.forEach((group) => {
      const option = document.createElement('option');
      option.value = group;
      option.textContent = group.replaceAll('-', ' ');
      select.append(option);
    });
    render();
  } catch (_error) {
    byId('result-summary').textContent = 'Catalog unavailable';
    byId('empty-state').hidden = false;
  }
}

byId('search').addEventListener('input', (event) => {
  state.query = event.target.value;
  render();
});

byId('group-filter').addEventListener('change', (event) => {
  state.group = event.target.value;
  render();
});

byId('audience-modes').addEventListener('click', (event) => {
  const button = event.target.closest('button[data-mode]');
  if (!button) return;
  state.mode = button.dataset.mode;
  document.querySelectorAll('#audience-modes button').forEach((candidate) => {
    candidate.setAttribute('aria-pressed', String(candidate === button));
  });
  render();
});

providerButton.addEventListener('click', measureProvider);
dialog.addEventListener('click', (event) => {
  if (event.target === dialog) dialog.close();
});

document.addEventListener('keydown', (event) => {
  if (event.key === '/' && !event.ctrlKey && !event.metaKey && document.activeElement?.tagName !== 'INPUT') {
    event.preventDefault();
    byId('search').focus();
  }
});

Promise.all([loadCatalog(), loadSource()]);
