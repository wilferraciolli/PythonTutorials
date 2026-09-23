import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AskStore } from '../ask.store';
import { AskPage } from './ask-page';

describe('AskPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AskPage],
      providers: [AskStore, provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('says the assistant is unavailable when the profile has no aiAssistant link', () => {
    const fixture = TestBed.createComponent(AskPage);
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain("The assistant isn't available on this API");
  });

  it('records an error instead of calling the API when there is no link', async () => {
    const store = TestBed.inject(AskStore);
    await store.ask('How many todos are overdue?');

    expect(store.entries()).toHaveLength(1);
    expect(store.entries()[0].error).toBeTruthy();
    expect(store.entries()[0].answer).toBeNull();
    TestBed.inject(HttpTestingController).verify();
  });

  it('ignores blank questions', async () => {
    const store = TestBed.inject(AskStore);
    await store.ask('   ');
    expect(store.entries()).toHaveLength(0);
  });
});
