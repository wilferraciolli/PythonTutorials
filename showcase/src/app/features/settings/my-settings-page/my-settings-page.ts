import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { LinkService } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { RegionSettingsForm } from '../region-settings-form/region-settings-form';
import { RegionSettingsPayload, UserSettingsStore } from '../region-settings.store';

// The signed-in user's own settings. Every user can open this; the API only
// hands out the `userSettings` link on your own profile, and refuses anyone
// else's settings with a 403.
@Component({
  selector: 'app-my-settings-page',
  imports: [MatButtonModule, MatCardModule, RegionSettingsForm],
  providers: [UserSettingsStore],
  templateUrl: './my-settings-page.html',
  styleUrl: './my-settings-page.scss',
})
export class MySettingsPage {
  protected readonly store = inject(UserSettingsStore);
  private readonly links = inject(LinkService);

  protected readonly saving = signal(false);
  protected readonly saveError = signal<string | null>(null);
  protected readonly status = signal<string | null>(null);

  // SYSTEM until the user saves their own settings for the first time.
  protected readonly usingDefaults = computed(() => this.store.settings()?.owner_type === 'SYSTEM');
  protected readonly canReset = computed(
    () =>
      !this.usingDefaults() && this.links.hasLink(this.store.settings()?.links['resetSettings']),
  );

  protected async save(payload: RegionSettingsPayload): Promise<void> {
    await this.run(() => this.store.save(payload), 'Settings saved.');
  }

  protected async reset(): Promise<void> {
    await this.run(() => this.store.reset(), 'Back to the system defaults.');
  }

  private async run(action: () => Promise<void>, doneMessage: string): Promise<void> {
    this.saveError.set(null);
    this.status.set(null);
    this.saving.set(true);
    try {
      await action();
      this.status.set(doneMessage);
    } catch (err) {
      this.saveError.set(describeApiError(err, 'Failed to save.'));
    } finally {
      this.saving.set(false);
    }
  }
}
