import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { GroupsPage } from './groups-page';

describe('GroupsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupsPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('opens the create form', () => {
    const fixture = TestBed.createComponent(GroupsPage);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const newGroup = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('New group'),
    );
    newGroup!.click();
    fixture.detectChanges();
    expect(el.textContent).toContain('Who can see it');
  });
});
