// SPDX-License-Identifier: Apache-2.0
// Local presentation proof only. No outside traffic, writes, inference, or provider calls.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const base = new URL(process.env.PREVIEW_BASE_URL);
assert.equal(base.hostname, '127.0.0.1', 'serve a local fixture');
const source = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
assert.equal(source, process.env.EXPECTED_SOURCE_REVISION);
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE_PATH).href);
const directory = process.env.NATIVE_REPORT_DIR || 'reports/atelier-native';
fs.mkdirSync(directory, { recursive: true });
const report = {
  schema: 'szl.atelier-native-preview/v1', source_revision: source,
  working_tree_dirty: Boolean(execFileSync('git', ['status', '--porcelain'], { encoding: 'utf8' }).trim()),
  observed_at: new Date().toISOString(),
  scope: 'Local served UI; provider cases use intercepted fixtures. CSS zoom is not native browser zoom.',
  live_verified: false, effects_executed: false, cases: [], complete: false,
};
const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? {
  executablePath: process.env.CHROMIUM_EXECUTABLE, args: ['--no-sandbox', '--disable-dev-shm-usage'],
} : {}) });
const items = Array.from({ length: 17 }, (_, i) => ({ slug: `fixture-${i}`, title: `Local fixture ${i}`,
  kind: i % 2 ? 'dataset' : 'model', hub_slug: `SZLHOLDINGS/local-fixture-${i}`, group: i % 2 ? 'research' : 'models',
  summary: 'Intercepted presentation fixture; no actual provider or model is called.',
  source_repository: 'szl-holdings/szl-atelier', evidence_state: 'DECLARED',
  commercial_flagship: false, inventory_only: true,
}));
const json = (route, payload, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(payload) });

async function scenario(name, options, fixtures, run) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, colorScheme: 'dark', reducedMotion: 'reduce', ...options });
  const blocked = [], errors = [];
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await context.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url());
    if (request.method() !== 'GET' || url.origin !== base.origin) {
      blocked.push({ method: request.method(), url: request.url() });
      return route.abort('blockedbyclient');
    }
    if (fixtures && await fixtures(route, url)) return;
    if (url.searchParams.get('live') === 'true') {
      blocked.push({ method: request.method(), url: request.url(), reason: 'provider readback has no fixture' });
      return route.abort('blockedbyclient');
    }
    return route.continue();
  });
  const result = { name, passed: false, blocked_requests: blocked, page_errors: errors };
  try {
    const response = await page.goto(base.href, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200);
    await run(page, result);
    assert.equal(blocked.length, 0, 'a request crossed the local read-only boundary');
    assert.equal(errors.length, 0, 'page errors');
    result.passed = true;
  } catch (error) { result.error = error.message; }
  if (!result.passed || /1440|320|400|dialog|no-script/.test(name)) {
    const file = `${name}.png`;
    await page.screenshot({ path: path.join(directory, file), fullPage: false });
    result.screenshot = file;
  }
  report.cases.push(result);
  await context.close();
}

