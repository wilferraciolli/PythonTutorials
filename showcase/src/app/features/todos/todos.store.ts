import { httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { ApiClientService, CollectionEnvelope, ILink, MetadataService } from '@wiliamferraciolli/ngx-api-client';

import { CurrentUserStore } from '../../core/user/current-user.store';

export type TodoState = 'NEW' | 'ACTIVE' | 'CLOSED';

export interface Todo {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  complete_by: string;
  state: TodoState;
  created_date: string;
  links: Record<string, ILink>;
}

export interface TodoPayload {
  title: string;
  description: string | null;
  complete_by: string;
  state: TodoState;
}

type TodosEnvelope = CollectionEnvelope<'todos', Todo>;

// Feature-local state — a plain injectable, not a signalStore, per
// docs/frontend-conventions.md. Provided on TodosShell so its lifecycle is
// tied to the /todos route tree being active.
@Injectable()
export class TodosStore {
  private readonly api = inject(ApiClientService);
  private readonly metadata = inject(MetadataService);
  private readonly currentUser = inject(CurrentUserStore);

  readonly stateFilter = signal<TodoState | null>(null);

  // A raw httpResource, not ApiClientService.collectionResource() — this
  // list also needs `_metadata` (stateOptions below) and `_metaLinks`
  // (createTodo), which that convenience wrapper only exposes `_data`
  // from. The URL is never built by hand: it's the `myTodos` link /me
  // hands out (current-user.store.ts), resolved via ApiClientService
  // against API_ORIGIN. No link yet (still loading /me) means no request.
  private readonly listResource = httpResource<TodosEnvelope>(() => {
    const link = this.currentUser.myTodosLink();
    if (!link) return undefined;
    const url = this.api.resolve(link)!;
    const state = this.stateFilter();
    return state ? `${url}?state=${state}` : url;
  });

  readonly todos = computed(() => this.listResource.value()?._data['todos'] ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());

  // Allowed state values straight from the API's own metadata (its
  // business rule: NEW stops being offered once a todo has left it) —
  // MetadataService.resolveMetadataIdValues turns {id, value}[] into the
  // {value, viewValue}[] shape a <select> renders.
  readonly stateOptions = computed(() =>
    this.metadata.resolveMetadataIdValues(this.listResource.value()?._metadata?.['state']?.values ?? []),
  );

  async createTodo(payload: TodoPayload): Promise<Todo> {
    // The collection's own `createTodo` link (from the last response),
    // falling back to `myTodos` if the list hasn't loaded yet — same URL
    // either way today, but this is the one HATEOAS says to POST to.
    const link = this.listResource.value()?._metaLinks?.['createTodo'] ?? this.currentUser.myTodosLink();
    const url = this.api.requireLink(link, 'No todos collection link available yet — try again.');
    const todo = await this.api.post<'todo', Todo, TodoPayload>('todo', url, payload);
    this.listResource.reload();
    return todo;
  }

  async updateTodo(todo: Todo, payload: TodoPayload): Promise<Todo> {
    const url = this.api.requireLink(todo.links['update'], `Not permitted to update todo ${todo.id}`);
    const updated = await this.api.put<'todo', Todo, TodoPayload>('todo', url, payload);
    this.listResource.reload();
    return updated;
  }

  async deleteTodo(todo: Todo): Promise<void> {
    const url = this.api.requireLink(todo.links['delete'], `Not permitted to delete todo ${todo.id}`);
    await this.api.delete(url);
    this.listResource.reload();
  }
}
