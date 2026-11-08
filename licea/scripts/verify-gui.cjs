const {chromium} = require('C:/Users/lukasz/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const origin = process.env.ATLAS_TEST_URL || 'http://127.0.0.1:8765';

(async () => {
  const browser = await chromium.launch({headless:true, channel:'msedge'});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}}), errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(origin, {waitUntil:'networkidle'});
    await page.waitForSelector('#dataTab');
    assert.equal(await page.evaluate(() => window.DATA_API_READY), true);
    const response = await page.request.get(origin + '/api/datasets');
    assert.equal(response.status(), 200);
    const before = await response.json();
    const published = JSON.parse(await fs.readFile(path.join(__dirname, '../server/seed.json'), 'utf8'));
    assert.deepEqual(before, {datasets:published, revisions:{}});
    assert.equal(await page.locator('#importForm, #importPreview, #saveImport, #fetchRanking').count(), 0);
    await page.click('#dataTab');
    assert(!/import|zapisz/i.test(await page.locator('#dataPanel').innerText()));
    await page.selectOption('#exportYear', '2025');
    async function download(button) {
      const event = page.waitForEvent('download'); await page.click(button);
      return fs.readFile(await (await event).path());
    }
    const csvBytes = await download('#exportCSV'), csv = csvBytes.toString('utf8');
    assert.equal(csvBytes.subarray(0,3).toString('hex'), 'efbbbf');
    assert(csv.includes('Witkowskiego'));
    const expectedRows = before.datasets['2025'].schools.reduce((count, school) => count + Object.values(school.rankings).filter(Boolean).length, 0);
    assert.equal(csv.split('\r\n').length, expectedRows + 2);
    assert.deepEqual(JSON.parse((await download('#exportJSON')).toString('utf8')), before.datasets['2025']);

    // Same-origin requests previously accepted by the public importer must fail.
    for (const endpoint of ['preview', 'prepare', 'commit']) {
      for (const method of ['GET', 'POST']) {
        const result = await page.request.fetch(origin + '/api/import/' + endpoint, {
          method, headers:{Origin:origin, 'Content-Type':'application/json'},
          ...(method === 'GET' ? {} : {data:{source:'oto', year:2026, id:'00000000-0000-4000-8000-000000000000'}}),
        });
        assert([404,405].includes(result.status()), `${method} ${endpoint}: ${result.status()}`);
      }
    }
    assert.deepEqual(await page.request.get(origin + '/api/datasets').then(result => result.json()), before);
    await page.click('#atlasTab');
    await page.selectOption('#year', '2017');
    assert((await page.locator('.school-row').count()) > 0);
    await page.click('#dataTab');
    assert.equal(await page.locator('#exportYear').inputValue(), '2017');
    await page.setViewportSize({width:390, height:844});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.click('#atlasTab');
    await page.locator('.school-row').first().click();
    assert(await page.locator('#historyChart').count());
    assert.deepEqual(errors, []);
    console.log('Public atlas: no import UI; CSV/JSON exports, annual selection and mobile passed. Removed import endpoints rejected all 6 GET/POST requests; published datasets unchanged.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
