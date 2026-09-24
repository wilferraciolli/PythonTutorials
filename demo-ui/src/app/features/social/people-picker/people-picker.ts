import { httpResource } from '@angular/common/http';
import { Component, computed, inject, model, signal } from '@angular/core';
import {
  MatAutocompleteModule,
  MatAutocompleteSelectedEvent,
} from '@angular/material/autocomplete';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { ApiClientService, CollectionEnvelope, IdValue } from '@wiliamferraciolli/ngx-api-client';

import { CurrentUserStore } from '../../../core/user/current-user.store';
import { MAX_TAGGED_PEOPLE, UserSummary } from '../social.models';

const MIN_SEARCH = 2;

// "Tag people" for a post: the tagged people as input chips, and a search
// (the profile's `searchUsers` link) that offers everyone else as you type.
// Two-way bound: `[(people)]` holds {id, value: full name}, the same shape the
// API's `_metadata.taggedUserIds.values` uses, so a post's existing tags drop
// straight in and `people().map(p => p.id)` is what gets sent.
@Component({
  selector: 'app-people-picker',
  imports: [MatAutocompleteModule, MatChipsModule, MatFormFieldModule, MatIconModule],
  templateUrl: './people-picker.html',
  styleUrl: './people-picker.scss',
})
export class PeoplePicker {
  readonly people = model<IdValue[]>([]);

  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);

  protected readonly term = signal('');
  protected readonly full = computed(() => this.people().length >= MAX_TAGGED_PEOPLE);

  private readonly search = httpResource<CollectionEnvelope<'users', UserSummary>>(() => {
    const url = this.api.resolve(this.currentUser.link('searchUsers'));
    const term = this.term().trim();
    return url && term.length >= MIN_SEARCH ? `${url}?q=${encodeURIComponent(term)}` : undefined;
  });

  protected readonly matches = computed(() => {
    if (!this.search.hasValue() || this.term().trim().length < MIN_SEARCH) return [];
    const tagged = new Set(this.people().map((person) => person.id));
    return (this.search.value()._data['users'] ?? []).filter((user) => !tagged.has(user.id));
  });

  protected add(event: MatAutocompleteSelectedEvent, input: HTMLInputElement): void {
    const user = event.option.value as UserSummary;
    if (!this.full() && !this.people().some((person) => person.id === user.id)) {
      this.people.update((people) => [...people, { id: user.id, value: user.name }]);
    }
    this.term.set('');
    input.value = '';
  }

  protected remove(person: IdValue): void {
    this.people.update((people) => people.filter((p) => p.id !== person.id));
  }

  // The option's value is a user object; keep the input empty after picking one.
  protected readonly blank = () => '';
}
