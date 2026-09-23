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

  it('invites a signed-out visitor to sign in, above the destinations', () => {
    const fixture = TestBed.createComponent(Home);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('FastAPI');
    expect(compiled.querySelector('.Home-signin')?.textContent).toContain('Sign in');
  });

  // Home, Tags (not a card) and Admin (admins only) are left out; the two AI
  // destinations carry the tertiary role.
  it('shows a card per destination, tinting the AI ones', () => {
    const fixture = TestBed.createComponent(Home);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const titles = Array.from(compiled.querySelectorAll('.Home-card-title')).map((t) =>
      t.textContent?.trim(),
    );
    expect(titles).toEqual(['Todos', 'AI chat', 'Ask your data', 'Timeline', 'Groups']);
    expect(compiled.querySelectorAll('.Home-card.is-tertiary')).toHaveLength(2);
  });
});
