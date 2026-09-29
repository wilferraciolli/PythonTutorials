import { httpResource } from '@angular/common/http';
import { Injectable, computed, inject } from '@angular/core';
import {
  ApiClientService,
  ApiEnvelope,
  ILink,
  MetadataService,
  ValueViewValue,
} from '@wiliamferraciolli/ngx-api-client';

import { ApiErrors } from '../../core/api/api-error';
import { TranslationService } from '../../core/i18n/translation.service';
import { CurrentUserStore } from '../../core/user/current-user.store';

// Region settings — the same shape for a user's own settings
// (`/users/{id}/settings`) and the system defaults (`/admin/settings`).
export interface RegionSettings {
  id: string;
  // Only on user settings: SYSTEM while the user still falls back to the
  // system defaults, USER once they've saved their own.
  owner_type?: 'SYSTEM' | 'USER';
  timezone: string;
  language: string;
  locale: string;
  currency: string;
  theme: string;
  links: Record<string, ILink>;
}

export type RegionSettingsPayload = Pick<
  RegionSettings,
  'timezone' | 'language' | 'locale' | 'currency' | 'theme'
>;

export type RegionSettingsOptions = Record<keyof RegionSettingsPayload, ValueViewValue[]>;

const EMPTY_OPTIONS: RegionSettingsOptions = {
  timezone: [],
  language: [],
  locale: [],
  currency: [],
  theme: [],
};

// Shared by UserSettingsStore and SystemSettingsStore below: both screens
// load one settings resource by following a link on the user profile, show
// its `_metadata` option lists, and PUT back through the resource's own
// `updateSettings` link. Subclasses only say which `_data` key and which
// profile link. Feature-local, so each page provides its own instance.
export abstract class RegionSettingsStore {
  private readonly api = inject(ApiClientService);
  private readonly metadata = inject(MetadataService);
  private readonly apiErrors = inject(ApiErrors);
  private readonly i18n = inject(TranslationService);
  protected readonly currentUser = inject(CurrentUserStore);

  /** The `_data` key the API wraps the settings in. */
  protected abstract readonly root: string;
  /** The profile link this screen follows; absent if the caller may not use it. */
  protected abstract profileLink(): ILink | undefined;

  // Never a hand-built URL: no link (profile still loading, or the caller
  // isn't allowed) means no request.
  private readonly resource = httpResource<ApiEnvelope<Record<string, RegionSettings>>>(() =>
    this.api.resolve(this.profileLink()),
  );

  readonly settings = computed(() => this.resource.value()?._data[this.root]);
  readonly isLoading = computed(() => this.currentUser.loading() || this.resource.isLoading());
  readonly errorMessage = computed(() => {
    const error = this.resource.error();
    return error ? this.apiErrors.describe(error, 'settings.loadFailed') : null;
  });

  // The profile has loaded and handed out no link: this caller may not use
  // the screen (e.g. a non-admin on the system settings).
  readonly notAvailable = computed(
    () => !this.currentUser.loading() && !!this.currentUser.profile() && !this.profileLink(),
  );

  // Allowed values straight from the API's metadata, as {value, viewValue}
  // for the <select>s — never a hardcoded list in the UI.
  readonly options = computed<RegionSettingsOptions>(() => {
    const metadata = this.resource.value()?._metadata;
    if (!metadata) return EMPTY_OPTIONS;
    // Labels for the fields that have them (language, locale, theme); the
    // rest (timezone, currency) show the API's own value.
    const resolve = (field: keyof RegionSettingsPayload) =>
      this.metadata.resolveMetadataIdValues(metadata[field]?.values ?? []).map((option) => ({
        ...option,
        viewValue: this.i18n.optionLabel(`settings.options.${field}`, option.value),
      }));
    return {
      timezone: resolve('timezone'),
      language: resolve('language'),
      locale: resolve('locale'),
      currency: resolve('currency'),
      theme: resolve('theme'),
    };
  });

  async save(payload: RegionSettingsPayload): Promise<void> {
    const url = this.api.requireLink(
      this.settings()?.links['updateSettings'],
      this.i18n.t('settings.notPermittedChange'),
    );
    await this.api.put<string, RegionSettings, RegionSettingsPayload>(this.root, url, payload);
    this.resource.reload();
  }

  async reset(): Promise<void> {
    const url = this.api.requireLink(
      this.settings()?.links['resetSettings'],
      this.i18n.t('settings.cannotReset'),
    );
    await this.api.delete(url);
    this.resource.reload();
  }
}

@Injectable()
export class UserSettingsStore extends RegionSettingsStore {
  protected readonly root = 'userSettings';

  // Only on the caller's own profile — settings are personal.
  protected profileLink(): ILink | undefined {
    return this.currentUser.link('userSettings');
  }
}

@Injectable()
export class SystemSettingsStore extends RegionSettingsStore {
  protected readonly root = 'systemSettings';

  // Only handed out to admins.
  protected profileLink(): ILink | undefined {
    return this.currentUser.link('systemSettings');
  }
}
