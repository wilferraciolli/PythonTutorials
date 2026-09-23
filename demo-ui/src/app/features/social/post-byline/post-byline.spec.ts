import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { PostByline } from './post-byline';

describe('PostByline', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PostByline],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  function render(inputs: Record<string, unknown>) {
    const fixture = TestBed.createComponent(PostByline);
    for (const [name, value] of Object.entries(inputs)) fixture.componentRef.setInput(name, value);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it("shows the author's name and initial, and a machine-readable time", () => {
    const el = render({ author: 'Olive Branch', date: '2026-01-01T00:00:00Z' });
    expect(el.querySelector('.PostByline-author')?.textContent).toBe('Olive Branch');
    expect(el.querySelector('.PostByline-avatar')?.textContent?.trim()).toBe('O');
    expect(el.querySelector('time')?.getAttribute('datetime')).toBe('2026-01-01T00:00:00Z');
  });

  it('says Unknown for a deleted author', () => {
    const el = render({ author: null, date: '2026-01-01T00:00:00Z' });
    expect(el.querySelector('.PostByline-author')?.textContent).toBe('Unknown');
  });

  it('links the group only when both its id and name are given', () => {
    const without = render({ author: 'A', date: '2026-01-01T00:00:00Z' });
    expect(without.querySelector('.PostByline-group')).toBeNull();

    const withGroup = render({
      author: 'A',
      date: '2026-01-01T00:00:00Z',
      groupId: 'g1',
      groupName: 'News',
    });
    const link = withGroup.querySelector('.PostByline-group');
    expect(link?.textContent).toBe('News');
    expect(link?.getAttribute('href')).toBe('/groups/g1');
  });

  it('marks an edited post', () => {
    const el = render({
      author: 'A',
      date: '2026-01-01T00:00:00Z',
      editedDate: '2026-01-02T00:00:00Z',
    });
    expect(el.querySelector('.PostByline-meta')?.textContent).toContain('Edited');
  });
});
