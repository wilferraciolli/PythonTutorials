import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_ORIGIN } from '@wiliamferraciolli/ngx-api-client';

import { CurrentUserStore } from '../../../core/user/current-user.store';
import { PeoplePicker } from './people-picker';

describe('PeoplePicker', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PeoplePicker],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_ORIGIN, useValue: '' },
        { provide: CurrentUserStore, useValue: { link: () => ({ href: '/api/users/search' }) } },
      ],
    }).compileComponents();
  });

  function render(people: { id: string; value: string }[]) {
    const fixture = TestBed.createComponent(PeoplePicker);
    fixture.componentRef.setInput('people', people);
    fixture.detectChanges();
    return fixture;
  }

  it('shows each tagged person as a removable chip', () => {
    const fixture = render([
      { id: 'u1', value: 'Olive Branch' },
      { id: 'u2', value: 'Sam Rivera' },
    ]);
    const el = fixture.nativeElement as HTMLElement;
    const chips = Array.from(el.querySelectorAll('mat-chip-row')).map((c) => c.textContent?.trim());
    expect(chips[0]).toContain('Olive Branch');
    expect(chips[1]).toContain('Sam Rivera');

    el.querySelector<HTMLButtonElement>('[aria-label="Remove Olive Branch"]')!.click();
    fixture.detectChanges();
    expect(fixture.componentInstance.people()).toEqual([{ id: 'u2', value: 'Sam Rivera' }]);
  });

  it('searches once two characters are typed, leaving out people already tagged', async () => {
    const fixture = render([{ id: 'u1', value: 'Olive Branch' }]);
    const input = (fixture.nativeElement as HTMLElement).querySelector('input')!;
    input.value = 'o';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    TestBed.inject(HttpTestingController).expectNone(() => true);

    input.value = 'ol';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    TestBed.tick();
    TestBed.inject(HttpTestingController)
      .expectOne('/api/users/search?q=ol')
      .flush({
        _data: {
          users: [
            { id: 'u1', name: 'Olive Branch', email: 'o@x.io' },
            { id: 'u3', name: 'Oliver Twist', email: 't@x.io' },
          ],
        },
      });
    await fixture.whenStable();
    const matches = (fixture.componentInstance as unknown as { matches: () => { id: string }[] })
      .matches()
      .map((u) => u.id);
    expect(matches).toEqual(['u3']);
  });
});
