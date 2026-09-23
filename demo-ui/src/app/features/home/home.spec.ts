import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { Home } from './home';

describe('Home', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Home],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(Home);
    expect(fixture.componentInstance).toBeTruthy();
  });

  // All cards render unconditionally when signed out — no sign-in gate on
  // this page; authGuard is what stops a signed-out visitor at /todos or
  // /workers-ai. (When signed in, a card hides its link if /me lacks it.)
  it('links to every guarded project route', () => {
    const fixture = TestBed.createComponent(Home);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const hrefs = Array.from(compiled.querySelectorAll('a')).map((a) => a.getAttribute('href'));
    expect(hrefs).toContain('/todos');
    expect(hrefs).toContain('/workers-ai');
  });
});
