import { TestBed } from '@angular/core/testing';

import { TranslationService } from './translation.service';

describe('TranslationService', () => {
  function setup() {
    return { i18n: TestBed.inject(TranslationService) };
  }

  it('starts in en-GB', () => {
    const { i18n } = setup();
    expect(i18n.t('nav.signIn')).toBe('Sign in');
  });

  it('switches language at runtime', async () => {
    const { i18n } = setup();
    await i18n.use('el-CY');
    expect(i18n.t('nav.signIn')).toBe('Σύνδεση');
    expect(i18n.language()).toBe('el-CY');

    await i18n.use('pt-BR');
    expect(i18n.t('nav.signIn')).toBe('Entrar');
  });

  it('falls back to en-GB for strings a regional variant leaves out', async () => {
    const { i18n } = setup();
    await i18n.use('en-US');
    expect(i18n.t('nav.signIn')).toBe('Sign in');
  });

  it('interpolates params', async () => {
    const { i18n } = setup();
    await i18n.use('el-CY');
    expect(i18n.t('tags.deleteDialog.message', { name: 'επείγον' })).toContain('επείγον');
  });

  it('labels API option values, and shows an unknown value as itself', async () => {
    const { i18n } = setup();
    await i18n.use('el-CY');
    expect(i18n.optionLabel('settings.options.language', 'pt-BR')).toBe('Πορτογαλικά (Βραζιλία)');
    expect(i18n.optionLabel('settings.options.language', 'fr-FR')).toBe('fr-FR');
  });
});
