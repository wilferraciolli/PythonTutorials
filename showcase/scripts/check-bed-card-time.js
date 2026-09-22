// Manual/dev helper — drives the already-running dev server (`ng serve` on
// :4200 talking to the docker-compose api on :8001) through a real Clerk
// sign-in and screenshots an occupied bed card (to check the clock-time
// range / remaining-duration formatting) and an open status dropdown (to
// check option spacing).
//
// Requires the same setup as check-ward-filter.js — see that file's header.
//
// Usage: node scripts/check-bed-card-time.js [baseURL] [screenshotDir]

require('dotenv/config');
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const { clerk, clerkSetup } = require('@clerk/testing/playwright');

const baseURL = process.argv[2] || 'http://localhost:4200';
const outDir = process.argv[3] || path.join(__dirname, '..', '.tmp', 'bed-card-time-check');

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

  const minutesLine = page.locator('.BedCard-minutes').first();
  console.log('time range / remaining text:', (await minutesLine.textContent()).trim());
  await minutesLine.scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outDir, '1-occupied-card.png'), fullPage: false });

  // Open the first dropdown and screenshot it expanded.
  const firstSelect = page.locator('.BedCard-status-select').first();
  await firstSelect.scrollIntoViewIfNeeded();
  await firstSelect.click();
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(outDir, '2-dropdown-open.png'), fullPage: false });

  console.log('console/page errors:', errors);
  await browser.close();
  console.log(`Screenshots in ${outDir}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
