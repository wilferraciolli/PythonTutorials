import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { DoctorsManagementShell } from './doctors-management-shell';

describe('DoctorsManagementShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DoctorsManagementShell],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(DoctorsManagementShell);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
