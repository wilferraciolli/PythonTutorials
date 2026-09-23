import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { TodosStore } from '../todos.store';
import { TodosList } from './todos-list';

describe('TodosList', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TodosList],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), TodosStore],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(TodosList);
    expect(fixture.componentInstance).toBeTruthy();
  });

  // No /me loaded yet (no session in a unit test) means no myTodosHref, so
  // the store never fires a request — the empty state renders instead of
  // an error.
  it('shows the empty state before /me has resolved a todos link', () => {
    const fixture = TestBed.createComponent(TodosList);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.TodosList-empty')).toBeTruthy();
  });
});

describe('TodosList rows', () => {
  const link = { href: '/api/todos/x' };
  const todo = (id: string, title: string, state: string, complete_by: string) => ({
    id,
    user_id: 'u1',
    title,
    description: null,
    complete_by,
    state,
    created_date: '2026-01-01T00:00:00Z',
    links: { update: link, delete: link },
  });
  const past = '2020-01-01T00:00:00Z';
  const future = '2999-01-01T00:00:00Z';

  const store = {
    stateFilter: signal(null),
    stateOptions: signal([
      { value: 'NEW', viewValue: 'New' },
      { value: 'CLOSED', viewValue: 'Closed' },
    ]),
    todos: signal([
      todo('1', 'Late and open', 'NEW', past),
      todo('2', 'Late but done', 'CLOSED', past),
      todo('3', 'On time', 'NEW', future),
    ]),
    isLoading: signal(false),
    loadErrorMessage: signal(null),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TodosList],
      providers: [provideRouter([]), { provide: TodosStore, useValue: store }],
    }).compileComponents();
  });

  function render() {
    const fixture = TestBed.createComponent(TodosList);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('shows one row per todo, worded the way the API words its states', () => {
    const rows = render().querySelectorAll('.TodosList-item');
    expect(rows).toHaveLength(3);
    expect(rows[0].querySelector('.TodosList-item-meta')?.textContent).toContain('New · Due');
  });

  it('flags only open todos that are past due', () => {
    const rows = render().querySelectorAll('.TodosList-item');
    expect(rows[0].querySelector('.is-overdue')).toBeTruthy();
    expect(rows[1].querySelector('.is-overdue')).toBeNull();
    expect(rows[2].querySelector('.is-overdue')).toBeNull();
  });

  it('marks a closed todo and offers to reopen it', () => {
    const closed = render().querySelectorAll('.TodosList-item')[1];
    expect(closed.classList).toContain('is-closed');
    expect(closed.querySelector('.TodosList-check')?.getAttribute('aria-label')).toBe('Reopen');
  });
});
