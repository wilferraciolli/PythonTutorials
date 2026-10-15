import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { disabled, FormRoot, form, required, schema } from '@angular/forms/signals';
import { MatButtonModule } from '@angular/material/button';
import { Router, RouterLink } from '@angular/router';
import { TranslocoPipe } from '@jsverse/transloco';
import { ApiClientService, LinkService } from '@wiltech-labs/ngx-api-client';
import {
  ChipsField,
  FormFieldType,
  InstantDateTimeField,
  SelectField,
  TextareaField,
  TextField,
} from '@wiltech-labs/ngx-forms';
import type { FieldDef } from '@wiltech-labs/ngx-forms';

import { ApiErrors } from '../../../core/api/api-error';
import { TranslationService } from '../../../core/i18n/translation.service';
import { Tag } from '../../../core/api/tags-api';
import { TodoPayload, TodosStore } from '../todos.store';

interface TodoFormModel {
  title: string;
  description: string;
  // UTC instant ('YYYY-MM-DDThh:mm:ssZ', '' when unset) — the exact shape
  // InstantDateTimeField both reads and writes, and TodoPayload.complete_by's
  // own shape, so no local <-> UTC conversion is needed on either side.
  complete_by: string;
  state: string;
}

const INITIAL_MODEL: TodoFormModel = { title: '', description: '', complete_by: '', state: 'NEW' };

@Component({
  selector: 'app-todo-form',
  imports: [
    RouterLink,
    FormRoot,
    MatButtonModule,
    TextField,
    TextareaField,
    SelectField,
    InstantDateTimeField,
    ChipsField,
    TranslocoPipe,
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
  private readonly apiErrors = inject(ApiErrors);
  private readonly i18n = inject(TranslationService);

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

  protected readonly titleField = computed<FieldDef>(() => ({
    name: 'title',
    type: FormFieldType.TEXT,
    label: this.i18n.t('todos.form.title'),
    required: true,
  }));
  protected readonly descriptionField = computed<FieldDef>(() => ({
    name: 'description',
    type: FormFieldType.TEXTAREA,
    label: this.i18n.t('todos.form.description'),
  }));
  protected readonly dueField = computed<FieldDef>(() => ({
    name: 'complete_by',
    type: FormFieldType.INSTANT_DATE_TIME,
    label: this.i18n.t('todos.form.due'),
    required: true,
  }));
  protected readonly stateField = computed<FieldDef>(() => ({
    name: 'state',
    type: FormFieldType.SELECT,
    label: this.i18n.t('todos.form.state'),
    options: this.store.stateOptions().map((option) => ({ label: option.viewValue, value: option.value })),
  }));

  // Hand-written (not ngx-forms' toSchema()) so the required messages come
  // from the app's own translated keys instead of toSchema's English-only
  // "<label> is required".
  protected readonly todoForm = form(
    this.model,
    schema<TodoFormModel>((path) => {
      required(path.title, { message: () => this.i18n.t('todos.form.titleRequired') });
      required(path.complete_by, { message: () => this.i18n.t('todos.form.dueRequired') });
    }),
    {
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
    },
  );

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
  protected readonly tagError = signal<string | null>(null);

  // Not submitted with todoForm — each add/remove is its own API call, same
  // as before this used ngx-forms. ChipsField only replaces the hand-rolled
  // mat-chip-grid as the UI; reconcileTags() below does the actual syncing.
  protected readonly tagsModel = signal<string[]>([]);
  protected readonly canAddTag = computed(() => this.links.hasLink(this.existing()?.links['addTag']));
  protected readonly tagsForm = form(
    this.tagsModel,
    schema<string[]>((path) => {
      disabled(path, () => !this.canAddTag());
    }),
  );
  protected readonly tagsField = computed<FieldDef>(() => ({
    name: 'tags',
    type: FormFieldType.CHIPS,
    label: this.i18n.t('todos.form.tags'),
  }));

  // The last tag list this component itself produced — from the server, or
  // from a reconcile that already succeeded — so the effect below only acts
  // on a genuine ChipsField edit, never on its own sync-back from the server.
  private knownTags: string[] = [];

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
        complete_by: todo.complete_by,
        state: todo.state,
      });
    });

    // Create mode's counterpart — seeds the form from the API's own
    // create-template response (fetched via the `todoTemplate` link; see
    // TodosStore.template) instead of hardcoding defaults here.
    effect(() => {
      if (this.isEditMode()) return;
      const template = this.store.template();
      if (!template) return;
      this.model.set({
        title: template.title,
        description: template.description ?? '',
        complete_by: template.complete_by ?? '',
        state: template.state,
      });
    });

    // Keeps tagsModel in step with the server — the source of truth both on
    // first load and after reconcileTags()'s own reload.
    effect(() => {
      const loaded = this.tags();
      if (loaded === undefined) return;
      const texts = loaded.map((t) => t.tag);
      this.knownTags = texts;
      this.tagsModel.set(texts);
    });

    // Fires on every tagsModel change, including the sync above — but that
    // one always sets tagsModel to exactly knownTags, so the diff below is
    // empty and this is a no-op for it. Only a real ChipsField add/remove
    // produces a non-empty diff.
    effect(() => {
      const current = this.tagsModel();
      const added = current.filter((tag) => !this.knownTags.includes(tag));
      const removed = this.knownTags.filter((tag) => !current.includes(tag));
      if (added.length === 0 && removed.length === 0) return;
      this.knownTags = current;
      void this.reconcileTags(added, removed);
    });
  }

  private async reconcileTags(added: string[], removed: string[]): Promise<void> {
    const todo = this.existing();
    if (!todo) return;

    this.tagError.set(null);
    try {
      for (const tagText of added) {
        const url = this.api.requireLink(
          todo.links['addTag'],
          this.i18n.t('todos.notPermittedUpdate', { id: todo.id }),
        );
        await this.api.post<'tag', Tag, { resource_id: string; tag: string }>('tag', url, {
          resource_id: todo.id,
          tag: tagText,
        });
      }
      for (const tagText of removed) {
        const tag = (this.tags() ?? []).find((t) => t.tag === tagText);
        const url = this.api.requireLink(
          tag?.links['delete'],
          this.i18n.t('tags.notPermittedDelete', { id: tagText }),
        );
        await this.api.delete(url);
      }
      this.tagsResource.reload();
    } catch (err) {
      this.tagError.set(this.extractErrorMessage(err));
      // Revert the optimistic edit — tagsResource still holds the old
      // truth, so re-sync from it instead of guessing.
      const loaded = this.tags() ?? [];
      this.knownTags = loaded.map((t) => t.tag);
      this.tagsModel.set(this.knownTags);
    }
  }

  private async persist(): Promise<void> {
    const value = this.model();
    const payload: TodoPayload = {
      title: value.title,
      description: value.description || null,
      complete_by: value.complete_by,
      state: value.state as TodoPayload['state'],
    };

    if (this.isEditMode()) {
      const existing = this.existing();
      if (!existing) throw new Error(this.i18n.t('todos.form.stillLoading'));
      await this.store.updateTodo(existing, payload);
    } else {
      await this.store.createTodo(payload);
    }
    await this.router.navigate(['/todos']);
  }

  private extractErrorMessage(err: unknown): string {
    return this.apiErrors.describe(err, 'todos.form.saveFailed');
  }
}
