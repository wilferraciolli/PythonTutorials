import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_ORIGIN } from '@wiliamferraciolli/ngx-api-client';

import { Group } from '../../social.models';
import { GroupFollowers } from './group-followers';

describe('GroupFollowers', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupFollowers],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_ORIGIN, useValue: 'http://api' },
      ],
    }).compileComponents();
  });

  it('lists followers from the group followers link', async () => {
    const fixture = TestBed.createComponent(GroupFollowers);
    fixture.componentRef.setInput('group', {
      links: { followers: { href: '/api/groups/g1/followers' } },
    } as unknown as Group);
    fixture.detectChanges();

    TestBed.inject(HttpTestingController)
      .expectOne('http://api/api/groups/g1/followers')
      .flush({
        _data: {
          followers: [{ userId: 'u1', name: 'Olive', created_date: '2026-01-01T00:00:00Z' }],
        },
      });
    await fixture.whenStable();
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Olive');
  });
});
