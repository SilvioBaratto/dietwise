import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { WeeklyComponent } from './weekly.component';

describe('WeeklyComponent', () => {
  let component: WeeklyComponent;
  let fixture: ComponentFixture<WeeklyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WeeklyComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(WeeklyComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
