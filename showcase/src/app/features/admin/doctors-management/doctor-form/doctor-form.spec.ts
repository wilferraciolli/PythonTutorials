import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { DoctorsManagementStore } from '../doctors-management.store';
import { DoctorForm } from './doctor-form';

describe('DoctorForm', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DoctorForm],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        DoctorsManagementStore,
      ],
    }).compileComponents();
  });

  it('creates in create mode (no id)', () => {
    const fixture = TestBed.createComponent(DoctorForm);
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('creates in edit mode (id set)', () => {
    const fixture = TestBed.createComponent(DoctorForm);
    fixture.componentRef.setInput('id', 'doc_1');
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });
});
