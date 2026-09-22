import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { WardsManagementStore } from '../wards-management.store';
import { WardsList } from './wards-list';

describe('WardsList', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WardsList],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), WardsManagementStore],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(WardsList);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