async function layout(page, result, zoom = 1) {
  await page.locator('.artifact-card').first().waitFor();
  if (zoom !== 1) await page.evaluate(value => { document.documentElement.style.zoom = String(value); }, zoom);
  result.layout = await page.evaluate(() => {
    const root = document.documentElement;
    const img = document.querySelector('.native-mark img');
    const visible = element => element.getBoundingClientRect().width > 0 && element.getBoundingClientRect().height > 0;
    const clipped = [...document.querySelectorAll('h1,h2,h3')].filter(e => visible(e) && e.scrollWidth > e.clientWidth + 1).map(e => e.textContent);
    const rgb = value => {
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
      const ctx = canvas.getContext('2d'); ctx.fillStyle = value; ctx.fillRect(0,0,1,1);
      return [...ctx.getImageData(0,0,1,1).data].slice(0,3);
    };
    const luminance = color => rgb(color).map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((sum,v,i) => sum + v * [.2126,.7152,.0722][i],0);
    const action = getComputedStyle(document.querySelector('.segmented [aria-pressed="true"]'));
    const a = luminance(action.color), b = luminance(action.backgroundColor);
    return { theme: root.dataset.surface, overflow_px: root.scrollWidth-root.clientWidth, clipped_headings: clipped,
      h1_count: document.querySelectorAll('h1').length, image_loaded: img.complete && img.naturalWidth > 0,
      icon_width: parseFloat(getComputedStyle(img).width), clear_space: parseFloat(getComputedStyle(img.parentElement).paddingLeft),
      action_contrast: (Math.max(a,b)+.05)/(Math.min(a,b)+.05),
      source_label: document.querySelector('#source-state').textContent,
      constellation_valid: [...document.querySelector('#constellation').children].every(e => e.tagName === 'LI'),
    };
  });
  assert.ok(result.layout.overflow_px <= 1);
  assert.deepEqual(result.layout.clipped_headings, []);
  assert.equal(result.layout.h1_count, 1);
  assert.ok(result.layout.image_loaded && result.layout.icon_width === 32 && result.layout.clear_space >= 8);
  assert.ok(result.layout.action_contrast >= 4.5, `action contrast ${result.layout.action_contrast}`);
  assert.ok(result.layout.constellation_valid);
  assert.ok(result.layout.source_label.startsWith('Reported source '));
  assert.ok(!/verified/i.test(result.layout.source_label));
}

