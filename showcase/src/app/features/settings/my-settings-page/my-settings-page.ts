import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { LinkService } from '@wiltech-labs/ngx-api-client';
import { RegionSettingsPayload, UserSettingsStore, RegionSettingsFormComponent } from '@wiltech-labs/ngx-region-settings';

import { ApiErrors } from '../../../core/api/api-error';
import { TranslationService } from '../../../core/i18n/translation.service';
import { translateRegionSettingsOptions } from '../region-settings-options';
import { TranslocoPipe } from '@jsverse/transloco';

// The signed-in user's own settings. Every user can open this; the API only
// hands out the `userSettings` link on your own profile, and refuses anyone
// else's settings with a 403.
@Component({
  selector: 'app-my-settings-page',
  imports: [MatButtonModule, MatCardModule, RegionSettingsFormComponent, TranslocoPipe],
  templateUrl: './my-settings-page.html',
  styleUrl: './my-settings-page.scss',
})
export class MySettingsPage {
  protected readonly store = inject(UserSettingsStore);
  private readonly links = inject(LinkService);
  private readonly apiErrors = inject(ApiErrors);
  private readonly i18n = inject(TranslationService);

  protected readonly saving = signal(false);
  protected readonly saveError = signal<string | null>(null);
  protected readonly status = signal<string | null>(null);

  // SYSTEM until the user saves their own settings for the first time.
  protected readonly usingDefaults = computed(() => this.store.settings()?.owner_type === 'SYSTEM');
  protected readonly canReset = computed(
    () =>
      !this.usingDefaults() && this.links.hasLink(this.store.settings()?.links['resetSettings']),
  );
  protected readonly errorMessage = computed(() => {
    const error = this.store.error();
    return error ? this.apiErrors.describe(error, 'settings.loadFailed') : null;
  });

  protected readonly translatedOptions = computed(() =>
    translateRegionSettingsOptions(this.store.options(), this.i18n),
  );

  protected async save(payload: RegionSettingsPayload): Promise<void> {
    await this.run(() => this.store.save(payload), this.i18n.t('settings.my.saved'));
  }

  protected async reset(): Promise<void> {
    await this.run(() => this.store.reset(), this.i18n.t('settings.my.resetDone'));
  }

  private async run(action: () => Promise<void>, doneMessage: string): Promise<void> {
    this.saveError.set(null);
    this.status.set(null);
    this.saving.set(true);
    try {
      await action();
      // Language and locale are now automatically reflected in the UI through
      // the shared root-provided UserSettingsStore.
      this.status.set(doneMessage);
    } catch (err) {
      this.saveError.set(this.apiErrors.describe(err, 'settings.saveFailed'));
    } finally {
      this.saving.set(false);
    }
  }
}
