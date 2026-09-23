import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
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
