import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { DoctorsManagementStore } from '../doctors-management.store';
import { DoctorsList } from './doctors-list';

describe('DoctorsList', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DoctorsList],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        DoctorsManagementStore,
      ],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(DoctorsList);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
