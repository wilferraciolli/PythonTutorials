import { httpResource } from '@angular/common/http';
import { Injectable, computed, effect, inject } from '@angular/core';
import { ApiClientService, ApiEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { CurrentUserStore } from '../user/current-user.store';
import { TranslationService } from './translation.service';
import { AVAILABLE_LANGUAGES, DEFAULT_LANGUAGE, isAppLanguage } from './translations';

interface RegionPreferences {
  language: string;
  locale: string;
}

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
  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);

  // Followed via the profile's `userSettings` link, like the settings screen —
  // never a hand-built URL. No link (signed out) means no request.
  private readonly preferences = httpResource<ApiEnvelope<Record<string, RegionPreferences>>>(() =>
    this.api.resolve(this.currentUser.link('userSettings')),
  );

  /** The locale id for formatting (`date` pipe etc.), e.g. 'el-CY'. */
  readonly locale = computed(
    () => this.preferences.value()?._data['userSettings']?.locale ?? browserLanguage(),
  );

  constructor() {
    effect(() => {
      const language = this.preferences.value()?._data['userSettings']?.language;
      const active = isAppLanguage(language) ? language : browserLanguage();
      void this.translation.use(active);
      // Screen readers and the browser's own translation prompt read this.
      document.documentElement.lang = active;
    });
  }

  /** Re-reads the user's settings — call after they are saved or reset. */
  refresh(): void {
    this.preferences.reload();
  }
}
