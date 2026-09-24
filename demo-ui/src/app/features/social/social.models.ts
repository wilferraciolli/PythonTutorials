import { ILink } from '@wiliamferraciolli/ngx-api-client';

// Shapes returned by fastapi-ai's social endpoints (docs/social-groups.md).
// Every action is a link: a missing link means the caller may not do it.

export type GroupVisibility = 'PUBLIC' | 'PRIVATE';
export type TimelineType = 'ALL' | 'FOLLOWING' | 'POPULAR';

export interface Group {
  id: string;
  name: string;
  description: string | null;
  visibility: GroupVisibility;
  ownerId: string | null;
  memberCount: number;
  followerCount: number;
  isOwner: boolean;
  isMember: boolean;
  isFollowing: boolean;
  created_date: string;
  links: Record<string, ILink>;
}

export type MediaType = 'UNSPLASH' | 'GIPHY' | 'YOUTUBE';

/** What gets sent to attach media: the server looks up the URL and credits from the id. */
export interface MediaRef {
  type: MediaType;
  id: string;
}

/** A post's media. `url` is null for YouTube: the embed is built from the 11-character id. */
export interface PostMedia extends MediaRef {
  url: string | null;
  /** Alt text (Unsplash's description of the photo). */
  title?: string | null;
  authorName: string | null;
  authorUrl: string | null;
}

/** One search result: an Unsplash photo (via our API) or a Giphy GIF (from Giphy directly). */
export interface MediaSearchResult extends MediaRef {
  title: string | null;
  previewUrl: string;
  url: string;
  authorName: string | null;
  authorUrl: string | null;
}

/** A picked item: the ref to send, plus something to show before saving. */
export interface MediaSelection {
  ref: MediaRef;
  previewUrl: string;
  label: string;
}

export const YOUTUBE_ID = /^[A-Za-z0-9_-]{11}$/;

/**
 * The 11-character video id from what someone pasted: the bare id, or a
 * youtube.com/watch?v=, youtu.be/, /shorts/ or /embed/ link. Null if none found.
 */
export function youtubeId(text: string): string | null {
  const value = text.trim();
  if (YOUTUBE_ID.test(value)) return value;
  try {
    const url = new URL(value.includes('://') ? value : `https://${value}`);
    const host = url.hostname.replace(/^(www\.|m\.)/, '');
    const candidate =
      host === 'youtu.be'
        ? url.pathname.slice(1)
        : host.endsWith('youtube.com') || host.endsWith('youtube-nocookie.com')
          ? (url.searchParams.get('v') ?? url.pathname.split('/')[2] ?? '')
          : '';
    return YOUTUBE_ID.test(candidate) ? candidate : null;
  } catch {
    return null;
  }
}

export interface Post {
  id: string;
  groupId: string;
  groupName: string;
  authorId: string | null;
  authorName: string | null;
  title: string;
  body: string;
  media?: PostMedia | null;
  /** Ids of the people tagged in the post; names are in the response's _metadata.taggedUserIds. */
  taggedUserIds?: string[];
  isDeleted: boolean;
  likeCount: number;
  commentCount: number;
  likedByMe: boolean;
  created_date: string;
  updated_date: string;
  links: Record<string, ILink>;
}

export interface PostComment {
  id: string;
  postId: string;
  parentCommentId: string | null;
  authorId: string | null;
  authorName: string | null;
  body: string;
  isDeleted: boolean;
  likeCount: number;
  likedByMe: boolean;
  created_date: string;
  links: Record<string, ILink>;
}

export interface GroupMember {
  userId: string;
  name: string | null;
  isOwner: boolean;
  joined_date: string;
  links: Record<string, ILink>;
}

export interface GroupFollower {
  userId: string;
  name: string | null;
  created_date: string;
}

/** The most people a post can tag (the API's limit too). */
export const MAX_TAGGED_PEOPLE = 20;

/**
 * "With Olive", "With Olive and Sam", "With Olive, Sam and Ana",
 * "With Olive, Sam and 3 others". Empty for nobody.
 */
export function formatPeople(names: string[]): string {
  if (names.length === 0) return '';
  if (names.length === 1) return `With ${names[0]}`;
  if (names.length <= 3) return `With ${names.slice(0, -1).join(', ')} and ${names.at(-1)}`;
  const others = names.length - 2;
  return `With ${names[0]}, ${names[1]} and ${others} others`;
}

/** The tagged people's names, resolved from the response metadata (ids it can't name are skipped). */
export function taggedNames(post: Post, people: { id: string; value: string }[]): string[] {
  const names = new Map(people.map((person) => [person.id, person.value]));
  return (post.taggedUserIds ?? []).flatMap((id) => (names.has(id) ? [names.get(id)!] : []));
}

export interface UserSummary {
  id: string;
  name: string;
  email: string;
}

export interface ThreadedComment {
  comment: PostComment;
  depth: number;
}

/**
 * The API returns comments flat (oldest first) with `parentCommentId`;
 * this orders them as a thread (each reply straight under its parent) and
 * works out how far to indent each one.
 */
export function threadComments(comments: PostComment[]): ThreadedComment[] {
  const children = new Map<string | null, PostComment[]>();
  const ids = new Set(comments.map((c) => c.id));
  for (const comment of comments) {
    // A reply whose parent is missing is shown at the top level rather than lost.
    const parent =
      comment.parentCommentId && ids.has(comment.parentCommentId) ? comment.parentCommentId : null;
    children.set(parent, [...(children.get(parent) ?? []), comment]);
  }

  const thread: ThreadedComment[] = [];
  const visit = (parent: string | null, depth: number) => {
    for (const comment of children.get(parent) ?? []) {
      thread.push({ comment, depth });
      visit(comment.id, depth + 1);
    }
  };
  visit(null, 0);
  return thread;
}
