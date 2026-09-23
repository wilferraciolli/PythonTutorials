import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { AuthStore } from './core/auth/auth.store';

import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders the router outlet', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('router-outlet')).toBeTruthy();
  });

  // No session means nowhere to navigate: just the app bar and the page.
  it('has no navigation rail while signed out', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.AppShell-rail')).toBeNull();
    expect(compiled.querySelector('[aria-label="Open navigation menu"]')).toBeNull();
  });
});

describe('App shell, signed in', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: AuthStore, useValue: { isSignedIn: () => true, signIn: async () => {} } },
      ],
    }).compileComponents();
  });

  // Unit tests run without matchMedia, so the window is never "compact":
  // a signed-in user gets the rail rather than the modal drawer.
  it('shows the navigation rail', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.AppShell-rail app-nav-menu')).toBeTruthy();
    expect(compiled.querySelector('[aria-label="Open navigation menu"]')).toBeNull();
  });
});
