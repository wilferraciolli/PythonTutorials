import { httpResource } from '@angular/common/http';
import { Component, computed, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatMenuModule } from '@angular/material/menu';
import { MatTabsModule } from '@angular/material/tabs';
import { Router, RouterLink } from '@angular/router';
import {
  ApiClientService,
  CollectionEnvelope,
  SingleEnvelope,
} from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { CurrentUserStore } from '../../../core/user/current-user.store';
import { MediaPicker } from '../media-picker/media-picker';
import { PostCard } from '../post-card/post-card';
import { GroupFollowers } from './group-followers/group-followers';
import { GroupMembers } from './group-members/group-members';
import { SocialActions } from '../social-actions';
import { Group, GroupVisibility, MediaSelection, Post } from '../social.models';

// One group: its details, join/leave/follow buttons (each shown only when
// the API hands out that link), a new-post form for members, and its posts.
@Component({
  selector: 'app-group-page',
  imports: [
    RouterLink,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatMenuModule,
    MatTabsModule,
    MediaPicker,
    PostCard,
    GroupMembers,
    GroupFollowers,
  ],
  templateUrl: './group-page.html',
  styleUrl: './group-page.scss',
})
export class GroupPage {
  // Bound from the `:groupId` route param via withComponentInputBinding().
  readonly groupId = input.required<string>();

  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);
  private readonly actions = inject(SocialActions);
  private readonly router = inject(Router);

  // A deep link only has the id, so the group's URL is the profile's
  // `groups` collection link plus the id (the API's own `self` shape).
  private readonly groupResource = httpResource<SingleEnvelope<'group', Group>>(() => {
    const groups = this.api.resolve(this.currentUser.link('groups'));
    return groups ? `${groups}/${this.groupId()}` : undefined;
  });
  protected readonly group = computed(() => this.groupResource.value()?._data['group']);
  protected readonly groupError = computed(() => {
    const error = this.groupResource.error();
    return error ? describeApiError(error, "Couldn't load this group.") : null;
  });

  private readonly postsResource = httpResource<CollectionEnvelope<'posts', Post>>(() =>
    this.api.resolve(this.group()?.links['posts']),
  );
  protected readonly posts = computed(() => this.postsResource.value()?._data['posts'] ?? []);
  protected readonly postsLoading = computed(() => this.postsResource.isLoading());

  protected readonly busy = signal(false);
  protected readonly actionError = signal<string | null>(null);

  protected readonly section = signal<'posts' | 'members' | 'followers'>('posts');

  protected readonly editing = signal(false);
  protected readonly editName = signal('');
  protected readonly editDescription = signal('');
  protected readonly editVisibility = signal<GroupVisibility>('PUBLIC');

  protected readonly title = signal('');
  protected readonly body = signal('');
  protected readonly media = signal<MediaSelection | null>(null);
  protected readonly pickingMedia = signal(false);

  protected async run(name: 'join' | 'leave' | 'follow' | 'unfollow'): Promise<void> {
    const group = this.group();
    if (!group) return;
    await this.attempt(async () => {
      await this.actions.groupAction(group, name);
      this.groupResource.reload();
      this.postsResource.reload();
    }, `Couldn't ${name} the group.`);
  }

  protected async post(): Promise<void> {
    const group = this.group();
    if (!group || !this.title().trim() || !this.body().trim()) return;
    await this.attempt(async () => {
      await this.actions.createPost(group, {
        title: this.title().trim(),
        body: this.body().trim(),
        media: this.media()?.ref ?? null,
      });
      this.title.set('');
      this.body.set('');
      this.media.set(null);
      this.postsResource.reload();
    }, "Couldn't create the post.");
  }

  protected async deleteGroup(): Promise<void> {
    const group = this.group();
    if (!group) return;
    const confirmed = await this.actions.confirm(
      'Delete group',
      `Delete "${group.name}" with all its posts and comments? This can't be undone.`,
    );
    if (!confirmed) return;
    await this.attempt(async () => {
      await this.actions.deleteGroup(group);
      await this.router.navigate(['/groups']);
    }, "Couldn't delete the group.");
  }

  protected startEdit(group: Group): void {
    this.editName.set(group.name);
    this.editDescription.set(group.description ?? '');
    this.editVisibility.set(group.visibility);
    this.editing.set(true);
  }

  protected setEditVisibility(value: string): void {
    if (value === 'PUBLIC' || value === 'PRIVATE') this.editVisibility.set(value);
  }

  protected async saveEdit(group: Group): Promise<void> {
    await this.attempt(async () => {
      await this.actions.updateGroup(group, {
        name: this.editName().trim(),
        description: this.editDescription().trim(),
        visibility: this.editVisibility(),
      });
      this.editing.set(false);
      this.groupResource.reload();
    }, "Couldn't save the group.");
  }

  protected reloadGroup(): void {
    this.groupResource.reload();
  }

  protected reloadPosts(): void {
    this.postsResource.reload();
  }

  private async attempt(work: () => Promise<void>, fallback: string): Promise<void> {
    this.busy.set(true);
    this.actionError.set(null);
    try {
      await work();
    } catch (err) {
      this.actionError.set(describeApiError(err, fallback));
    } finally {
      this.busy.set(false);
    }
  }
}
