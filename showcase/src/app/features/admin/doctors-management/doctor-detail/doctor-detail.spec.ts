import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { DoctorDetail } from './doctor-detail';

describe('DoctorDetail', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DoctorDetail],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(DoctorDetail);
    fixture.componentRef.setInput('id', 'doc_1');
    expect(fixture.componentInstance).toBeTruthy();
  });
});
