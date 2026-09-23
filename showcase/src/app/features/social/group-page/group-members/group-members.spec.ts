import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_ORIGIN } from '@wiliamferraciolli/ngx-api-client';

import { Group } from '../../social.models';
import { GroupMembers } from './group-members';

const group: Group = {
  id: 'g1',
  name: 'Cyclists',
  description: null,
  visibility: 'PRIVATE',
  ownerId: 'u1',
  memberCount: 2,
  followerCount: 2,
  isOwner: true,
  isMember: true,
  isFollowing: true,
  created_date: '2026-01-01T00:00:00Z',
  links: { members: { href: '/api/groups/g1/members' } },
};

describe('GroupMembers', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupMembers],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_ORIGIN, useValue: 'http://api' },
      ],
    }).compileComponents();
  });

  it('lists members with an owner badge and only the actions their links allow', async () => {
    const fixture = TestBed.createComponent(GroupMembers);
    fixture.componentRef.setInput('group', group);
    fixture.detectChanges();

    TestBed.inject(HttpTestingController)
      .expectOne('http://api/api/groups/g1/members')
      .flush({
        _data: {
          members: [
            {
              userId: 'u1',
              name: 'Olive',
              isOwner: true,
              joined_date: '2026-01-01T00:00:00Z',
              links: {},
            },
            {
              userId: 'u2',
              name: 'Sam',
              isOwner: false,
              joined_date: '2026-01-02T00:00:00Z',
              links: { remove: { href: '/x' }, makeOwner: { href: '/y' } },
            },
          ],
        },
      });
    await fixture.whenStable();
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Olive');
    expect(text).toContain('Owner');
    expect(text).toContain('Make owner');
    expect(text).toContain('Remove');
    expect(text).not.toContain('Add someone'); // no addMember link
  });
});
