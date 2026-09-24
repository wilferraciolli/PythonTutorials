import { Component, computed, input, linkedSignal, output } from '@angular/core';
import { FormField, FormRoot, form } from '@angular/forms/signals';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { RegionSettingsOptions, RegionSettingsPayload } from '../region-settings.store';

function toPayload(settings: RegionSettingsPayload): RegionSettingsPayload {
  const { timezone, language, currency, theme } = settings;
  return { timezone, language, currency, theme };
}

// Presentational: the four region fields as <select>s, shared by the user's
// own settings and the system settings. The page owns loading and saving.
@Component({
  selector: 'app-region-settings-form',
  imports: [FormField, FormRoot, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './region-settings-form.html',
  styleUrl: './region-settings-form.scss',
})
export class RegionSettingsForm {
  readonly settings = input.required<RegionSettingsPayload>();
  readonly options = input.required<RegionSettingsOptions>();
  readonly saving = input(false);

  readonly save = output<RegionSettingsPayload>();

  // Re-seeds from the saved settings whenever they (re)load, and stays
  // editable in between — linkedSignal rather than an effect().
  protected readonly model = linkedSignal(() => toPayload(this.settings()));

  protected readonly changed = computed(
    () => JSON.stringify(this.model()) !== JSON.stringify(toPayload(this.settings())),
  );

  protected readonly settingsForm = form(this.model, {
    submission: {
      action: async () => {
        this.save.emit(this.model());
        return undefined;
      },
    },
  });
}
