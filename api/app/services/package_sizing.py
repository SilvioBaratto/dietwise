"""Round aggregated grocery-list quantities up to real, purchasable package sizes.

GeneraListaSpesa's own prompt already asks the LLM to "arrotonda considerando
... porzioni commerciali" — it doesn't reliably do it (15g of honey isn't
something you can buy). This is the deterministic version of that instruction,
applied to the BAML output before it's persisted. Only shelf-stable/packaged
goods are matched; fresh produce, fresh meat/fish and fresh herbs are sold by
continuous weight and are left untouched.
"""

from dataclasses import dataclass
import math
import re

from baml_client.types import Ingrediente, UnitaMisura


@dataclass(frozen=True)
class _PackageRule:
    pattern: re.Pattern[str]
    # unit family ("GR" covers GR/KG input, "ML" covers ML/L input) -> smallest
    # real package size in that family's base unit. Most ingredients only
    # round under one family; a few (e.g. syrup) get reported by the LLM as
    # either weight or volume across calls, so they list both.
    increments: dict[str, float]


# Ordered most-specific to least-specific — first match wins, so e.g. "yogurt
# greco" is checked before the generic "yogurt" fallback.
_PACKAGE_RULES: list[_PackageRule] = [
    _PackageRule(re.compile(r"yogurt\s*greco"), {"GR": 150}),
    _PackageRule(re.compile(r"yogurt"), {"GR": 125}),
    _PackageRule(re.compile(r"\btonno\b"), {"GR": 80}),
    _PackageRule(re.compile(r"parmigiano|grana\s*padano|grattugiat"), {"GR": 100}),
    _PackageRule(re.compile(r"\bchia\b"), {"GR": 250}),
    _PackageRule(re.compile(r"\blino\b"), {"GR": 200}),
    _PackageRule(re.compile(r"mandorl|\bnoci\b|nocciol|pistacch|anacard|frutta\s*secca"), {"GR": 100}),
    _PackageRule(re.compile(r"gallett"), {"GR": 130}),
    _PackageRule(re.compile(r"cracker"), {"GR": 300}),
    _PackageRule(re.compile(r"fette\s*biscottat"), {"GR": 275}),
    _PackageRule(re.compile(r"burro\s*(di\s*)?arachidi"), {"GR": 220}),
    _PackageRule(re.compile(r"miele"), {"GR": 250}),
    # LLM reports this one inconsistently as weight or volume across calls —
    # round under whichever unit it actually comes back as.
    _PackageRule(re.compile(r"sciroppo\s*d.?\s*acero"), {"GR": 250, "ML": 250}),
    _PackageRule(re.compile(r"\bolio\b"), {"ML": 250}),
    _PackageRule(re.compile(r"\blatte\b(?!\s*di\s*cocco)"), {"ML": 1000}),
    _PackageRule(
        re.compile(r"pasta|\briso\b|farro|quinoa|\borzo\b|avena|farina"),
        {"GR": 500},
    ),
    _PackageRule(re.compile(r"cec[ei]|fagiol|lenticch|\blegum"), {"GR": 400}),
]

_GR_UNITS = {UnitaMisura.GR, UnitaMisura.KG}
_ML_UNITS = {UnitaMisura.ML, UnitaMisura.L}


def _match_rule(name: str) -> _PackageRule | None:
    lowered = name.lower()
    for rule in _PACKAGE_RULES:
        if rule.pattern.search(lowered):
            return rule
    return None


def round_to_purchasable(ingredienti: list[Ingrediente]) -> list[Ingrediente]:
    """Round each ingredient's quantity up to a realistic package multiple.

    Every quantity given in PZ is ceil'd to a whole piece first — there is no
    such thing as buying half an item. Ingredients matching a known packaged
    category are then normalized to that category's base unit (GR or ML,
    converting from KG/L if needed) and rounded up to its package increment.
    Everything else — fresh produce, fresh meat/fish, anything unmatched —
    passes through unchanged.
    """
    result = []
    for ingr in ingredienti:
        quantita = ingr.quantita
        unita = ingr.unita

        if unita == UnitaMisura.PZ:
            quantita = math.ceil(quantita)
            result.append(Ingrediente(nome=ingr.nome, quantita=quantita, unita=unita))
            continue

        rule = _match_rule(ingr.nome)
        if rule is None:
            result.append(ingr)
            continue

        if "GR" in rule.increments and unita in _GR_UNITS:
            increment = rule.increments["GR"]
            grams = quantita * 1000 if unita == UnitaMisura.KG else quantita
            rounded = math.ceil(grams / increment) * increment
            result.append(Ingrediente(nome=ingr.nome, quantita=rounded, unita=UnitaMisura.GR))
        elif "ML" in rule.increments and unita in _ML_UNITS:
            increment = rule.increments["ML"]
            ml = quantita * 1000 if unita == UnitaMisura.L else quantita
            rounded = math.ceil(ml / increment) * increment
            result.append(Ingrediente(nome=ingr.nome, quantita=rounded, unita=UnitaMisura.ML))
        else:
            # Matched category but an unexpected unit came back (e.g. a
            # weight-based rule against a PZ item) — don't guess, pass through.
            result.append(ingr)

    return result
