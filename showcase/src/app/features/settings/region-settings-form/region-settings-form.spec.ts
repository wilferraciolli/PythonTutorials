import { TestBed } from '@angular/core/testing';

import { RegionSettingsOptions, RegionSettingsPayload } from '../region-settings.store';
import { RegionSettingsForm } from './region-settings-form';

const SETTINGS: RegionSettingsPayload = {
  timezone: 'Europe/London',
  language: 'en-GB',
  currency: 'GBP',
  theme: 'light',
};

const OPTIONS: RegionSettingsOptions = {
  timezone: [
    { value: 'Europe/London', viewValue: 'Europe/London' },
    { value: 'Asia/Nicosia', viewValue: 'Asia/Nicosia' },
  ],
  language: [{ value: 'en-GB', viewValue: 'en-GB' }],
  currency: [{ value: 'GBP', viewValue: 'GBP' }],
  theme: [
    { value: 'light', viewValue: 'light' },
    { value: 'dark', viewValue: 'dark' },
  ],
};

describe('RegionSettingsForm', () => {
  function setup() {
    TestBed.configureTestingModule({ imports: [RegionSettingsForm] });
    const fixture = TestBed.createComponent(RegionSettingsForm);
    fixture.componentRef.setInput('settings', SETTINGS);
    fixture.componentRef.setInput('options', OPTIONS);
    fixture.detectChanges();
    const element: HTMLElement = fixture.nativeElement;
    const submit = element.querySelector<HTMLButtonElement>('button[type="submit"]')!;
    return { fixture, element, submit };
  }

  it('renders one select per field with the API options', () => {
    const { element } = setup();
    const selects = element.querySelectorAll('select');
    expect(selects.length).toBe(4);
    expect(selects[0].querySelectorAll('option').length).toBe(2);
  });

  it('keeps Save disabled until something changes', async () => {
    const { fixture, element, submit } = setup();
    expect(submit.disabled).toBe(true);

    const theme = element.querySelectorAll('select')[3];
    theme.value = 'dark';
    theme.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    await fixture.whenStable();

    expect(submit.disabled).toBe(false);
  });

  it('emits the edited settings on submit', async () => {
    const { fixture, element } = setup();
    const emitted: RegionSettingsPayload[] = [];
    fixture.componentInstance.save.subscribe((value) => emitted.push(value));

    const theme = element.querySelectorAll('select')[3];
    theme.value = 'dark';
    theme.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    element.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    expect(emitted).toEqual([{ ...SETTINGS, theme: 'dark' }]);
  });
});
