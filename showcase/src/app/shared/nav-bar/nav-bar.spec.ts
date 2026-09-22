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
});
