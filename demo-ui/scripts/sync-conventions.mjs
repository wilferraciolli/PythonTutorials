// Keeps the code blocks in docs/frontend-conventions.md identical to the real
// files they copy. Each copied block sits between markers:
//
//   <!-- embed: src/styles/_ui.scss -->
//   ```scss
//   ...
//   ```
//   <!-- /embed -->
//
// An optional `until="text"` stops the copy just before the first line that
// starts with `text` (to embed only the reusable top of a file).
//
//   node scripts/sync-conventions.mjs          rewrite the blocks from the files
//   node scripts/sync-conventions.mjs --check  exit 1 if any block is stale
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const docPath = join(root, 'docs', 'frontend-conventions.md');
const check = process.argv.includes('--check');

// The doc is portable: app-specific names become placeholders.
const PORTABLE = [['Showcase', 'AppName']];
const LANG = { '.scss': 'scss', '.ts': 'ts', '.html': 'html', '.css': 'css' };

const doc = readFileSync(docPath, 'utf8').replace(/\r\n/g, '\n');
const marker = /<!-- embed: (\S+)(?: until="([^"]*)")? -->\n[\s\S]*?<!-- \/embed -->/g;

const stale = [];
let count = 0;
const next = doc.replace(marker, (block, file, until) => {
  count++;
  let text = readFileSync(join(root, file), 'utf8').replace(/\r\n/g, '\n');
  if (until) {
    const lines = text.split('\n');
    const stop = lines.findIndex((line) => line.startsWith(until));
    if (stop < 0) throw new Error(`${file}: no line starts with "${until}"`);
    text = lines.slice(0, stop).join('\n');
  }
  for (const [from, to] of PORTABLE) text = text.split(from).join(to);
  const opening = until ? `<!-- embed: ${file} until="${until}" -->` : `<!-- embed: ${file} -->`;
  const fresh = `${opening}\n\`\`\`${LANG[extname(file)] ?? ''}\n${text.trimEnd()}\n\`\`\`\n<!-- /embed -->`;
  if (fresh !== block) stale.push(file);
  return fresh;
});

if (check) {
  if (stale.length) {
    console.error(`frontend-conventions.md is out of date for:\n  ${stale.join('\n  ')}`);
    console.error('Run `npm run docs:sync` and commit the result.');
    process.exit(1);
  }
  console.log(`frontend-conventions.md: ${count} embedded files up to date.`);
} else {
  writeFileSync(docPath, next);
  console.log(`frontend-conventions.md: ${count} embedded files, ${stale.length} refreshed.`);
}
