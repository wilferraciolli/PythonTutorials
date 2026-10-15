import { ValueViewValue } from '@wiltech-labs/ngx-api-client';
import { RegionSettingsFieldOptions, RegionSettingsPayload } from '@wiltech-labs/ngx-region-settings';

import { TranslationService } from '../../core/i18n/translation.service';

/**
 * Translates the API's raw `{value, viewValue}` option lists into the form's
 * `{label, value}` shape, via `settings.options.<field>.<value>` keys. Each
 * app owns this mapping (not the library) since the value set — locales,
 * currencies — differs per project.
 */
export function translateRegionSettingsOptions(
  options: Partial<Record<keyof RegionSettingsPayload, ValueViewValue[]>>,
  i18n: TranslationService,
): RegionSettingsFieldOptions {
  const translated: RegionSettingsFieldOptions = {};
  for (const key of Object.keys(options) as (keyof RegionSettingsPayload)[]) {
    translated[key] = options[key]?.map((v) => ({
      label: i18n.optionLabel(`settings.options.${key}`, v.viewValue),
      value: v.viewValue,
    }));
  }
  return translated;
}
