import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { WardsManagementStore } from '../wards-management.store';
import { WardForm } from './ward-form';

describe('WardForm', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WardForm],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), WardsManagementStore],
    }).compileComponents();
  });

  it('creates in create mode (no id)', () => {
    const fixture = TestBed.createComponent(WardForm);
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('creates in edit mode (id set)', () => {
    const fixture = TestBed.createComponent(WardForm);
    fixture.componentRef.setInput('id', 'icu');
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });
});
