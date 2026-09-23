import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { TimelinePage } from './timeline-page';

describe('TimelinePage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TimelinePage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('shows the three tabs', () => {
    const fixture = TestBed.createComponent(TimelinePage);
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('All');
    expect(text).toContain('Following');
    expect(text).toContain('Popular');
  });
});
