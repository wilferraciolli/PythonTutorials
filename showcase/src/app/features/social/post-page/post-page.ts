import { DatePipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { Component, computed, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { Router, RouterLink } from '@angular/router';
import {
  ApiClientService,
  CollectionEnvelope,
  SingleEnvelope,
} from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { CurrentUserStore } from '../../../core/user/current-user.store';
import { SocialActions } from '../social-actions';
import { Group, Post, PostComment, threadComments } from '../social.models';

const MAX_INDENT = 6;

// One post with its threaded comments. Replying opens a box under that comment.
@Component({
  selector: 'app-post-page',
  imports: [
    DatePipe,
    RouterLink,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './post-page.html',
  styleUrl: './post-page.scss',
})
export class PostPage {
  // Bound from `:groupId` / `:postId` via withComponentInputBinding().
  readonly groupId = input.required<string>();
  readonly postId = input.required<string>();

  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);
  private readonly actions = inject(SocialActions);
  private readonly router = inject(Router);

  // Group first (its visibility decides whether the post exists for us),
  // then the post under the group's `posts` link, then its comments link.
  private readonly groupResource = httpResource<SingleEnvelope<'group', Group>>(() => {
    const groups = this.api.resolve(this.currentUser.link('groups'));
    return groups ? `${groups}/${this.groupId()}` : undefined;
  });
  protected readonly group = computed(() => this.groupResource.value()?._data['group']);

  private readonly postResource = httpResource<SingleEnvelope<'post', Post>>(() => {
    const posts = this.api.resolve(this.group()?.links['posts']);
    return posts ? `${posts}/${this.postId()}` : undefined;
  });
  protected readonly post = computed(() => this.postResource.value()?._data['post']);

  private readonly commentsResource = httpResource<CollectionEnvelope<'comments', PostComment>>(
    () => this.api.resolve(this.post()?.links['comments']),
  );
  protected readonly thread = computed(() =>
    threadComments(this.commentsResource.value()?._data['comments'] ?? []),
  );

  protected readonly loadError = computed(() => {
    const error = this.groupResource.error() ?? this.postResource.error();
    return error ? describeApiError(error, "Couldn't load this post.") : null;
  });

  protected readonly draft = signal('');
  protected readonly replyTo = signal<string | null>(null);
  protected readonly replyDraft = signal('');
  protected readonly busy = signal(false);
  protected readonly actionError = signal<string | null>(null);

  protected indent(depth: number): string {
    return `${Math.min(depth, MAX_INDENT) * 1.25}rem`;
  }

  protected canLike(item: Post | PostComment): boolean {
    return !!(item.links['like'] || item.links['unlike']);
  }

  protected async togglePostLike(post: Post): Promise<void> {
    await this.attempt(() => this.actions.togglePostLike(post), "Couldn't update the like.");
  }

  protected async toggleCommentLike(comment: PostComment): Promise<void> {
    await this.attempt(() => this.actions.toggleCommentLike(comment), "Couldn't update the like.");
  }

  protected async comment(post: Post): Promise<void> {
    if (!this.draft().trim()) return;
    await this.attempt(async () => {
      await this.actions.addComment(post, this.draft().trim());
      this.draft.set('');
    }, "Couldn't add the comment.");
  }

  protected startReply(comment: PostComment): void {
    this.replyTo.set(comment.id);
    this.replyDraft.set('');
  }

  protected async reply(post: Post, parent: PostComment): Promise<void> {
    if (!this.replyDraft().trim()) return;
    await this.attempt(async () => {
      await this.actions.addComment(post, this.replyDraft().trim(), parent);
      this.replyTo.set(null);
    }, "Couldn't add the reply.");
  }

  protected async deleteComment(comment: PostComment): Promise<void> {
    if (!(await this.actions.confirm('Delete comment', 'Delete this comment? Replies to it stay.')))
      return;
    await this.attempt(() => this.actions.deleteComment(comment), "Couldn't delete the comment.");
  }

  protected async deletePost(post: Post): Promise<void> {
    if (!(await this.actions.confirm('Delete post', `Delete "${post.title}"?`))) return;
    this.busy.set(true);
    try {
      await this.actions.deletePost(post);
      await this.router.navigate(['/groups', post.groupId]);
    } catch (err) {
      this.actionError.set(describeApiError(err, "Couldn't delete the post."));
    } finally {
      this.busy.set(false);
    }
  }

  private async attempt(work: () => Promise<unknown>, fallback: string): Promise<void> {
    this.busy.set(true);
    this.actionError.set(null);
    try {
      await work();
      this.postResource.reload();
      this.commentsResource.reload();
    } catch (err) {
      this.actionError.set(describeApiError(err, fallback));
    } finally {
      this.busy.set(false);
    }
  }
}
