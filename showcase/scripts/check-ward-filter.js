// Manual/dev helper — drives the already-running dev server (`ng serve` on
// :4200 talking to the docker-compose api on :8001) through a real Clerk
// sign-in and exercises the bed-board ward filter chips, screenshotting
// each step. Not part of the `playwright test` e2e suite (../e2e) — that
// suite spins up its own isolated, freshly-wiped e2e-local.db per run, so
// it never has more than one ward's worth of beds seeded and can't
// exercise a multi-ward filter.
//
// Requires: `docker compose up` in resource-management-api (seeded via
// `docker compose exec api uv run python scripts/seed_demo_data.py`),
// `npx ng serve` running in this directory, and this directory's `.env`
// (see e2e/auth.setup.ts for what it needs — CLERK_SECRET_KEY,
// CLERK_PUBLISHABLE_KEY, E2E_CLERK_USER_EMAIL).
//
// Usage: node scripts/check-ward-filter.js [baseURL] [screenshotDir]

require('dotenv/config');
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const { clerk, clerkSetup } = require('@clerk/testing/playwright');

const baseURL = process.argv[2] || 'http://localhost:4200';
const outDir = process.argv[3] || path.join(__dirname, '..', '.tmp', 'ward-filter-check');

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
  await page.waitForSelector('.BedBoardShell-title', { timeout: 15_000 });
  await page.screenshot({ path: path.join(outDir, '1-initial.png'), fullPage: true });

  const chips = page.locator('mat-chip-option');
  const chipCount = await chips.count();
  console.log(`ward chips found: ${chipCount}`);

  if (chipCount < 2) {
    console.log('Fewer than 2 wards in seeded data — cannot exercise multi-select. Seed demo data first.');
  } else {
    await chips.nth(0).click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(outDir, '2-after-first-chip.png'), fullPage: true });

    const chipsAfterOne = await page.locator('mat-chip-option').count();
    console.log(`ward chips still present after selecting one: ${chipsAfterOne}`);
    if (chipsAfterOne !== chipCount) {
      throw new Error(`BUG STILL PRESENT: chip count changed from ${chipCount} to ${chipsAfterOne} after selecting one.`);
    }

    await chips.nth(1).click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(outDir, '3-after-second-chip.png'), fullPage: true });

    await page.locator('.BedBoardShell-ward-filter-clear').click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(outDir, '4-cleared.png'), fullPage: true });
  }

  console.log('console/page errors:', errors);
  await browser.close();
  console.log(`Screenshots written to ${outDir}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
