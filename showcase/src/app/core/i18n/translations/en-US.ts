import type { Translation } from './en-GB';

// American English only lists the strings that differ from en-GB — anything
// missing here falls back to en-GB (see `fallbackLang` in i18n.providers.ts).
export const enUS: Partial<Translation> = {};
