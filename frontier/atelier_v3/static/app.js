/* SPDX-License-Identifier: Apache-2.0 */
'use strict';

const state = {
  items: [],
  mode: 'user',
  group: '',
  query: '',
  selected: null,
  catalogStatus: 'loading',
};

const modeCopy = {
  user: 'A clear public view of what each artifact does and where its source lives.',
  developer: 'Source repositories, artifact kinds, evidence states, and deterministic receipt boundaries.',
  investor: 'Commercial flagships remain distinct from laboratories, capabilities, and inventory-only research.',
  operator: 'Runtime and provider evidence stays unavailable until explicitly measured and read back.',
};

function publicExperienceSnapshot() {
  const root = document.documentElement;
  const parsedZoom = Number.parseFloat(window.getComputedStyle(root).zoom);
  const zoom = Number.isFinite(parsedZoom) && parsedZoom > 0 ? parsedZoom : 1;
  const width = Math.max(1, Math.round(Number(window.visualViewport?.width) || 0),
    Math.round(Number(window.innerWidth) || 0), Math.round(Number(root.clientWidth) || 0));
  const height = Math.max(1, Math.round(Number(window.visualViewport?.height) || 0),
    Math.round(Number(window.innerHeight) || 0), Math.round(Number(root.clientHeight) || 0));
  const effectiveWidth = Math.max(280, Math.round(width / zoom));
  const viewportTier = effectiveWidth < 480 ? 'phone'
    : effectiveWidth < 768 ? 'compact'
      : effectiveWidth < 1024 ? 'tablet'
        : effectiveWidth < 1440 ? 'desktop'
          : effectiveWidth < 1920 ? 'wide'
            : effectiveWidth < 2560 ? 'theatre' : 'ultrawide';
  const zoomTier = zoom >= 3 ? 'extreme' : zoom >= 1.5 ? 'high' : 'normal';
  return Object.freeze({ width, height, effectiveWidth, zoom, zoomTier, viewportTier, audience: state.mode });
}

function syncPublicExperience() {
  const snapshot = publicExperienceSnapshot();
  const root = document.documentElement;
  root.dataset.szlViewportTier = snapshot.viewportTier;
  root.dataset.szlZoomTier = snapshot.zoomTier;
  root.dataset.szlAudience = snapshot.audience;
  root.dataset.szlPublicExperienceV3 = 'true';
}

window.SZLPublicExperience = Object.freeze({ snapshot: publicExperienceSnapshot });
window.addEventListener('resize', syncPublicExperience);
window.visualViewport?.addEventListener?.('resize', syncPublicExperience);
const zoomObserver = new MutationObserver(syncPublicExperience);
zoomObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['style'] });
syncPublicExperience();

const byId = (id) => document.getElementById(id);
document.documentElement.dataset.jsReady = 'true';
const grid = byId('catalog-grid');
const constellation = byId('constellation');
const dialog = byId('artifact-dialog');
const providerButton = byId('provider-readback');
const providerResult = byId('provider-result');
const providerStatus = byId('provider-status');
const themeButton = byId('theme-toggle');

function setTheme(surface) {
  document.documentElement.dataset.surface = surface === 'light' ? 'light' : 'dark';
  themeButton.textContent = surface === 'light' ? 'Use dark theme' : 'Use light theme';
}

setTheme(window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
themeButton.hidden = false;
themeButton.addEventListener('click', () => {
  setTheme(document.documentElement.dataset.surface === 'light' ? 'dark' : 'light');
});

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
  const button = node('button', compact ? 'orbit-node' : 'artifact-open');
  button.type = 'button';
  button.dataset.slug = item.slug;
  button.setAttribute('aria-label', `Open ${item.title} evidence`);
  button.addEventListener('click', () => openArtifact(item));

  if (compact) {
    const pulse = node('span', 'orbit-pulse');
    pulse.setAttribute('aria-hidden', 'true');
    button.append(pulse, node('span', 'orbit-label', item.title));
    return button;
  } else {
    const card = node('article', 'artifact-card');
    card.dataset.slug = item.slug;
    const meta = node('div', 'card-meta');
    meta.append(node('span', 'kind-label', item.kind), evidenceBadge(item));
    const title = node('h3');
    button.textContent = item.title;
    title.append(button);
    const summary = node('p', 'card-summary', modeLine(item));
    const source = node('p', 'card-source', item.source_repository);
    card.append(meta, title, summary, source);
    if (item.commercial_flagship) card.dataset.flagship = 'true';
    if (item.inventory_only) card.dataset.inventory = 'true';
    return card;
  }
}

