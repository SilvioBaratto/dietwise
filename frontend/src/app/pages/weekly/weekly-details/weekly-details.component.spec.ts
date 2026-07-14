import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { WeeklyDetailsComponent } from './weekly-details.component';

describe('WeeklyDetailsComponent', () => {
  let component: WeeklyDetailsComponent;
  let fixture: ComponentFixture<WeeklyDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WeeklyDetailsComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(WeeklyDetailsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
