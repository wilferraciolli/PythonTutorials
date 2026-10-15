import { TestBed } from '@angular/core/testing';

import { provideI18n } from './app/core/i18n/i18n.providers';

// Every component now reads translations, so every spec gets the real
// (bundled) dictionaries — assertions can use the en-GB text a user would see.
beforeEach(() => {
  TestBed.configureTestingModule({ providers: [provideI18n()] });
});
