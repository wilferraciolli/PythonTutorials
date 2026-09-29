import type { Translation } from './en-GB';
import { elCY } from './el-CY';
import { enGB } from './en-GB';
import { enUS } from './en-US';
import { ptBR } from './pt-BR';

// One entry per value of the API's `SupportedLanguages` enum.
export const TRANSLATIONS = {
  'en-GB': enGB,
  'en-US': enUS,
  'el-CY': elCY,
  'pt-BR': ptBR,
} satisfies Record<string, Partial<Translation>>;

export type AppLanguage = keyof typeof TRANSLATIONS;

export const AVAILABLE_LANGUAGES = Object.keys(TRANSLATIONS) as AppLanguage[];
export const DEFAULT_LANGUAGE: AppLanguage = 'en-GB';

export function isAppLanguage(value: unknown): value is AppLanguage {
  return typeof value === 'string' && value in TRANSLATIONS;
}
