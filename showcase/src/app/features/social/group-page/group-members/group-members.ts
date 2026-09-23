import { DatePipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { Component, computed, inject, input, output, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { ApiClientService, CollectionEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../../core/api/api-error';
import { CurrentUserStore } from '../../../../core/user/current-user.store';
import { SocialActions } from '../../social-actions';
import { Group, GroupMember, UserSummary } from '../../social.models';

const MIN_SEARCH = 2;

// A group's members: who owns it, remove / make-owner buttons where the API
// allows them, and (for anyone with the group's `addMember` link) a user
// search to add someone. Adding someone to a private group is the only way in.
@Component({
  selector: 'app-group-members',
  imports: [DatePipe, MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule],
  templateUrl: './group-members.html',
  styleUrl: './group-members.scss',
})
export class GroupMembers {
  readonly group = input.required<Group>();
  /** Membership or ownership changed: the parent reloads the group. */
  readonly changed = output<void>();

  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);
  private readonly actions = inject(SocialActions);

  private readonly membersResource = httpResource<CollectionEnvelope<'members', GroupMember>>(() =>
    this.api.resolve(this.group().links['members']),
  );
  protected readonly members = computed(() => this.membersResource.value()?._data['members'] ?? []);
  protected readonly myId = computed(() => this.currentUser.me()?.id);

  protected readonly canAdd = computed(() => !!this.group().links['addMember']);
  protected readonly search = signal('');
  private readonly searchResource = httpResource<CollectionEnvelope<'users', UserSummary>>(() => {
    const url = this.api.resolve(this.currentUser.link('searchUsers'));
    const term = this.search().trim();
    return url && this.canAdd() && term.length >= MIN_SEARCH
      ? `${url}?q=${encodeURIComponent(term)}`
      : undefined;
  });
  protected readonly candidates = computed(() => {
    const memberIds = new Set(this.members().map((m) => m.userId));
    return (this.searchResource.value()?._data['users'] ?? []).filter((u) => !memberIds.has(u.id));
  });
  protected readonly searching = computed(
    () => this.search().trim().length >= MIN_SEARCH && this.searchResource.isLoading(),
  );

  protected readonly busy = signal(false);
  protected readonly error = signal<string | null>(null);

  protected async add(user: UserSummary): Promise<void> {
    await this.attempt(
      () => this.actions.addMember(this.group(), user.id),
      `Couldn't add ${user.name}.`,
    );
    this.search.set('');
  }

  protected async remove(member: GroupMember): Promise<void> {
    const confirmed = await this.actions.confirm(
      'Remove member',
      `Remove ${member.name ?? 'this member'} from ${this.group().name}?`,
      'Remove',
    );
    if (confirmed)
      await this.attempt(() => this.actions.removeMember(member), "Couldn't remove the member.");
  }

  protected async makeOwner(member: GroupMember): Promise<void> {
    const confirmed = await this.actions.confirm(
      'Change owner',
      `Make ${member.name ?? 'this member'} the owner of ${this.group().name}?`,
      'Make owner',
    );
    if (confirmed)
      await this.attempt(() => this.actions.makeOwner(member), "Couldn't change the owner.");
  }

  private async attempt(work: () => Promise<unknown>, fallback: string): Promise<void> {
    this.busy.set(true);
    this.error.set(null);
    try {
      await work();
      this.membersResource.reload();
      this.changed.emit();
    } catch (err) {
      this.error.set(describeApiError(err, fallback));
    } finally {
      this.busy.set(false);
    }
  }
}
