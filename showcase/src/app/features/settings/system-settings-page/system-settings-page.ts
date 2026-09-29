import { Component, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { ApiErrors } from '../../../core/api/api-error';
import { TranslationService } from '../../../core/i18n/translation.service';
import { RegionSettingsForm } from '../region-settings-form/region-settings-form';
import { RegionSettingsPayload, SystemSettingsStore } from '../region-settings.store';
import { TranslocoPipe } from '@jsverse/transloco';

// Admin-only: the defaults every user falls back to until they save their
// own. The screen follows the `systemSettings` profile link, which the API
// only hands to admins — a non-admin who types /settings/system just sees
// "not available" (and the API would 403 them anyway).
@Component({
  selector: 'app-system-settings-page',
  imports: [MatCardModule, RegionSettingsForm, TranslocoPipe],
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
