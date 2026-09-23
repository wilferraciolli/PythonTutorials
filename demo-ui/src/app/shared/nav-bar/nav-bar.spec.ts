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

  // AuthStore starts with no session (init() only runs via
  // provideAppInitializer), so an un-bootstrapped store is signed out.
  it('shows a sign-in button when signed out', () => {
    const fixture = TestBed.createComponent(NavBar);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('button')?.textContent).toContain('Sign in');
  });

  it('only shows the navigation-drawer button when asked to', () => {
    const fixture = TestBed.createComponent(NavBar);
    const el = fixture.nativeElement as HTMLElement;
    fixture.detectChanges();
    expect(el.querySelector('[aria-label="Open navigation menu"]')).toBeNull();

    fixture.componentRef.setInput('showMenuButton', true);
    fixture.detectChanges();
    expect(el.querySelector('[aria-label="Open navigation menu"]')).toBeTruthy();
  });

  it('asks the shell to open the drawer', () => {
    const fixture = TestBed.createComponent(NavBar);
    let requested = 0;
    fixture.componentInstance.menuRequested.subscribe(() => requested++);
    fixture.componentRef.setInput('showMenuButton', true);
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[aria-label="Open navigation menu"]')!
      .click();
    expect(requested).toBe(1);
  });

  it('picks up the scrolled (tonal) container once the page scrolls', () => {
    const fixture = TestBed.createComponent(NavBar);
    const bar = () => (fixture.nativeElement as HTMLElement).querySelector('.NavBar')!;
    fixture.detectChanges();
    expect(bar().classList).not.toContain('is-scrolled');

    Object.defineProperty(window, 'scrollY', { value: 24, configurable: true });
    window.dispatchEvent(new Event('scroll'));
    fixture.detectChanges();
    expect(bar().classList).toContain('is-scrolled');

    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true });
  });
});
