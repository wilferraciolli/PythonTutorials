import { TestBed } from '@angular/core/testing';

import { WorkersAiPage } from './workers-ai-page';

describe('WorkersAiPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkersAiPage],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(WorkersAiPage);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
