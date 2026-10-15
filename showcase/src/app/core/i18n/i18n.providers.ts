import { registerLocaleData } from '@angular/common';
import localeElCY from '@angular/common/locales/el-CY';
import localeEnGB from '@angular/common/locales/en-GB';
import localePt from '@angular/common/locales/pt';
import {
  EnvironmentProviders,
  Injectable,
  inject,
  isDevMode,
  provideAppInitializer,
} from '@angular/core';
import { Translation, TranslocoLoader, provideTransloco } from '@jsverse/transloco';
import { Observable, of } from 'rxjs';

import { TranslationService } from './translation.service';
import { AVAILABLE_LANGUAGES, AppLanguage, DEFAULT_LANGUAGE, TRANSLATIONS } from './translations';

// The dictionaries ship inside the bundle (they're small, typed and checked at
// build time), so a language switch is instant and there is no flash of raw
// keys while a JSON file downloads.
@Injectable({ providedIn: 'root' })
class BundledTranslationLoader implements TranslocoLoader {
  getTranslation(lang: string): Observable<Translation> {
    return of((TRANSLATIONS[lang as AppLanguage] ?? {}) as Translation);
  }
}

export function provideI18n(): EnvironmentProviders[] {
  // Angular only ships en-US formats; the `date` pipe needs the others
  // registered. 'pt' covers pt-BR.
  registerLocaleData(localeEnGB, 'en-GB');
  registerLocaleData(localeElCY, 'el-CY');
  registerLocaleData(localePt, 'pt');

  return provideTransloco({
    config: {
      availableLangs: AVAILABLE_LANGUAGES,
      defaultLang: DEFAULT_LANGUAGE,
      // Regional variants (en-US) list only what differs and lean on this.
      fallbackLang: DEFAULT_LANGUAGE,
      reRenderOnLangChange: true,
      prodMode: !isDevMode(),
      missingHandler: { useFallbackTranslation: true },
    },
    loader: BundledTranslationLoader,
  }).concat(
    // The default language is ready before the first render, so nothing ever
    // shows a raw key while the user's own language is still being fetched.
    provideAppInitializer(() => inject(TranslationService).use(DEFAULT_LANGUAGE)),
  );
}
