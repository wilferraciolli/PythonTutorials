import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { enGB } from './translations/en-GB';

// Keys are plain strings, so a typo would only show up as a raw key on
// screen. This reads the templates and the TypeScript that translate and
// checks every literal key exists in the source dictionary.
const APP_DIR = join(process.cwd(), 'src/app');

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return files(path);
    return /\.(html|ts)$/.test(name) && !name.endsWith('.spec.ts') ? [path] : [];
  });
}

function has(key: string): boolean {
  let node: unknown = enGB;
  for (const part of key.split('.')) {
    if (typeof node !== 'object' || node === null || !(part in node)) return false;
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === 'string';
}

// 'a.b' | transloco   ·   ? 'a.b' : 'c.d'   inside a pipe expression
const PIPE_KEYS = /'([a-z][A-Za-z]*(?:\.[A-Za-z0-9-]+)+)'(?=[^']*\|\s*transloco)/g;
// this.i18n.t('a.b')   ·   apiErrors.describe(err, 'a.b')
const CODE_KEYS = /(?:i18n\.t\(|\.describe\([^,]+,\s*)'([a-z][A-Za-z]*(?:\.[A-Za-z0-9-]+)+)'/g;

describe('translation keys', () => {
  const used: { file: string; key: string }[] = [];
  for (const file of files(APP_DIR)) {
    const source = readFileSync(file, 'utf8');
    const pattern = file.endsWith('.html') ? PIPE_KEYS : CODE_KEYS;
    for (const match of source.matchAll(pattern)) {
      used.push({ file: file.replace(APP_DIR, 'src/app'), key: match[1] });
    }
  }

  it('finds the keys the app uses', () => {
    expect(used.length).toBeGreaterThan(50);
  });

  it('every key used exists in en-GB', () => {
    const missing = used.filter(({ key }) => !has(key));
    expect(missing).toEqual([]);
  });
});
