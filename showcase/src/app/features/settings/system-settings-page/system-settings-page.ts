import { Component, computed, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { RegionSettingsPayload, SystemSettingsStore, RegionSettingsFormComponent } from '@wiltech-labs/ngx-region-settings';

import { ApiErrors } from '../../../core/api/api-error';
import { TranslationService } from '../../../core/i18n/translation.service';
import { TranslocoPipe } from '@jsverse/transloco';

// Admin-only: the defaults every user falls back to until they save their
// own. The screen follows the `systemSettings` profile link, which the API
// only hands to admins — a non-admin who types /settings/system just sees
// "not available" (and the API would 403 them anyway).
@Component({
  selector: 'app-system-settings-page',
  imports: [MatCardModule, RegionSettingsFormComponent, TranslocoPipe],
  providers: [SystemSettingsStore],
  templateUrl: './system-settings-page.html',
  styleUrl: './system-settings-page.scss',
})
export class SystemSettingsPage {
  protected readonly store = inject(SystemSettingsStore);
  private readonly apiErrors = inject(ApiErrors);
  private readonly i18n = inject(TranslationService);

  protected readonly saving = signal(false);
  protected readonly saveError = signal<string | null>(null);
  protected readonly status = signal<string | null>(null);

  protected readonly errorMessage = computed(() => {
    const error = this.store.error;
    return error ? this.apiErrors.describe(error, 'settings.loadFailed') : null;
  });

  protected async save(payload: RegionSettingsPayload): Promise<void> {
    this.saveError.set(null);
    this.status.set(null);
    this.saving.set(true);
    try {
      await this.store.save(payload);
      this.status.set(this.i18n.t('settings.system.saved'));
    } catch (err) {
      this.saveError.set(this.apiErrors.describe(err, 'settings.saveFailed'));
    } finally {
      this.saving.set(false);
    }
  }
}
