import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Envelope, Links, fieldOptions, metaLink, unwrapData } from '../../core/api/envelope';
import { CurrentUserStore } from '../../core/user/current-user.store';
import { environment } from '../../../environments/environment';

export type TodoState = 'NEW' | 'ACTIVE' | 'CLOSED';

export interface Todo {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  complete_by: string;
  state: TodoState;
  created_date: string;
  links: Links;
}

export interface TodoPayload {
  title: string;
  description: string | null;
  complete_by: string;
  state: TodoState;
}

type TodosEnvelope = Envelope<Todo[]>;
type TodoEnvelope = Envelope<Todo>;

const EMPTY_LIST_ENVELOPE: TodosEnvelope = { _data: { todos: [] } };

// Feature-local state — a plain injectable, not a signalStore, per
// docs/frontend-conventions.md. Provided on TodosShell so its lifecycle is
// tied to the /todos route tree being active.
@Injectable()
export class TodosStore {
  private readonly http = inject(HttpClient);
  private readonly currentUser = inject(CurrentUserStore);

  readonly stateFilter = signal<TodoState | null>(null);

  // The collection URL is never built by hand — it's the `myTodos` link
  // /me hands out (see current-user.store.ts). No href yet (still loading
  // /me) means no request; httpResource treats `undefined` as "don't fetch".
  readonly listResource = httpResource<TodosEnvelope>(
    () => {
      const href = this.currentUser.myTodosHref();
      if (!href) return undefined;
      const state = this.stateFilter();
      return `${environment.apiUrl}${href}${state ? `?state=${state}` : ''}`;
    },
    { defaultValue: EMPTY_LIST_ENVELOPE },
  );

  readonly todos = computed(() => unwrapData(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'todos') ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());

  // Allowed state values straight from the API's metadata — see
  // DoctorsManagementStore.specializationOptions for the same pattern.
  readonly stateOptions = computed(() =>
    fieldOptions(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'state'),
  );

  async createTodo(payload: TodoPayload): Promise<Todo> {
    // The collection's own `createTodo` link (from the last response),
    // falling back to `myTodos` if the list hasn't loaded yet — same URL
    // either way today, but this is the one HATEOAS says to POST to.
    const url =
      metaLink(this.listResource.value(), 'createTodo') ?? this.currentUser.myTodosHref();
    if (!url) throw new Error('No todos collection link available yet — try again.');
    const response = await firstValueFrom(this.http.post<TodoEnvelope>(`${environment.apiUrl}${url}`, payload));
    this.listResource.reload();
    return unwrapData(response, 'todo') as Todo;
  }

  async updateTodo(todo: Todo, payload: TodoPayload): Promise<Todo> {
    const url = todo.links['update']?.href;
    if (!url) throw new Error(`Not permitted to update todo ${todo.id}`);
    const response = await firstValueFrom(this.http.put<TodoEnvelope>(`${environment.apiUrl}${url}`, payload));
    this.listResource.reload();
    return unwrapData(response, 'todo') as Todo;
  }

  async deleteTodo(todo: Todo): Promise<void> {
    const url = todo.links['delete']?.href;
    if (!url) throw new Error(`Not permitted to delete todo ${todo.id}`);
    await firstValueFrom(this.http.delete(`${environment.apiUrl}${url}`));
    this.listResource.reload();
  }
}
