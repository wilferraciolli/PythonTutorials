import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { NavBar } from './nav-bar';

describe('NavBar', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavBar],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(NavBar);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows a sign-in button when signed out', () => {
    const fixture = TestBed.createComponent(NavBar);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.NavBar-sign-in')).toBeTruthy();
    expect(compiled.querySelector('.NavBar-links')).toBeFalsy();
  });

  it('shows an EN/GR language toggle with the current locale active', () => {
    const fixture = TestBed.createComponent(NavBar);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const options = Array.from(compiled.querySelectorAll<HTMLButtonElement>('.NavBar-lang-option'));
    expect(options.map((el) => el.textContent?.trim())).toEqual(['GR', 'EN']);

    const active = compiled.querySelector('.NavBar-lang-option.is-active');
    expect(active?.textContent?.trim()).toBe('GR'); // el-GR is the store's default fallback locale
  });
});
