import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { GroupPage } from './group-page';

describe('GroupPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('waits for the profile before loading the group', () => {
    const fixture = TestBed.createComponent(GroupPage);
    fixture.componentRef.setInput('groupId', 'g1');
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Loading');
  });
});
