import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { CurrentUserStore } from '../../core/user/current-user.store';
import { NavMenu } from './nav-menu';

function setup(links: Record<string, { href: string }> = {}) {
  TestBed.configureTestingModule({
    imports: [NavMenu],
    providers: [
      provideRouter([]),
      { provide: CurrentUserStore, useValue: { link: (name: string) => links[name] } },
    ],
  });
  const fixture = TestBed.createComponent(NavMenu);
  fixture.detectChanges();
  const el = fixture.nativeElement as HTMLElement;
  return { fixture, el };
}

const labels = (el: HTMLElement) =>
  Array.from(el.querySelectorAll('.NavMenu-label')).map((label) => label.textContent?.trim());

describe('NavMenu', () => {
  it('lists the destinations in order, without Admin for a non-admin', () => {
    const { el } = setup();
    expect(labels(el)).toEqual(['Home', 'Todos', 'Tags', 'AI chat', 'Ask', 'Timeline', 'Groups']);
  });

  it('adds Admin when the profile carries the admin link', () => {
    const { el } = setup({ admin: { href: '/api/admin' } });
    expect(labels(el)).toContain('Admin');
  });

  it('links each destination to its route', () => {
    const { el } = setup();
    const hrefs = Array.from(el.querySelectorAll('a')).map((a) => a.getAttribute('href'));
    expect(hrefs).toEqual(['/', '/todos', '/tags', '/workers-ai', '/ask', '/timeline', '/groups']);
  });

  it('is a rail by default and a drawer when asked', () => {
    const { fixture, el } = setup();
    expect(el.querySelector('.NavMenu')?.classList).toContain('is-rail');

    fixture.componentRef.setInput('variant', 'drawer');
    fixture.detectChanges();
    expect(el.querySelector('.NavMenu')?.classList).toContain('is-drawer');
    expect(el.querySelector('.NavMenu')?.classList).not.toContain('is-rail');
  });

  it('announces a chosen destination so a modal drawer can close', () => {
    const { fixture, el } = setup();
    let navigated = 0;
    fixture.componentInstance.navigated.subscribe(() => navigated++);

    (el.querySelector('a') as HTMLAnchorElement).click();
    expect(navigated).toBe(1);
  });
});
