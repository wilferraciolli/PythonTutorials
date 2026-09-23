import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { PostComment, threadComments } from '../social.models';
import { PostPage } from './post-page';

function comment(id: string, parentCommentId: string | null): PostComment {
  return {
    id,
    postId: 'p1',
    parentCommentId,
    authorId: 'u1',
    authorName: 'Sam',
    body: id,
    isDeleted: false,
    likeCount: 0,
    likedByMe: false,
    created_date: '2026-01-01T00:00:00Z',
    links: {},
  };
}

describe('threadComments', () => {
  it('puts each reply straight under its parent with its depth', () => {
    const flat = [comment('a', null), comment('b', null), comment('a1', 'a'), comment('a1x', 'a1')];
    expect(threadComments(flat).map((t) => `${t.comment.id}:${t.depth}`)).toEqual([
      'a:0',
      'a1:1',
      'a1x:2',
      'b:0',
    ]);
  });

  it('keeps a reply whose parent is missing, at the top level', () => {
    expect(threadComments([comment('orphan', 'gone')]).map((t) => t.depth)).toEqual([0]);
  });
});

describe('PostPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PostPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(PostPage);
    fixture.componentRef.setInput('groupId', 'g1');
    fixture.componentRef.setInput('postId', 'p1');
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Loading');
  });
});
