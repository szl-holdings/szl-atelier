// SPDX-License-Identifier: Apache-2.0
// Behavioral fixture for the shipped script; no browser, network, or provider.
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const script = readFileSync(process.env.ATELIER_TEST_SCRIPT || path.join(__dirname, '../static/app.js'), 'utf8');
const flush = () => new Promise((resolve) => setImmediate(resolve));

function element() {
  return {
    textContent: '', hidden: false, disabled: false, open: false, dataset: {}, listeners: {},
    append() {}, replaceChildren() {}, setAttribute() {},
    addEventListener(name, fn) { (this.listeners[name] ||= []).push(fn); },
    showModal() { this.open = true; },
    close() { this.open = false; for (const fn of this.listeners.close || []) fn(); },
  };
}

async function fixture(catalog = { items: [] }) {
  const elements = new Map();
  const pending = [];
  const root = { dataset: {} };
  const windowListeners = {};
  let cssZoom = 1;
  let styleObserver = null;
  class MutationObserver {
    constructor(callback) { styleObserver = callback; }
    observe() {}
  }
  const window = {
    innerWidth: 1280, innerHeight: 900,
    visualViewport: { width: 1280, height: 900, scale: 1 },
    getComputedStyle: () => ({ zoom: String(cssZoom) }),
    addEventListener(name, fn) { (windowListeners[name] ||= []).push(fn); },
  };
  window.visualViewport.addEventListener = window.addEventListener.bind(window);
  const get = (id) => { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); };
  const context = vm.createContext({
    AbortController,
    MutationObserver,
    document: { documentElement: root, getElementById: get, createElement: element, addEventListener() {}, querySelectorAll: () => [] },
    window,
    fetch(url, options) {
      if (url === '/api/catalog') {
        if (catalog instanceof Error) return Promise.reject(catalog);
        return Promise.resolve({ ok: true, json: async () => catalog });
      }
      if (url === '/api/source') return Promise.resolve({ ok: true, json: async () => ({ source: {} }) });
      // Deliberately ignore abort: a response can already be queued for parsing.
      return new Promise((resolve, reject) => pending.push({ url, options, resolve, reject }));
    },
  });
  vm.runInContext(script, context);
  await flush();
  const item = (slug) => ({ slug, title: slug, kind: 'model', hub_slug: `SZLHOLDINGS/${slug}`,
    group: 'research', summary: 'fixture', source_repository: 'szl-holdings/fixture', evidence_state: 'DECLARED' });
  return {
    get, pending, root, window,
    setZoom(value) { cssZoom = value; styleObserver?.(); },
    setVisualWidth(value) { window.visualViewport.width = value; for (const listener of windowListeners.resize || []) listener(); },
    open: (slug) => context.openArtifact(item(slug)),
    measure: () => context.measureProvider(), render: () => context.render(),
  };
}

test('public experience exposes a live reflow snapshot and audience state', async () => {
  const f = await fixture();
  assert.equal(f.root.dataset.szlPublicExperienceV3, 'true');
  assert.equal(f.window.SZLPublicExperience.snapshot().effectiveWidth, 1280);
  assert.equal(f.root.dataset.szlAudience, 'user');

  f.setVisualWidth(320);
  assert.equal(f.window.SZLPublicExperience.snapshot().effectiveWidth, 1280);
  assert.equal(f.root.dataset.szlViewportTier, 'desktop');

  f.setZoom(4);
  assert.equal(f.window.SZLPublicExperience.snapshot().effectiveWidth, 320);
  assert.equal(f.root.dataset.szlViewportTier, 'phone');
  assert.equal(f.root.dataset.szlZoomTier, 'extreme');

  f.get('audience-modes').listeners.click[0]({ target: { closest: () => ({ dataset: { mode: 'operator' } }) } });
  assert.equal(f.root.dataset.szlAudience, 'operator');
  assert.equal(f.window.SZLPublicExperience.snapshot().audience, 'operator');
});

function complete(request, name) {
  request.resolve({ ok: true, json: async () => ({ provider: { state: 'MEASURED', slug: name } }) });
}

test('late success for A cannot replace B evidence or unlock B pending request', async () => {
  const f = await fixture();
  f.open('a'); const a = f.measure();
  f.open('b'); const b = f.measure();
  complete(f.pending[0], 'a'); await a;
  assert.equal(f.get('provider-result').textContent, 'Public provider readback in progress.');
  assert.equal(f.get('provider-readback').disabled, true);
  complete(f.pending[1], 'b'); await b;
  assert.equal(JSON.parse(f.get('provider-result').textContent).slug, 'b');
  assert.equal(f.get('provider-readback').disabled, false);
});

test('late rejection for A cannot replace B with an unrelated error', async () => {
  const f = await fixture();
  f.open('a'); const a = f.measure();
  f.open('b');
  f.pending[0].reject(new Error('A provider failed')); await a;
  assert.equal(f.get('provider-result').textContent, '');
  assert.equal(f.get('provider-readback').textContent, 'Measure public Hub state');
});

test('closing cancels the read and discards a late response even for the same reopened artifact', async () => {
  const f = await fixture();
  f.open('a'); const old = f.measure();
  f.get('artifact-dialog').close();
  assert.equal(f.pending[0].options.signal.aborted, true);
  f.open('a'); const current = f.measure();
  complete(f.pending[0], 'old-a'); await old;
  assert.equal(f.get('provider-readback').disabled, true);
  complete(f.pending[1], 'new-a'); await current;
  assert.equal(JSON.parse(f.get('provider-result').textContent).slug, 'new-a');
});

test('selection changes during response decoding also discard the old evidence', async () => {
  const f = await fixture();
  f.open('a'); const a = f.measure();
  let resolveBody;
  f.pending[0].resolve({ ok: true, json: () => new Promise((resolve) => { resolveBody = resolve; }) });
  await flush();
  f.open('b');
  resolveBody({ provider: { slug: 'a' } }); await a;
  assert.equal(f.get('provider-result').textContent, '');
});

test('current provider failures remain visible and permit retry', async () => {
  const f = await fixture();
  f.open('a'); const a = f.measure();
  f.pending[0].resolve({ ok: false, status: 503, json: async () => ({ detail: 'Provider unavailable' }) });
  await a;
  assert.equal(JSON.parse(f.get('provider-result').textContent).state, 'UNAVAILABLE');
  assert.equal(f.get('provider-readback').disabled, false);
  assert.equal(f.get('provider-readback').textContent, 'Measure again');
});

for (const [label, response] of [['network failure', new Error('offline')], ['malformed response', {}]]) {
  test(`catalog ${label} is unavailable, including after a filter rerender`, async () => {
    const f = await fixture(response);
    f.render();
    assert.equal(f.get('result-summary').textContent, 'Catalog unavailable');
    assert.equal(f.get('catalog-error').hidden, false);
    assert.equal(f.get('empty-state').hidden, true);
    assert.notEqual(f.get('artifact-count').textContent, '0');
  });
}

test('a valid empty catalog remains distinct from an unavailable catalog', async () => {
  const f = await fixture();
  assert.equal(f.get('result-summary').textContent, '0 of 0 artifacts shown');
  assert.equal(f.get('catalog-error').hidden, true);
  assert.equal(f.get('empty-state').hidden, false);
});
