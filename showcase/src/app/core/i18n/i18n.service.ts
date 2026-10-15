import { Injectable, computed, effect, inject } from '@angular/core';
import { UserSettingsStore } from '@wiltech-labs/ngx-region-settings';

import { TranslationService } from './translation.service';
import { AVAILABLE_LANGUAGES, DEFAULT_LANGUAGE, isAppLanguage } from './translations';

// The browser's own preference, used until (or unless) the user has settings:
// an exact match ('el-CY'), else the first language with the same base ('el').
function browserLanguage(): string {
  const preferred = typeof navigator === 'undefined' ? [] : (navigator.languages ?? []);
  for (const tag of preferred) {
    const base = tag.split('-')[0];
    const match =
      AVAILABLE_LANGUAGES.find((lang) => lang === tag) ??
      AVAILABLE_LANGUAGES.find((lang) => lang.split('-')[0] === base);
    if (match) return match;
  }
  return DEFAULT_LANGUAGE;
}

// Owns "which language is the UI in and which locale formats dates". Both
// come from the signed-in user's own region settings (`language`, `locale`),
// the same values the settings screen edits — the UI never picks them itself.
// Signed out, or before the settings load, it follows the browser.
@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly translation = inject(TranslationService);
  private readonly settings = inject(UserSettingsStore);

  /** The locale id for formatting (`date` pipe etc.), e.g. 'el-CY'. */
  readonly locale = computed(
    () => this.settings.settings()?.locale ?? browserLanguage(),
  );

  constructor() {
    effect(() => {
      const language = this.settings.settings()?.language;
      const active = isAppLanguage(language) ? language : browserLanguage();
      void this.translation.use(active);
      // Screen readers and the browser's own translation prompt read this.
      document.documentElement.lang = active;
    });
  }
}