function render() {
  grid.setAttribute('aria-busy', String(state.catalogStatus === 'loading'));
  byId('retry-catalog').disabled = state.catalogStatus === 'loading';
  byId('clear-filters').hidden = !state.query && !state.group;
  if (state.catalogStatus !== 'ready') {
    grid.replaceChildren();
    constellation.replaceChildren();
    constellation.hidden = true;
    byId('artifact-count').textContent = '—';
    byId('collection-count').textContent = '—';
    byId('constellation-summary').textContent = state.catalogStatus === 'unavailable'
      ? 'Constellation unavailable until the catalog can be read.' : 'Reading the locally served catalog…';
    byId('result-summary').textContent = state.catalogStatus === 'unavailable' ? 'Catalog unavailable' : 'Loading catalog.';
    byId('catalog-error').hidden = state.catalogStatus !== 'unavailable';
    byId('empty-state').hidden = true;
    return;
  }
  byId('catalog-error').hidden = true;
  const items = filteredItems();
  grid.replaceChildren(...items.map((item) => artifactButton(item)));
  constellation.replaceChildren(...items.slice(0, 12).map((item) => {
    const entry = node('li', 'constellation-entry');
    entry.append(artifactButton(item, true));
    return entry;
  }));
  constellation.hidden = items.length === 0;
  byId('constellation-summary').textContent = `${Math.min(12, items.length)} of ${items.length} matching artifacts previewed. The full catalog follows.`;
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

let providerRequest = null;

function cancelProviderReadback() {
  if (providerRequest) providerRequest.abort();
  providerRequest = null;
}

function openArtifact(item) {
  cancelProviderReadback();
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
  providerStatus.textContent = providerButton.hidden ? 'No public Hub measurement is available for this artifact kind.'
    : 'Provider metadata is read only when you request it. A provider response does not establish source parity.';
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else dialog.setAttribute('open', '');
}

async function measureProvider() {
  const item = state.selected;
  if (!item || !item.hub_slug) return;
  cancelProviderReadback();
  const request = new AbortController();
  providerRequest = request;
  const isCurrent = () => providerRequest === request && state.selected === item && dialog.open;
  providerButton.disabled = true;
  providerButton.textContent = 'Measuring…';
  providerResult.hidden = false;
  providerResult.textContent = 'Public provider readback in progress.';
  providerStatus.textContent = 'Reading public Hub metadata…';
  try {
    const response = await fetch(`/api/catalog/${encodeURIComponent(item.kind)}/${encodeURIComponent(item.slug)}?live=true`, {
      method: 'GET',
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
      signal: request.signal,
    });
    const payload = await response.json();
    if (!isCurrent()) return;
    if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
    providerResult.textContent = JSON.stringify(payload.provider, null, 2);
    providerStatus.textContent = payload.provider?.state === 'MEASURED'
      ? 'Public metadata received. Inspect the response below; runtime and source parity remain separate checks.'
      : 'Public metadata is unavailable. Inspect the response below for its reported state.';
  } catch (error) {
    if (isCurrent()) {
      providerResult.textContent = JSON.stringify({ state: 'UNAVAILABLE', error: String(error.message || error) }, null, 2);
      providerStatus.textContent = 'Public metadata could not be read. You can try again.';
    }
  } finally {
    if (isCurrent()) {
      providerRequest = null;
      providerButton.disabled = false;
      providerButton.textContent = 'Measure again';
    }
  }
}

async function loadSource() {
  try {
    const response = await fetch('/api/source', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const source = payload.source || {};
    const reported = source.state === 'MEASURED' && /^[0-9a-f]{40}$/.test(String(source.revision));
    byId('source-indicator').dataset.state = reported ? 'reported' : 'unavailable';
    byId('source-state').textContent = reported
      ? `Reported source ${source.revision.slice(0, 12)}`
      : 'Source revision unavailable — no runtime claim';
  } catch (_error) {
    byId('source-indicator').dataset.state = 'unavailable';
    byId('source-state').textContent = 'Source evidence unavailable';
  }
}

let catalogRequest = 0;

async function loadCatalog() {
  const request = ++catalogRequest;
  state.catalogStatus = 'loading';
  render();
  try {
    const response = await fetch('/api/catalog', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (request !== catalogRequest) return;
    if (!Array.isArray(payload.items)) throw new Error('Catalog items unavailable');
    state.items = payload.items;
    state.catalogStatus = 'ready';
    const groups = [...new Set(state.items.map((item) => item.group))].sort();
    const select = byId('group-filter');
    const allCollections = node('option', '', 'All collections');
    allCollections.value = '';
    select.replaceChildren(allCollections);
    groups.forEach((group) => {
      const option = document.createElement('option');
      option.value = group;
      option.textContent = group.replaceAll('-', ' ');
      select.append(option);
    });
    if (state.group && !groups.includes(state.group)) state.group = '';
    select.value = state.group;
    render();
  } catch (_error) {
    if (request !== catalogRequest) return;
    state.catalogStatus = 'unavailable';
    render();
  }
}

byId('search').addEventListener('input', (event) => {
  state.query = event.target.value;
  render();
});

byId('clear-filters').addEventListener('click', () => {
  state.query = '';
  state.group = '';
  byId('search').value = '';
  byId('group-filter').value = '';
  render();
  byId('search').focus();
});
byId('retry-catalog').addEventListener('click', loadCatalog);

byId('group-filter').addEventListener('change', (event) => {
  state.group = event.target.value;
  render();
});

byId('audience-modes').addEventListener('click', (event) => {
  const button = event.target.closest('button[data-mode]');
  if (!button) return;
  state.mode = button.dataset.mode;
  syncPublicExperience();
  document.querySelectorAll('#audience-modes button').forEach((candidate) => {
    candidate.setAttribute('aria-pressed', String(candidate === button));
  });
  render();
});

providerButton.addEventListener('click', measureProvider);
dialog.addEventListener('close', cancelProviderReadback);
dialog.addEventListener('cancel', cancelProviderReadback);
dialog.addEventListener('click', (event) => {
  if (event.target === dialog) dialog.close();
});

document.addEventListener('keydown', (event) => {
  const active = document.activeElement;
  const editing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(active?.tagName) || active?.isContentEditable;
  if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !editing && !dialog.open) {
    event.preventDefault();
    byId('search').focus();
  }
});

Promise.all([loadCatalog(), loadSource()]);
