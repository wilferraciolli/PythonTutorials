import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_ORIGIN } from '@wiliamferraciolli/ngx-api-client';

import { CurrentUserStore } from '../../core/user/current-user.store';
import { TodosStore } from './todos.store';

describe('TodosStore', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        TodosStore,
        { provide: API_ORIGIN, useValue: '' },
        {
          provide: CurrentUserStore,
          useValue: { myTodosLink: () => ({ href: '/api/todos' }) },
        },
      ],
    });
  });

  // Regression: reading a failed httpResource's value() throws, which used to
  // take the whole todos page down (it sat on "Loading…") instead of showing
  // the error message.
  it('reads as empty, with an error message, when the API fails', async () => {
    const store = TestBed.inject(TodosStore);
    TestBed.tick();
    TestBed.inject(HttpTestingController)
      .expectOne('/api/todos')
      .flush({ message: 'Boom' }, { status: 500, statusText: 'Server Error' });
    await Promise.resolve();

    expect(() => store.todos()).not.toThrow();
    expect(store.todos()).toEqual([]);
    expect(store.stateOptions()).toEqual([]);
    expect(store.loadErrorMessage()).toBeTruthy();
  });

  it('exposes the todos and the API-provided states once loaded', async () => {
    const store = TestBed.inject(TodosStore);
    TestBed.tick();
    TestBed.inject(HttpTestingController)
      .expectOne('/api/todos')
      .flush({
        _data: { todos: [{ id: '1', title: 'One', state: 'NEW', links: {} }] },
        _metadata: { state: { values: [{ id: 'NEW', value: 'New' }] } },
      });
    await Promise.resolve();

    expect(store.todos().map((todo) => todo.title)).toEqual(['One']);
    expect(store.stateOptions()).toEqual([{ value: 'NEW', viewValue: 'New' }]);
    expect(store.loadErrorMessage()).toBeNull();
  });
});
