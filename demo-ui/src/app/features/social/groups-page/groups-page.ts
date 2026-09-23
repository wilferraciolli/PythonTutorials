import { httpResource } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { Router, RouterLink } from '@angular/router';
import { ApiClientService, CollectionEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { CurrentUserStore } from '../../../core/user/current-user.store';
import { SocialActions } from '../social-actions';
import { Group, GroupVisibility } from '../social.models';

type Filter = 'all' | 'mine' | 'following';

// Browse and search the groups you can see, and create a new one.
@Component({
  selector: 'app-groups-page',
  imports: [RouterLink, MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule],
  templateUrl: './groups-page.html',
  styleUrl: './groups-page.scss',
})
export class GroupsPage {
  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);
  private readonly actions = inject(SocialActions);
  private readonly router = inject(Router);

  protected readonly search = signal('');
  protected readonly filter = signal<Filter>('all');

  private readonly list = httpResource<CollectionEnvelope<'groups', Group>>(() => {
    const url = this.api.resolve(this.currentUser.link('groups'));
    if (!url) return undefined;
    const params = new URLSearchParams();
    if (this.search().trim()) params.set('q', this.search().trim());
    if (this.filter() === 'mine') params.set('mine', 'true');
    if (this.filter() === 'following') params.set('following', 'true');
    const query = params.toString();
    return query ? `${url}?${query}` : url;
  });

  protected readonly groups = computed(() => this.list.value()?._data['groups'] ?? []);
  protected readonly isLoading = computed(() => this.list.isLoading());
  protected readonly errorMessage = computed(() => {
    const error = this.list.error();
    return error ? describeApiError(error, "Couldn't load groups.") : null;
  });
  protected readonly available = computed(
    () => !this.currentUser.profile() || !!this.currentUser.link('groups'),
  );

  // create form
  protected readonly creating = signal(false);
  protected readonly name = signal('');
  protected readonly description = signal('');
  protected readonly visibility = signal<GroupVisibility>('PUBLIC');
  protected readonly saving = signal(false);
  protected readonly createError = signal<string | null>(null);

  protected setFilter(value: string): void {
    if (value === 'all' || value === 'mine' || value === 'following') this.filter.set(value);
  }

  protected setVisibility(value: string): void {
    if (value === 'PUBLIC' || value === 'PRIVATE') this.visibility.set(value);
  }

  protected async create(): Promise<void> {
    if (!this.name().trim() || this.saving()) return;
    this.saving.set(true);
    this.createError.set(null);
    try {
      const group = await this.actions.createGroup(this.currentUser.link('createGroup'), {
        name: this.name().trim(),
        description: this.description().trim(),
        visibility: this.visibility(),
      });
      await this.router.navigate(['/groups', group.id]);
    } catch (err) {
      this.createError.set(describeApiError(err, "Couldn't create the group."));
    } finally {
      this.saving.set(false);
    }
  }
}
