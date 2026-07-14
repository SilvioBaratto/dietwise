import pytest

from app.services.package_sizing import round_to_purchasable
from baml_client.types import Ingrediente, UnitaMisura


def _round_one(nome: str, quantita: float, unita: UnitaMisura) -> Ingrediente:
    (result,) = round_to_purchasable(
        [Ingrediente(nome=nome, quantita=quantita, unita=unita)]
    )
    return result


@pytest.mark.unit
@pytest.mark.parametrize(
    ("nome", "quantita", "unita", "expected_quantita", "expected_unita"),
    [
        ("Miele", 15, UnitaMisura.GR, 250, UnitaMisura.GR),
        ("Parmigiano", 10, UnitaMisura.GR, 100, UnitaMisura.GR),
        ("Semi di chia", 20, UnitaMisura.GR, 250, UnitaMisura.GR),
        ("Semi di lino", 20, UnitaMisura.GR, 200, UnitaMisura.GR),
        ("Tonno al naturale", 300, UnitaMisura.GR, 320, UnitaMisura.GR),
        ("Burro di arachidi", 15, UnitaMisura.GR, 220, UnitaMisura.GR),
    ],
)
def test_rounds_up_to_real_package_size(
    nome, quantita, unita, expected_quantita, expected_unita
):
    result = _round_one(nome, quantita, unita)

    assert result.quantita == expected_quantita
    assert result.unita == expected_unita


@pytest.mark.unit
def test_kg_input_normalizes_to_grams_before_rounding():
    result = _round_one("Pasta integrale", 0.3, UnitaMisura.KG)

    assert result.unita == UnitaMisura.GR
    assert result.quantita == 500  # 300g -> one 500g package


@pytest.mark.unit
def test_pz_quantities_are_always_ceiled_to_whole_pieces():
    result = _round_one("Banana", 0.5, UnitaMisura.PZ)

    assert result.quantita == 1
    assert result.unita == UnitaMisura.PZ


@pytest.mark.unit
def test_already_clean_multiple_is_left_unchanged():
    result = _round_one("Olio extravergine d'oliva", 500, UnitaMisura.ML)

    assert result.quantita == 500
    assert result.unita == UnitaMisura.ML


@pytest.mark.unit
@pytest.mark.parametrize(
    "nome", ["Zucchine", "Pomodori / Pomodorini", "Petto di pollo"]
)
def test_fresh_produce_and_meat_are_never_rounded(nome):
    result = _round_one(nome, 500, UnitaMisura.GR)

    assert result.quantita == 500
    assert result.unita == UnitaMisura.GR


@pytest.mark.unit
def test_unmatched_ingredient_name_passes_through_untouched():
    result = _round_one("Qualcosa di sconosciuto", 37, UnitaMisura.GR)

    assert result.quantita == 37
    assert result.unita == UnitaMisura.GR


@pytest.mark.unit
@pytest.mark.parametrize(
    ("unita", "expected_unita"),
    [(UnitaMisura.GR, UnitaMisura.GR), (UnitaMisura.ML, UnitaMisura.ML)],
)
def test_dual_family_rule_rounds_under_whichever_unit_it_gets(unita, expected_unita):
    # The LLM reports maple syrup as weight or volume inconsistently across
    # calls — this rule accepts either instead of guessing/dropping it.
    result = _round_one("Sciroppo d'acero", 10, unita)

    assert result.quantita == 250
    assert result.unita == expected_unita


@pytest.mark.unit
def test_single_family_rule_does_not_guess_on_mismatched_unit():
    # Olio EVO is an ML-only rule; if the LLM mislabels it as GR, don't
    # silently reinterpret grams as milliliters.
    result = _round_one("Olio extravergine d'oliva", 500, UnitaMisura.GR)

    assert result.quantita == 500
    assert result.unita == UnitaMisura.GR


@pytest.mark.unit
def test_zero_and_negative_quantities_round_to_zero_not_a_full_package():
    result = _round_one("Miele", 0, UnitaMisura.GR)

    assert result.quantita == 0
