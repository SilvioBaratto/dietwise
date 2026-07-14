import pytest

from app.services.nutrition_calculator import compute_calorie_target


@pytest.mark.unit
def test_compute_calorie_target_male_profile():
    target = compute_calorie_target(weight_kg=90.0, height_cm=178.0, age=38, sex="M")

    assert target.bmr == 1828
    assert target.tdee == 2833
    assert target.floor == 2124
    assert target.ceiling == 3399


@pytest.mark.unit
def test_compute_calorie_target_female_profile():
    target = compute_calorie_target(weight_kg=65.0, height_cm=165.0, age=30, sex="F")

    expected_bmr = round(10 * 65.0 + 6.25 * 165.0 - 5 * 30 - 161)
    assert target.bmr == expected_bmr


@pytest.mark.unit
def test_compute_calorie_target_defaults_missing_age_and_sex():
    with_defaults = compute_calorie_target(
        weight_kg=80.0, height_cm=175.0, age=None, sex=None
    )
    explicit = compute_calorie_target(weight_kg=80.0, height_cm=175.0, age=30, sex=None)

    assert with_defaults == explicit


@pytest.mark.unit
def test_compute_calorie_target_missing_sex_uses_midpoint_constant():
    male = compute_calorie_target(80.0, 175.0, 28, "M")
    female = compute_calorie_target(80.0, 175.0, 28, "F")
    unspecified = compute_calorie_target(80.0, 175.0, 28, None)

    assert female.bmr < unspecified.bmr < male.bmr


@pytest.mark.unit
@pytest.mark.parametrize(
    ("weight_kg", "height_cm", "age", "sex"),
    [
        (50.0, 150.0, 20, "F"),
        (120.0, 200.0, 70, "M"),
        (80.0, 175.0, None, None),
    ],
)
def test_floor_never_drops_below_bmr(weight_kg, height_cm, age, sex):
    target = compute_calorie_target(weight_kg, height_cm, age, sex)

    assert target.floor >= target.bmr
    assert target.floor <= target.tdee <= target.ceiling
