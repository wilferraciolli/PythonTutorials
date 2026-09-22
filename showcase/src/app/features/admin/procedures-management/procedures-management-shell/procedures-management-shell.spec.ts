import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { ProceduresManagementShell } from './procedures-management-shell';

describe('ProceduresManagementShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProceduresManagementShell],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ProceduresManagementShell);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
