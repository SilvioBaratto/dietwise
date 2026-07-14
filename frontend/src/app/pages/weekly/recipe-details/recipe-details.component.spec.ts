import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { RecipeDetailsComponent } from './recipe-details.component';

describe('RecipeDetailsComponent', () => {
  let component: RecipeDetailsComponent;
  let fixture: ComponentFixture<RecipeDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RecipeDetailsComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RecipeDetailsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
