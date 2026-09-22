import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { WardsManagementShell } from './wards-management-shell';

describe('WardsManagementShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WardsManagementShell],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(WardsManagementShell);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
