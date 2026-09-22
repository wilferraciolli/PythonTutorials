import { httpResource } from '@angular/common/http';
import { computed, inject } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withProps, withState } from '@ngrx/signals';

import { Envelope, unwrapData } from '../api/envelope';
import { CurrentUserStore } from '../user/current-user.store';
import { environment } from '../../../environments/environment';
import adminEl from './translations/el-GR/admin.json';
import bedsEl from './translations/el-GR/beds.json';
import commonEl from './translations/el-GR/common.json';
import errorsEl from './translations/el-GR/errors.json';
import messagesEl from './translations/el-GR/messages.json';
import navigationEl from './translations/el-GR/navigation.json';
import profileEl from './translations/el-GR/profile.json';
import adminEn from './translations/en-GB/admin.json';
import bedsEn from './translations/en-GB/beds.json';
import commonEn from './translations/en-GB/common.json';
import errorsEn from './translations/en-GB/errors.json';
import messagesEn from './translations/en-GB/messages.json';
import navigationEn from './translations/en-GB/navigation.json';
import profileEn from './translations/en-GB/profile.json';

export type Locale = 'el-GR' | 'en-GB';

interface OrganizationSummary {
  id: string;
  name: string;
  default_language: Locale;
  timezone: string;
}

type OrganizationEnvelope = Envelope<OrganizationSummary>;

// Per docs/features/internationalization-i18n.md's "Scope: Organization
// Settings vs. User Preference" — language resolves user override, then
// the organization's default, then this hardcoded fallback; timezone is
// organization-wide only (no per-user/per-locale override at all).
const FALLBACK_LOCALE: Locale = 'el-GR';
const FALLBACK_TIMEZONE = 'Europe/Athens';

// Bundled at build time (see tsconfig's `resolveJsonModule`) rather than
// fetched at runtime — there are only two small, finite locales, so a
// network round trip (and the asset-path/base-href complexity that comes
// with `src/assets/`) buys nothing here.
const DICTIONARIES: Record<Locale, Record<string, Record<string, unknown>>> = {
  'el-GR': { common: commonEl, navigation: navigationEl, beds: bedsEl, admin: adminEl, profile: profileEl, errors: errorsEl, messages: messagesEl },
  'en-GB': { common: commonEn, navigation: navigationEn, beds: bedsEn, admin: adminEn, profile: profileEn, errors: errorsEn, messages: messagesEn },
};

const INTL_LOCALE: Record<Locale, string> = { 'el-GR': 'el-GR', 'en-GB': 'en-GB' };
const NATIVE_NAME: Record<Locale, string> = { 'el-GR': 'Ελληνικά', 'en-GB': 'English (UK)' };

function lookup(dict: Record<string, unknown>, path: string[]): string | undefined {
  let node: unknown = dict;
  for (const part of path) {
    if (typeof node !== 'object' || node === null) return undefined;
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === 'string' ? node : undefined;
}

// App-wide state (like AuthStore/CurrentUserStore) — every screen's
// template needs the current locale to translate and format with.
export const I18nStore = signalStore(
  { providedIn: 'root' },
  // A same-session override so a language change applies instantly (the
  // doc's "responsive... without reload" success metric) rather than
  // waiting on the PATCH /me round-trip below to resolve and flow back
  // through `currentUser.profile()`.
  withState<{ sessionOverride: Locale | null }>({ sessionOverride: null }),
  withProps(() => ({
    currentUser: inject(CurrentUserStore),
    organizationResource: httpResource<OrganizationEnvelope>(() => `${environment.apiUrl}/organization`),
  })),
  withComputed(({ currentUser, organizationResource, sessionOverride }) => {
    const organization = computed(() => {
      const value = organizationResource.value();
      return value ? unwrapData(value, 'organization') : undefined;
    });

    // Resolution order: this session's override, then the signed-in
    // user's own persisted preference, then the organization's default,
    // then the hardcoded fallback — see docs/features/internationalization-i18n.md.
    const locale = computed<Locale>(
      () =>
        sessionOverride() ??
        (currentUser.profile()?.language as Locale | undefined) ??
        organization()?.default_language ??
        FALLBACK_LOCALE,
    );

    // Timezone is organization-wide only — never derived from the chosen
    // language/locale, and there is no user override for it at all.
    const timezone = computed(() => organization()?.timezone ?? FALLBACK_TIMEZONE);

    return { organization, locale, timezone };
  }),
  withMethods((store) => {
    return {
      // Applies instantly for this session, then persists server-side via
      // the user's own profile (PATCH /me) in the background — not
      // localStorage, per the doc's "not just localStorage" success
      // metric. A failed persist leaves the session override in place
      // rather than silently reverting the user's choice. Skips the
      // persist when no profile is loaded — the nav bar's language
      // switcher is reachable while signed out too, and there's no /me
      // to PATCH yet (the session override above is all a signed-out
      // visitor gets).
      setLocale(locale: Locale): void {
        patchState(store, { sessionOverride: locale });
        if (store.currentUser.profile()) {
          void store.currentUser.updateProfile({ language: locale });
        }
      },

      // `key` is `"<namespace>.<...path>"`, e.g. "common.buttons.save" —
      // falls back to the key itself so a missing translation is visible
      // and debuggable rather than rendering blank.
      t(key: string, params?: Record<string, string | number>): string {
        const [namespace, ...path] = key.split('.');
        const dict = DICTIONARIES[store.locale()][namespace];
        let value = (dict && lookup(dict, path)) ?? key;
        if (params) {
          for (const [name, replacement] of Object.entries(params)) {
            value = value.replace(`{{${name}}}`, String(replacement));
          }
        }
        return value;
      },

      formatDate(value: string | Date, format: 'date' | 'time' | 'dateTime' = 'dateTime'): string {
        const date = typeof value === 'string' ? new Date(value) : value;
        const options: Intl.DateTimeFormatOptions = { timeZone: store.timezone() };
        if (format === 'date' || format === 'dateTime') {
          Object.assign(options, { day: '2-digit', month: '2-digit', year: 'numeric' });
        }
        if (format === 'time' || format === 'dateTime') {
          Object.assign(options, { hour: '2-digit', minute: '2-digit', hour12: false });
        }
        return new Intl.DateTimeFormat(INTL_LOCALE[store.locale()], options).format(date);
      },

      supportedLocales(): { code: Locale; name: string }[] {
        return (Object.keys(NATIVE_NAME) as Locale[]).map((code) => ({ code, name: NATIVE_NAME[code] }));
      },
    };
  }),
);
