import { Injectable, inject } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ApiClientService, ILink } from '@wiliamferraciolli/ngx-api-client';

import { firstValueFrom } from 'rxjs';

import { ConfirmDialog } from '../../shared/confirm-dialog/confirm-dialog';
import { Group, GroupVisibility, Post, PostComment } from './social.models';

// Every write in the social feature, each one following a link the API
// handed out (never a hand-built URL). Callers reload their own resources
// afterwards.
@Injectable({ providedIn: 'root' })
export class SocialActions {
  private readonly api = inject(ApiClientService);
  private readonly dialog = inject(MatDialog);

  /** Ask before a destructive action; resolves true when confirmed. */
  async confirm(title: string, message: string, confirmLabel = 'Delete'): Promise<boolean> {
    const ref = this.dialog.open(ConfirmDialog, {
      data: { title, message, confirmLabel, tone: 'danger' },
    });
    return (await firstValueFrom(ref.afterClosed())) === true;
  }

  private require(link: ILink | undefined, action: string): string {
    return this.api.requireLink(link, `You can't ${action}.`);
  }

  createGroup(
    createLink: ILink | undefined,
    payload: { name: string; description: string; visibility: GroupVisibility },
  ): Promise<Group> {
    return this.api.post('group', this.require(createLink, 'create a group'), payload);
  }

  // join / leave / follow / unfollow: PUT or DELETE on the link of that name
  groupAction(group: Group, name: 'join' | 'leave' | 'follow' | 'unfollow'): Promise<unknown> {
    const url = this.require(group.links[name], name);
    return name === 'join' || name === 'follow'
      ? this.api.put('group', url, {})
      : this.api.delete(url);
  }

  deleteGroup(group: Group): Promise<void> {
    return this.api.delete(this.require(group.links['delete'], 'delete this group'));
  }

  createPost(group: Group, payload: { title: string; body: string }): Promise<Post> {
    return this.api.post('post', this.require(group.links['createPost'], 'post here'), payload);
  }

  deletePost(post: Post): Promise<void> {
    return this.api.delete(this.require(post.links['delete'], 'delete this post'));
  }

  togglePostLike(post: Post): Promise<unknown> {
    return post.likedByMe
      ? this.api.delete(this.require(post.links['unlike'], 'unlike this post'))
      : this.api.put('post', this.require(post.links['like'], 'like this post'), {});
  }

  addComment(post: Post, body: string, parent?: PostComment): Promise<PostComment> {
    const link = parent ? parent.links['reply'] : post.links['addComment'];
    return this.api.post('comment', this.require(link, 'comment here'), {
      body,
      parentCommentId: parent?.id ?? null,
    });
  }

  deleteComment(comment: PostComment): Promise<void> {
    return this.api.delete(this.require(comment.links['delete'], 'delete this comment'));
  }

  toggleCommentLike(comment: PostComment): Promise<unknown> {
    return comment.likedByMe
      ? this.api.delete(this.require(comment.links['unlike'], 'unlike this comment'))
      : this.api.put('comment', this.require(comment.links['like'], 'like this comment'), {});
  }
}
