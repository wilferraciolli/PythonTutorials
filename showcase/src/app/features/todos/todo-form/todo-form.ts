import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormField, FormRoot, form, required, schema } from '@angular/forms/signals';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { Router, RouterLink } from '@angular/router';
import { ApiClientService, LinkService } from '@wiliamferraciolli/ngx-api-client';

import { Tag } from '../../../core/api/tags-api';
import { TodoPayload, TodosStore } from '../todos.store';

interface TodoFormModel {
  title: string;
  description: string;
  // Native `datetime-local` value ("YYYY-MM-DDTHH:mm", local time) — see
  // toDatetimeLocalValue()/fromDatetimeLocalValue() for the round-trip to
  // the API's UTC ISO string.
  complete_by: string;
  state: string;
}

const INITIAL_MODEL: TodoFormModel = { title: '', description: '', complete_by: '', state: 'NEW' };

const todoSchema = schema<TodoFormModel>((path) => {
  required(path.title);
  required(path.complete_by);
});

function toDatetimeLocalValue(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromDatetimeLocalValue(value: string): string {
  return new Date(value).toISOString();
}

@Component({
  selector: 'app-todo-form',
  imports: [
    RouterLink,
    FormField,
    FormRoot,
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './todo-form.html',
  styleUrl: './todo-form.scss',
})
export class TodoForm {
  // Bound from the `:id` route param via withComponentInputBinding() —
  // present only on the `:id/edit` route, undefined on `new`.
  readonly id = input<string>();

  protected readonly store = inject(TodosStore);
  protected readonly links = inject(LinkService);
  private readonly api = inject(ApiClientService);
  private readonly router = inject(Router);

  protected readonly isEditMode = computed(() => this.id() !== undefined);

  // The list is already loaded for the page above this one in the route
  // tree — reuse it instead of a second GET for the single todo, and
  // follow its own `links` for the mutations below.
  protected readonly existing = computed(() => this.store.todos().find((t) => t.id === this.id()));
  protected readonly notFound = computed(
    () => this.isEditMode() && !this.store.isLoading() && !this.existing(),
  );

  protected readonly model = signal<TodoFormModel>(INITIAL_MODEL);
  protected readonly saveError = signal<string | null>(null);
  protected readonly saving = signal(false);

  protected readonly todoForm = form(this.model, todoSchema, {
    submission: {
      action: async () => {
        this.saveError.set(null);
        this.saving.set(true);
        try {
          await this.persist();
        } catch (err) {
          this.saveError.set(this.extractErrorMessage(err));
        } finally {
          this.saving.set(false);
        }
        return undefined;
      },
    },
  });

  // Reactively bound to the current todo's own `tags` link — resolves to
  // undefined (unfetched) until the todo is found, and re-resolves if a
  // different :id is navigated to. Follows the link rather than
  // reconstructing `/tags?resource_id=…` client-side.
  private readonly tagsResource = this.api.collectionResource<'tags', Tag>('tags', () => {
    const link = this.existing()?.links['tags'];
    return link ? this.api.resolve(link) : undefined;
  });
  protected readonly tags = this.tagsResource.value;
  protected readonly tagsLoading = this.tagsResource.isLoading;
  protected readonly newTag = signal('');
  protected readonly tagError = signal<string | null>(null);

  constructor() {
    // Prefills the writable form model once the existing todo is found —
    // there is no signals-only way to seed a WritableSignal from a
    // computed, so this is a genuine (one-shot, per todo id) sync effect.
    effect(() => {
      const todo = this.existing();
      if (!todo) return;
      this.model.set({
        title: todo.title,
        description: todo.description ?? '',
        complete_by: toDatetimeLocalValue(todo.complete_by),
        state: todo.state,
      });
    });
  }

  protected async addTag(): Promise<void> {
    const todo = this.existing();
    const tagText = this.newTag().trim();
    if (!todo || !tagText) return;

    this.tagError.set(null);
    try {
      const url = this.api.requireLink(todo.links['addTag'], `Not permitted to tag todo ${todo.id}`);
      await this.api.post<'tag', Tag, { resource_id: string; tag: string }>('tag', url, {
        resource_id: todo.id,
        tag: tagText,
      });
      this.tagsResource.reload();
      this.newTag.set('');
    } catch (err) {
      this.tagError.set(this.extractErrorMessage(err));
    }
  }

  protected async removeTag(tag: Tag): Promise<void> {
    this.tagError.set(null);
    try {
      const url = this.api.requireLink(tag.links['delete'], `Not permitted to delete tag ${tag.id}`);
      await this.api.delete(url);
      this.tagsResource.reload();
    } catch (err) {
      this.tagError.set(this.extractErrorMessage(err));
    }
  }

  private async persist(): Promise<void> {
    const value = this.model();
    const payload: TodoPayload = {
      title: value.title,
      description: value.description || null,
      complete_by: fromDatetimeLocalValue(value.complete_by),
      state: value.state as TodoPayload['state'],
    };

    if (this.isEditMode()) {
      const existing = this.existing();
      if (!existing) throw new Error('Todo is still loading — try again.');
      await this.store.updateTodo(existing, payload);
    } else {
      await this.store.createTodo(payload);
    }
    await this.router.navigate(['/todos']);
  }

  private extractErrorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return err.error?.detail ?? 'Failed to save.';
    }
    return err instanceof Error ? err.message : 'Failed to save.';
  }
}