try {
  for (const [name,width,height,scheme,zoom] of [
    ['dark-320',320,812,'dark',1],['dark-390',390,844,'dark',1],['dark-768',768,1024,'dark',1],
    ['dark-1440',1440,1000,'dark',1],['light-320',320,812,'light',1],['light-1440',1440,1000,'light',1],
    ['css-zoom-200',1280,900,'dark',2],['css-zoom-400',1280,900,'dark',4],['light-zoom-400',1280,900,'light',4],
  ]) await scenario(name,{viewport:{width,height},colorScheme:scheme},null,(page,result) => layout(page,result,zoom));

  await scenario('forced-colors',{ viewport:{width:375,height:812}, forcedColors:'active' },null,async (page,result) => {
    await page.locator('.artifact-card').first().waitFor();
    result.overflow_px = await page.evaluate(() => document.documentElement.scrollWidth-document.documentElement.clientWidth);
    assert.ok(result.overflow_px <= 1);
    await page.getByRole('button',{name:'Use light theme'}).focus();
    const outline = await page.getByRole('button',{name:'Use light theme'}).evaluate(e => getComputedStyle(e).outlineStyle);
    assert.notEqual(outline, 'none');
  });
  await scenario('no-script-320',{viewport:{width:320,height:812},javaScriptEnabled:false},null,async page => {
    assert.equal(await page.locator('.noscript').isVisible(),true);
    assert.equal(await page.locator('.noscript a[href="/api/catalog"]').isVisible(),true);
    assert.equal(await page.locator('#catalog-controls').isVisible(),false);
    assert.equal(await page.locator('#theme-toggle').isVisible(),false);
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('.skip-link').evaluate(e => e === document.activeElement),true);
  });

  const catalogFixture = async (route,url) => { if (url.pathname === '/api/catalog') { await json(route,{items}); return true; } return false; };
  await scenario('catalog-controls',{},catalogFixture,async page => {
    await page.locator('.artifact-card').first().waitFor();
    assert.equal(await page.locator('.artifact-card').count(),17);
    assert.equal(await page.locator('#constellation > li').count(),12);
    assert.equal(await page.locator('#constellation-summary').textContent(),'12 of 17 matching artifacts previewed. The full catalog follows.');
    await page.locator('#search').fill('nothing-will-match');
    assert.equal(await page.locator('#empty-state').isVisible(),true);
    await page.getByRole('button',{name:'Clear search and collection'}).click();
    assert.equal(await page.locator('.artifact-card').count(),17);
    assert.equal(await page.locator('#search').evaluate(e => e === document.activeElement),true);
    await page.locator('#group-filter').selectOption('research');
    assert.equal(await page.locator('.artifact-card').count(),8);
    await page.locator('#group-filter').focus(); await page.keyboard.press('/');
    assert.equal(await page.locator('#group-filter').evaluate(e => e === document.activeElement),true);
    await page.getByRole('button',{name:'Developer',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'Developer',exact:true}).getAttribute('aria-pressed'),'true');
    await page.keyboard.press('/');
    assert.equal(await page.locator('#search').evaluate(e => e === document.activeElement),true);
    await page.getByRole('button',{name:'Use light theme'}).click();
    assert.equal(await page.locator('html').getAttribute('data-surface'),'light');
  });

  let reads = 0;
  await scenario('dialog-provider-fixture',{viewport:{width:390,height:844}},async (route,url) => {
    if (await catalogFixture(route,url)) return true;
    if (url.searchParams.get('live') === 'true') {
      reads++;
      await json(route,reads === 1 ? {provider:{state:'MEASURED',fixture:true,runtime:{stage:'RUNNING'}}} : {detail:'fixture unavailable'},reads === 1 ? 200 : 503);
      return true;
    }
    return false;
  },async page => {
    await page.locator('.artifact-card button').first().click();
    assert.equal(reads,0,'opening detail never measures the provider');
    await page.screenshot({ path: path.join(directory,'dialog-open-390.png') });
    assert.equal(await page.locator('#artifact-dialog').evaluate(e => e.open),true);
    await page.keyboard.press('/');
    assert.equal(await page.locator('#search').evaluate(e => e === document.activeElement),false);
    await page.getByRole('button',{name:'Measure public Hub state',exact:true}).click();
    await page.getByRole('button',{name:'Measure again',exact:true}).waitFor();
    assert.match(await page.locator('#provider-status').innerText(),/source parity remain separate/);
    assert.match(await page.locator('#provider-result').innerText(),/"fixture": true/);
    await page.getByRole('button',{name:'Measure again',exact:true}).click();
    await page.getByRole('button',{name:'Measure again',exact:true}).waitFor();
    assert.match(await page.locator('#provider-status').innerText(),/could not be read/);
    assert.match(await page.locator('#provider-result').innerText(),/UNAVAILABLE/);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#artifact-dialog').evaluate(e => e.open),false);
    assert.equal(await page.locator('.artifact-card button').first().evaluate(e => e === document.activeElement),true);
  });

  let attempts = 0;
  await scenario('catalog-retry',{},async (route,url) => {
    if (url.pathname === '/api/catalog') { await json(route,++attempts === 1 ? {detail:'fixture outage'} : {items},attempts === 1 ? 503 : 200); return true; }
    return false;
  },async page => {
    await page.locator('#catalog-error').waitFor();
    assert.equal(await page.locator('#empty-state').isVisible(),false);
    await page.getByRole('button',{name:'Retry catalog',exact:true}).click();
    await page.locator('.artifact-card').first().waitFor();
    assert.equal(await page.locator('.artifact-card').count(),17);
    assert.equal(await page.locator('#group-filter option').count(),3);
    assert.equal(await page.locator('#catalog-grid').getAttribute('aria-busy'),'false');
  });
  await scenario('valid-empty-catalog',{},async (route,url) => {
    if (url.pathname === '/api/catalog') { await json(route,{items:[]}); return true; } return false;
  },async page => {
    await page.locator('#empty-state').waitFor();
    assert.equal(await page.locator('#catalog-error').isVisible(),false);
    assert.equal(await page.locator('#artifact-count').textContent(),'0');
  });
  await scenario('malformed-source-identity',{},async (route,url) => {
    if (url.pathname === '/api/source') { await json(route,{source:{state:'MEASURED',revision:'not-an-exact-commit'}}); return true; } return false;
  },async page => {
    await page.locator('.artifact-card').first().waitFor();
    assert.match(await page.locator('#source-state').innerText(),/unavailable/);
    assert.equal(await page.locator('#source-indicator').getAttribute('data-state'),'unavailable');
  });
  report.complete = true;
} finally {
  await browser.close();
  fs.writeFileSync(path.join(directory,'report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(c=>c.passed).length,complete:report.complete}));
}
assert.ok(report.complete && report.cases.every(result => result.passed),'inspect retained native presentation exceptions');
