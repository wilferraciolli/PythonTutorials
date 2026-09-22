// Manual/dev helper — drives the already-running dev server (`ng serve` on
// :4200 talking to the docker-compose api on :8001) through a real Clerk
// sign-in and exercises the bed-card status dropdown:
//  1. confirms all four options (including the new 'cleaning' one) are
//     present, selects 'cleaning' on the first bed found, and confirms it
//     persists across a reload (proving the PATCH round-tripped through
//     the API's new BedStatus enum value and the widened DB CHECK
//     constraint, not just client state).
//  2. confirms the store's poll (see POLL_INTERVAL_MS in bed-board.store.ts)
//     does NOT replace a bed's DOM node/select element when that bed's data
//     hasn't changed — the fix for the dropdown closing itself mid-tap.
//
// Requires: `docker compose up` in resource-management-api (seeded via
// `docker compose exec api uv run python scripts/seed_demo_data.py`),
// `npx ng serve` running in this directory, and this directory's `.env`
// (see e2e/auth.setup.ts for what it needs — CLERK_SECRET_KEY,
// CLERK_PUBLISHABLE_KEY, E2E_CLERK_USER_EMAIL).
//
// Usage: node scripts/check-bed-status-dropdown.js [baseURL] [screenshotDir]

require('dotenv/config');
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const { clerk, clerkSetup } = require('@clerk/testing/playwright');

const baseURL = process.argv[2] || 'http://localhost:4200';
const outDir = process.argv[3] || path.join(__dirname, '..', '.tmp', 'bed-status-dropdown-check');

async function main() {
  const email = process.env.E2E_CLERK_USER_EMAIL;
  if (!email) {
    throw new Error('E2E_CLERK_USER_EMAIL is not set — copy .env.example to .env and fill it in.');
  }
  fs.mkdirSync(outDir, { recursive: true });

  await clerkSetup();

  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await (await browser.newContext()).newPage();
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await page.goto(baseURL);
  await clerk.signIn({ page, emailAddress: email });
  await page.goto(`${baseURL}/board`);
  await page.waitForSelector('.BedCard-status-select', { timeout: 15_000 });

  // --- Part 1: 'cleaning' option exists and persists ---
  const firstSelect = page.locator('.BedCard-status-select').first();
  const optionValues = await firstSelect.locator('option').evaluateAll((opts) => opts.map((o) => o.value));
  console.log('status options on first card:', optionValues);
  if (!optionValues.includes('cleaning')) {
    throw new Error(`'cleaning' missing from dropdown options: ${optionValues.join(', ')}`);
  }

  await firstSelect.selectOption('cleaning');
  await page.waitForTimeout(500);
  const classAfterSelect = await firstSelect.getAttribute('class');
  if (!classAfterSelect.includes('BedCard-status-select-cleaning')) {
    throw new Error(`expected BedCard-status-select-cleaning class, got: ${classAfterSelect}`);
  }
  await page.screenshot({ path: path.join(outDir, '1-selected-cleaning.png'), fullPage: false });

  await page.reload();
  await page.waitForSelector('.BedCard-status-select', { timeout: 15_000 });
  const reloadedClass = await page.locator('.BedCard-status-select').first().getAttribute('class');
  if (!reloadedClass.includes('BedCard-status-select-cleaning')) {
    throw new Error(`status did not persist across reload — got class: ${reloadedClass}`);
  }
  console.log('PASS: cleaning option persists through the API');

  // Restore to occupied so repeated runs / manual use of the dev board
  // aren't left with a bed stuck in 'cleaning'.
  await page.locator('.BedCard-status-select').first().selectOption('occupied');
  await page.waitForTimeout(300);

  // --- Part 2: unchanged beds keep the same DOM node across a poll tick ---
  // Tag the first select's underlying element so we can tell if Angular
  // swapped it for a new one vs. reused it in place.
  await page.evaluate(() => {
    document.querySelectorAll('.BedCard-status-select')[0].setAttribute('data-probe', 'unchanged-1');
  });
  console.log('waiting ~65s for a poll tick (POLL_INTERVAL_MS = 60000)...');
  await page.waitForTimeout(65_000);
  const probeSurvived = await page.evaluate(
    () => document.querySelector('[data-probe="unchanged-1"]') !== null,
  );
  console.log(probeSurvived ? 'PASS: unchanged bed kept its DOM node across a poll' : 'FAIL: DOM node was replaced on an unrelated poll');
  await page.screenshot({ path: path.join(outDir, '2-after-poll.png'), fullPage: false });

  console.log('console/page errors:', errors);
  await browser.close();
  if (!probeSurvived) process.exit(1);
  console.log(`Screenshots in ${outDir}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
