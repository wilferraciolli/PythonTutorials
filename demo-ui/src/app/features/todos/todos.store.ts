import { httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import {
  ApiClientService,
  CollectionEnvelope,
  ILink,
  LinkService,
  MetadataService,
} from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../core/api/api-error';
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
  private readonly links = inject(LinkService);
  private readonly metadata = inject(MetadataService);
  private readonly currentUser = inject(CurrentUserStore);

  readonly stateFilter = signal<TodoState | null>(null);

  // A raw httpResource, not ApiClientService.collectionResource() — this
  // list also needs `_metadata` (stateOptions below) and `_metaLinks`
  // (todoTemplate), which that convenience wrapper only exposes `_data`
  // from. The URL is never built by hand: it's the `todos` link the user
  // profile hands out (current-user.store.ts), resolved via ApiClientService
  // against API_ORIGIN. No link yet (still loading the profile) means no request.
  private readonly listResource = httpResource<TodosEnvelope>(() => {
    const link = this.currentUser.myTodosLink();
    if (!link) return undefined;
    const url = this.api.resolve(link)!;
    const state = this.stateFilter();
    return state ? `${url}?state=${state}` : url;
  });

  // `value()` throws while the resource is in its error state, so every read
  // goes through here: no value (still loading, or failed) reads as undefined
  // and the page falls through to its own error message instead of crashing.
  private readonly data = computed(() =>
    this.listResource.hasValue() ? this.listResource.value() : undefined,
  );

  readonly todos = computed(() => this.data()?._data['todos'] ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());
  readonly loadErrorMessage = computed(() => {
    const error = this.loadError();
    return error ? describeApiError(error, "Couldn't load your todos.") : null;
  });

  // Allowed state values straight from the API's own metadata (its
  // business rule: NEW stops being offered once a todo has left it) —
  // MetadataService.resolveMetadataIdValues turns {id, value}[] into the
  // {value, viewValue}[] shape a <select> renders.
  readonly stateOptions = computed(() =>
    this.metadata.resolveMetadataIdValues(this.data()?._metadata?.['state']?.values ?? []),
  );

  // The "new todo" screen's own resource, fetched via the collection's
  // `todoTemplate` link — gives the create form real server-side defaults
  // (e.g. `complete_by` defaulting to now) instead of the UI guessing them.
  private readonly templateResource = this.api.resource<'todo', TodoPayload>('todo', () => {
    const link = this.data()?._metaLinks?.['todoTemplate'];
    return link ? this.api.resolve(link) : undefined;
  });

  readonly template = this.templateResource.value;
  readonly templateLoading = this.templateResource.isLoading;

  async createTodo(payload: TodoPayload): Promise<Todo> {
    // The create URL is never hand-built or read off a separate meta link
    // — it's derived from the same `todoTemplate` link the form used to
    // load its defaults, via LinkService.getCreateUrlFromTemplateUrl()
    // (strips the trailing "/template" segment).
    const templateLink = this.data()?._metaLinks?.['todoTemplate'];
    const templateUrl = this.api.requireLink(
      templateLink,
      'No todo template link available yet — try again.',
    );
    const createUrl = this.links.getCreateUrlFromTemplateUrl({ href: templateUrl });
    if (!createUrl) {
      throw new Error('Could not derive the create-todo URL from the template link.');
    }

    const todo = await this.api.post<'todo', Todo, TodoPayload>('todo', createUrl, payload);
    this.listResource.reload();
    return todo;
  }

  async updateTodo(todo: Todo, payload: TodoPayload): Promise<Todo> {
    const url = this.api.requireLink(
      todo.links['update'],
      `Not permitted to update todo ${todo.id}`,
    );
    const updated = await this.api.put<'todo', Todo, TodoPayload>('todo', url, payload);
    this.listResource.reload();
    return updated;
  }

  async deleteTodo(todo: Todo): Promise<void> {
    const url = this.api.requireLink(
      todo.links['delete'],
      `Not permitted to delete todo ${todo.id}`,
    );
    await this.api.delete(url);
    this.listResource.reload();
  }
}
