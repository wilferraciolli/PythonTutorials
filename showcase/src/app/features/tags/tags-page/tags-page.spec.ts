import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { TagsPage } from './tags-page';

describe('TagsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TagsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(TagsPage);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
