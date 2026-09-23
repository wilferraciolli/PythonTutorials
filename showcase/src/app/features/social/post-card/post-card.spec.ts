import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Post } from '../social.models';
import { PostCard } from './post-card';

const post: Post = {
  id: 'p1',
  groupId: 'g1',
  groupName: 'News',
  authorId: null,
  authorName: 'System',
  title: 'Welcome',
  body: 'Hello',
  isDeleted: false,
  likeCount: 2,
  commentCount: 3,
  likedByMe: false,
  created_date: '2026-01-01T00:00:00Z',
  updated_date: '2026-01-01T00:00:00Z',
  links: {},
};

describe('PostCard', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PostCard],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('shows the post and disables like without a like link', () => {
    const fixture = TestBed.createComponent(PostCard);
    fixture.componentRef.setInput('post', post);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;

    expect(el.textContent).toContain('Welcome');
    expect(el.textContent).toContain('System');
    expect(el.querySelector('button')?.disabled).toBe(true);
  });
});
