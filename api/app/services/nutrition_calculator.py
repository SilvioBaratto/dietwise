"""Deterministic BMR/TDEE/calorie-target math for diet generation.

Computed in Python and handed to BAML as hard numbers, instead of asking the
LLM to derive BMR/TDEE inline from prose — see diet.baml's use of
compute_calorie_target() output.
"""

from dataclasses import dataclass

# This app's diet-plan users are here for a workout-integrated meal plan, so
# "moderately active" (exercise ~3-5x/week) is the baseline assumption absent
# a structured training-frequency field on UserSettings.
_ACTIVITY_FACTOR = 1.55

# Never target a day below resting BMR; cap the deficit at 25% under
# maintenance for a sustainable rate of loss (~0.5-1kg/week for most adults).
_MIN_DEFICIT_FACTOR = 0.75
_MAX_SURPLUS_FACTOR = 1.20


@dataclass(frozen=True)
class CalorieTarget:
    bmr: int
    tdee: int
    floor: int
    ceiling: int


def compute_calorie_target(
    weight_kg: float,
    height_cm: float,
    age: int | None,
    sex: str | None,
) -> CalorieTarget:
    """Mifflin-St Jeor BMR -> TDEE -> a safe daily-calorie floor/ceiling.

    Missing age defaults to 30, missing sex averages the male/female
    constant — the same defaults the prompt previously assumed in prose.
    """
    resolved_age = age if age is not None else 30
    if sex == "M":
        sex_constant = 5
    elif sex == "F":
        sex_constant = -161
    else:
        sex_constant = -78  # midpoint of the male/female constants

    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * resolved_age + sex_constant
    tdee = bmr * _ACTIVITY_FACTOR

    floor = max(bmr, tdee * _MIN_DEFICIT_FACTOR)
    ceiling = tdee * _MAX_SURPLUS_FACTOR

    return CalorieTarget(
        bmr=round(bmr),
        tdee=round(tdee),
        floor=round(floor),
        ceiling=round(ceiling),
    )
