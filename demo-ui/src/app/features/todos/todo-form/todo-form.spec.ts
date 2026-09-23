import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { TodosStore } from '../todos.store';
import { TodoForm } from './todo-form';

describe('TodoForm', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TodoForm],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), TodosStore],
    }).compileComponents();
  });

  it('renders the "new todo" heading with no id input bound', () => {
    const fixture = TestBed.createComponent(TodoForm);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.TodoForm-title')?.textContent).toContain('New todo');
  });
});
