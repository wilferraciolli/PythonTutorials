import { Injectable, inject } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ApiClientService, ILink } from '@wiliamferraciolli/ngx-api-client';

import { firstValueFrom } from 'rxjs';

import { ConfirmDialog } from '../../shared/confirm-dialog/confirm-dialog';
import { Group, GroupMember, GroupVisibility, MediaRef, Post, PostComment } from './social.models';

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

  updateGroup(
    group: Group,
    payload: { name: string; description: string; visibility: GroupVisibility },
  ): Promise<Group> {
    return this.api.put('group', this.require(group.links['update'], 'edit this group'), payload);
  }

  // The API hands out `addMember` as a template (`.../members/{userId}`).
  addMember(group: Group, userId: string): Promise<Group> {
    const template = this.require(group.links['addMember'], 'add people to this group');
    return this.api.put('group', template.replace('{userId}', encodeURIComponent(userId)), {});
  }

  removeMember(member: GroupMember): Promise<void> {
    return this.api.delete(this.require(member.links['remove'], 'remove this member'));
  }

  makeOwner(member: GroupMember): Promise<Group> {
    return this.api.put('group', this.require(member.links['makeOwner'], 'change the owner'), {
      userId: member.userId,
    });
  }

  deleteGroup(group: Group): Promise<void> {
    return this.api.delete(this.require(group.links['delete'], 'delete this group'));
  }

  createPost(
    group: Group,
    payload: { title: string; body: string; media: MediaRef | null },
  ): Promise<Post> {
    return this.api.post('post', this.require(group.links['createPost'], 'post here'), payload);
  }

  // Media is changed by removing it, then adding another.
  addMedia(post: Post, media: MediaRef): Promise<Post> {
    return this.api.put('post', this.require(post.links['addMedia'], 'add media'), media);
  }

  removeMedia(post: Post): Promise<unknown> {
    return this.api.delete(this.require(post.links['removeMedia'], 'remove the media'));
  }

  updatePost(post: Post, payload: { title: string; body: string }): Promise<Post> {
    return this.api.put('post', this.require(post.links['update'], 'edit this post'), payload);
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

  updateComment(comment: PostComment, body: string): Promise<PostComment> {
    return this.api.put('comment', this.require(comment.links['update'], 'edit this comment'), {
      body,
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
