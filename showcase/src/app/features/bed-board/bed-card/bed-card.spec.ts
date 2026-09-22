import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { MetadataValue } from '../../../core/api/envelope';
import { I18nStore } from '../../../core/i18n/i18n.store';
import { Bed } from '../bed-board.store';
import { BedCard } from './bed-card';

const mockBed: Bed = {
  id: '1',
  bed_number: '3',
  ward_id: 'icu',
  status: 'occupied',
  status_changed_at: new Date().toISOString(),
  expected_duration_minutes: null,
  occupied_minutes: 45,
  is_overdue: false,
  overdue_minutes: 0,
  remaining_minutes: null,
  current_procedure_type_id: null,
  procedure_type: null,
  procedure_notes: null,
  duration_changed_at: null,
  links: { self: { href: '/beds/1' }, update: { href: '/beds/1/status' } },
};

const mockStatusOptions: MetadataValue[] = [
  { id: 'ready', value: 'Ready' },
  { id: 'preparing', value: 'Preparing' },
  { id: 'occupied', value: 'Occupied' },
];

describe('BedCard', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BedCard],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    // Status labels are translated locally (see BedCard.statusLabel), not
    // read from the API's English `value` — pin to en-GB so assertions
    // below stay readable regardless of the store's default locale.
    TestBed.inject(I18nStore).setLocale('en-GB');
  });

  it('renders the translated ward label, bed number, and translated status label', () => {
    const fixture = TestBed.createComponent(BedCard);
    fixture.componentRef.setInput('bed', mockBed);
    fixture.componentRef.setInput('statusOptions', mockStatusOptions);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.BedCard-title')?.textContent).toContain('3');
    expect(el.querySelector('.BedCard-ward')?.textContent).toContain('ICU');
    expect(el.querySelector('.BedCard-status-badge')?.textContent).toContain('Occupied');
  });

  it('emits statusChange with the option id when an action button is clicked', () => {
    const fixture = TestBed.createComponent(BedCard);
    fixture.componentRef.setInput('bed', mockBed);
    fixture.componentRef.setInput('statusOptions', mockStatusOptions);
    fixture.detectChanges();

    const emitted: string[] = [];
    fixture.componentInstance.statusChange.subscribe((status) => emitted.push(status));

    const el = fixture.nativeElement as HTMLElement;
    const buttons = Array.from(el.querySelectorAll<HTMLButtonElement>('.BedCard-action'));
    const readyButton = buttons.find((btn) => btn.textContent?.trim() === 'Ready');
    readyButton?.click();

    expect(emitted).toEqual(['ready']);
  });
});
