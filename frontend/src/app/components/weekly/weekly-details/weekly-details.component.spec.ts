import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WeeklyDetailsComponent } from './weekly-details.component';

describe('WeeklyDetailsComponent', () => {
  let component: WeeklyDetailsComponent;
  let fixture: ComponentFixture<WeeklyDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WeeklyDetailsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WeeklyDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
