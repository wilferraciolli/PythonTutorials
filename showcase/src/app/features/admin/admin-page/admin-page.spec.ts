import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AdminPage } from './admin-page';

describe('AdminPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(AdminPage);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Admin');
  });
});
