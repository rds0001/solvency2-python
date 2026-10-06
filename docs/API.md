# Function reference

All inherited functions are directly available at `solvency2.<name>` and at the domain path below.
The local-input helpers are available from their named modules. No engine instance is required.

## Shared contract

Calculation inputs use the context currency for monetary amounts and decimal ratios unless the method explicitly states another unit.
Signs, selected populations and qualification declarations are method-specific; missing is never zero.
Calculation outputs are `Result`; see [context, provenance and errors](LIMITATIONS.md).
Source IDs below are inherited method anchors, not a new legal interpretation. Dynamic result sources may add more detail.
Examples use fixed independent synthetic references; their declarations are not insurer data or approvals.
The full input mapping and original derivation are available offline by case ID. Known guards and errors remain active.
For a new function, first inspect its example inputs, method description and returned details. See [recipes](RECIPES.md), [inputs](DATA.md), and [overrides](PARAMETERS.md).

## solvency2.life

### simplified_longevity_risk

```python
solvency2.life.simplified_longevity_risk(mortality_rate: float, modified_duration: float, best_estimate: float, *, kind: str, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Art92/98: factor*q*n*growth**((n-1)/2)*BE on qualified selected contracts.

q is the sum-assured weighted NEXT-twelve-month mortality rate. Fractional
modified durations are retained; no invented rounding or contract selection.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `uw-simplified-baseline-life-longevity-3`. 24 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'uw-simplified-baseline-life-longevity-3')
context = replace(base, **case.get('context', {}))
result = s2.simplified_longevity_risk(**case['kwargs'], context=context)
# Independent expected value: 13.2
```

Example input (JSON):

```json
{
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art88-selected-contracts-weighted-inputs",
  "kind": "life",
  "mortality_rate": 0.02,
  "modified_duration": 3,
  "best_estimate": 1000
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### simplified_expense_risk

```python
solvency2.life.simplified_expense_risk(previous_year_amount: float, modified_duration: float, inflation_rate: float, *, kind: str, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Art94/99/101: factor*A*n + A*(G(i+shift,n)-G(i,n)).

G(r,n)=((1+r)**n-1)/r, continuously extended to G(0,n)=n. The amount is
last-year expenses (life/health) or medical payments, NOT a projected BE.
High-precision intermediates avoid cancellation around zero inflation.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `uw-simplified-baseline-life_expense-zero`. 60 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'uw-simplified-baseline-life_expense-zero')
context = replace(base, **case.get('context', {}))
result = s2.simplified_expense_risk(**case['kwargs'], context=context)
# Independent expected value: 21
```

Example input (JSON):

```json
{
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art88-selected-contracts-weighted-inputs",
  "kind": "life_expense",
  "previous_year_amount": 100,
  "modified_duration": 2,
  "inflation_rate": 0
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### simplified_capital_at_risk

```python
solvency2.life.simplified_capital_at_risk(contracts: Mapping, *, kind: str, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Sum per-contract max(current net benefit + additional future PV - net BE,0).

Inputs refer to the year/event specified by the chosen article. A net
portfolio difference is not a substitute for individually floored contracts.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `uw-biometric-baseline-car-health_income-negative-be`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'uw-biometric-baseline-car-health_income-negative-be')
context = replace(base, **case.get('context', {}))
result = s2.simplified_capital_at_risk(**case['kwargs'], context=context)
# Independent expected value: 20
```

Example input (JSON):

```json
{
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art88-event-year-selection-and-d2-period-qualified",
  "kind": "health_income",
  "contracts": {
    "A": {
      "net_current_benefits": 0,
      "net_future_benefits_pv": 0,
      "net_best_estimate": -20
    }
  }
}
```

### simplified_mortality_risk

```python
solvency2.life.simplified_mortality_risk(capital_at_risk: list[float], basic_spot_rates: list[float], mortality_rate: float, modified_duration: float, *, kind: str, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Art91/97 finite annual sum with midyear discount and survival weighting.

q is the sum-assured weighted rate over all future years, unlike longevity.
The printed upper index is modified duration: fractional values remain
unqualified, never silently rounded, truncated or prorated.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `uw-biometric-baseline-mortality-life-empty`. 36 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'uw-biometric-baseline-mortality-life-empty')
context = replace(base, **case.get('context', {}))
result = s2.simplified_mortality_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art88-event-year-selection-and-d2-period-qualified",
  "kind": "life",
  "capital_at_risk": [],
  "basic_spot_rates": [],
  "mortality_rate": 0.02,
  "modified_duration": 0
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### simplified_disability_risk

```python
solvency2.life.simplified_disability_risk(capital_at_risk_1: float, capital_at_risk_2: float, incidence_rate_1: float, incidence_rate_2: float, termination_rate: float, modified_duration: float, best_estimate: float, *, kind: str, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Three printed terms under Art93/100; no period inference or term floors.

Health Art100(d) has conflicting DE/EN d2 descriptions. The supplied d2
basis must be explicitly externally qualified; its numeric value is retained.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `uw-biometric-baseline-disability-life-no-incidence`. 28 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'uw-biometric-baseline-disability-life-no-incidence')
context = replace(base, **case.get('context', {}))
result = s2.simplified_disability_risk(**case['kwargs'], context=context)
# Independent expected value: 6.6
```

Example input (JSON):

```json
{
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art88-event-year-selection-and-d2-period-qualified",
  "kind": "life",
  "capital_at_risk_1": 100,
  "capital_at_risk_2": 80,
  "incidence_rate_1": 0,
  "incidence_rate_2": 0,
  "termination_rate": 0.05,
  "modified_duration": 3,
  "best_estimate": 200
}
```

Reference-tested failure codes: `INVALID_INPUT`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### simplified_life_catastrophe_risk

```python
solvency2.life.simplified_life_catastrophe_risk(capital_at_risk: float, *, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Art96 factor times the already contract-floored CAR sum, not death benefits.

Output unit: `context currency`. Sources: `DR:article-88`, `DR:article-96`.

Fixed example: `uw-biometric-baseline-catastrophe-zero`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'uw-biometric-baseline-catastrophe-zero')
context = replace(base, **case.get('context', {}))
result = s2.simplified_life_catastrophe_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art88-event-year-selection-and-d2-period-qualified",
  "capital_at_risk": 0
}
```

Reference-tested failure codes: `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### simplified_lapse_risk

```python
solvency2.life.simplified_lapse_risk(contracts: Mapping, average_lapse_rate: float, runoff_period: float, *, kind: str, direction: str, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Art95/102 up: half * max(qualified rate, source threshold) * years * S+.

Each contract provides termination_payment_net (after amounts recoverable
from the policyholder/intermediary) and technical_provisions_excluding_rm.
Negative strains never offset positive ones. Rate and period must describe
the positive-strain population. The printed down formula has an unresolved
sign issue and is deliberately not converted to positive capital.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `uw-lapse-baseline-life-empty`. 56 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'uw-lapse-baseline-life-empty')
context = replace(base, **case.get('context', {}))
result = s2.simplified_lapse_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "contracts": {},
  "average_lapse_rate": 0.1,
  "runoff_period": 2,
  "kind": "life",
  "direction": "up",
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art88-positive-strain-population-rate-and-runoff"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### life_mass_lapse_special_eligibility

```python
solvency2.life.life_mass_lapse_special_eligibility(policyholder_type: str, conditions: Mapping, *, beneficiary_count: int | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Screen declared142(6)a facts; a negative result does NOT select category b.

Related beneficiaries are excluded independently of count. The20-person
limit belongs to the separate estate/inheritance-purpose exclusion only.
Underlying reinsurance scope and worst termination valuation remain external.

Output unit: `indicator`. Sources: `DR:article-142:6:a`.

Fixed example: `mass-lapse-special-baseline-non-natural-consent-true`. 64 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mass-lapse-special-baseline-non-natural-consent-true')
context = replace(base, **case.get('context', {}))
result = s2.life_mass_lapse_special_eligibility(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "policyholder_type": "non_natural_person",
  "conditions": {
    "in_directive_scope": true,
    "termination_increases_tp": true,
    "beneficiary_consent_required": true
  },
  "beneficiary_count": null,
  "qualification_reference": "SYN-qualified-contract"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### life_biometric_selection

```python
solvency2.life.life_biometric_selection(shock: str, valuations: Mapping, *, valuation_basis: str, grouping_mode: str, grouping_qualified: bool | None = None, valuation_reference: str, context: solvency2._core.core.Context)
```

Select qualified life units by strictly increased TP excluding risk margin.

Direct/underlying basis, grouping and external TP valuation requirements
are unchanged; the shared private helper does not contribute health sources.

Output unit: `selection_units`. Sources: `DR:articles-137-138:2-3`.

Fixed example: `life-selection-baseline-mortality-qualified-aggregate`. 102 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-selection-baseline-mortality-qualified-aggregate')
context = replace(base, **case.get('context', {}))
result = s2.life_biometric_selection(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "shock": "mortality",
  "valuations": {
    "group": {
      "base_tp_excluding_risk_margin": 200,
      "stressed_tp_excluding_risk_margin": 195
    }
  },
  "valuation_basis": "direct_insurance_contracts",
  "grouping_mode": "article35",
  "grouping_qualified": true,
  "valuation_reference": "SYN-qualified-contract-TP-excluding-RM-and-shock"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### life_biometric_stress

```python
solvency2.life.life_biometric_stress(rate: float, shock: str, *, rate_basis: str, context: solvency2._core.core.Context)
```

Apply a selected biometric stress without inventing a probability/intensity conversion.

Disability incidence/recovery stresses must be projected jointly. Contract
selection and time-period assignment are external, not inferred from rate.

Output unit: `rate`. Sources: `DR:article-137:1`, `DR:article-138:1`, `DR:article-139`.

Fixed example: `life-rate-intensity`. 15 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-rate-intensity')
context = replace(base, **case.get('context', {}))
result = s2.life_biometric_stress(**case['kwargs'], context=context)
# Independent expected value: 2.3
```

Example input (JSON):

```json
{
  "rate": 2,
  "shock": "mortality",
  "rate_basis": "intensity"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### life_catastrophe_rate_stress

```python
solvency2.life.life_catastrophe_rate_stress(rate: float, *, selected: bool | None, selection_reference: str, context: solvency2._core.core.Context)
```

Add the twelve-month mortality shock only to externally selected contracts.

The input is a mortality probability for the next twelve months, not an
intensity. No lifetime extrapolation, contract selection or BOF valuation
is inferred; article 143 specifies no probability cap.

Output unit: `probability`. Sources: `DR:article-143:1-3`.

Fixed example: `life-2027-cat-true`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-2027-cat-true')
context = replace(base, **case.get('context', {}))
result = s2.life_catastrophe_rate_stress(**case['kwargs'], context=context)
# Independent expected value: 0.0115
```

Example input (JSON):

```json
{
  "rate": 0.01,
  "selected": true,
  "selection_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### life_expense_level_stress

```python
solvency2.life.life_expense_level_stress(expense: float, *, context: solvency2._core.core.Context)
```

Stress eligible costs; combine with inflation stress in the external projection.

Output unit: `context currency`. Sources: `DR:article-140:a`.

Fixed example: `life-expense-zero`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-expense-zero')
context = replace(base, **case.get('context', {}))
result = s2.life_expense_level_stress(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "expense": 0
}
```

### life_expense_inflation_stress

```python
solvency2.life.life_expense_inflation_stress(inflation_rate: float, *, context: solvency2._core.core.Context)
```

Add the prescribed percentage-point shock without choosing a compounding model.

Output unit: `rate`. Sources: `DR:article-140:b`.

Fixed example: `life-expense-inflation`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-expense-inflation')
context = replace(base, **case.get('context', {}))
result = s2.life_expense_inflation_stress(**case['kwargs'], context=context)
# Independent expected value: 0.03
```

Example input (JSON):

```json
{
  "inflation_rate": 0.02
}
```

### life_revision_stress

```python
solvency2.life.life_revision_stress(annuity_benefit: float, *, revision_exposed: bool | None, context: solvency2._core.core.Context)
```

Increase only externally qualified revision-exposed annuity benefits.

Output unit: `context currency`. Sources: `DR:article-141`.

Fixed example: `life-2027-revision-true`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-2027-revision-true')
context = replace(base, **case.get('context', {}))
result = s2.life_revision_stress(**case['kwargs'], context=context)
# Independent expected value: 103
```

Example input (JSON):

```json
{
  "annuity_benefit": 100,
  "revision_exposed": true
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### lapse_stress

```python
solvency2.life.lapse_stress(rate: float, direction: str, *, context: solvency2._core.core.Context)
```

Stress the relevant option-exercise rate after the required contract selection.

Output unit: `probability`. Sources: `DR:article-142:2-3`.

Fixed example: `life-2027-lapse-up-cap`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-2027-lapse-up-cap')
context = replace(base, **case.get('context', {}))
result = s2.lapse_stress(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "rate": 0.8,
  "direction": "up"
}
```

### life_lapse_option_stress

```python
solvency2.life.life_lapse_option_stress(exercise_rate: float, direction: str, *, option_kind: str, selected: bool | None, selection_reference: str, context: solvency2._core.core.Context)
```

Return exercise probability, stressing non-exercise for extension options.

Selection depends on the relevant technical-provision effect, not merely
the option label. Underlying/reinsurance rights are classified externally.

Output unit: `probability`. Sources: `DR:article-142:2-5`.

Fixed example: `life-2027-extension-up`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-2027-extension-up')
context = replace(base, **case.get('context', {}))
result = s2.life_lapse_option_stress(**case['kwargs'], context=context)
# Independent expected value: 0.7
```

Example input (JSON):

```json
{
  "exercise_rate": 0.8,
  "direction": "up",
  "option_kind": "extension",
  "selected": true,
  "selection_reference": "SYN"
}
```

### life_lapse_risk

```python
solvency2.life.life_lapse_risk(gross_losses: Mapping, net_losses: Mapping, *, valuation_reference: str, tie_break: str | None = None, context: solvency2._core.core.Context)
```

Select gross capital using all three externally valued net scenarios.

Output unit: `context currency`. Sources: `DR:article-142:1`, `DR:article-142:7`, `DR:article-206:2`.

Fixed example: `life-lapse-net-selection`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-lapse-net-selection')
context = replace(base, **case.get('context', {}))
result = s2.life_lapse_risk(**case['kwargs'], context=context)
# Independent expected value: 80
```

Example input (JSON):

```json
{
  "gross_losses": {
    "up": 100,
    "down": 80,
    "mass": 90
  },
  "net_losses": {
    "up": 30,
    "down": 50,
    "mass": 40
  },
  "valuation_reference": "SYN-142"
}
```

Reference-tested failure codes: `AMBIGUOUS_SELECTION`. Additional shared validation errors can apply.

### life_mass_lapse_factor

```python
solvency2.life.life_mass_lapse_factor(category: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Return event share, never a proportional BOF/TP loss or standalone mass SCR.

Categories a/b are disjoint and a/b/c apply jointly where relevant. Special
category qualification and worst termination form remain external.
In2027, uniform application to affected contracts and application to the
underlying insurance contracts for reinsurance a/b must also be qualified.

Output unit: `ratio`. Sources: `DR:article-142:6`.

Fixed example: `life-mass-future_142_6_c`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-mass-future_142_6_c')
context = replace(base, **case.get('context', {}))
result = s2.life_mass_lapse_factor(**case['kwargs'], context=context)
# Independent expected value: 0.4
```

Example input (JSON):

```json
{
  "category": "future_142_6_c",
  "qualification_reference": "SYN-142"
}
```

## solvency2.own_funds

### own_funds_tier1_loss_absorption_trigger

```python
solvency2.own_funds.own_funds_tier1_loss_absorption_trigger(eligible_scr_own_funds: float, scr: float, eligible_mcr_own_funds: float, mcr: float, *, scr_not_restored_within_period: bool | None, additional_contractual_trigger: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Article71(8) event screen, NOT write-down/conversion or Tier1 eligibility.

Use distinct SCR/MCR eligible funds. Equality at either threshold triggers.
The three-month non-restoration history and any additional contractual event
are externally established; a current recovery does not erase a past event.
Article71(10) waiver may affect execution, never the fact of the event.

Output unit: `indicator`. Sources: `DR:article-71:8`.

Fixed example: `tier1-trigger-baseline-decidable-or`. 38 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tier1-trigger-baseline-decidable-or')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_tier1_loss_absorption_trigger(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "eligible_scr_own_funds": 70,
  "scr": 100,
  "eligible_mcr_own_funds": 41,
  "mcr": 40,
  "scr_not_restored_within_period": null,
  "additional_contractual_trigger": null,
  "qualification_reference": "SYN-eligible-bases-latest-values-Art69-instrument-and-event-history"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### own_funds_tier1_mechanism_requirements

```python
solvency2.own_funds.own_funds_tier1_mechanism_requirements(eligible_scr_own_funds: float, scr: float, eligible_mcr_own_funds: float, mcr: float, *, scr_not_restored_within_period: bool | None, additional_contractual_trigger: bool | None, mechanism: str, partial_restoration_sufficient: bool | None, qualification_reference: str, context: solvency2._core.core.Context, waiver_conditions: Optional[Mapping] = None, waiver_reference: str | None = None)
```

Select statutory execution requirements; no instrument amount or booking.

a/b requires full absorption. c permits partial restoration or at-least-linear
absorption, unless the narrowly qualified supervisory exception is declared.
Contract-only additional triggers have no universal execution rule here.

Output unit: `indicator`. Sources: `DR:article-71:5a`, `DR:article-71:6a`, `DR:article-71:10`.

Fixed example: `tier1-mechanism-baseline-write_down-partial`. 60 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tier1-mechanism-baseline-write_down-partial')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_tier1_mechanism_requirements(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "eligible_scr_own_funds": 90,
  "scr": 100,
  "eligible_mcr_own_funds": 41,
  "mcr": 40,
  "scr_not_restored_within_period": true,
  "additional_contractual_trigger": false,
  "qualification_reference": "SYN-eligible-bases-latest-values-Art69-instrument-and-event-history",
  "mechanism": "write_down",
  "partial_restoration_sufficient": true
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### own_funds_step_up_limit

```python
solvency2.own_funds.own_funds_step_up_limit(original_credit_spread: float, swap_spread: float, *, tier: str, one_off_coupon_increase_with_call_option: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Art73(4)/77(4) maximum modest one-off step-up, not whole-tier eligibility.

Decimal rate units:100bp=.01. The original-to-stepped-index swap spread is
subtracted in BOTH branches; a negative limit is retained, never floored.

Output unit: `rate`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `final-numeric-baseline-step-tier2-negative-limit`. 24 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'final-numeric-baseline-step-tier2-negative-limit')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_step_up_limit(**case['kwargs'], context=context)
# Independent expected value: -0.005
```

Example input (JSON):

```json
{
  "original_credit_spread": 0.03,
  "swap_spread": 0.02,
  "tier": "tier2",
  "one_off_coupon_increase_with_call_option": true,
  "qualification_reference": "SYN-one-off-step-up-with-call-and-index-bases"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### own_funds_classification_evidence_check

```python
solvency2.own_funds.own_funds_classification_evidence_check(evidence: Mapping, *, tier: str, own_funds_kind: str, unlisted: bool, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory declared classification evidence, never classify an instrument.

References identify the applicable instrument/subparagraph, justified
non-applicability and any approved exception. Periods describe those routes;
they are not unconditional maturity tests or permission to repay. Tier1
quality in excess of its cap may follow73(1)(j), not ordinary Tier2 terms.
Values for subsequent allocation remain independently qualified inputs.

Output unit: `indicator`. Sources: `DR:articles-62-67`, `DR:articles-69;71-79`.

Fixed example: `of-class-close-baseline-basic-tier1-listed-missing`. 48 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-class-close-baseline-basic-tier1-listed-missing')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_classification_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "tier": "tier1",
  "own_funds_kind": "basic",
  "unlisted": false,
  "evidence": {},
  "assessment_reference": "SYN-qualified-instrument-subparagraphs-exceptions"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### own_funds_expected_future_premium_profit

```python
solvency2.own_funds.own_funds_expected_future_premium_profit(group_valuations: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Aggregate without-minus-with valuations in externally qualified groups.

Each row has exactly with_future_premiums and without_future_premiums,
both WITHOUT risk margin. Historical losses cannot offset other groups;
the published 2027 rule requires signed cross-group netting. No invented
total zero floor, insurer valuation model or additional own-funds credit.

Output unit: `currency`. Sources: `DR:article-1:46`, `DR:article-260:2:3:4`.

Fixed example: `future-profit-baseline-zero`. 36 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-profit-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_expected_future_premium_profit(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "group_valuations": {
    "A": {
      "with_future_premiums": 0,
      "without_future_premiums": 0
    }
  },
  "qualification_reference": "SYN-qualified-DR260-group-and-scenarios"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### own_funds_expected_future_fee_profit_2027

```python
solvency2.own_funds.own_funds_expected_future_fee_profit_2027(with_future_fees: float, without_future_fees: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Signed fee-scenario difference for one qualified index/unit-linked scope.

Both input valuations exclude risk margin. No transfer of the premium-only
grouping clause to fees, and no automatic addition of fee profit to EPIFP.

Output unit: `currency`. Sources: `DR:article-1:46a`, `DR:article-260:2a`.

Fixed example: `future-profit-future-fee-zero`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-profit-future-fee-zero')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_expected_future_fee_profit_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "with_future_fees": 0,
  "without_future_fees": 0,
  "qualification_reference": "SYN-qualified-unit-linked-fee-scenarios"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### own_funds_scr_allocation

```python
solvency2.own_funds.own_funds_scr_allocation(scr: float, tier1: float, restricted_tier1: float, tier2: float, tier3: float, *, context: solvency2._core.core.Context)
```

Validate one proposed full SCR-covering allocation of preclassified tiers.

Output unit: `context currency`. Sources: `DIR:article-98:3`, `DR:article-82:1`, `DR:article-82:3`.

Fixed example: `of-scr-exact-half`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-scr-exact-half')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_scr_allocation(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "scr": 100,
  "tier1": 50,
  "restricted_tier1": 10,
  "tier2": 50,
  "tier3": 0
}
```

Reference-tested failure codes: `INELIGIBLE_ALLOCATION`, `INSUFFICIENT_COVERAGE`. Additional shared validation errors can apply.

### own_funds_mcr_allocation

```python
solvency2.own_funds.own_funds_mcr_allocation(mcr: float, basic_tier1: float, restricted_tier1: float, basic_tier2: float, *, context: solvency2._core.core.Context)
```

Validate one proposed full MCR-covering allocation of basic own funds.

Output unit: `context currency`. Sources: `DIR:article-98:4`, `DR:article-82:2`, `DR:article-82:3`.

Fixed example: `of-2027-mcr-limits`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-2027-mcr-limits')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_mcr_allocation(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "mcr": 100,
  "basic_tier1": 80,
  "restricted_tier1": 16,
  "basic_tier2": 20
}
```

Reference-tested failure codes: `INELIGIBLE_ALLOCATION`, `INSUFFICIENT_COVERAGE`. Additional shared validation errors can apply.

### own_funds_basic_before_adjustments

```python
solvency2.own_funds.own_funds_basic_before_adjustments(excess_assets_over_liabilities: float, subordinated_liabilities: float, own_shares: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Compose Article88 amounts before further deductions and eligibility limits.

Excess must still include own shares; using an already adjusted surplus
here would double-deduct them. This is not eligible own funds or Tier1.

Output unit: `context currency`. Sources: `DIR:article-88`.

Fixed example: `future-of-basic-zero`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-of-basic-zero')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_basic_before_adjustments(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "excess_assets_over_liabilities": 0,
  "subordinated_liabilities": 0,
  "own_shares": 0,
  "qualification_reference": "SYN"
}
```

### own_funds_reconciliation_reserve

```python
solvency2.own_funds.own_funds_reconciliation_reserve(excess_assets_over_liabilities: float, deductions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Subtract Article70 items, with explicit financial-participation overlap.

Future-premium expected profit is already in the supplied surplus, not an
extra addition. A signed reserve is preserved; no Tier1 eligibility is
inferred from this arithmetic. All deduction categories must be supplied.

Output unit: `context currency`. Sources: `DR:article-70:1:2`.

Fixed example: `of-reserve-negative-excess`. 11 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-reserve-negative-excess')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_reconciliation_reserve(**case['kwargs'], context=context)
# Independent expected value: -20
```

Example input (JSON):

```json
{
  "excess_assets_over_liabilities": -20,
  "deductions": {
    "own_shares": 0,
    "foreseeable_distributions": 0,
    "listed_basic_items": 0,
    "approved_unlisted_items": 0,
    "restricted_items": 0,
    "financial_participation_deductions": 0,
    "financial_participation_already_counted": 0
  },
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### own_funds_restricted_deduction

```python
solvency2.own_funds.own_funds_restricted_deduction(restricted_own_funds: float, portfolio_kind: str, immaterial_simplification: bool, *, notional_scr: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Deduct restricted surplus, or the full elected immaterial RFF amount.

Restricted funds already exclude future shareholder transfers. Materiality,
portfolio classification and notional SCR are externally qualified; no
internal model or arbitrary materiality threshold is supplied here.

Output unit: `context currency`. Sources: `DR:article-70:1:e`, `DR:article-80:2`, `DR:article-81`.

Fixed example: `of-2027-restricted-immaterial`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-2027-restricted-immaterial')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_restricted_deduction(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "restricted_own_funds": 100,
  "portfolio_kind": "ring_fenced",
  "immaterial_simplification": true,
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### own_funds_financial_participation_deduction

```python
solvency2.own_funds.own_funds_financial_participation_deduction(participations: Mapping, threshold_basis: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Deduct qualified nonexempt financial participations, with per-holding audit.

Each input is a complete participation, not an arbitrary instrument slice.
Article68(3) exemptions and direct/indirect ownership are qualified before
calling. SRC-0135 Guideline5 / SRC-0067 paragraph26 require the basis
BEFORE Article68 deductions; exemptions are not inherited across versions.
Deduction amounts here are not yet allocated to own-funds tiers.

Output unit: `context currency`. Sources: `DR:article-68:1:2:4`.

Fixed example: `of-financial-zero-basis`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-financial-zero-basis')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_financial_participation_deduction(**case['kwargs'], context=context)
# Independent expected value: 5
```

Example input (JSON):

```json
{
  "participations": {
    "E": 5
  },
  "threshold_basis": 0,
  "qualification_reference": "SYN"
}
```

### own_funds_financial_deduction_tier

```python
solvency2.own_funds.own_funds_financial_deduction_tier(tier: str, available: Mapping, deductions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Select a remaining own-fund bucket after externally qualified deductions.

All available amounts precede Article68 deductions. The deduction amounts
already reflect version-specific exemption/approval decisions. This does not
classify instruments, grant exemptions or calculate eligible own funds.

Output unit: `context currency`. Sources: `DR:article-68:5`.

Fixed example: `of-financial-tier-base-7-tier2`. 48 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-financial-tier-base-7-tier2')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_financial_deduction_tier(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "tier": "tier2",
  "available": {
    "unrestricted_tier1": 0,
    "restricted_tier1": 0,
    "tier2": 0
  },
  "deductions": {
    "cet1": 0,
    "additional_tier1": 0,
    "tier2": 0,
    "unclassified": 0
  },
  "qualification_reference": "SYN-pre-deduction-qualified-tiers-and-nonexempt-deductions"
}
```

### own_funds_financial_exemption_screen

```python
solvency2.own_funds.own_funds_financial_exemption_screen(facts: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context, approval_reference: str | None = None)
```

Version-specific declared-prerequisite screen, never approval of an exemption.

Unknown necessary facts block the decision. A proved alternative can settle
an OR without inventing facts. The 2027 branch separately requires declared
actual supervisory permission; evidence remains externally qualified.

Output unit: `indicator`. Sources: `DR:article-68:3`.

Fixed example: `of-exemption-base-unknown-alternative`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'of-exemption-base-unknown-alternative')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_financial_exemption_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "facts": {
    "strategic": true,
    "method1_financial_conglomerate": null,
    "method1_solvency2": true
  },
  "qualification_reference": "SYN-declared-qualified-prerequisites",
  "approval_reference": null
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### own_funds_distribution_policy_ratio

```python
solvency2.own_funds.own_funds_distribution_policy_ratio(policy_usable: bool, *, qualification_reference: str, context: solvency2._core.core.Context, policy_lower: float | None = None, policy_upper: float | None = None, historical_values: list[float] | tuple[float, ...] | None = None, public_announcements: list[float] | tuple[float, ...] | None = None)
```

Select a qualified payout ratio; no invented cap at 100 percent.

Output unit: `ratio`. Sources: `DR:article-70a:4-5`.

Fixed example: `distribution-ratio-policy-3`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'distribution-ratio-policy-3')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_distribution_policy_ratio(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "policy_usable": true,
  "policy_lower": 0,
  "policy_upper": 0,
  "qualification_reference": "SYN-qualified-2027-policy-and-accounting-inputs"
}
```

### own_funds_distribution_policy_amount

```python
solvency2.own_funds.own_funds_distribution_policy_amount(policy_usable: bool, *, qualification_reference: str, context: solvency2._core.core.Context, policy_lower: float | None = None, policy_upper: float | None = None, historical_values: list[float] | tuple[float, ...] | None = None, public_announcements: list[float] | tuple[float, ...] | None = None)
```

Select a qualified annual payout amount, in the context reporting currency.

Output unit: `context currency`. Sources: `DR:article-70a:4-5`.

Fixed example: `distribution-amount-policy`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'distribution-amount-policy')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_distribution_policy_amount(**case['kwargs'], context=context)
# Independent expected value: 40
```

Example input (JSON):

```json
{
  "policy_usable": true,
  "policy_lower": 20,
  "policy_upper": 40,
  "qualification_reference": "SYN-qualified-2027-policy-and-accounting-inputs"
}
```

### own_funds_foreseeable_distributions_2027

```python
solvency2.own_funds.own_funds_foreseeable_distributions_2027(method: str, *, qualification_reference: str, context: solvency2._core.core.Context, formal_amount: float | None = None, prior_year_distributions: float | None = None, payout_ratio: float | None = None, cumulative_interim_profit: float | None = None, estimated_annual_distribution: float | None = None, elapsed_year_fraction: float | None = None)
```

Formal amount, or one of two permitted accrual methods before that stage.

Formal decisions/proposals, accounting profit and fiscal-year fraction are
qualified externally. No internal profit model or day-count is invented.
Fees under Article70(1)(b) are separate, not calculated by this function.

Output unit: `context currency`. Sources: `DR:article-70a:2-3`.

Fixed example: `distribution-foreseeable-formal0`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'distribution-foreseeable-formal0')
context = replace(base, **case.get('context', {}))
result = s2.own_funds_foreseeable_distributions_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "method": "formal",
  "formal_amount": 0,
  "qualification_reference": "SYN-qualified-2027-policy-and-accounting-inputs"
}
```

## solvency2.capital

### restricted_portfolio_scenario_charge

```python
solvency2.capital.restricted_portfolio_scenario_charge(portfolio_kinds: Mapping, gross_losses: Mapping, net_losses: Mapping, target_portfolio: str, *, article217_scope_confirmed: bool | None, qualification_reference: str, context: solvency2._core.core.Context, view: str = 'gross', tie_break: str | None = None)
```

One portfolio's nonnegative charge under the COMMON worst net scenario.

Nested losses are portfolio -> scenario -> signed BOF loss, already adjusted
for217(5) profit participation. A gain is negative and offsets losses when
selecting the whole-undertaking scenario, never after independent choices.
net includes qualified FDB absorption; gross and net retain the same scenario.

Output unit: `context currency`. Sources: `DR:article-216`, `DR:article-217:3-7`.

Fixed example: `restricted-portfolio-baseline-common`. 28 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'restricted-portfolio-baseline-common')
context = replace(base, **case.get('context', {}))
result = s2.restricted_portfolio_scenario_charge(**case['kwargs'], context=context)
# Independent expected value: 10
```

Example input (JSON):

```json
{
  "portfolio_kinds": {
    "fund": "ring_fenced",
    "rest": "remainder"
  },
  "gross_losses": {
    "fund": {
      "up": -30,
      "down": 10
    },
    "rest": {
      "up": 40,
      "down": 5
    }
  },
  "net_losses": {
    "fund": {
      "up": -30,
      "down": 10
    },
    "rest": {
      "up": 40,
      "down": 5
    }
  },
  "target_portfolio": "fund",
  "article217_scope_confirmed": true,
  "qualification_reference": "SYN-all217-scope-signed-BOF-after-profit-sharing"
}
```

Reference-tested failure codes: `AMBIGUOUS_SELECTION`, `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### restricted_portfolio_scr_sum

```python
solvency2.capital.restricted_portfolio_scr_sum(notional_scr: Mapping, portfolio_kinds: Mapping, *, article217_scope_confirmed: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Sum complete qualified notional SCRs, including remainder; no diversification.

Output unit: `context currency`. Sources: `DR:article-216`, `DR:article-217:1-2`, `DR:article-217:8-9`.

Fixed example: `restricted-portfolio-baseline-zero`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'restricted-portfolio-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.restricted_portfolio_scr_sum(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "notional_scr": {
    "fund": 0,
    "rest": 0
  },
  "portfolio_kinds": {
    "fund": "ring_fenced",
    "rest": "remainder"
  },
  "article217_scope_confirmed": true,
  "qualification_reference": "SYN-all217-scope-signed-BOF-after-profit-sharing"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### capital_breach_requirements

```python
solvency2.capital.capital_breach_requirements(capital_requirement: str, actual_breach: bool, breach_risk_within_horizon: bool, *, qualification_reference: str, deterioration: Optional[Mapping] = None, consolidated_own_funds: float | None = None, consolidated_scr: float | None = None, transition_measures: list[str] | None = None, transition_plan_active: bool | None = None, context: solvency2._core.core.Context)
```

Select notification/plan duties using externally established breach facts.

Future MCR plans also respond to prospective breach; historical MCR and
SCR plans here respond to actual breach. No grace period for notification,
calendar deadline, automatic extension, filing or approval is produced.
Optional Article136 evidence adds its independent notification trigger;
absence is not evidence that financial deterioration has been ruled out.
Combined-group minimum breaches use233a(6) only in the2027 profile;
SCR own funds never substitute for minimum-eligible basic own funds.

Output unit: `indicator`. Sources: `DIR:article-138:1-3`, `DIR:article-139:1-2`.

Fixed example: `capital-breach-baseline-scr-11`. 64 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'capital-breach-baseline-scr-11')
context = replace(base, **case.get('context', {}))
result = s2.capital_breach_requirements(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "capital_requirement": "scr",
  "actual_breach": true,
  "breach_risk_within_horizon": true,
  "qualification_reference": "SYN-capital-status-qualified"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### lac_dt_profit_assumptions_check

```python
solvency2.capital.lac_dt_profit_assumptions_check(projection: Mapping, conditions: Mapping, *, management_actions_assumed: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Check one externally qualified projection/return-pair and declared evidence.

Five years bounds new-business revenue assumptions, not all future profits.
A longer profit forecast activates the haircut condition, without inventing
its amount. Lower-than-forward returns require review of the literal source
rather than treating conservative assumptions as automatically unlawful.

Output unit: `indicator`. Sources: `DR:article-207:2a-2d`, `DR:article-15`.

Fixed example: `lac-dt-profit-baseline-boundary-five`. 72 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'lac-dt-profit-baseline-boundary-five')
context = replace(base, **case.get('context', {}))
result = s2.lac_dt_profit_assumptions_check(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "projection": {
    "business_plan_years": 5,
    "new_business_years": 5,
    "forecast_years": 5,
    "assumed_return": 0.02,
    "post_stress_forward_return": 0.02
  },
  "conditions": {
    "carryforward_limits_considered": true,
    "stress_effects_considered": true,
    "forecast_uncertainty_considered": true,
    "probability_no_more_favourable": true,
    "planned_business_only": true
  },
  "management_actions_assumed": false,
  "qualification_reference": "SYN-qualified-projection-and-corresponding-period-returns"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### aggregate_risk

```python
solvency2.capital.aggregate_risk(components: 'Mapping[str, float]', matrix_id: 'str', *, context: 'Context')
```

Aggregate already determined module charges using an explicit regulatory matrix.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `default-baseline-matrix-3-4`. 86 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'default-baseline-matrix-3-4')
context = replace(base, **case.get('context', {}))
result = s2.aggregate_risk(**case['kwargs'], context=context)
# Independent expected value: 6.557438524302
```

Example input (JSON):

```json
{
  "matrix_id": "default",
  "components": {
    "type1": 3,
    "type2": 4
  }
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### basic_scr

```python
solvency2.capital.basic_scr(components: 'Mapping[str, float]', intangible_charge: 'float', *, context: 'Context')
```

Five-module aggregation plus the charge on recognised intangible assets.

Output unit: `context currency`. Sources: `DIR:article-104`, `DIR:annex-IV:1`, `DR:article-87`, `DR:article-203`.

Fixed example: `bscr-2027-five-modules`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'bscr-2027-five-modules')
context = replace(base, **case.get('context', {}))
result = s2.basic_scr(**case['kwargs'], context=context)
# Independent expected value: 5.567764362830021
```

Example input (JSON):

```json
{
  "components": {
    "market": 3,
    "default": 4,
    "life": 0,
    "health": 0,
    "nonlife": 0
  },
  "intangible_charge": 0
}
```

### scenario_loss

```python
solvency2.capital.scenario_loss(base_bof: 'float', stressed_bof: 'float', *, context: 'Context', assumption_checks: 'Mapping | None' = None)
```

Loss from external BOF; optional gross83 input checks are not a valuation model.

Output unit: `context currency`. Sources: `DR:article-83:5`.

Fixed example: `scenario-2027-bof-0`. 105 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'scenario-2027-bof-0')
context = replace(base, **case.get('context', {}))
result = s2.scenario_loss(**case['kwargs'], context=context)
# Independent expected value: 10
```

Example input (JSON):

```json
{
  "base_bof": 100,
  "stressed_bof": 90
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### select_scenario

```python
solvency2.capital.select_scenario(gross_losses: 'Mapping[str, float]', net_losses: 'Mapping[str, float]', tie_break: 'str | None' = None, *, context: 'Context')
```

Select the gross charge corresponding to the greatest net-of-FDB loss.

Output unit: `context currency`. Sources: `DR:article-165:2`, `DR:article-142:7`, `DR:article-188:7`, `DR:article-179:4`.

Fixed example: `net-scenario-selection`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'net-scenario-selection')
context = replace(base, **case.get('context', {}))
result = s2.select_scenario(**case['kwargs'], context=context)
# Independent expected value: 80
```

Example input (JSON):

```json
{
  "gross_losses": {
    "up": 100,
    "down": 80
  },
  "net_losses": {
    "up": 30,
    "down": 50
  }
}
```

### intangible_risk

```python
solvency2.capital.intangible_risk(recognised_value: float, *, context: solvency2._core.core.Context)
```

Charge on intangible value already recognised under Article 12.

Output unit: `context currency`. Sources: `DR:article-203`.

Fixed example: `capital-2027-intangible-0`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'capital-2027-intangible-0')
context = replace(base, **case.get('context', {}))
result = s2.intangible_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "recognised_value": 0
}
```

### lac_tp

```python
solvency2.capital.lac_tp(bscr: float, net_bscr: float, future_discretionary_benefits: float, *, context: solvency2._core.core.Context)
```

Signed (nonpositive) loss-absorbing adjustment for technical provisions.

Output unit: `context currency`. Sources: `DR:article-206:1`.

Fixed example: `capital-2027-lac-tp-3`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'capital-2027-lac-tp-3')
context = replace(base, **case.get('context', {}))
result = s2.lac_tp(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "bscr": 0,
  "net_bscr": 0,
  "future_discretionary_benefits": 0
}
```

### operational_risk

```python
solvency2.capital.operational_risk(bscr: float, earned_life: float, earned_life_ul: float, earned_nonlife: float, previous_life: float, previous_life_ul: float, previous_nonlife: float, tp_life: float, tp_life_ul: float, tp_nonlife: float, expenses_ul: float, *, context: solvency2._core.core.Context)
```

Gross premium/provision calculation; provisions exclude the risk margin.

Output unit: `context currency`. Sources: `DR:article-204:1-4`.

Fixed example: `capital-2027-op-zero`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'capital-2027-op-zero')
context = replace(base, **case.get('context', {}))
result = s2.operational_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "bscr": 0,
  "earned_life": 0,
  "earned_life_ul": 0,
  "earned_nonlife": 0,
  "previous_life": 0,
  "previous_life_ul": 0,
  "previous_nonlife": 0,
  "tp_life": 0,
  "tp_life_ul": 0,
  "tp_nonlife": 0,
  "expenses_ul": 0
}
```

### lac_dt_stress_amount

```python
solvency2.capital.lac_dt_stress_amount(bscr: float, operational: float, adjustment_tp: float, *, context: solvency2._core.core.Context)
```

Loss for the external tax revaluation, before (not after) the tax adjustment.

Output unit: `context currency`. Sources: `DR:article-207:1`.

Fixed example: `tax-stress-2027-zero`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tax-stress-2027-zero')
context = replace(base, **case.get('context', {}))
result = s2.lac_dt_stress_amount(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "bscr": 100,
  "operational": 0,
  "adjustment_tp": -100
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### lac_dt

```python
solvency2.capital.lac_dt(base_dta: float, base_dtl: float, stressed_dta: float, stressed_dtl: float, *, recoverability_reference: str | None = None, context: solvency2._core.core.Context)
```

Signed tax adjustment from externally valued balances after the Article 207(1) loss.

A nonempty evidence reference records the caller's basis for increased DTA;
it does not substantively establish future profits or legal recoverability.

Output unit: `context currency`. Sources: `DR:article-207:2-4`, `DR:article-15`.

Fixed example: `tax-2027-positive-zeroed`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tax-2027-positive-zeroed')
context = replace(base, **case.get('context', {}))
result = s2.lac_dt(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "base_dta": 10,
  "base_dtl": 40,
  "stressed_dta": 5,
  "stressed_dtl": 40
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### scr_standard_formula

```python
solvency2.capital.scr_standard_formula(bscr: float, operational: float, adjustment_tp: float, adjustment_dt: float, *, context: solvency2._core.core.Context, capital_addons: Optional[Mapping] = None, purpose: str = 'scr')
```

Compose standard formula and explicit imposed add-ons, not a full release.

Inputs exclude these add-ons already. For the risk_margin view only the
governance Article37(1)c add-on is removed by37(5); all reference-undertaking
selection underDR38 remains external, not inferred from this view switch.

Output unit: `context currency`. Sources: `DIR:article-103`, `DR:article-205`.

Fixed example: `scr-standard-zero`. 17 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'scr-standard-zero')
context = replace(base, **case.get('context', {}))
result = s2.scr_standard_formula(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "bscr": 0,
  "operational": 0,
  "adjustment_tp": 0,
  "adjustment_dt": 0
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### capital_add_on_amount

```python
solvency2.capital.capital_add_on_amount(base_scr: float, modified_scr: float, *, method: str, qualification_reference: str, context: solvency2._core.core.Context, base_eligible_own_funds: float | None = None, modified_eligible_own_funds: float | None = None, rebuttal_established: bool | None = None)
```

Prescribed add-on arithmetic, not a supervisory imposition or risk model.

SCR inputs exclude prior/concurrent add-ons. Modified valuations and any
permitted offsetting under283(7) are externally qualified. Article279's
risk-profile significance thresholds are separate from imposing an add-on.
No quantitative governance/additional2027 Article37(1)e formula is invented.

Output unit: `context currency`. Sources: `DR:article-279`, `DR:article-282`, `DR:article-284`.

Fixed example: `capital-addon-baseline-risk-zero-base`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'capital-addon-baseline-risk-zero-base')
context = replace(base, **case.get('context', {}))
result = s2.capital_add_on_amount(**case['kwargs'], context=context)
# Independent expected value: 10
```

Example input (JSON):

```json
{
  "base_scr": 0,
  "modified_scr": 10,
  "method": "risk_profile",
  "qualification_reference": "SYN-qualified-SCRs-without-prior-addons"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

## solvency2.reinsurance

### simplified_reinsurance_default_adjustment

```python
solvency2.reinsurance.simplified_reinsurance_default_adjustment(probability_of_default: float, modified_duration: float, recoverables_best_estimate: float, *, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Positive deduction corresponding to the printed negative Article61 AdjCD.

One counterparty/homogeneous group; PD is next12months, duration and BE
refer to the same recoverables. Not a counterparty-default SCR or projection.

Output unit: `context currency`. Sources: `DR:article-56`, `DR:article-61`, `DIR:article-81`.

Fixed example: `final-numeric-baseline-ri-zero-pd`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'final-numeric-baseline-ri-zero-pd')
context = replace(base, **case.get('context', {}))
result = s2.simplified_reinsurance_default_adjustment(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "probability_of_default": 0,
  "modified_duration": 2,
  "recoverables_best_estimate": 900,
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-Art56-same-counterparty-HRG-PD12month-duration-BE"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### underwriting_currency_basis_risk

```python
solvency2.reinsurance.underwriting_currency_basis_risk(capital_charge: float, joint_currency_stress_charge: float, *, single_component_only: bool | None, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Art86(a) lowest-level charge plus a fraction of its joint-FX difference.

The hypothetical charge is externally valued under simultaneous Art188.
Multiple affected components need86(b)'s common capacity treatment, not
independent repeated limits or an invented allocation of shared capacity.

Output unit: `context currency`. Sources: `DR:article-86:a`.

Fixed example: `final-numeric-baseline-fx-zero`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'final-numeric-baseline-fx-zero')
context = replace(base, **case.get('context', {}))
result = s2.underwriting_currency_basis_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "capital_charge": 0,
  "joint_currency_stress_charge": 0,
  "single_component_only": true,
  "eligibility_reference": "SYN-209-210-211-currency-basis-risk-single-component",
  "valuation_reference": "SYN-simultaneous-188-lowest-level"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### public_counter_guarantee_conditions_2027

```python
solvency2.reinsurance.public_counter_guarantee_conditions_2027(conditions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Article215a equivalence gate, not guarantee valuation or zero capital.

Only the directness requirement is waived for the counter-guarantee;
original guarantee requirements and all other counter-guarantee conditions
remain. Any downstream Article180/192 treatment needs its own scope checks.

Output unit: `indicator`. Sources: `DR:article-215a`.

Fixed example: `future-close-counter-all`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-close-counter-all')
context = replace(base, **case.get('context', {}))
result = s2.public_counter_guarantee_conditions_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "counter_guarantor_article180_2_first_subparagraph": true,
    "all_credit_risk_covered": true,
    "original_guarantee_article215": true,
    "counter_guarantee_article215_except_directness": true,
    "robust_protection_no_lower_effectiveness_evidence": true
  },
  "qualification_reference": "SYN-future-closing-qualified"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### simplified_single_segment_mitigation

```python
solvency2.reinsurance.simplified_single_segment_mitigation(cat_hyp: float, cat_without: float, premium_hyp: float, premium_without: float, sigma: float, recoverables: float, *, single_segment: bool | None, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Literal111a quadratic formula; preserve signed differences, no subfloors.

'hyp' is the scenario without the arrangement. Despite its source label,
'without' denotes the ordinary capital/volume defined in111a(b/e).
Recoverables are the qualified best estimate plus corresponding receivables.
Segment sigma follows117(3)/148(3), not total premium/reserve sigma.

Output unit: `context currency`. Sources: `DR:article-111a`, `DR:article-196`, `DR:article-88`.

Fixed example: `simpl-close-baseline-mitigation-signed`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simpl-close-baseline-mitigation-signed')
context = replace(base, **case.get('context', {}))
result = s2.simplified_single_segment_mitigation(**case['kwargs'], context=context)
# Independent expected value: 3.6742346141747673
```

Example input (JSON):

```json
{
  "cat_hyp": 7,
  "cat_without": 10,
  "premium_hyp": 20,
  "premium_without": 15,
  "sigma": 0.1,
  "recoverables": 5,
  "single_segment": true,
  "eligibility_reference": "SYN-88-single-II-segment",
  "valuation_reference": "SYN-111a-bases"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### reinsurance_recoverables_from_net

```python
solvency2.reinsurance.reinsurance_recoverables_from_net(gross_best_estimate: float, unadjusted_net_best_estimate: float, *, proportionality_satisfied: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Article57 signed gross-minus-net difference BEFORE expected default loss.

The externally qualified net BE is based on homogeneous groups, each with
at most one treaty/SPV unless homogeneous risks are transferred. Both BEs
share scope/date/basis. Neither supplied BE includes the counterparty loss
adjustment; apply the separate default-adjustment component afterwards.

Output unit: `context currency`. Sources: `DR:article-56`, `DR:article-57`.

Fixed example: `net-recovery-close-baseline-zero`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'net-recovery-close-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.reinsurance_recoverables_from_net(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "gross_best_estimate": 80,
  "unadjusted_net_best_estimate": 80,
  "proportionality_satisfied": true,
  "qualification_reference": "SYN-56-57-common-basis-homogeneous-treaty"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### reinsurance_adjusted_recoverable

```python
solvency2.reinsurance.reinsurance_adjusted_recoverable(recoverables_before_default: float, expected_default_adjustment: float, *, reconciliation_reference: str, context: solvency2._core.core.Context)
```

Subtract the separately calculated EXPECTED default adjustment exactly once.

Values must already share counterparty/LoB/contract/provision scope, date,
currency and qualified valuation basis. This does not compute PD, reapply
an LGD floor, net gross TP, or choose a deposit/SPV-cap ordering.
A signed negative result is not automatically a recognised asset.

Output unit: `context currency`. Sources: `DIR:article-81`, `DR:article-42:1-3`.

Fixed example: `ri-reconciliation-baseline-zero`. 44 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'ri-reconciliation-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.reinsurance_adjusted_recoverable(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "recoverables_before_default": 0,
  "expected_default_adjustment": 0,
  "reconciliation_reference": "SYN-same-partition-valuation-and-currency-already-qualified-no-deposit-or-spv-adjustment"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### reinsurance_default_loss

```python
solvency2.reinsurance.reinsurance_default_loss(recoverables_before_adjustment: float, estimated_loss: float, *, method: str, valuation_reference: str | None = None, context: solvency2._core.core.Context)
```

Apply the loss-given-default floor or an explicitly evidenced alternative.

The minimum is not a point estimate and is not a probability of default.
This result must not be used as the full expected default adjustment: its
timing, probabilities and segmentation require a separate calculation.

Output unit: `context currency`. Sources: `DR:article-42:4`, `DIR:article-81`.

Fixed example: `future-ri-loss-zero`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-ri-loss-zero')
context = replace(base, **case.get('context', {}))
result = s2.reinsurance_default_loss(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "recoverables_before_adjustment": 0,
  "estimated_loss": 0,
  "method": "standard_floor"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### spv_recoverable_cap

```python
solvency2.reinsurance.spv_recoverable_cap(recoverable: float, aggregate_maximum_exposure: float, *, exposure_reference: str | None = None, context: solvency2._core.core.Context)
```

Cap one SPV's separately valued recoverable at its external aggregate exposure.

Do not substitute collateral or sum unrelated counterparties here. Contract
boundaries, basis risk and the exposure evidence remain external prerequisites.

Output unit: `context currency`. Sources: `DR:article-41:2`.

Fixed example: `future-spv-cap-zero-exposure`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-spv-cap-zero-exposure')
context = replace(base, **case.get('context', {}))
result = s2.spv_recoverable_cap(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "recoverable": 120,
  "aggregate_maximum_exposure": 0,
  "exposure_reference": "SYN-SPV-EXPOSURE"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### reinsurance_recoverable_cashflows

```python
solvency2.reinsurance.reinsurance_recoverable_cashflows(cashflows: Mapping[str, dict], *, partition: Mapping[str, str], runoff_complete: bool, projection_reference: str, curve_reference: str, context: solvency2._core.core.Context)
```

Discount externally selected expected recoveries at their own payment dates.

Signed values remain signed. No gross-claim date substitution, default
adjustment, SPV cap or claim/deposit qualification is performed implicitly.

Output unit: `context currency`. Sources: `DIR:article-81`, `DR:article-41:2`, `DR:article-41:4`.

Fixed example: `future-ri-cashflow-zero`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-ri-cashflow-zero')
context = replace(base, **case.get('context', {}))
result = s2.reinsurance_recoverable_cashflows(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "partition": {
    "counterparty_id": "SYN-REINSURER-A",
    "line_of_business": "SYN-NL-LOB",
    "contract_type": "other_reinsurance",
    "provision_type": "nonlife_claims"
  },
  "runoff_complete": true,
  "projection_reference": "SYN-PROJECTION",
  "curve_reference": "SYN-CURVE",
  "cashflows": {
    "2028-01-30": {
      "expected_recovery": 0,
      "discount_factor": 0.95
    }
  }
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### reinsurance_default_adjustment

```python
solvency2.reinsurance.reinsurance_default_adjustment(cashflows: Mapping[str, dict], *, partition: Mapping[str, str], runoff_complete: bool, projection_reference: str, curve_reference: str, noncollateral_mitigation_included: bool, context: solvency2._core.core.Context, separate_noncollateral_mitigation: Optional[Mapping[str, dict]] = None)
```

PV of already probability-weighted shortfalls; positive result is a deduction.

Payment-date differences may be negative (e.g. delayed receipts), but a
negative total needs review. Default times, PD, litigation and collateral
effects must already be in the external projection: never multiply PD twice.

Output unit: `context currency`. Sources: `DIR:article-81`, `DR:article-42:1-3`.

Fixed example: `future-ri-adjustment-zero`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-ri-adjustment-zero')
context = replace(base, **case.get('context', {}))
result = s2.reinsurance_default_adjustment(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "partition": {
    "counterparty_id": "SYN-REINSURER-A",
    "line_of_business": "SYN-NL-LOB",
    "contract_type": "other_reinsurance",
    "provision_type": "nonlife_claims"
  },
  "runoff_complete": true,
  "projection_reference": "SYN-PROJECTION",
  "curve_reference": "SYN-CURVE",
  "cashflows": {
    "2028-01-30": {
      "expected_shortfall": 0,
      "discount_factor": 0.95
    },
    "2029-01-30": {
      "expected_shortfall": 0,
      "discount_factor": 0.9
    }
  },
  "noncollateral_mitigation_included": false
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### reinsurance_nonlife_allocation

```python
solvency2.reinsurance.reinsurance_nonlife_allocation(payments: Mapping[str, dict], *, target_provision: str, eligibility_reference: str, context: solvency2._core.core.Context)
```

Allocate already eligible payments using their external gross-claims linkage.

False means premium only after prior eligibility under Article 41: it is
not permission to include settled claims, unrelated payments or deposits.
Call separately for each date and homogeneous counterparty/LoB/type slice.

Output unit: `context currency`. Sources: `DR:article-41:4:a-b`.

Fixed example: `future-ri-allocation-zero`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-ri-allocation-zero')
context = replace(base, **case.get('context', {}))
result = s2.reinsurance_nonlife_allocation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "payments": {
    "B": {
      "amount": 0,
      "claim_in_gross_claims_provision": false
    }
  },
  "target_provision": "nonlife_premium",
  "eligibility_reference": "SYN-ART41-QUALIFICATION"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### risk_mitigation_recognition_factor

```python
solvency2.reinsurance.risk_mitigation_recognition_factor(remaining_months: float, conditions: Mapping, *, purpose: str, instrument_kind: str, finite_or_similar: bool | None, replacement: Optional[Mapping] = None, proportional_factor: float | None = None, counterparty_factor: float = 1, residential_guarantee_payment_months: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Full, excluded, or externally qualified time-proportionate recognition.

Proportional_factor is required only for a qualified short contract without
valid209(3) replacement. Its exposure-dependent time basis is external.
Finite/similar arrangements are excluded from volume/USP even if209 passes.
Scenario valuation must already reflect only the actually transferred risk;
this factor is NOT applied blindly to recoverables, LGD or capital amounts.
counterparty_factor may bind the separately calculated211 haircut. Default1
explicitly declares full counterparty recognition, never verifies it.
Optional residential mortgage guarantee payment window implements only
future215(c)(iii)/(d); all other guarantee criteria remain in qualification.

Output unit: `factor`. Sources: `DR:article-208`, `DR:article-209`, `DR:article-211`.

Fixed example: `closing-rules-baseline-finite-usp`. 42 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'closing-rules-baseline-finite-usp')
context = replace(base, **case.get('context', {}))
result = s2.risk_mitigation_recognition_factor(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "remaining_months": 12,
  "conditions": {
    "legal_enforceability": true,
    "effectiveness_actions": true,
    "ongoing_monitoring": true,
    "direct_claim": true,
    "no_double_count": true,
    "other_section10_conditions": true
  },
  "purpose": "usp",
  "instrument_kind": "reinsurance",
  "finite_or_similar": true,
  "qualification_reference": "SYN-qualified-208-209-no-legal-certification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### reinsurance_counterparty_recognition_factor

```python
solvency2.reinsurance.reinsurance_counterparty_recognition_factor(counterparty_type: str, coverage_ratio: float | None, *, conditions: Mapping, months_since_breach: float | None = None, credit_quality_step: int | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Prescribed211 eligibility/haircut; not PD, LGD or recoverable valuation.

Coverage is SCR/local-equivalent solvency coverage for the insurer route,
or assets/equivalent eligible amount divided by aggregate maximum SPV
exposure. Solvency dates, equivalence, legal status and credible restoration
evidence are external. Months are completed regulatory calendar periods;
at the expiry of6/3months an unresolved shortfall receives zero recognition.
Non-equivalent insurers use the separate CQS route, not an invented SCR.

Output unit: `factor`. Sources: `DR:article-211`.

Fixed example: `counterparty-close-baseline-spv-two`. 36 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'counterparty-close-baseline-spv-two')
context = replace(base, **case.get('context', {}))
result = s2.reinsurance_counterparty_recognition_factor(**case['kwargs'], context=context)
# Independent expected value: 0.75
```

Example input (JSON):

```json
{
  "counterparty_type": "spv",
  "coverage_ratio": 0.75,
  "months_since_breach": 2,
  "conditions": {
    "legal_and_equivalence_conditions": true,
    "post_contract_breach": true,
    "mcr_met": true,
    "restoration_expected": true
  },
  "qualification_reference": "SYN-211-qualified-coverage-and-calendar-period"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

## solvency2.market

### equity_stress_amount_2027

```python
solvency2.market.equity_stress_amount_2027(equity_value: float, shock: float, *, short_position: bool, losses_can_exceed_investment: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply an externally qualified169 factor to the prescribed position basis.

A negative investment with losses beyond the invested amount uses its
absolute value; other negative non-short investments have a zero stress
basis, not a zero balance-sheet value. Short pricing is deliberately not
inferred from a signed value or from the absolute-value exception.

Output unit: `context currency`. Sources: `DR:article-169:5`.

Fixed example: `equity-position-zero`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'equity-position-zero')
context = replace(base, **case.get('context', {}))
result = s2.equity_stress_amount_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "equity_value": 0,
  "shock": 0.39,
  "short_position": false,
  "losses_can_exceed_investment": true,
  "qualification_reference": "SYN-Art75-169-investment-liability-not-short"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### captive_interest_duration

```python
solvency2.market.captive_interest_duration(band: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Look up an explicitly qualified lettered band; do not invent boundary rules.

Output unit: `years`. Sources: `DR:article-103:4`.

Fixed example: `captive-interest-baseline-duration-a`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'captive-interest-baseline-duration-a')
context = replace(base, **case.get('context', {}))
result = s2.captive_interest_duration(**case['kwargs'], context=context)
# Independent expected value: 0.5
```

Example input (JSON):

```json
{
  "band": "a",
  "qualification_reference": "SYN-band"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### captive_interest_currency

```python
solvency2.market.captive_interest_currency(assets: Mapping[str, dict], technical_provisions: Mapping[str, dict], *, direction: str, eligibility_reference: str, valuation_reference: str, stress_reference: str, context: solvency2._core.core.Context)
```

Evaluate one currency's literal asset-minus-BE formula for a declared scenario.

Relative stresses, rate/duration consistency and eligibility are externally
qualified. Signed inputs are preserved: there is no hidden down-direction
sign flip, floor or stress-curve generation (including blocked 2027 curves).
All five asset bands and all 36 Annex I LoBs must be supplied explicitly.

Output unit: `currency`. Sources: `DR:article-103:2`, `DR:article-103:3`, `DR:article-103:4`, `DR:annex-I`.

Fixed example: `captive-interest-baseline-zero`. 46 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'captive-interest-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.captive_interest_currency(**case['kwargs'], context=context)
# Independent expected value: 0
```

Inspect `case['kwargs']` for the complete nested input mapping (kept in the bundled dataset rather than duplicated here).

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### assigned_credit_eligibility_screen

```python
solvency2.market.assigned_credit_eligibility_screen(issuer_financials: Mapping, yield_inputs: Mapping, conditions: Mapping, *, target_cqs: str, qualification_reference: str, context: solvency2._core.core.Context, assessment: Optional[Mapping] = None)
```

Return eligibility for the CHOSEN route, never an internally modelled CQS.

Route3 excludes already assigned176a(1)-CQS2 instruments, not every instrument
that might hypothetically qualify for2. Choice and substantive assessments
are explicit external inputs. Existing numeric screens remain authoritative
for their limited arithmetic and profile-specific analyst overrides.

Output unit: `indicator`. Sources: `DR:article-176a:1-9`.

Fixed example: `assigned-credit-eligibility-baseline-financial-fails`. 126 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'assigned-credit-eligibility-baseline-financial-fails')
context = replace(base, **case.get('context', {}))
result = s2.assigned_credit_eligibility_screen(**case['kwargs'], context=context)
# Independent expected value: 0
```

Inspect `case['kwargs']` for the complete nested input mapping (kept in the bundled dataset rather than duplicated here).

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### lookthrough_exposure_amount

```python
solvency2.market.lookthrough_exposure_amount(funds: Mapping, holdings: Mapping, *, exposure_id: str, complete_scope: bool | None, basis_reference: str, context: solvency2._core.core.Context)
```

Sum one underlying exposure across all qualified direct/indirect fund paths.

Factors are supplied linear multipliers, NOT inferred ownership fractions.
Signed/leverage inputs remain externally qualified; no normalisation, NAV
solving, asset classification, fallback completion or risk-charge netting.
Kahn traversal avoids recursion limits and exponential path enumeration.

Output unit: `context currency`. Sources: `DR:article-84:1-2`, `LOOKTHROUGH_GUIDANCE:guideline-2`.

Fixed example: `lookthrough-exposure-baseline-known-zero-position`. 74 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'lookthrough-exposure-baseline-known-zero-position')
context = replace(base, **case.get('context', {}))
result = s2.lookthrough_exposure_amount(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "funds": {
    "A": {
      "positions": {
        "bond": 0,
        "property": 80
      },
      "fund_links": {
        "B": 0.4
      }
    },
    "B": {
      "positions": {
        "bond": 0,
        "property": 20
      },
      "fund_links": {}
    }
  },
  "holdings": {
    "A": 0.5
  },
  "exposure_id": "bond",
  "complete_scope": true,
  "basis_reference": "SYN-complete-linear-lookthrough-same-unit-qualified"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### symmetric_adjustment_average

```python
solvency2.market.symmetric_adjustment_average(daily_indices: Mapping[str, float | None], *, window_months: int, complete_window: bool | None, index_qualified: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Average determined daily levels, not dates, months or carried-forward values.

None declares that no index was determined that day; it is not permission
to hide missing observations. Exact endpoint selection and completeness
remain externally qualified. Never fetch or manufacture market data.

Output unit: `index_level`. Sources: `DR:article-172:2:b`, `DR:article-172:3`.

Fixed example: `symmetric-average-baseline-single`. 72 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'symmetric-average-baseline-single')
context = replace(base, **case.get('context', {}))
result = s2.symmetric_adjustment_average(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "daily_indices": {
    "2024-06-02": 100
  },
  "window_months": 36,
  "complete_window": true,
  "index_qualified": true,
  "qualification_reference": "SYN-qualified-complete-profile-window-and-representative-index"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### coinvestment_numeric_screen

```python
solvency2.market.coinvestment_numeric_screen(revenue_currency_share: float, financial_years, retentions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check strict issuer size/revenue and inclusive retention for EACH security.

Model approvals, contract requirements, CQS/PD mapping, consolidated issuer
scope, fiscal-year selection and EUR conversion remain external. There is
no averaging of retention across securities and no internal credit model.

Output unit: `indicator`. Sources: `DR:article-176c:3:d:e`, `DR:article-176c:4:e`.

Fixed example: `coinvestment-baseline-employee-route`. 60 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'coinvestment-baseline-employee-route')
context = replace(base, **case.get('context', {}))
result = s2.coinvestment_numeric_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "revenue_currency_share": 0.51,
  "financial_years": [
    {
      "turnover_eur": 0,
      "balance_sheet_total_eur": 0,
      "employees": 51
    },
    {
      "turnover_eur": 0,
      "balance_sheet_total_eur": 0,
      "employees": 51
    },
    {
      "turnover_eur": 0,
      "balance_sheet_total_eur": 0,
      "employees": 51
    }
  ],
  "retentions": {
    "bond": {
      "nominal_value": 100,
      "retained_nominal_value": 20
    },
    "loan": {
      "nominal_value": 50,
      "retained_nominal_value": 10
    }
  },
  "qualification_reference": "SYN-complete-qualified176c-numeric-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### unlisted_equity_beta

```python
solvency2.market.unlisted_equity_beta(gross_margin_mean: float, debt: float, cashflow_mean: float, equity_return_mean: float, *, formula_units_qualified: bool | None, input_basis_reference: str, context: solvency2._core.core.Context)
```

Literal formula; never infer percentage-point/fraction scaling of GM/ROCE.

The archived DE definitions do not explicitly resolve that scaling. Means,
accounting equity definition and formula-native units need external review.
Debt/CFO is signed; no regulatory beta floor/cap is added.

Output unit: `beta`. Sources: `DR:article-168a:2`.

Fixed example: `unlisted-equity-baseline-beta-intercept`. 26 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'unlisted-equity-baseline-beta-intercept')
context = replace(base, **case.get('context', {}))
result = s2.unlisted_equity_beta(**case['kwargs'], context=context)
# Independent expected value: 0.9478
```

Example input (JSON):

```json
{
  "gross_margin_mean": 0,
  "debt": 0,
  "cashflow_mean": 100,
  "equity_return_mean": 0,
  "formula_units_qualified": true,
  "input_basis_reference": "SYN-formula-native-inputs-not-percentage-inference"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### unlisted_equity_portfolio_screen

```python
solvency2.market.unlisted_equity_portfolio_screen(investments: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check all supplied issuers; book weights differ from concentration values.

Input completeness, company consolidation, fiscal periods, FX conversion and
beta methodology are externally qualified. A failed condition yields0, an
unresolved condition raises REVIEW_REQUIRED instead of being treated asFalse.

Output unit: `indicator`. Sources: `DR:article-168a:1`, `DR:article-168a:2`.

Fixed example: `unlisted-equity-baseline-portfolio-negative-beta`. 72 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'unlisted-equity-baseline-portfolio-negative-beta')
context = replace(base, **case.get('context', {}))
result = s2.unlisted_equity_portfolio_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Inspect `case['kwargs']` for the complete nested input mapping (kept in the bundled dataset rather than duplicated here).

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### assigned_credit_issuer_financial_screen

```python
solvency2.market.assigned_credit_issuer_financial_screen(financial_years: list, latest_financials: Mapping, eligible_currency_revenue_share: float, years_without_credit_event: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Screen seven numeric issuer criteria on qualified EUR financial values.

Rows are oldest to newest, consecutive completed financial years. All
supplied rows are validated; only the latest prescribed windows are used.
EUR inputs remain EUR even if Context.currency differs. Definitions,
chronology, latest-value alignment and currency-revenue scope are external.
A pass does not satisfy other Article176a conditions or assign a CQS.

Output unit: `indicator`. Sources: `DR:article-176a:3:g:iii-ix`.

Fixed example: `assigned-credit-baseline-one-small-year`. 52 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'assigned-credit-baseline-one-small-year')
context = replace(base, **case.get('context', {}))
result = s2.assigned_credit_issuer_financial_screen(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "financial_years": [
    {
      "revenue_eur": 0,
      "balance_sheet_eur": 0,
      "employees": 0,
      "ebitda_eur": 65,
      "free_cashflow_eur": 10
    },
    {
      "revenue_eur": 0,
      "balance_sheet_eur": 0,
      "employees": 0,
      "ebitda_eur": 65,
      "free_cashflow_eur": 10
    },
    {
      "revenue_eur": 0,
      "balance_sheet_eur": 0,
      "employees": 0,
      "ebitda_eur": 65,
      "free_cashflow_eur": 10
    },
    {
      "revenue_eur": 0,
      "balance_sheet_eur": 13000000,
      "employees": 0,
      "ebitda_eur": 65,
      "free_cashflow_eur": 10
    },
    {
      "revenue_eur": 0,
      "balance_sheet_eur": 0,
      "employees": 51,
      "ebitda_eur": 65,
      "free_cashflow_eur": 10
    }
  ],
  "latest_financials": {
    "total_debt_eur": 65,
    "interest_expense_eur": 10,
    "net_debt_eur": 150,
    "equity_eur": 100
  },
  "eligible_currency_revenue_share": 0.6,
  "years_without_credit_event": 10,
  "qualification_reference": "SYN-176a-qualified-consecutive-years-latest-values-and-currency-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### assigned_credit_yield_screen

```python
solvency2.market.assigned_credit_yield_screen(yield_observations: Mapping, index_yields: Mapping, *, current_issue_id: str, target_cqs: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Check every qualified issue against both prescribed yield ceilings.

Index keys are 2/4 or 3/4, not sorted by observed yield. All rates are
absolute decimal rates, allowing negative yields. Complete comparable own
issues, issue-date indices, maturity/currency and any adjustments under
paragraphs8/9 must be supplied and qualified externally.

Output unit: `indicator`. Sources: `DR:article-176a:4-9`.

Fixed example: `assigned-credit-baseline-yield-not-capped-at-one`. 32 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'assigned-credit-baseline-yield-not-capped-at-one')
context = replace(base, **case.get('context', {}))
result = s2.assigned_credit_yield_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "yield_observations": {
    "current": 2
  },
  "index_yields": {
    "2": 2,
    "4": 4
  },
  "current_issue_id": "current",
  "target_cqs": "2",
  "qualification_reference": "SYN-qualified-comparable-complete-issues-indices-adjustments-and-dates"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### infrastructure_corporate_eligibility_screen

```python
solvency2.market.infrastructure_corporate_eligibility_screen(conditions: Mapping, *, instrument: str, revenue_route: str, many_users: bool, rating_available: bool, qualification_reference: str, credit_quality_step: str | None = None, operating_years: float | None = None, history_basis: str | None = None, context: solvency2._core.core.Context)
```

Screen declared corporate criteria with conditional controls and numbers.

The caller qualifies the infrastructure majority, EEA/OECD location,
revenue pattern and (where needed) offtaker. No percentage for a 'clear
majority' or numeric interpretation of Article164a(2)biii is invented.
Corporate CQS0..3 in Article164b(7) is distinct and explicit.

Output unit: `indicator`. Sources: `DR:article-164b`, `DR:article-164a:2`.

Fixed example: `infrastructure-corporate-baseline-cqs-0`. 90 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'infrastructure-corporate-baseline-cqs-0')
context = replace(base, **case.get('context', {}))
result = s2.infrastructure_corporate_eligibility_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "infrastructure_majority_eea_oecd": true,
    "revenue_pattern_qualified": true,
    "offtaker_164a_2b_qualified": true,
    "revenue_diversified": true,
    "hold_to_maturity_demonstrated": true
  },
  "instrument": "debt",
  "revenue_route": "volume_price",
  "many_users": false,
  "rating_available": true,
  "qualification_reference": "SYN-qualified-infrastructure-corporate",
  "credit_quality_step": "0"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### infrastructure_project_eligibility_screen

```python
solvency2.market.infrastructure_project_eligibility_screen(conditions: Mapping, *, investment_kind: str, revenue_route: str, many_users: bool, qualification_reference: str, security_route: str | None = None, alternative_security_mechanisms: list[str] | None = None, in_construction: bool | None = None, construction_risk: bool | None = None, material_operational_risk: bool | None = None, context: solvency2._core.core.Context)
```

Apply only the declared, branch-specific project prerequisites.

Equity and unrated debt carry the additional paragraph1(f) criteria.
Instrument rating availability is externally qualified, not inferred from
a corporate rating. Revenue/offtaker/stress/financial assessments remain
external; a successful screen does not select a reduced capital factor.

Output unit: `indicator`. Sources: `DR:article-164a:1:2`.

Fixed example: `infrastructure-project-baseline-rated-debt`. 166 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'infrastructure-project-baseline-rated-debt')
context = replace(base, **case.get('context', {}))
result = s2.infrastructure_project_eligibility_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "stressed_cashflow_sufficiency": true,
    "revenue_pattern_qualified": true,
    "high_investor_protection": true,
    "contingency_working_capital": true,
    "debt_security_all_assets": true,
    "debt_cashflow_restricted": true,
    "debt_adverse_activities_restricted": true,
    "hold_to_maturity_demonstrated": true
  },
  "investment_kind": "rated_debt",
  "revenue_route": "return_regulated",
  "many_users": true,
  "qualification_reference": "SYN-DR164a-project-classification-and-substantive-evidence",
  "security_route": "all_assets_contracts"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### simplified_bond_spread_stress

```python
solvency2.market.simplified_bond_spread_stress(modified_duration: float, *, credit_quality_step: str, eligibility_reference: str, context: solvency2._core.core.Context)
```

DR104 factor: rated values have no invented cap; only unrated is capped.

Output unit: `ratio`. Sources: `DR:article-104:1-3`.

Fixed example: `simplified-market-baseline-slope-0`. 26 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simplified-market-baseline-slope-0')
context = replace(base, **case.get('context', {}))
result = s2.simplified_bond_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0.009
```

Example input (JSON):

```json
{
  "modified_duration": 1,
  "credit_quality_step": "0",
  "eligibility_reference": "SYN-88"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### simplified_bond_spread_risk

```python
solvency2.market.simplified_bond_spread_risk(buckets: Mapping[str, dict], liability_change: float, *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Sum qualified bucket losses plus signed, externally valued DeltaLiab.

Amount weighting is algebraically identical to MV times portfolio shares.
Fractions avoid unnecessary intermediate overflow and cancellation. No
options/guarantee model, floor or general eligibility approval is inferred.

Output unit: `context currency`. Sources: `DR:article-104:1-3`.

Fixed example: `simplified-market-baseline-empty-book`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simplified-market-baseline-empty-book')
context = replace(base, **case.get('context', {}))
result = s2.simplified_bond_spread_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "buckets": {
    "0": {
      "market_value": 0,
      "modified_duration": 0
    },
    "1": {
      "market_value": 0,
      "modified_duration": 0
    },
    "2": {
      "market_value": 0,
      "modified_duration": 0
    },
    "3": {
      "market_value": 0,
      "modified_duration": 0
    },
    "4": {
      "market_value": 0,
      "modified_duration": 0
    },
    "5": {
      "market_value": 0,
      "modified_duration": 0
    },
    "6": {
      "market_value": 0,
      "modified_duration": 0
    },
    "unrated": {
      "market_value": 0,
      "modified_duration": 0
    }
  },
  "liability_change": 0,
  "eligibility_reference": "SYN",
  "valuation_reference": "SYN"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### unrated_bond_simplification_conditions

```python
solvency2.market.unrated_bond_simplification_conditions(rated_share: float, conditions: Mapping[str, bool], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check the inclusive rated-portfolio share and qualified bond facts.

The portfolio denominator excludes Article180(2-16) positions. Classification
against the referenced reporting definitions and liability cover is external;
a missing rating field is never treated as evidence of an unrated bond.

Output unit: `indicator`. Sources: `DR:article-105a`.

Fixed example: `proportionality-baseline-bond-all-rated`. 24 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'proportionality-baseline-bond-all-rated')
context = replace(base, **case.get('context', {}))
result = s2.unrated_bond_simplification_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "rated_share": 1,
  "conditions": {
    "article88_satisfied": true,
    "outside_article180_2_16": true,
    "unrated": true,
    "fixed_redemption_regular_interest": true,
    "not_structured_or_collateralised": true,
    "not_covering_excluded_liabilities": true
  },
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### lookthrough_fallback_conditions

```python
solvency2.market.lookthrough_fallback_conditions(conditions: Mapping[str, bool], *, allocation_basis: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Test target-first fallback conditions, not infer a fund's asset allocation.

Only externally qualified collective/fund-form investments are in scope.
Prudence and any data-grouping cap must be checked separately.

Output unit: `indicator`. Sources: `DR:article-84:3`, `DR:article-88`.

Fixed example: `lookthrough-baseline-target`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'lookthrough-baseline-target')
context = replace(base, **case.get('context', {}))
result = s2.lookthrough_fallback_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "lookthrough_unavailable": true,
    "article88_satisfied": true,
    "target_allocation_known": true,
    "managed_according_to_allocation": true,
    "no_material_short_term_fluctuations": true
  },
  "allocation_basis": "target",
  "qualification_reference": "SYN-qualified-fund-and-excluded-UL-scope"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### lookthrough_grouping_limit

```python
solvency2.market.lookthrough_grouping_limit(grouped_assets_in_scope: float, total_assets_in_scope: float, *, article84_3a_scope_qualified: bool, prudent_grouping: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Check an inclusive cap on externally scope-adjusted grouping amounts.

Article84(3a) exclusion/classification and prudent risk grouping are external;
zero/zero means only the inequality holds, not that a method is approved.

Output unit: `indicator`. Sources: `DR:article-84:3`, `DR:article-84:3a`.

Fixed example: `lookthrough-baseline-group-zero`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'lookthrough-baseline-group-zero')
context = replace(base, **case.get('context', {}))
result = s2.lookthrough_grouping_limit(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "grouped_assets_in_scope": 0,
  "total_assets_in_scope": 0,
  "article84_3a_scope_qualified": true,
  "prudent_grouping": true,
  "qualification_reference": "SYN-qualified-fund-and-excluded-UL-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### interest_down_stress_2027

```python
solvency2.market.interest_down_stress_2027(rate: float, maturity: float, first_smoothing_point: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Literal downward stress only at/before an externally qualified first smoothing point.

Output unit: `annual_rate`. Sources: `DR:article-167:1-2`.

Fixed example: `interest-down-2027-rate-1`. 11 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'interest-down-2027-rate-1')
context = replace(base, **case.get('context', {}))
result = s2.interest_down_stress_2027(**case['kwargs'], context=context)
# Independent expected value: -0.0116
```

Example input (JSON):

```json
{
  "rate": 0,
  "maturity": 1,
  "first_smoothing_point": 20,
  "qualification_reference": "SYN-qualified-currency-FSP-and-basic-curve"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### interest_relative_factor_2027

```python
solvency2.market.interest_relative_factor_2027(maturity: float, direction: str, *, context: solvency2._core.core.Context)
```

Interpolate s using its own90year tail, not the additive60year tail.

Output unit: `ratio`. Sources: `DR:article-166:2`, `DR:article-167:2`.

Fixed example: `interest-original-row-up-1-interest_relative_factor_2027`. 120 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'interest-original-row-up-1-interest_relative_factor_2027')
context = replace(base, **case.get('context', {}))
result = s2.interest_relative_factor_2027(**case['kwargs'], context=context)
# Independent expected value: 0.61
```

Example input (JSON):

```json
{
  "maturity": 1,
  "direction": "up"
}
```

### interest_additive_shift_2027

```python
solvency2.market.interest_additive_shift_2027(maturity: float, direction: str, *, context: solvency2._core.core.Context)
```

Return the nonnegative b magnitude; its application sign belongs to the scenario.

Output unit: `annual_rate`. Sources: `DR:article-166:2`, `DR:article-167:2`.

Fixed example: `interest-original-row-up-1-interest_additive_shift_2027`. 120 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'interest-original-row-up-1-interest_additive_shift_2027')
context = replace(base, **case.get('context', {}))
result = s2.interest_additive_shift_2027(**case['kwargs'], context=context)
# Independent expected value: 0.0214
```

Example input (JSON):

```json
{
  "maturity": 1,
  "direction": "up"
}
```

### interest_down_floor_2027

```python
solvency2.market.interest_down_floor_2027(maturity: float, *, context: solvency2._core.core.Context)
```

Published floor from1year; subannual ambiguity is not filled by extrapolation.

Output unit: `annual_rate`. Sources: `DR:article-167:1`.

Fixed example: `interest-floor-2027-1`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'interest-floor-2027-1')
context = replace(base, **case.get('context', {}))
result = s2.interest_down_floor_2027(**case['kwargs'], context=context)
# Independent expected value: -0.0125
```

Example input (JSON):

```json
{
  "maturity": 1
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### interest_ufr_stress_2027

```python
solvency2.market.interest_ufr_stress_2027(ufr: float, direction: str, *, context: solvency2._core.core.Context)
```

Shift an externally supplied UFR, without constructing a stressed extrapolation.

Output unit: `annual_rate`. Sources: `DR:article-166:2a:a`, `DR:article-167:2a:a`.

Fixed example: `interest-ufr-2027-up`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'interest-ufr-2027-up')
context = replace(base, **case.get('context', {}))
result = s2.interest_ufr_stress_2027(**case['kwargs'], context=context)
# Independent expected value: 0.0365
```

Example input (JSON):

```json
{
  "ufr": 0.035,
  "direction": "up"
}
```

### interest_scenario_charge

```python
solvency2.market.interest_scenario_charge(gross_by_currency: Mapping, net_by_currency: Mapping, *, valuation_reference: str, tie_break: str | None = None, context: solvency2._core.core.Context)
```

Sum each direction across qualified currency groups before scenario selection.

Future EUR/peg joint scenarios must already be qualified and grouped externally,
with no duplicate exposure. Currency/group keys never trigger automatic merging.

Output unit: `context currency`. Sources: `DR:article-165`, `DR:article-164:3`, `DR:article-206:2`.

Fixed example: `interest-sum-net-down`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'interest-sum-net-down')
context = replace(base, **case.get('context', {}))
result = s2.interest_scenario_charge(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "gross_by_currency": {
    "EUR": {
      "up": 100,
      "down": 20
    },
    "USD": {
      "up": 10,
      "down": 80
    }
  },
  "net_by_currency": {
    "EUR": {
      "up": 10,
      "down": 15
    },
    "USD": {
      "up": 5,
      "down": 35
    }
  },
  "valuation_reference": "SYN-CURRENCY-FDB"
}
```

Reference-tested failure codes: `AMBIGUOUS_SELECTION`. Additional shared validation errors can apply.

### market_risk_from_interest_scenarios

```python
solvency2.market.market_risk_from_interest_scenarios(other_components: Mapping, gross_by_currency: Mapping, net_by_currency: Mapping, *, valuation_reference: str, tie_break: str | None = None, context: solvency2._core.core.Context)
```

Aggregate supplied market submodules, with the source's interest-charge equality rule.

Keys identify externally qualified stress currencies/groups; all monetary inputs are already in context
currency. This function neither values instruments nor certifies completeness.
The selected profile supplies its own matrices, including the2027 interest/spread B coefficient.

Output unit: `context currency`. Sources: `DR:article-164:2-3`, `DR:article-165`, `DR:article-206:2`.

Fixed example: `market-zero`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'market-zero')
context = replace(base, **case.get('context', {}))
result = s2.market_risk_from_interest_scenarios(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "gross_by_currency": {
    "EUR": {
      "up": 0,
      "down": 0
    }
  },
  "net_by_currency": {
    "EUR": {
      "up": 0,
      "down": 0
    }
  },
  "valuation_reference": "SYN",
  "other_components": {
    "equity": 0,
    "property": 0,
    "spread": 0,
    "concentration": 0,
    "currency": 0
  }
}
```

### interest_participation_bof_change

```python
solvency2.market.interest_participation_bof_change(participations: Mapping, *, direction: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Retain gains but exclude losses on Art68-deducted financial holdings.

Signed BOF deltas are externally valued for one up/down scenario and one
consistent gross/net-FDB basis. Apply before full currency-scenario losses,
never subtract the result from an already floored SCR. No pricing or legal
deduction qualification is inferred. The arithmetic is shared with188(6).

Output unit: `context currency`. Sources: `DR:article-166:3`, `DR:article-167:3`.

Fixed example: `interest-participation-baseline-up-empty`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'interest-participation-baseline-up-empty')
context = replace(base, **case.get('context', {}))
result = s2.interest_participation_bof_change(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "participations": {},
  "direction": "up",
  "qualification_reference": "SYN-166-167-financial-holdings-Art68-deductions-and-scenario"
}
```

### bond_spread_stress

```python
solvency2.market.bond_spread_stress(modified_duration: float, *, category: str, classification_reference: str, credit_quality_step: str | None = None, context: solvency2._core.core.Context, assigned_eligibility: collections.abc.Mapping | None = None, coinvestment: collections.abc.Mapping | None = None)
```

Use modified duration, floored at1; floats need externally assessed equivalent fixed duration.

Assigned CQS eligibility and exclusions are external. The published CQS4
jump above20 years is retained, not interpolated away.
The 2027 scope explicitly excludes defaulted and forborne loans; callers
must qualify that scope before supplying a position to this factor API.

Output unit: `ratio`. Sources: `DR:article-176:2-4a`.

Fixed example: `simplified-market-baseline-captive-quality`. 192 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simplified-market-baseline-captive-quality')
context = replace(base, **case.get('context', {}))
result = s2.bond_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0.2
```

Example input (JSON):

```json
{
  "modified_duration": 10,
  "category": "captive",
  "classification_reference": "SYN-88-89"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### secured_bond_spread_stress

```python
solvency2.market.secured_bond_spread_stress(unsecured_stress: float, asset_value: float, risk_adjusted_collateral: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Three collateral branches on an externally qualified Article176(4) shock.

Full coverage is inclusive; equality to the unsecured post-stress value
leaves the original shock unchanged. This does not value collateral.

Output unit: `ratio`. Sources: `DR:article-176:5`.

Fixed example: `future-secured-spread-extreme-1`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-secured-spread-extreme-1')
context = replace(base, **case.get('context', {}))
result = s2.secured_bond_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0.75
```

Example input (JSON):

```json
{
  "unsecured_stress": 1,
  "asset_value": 100,
  "risk_adjusted_collateral": 50,
  "qualification_reference": "SYN"
}
```

### securitisation_spread_stress

```python
solvency2.market.securitisation_spread_stress(modified_duration: float, *, category: str, qualification_reference: str, credit_quality_step: str | None = None, transition: collections.abc.Mapping | None = None, context: solvency2._core.core.Context, imposed_increase_fraction: float | None = None, supervisory_decision_reference: str | None = None)
```

Article178 factors on externally qualified positions; no automatic transition relief.

Paragraph6 literally uses the paragraph3 senior table at CQS5. The unusual
source reference remains explicit, not silently redirected to paragraph4.

Output unit: `ratio`. Sources: `DR:article-178`.

Fixed example: `future-securitisation-residual-na-0`. 341 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-securitisation-residual-na-0')
context = replace(base, **case.get('context', {}))
result = s2.securitisation_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "modified_duration": 0,
  "category": "residual",
  "qualification_reference": "SYN-STS-RATING"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### specific_exposure_spread_stress

```python
solvency2.market.specific_exposure_spread_stress(modified_duration: float, *, category: str, qualification_reference: str, credit_quality_step: str | None = None, qualification: collections.abc.Mapping | None = None, context: solvency2._core.core.Context)
```

Article180 table factors on externally qualified debt, not eligibility or BOF SCR.

Published rounded discontinuities are retained. Insurer MCR breach requires
external confirmation of the paragraph6 first-SFCR applicability condition.

Output unit: `ratio`. Sources: `DR:article-180`, `DR:article-176:2`.

Fixed example: `future-specific-spread-regional_local-none-12`. 256 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-specific-spread-regional_local-none-12')
context = replace(base, **case.get('context', {}))
result = s2.specific_exposure_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0.094
```

Example input (JSON):

```json
{
  "modified_duration": 12,
  "category": "regional_local",
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### insurer_solvency_spread_stress

```python
solvency2.market.insurer_solvency_spread_stress(modified_duration: float, solvency_ratio: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Interpolate stress, not rating, for externally qualified unrated insurers.

Duplicate published 75% knots share CQS5_6. MCR/SFCR eligibility is external.

Output unit: `ratio`. Sources: `DR:article-180:4`, `DR:article-176:2-3`.

Fixed example: `future-insurer-solvency-spread-1-0`. 32 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-insurer-solvency-spread-1-0')
context = replace(base, **case.get('context', {}))
result = s2.insurer_solvency_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0.075
```

Example input (JSON):

```json
{
  "modified_duration": 1,
  "solvency_ratio": 0,
  "qualification_reference": "SYN"
}
```

### matching_fundamental_spread_increase

```python
solvency2.market.matching_fundamental_spread_increase(asset_stress: float, modified_duration: float, *, category: str, qualification_reference: str, credit_quality_step: str | None = None, context: solvency2._core.core.Context)
```

Fundamental-spread increment, not MA/technical-provision revaluation.

Use actual modified duration here, not the floor used to determine the
separately supplied asset shock. The last paragraph overrides CQS3 for
qualified infrastructure investments and infrastructure corporate assets.

Output unit: `annual_rate`. Sources: `DR:article-181:b`.

Fixed example: `future-matching-spread-increase-7`. 24 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-matching-spread-increase-7')
context = replace(base, **case.get('context', {}))
result = s2.matching_fundamental_spread_increase(**case['kwargs'], context=context)
# Independent expected value: 0.02
```

Example input (JSON):

```json
{
  "asset_stress": 0.1,
  "modified_duration": 5,
  "category": "unrated",
  "qualification_reference": "SYN"
}
```

### financial_issuer_spread_stress

```python
solvency2.market.financial_issuer_spread_stress(modified_duration: float, *, category: str, qualification_reference: str, credit_quality_step: str | None = None, solvency_ratio: float | None = None, mcr_compliant: bool | None = None, sfcr_published: bool | None = None, context: solvency2._core.core.Context)
```

Route insurer and externally qualified financial-issuer factors, not legal eligibility.

After first SFCR, MCR breach takes precedence even over an available rating.
Before SFCR, compliance and current solvency inputs are not used/accepted.

Output unit: `ratio`. Sources: `DR:article-180:4-8`.

Fixed example: `future-financial-issuer-spread-9`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-financial-issuer-spread-9')
context = replace(base, **case.get('context', {}))
result = s2.financial_issuer_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0.2527777777777778
```

Example input (JSON):

```json
{
  "modified_duration": 7,
  "category": "unrated_compliant_credit_financial",
  "qualification_reference": "SYN"
}
```

### concentration_asset_loss

```python
solvency2.market.concentration_asset_loss(excess: float, risk_factor: float, *, context: solvency2._core.core.Context)
```

Immediate asset-value loss, explicitly NOT the resulting BOF capital charge.

Output unit: `context currency`. Sources: `DR:article-183:2`.

Fixed example: `future-concentration-core-5`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-core-5')
context = replace(base, **case.get('context', {}))
result = s2.concentration_asset_loss(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "excess": 10,
  "risk_factor": 0
}
```

### concentration_excess

```python
solvency2.market.concentration_excess(exposure: float, assets: float, threshold: float, *, context: solvency2._core.core.Context)
```

Threshold excess on already scoped Assets and zero-factor-adjusted exposure.

Output unit: `context currency`. Sources: `DR:article-184:1`.

Fixed example: `future-concentration-core-3`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-core-3')
context = replace(base, **case.get('context', {}))
result = s2.concentration_excess(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposure": 0,
  "assets": 0,
  "threshold": 0
}
```

### concentration_exposure_sum

```python
solvency2.market.concentration_exposure_sum(exposures: collections.abc.Mapping[str, float], *, grouping_reference: str, context: solvency2._core.core.Context)
```

Sum externally grouped counterparty/single-name exposures, not all Assets.

Output unit: `context currency`. Sources: `DR:article-182:2-3`.

Fixed example: `future-concentration-core-13`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-core-13')
context = replace(base, **case.get('context', {}))
result = s2.concentration_exposure_sum(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposures": {
    "a": 0
  },
  "grouping_reference": "SYN"
}
```

### concentration_risk

```python
solvency2.market.concentration_risk(single_name_charges: collections.abc.Mapping[str, float], *, context: solvency2._core.core.Context)
```

Euclidean norm of already valued single-name BOF charges; not asset losses.

Output unit: `context currency`. Sources: `DR:article-183:1`.

Fixed example: `future-concentration-core-7`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-core-7')
context = replace(base, **case.get('context', {}))
result = s2.concentration_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "single_name_charges": {
    "a": 0
  }
}
```

### concentration_single_name_quality

```python
solvency2.market.concentration_single_name_quality(exposures: collections.abc.Mapping[str, dict], *, grouping_reference: str, context: solvency2._core.core.Context)
```

Ceil value-weighted quality only after aggregation, without epsilon rounding.

Exact arithmetic on validated binary inputs protects integer boundaries and
avoids overflow in weighted products. Input qualities may be fractional.

Output unit: `credit_quality_step`. Sources: `DR:article-182:4`.

Fixed example: `future-concentration-core-9`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-core-9')
context = replace(base, **case.get('context', {}))
result = s2.concentration_single_name_quality(**case['kwargs'], context=context)
# Independent expected value: 4
```

Example input (JSON):

```json
{
  "exposures": {
    "a": {
      "value": 100,
      "quality": 3.82
    }
  },
  "grouping_reference": "SYN"
}
```

### concentration_factor

```python
solvency2.market.concentration_factor(category: str, *, qualification_reference: str, credit_quality_step: str | float | None = None, context: solvency2._core.core.Context)
```

gi selection, not grouping or CT selection; regional CQS2 reference affects gi only.

Output unit: `ratio`. Sources: `DR:article-186:1`, `DR:article-187:2-4`.

Fixed example: `future-concentration_factor-property-none`. 34 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration_factor-property-none')
context = replace(base, **case.get('context', {}))
result = s2.concentration_factor(**case['kwargs'], context=context)
# Independent expected value: 0.12
```

Example input (JSON):

```json
{
  "category": "property",
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### concentration_threshold

```python
solvency2.market.concentration_threshold(category: str, *, qualification_reference: str, credit_quality_step: str | float | None = None, context: solvency2._core.core.Context)
```

CT on externally established single-name quality or qualified special exposure.

Output unit: `ratio`. Sources: `DR:article-185`, `DR:article-187:1-2`.

Fixed example: `future-concentration_threshold-property-none`. 30 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration_threshold-property-none')
context = replace(base, **case.get('context', {}))
result = s2.concentration_threshold(**case['kwargs'], context=context)
# Independent expected value: 0.1
```

Example input (JSON):

```json
{
  "category": "property",
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### concentration_credit_quality

```python
solvency2.market.concentration_credit_quality(category: str, *, qualification_reference: str, credit_quality_step: str | float | None = None, solvency_ratio: float | None = None, mcr_compliant: bool | None = None, sfcr_published: bool | None = None, context: solvency2._core.core.Context)
```

Position quality before single-name weighting/ceiling; eligibility is external.

Here the quality itself is interpolated, unlike Article180 stress-factor
interpolation. MCR/SFCR routing in Article182(6-8) concerns unrated insurers.

Output unit: `credit_quality_step`. Sources: `DR:article-182:5-11`.

Fixed example: `future-concentration-quality-residual`. 53 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-quality-residual')
context = replace(base, **case.get('context', {}))
result = s2.concentration_credit_quality(**case['kwargs'], context=context)
# Independent expected value: 5
```

Example input (JSON):

```json
{
  "category": "residual",
  "qualification_reference": "SYN"
}
```

### concentration_adjusted_exposure

```python
solvency2.market.concentration_adjusted_exposure(exposures: collections.abc.Mapping[str, dict], *, grouping_reference: str, context: solvency2._core.core.Context)
```

Ei excluding zero-gi counterparties; does not alter Assets or quality weights.

Output unit: `context currency`. Sources: `DR:article-184:3`.

Fixed example: `future-concentration-adjusted-zero`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-adjusted-zero')
context = replace(base, **case.get('context', {}))
result = s2.concentration_adjusted_exposure(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposures": {
    "a": {
      "value": 100,
      "risk_factor": 0
    }
  },
  "grouping_reference": "SYN"
}
```

### concentration_assets

```python
solvency2.market.concentration_assets(assets: collections.abc.Mapping[str, dict], *, classification_reference: str, context: solvency2._core.core.Context)
```

Select Assets from externally classified holdings; intragroup needs all five flags.

Exclusions are not inferred from names. Intragroup category itself asserts
group membership externally; a failed exclusion condition retains the asset.

Output unit: `context currency`. Sources: `DR:article-184:2`.

Fixed example: `future-concentration-assets-all-excluded`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-concentration-assets-all-excluded')
context = replace(base, **case.get('context', {}))
result = s2.concentration_assets(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "assets": {
    "a": {
      "value": 10,
      "category": "deferred_tax_asset"
    }
  },
  "classification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### currency_rate_stress

```python
solvency2.market.currency_rate_stress(exchange_rate: float, *, direction: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Stress local currency per one foreign unit, not its reciprocal or a BOF amount.

Output unit: `exchange_rate`. Sources: `DR:article-188:3-4`.

Fixed example: `currency-rate-1-up`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'currency-rate-1-up')
context = replace(base, **case.get('context', {}))
result = s2.currency_rate_stress(**case['kwargs'], context=context)
# Independent expected value: 1.25
```

Example input (JSON):

```json
{
  "exchange_rate": 1,
  "direction": "up",
  "valuation_reference": "SYN"
}
```

### currency_risk

```python
solvency2.market.currency_risk(currency_charges: collections.abc.Mapping[str, float], *, classification_reference: str, context: solvency2._core.core.Context)
```

Sum already net-scenario-selected gross charges, all valued in Context.currency.

Output unit: `context currency`. Sources: `DR:article-188:1-2`, `DR:article-188:7`.

Fixed example: `currency-sum-zero`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'currency-sum-zero')
context = replace(base, **case.get('context', {}))
result = s2.currency_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "currency_charges": {
    "USD": 0
  },
  "classification_reference": "SYN"
}
```

### currency_scenario_charge

```python
solvency2.market.currency_scenario_charge(gross_losses: collections.abc.Mapping, net_losses: collections.abc.Mapping, *, valuation_reference: str, tie_break: str | None = None, context: solvency2._core.core.Context)
```

One currency: select gross charge by the largest externally valued net-FDB loss.

Each mapping contains exactly up/down in the context's local currency.
This does not value exposures or approve their currency classification.

Output unit: `context currency`. Sources: `DR:article-188:2:7`, `DR:article-206:2`.

Fixed example: `currency-select-baseline-equal`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'currency-select-baseline-equal')
context = replace(base, **case.get('context', {}))
result = s2.currency_scenario_charge(**case['kwargs'], context=context)
# Independent expected value: 5
```

Example input (JSON):

```json
{
  "gross_losses": {
    "up": 5,
    "down": 5
  },
  "net_losses": {
    "up": 3,
    "down": 3
  },
  "tie_break": null,
  "valuation_reference": "SYN"
}
```

Reference-tested failure codes: `AMBIGUOUS_SELECTION`. Additional shared validation errors can apply.

### currency_participation_bof_change

```python
solvency2.market.currency_participation_bof_change(participations: collections.abc.Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Signed FX BOF change: deducted holdings contribute gains but not losses.

Inputs are externally valued BOF deltas for each holding's Art68-deducted
and non-deducted parts, not market values or deduction amounts. Apply the
positive-part rule per holding before summation; do not net excluded losses.

Output unit: `context currency`. Sources: `DR:article-188:6`.

Fixed example: `currency-participation-baseline-empty`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'currency-participation-baseline-empty')
context = replace(base, **case.get('context', {}))
result = s2.currency_participation_bof_change(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "participations": {},
  "qualification_reference": "SYN-qualified-Art68-and-FX-scenario"
}
```

### currency_peg_factor

```python
solvency2.market.currency_peg_factor(foreign_currency: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Historical document-profile pair factor, not confirmation of a current currency peg.

All 15 unordered pairs are explicit original values, not cross-rate-derived
estimates. External evidence must establish date-specific applicability.

Output unit: `ratio`. Sources: `DR:article-188:5`, `ITS2015_2017:article-1-2`.

Fixed example: `currency-peg-factor-EUR-DKK`. 30 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'currency-peg-factor-EUR-DKK')
context = replace(base, **case.get('context', {}))
result = s2.currency_peg_factor(**case['kwargs'], context=context)
# Independent expected value: 0.0039
```

Example input (JSON):

```json
{
  "foreign_currency": "DKK",
  "qualification_reference": "SYN"
}
```

### currency_peg_rate_stress

```python
solvency2.market.currency_peg_rate_stress(exchange_rate: float, foreign_currency: str, *, direction: str, qualification_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Apply a qualified original peg factor to local currency per one foreign unit.

Output unit: `exchange_rate`. Sources: `DR:article-188:3-5`, `ITS2015_2017:article-1-2`.

Fixed example: `currency-peg-rate-EUR-DKK-up`. 60 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'currency-peg-rate-EUR-DKK-up')
context = replace(base, **case.get('context', {}))
result = s2.currency_peg_rate_stress(**case['kwargs'], context=context)
# Independent expected value: 1.0039
```

Example input (JSON):

```json
{
  "exchange_rate": 1,
  "foreign_currency": "DKK",
  "direction": "up",
  "qualification_reference": "SYN",
  "valuation_reference": "SYN"
}
```

### guaranteed_sts_securitisation_spread_stress

```python
solvency2.market.guaranteed_sts_securitisation_spread_stress(conditions: collections.abc.Mapping[str, bool], *, qualification_reference: str, transition: collections.abc.Mapping[str, bool] | None = None, context: solvency2._core.core.Context)
```

Qualified Article180(10)/(10a) factor; historical name retained for callers.

The 2027 text no longer separately names STS; CRR243 compliance remains
required and externally qualified, not inferred from a non-STS declaration.
Paragraph10a requires external pre-2019 issue and exact 2018-rule assessment,
not a current type label or an engine-generated historical classification.

Output unit: `ratio`. Sources: `DR:article-180:10`.

Fixed example: `spread-zero-baseline-transition-eligible`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'spread-zero-baseline-transition-eligible')
context = replace(base, **case.get('context', {}))
result = s2.guaranteed_sts_securitisation_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "conditions": {},
  "transition": {
    "issued_before_2019": true,
    "qualified_under_2018_article180_10": true
  },
  "qualification_reference": "SYN-issue-date-and-2018-rule-classification"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### insured_deposit_concentration_factor

```python
solvency2.market.insured_deposit_concentration_factor(conditions: collections.abc.Mapping[str, bool], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Deposit guarantee concentration gi only; no default/spread risk exemption.

Output unit: `ratio`. Sources: `DR:article-187:5`.

Fixed example: `future-deposit-zero-qualified`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-deposit-zero-qualified')
context = replace(base, **case.get('context', {}))
result = s2.insured_deposit_concentration_factor(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "conditions": {
    "fully_eu_deposit_guaranteed": true,
    "unrestricted": true,
    "no_double_count": true
  },
  "qualification_reference": "SYN"
}
```

### public_exposure_zero_factor

```python
solvency2.market.public_exposure_zero_factor(category: str, conditions: collections.abc.Mapping[str, bool], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Shared public-factor rule; Art180 debt scope and Art187 scope remain distinct.

Public-body/list classification and underlying guarantee assessment are
external evidence, not conclusions drawn from these supplied booleans.
The future-only308b(12) category concerns the position's inception, not
merely the security's issue date; it does not extend public guarantees.

Output unit: `ratio`. Sources: `DR:article-180:2`, `DR:article-187:3`.

Fixed example: `future-public-zero-ecb`. 19 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-public-zero-ecb')
context = replace(base, **case.get('context', {}))
result = s2.public_exposure_zero_factor(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "category": "ecb",
  "conditions": {},
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### partial_public_guarantee_zero_amount_2027

```python
solvency2.market.partial_public_guarantee_zero_amount_2027(positions: collections.abc.Mapping[str, dict], *, category: str, first_loss_cover: float, guarantee_value: float, conditions: collections.abc.Mapping[str, bool], qualification_reference: str, allocation_reference: str, context: solvency2._core.core.Context)
```

Validate explicit zero-treatment allocation, not guarantee pricing or capital.

Nominal first-loss coverage and the externally determined guarantee value
are distinct inputs. Pool allocation is chosen by the analyst, never here.
Article215(f) payment coverage remains part of external qualification.

Output unit: `context currency`. Sources: `DR:article-180:2:subparagraphs-3-5`.

Fixed example: `partial-public-guarantee-single`. 15 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'partial-public-guarantee-single')
context = replace(base, **case.get('context', {}))
result = s2.partial_public_guarantee_zero_amount_2027(**case['kwargs'], context=context)
# Independent expected value: 5
```

Example input (JSON):

```json
{
  "positions": {
    "bond": {
      "nominal": 100,
      "value": 90,
      "zero_amount": 5
    }
  },
  "category": "single",
  "first_loss_cover": 5,
  "guarantee_value": 5,
  "conditions": {
    "guarantor_qualifies_under_a_to_d": true,
    "unconditional": true,
    "irrevocable": true,
    "first_loss_guarantee": true,
    "article215_compliant": true
  },
  "qualification_reference": "SYN-Art215-including-f",
  "allocation_reference": "SYN-explicit"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### credit_derivative_scenario_charge

```python
solvency2.market.credit_derivative_scenario_charge(gross_losses: Optional[Mapping], net_losses: Optional[Mapping], *, valuation_reference: str, tie_break: str | None = None, public_underlying: Optional[Mapping] = None, hedge_exemption: Optional[Mapping] = None, context: solvency2._core.core.Context)
```

Select gross credit-derivative charge by maximal net-FDB scenario loss.

Widening/tightening BOF valuations and Article179(3) hedge exclusions must
be qualified externally. This is neither derivative pricing nor hedge approval.
Article180(9) can instead use an explicitly qualified public debt underlying;
no partial guarantee, other underlying or missing scenarios implies zero.

Output unit: `context currency`. Sources: `DR:article-179:1:4`, `DR:article-206:2`.

Fixed example: `credit-derivative-select-baseline-equal`. 32 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'credit-derivative-select-baseline-equal')
context = replace(base, **case.get('context', {}))
result = s2.credit_derivative_scenario_charge(**case['kwargs'], context=context)
# Independent expected value: 4
```

Example input (JSON):

```json
{
  "gross_losses": {
    "widening": 4,
    "tightening": 4
  },
  "net_losses": {
    "widening": 2,
    "tightening": 2
  },
  "valuation_reference": "SYN-gross-net-FDB"
}
```

Reference-tested failure codes: `AMBIGUOUS_SELECTION`, `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### credit_spread_stress

```python
solvency2.market.credit_spread_stress(spread: float, direction: str, *, category: str, qualification_reference: str, credit_quality_step: str | None = None, context: solvency2._core.core.Context)
```

Absolute widening versus relative tightening; hedge exclusions require separate assessment.

Output unit: `annual_rate`. Sources: `DR:article-179:1-2`.

Fixed example: `future-credit-spread-tighten-0`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-credit-spread-tighten-0')
context = replace(base, **case.get('context', {}))
result = s2.credit_spread_stress(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "spread": 0,
  "direction": "tightening",
  "category": "unrated",
  "qualification_reference": "SYN"
}
```

### property_value_stress

```python
solvency2.market.property_value_stress(property_value: float, *, valuation_reference: str, context: solvency2._core.core.Context)
```

Stress an externally identified property asset, not total BOF or property SCR.

Output unit: `context currency`. Sources: `DR:article-174`.

Fixed example: `property-value-0`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'property-value-0')
context = replace(base, **case.get('context', {}))
result = s2.property_value_stress(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "property_value": 0,
  "valuation_reference": "SYN"
}
```

### spread_risk

```python
solvency2.market.spread_risk(bonds: float, securitisation: float, credit_derivatives: float, *, context: solvency2._core.core.Context)
```

Sum three already valued/selected spread submodules; no missing-component defaults.

Output unit: `context currency`. Sources: `DR:article-175`.

Fixed example: `future-spread-sum-zero`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-spread-sum-zero')
context = replace(base, **case.get('context', {}))
result = s2.spread_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "bonds": 0,
  "securitisation": 0,
  "credit_derivatives": 0
}
```

### equity_shock

```python
solvency2.market.equity_shock(category: str, symmetric_adjustment: float, *, duration_based: Optional[Mapping] = None, context: solvency2._core.core.Context, classification: Optional[Mapping] = None)
```

Shock factor with optional qualified168 route checks, never asset valuation.

Without classification, eligibility remains external. Optional route inputs
bind market/fund scope or existing qualification screens to the chosen factor.
Strategic/long-term recognition and own-funds deductions remain separate.

Output unit: `ratio`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `equity-shock-type1-1`. 219 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'equity-shock-type1-1')
context = replace(base, **case.get('context', {}))
result = s2.equity_shock(**case['kwargs'], context=context)
# Independent expected value: 0.39
```

Example input (JSON):

```json
{
  "category": "type1",
  "symmetric_adjustment": 0
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### interest_stress

```python
solvency2.market.interest_stress(rate: float, maturity: float, direction: str, *, context: solvency2._core.core.Context)
```

Stress a basic annual spot rate; linear factor interpolation including endpoints.

Output unit: `annual_rate`. Sources: `DR:article-166`, `DR:article-167`.

Fixed example: `rate-interpolation`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rate-interpolation')
context = replace(base, **case.get('context', {}))
result = s2.interest_stress(**case['kwargs'], context=context)
# Independent expected value: 0.123
```

Example input (JSON):

```json
{
  "rate": 0.1,
  "maturity": 55,
  "direction": "up"
}
```

### symmetric_adjustment

```python
solvency2.market.symmetric_adjustment(current_index: float, average_index: float, *, context: solvency2._core.core.Context)
```

Use an externally qualified daily mean; the selected profile determines its window and cap.

Output unit: `ratio`. Sources: `DR:article-172:2-4`.

Fixed example: `market-2027-sa-50`. 11 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'market-2027-sa-50')
context = replace(base, **case.get('context', {}))
result = s2.symmetric_adjustment(**case['kwargs'], context=context)
# Independent expected value: -0.13
```

Example input (JSON):

```json
{
  "current_index": 50,
  "average_index": 100
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

## solvency2.reporting

### reporting_catalog

```python
solvency2.reporting.reporting_catalog(*, technical_version: str) -> dict
```

Return module/template/table navigation for one explicit archived release.

Baseline and hotfix share schema URIs, so neither an URI nor a date uniquely
selects a version. Module inclusion does not prove an insurer must file it.
No Context is accepted: technical and regulatory applicability are distinct.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_data

```python
solvency2.reporting.reporting_data(category: str, *, technical_version: str) -> dict
```

Load one hash-verified detail category, preserving raw DPM column names.

Categories: structure, cells, dictionary, rules. Only the requested category
is decompressed. The rules category contains definitions and module/table
associations; IsEnabled/IncludeInXBRL are preserved, not interpreted as an
execution result or a current supervisory deactivation check.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_table

```python
solvency2.reporting.reporting_table(table_code: str, *, technical_version: str) -> dict
```

Return one table's cell/axis definitions without expanding open axes.

Source IDs are local to the explicit technical release. Shaded cells,
abstract headers, optional keys and hierarchy restrictions retain their
original meanings and flags; they are never converted into zero inputs.
This is a definition lookup, not a fact validator or a filing requirement.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_bound_rule_check

```python
solvency2.reporting.reporting_bound_rule_check(validation_code: str, bindings: dict, *, technical_version: str, binding_reference: str) -> dict
```

Check only the supported expression of one archived rule.

Bind each source variable ID to {value, decimals} or, for seq=True, to
{values: [{value, decimals}, ...]}. Atomic alternatives are {text: str},
{boolean: bool}, {qname: {namespace, local_name}}, {date: "YYYY-MM-DD"}
and {absent: true}; absence
is not an item within a sequence. All syntactic variables must be supplied;
there is no implicit zero/default fill, even for an inactive branch. An empty
sequence must be explicitly supplied. The binding reference records external
qualification, not an engine verification of correct selection or filing.

A fact may alternatively carry an explicit dimension list in the wrapper
{fact: atom, dimensions: [{dimension: {namespace, local_name}, value: atom}]}.
Dimension admissibility and defaults remain externally qualified. Supported
local filters run on every supplied candidate; rejected scalars become
absent, not source-default zero. Sequence candidates are filtered before
aggregation. Global filters, joins and cross-fact local filters are rejected.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_rule_precondition

```python
solvency2.reporting.reporting_rule_precondition(validation_code: str, indicators: dict, *, technical_version: str, module: str) -> dict
```

Check only an archived module's filing-indicator condition.

Supply explicit Boolean declarations for all referenced template indicators.
True means this one technical condition holds, not that the rule is legally
applicable, currently active or numerically satisfied. No filing is created.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_closed_rule_check

```python
solvency2.reporting.reporting_closed_rule_check(validation_code, facts, *, technical_version, fact_context, binding_reference)
```

Public component boundary: closed DPM cells to a typed expression check.

Requires declared, externally qualified facts and one entity/period/unit
context. It does not apply filing indicators, determine legal applicability,
check current deactivations, expand open tables or construct an XBRL report.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_validation_status

```python
solvency2.reporting.reporting_validation_status(validation_code, *, technical_version, module)
```

Return one archived module/rule status, not a regulatory filing decision.

No date-based automatic taxonomy selection, internet lookup, insurer model,
or submission occurs. Read source snapshot dates and REVIEW_REQUIRED states.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_metric_value_check

```python
solvency2.reporting.reporting_metric_value_check(metric_code, fact, *, technical_version)
```

Public explicit-version DPM value check; not a report or XML importer.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reporting_instance

```python
solvency2.reporting.reporting_instance(facts, *, technical_version, module, entity, instant, indicators, qualification_reference, validation_codes=None, filing_overrides=())
```

Assemble a deterministic draft and cell-to-fact reconciliation.

Each input is {business_code, atom, open_dimensions?, unit?}. The complete
archived BusinessCode (including braces) is mandatory. Caller-selected
technical version/module and applicability reference are not auto-approved.
Returns XML text, its SHA-256, source evidence and explicit pending checks.
No network, filesystem writes or submission is performed.
Optional validation_codes are explicitly selected archived rules; supported
closed-cell checks use these same facts. Unselected rules remain unchecked.
"ALL_MODULE" attempts the union of archived module links and workbook duties;
unresolved rules stay visible and never imply full-report validation.
filing_overrides are explicit NumericOverride objects for archived precision
parameters; original values and reasons remain in the returned audit.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### sfcr_captive_disclosure_conditions_2027

```python
solvency2.reporting.sfcr_captive_disclosure_conditions_2027(captive_type: str, permitted_policyholders: bool, natural_person_tp_share: float, no_compulsory_liability: bool, *, group_loans_asset_share: float | None = None, maximum_loss_deterministic: bool | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Declared captive relief conditions, distinct from ORSA/reporting relief.

Captive status, beneficiary qualification, loan/cash-pool scope and the
deterministic maximum-loss assessment are external. Reinsurance liability
exclusion concerns the underlying insurance contracts, not only the treaty.

Output unit: `indicator`. Sources: `DIR:article-51:3-4`.

Fixed example: `sfcr-insurance-share-zero`. 43 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'sfcr-insurance-share-zero')
context = replace(base, **case.get('context', {}))
result = s2.sfcr_captive_disclosure_conditions_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "captive_type": "insurance",
  "permitted_policyholders": true,
  "natural_person_tp_share": 0,
  "no_compulsory_liability": true,
  "qualification_reference": "SYN-SFCR-qualified"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### sfcr_balance_sheet_audit_required_2027

```python
solvency2.reporting.sfcr_balance_sheet_audit_required_2027(small_non_complex: bool, captive: bool, national_extension_applies: bool, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Select the balance-sheet audit duty, not the complete audit perimeter.

Captive classification is not conditional on Article51 disclosure relief.
The caller must qualify national extensions explicitly; no default national
rule, automatic legal research or audit-content approval is inferred.

Output unit: `indicator`. Sources: `DIR:article-51a:1-3`.

Fixed example: `sfcr-audit-111`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'sfcr-audit-111')
context = replace(base, **case.get('context', {}))
result = s2.sfcr_balance_sheet_audit_required_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "small_non_complex": true,
  "captive": true,
  "national_extension_applies": true,
  "qualification_reference": "SYN-national-and-entity-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### sfcr_content_evidence_check

```python
solvency2.reporting.sfcr_content_evidence_check(evidence: Mapping[str, dict], *, report_part: str, full_narrative_scope: bool, assessment_reference: str, scope_reference: str, context: solvency2._core.core.Context, structure_sections: list[str] | None = None, structure_reference: str | None = None, de_materiality: Optional[Mapping] = None, reporting_scope: str = 'solo', group_evidence: Optional[Mapping] = None)
```

Inventory references for an externally qualified full narrative part.

A conditional paragraph needs either its content evidence or a qualified
non-applicability assessment, never an unqualified silent omission.
References are not retrieved or assessed. Quantitative-only relief reports
require a different perimeter and are deliberately not certified here.

Output unit: `indicator`. Sources: `DR:article-290`, `DR:article-291`, `DR:article-292-298a`.

Fixed example: `sfcr-content-baseline-sfcr-empty`. 249 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'sfcr-content-baseline-sfcr-empty')
context = replace(base, **case.get('context', {}))
result = s2.sfcr_content_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "report_part": "sfcr",
  "full_narrative_scope": true,
  "assessment_reference": "SYN-SFCR-assessment",
  "scope_reference": "SYN-full-narrative-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### sfcr_publication_evidence_check

```python
solvency2.reporting.sfcr_publication_evidence_check(evidence: Mapping, *, assessment_reference: str, context: solvency2._core.core.Context, publication_facts: Optional[Mapping] = None, capital_events: Optional[Mapping] = None)
```

Join versioned duty references and qualified event facts, not legal sign-off.

Every control needs evidence, including reasoned non-applicability when
conditional. AVAILABLE merely records a reference. Elapsed months and
historical deadline facts are externally qualified; no calendar guess.
Missing optional screenings remain NOT_ASSESSED, never implicitly passed.

Output unit: `indicator`. Sources: `DIR:articles-53-55`, `DR:articles-299-303`.

Fixed example: `sfcr-publication-future-missing`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'sfcr-publication-future-missing')
context = replace(base, **case.get('context', {}))
result = s2.sfcr_publication_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Inspect `case['kwargs']` for the complete nested input mapping (kept in the bundled dataset rather than duplicated here).

### rsr_long_term_equity_extra_disclosure_2027

```python
solvency2.reporting.rsr_long_term_equity_extra_disclosure_2027(long_term_equity_asset_share: float, scr_compliant_without_treatment: bool, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Extra impact/action disclosures for an externally qualified105a holding.

Share is relative to ALL held assets, not the equity portfolio. The
counterfactual SCR-compliance fact must already have been established.
Exactly4% does not trigger the share branch. No general reporting waiver.

Output unit: `indicator`. Sources: `DR:article-311:5`.

Fixed example: `rsr-content-future-lte-0-true`. 19 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rsr-content-future-lte-0-true')
context = replace(base, **case.get('context', {}))
result = s2.rsr_long_term_equity_extra_disclosure_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "long_term_equity_asset_share": 0,
  "scr_compliant_without_treatment": true,
  "qualification_reference": "SYN-LTE105a-scope-and-counterfactual"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### capital_recovery_plan_evidence_check

```python
solvency2.reporting.capital_recovery_plan_evidence_check(evidence: Mapping[str, dict], *, plan_kind: str, assessment_reference: str, scope_reference: str, context: solvency2._core.core.Context)
```

Inventory the five common plan contents; do not project or approve them.

Output unit: `indicator`. Sources: `DIR:article-142:1:a-e`.

Fixed example: `capital-breach-baseline-scr_recovery-empty`. 36 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'capital-breach-baseline-scr_recovery-empty')
context = replace(base, **case.get('context', {}))
result = s2.capital_recovery_plan_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "plan_kind": "scr_recovery",
  "assessment_reference": "SYN-assessment",
  "scope_reference": "SYN-qualified-plan"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### group_significant_branch_screen

```python
solvency2.reporting.group_significant_branch_screen(branch_gross_premiums: float, group_gross_premiums: float, host_market_gross_premiums: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Strict 5% group OR host-market test used by group reporting definitions.

Latest applicable accounts, currency, host-market life/nonlife scope and
branch perimeter are externally qualified. No college invitation or broad
materiality judgement follows automatically from this numeric indicator.

Output unit: `indicator`. Sources: `DR:article-354:1`, `DR:article-359:a:i`, `DR:article-372:2:a`.

Fixed example: `group-report-close-baseline-branch-host`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-report-close-baseline-branch-host')
context = replace(base, **case.get('context', {}))
result = s2.group_significant_branch_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "branch_gross_premiums": 5,
  "group_gross_premiums": 200,
  "host_market_gross_premiums": 50,
  "qualification_reference": "SYN-latest-accounts-and-host-market"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### supervisory_reporting_deadline_weeks

```python
solvency2.reporting.supervisory_reporting_deadline_weeks(report_kind: str, *, qualification_reference: str, scope: str = 'solo', context: solvency2._core.core.Context, exceptional_extension_weeks: float = 0, delegated_act_reference: str | None = None)
```

Select an archived deadline length for an externally qualified type/scope.

Historical rows are post-transition. Future ORSA has no inherited two-week
row. The returned length is not a legally determined calendar date.
Explicit group scope uses separate254/256/256b or historical373 rules.
Group sfcr/single_sfcr entries include public disclosure, not just filing.
Optional304e extension requires an externally qualified delegated act;
an extreme event alone never creates an extension. ORSA/SPV are excluded.

Output unit: `weeks`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `reporting-timing-baseline-deadline-orsa`. 52 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'reporting-timing-baseline-deadline-orsa')
context = replace(base, **case.get('context', {}))
result = s2.supervisory_reporting_deadline_weeks(**case['kwargs'], context=context)
# Independent expected value: 2
```

Example input (JSON):

```json
{
  "report_kind": "orsa",
  "qualification_reference": "SYN-individual-qualified-report-period"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### regular_supervisory_report_interval

```python
solvency2.reporting.regular_supervisory_report_interval(small_non_complex: bool, *, supervisory_interval_years: float | None = None, supervisory_reference: str | None = None, non_snc_approval_reference: str | None = None, scope: str = 'solo', qualification_reference: str, context: solvency2._core.core.Context)
```

Select declared RSR periodicity without waiving other reporting duties.

None explicitly declares no additional supervisory decision. Classification
and authenticity of instructions/approval remain external qualifications.
non_snc_approval_reference enables the separately approved29d/327b route;
a size-screen result is never substituted for this supervisory decision.

Output unit: `years`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `group-close-baseline-rsr-default`. 46 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-close-baseline-rsr-default')
context = replace(base, **case.get('context', {}))
result = s2.regular_supervisory_report_interval(**case['kwargs'], context=context)
# Independent expected value: 3
```

Example input (JSON):

```json
{
  "small_non_complex": false,
  "scope": "group",
  "qualification_reference": "SYN-qualified-group-RSR-period"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### supervisory_reporting_evidence_check

```python
solvency2.reporting.supervisory_reporting_evidence_check(evidence: Mapping[str, dict], *, assessment_reference: str, scope_reference: str, report_kind: str = 'core', context: solvency2._core.core.Context, structure_sections: list[str] | None = None, structure_reference: str | None = None, reporting_scope: str = 'solo', group_evidence: Optional[Mapping] = None)
```

Inventory core or full RSR references for a qualified request/period.

Qualitative/quantitative, temporal and data-source alternatives remain
alternatives: one reference documents the externally justified selection.
No file inspection, content certification, board approval or filing occurs.

Output unit: `indicator`. Sources: `DIR:article-35:1`, `DIR:article-35:3-5`.

Fixed example: `rsr-content-baseline-empty`. 237 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rsr-content-baseline-empty')
context = replace(base, **case.get('context', {}))
result = s2.supervisory_reporting_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "report_kind": "rsr",
  "assessment_reference": "SYN-RSR-assessment",
  "scope_reference": "SYN-full-RSR-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### reporting_captive_itemised_exemption_2027

```python
solvency2.reporting.reporting_captive_itemised_exemption_2027(is_captive: bool, permitted_policyholders: bool, natural_person_tp_share: float, no_compulsory_liability: bool, reporting_interval_years: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Declared Article35a(3) eligibility only for subannual itemised reporting.

Policyholder/beneficiary scope and underlying reinsurance contracts must
already be qualified. Neither ORSA eligibility nor a general waiver is inferred.

Output unit: `indicator`. Sources: `DIR:article-35a:3`.

Fixed example: `reporting-captive-natural_person_tp_share-0`. 31 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'reporting-captive-natural_person_tp_share-0')
context = replace(base, **case.get('context', {}))
result = s2.reporting_captive_itemised_exemption_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "is_captive": true,
  "permitted_policyholders": true,
  "natural_person_tp_share": 0,
  "no_compulsory_liability": true,
  "reporting_interval_years": 0.25,
  "qualification_reference": "SYN-qualified-captive-policyholders-beneficiaries-and-underlying-reinsurance-no-compulsory-liability"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### orsa_report_evidence_check

```python
solvency2.reporting.orsa_report_evidence_check(evidence: Mapping[str, dict], significant_uncovered_risk_deviation: bool, *, qualification_reference: str, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory report content/transmission evidence, not the report itself.

Quantification of non-reflected risks is conditional on externally assessed
significance. Future electronic form also requires machine readability and
searchable text/figures. No format inspection, filing or deadline approval.

Output unit: `indicator`. Sources: `DR:article-306`, `DR:article-313`.

Fixed example: `orsa-report-baseline-submission-missing`. 17 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-report-baseline-submission-missing')
context = replace(base, **case.get('context', {}))
result = s2.orsa_report_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {
    "results_qualitative": {
      "status": "AVAILABLE",
      "reference": "SYN-results_qualitative"
    },
    "results_quantitative": {
      "status": "AVAILABLE",
      "reference": "SYN-results_quantitative"
    },
    "conclusions": {
      "status": "AVAILABLE",
      "reference": "SYN-conclusions"
    },
    "methods": {
      "status": "AVAILABLE",
      "reference": "SYN-methods"
    },
    "key_assumptions": {
      "status": "AVAILABLE",
      "reference": "SYN-key_assumptions"
    },
    "solvency_need": {
      "status": "AVAILABLE",
      "reference": "SYN-solvency_need"
    },
    "capital_and_own_funds_comparison": {
      "status": "AVAILABLE",
      "reference": "SYN-capital_and_own_funds_comparison"
    },
    "uncovered_quantifiable_risks_qualitative": {
      "status": "AVAILABLE",
      "reference": "SYN-uncovered_quantifiable_risks_qualitative"
    }
  },
  "significant_uncovered_risk_deviation": false,
  "qualification_reference": "SYN-significance",
  "assessment_reference": "SYN-report"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

## solvency2.models

### usp_credibility_factor

```python
solvency2.models.usp_credibility_factor(years: int, *, method: str, risk_module: str, segment: str | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Look up AnnexXVII credibility with the method's correct year basis.

The year count is not evidence of data representativeness or required
consecutive history. Revision has no nonlife segment. Terminal table rows
apply to all later years; no interpolation or below-table extrapolation.

Output unit: `factor`. Sources: `DR:annex-XVII:G`.

Fixed example: `usp-credibility-baseline-life`. 100 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-credibility-baseline-life')
context = replace(base, **case.get('context', {}))
result = s2.usp_credibility_factor(**case['kwargs'], context=context)
# Independent expected value: 0.51
```

Example input (JSON):

```json
{
  "years": 6,
  "method": "revision",
  "risk_module": "life",
  "segment": null,
  "qualification_reference": "SYN-qualifying-USP-history"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_nonproportional_credibility_blend

```python
solvency2.models.usp_nonproportional_credibility_blend(estimated_factor: float, standard_factor: float, credibility: float, *, method: str, calibration_reference: str, context: solvency2._core.core.Context)
```

c*NP_est + (1-c)*NP_standard; separate from either F1/F2 estimator.

Input-factor qualification and their source-defined calibration are external.
The engine neither estimates loss distributions here nor substitutes this
result into a standard-formula calculation or grants approval.

Output unit: `factor`. Sources: `DR:annex-XVII:F1:4`, `DR:annex-XVII:F2:method-specification-2`.

Fixed example: `usp-blend-baseline-nonproportional_1-full`. 32 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-blend-baseline-nonproportional_1-full')
context = replace(base, **case.get('context', {}))
result = s2.usp_nonproportional_credibility_blend(**case['kwargs'], context=context)
# Independent expected value: 0.4
```

Example input (JSON):

```json
{
  "estimated_factor": 0.4,
  "standard_factor": 0.8,
  "credibility": 1,
  "method": "nonproportional_1",
  "calibration_reference": "SYN-qualified-raw-NP-and-standard-factor"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### usp_excess_of_loss_estimate

```python
solvency2.models.usp_excess_of_loss_estimate(ultimate_claims: list[float], retention: float, *, upper_limit: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Estimate raw NP′ for one homogeneous F1 excess-of-loss group.

F1 uses the second RAW moment, not variance. ``upper_limit`` is the
absolute upper loss threshold b2, not layer width. Data representativeness,
five reporting years, expense exclusion, gross/net basis, lognormal fit
and treaty eligibility need external qualification. No approval or automatic
standard-formula substitution follows from this component.

Output unit: `factor`. Sources: `DR:annex-XVII:F1:5`, `DR:annex-XVII:F1:6`.

Fixed example: `usp-f1-baseline-unlimited`. 36 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-f1-baseline-unlimited')
context = replace(base, **case.get('context', {}))
result = s2.usp_excess_of_loss_estimate(**case['kwargs'], context=context)
# Independent expected value: 0.5229982205089364
```

Example input (JSON):

```json
{
  "ultimate_claims": [
    50,
    100,
    150,
    200,
    300
  ],
  "retention": 100,
  "qualification_reference": "SYN-F1-data-and-treaty-qualification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### usp_excess_of_loss_group_weighting

```python
solvency2.models.usp_excess_of_loss_group_weighting(estimated_factors: Mapping[str, float], premium_volumes: Mapping[str, float], *, qualification_reference: str, method: str = 'nonproportional_1', context: solvency2._core.core.Context)
```

Weight raw F1/F2 group estimates by externally qualified premium volumes.

Same-segment homogeneity and Article116(3) volume measurement are not
inferred from group labels. This is a weighted mean, not diversification,
credibility weighting or permission to replace a standard parameter.
F2 only supports weighting externally qualified estimates here; its printed
estimator/moment anomalies are not repaired or evaluated. No inferred F2 cap.

Output unit: `factor`. Sources: `DR:annex-XVII:F1:7`, `DR:annex-XVII:F2:method-specification-5`, `DR:article-116:3`.

Fixed example: `usp-f1-groups-baseline-single`. 40 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-f1-groups-baseline-single')
context = replace(base, **case.get('context', {}))
result = s2.usp_excess_of_loss_group_weighting(**case['kwargs'], context=context)
# Independent expected value: 0.4
```

Example input (JSON):

```json
{
  "estimated_factors": {
    "A": 0.4
  },
  "premium_volumes": {
    "A": 100
  },
  "qualification_reference": "SYN-homogeneous-groups-and-DR116-volumes"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### usp_lognormal_sigma

```python
solvency2.models.usp_lognormal_sigma(losses: list[float], volumes: list[float], mixing: float, log_coefficient: float, *, method: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Evaluate prescribed sigma and objective at explicit delta/gamma.

This does NOT claim the supplied pair minimizes the objective. B uses
accident-year aggregated claims and earned premiums; C1 uses financial-year
end reserves plus payments for opening claims, and opening reserves.
Both include servicing expenses, unlike the F1 individual-claim estimator.
Consecutiveness, adjustments, statistical assumptions and fitting need
separate qualification. No automatic standard-formula replacement.

Output unit: `factor`. Sources: `DR:annex-XVII:B:5`, `DR:annex-XVII:B:6`, `DR:annex-XVII:C:5`, `DR:annex-XVII:C:6`.

Fixed example: `usp-lognormal-baseline-premium-delta0`. 80 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-lognormal-baseline-premium-delta0')
context = replace(base, **case.get('context', {}))
result = s2.usp_lognormal_sigma(**case['kwargs'], context=context)
# Independent expected value: 0.3400860072741989
```

Example input (JSON):

```json
{
  "losses": [
    60,
    120,
    100,
    190,
    250
  ],
  "volumes": [
    80,
    100,
    140,
    200,
    300
  ],
  "mixing": 0,
  "log_coefficient": -1,
  "method": "premium",
  "qualification_reference": "SYN-consecutive-qualified-years-not-optimality"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_lognormal_credibility_blend

```python
solvency2.models.usp_lognormal_credibility_blend(estimated_sigma: float, standard_sigma: float, credibility: float, years: int, *, method: str, calibration_reference: str, context: solvency2._core.core.Context)
```

Apply B/C1 finite-history correction BEFORE credibility blending.

c*sigma_hat*sqrt((T+1)/(T-1)) + (1-c)*sigma_standard. This correction
does not belong to F1/F2 or reserve method2. Appropriate standard sigma
and fitted sigma qualification are explicit external inputs.

Output unit: `factor`. Sources: `DR:annex-XVII:B:4`, `DR:annex-XVII:C:4`.

Fixed example: `usp-lognormal-blend-baseline-premium-zero`. 48 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-lognormal-blend-baseline-premium-zero')
context = replace(base, **case.get('context', {}))
result = s2.usp_lognormal_credibility_blend(**case['kwargs'], context=context)
# Independent expected value: 0.2
```

Example input (JSON):

```json
{
  "estimated_sigma": 0.1,
  "standard_sigma": 0.2,
  "credibility": 0,
  "years": 5,
  "method": "premium",
  "calibration_reference": "SYN-fitted-sigma-and-appropriate-standard"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_lognormal_fit

```python
solvency2.models.usp_lognormal_fit(losses: list[float], volumes: list[float], *, method: str, qualification_reference: str, context: solvency2._core.core.Context, max_iterations: int = 1000, gradient_tolerance: float = 1e-07)
```

Fit prescribed delta/gamma, returning raw sigma before credibility.

Both boundary faces and deterministic interior starts are searched. Optional
numerical controls are reported, never treated as regulatory parameters.
Nonconvergence and constant log-ratios are REVIEW_REQUIRED, not zero sigma.
Data assumptions, consecutive history and supervisory approval stay external.

Output unit: `factor`. Sources: `DR:annex-XVII:B:5`, `DR:annex-XVII:C:5`.

Fixed example: `usp-fit-baseline-premium-upper-boundary`. 56 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-fit-baseline-premium-upper-boundary')
context = replace(base, **case.get('context', {}))
result = s2.usp_lognormal_fit(**case['kwargs'], context=context)
# Independent expected value: 0.3763436440304585
```

Example input (JSON):

```json
{
  "losses": [
    75,
    110,
    85,
    280,
    140
  ],
  "volumes": [
    80,
    100,
    140,
    200,
    300
  ],
  "method": "premium",
  "qualification_reference": "SYN-independent-60digit-fit"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### external_model_checked_value

```python
solvency2.models.external_model_checked_value(value: float, evidence: collections.abc.Mapping, *, model_kind: str, output_kind: str, conditions: collections.abc.Mapping, model_reference: str, assessment_reference: str, scope_reference: str, context: solvency2._core.core.Context)
```

Forward an externally computed value after declared-evidence checks.

AVAILABLE references do not prove their contents, model approval, adequacy
or lawful integration. Partial-model results must already follow the
externally approved integration; this function applies no correlations.
Period metadata is not a calendar-deadline monitor or submission service.

Output unit: `context currency`. Sources: `DIR:articles-112-126`.

Fixed example: `model-standards-close-baseline-full`. 90 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'model-standards-close-baseline-full')
context = replace(base, **case.get('context', {}))
result = s2.external_model_checked_value(**case['kwargs'], context=context)
# Independent expected value: 50000000
```

Inspect `case['kwargs']` for the complete nested input mapping (kept in the bundled dataset rather than duplicated here).

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### model_va_scr_floor_2027

```python
solvency2.models.model_va_scr_floor_2027(model_scr: float, standard_va_scr: float, own_portfolio_va_scr: float, *, permitted_by_member_state: bool, excludes_company_adjustment: bool, excludes_macro_va: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Check declared method conditions and two external SCR floors, not raise SCR.

Output unit: `indicator`. Sources: `DIR:article-122:5`.

Fixed example: `model-va-future-equal`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'model-va-future-equal')
context = replace(base, **case.get('context', {}))
result = s2.model_va_scr_floor_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "model_scr": 90,
  "standard_va_scr": 80,
  "own_portfolio_va_scr": 90,
  "permitted_by_member_state": true,
  "excludes_company_adjustment": true,
  "excludes_macro_va": true,
  "qualification_reference": "SYN-qualified-VA-method-and-comparison-portfolios"
}
```

Reference-tested failure codes: `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### partial_model_bscr

```python
solvency2.models.partial_model_bscr(technique: int, inputs: collections.abc.Mapping, intangible_charge: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Annex XVIII techniques1-5, with recursive4/5 and certified external2.

Model charges and scalar module inputs are externally qualified. Nested inputs
use the same technique, with no intangible charge below the outermost BSCR.
    Technique2 verifies a PSD dual certificate of constrained maximisation;
    it does not develop or run an insurer model or an optimisation solver.

Output unit: `context currency`. Sources: `DR:article-239`, `DR:annex-XVIII`.

Fixed example: `partial-integration-baseline-3`. 24 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'partial-integration-baseline-3')
context = replace(base, **case.get('context', {}))
result = s2.partial_model_bscr(**case['kwargs'], context=context)
# Independent expected value: 8.557438524302
```

Example input (JSON):

```json
{
  "technique": 3,
  "inputs": {
    "ss": 3,
    "sc": 4,
    "s": 5,
    "pc": 4,
    "ps": 3,
    "p": 5
  },
  "intangible_charge": 2,
  "qualification_reference": "SYN-qualified-method-scope-and-exclusion-of-double-counting"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### usp_reserve2_estimate

```python
solvency2.models.usp_reserve2_estimate(cumulative_claims: list[list[float]], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Compute sqrt(MSEP)/reserve for a qualified square cumulative triangle.

Rows run oldest to newest accident year with lengths n,n-1,...,1.
I>J is permitted by D(2)e but needs a separately qualified treatment of
the printed formula's out-of-range diagonal indices; no silent padding.
Consecutive years, expense inclusion, matching net reinsurance basis,
negligible oldest-year tail and stochastic assumptions remain external.

Output unit: `factor`. Sources: `DR:annex-XVII:D:2`, `DR:annex-XVII:D:4`, `DR:annex-XVII:D:5`.

Fixed example: `usp-reserve2-baseline-square`. 28 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-reserve2-baseline-square')
context = replace(base, **case.get('context', {}))
result = s2.usp_reserve2_estimate(**case['kwargs'], context=context)
# Independent expected value: 0.03431376114205189
```

Example input (JSON):

```json
{
  "cumulative_claims": [
    [
      100,
      150,
      190,
      210,
      220
    ],
    [
      120,
      180,
      230,
      255
    ],
    [
      90,
      140,
      185
    ],
    [
      110,
      170
    ],
    [
      130
    ]
  ],
  "qualification_reference": "SYN-qualified-consecutive-net-cumulative-claims"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_reserve2_credibility_blend

```python
solvency2.models.usp_reserve2_credibility_blend(estimated_sigma: float, standard_sigma: float, credibility: float, *, calibration_reference: str, context: solvency2._core.core.Context)
```

D(4) linear blend, WITHOUT the different B/C1 finite-history correction.

Output unit: `factor`. Sources: `DR:annex-XVII:D:4`.

Fixed example: `usp-reserve2-blend-baseline-large`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-reserve2-blend-baseline-large')
context = replace(base, **case.get('context', {}))
result = s2.usp_reserve2_credibility_blend(**case['kwargs'], context=context)
# Independent expected value: 1e+308
```

Example input (JSON):

```json
{
  "estimated_sigma": 1e+308,
  "standard_sigma": 1e+308,
  "credibility": 0.34,
  "calibration_reference": "SYN-reserve2-sigma-and-standard"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### usp_revision_moments

```python
solvency2.models.usp_revision_moments(annual_benefits: Mapping[str, list[float]], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Return expected annual increases and prescribed sample moments.

Each beneficiary supplies aligned A0..AT, including the initial baseline.
Only strictly positive changes enter severity statistics. Frequency includes
ALL years, including zero-event years. Negative changes are not netted.
Computable moments do not prove negative-binomial/lognormal suitability,
independence, immaterial inflation risk or the prescribed aggregate quantile.

Output unit: `context currency`. Sources: `DR:annex-XVII:E:2:b`, `DR:annex-XVII:E:3`, `DR:annex-XVII:E:5`, `DR:annex-XVII:E:7`, `DR:annex-XVII:E:8`.

Fixed example: `usp-revision-moments-baseline-mixed`. 28 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-revision-moments-baseline-mixed')
context = replace(base, **case.get('context', {}))
result = s2.usp_revision_moments(**case['kwargs'], context=context)
# Independent expected value: 19
```

Example input (JSON):

```json
{
  "annual_benefits": {
    "A": [
      100,
      110,
      110,
      130,
      120,
      120
    ],
    "B": [
      200,
      200,
      215,
      215,
      235,
      235
    ],
    "C": [
      300,
      300,
      300,
      300,
      300,
      330
    ]
  },
  "qualification_reference": "SYN-qualified-gross-benefits-with-expenses"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_revision_credibility_blend

```python
solvency2.models.usp_revision_credibility_blend(mean_increase: float, quantile_increase: float, credibility: float, *, quantile_probability: float, risk_module: str, calibration_reference: str, context: solvency2._core.core.Context)
```

c*(quantile-mean)/mean+(1-c)*S, preserving the source's absence of a floor.

The quantile of the independent negative-binomial/lognormal compound sum is
externally qualified, NOT generated here. Probability must match the active
profile (including explicit analyst override). Credibility is supplied, not
inferred from the ambiguous printed E(4)a 'section7' cross-reference.

Output unit: `factor`. Sources: `DR:annex-XVII:E:4`, `DR:article-141`, `DR:article-158`.

Fixed example: `usp-revision-blend-baseline-life-no-floor`. 48 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-revision-blend-baseline-life-no-floor')
context = replace(base, **case.get('context', {}))
result = s2.usp_revision_credibility_blend(**case['kwargs'], context=context)
# Independent expected value: -1
```

Example input (JSON):

```json
{
  "mean_increase": 100,
  "quantile_increase": 0,
  "credibility": 1,
  "quantile_probability": 0.995,
  "risk_module": "life",
  "calibration_reference": "SYN-E6-distribution-quantile-and-mean"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_revision_compound_quantile

```python
solvency2.models.usp_revision_compound_quantile(annual_benefits: Mapping[str, list[float]], *, qualification_reference: str, context: solvency2._core.core.Context, relative_tolerance: float = 0.001, max_grid_power: int = 20)
```

Return the upper numerical bracket of the prescribed compound quantile.

Uses prescribed raw-data moments, not a Monte Carlo or internally chosen
insurer model. The lower/upper severity-rounding order is mathematical;
the floating-point guard is NOT formally certified interval arithmetic.
Numerical controls, backend versions, bounds and clipping are disclosed.
Nonconvergence or degenerate distribution fits require external review.

Output unit: `currency`. Sources: `DR:annex-XVII:E:4:c`, `DR:annex-XVII:E:6:a-c`, `DR:annex-XVII:E:7-8`.

Fixed example: `usp-revision-quantile-baseline-standard`. 38 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-revision-quantile-baseline-standard')
context = replace(base, **case.get('context', {}))
result = s2.usp_revision_compound_quantile(**case['kwargs'], context=context)
# Independent expected value: 411.74776013911674
```

Example input (JSON):

```json
{
  "annual_benefits": {
    "0": [
      100,
      100,
      100,
      100,
      100,
      110
    ],
    "1": [
      100,
      100,
      100,
      100,
      100,
      120
    ],
    "2": [
      100,
      100,
      100,
      100,
      100,
      130
    ],
    "3": [
      100,
      100,
      100,
      100,
      100,
      140
    ],
    "4": [
      100,
      100,
      100,
      100,
      100,
      150
    ]
  },
  "qualification_reference": "SYN-prescribed-E-moments-independent-distributions"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_parameter_scope_check

```python
solvency2.models.usp_parameter_scope_check(replacements: list[str], *, risk_module: str, segment: str | None = None, qualified_reinsurance: bool | None = None, material_inflation_risk: bool | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Check declared replacement scope, not data/method fitness or authorization.

Gross-premium sigma and the NP factor cannot both be replaced in one
segment. Revision is available only absent material inflation risk;
materiality follows decision relevance, not an invented numeric cutoff.

Output unit: `indicator`. Sources: `DR:article-218:1`, `DR:article-218:4`, `DIR:article-104:7`.

Fixed example: `usp-governance-baseline-segment-nonlife-1`. 124 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-governance-baseline-segment-nonlife-1')
context = replace(base, **case.get('context', {}))
result = s2.usp_parameter_scope_check(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "replacements": [
    "premium_sigma"
  ],
  "risk_module": "nonlife",
  "segment": "1",
  "qualification_reference": "SYN-scope-qualification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_reinsurance_contract_conditions

```python
solvency2.models.usp_reinsurance_contract_conditions(coverage_conditions: Mapping[str, bool], contract_requirements: Mapping[str, bool], *, contract_type: str, qualification_reference: str, finite_reinsurance_ids: list[str] | tuple = (), context: solvency2._core.core.Context)
```

Check collective coverage and each contract's declared209/210/211/213 compliance.

For multiple contracts the coverage conditions apply collectively, whereas
every individual contract must satisfy the cross-article requirements.
Qualified equivalent SPV arrangements are included; equivalent transfer is
externally assessed, never inferred from the name or number of contracts.
Finite/similar transfers invalidate this submitted contract set for USP;
omit none from the declaration (empty means all are qualified non-finite).

Output unit: `indicator`. Sources: `DR:article-218:2`, `DR:article-218:3`, `DR:article-208:2`.

Fixed example: `usp-governance-baseline-treaty-excess_of_loss-15`. 96 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-governance-baseline-treaty-excess_of_loss-15')
context = replace(base, **case.get('context', {}))
result = s2.usp_reinsurance_contract_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "coverage_conditions": {
    "full_cover_above_retention_to_limit_or_unlimited": true,
    "all_claims_over_horizon": true,
    "sufficient_reinstatements_over_horizon": true
  },
  "contract_requirements": {
    "A": true
  },
  "contract_type": "excess_of_loss",
  "qualification_reference": "SYN-qualified-cover-and-each-contract"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### usp_standard_method_selection

```python
solvency2.models.usp_standard_method_selection(method_results: Mapping[str, dict], *, parameter: str, superiority_demonstrated: bool, superior_method: str | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Select a qualified more accurate method, otherwise conservative capital result.

Capital requirements must be comparable under the same qualified inputs.
We do not assume that the largest raw parameter always gives the largest
capital requirement. Ties use a disclosed deterministic technical ordering,
not a claimed regulatory preference for one standardized method.

Output unit: `factor`. Sources: `DR:article-220:1`, `DR:article-220:2`.

Fixed example: `usp-governance-baseline-selection-single-premium_sigma-premium`. 36 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-governance-baseline-selection-single-premium_sigma-premium')
context = replace(base, **case.get('context', {}))
result = s2.usp_standard_method_selection(**case['kwargs'], context=context)
# Independent expected value: 0.2
```

Example input (JSON):

```json
{
  "method_results": {
    "premium": {
      "parameter_value": 0.2,
      "capital_requirement": 20
    }
  },
  "parameter": "premium_sigma",
  "superiority_demonstrated": false,
  "qualification_reference": "SYN-calibration-and-comparable-capital"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### usp_data_evidence_check

```python
solvency2.models.usp_data_evidence_check(evidence: Mapping[str, dict], *, external_data_used: bool, multiple_external_sources: bool, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory active USP data references, never certify their content or quality.

Output unit: `indicator`. Sources: `DR:article-219`, `DR:article-19:1-4`.

Fixed example: `usp-governance-baseline-evidence-empty-true-true`. 76 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-governance-baseline-evidence-empty-true-true')
context = replace(base, **case.get('context', {}))
result = s2.usp_data_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "external_data_used": true,
  "multiple_external_sources": true,
  "assessment_reference": "SYN-USP-data-assessment",
  "evidence": {}
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### usp_method_data_evidence_check

```python
solvency2.models.usp_method_data_evidence_check(evidence: Mapping[str, dict], *, method: str, data_basis: str, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory method-specific references, with explicit gross/net and year bases.

B/C/D/E include servicing expenses; F1/F2 exclude them. A reference is
never inspected or treated as verified data, calibration or approval.
This inventory neither enables the blocked F2 estimator nor extends the
square-triangle reserve2 calculator to rectangular development histories.

Output unit: `indicator`. Sources: `DR:article-219:1:d`, `DR:annex-XVII:B:1-2`, `DR:annex-XVII:C:1-2`, `DR:annex-XVII:D:1-2`, `DR:annex-XVII:E:1-2`, `DR:annex-XVII:F1:data-1-2`, `DR:annex-XVII:F2:data-1-2`.

Fixed example: `usp-method-data-baseline-premium-net-empty`. 250 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'usp-method-data-baseline-premium-net-empty')
context = replace(base, **case.get('context', {}))
result = s2.usp_method_data_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "method": "premium",
  "data_basis": "net",
  "assessment_reference": "SYN-qualified-method-data"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### simplification_share_screen_2027

```python
solvency2.models.simplification_share_screen_2027(risk_shares: Mapping[str, float], *, regime: str, evidence_age_years: float, small_non_complex: bool | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Check distinct strict SNC versus inclusive immaterial-risk thresholds.

Shares refer to each risk's externally qualified reference calculation;
never infer a common denominator or double-count nested modules. The age
is externally qualified and covers the oldest required reference evidence.

Output unit: `indicator`. Sources: `DIR:article-109:1-3`.

Fixed example: `simplification-2027-individual-over`. 13 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simplification-2027-individual-over')
context = replace(base, **case.get('context', {}))
result = s2.simplification_share_screen_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "risk_shares": {
    "a": 0.050001
  },
  "regime": "immaterial_modules",
  "evidence_age_years": 3,
  "qualification_reference": "SYN-nonoverlapping-reference-shares"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### captive_simplification_conditions

```python
solvency2.models.captive_simplification_conditions(conditions: Mapping[str, bool], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check externally assessed DR89 facts, not substantive eligibility itself.

Absent insurance/reinsurance business must be explicitly qualified by the
caller; missing evidence never means that a condition is met.

Output unit: `indicator`. Sources: `DR:article-89`.

Fixed example: `captive-baseline-eligible`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'captive-baseline-eligible')
context = replace(base, **case.get('context', {}))
result = s2.captive_simplification_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "captive_under_article13": true,
    "article88_satisfied": true,
    "insurance_group_only": true,
    "underlying_reinsurance_group_only": true,
    "no_compulsory_liability": true
  },
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### simplification_proportionality_conditions

```python
solvency2.models.simplification_proportionality_conditions(conditions: Mapping[str, bool], *, simplified_scr_higher: bool | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Screen declared assessments and the higher-SCR exception to material error.

Do not create a quantitative materiality threshold. A comparison with the
standard calculation is only requested where the exception is invoked;
the result records supplied facts, not a substantive adequacy conclusion.

Output unit: `indicator`. Sources: `DR:article-88:1-2`.

Fixed example: `proportionality-baseline-ordinary`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'proportionality-baseline-ordinary')
context = replace(base, **case.get('context', {}))
result = s2.simplification_proportionality_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "risk_assessed": true,
    "error_assessed": true,
    "decision_relevant_error": false
  },
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### simplified_immaterial_risk_2027

```python
solvency2.models.simplified_immaterial_risk_2027(base_scr: float, base_volume: float, current_volume: float, *, elapsed_years: float, is_market_risk: bool, eligibility_reference: str, volume_reference: str, context: solvency2._core.core.Context)
```

Scale the reference SCR with volume, retaining its prescribed floor.

Eligibility under DIR109(2/3), reference calculation and suitability of the
company-specific volume are externally established. A factor ratio in the
details avoids overflow/underflow from an unnecessary intermediate float.

Output unit: `context currency`. Sources: `DR:article-89a:2-3`, `DIR:article-109:2-3`.

Fixed example: `simplification-2027-zero-volume`. 11 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simplification-2027-zero-volume')
context = replace(base, **case.get('context', {}))
result = s2.simplified_immaterial_risk_2027(**case['kwargs'], context=context)
# Independent expected value: 10
```

Example input (JSON):

```json
{
  "base_scr": 10,
  "base_volume": 100,
  "current_volume": 0,
  "elapsed_years": 3,
  "is_market_risk": false,
  "eligibility_reference": "SYN-DIR109-2-3-and-initial-calculation",
  "volume_reference": "SYN-supervisory-volume-justification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

## solvency2.counterparty

### mortgage_type2_eligibility_screen

```python
solvency2.counterparty.mortgage_type2_eligibility_screen(conditions: Mapping[str, bool], total_debt_eur: float, years_since_value_monitoring: float, *, repayment_route: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Screen declarations and numerical limits, not the truth of legal conditions.

Debt is explicitly EUR and includes overdue/connected-party/group creditor
amounts. Context.currency causes no implicit FX conversion. A <=3-year age
does not waive more frequent monitoring under material market changes.
The future CRR alternative is an external qualification, not a CRR calculator.

Output unit: `indicator`. Sources: `DR:article-191:1-13`.

Fixed example: `mortgage-eligibility-future-crr124-zero`. 156 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mortgage-eligibility-future-crr124-zero')
context = replace(base, **case.get('context', {}))
result = s2.mortgage_type2_eligibility_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "retail_residential_mortgage": true,
    "eligible_borrower": true,
    "diversified_similar_exposures": true,
    "debt_information": true,
    "residential_use": true,
    "value_credit_independence": true,
    "enforceable_registered": true,
    "pledge_evidence": true,
    "timely_realisation": true,
    "enhanced_market_monitoring": true,
    "triggered_independent_revaluation": true,
    "credit_strategy_documented": true,
    "independent_valuation_documented": true,
    "insurance_monitoring": true,
    "type2_loss_reporting": true,
    "total_loss_reporting": true,
    "crr124_conditions": true
  },
  "total_debt_eur": 0,
  "years_since_value_monitoring": 0,
  "repayment_route": "crr124",
  "qualification_reference": "SYN-complete-debt-EUR-and-DR191-conditions"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### counterparty_solvency_ratio

```python
solvency2.counterparty.counterparty_solvency_ratio(eligible_own_funds: float, scr: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Divide externally qualified latest eligible funds by latest positive SCR.

Values must refer to the correct counterparty, currency and unit. Their
recency and regulatory eligibility are not established by this division.
Signed funds are preserved; neither MCR compliance nor a rating is inferred.

Output unit: `ratio`. Sources: `DR:article-180:4`, `DR:article-182:6`, `DR:article-199:3`.

Fixed example: `counterparty-ratio-baseline-zero`. 28 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'counterparty-ratio-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.counterparty_solvency_ratio(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "eligible_own_funds": 0,
  "scr": 100,
  "qualification_reference": "SYN-current-qualified-own-funds-and-SCR"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_exposure_type

```python
solvency2.counterparty.default_exposure_type(category: str, *, qualification_reference: str, single_name_count: int | None = None, elect_type1: bool | None = None, context: solvency2._core.core.Context)
```

Return1/2 for default types or0 for exclusion FROM THIS MODULE ONLY.

The category must already describe the precise qualified contractual risk,
including any spread/mortgage/CCP/guarantee conditions. An excluded risk
may attract capital elsewhere; zero is a routing code, not a capital value.
Only cedant deposits and called-unpaid commitments use the declared count
and optional legal election. Article190 grouping and Article189(5) provider
substitution, and the all-relevant-exposures scope of the election, remain
external prerequisites; no count is inferred from arbitrary asset IDs.

Output unit: `exposure_type`. Sources: `DR:article-189:2-7`.

Fixed example: `default-type-future-securities_financing`. 98 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'default-type-future-securities_financing')
context = replace(base, **case.get('context', {}))
result = s2.default_exposure_type(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "qualification_reference": "SYN-qualified-contract-risk-scope-and-count-universe",
  "category": "securities_financing"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### default_single_name_count

```python
solvency2.counterparty.default_single_name_count(exposures: Mapping, *, pool_treatment: Mapping, grouping_reference: str, context: solvency2._core.core.Context, provider_substitutions: Optional[Mapping] = None)
```

Count declared single names and retain every exposure-to-group assignment.

None for group/pool means externally established absence, NOT unknown.
Pool separation suppresses the pool edge only, not the corporate-group
rule. Optional189(5) substitutions are an explicit election, restricted to
this count. Original/effective legal memberships and completeness of the
relevant portfolio are external qualifications, never inferred from IDs.

Output unit: `single_names`. Sources: `DR:article-190:1`, `DR:article-190:2`.

Fixed example: `default-grouping-baseline-same-group`. 148 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'default-grouping-baseline-same-group')
context = replace(base, **case.get('context', {}))
result = s2.default_single_name_count(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "exposures": {
    "a": {
      "counterparty_id": "A",
      "group_id": "G",
      "pool_id": null
    },
    "b": {
      "counterparty_id": "B",
      "group_id": "G",
      "pool_id": null
    }
  },
  "pool_treatment": {},
  "grouping_reference": "SYN-qualified-complete-relationships"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_derivative_netting_value

```python
solvency2.counterparty.default_derivative_netting_value(positions: Mapping, *, netting_qualified: bool | None, liabilities_settled_before_clearing: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Combine market values, never stand-alone RM, collateral stress or LGD.

All values must already be in context currency and Article75-compatible.
Netting eligibility and completeness of the set remain externally assessed.
Fraction over decimal float representations prevents intermediate overflow
and preserves signed cancellation. Only the final value becomes float.

Output unit: `context currency`. Sources: `DR:article-192:1`, `DR:article-192:3d:a`.

Fixed example: `derivative-netting-baseline-single`. 58 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'derivative-netting-baseline-single')
context = replace(base, **case.get('context', {}))
result = s2.default_derivative_netting_value(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "positions": {
    "p0": {
      "market_value": 100,
      "counterparty_id": "CP",
      "netting_agreement_id": "N"
    }
  },
  "netting_qualified": true,
  "liabilities_settled_before_clearing": false,
  "qualification_reference": "SYN-qualified-netting-set"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_protected_probability

```python
solvency2.counterparty.default_protected_probability(original_pd: float, *, substitute_provider: bool | None, protection: Optional[Mapping], clearing_category: str | None, qualification_reference: str, context: solvency2._core.core.Context, central_government_guarantee: Optional[Mapping] = None)
```

Select a qualified provider PD, never the minimum of two probabilities.

Full protection and Articles209–215 compliance are externally assessed.
Clearing precedence is explicit. This does not regroup names under189(5),
change LGD, or infer sovereign zero-PD eligibility from a provider identity.

Output unit: `probability`. Sources: `DR:article-199:10`, `DR:article-199:12-13`.

Fixed example: `protected-pd-baseline-original`. 96 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'protected-pd-baseline-original')
context = replace(base, **case.get('context', {}))
result = s2.default_protected_probability(**case['kwargs'], context=context)
# Independent expected value: 0.042
```

Example input (JSON):

```json
{
  "original_pd": 0.042,
  "substitute_provider": false,
  "protection": null,
  "clearing_category": "none",
  "qualification_reference": "SYN-199-10-external-qualification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### default_clearing_conditions

```python
solvency2.counterparty.default_clearing_conditions(route: str, conditions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check one externally selected clearing route, not legal eligibility.

A failed declaration screen never implies zero capital or a fallback LGD
branch. The client joint-default exception relaxes only the named joint
failure case. Historical legal opinions must not substitute for the changed
2027 legal-review requirement. Direct own-account clearing is future-only.

Output unit: `indicator`. Sources: `DR:article-192a`.

Fixed example: `clearing-conditions-future-member_own_account-all`. 77 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'clearing-conditions-future-member_own_account-all')
context = replace(base, **case.get('context', {}))
result = s2.default_clearing_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "route": "member_own_account",
  "conditions": {
    "own_account_clearing_member_trade": true,
    "qualified_ccp": true
  },
  "qualification_reference": "SYN-qualified-clearing-route"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### simplified_reinsurance_mitigation

```python
solvency2.counterparty.simplified_reinsurance_mitigation(recoverables: Mapping[str, float], target_counterparty: str, scr_without: float, scr_with: float, *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Allocate underwriting mitigation using BE recoverables plus related debtors.

Only the target's nonnegative condition is imposed on individual recoveries;
other signed entries are not silently floored or the resulting share capped.

Output unit: `context currency`. Sources: `DR:article-107:1-2`, `DR:article-196`.

Fixed example: `mitigation-baseline-negative-total-effect`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mitigation-baseline-negative-total-effect')
context = replace(base, **case.get('context', {}))
result = s2.simplified_reinsurance_mitigation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "recoverables": {
    "A": 30,
    "B": 70
  },
  "target_counterparty": "A",
  "scr_without": 40,
  "scr_with": 60,
  "eligibility_reference": "SYN-88-specific-scope",
  "valuation_reference": "SYN-complete-valuations"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### simplified_proportional_mitigation

```python
solvency2.counterparty.simplified_proportional_mitigation(gross_best_estimate: float, recoverables: Mapping[str, float], submodule_scr: float, target_counterparty: str, *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Article108 proportional-contract amount with the prescribed net-BE denominator.

Output unit: `context currency`. Sources: `DR:article-108`, `DR:article-196`.

Fixed example: `mitigation-baseline-proportional-zero`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mitigation-baseline-proportional-zero')
context = replace(base, **case.get('context', {}))
result = s2.simplified_proportional_mitigation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "gross_best_estimate": 200,
  "recoverables": {
    "A": 0,
    "B": 70
  },
  "submodule_scr": 50,
  "target_counterparty": "A",
  "eligibility_reference": "SYN-88-specific-scope",
  "valuation_reference": "SYN-complete-valuations"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### simplified_ead_mitigation_2027

```python
solvency2.counterparty.simplified_ead_mitigation_2027(exposures: Mapping[str, float], target_counterparty: str, bscr_without: float, bscr_with: float, *, default_module_zero_in_both: bool, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Allocate default-zero BSCR mitigation using absolute EAD by external counterparty.

Reinsurance/securitisation EAD here is BE recoverables under107a(2), not
automatically the BE-plus-debtors basis of107. Derivative/SPV EAD is external.
A complete scoped portfolio and both hypothetical BSCR valuations are required.

Output unit: `context currency`. Sources: `DR:article-107a:1-3`, `DR:article-196`.

Fixed example: `mitigation-future-ead-floor`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mitigation-future-ead-floor')
context = replace(base, **case.get('context', {}))
result = s2.simplified_ead_mitigation_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposures": {
    "A": -30,
    "B": 70
  },
  "target_counterparty": "A",
  "bscr_without": 70,
  "bscr_with": 80,
  "default_module_zero_in_both": true,
  "eligibility_reference": "SYN-88-specific-scope",
  "valuation_reference": "SYN-complete-valuations"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### simplified_default_group_pd

```python
solvency2.counterparty.simplified_default_group_pd(probabilities: Mapping[str, float], *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context, pool_rating_group: Optional[Mapping[str, dict]] = None)
```

Conservative grouping PD, not LGD-weighted single-name PD under Article199.

Output unit: `probability`. Sources: `DR:article-110`.

Fixed example: `mitigation-baseline-zero-pd`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mitigation-baseline-zero-pd')
context = replace(base, **case.get('context', {}))
result = s2.simplified_default_group_pd(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "probabilities": {
    "A": 0,
    "B": 0
  },
  "eligibility_reference": "SYN-88-specific-scope",
  "valuation_reference": "SYN-complete-valuations"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### simplified_submodule_mitigation

```python
solvency2.counterparty.simplified_submodule_mitigation(scr_without: Mapping[str, float], scr_with: Mapping[str, float], *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Floor the difference of submodule sums once, not each submodule separately.

Output unit: `context currency`. Sources: `DR:article-111`, `DR:article-196`.

Fixed example: `mitigation-baseline-sum-floor`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mitigation-baseline-sum-floor')
context = replace(base, **case.get('context', {}))
result = s2.simplified_submodule_mitigation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "scr_without": {
    "A": 10
  },
  "scr_with": {
    "A": 20
  },
  "eligibility_reference": "SYN-88-specific-scope",
  "valuation_reference": "SYN-complete-valuations"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### simplified_pool_member_best_estimate

```python
solvency2.counterparty.simplified_pool_member_best_estimate(undertaking_best_estimate: float, undertaking_share: float, counterparty_share: float, *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

PC/PU times already externally netted BEU; do not net external recoveries twice.

Output unit: `context currency`. Sources: `DR:article-109:a`, `DR:article-194:1:d`.

Fixed example: `pool-simplified-baseline-member-zero`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'pool-simplified-baseline-member-zero')
context = replace(base, **case.get('context', {}))
result = s2.simplified_pool_member_best_estimate(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "undertaking_best_estimate": 100,
  "undertaking_share": 0.2,
  "counterparty_share": 0,
  "eligibility_reference": "SYN-88-pool-scope",
  "valuation_reference": "SYN-pool-values"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### simplified_pool_external_best_estimate

```python
solvency2.counterparty.simplified_pool_external_best_estimate(ceded_best_estimate: float, undertaking_share: float, *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Scale externally qualified BECEP to whole-pool BECE, retaining its sign.

Output unit: `context currency`. Sources: `DR:article-109:b`, `DR:article-195:c`.

Fixed example: `pool-simplified-baseline-external-zero`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'pool-simplified-baseline-external-zero')
context = replace(base, **case.get('context', {}))
result = s2.simplified_pool_external_best_estimate(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "ceded_best_estimate": 0,
  "undertaking_share": 0.2,
  "eligibility_reference": "SYN-88-pool-scope",
  "valuation_reference": "SYN-pool-values"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### simplified_pool_external_mitigation

```python
solvency2.counterparty.simplified_pool_external_mitigation(best_estimates: Mapping[str, float], target_counterparty: str, total_external_contribution: float, *, eligibility_reference: str, valuation_reference: str, context: solvency2._core.core.Context)
```

Allocate signed external pool contributions; no extra floor on individual contributions.

Output unit: `context currency`. Sources: `DR:article-109:c`, `DR:article-195:d`.

Fixed example: `pool-simplified-baseline-contribution`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'pool-simplified-baseline-contribution')
context = replace(base, **case.get('context', {}))
result = s2.simplified_pool_external_mitigation(**case['kwargs'], context=context)
# Independent expected value: 10
```

Example input (JSON):

```json
{
  "best_estimates": {
    "A": 100,
    "B": 300
  },
  "target_counterparty": "A",
  "total_external_contribution": 40,
  "eligibility_reference": "SYN-88-pool-scope",
  "valuation_reference": "SYN-pool-values"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_ccp_fund_lgd_2027

```python
solvency2.counterparty.default_ccp_fund_lgd_2027(contribution: float, prefunded: bool, *, qualification_reference: str, context: solvency2._core.core.Context)
```

LGD of an externally qualified CCP default-fund contribution, not CCP eligibility.

Output unit: `context currency`. Sources: `DR:article-192:7-8`.

Fixed example: `default-2027-ccp-fund-true`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'default-2027-ccp-fund-true')
context = replace(base, **case.get('context', {}))
result = s2.default_ccp_fund_lgd_2027(**case['kwargs'], context=context)
# Independent expected value: 18
```

Example input (JSON):

```json
{
  "contribution": 100,
  "prefunded": true,
  "qualification_reference": "SYN-qualified-CCP-fund"
}
```

### default_defaulted_loan_lgd_2027

```python
solvency2.counterparty.default_defaulted_loan_lgd_2027(loan: float, recoverables: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Article192(4a) floor; Loan is the source-defined qualified mortgage value.

Classification and guideline-compliant recovery valuation are external. This
does not extend the source-defined scope to arbitrary unsecured loans.

Output unit: `context currency`. Sources: `DR:article-192:4a`.

Fixed example: `default-2027-loan-0-0`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'default-2027-loan-0-0')
context = replace(base, **case.get('context', {}))
result = s2.default_defaulted_loan_lgd_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "loan": 0,
  "recoverables": 0,
  "qualification_reference": "SYN-qualified-DR192-4a-mortgage-value-and-recoveries"
}
```

### default_type2_shock_2027

```python
solvency2.counterparty.default_type2_shock_2027(overdue_intermediary_lgd: float, defaulted_forborne_lgd: float, other_lgd: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Three disjoint2027 LGD pools; no implicit zero for defaulted/forborne loans.

Inputs are qualified externally and the residual pool excludes both special
pools. The result is the exposure-value shock, not a completed BOF revaluation.

Output unit: `context currency`. Sources: `DR:article-202`.

Fixed example: `default-2027-type2-4`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'default-2027-type2-4')
context = replace(base, **case.get('context', {}))
result = s2.default_type2_shock_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "overdue_intermediary_lgd": 0,
  "defaulted_forborne_lgd": 0,
  "other_lgd": 0,
  "qualification_reference": "SYN-complete-disjoint-qualified-LGD-pools"
}
```

### default_probability

```python
solvency2.counterparty.default_probability(category: str, *, classification_reference: str, credit_quality_step: str | None = None, solvency_ratio: float | None = None, mcr_compliant: bool | None = None, sfcr_published: bool | None = None, context: solvency2._core.core.Context)
```

Apply an externally qualified Article 199 category; not a rating/classification engine.

Clearing exceptions in (12)/(13) take precedence in the external category
decision. A 'rated' call cannot establish that those exceptions are absent.

Output unit: `probability`. Sources: `DR:article-199:2-9`, `DR:article-199:12-13`.

Fixed example: `pd-other`. 61 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'pd-other')
context = replace(base, **case.get('context', {}))
result = s2.default_probability(**case['kwargs'], context=context)
# Independent expected value: 0.042
```

Example input (JSON):

```json
{
  "category": "other",
  "classification_reference": "SYN-CLASS"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_single_name_pd

```python
solvency2.counterparty.default_single_name_pd(exposures: Mapping[str, dict], *, grouping_reference: str, context: solvency2._core.core.Context)
```

LGD-weighted PD for one externally grouped single name, not legal grouping.

Output unit: `probability`. Sources: `DR:article-199:1`.

Fixed example: `pd-weighted-zero`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'pd-weighted-zero')
context = replace(base, **case.get('context', {}))
result = s2.default_single_name_pd(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposures": {
    "A": {
      "pd": 0,
      "lgd": 25
    }
  },
  "grouping_reference": "SYN-GROUP"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_collateral_factor

```python
solvency2.counterparty.default_collateral_factor(factor_type: str, *, collateral_ignored_in_estate_share: bool | None, legal_reference: str, context: solvency2._core.core.Context)
```

Select a coefficient, not an insolvency-law interpretation or collateral valuation.

Output unit: `ratio`. Sources: `DR:article-197:7`.

Fixed example: `future-lgd-factor-F-true`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-lgd-factor-F-true')
context = replace(base, **case.get('context', {}))
result = s2.default_collateral_factor(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "factor_type": "F",
  "collateral_ignored_in_estate_share": true,
  "legal_reference": "SYN-ESTATE"
}
```

### default_derivative_lgd

```python
solvency2.counterparty.default_derivative_lgd(derivative_value: float, risk_mitigation: float, collateral_value: float, *, variant: str, collateral_basis: str, collateral_ignored_in_estate_share: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Four externally qualified variants, with explicit market/risk-adjusted collateral.

For a qualified netting set, RM and collateral must be assessed at set level;
summing stand-alone risk mitigation is not justified by this function.

Output unit: `context currency`. Sources: `DR:article-192:3-3c`, `DR:article-197:7`.

Fixed example: `future-lgd-derivative-3-true`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-lgd-derivative-3-true')
context = replace(base, **case.get('context', {}))
result = s2.default_derivative_lgd(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "derivative_value": 100,
  "risk_mitigation": 20,
  "collateral_value": 40,
  "variant": "3",
  "collateral_basis": "market_value",
  "collateral_ignored_in_estate_share": true,
  "qualification_reference": "SYN-DERIVATIVE"
}
```

### default_mortgage_lgd

```python
solvency2.counterparty.default_mortgage_lgd(loan_value: float, risk_adjusted_mortgage: float, eligible_guarantee: float, *, qualification_reference: str, context: solvency2._core.core.Context, guarantee_conditions: Optional[Mapping] = None)
```

Use a qualified stress guarantee, not an arbitrary guarantee nominal amount.

The future Article192(4) adds a floor on the non-guaranteed loan value.
Historical results retain the published zero floor, not the new 5% floor.

Output unit: `context currency`. Sources: `DR:article-192:4`.

Fixed example: `lgd-mortgage-10`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'lgd-mortgage-10')
context = replace(base, **case.get('context', {}))
result = s2.default_mortgage_lgd(**case['kwargs'], context=context)
# Independent expected value: 10
```

Example input (JSON):

```json
{
  "loan_value": 100,
  "risk_adjusted_mortgage": 100,
  "eligible_guarantee": 10,
  "qualification_reference": "SYN-MORTGAGE"
}
```

### default_reinsurance_lgd

```python
solvency2.counterparty.default_reinsurance_lgd(recoverables: float, risk_mitigation: float, risk_adjusted_collateral: float, *, counterparty_is_insurer: bool | None, collateral_ignored_in_estate_share: bool | None, qualification_reference: str, encumbered_asset_fraction: float | None = None, context: solvency2._core.core.Context, method: str = 'standard', proportionality_reference: str | None = None)
```

Choose standard/high-encumbrance formula; input includes corresponding receivables.

This SCR LGD is distinct from the technical-provisions loss in Article42.
Netting, collateral eligibility and contract qualifications remain external.

Output unit: `context currency`. Sources: `DR:article-192:2`, `DR:article-197:7`.

Fixed example: `lgd-ri-full-collateral`. 26 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'lgd-ri-full-collateral')
context = replace(base, **case.get('context', {}))
result = s2.default_reinsurance_lgd(**case['kwargs'], context=context)
# Independent expected value: 15
```

Example input (JSON):

```json
{
  "recoverables": 100,
  "risk_mitigation": 20,
  "risk_adjusted_collateral": 40,
  "counterparty_is_insurer": true,
  "encumbered_asset_fraction": 0.6,
  "collateral_ignored_in_estate_share": true,
  "qualification_reference": "SYN-RI"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_risk_mitigation

```python
solvency2.counterparty.default_risk_mitigation(scr_without: float, scr_with: float, *, valuation_reference: str, context: solvency2._core.core.Context)
```

Difference for the same relevant risk module; never substitute overall SCR.

Output unit: `context currency`. Sources: `DR:article-196`.

Fixed example: `future-lgd-rm-floor`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-lgd-rm-floor')
context = replace(base, **case.get('context', {}))
result = s2.default_risk_mitigation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "scr_without": 80,
  "scr_with": 100,
  "valuation_reference": "SYN-SAME-MODULE"
}
```

### default_other_lgd

```python
solvency2.counterparty.default_other_lgd(recognised_value: float, *, exposure_type: str, classification_reference: str, nominal_value: float | None = None, context: solvency2._core.core.Context)
```

Two externally classified nonnegative valuation conventions; no hidden offsetting.

Output unit: `context currency`. Sources: `DR:article-192:5-6`.

Fixed example: `future-lgd-other-receivable-0`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-lgd-other-receivable-0')
context = replace(base, **case.get('context', {}))
result = s2.default_other_lgd(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "recognised_value": 0,
  "exposure_type": "deposit_or_receivable",
  "classification_reference": "SYN-ART192-6"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### default_single_name_lgd

```python
solvency2.counterparty.default_single_name_lgd(exposure_lgds: Mapping[str, float], *, grouping_reference: str, context: solvency2._core.core.Context)
```

Sum already assessed LGDs; qualified netting sets must not be counted twice.

Output unit: `context currency`. Sources: `DR:article-192:1`.

Fixed example: `future-lgd-single-name-zero`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-lgd-single-name-zero')
context = replace(base, **case.get('context', {}))
result = s2.default_single_name_lgd(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposure_lgds": {
    "A": 0
  },
  "grouping_reference": "SYN-GROUP"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### default_collateral_market_adjustment

```python
solvency2.counterparty.default_collateral_market_adjustment(scr_without: float, scr_with: float, *, valuation_reference: str, context: solvency2._core.core.Context)
```

Literal document-profile order; signed adjustment, not collateral eligibility.

External valuations must assess FX against exposure/loan currency. Do not
silently reverse this source's subtraction or apply the Article196 floor.

Output unit: `context currency`. Sources: `DR:article-197:5-6`, `DR:article-198:3-4`.

Fixed example: `future-collateral-adjustment-negative`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-collateral-adjustment-negative')
context = replace(base, **case.get('context', {}))
result = s2.default_collateral_market_adjustment(**case['kwargs'], context=context)
# Independent expected value: -20
```

Example input (JSON):

```json
{
  "scr_without": 80,
  "scr_with": 100,
  "valuation_reference": "SYN-CURRENCY-RELATIVE"
}
```

### default_pool_lgd

```python
solvency2.counterparty.default_pool_lgd(best_estimate: float, risk_mitigation_contribution: float, risk_adjusted_collateral: float, *, variant: str, encumbered_asset_fraction: float, collateral_ignored_in_estate_share: bool | None, qualification_reference: str, undertaking_share: float | None = None, counterparty_share: float | None = None, context: solvency2._core.core.Context)
```

Externally qualified type B/C pool formula, not pool classification.

B uses already net BEC/BEU; C uses the whole pool's BECE. The recovery
threshold is inclusive, unlike Article192(2). DeltaRM is not halved.

Output unit: `context currency`. Sources: `DR:article-194`, `DR:article-195`, `DR:article-197:7`.

Fixed example: `future-pool-C-boundary`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-pool-C-boundary')
context = replace(base, **case.get('context', {}))
result = s2.default_pool_lgd(**case['kwargs'], context=context)
# Independent expected value: 17
```

Example input (JSON):

```json
{
  "best_estimate": 100,
  "risk_mitigation_contribution": 10,
  "risk_adjusted_collateral": 20,
  "variant": "C",
  "undertaking_share": 0.2,
  "encumbered_asset_fraction": 0.6,
  "collateral_ignored_in_estate_share": false,
  "qualification_reference": "SYN-POOL"
}
```

### default_pool_member_ratio

```python
solvency2.counterparty.default_pool_member_ratio(category: str, *, classification_reference: str, credit_quality_step: str | None = None, current_solvency_ratio: float | None = None, equivalent: bool | None = None, context: solvency2._core.core.Context)
```

Select the pool SR convention, not the counterparty PD table.

Output unit: `ratio`. Sources: `DR:article-193:1:e-g`.

Fixed example: `future-pool-member-rating-0`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-pool-member-rating-0')
context = replace(base, **case.get('context', {}))
result = s2.default_pool_member_ratio(**case['kwargs'], context=context)
# Independent expected value: 1.96
```

Example input (JSON):

```json
{
  "category": "rated",
  "credit_quality_step": "0",
  "classification_reference": "SYN"
}
```

### default_pool_solvency_ratio

```python
solvency2.counterparty.default_pool_solvency_ratio(in_scope_members: Mapping, out_of_scope_members: Mapping, *, membership_reference: str, context: solvency2._core.core.Context)
```

Harmonic EOF-weighted inner group plus risk-share-weighted outer group.

Membership must include any central intermediary. Zero inner SR requires
a separately assessed limiting case; it is not silently replaced by zero.

Output unit: `ratio`. Sources: `DR:article-193:1:a-d`, `DR:article-193:2`.

Fixed example: `future-pool-ratio-outside`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-pool-ratio-outside')
context = replace(base, **case.get('context', {}))
result = s2.default_pool_solvency_ratio(**case['kwargs'], context=context)
# Independent expected value: 1.1
```

Example input (JSON):

```json
{
  "in_scope_members": {},
  "out_of_scope_members": {
    "C": {
      "risk_share": 1,
      "solvency_ratio": 1.1
    }
  },
  "membership_reference": "SYN"
}
```

### default_pool_type_a_lgd

```python
solvency2.counterparty.default_pool_type_a_lgd(base_lgd: float, *, joint_liability: bool | None, qualification_reference: str, pool_solvency_ratio: float | None = None, context: solvency2._core.core.Context)
```

Apply type-A liability rule to an externally qualified Article192 LGD.

Low SR legitimately gives a risk-share factor above1 in this source;
there is no invented reduction-only clamp.

Output unit: `context currency`. Sources: `DR:article-193:1`.

Fixed example: `future-pool-A-proportional`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-pool-A-proportional')
context = replace(base, **case.get('context', {}))
result = s2.default_pool_type_a_lgd(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "base_lgd": 100,
  "joint_liability": false,
  "qualification_reference": "SYN"
}
```

### default_securities_financing_lgd_2027

```python
solvency2.counterparty.default_securities_financing_lgd_2027(exposure: float, risk_adjusted_collateral: float, *, netting_applied: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Qualified repo/reverse-repo/securities-lending LGD, not a netting engine.

Netted inputs must already represent the same legally qualified set's
economic effect; collateral is assessed at set level, not blindly summed.

Output unit: `context currency`. Sources: `DR:article-192:3e-3f`.

Fixed example: `future-lgd-financing-zero`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-lgd-financing-zero')
context = replace(base, **case.get('context', {}))
result = s2.default_securities_financing_lgd_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposure": 0,
  "risk_adjusted_collateral": 0,
  "netting_applied": false,
  "qualification_reference": "SYN-qualified-1923ef"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### default_risk_adjusted_collateral

```python
solvency2.counterparty.default_risk_adjusted_collateral(market_value: float, market_adjustment: float | None, *, collateral_type: str, conditions: Mapping[str, bool | None], qualification_reference: str, context: solvency2._core.core.Context, method: str = 'standard', proportionality_reference: str | None = None, custodian_assessment: Optional[Mapping] = None)
```

Literal collateral branches, with signed results and explicit legal evidence.

Article197(3) says neither condition is met. Mixed failure is therefore
not silently treated as zero. A negative result remains visible; downstream
LGD APIs explicitly reject collateral outside their nonnegative contract.
Article112 is an explicit alternative on market value, not an additional
haircut after a market adjustment. Article88 qualification stays external.
Optional Article214(2) assessment checks the deposit institution's CQS;
its legal applicability and all other Article214 conditions stay external.
Omission preserves the qualified-input API, not a numeric eligibility check.

Output unit: `context currency`. Sources: `DR:article-197:1-4`.

Fixed example: `risk-adjusted-collateral-baseline-title`. 50 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'risk-adjusted-collateral-baseline-title')
context = replace(base, **case.get('context', {}))
result = s2.default_risk_adjusted_collateral(**case['kwargs'], context=context)
# Independent expected value: 80
```

Example input (JSON):

```json
{
  "market_value": 100,
  "market_adjustment": 20,
  "collateral_type": "title_transfer",
  "conditions": {
    "article214_compliant": true
  },
  "qualification_reference": "SYN-art214-rights"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### default_risk_adjusted_mortgage

```python
solvency2.counterparty.default_risk_adjusted_mortgage(property_value: float, market_adjustment: float, *, valuation_reference: str, context: solvency2._core.core.Context)
```

Subtract adjustment from externally assessed Article198(2) property value.

Monitoring, prior claims and the independent valuation's market-value cap
must already be reflected in property_value; no appraisal is invented here.

Output unit: `context currency`. Sources: `DR:article-198:1-2`.

Fixed example: `risk-adjusted-mortgage-baseline-zero`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'risk-adjusted-mortgage-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.default_risk_adjusted_mortgage(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "property_value": 0,
  "market_adjustment": 0,
  "valuation_reference": "SYN-external1982"
}
```

### default_type1

```python
solvency2.counterparty.default_type1(counterparties: list[dict], *, context: solvency2._core.core.Context, method: str = 'standard', proportionality_reference: str | None = None)
```

Type-1 variance and charge; PD/LGD supplied per already grouped single name.

Output unit: `context currency`. Sources: `DR:article-200`, `DR:article-201`.

Fixed example: `default-2027-type1-single-0`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'default-2027-type1-single-0')
context = replace(base, **case.get('context', {}))
result = s2.default_type1(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "counterparties": [
    {
      "id": "SYN-A",
      "pd": 0,
      "lgd": 100
    }
  ]
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### default_type2_shock

```python
solvency2.counterparty.default_type2_shock(overdue_intermediary_lgd: float, other_lgd: float, *, context: solvency2._core.core.Context)
```

Value-decrease amount; BOF must still be revalued to determine the capital charge.

Output unit: `context currency`. Sources: `DR:article-202`.

Fixed example: `type2-shock`. 1 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'type2-shock')
context = replace(base, **case.get('context', {}))
result = s2.default_type2_shock(**case['kwargs'], context=context)
# Independent expected value: 120
```

Example input (JSON):

```json
{
  "overdue_intermediary_lgd": 100,
  "other_lgd": 200
}
```

## solvency2.governance

### governance_evidence_check

```python
solvency2.governance.governance_evidence_check(evidence: Mapping, conditions: Mapping, *, assessment_reference: str, supervisory_policy_interval_years: float | None = None, non_snc_policy_approval_reference: str | None = None, de_ppp_assessment: Optional[Mapping] = None, guidance_assessment: Optional[Mapping] = None, liquidity_assessment: Optional[Mapping] = None, context: solvency2._core.core.Context)
```

Inventory applicable declared controls and expose versioned review periods.

No references are retrieved, substantive evidence reviewed, or actual calendar
deadlines monitored. Combination eligibility is conditional on external facts.
The optional29d/327d approval changes only the policy-review maximum, not
function-combination approval or any other governance interval.
Optional archived guidance requires its own explicit applicability reference;
omission is NOT_ASSESSED, never a statement that the guidelines do not apply.
Optional2027 liquidity_assessment separates solo/group plans, exemptions and
supervisory measures; no cashflow projection or supervisory decision is made.

Output unit: `indicator`. Sources: `DIR:articles-40-49`, `DR:articles-258-275a`.

Fixed example: `proportionality-scope-approved-policies-five`. 92 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'proportionality-scope-approved-policies-five')
context = replace(base, **case.get('context', {}))
result = s2.governance_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 1
```

Inspect `case['kwargs']` for the complete nested input mapping (kept in the bundled dataset rather than duplicated here).

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### governance_remuneration_deferral_years

```python
solvency2.governance.governance_remuneration_deferral_years(annual_variable: float, annual_total: float, *, supervisory_exception_denied: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Minimum deferral period for an externally qualified relevant staff member.

No prescribed significant-deferred-share percentage is invented. This is not
permission to ignore payment sustainability, vesting or malus/clawback rules.

Output unit: `years`. Sources: `DR:article-275:2:c`.

Fixed example: `governance-pay-baseline-zero`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'governance-pay-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.governance_remuneration_deferral_years(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "annual_variable": 0,
  "annual_total": 0,
  "supervisory_exception_denied": false,
  "qualification_reference": "SYN-qualified-relevant-employee-remuneration"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### de_liquidity_coverage

```python
solvency2.governance.de_liquidity_coverage(gross_inflows: float, gross_outflows: float, realisable_cash: float, total_investments: float, *, source_version: str, applicability_reference: str, horizon_reference: str, context: solvency2._core.core.Context)
```

Coverage, cash-flow gap and liquidity level for one qualified horizon.

Inflows and cash are disjoint sources; no netting or double counting.
Projections, liquidation assumptions and scenarios are insurer inputs.
The circular specifies no universal minimum ratio or fixed time bands.

Output unit: `ratio`. Sources: `DE_BAFIN_PPP:05/2025:14`.

Fixed example: `de-close-baseline-liquidity-zero-assets`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'de-close-baseline-liquidity-zero-assets')
context = replace(base, **case.get('context', {}))
result = s2.de_liquidity_coverage(**case['kwargs'], context=context)
# Independent expected value: 0.8
```

Example input (JSON):

```json
{
  "gross_inflows": 80,
  "gross_outflows": 100,
  "realisable_cash": 0,
  "total_investments": 0,
  "source_version": "05/2025",
  "applicability_reference": "SYN-DE-PPP",
  "horizon_reference": "SYN-disjoint-1month"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### orsa_core_evidence_check

```python
solvency2.governance.orsa_core_evidence_check(evidence: Mapping[str, dict], *, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory explicitly declared core evidence, not adequacy or compliance.

AVAILABLE means the caller supplies a reference; content is not inspected.
A value of1 certifies neither ORSA completeness nor a capital requirement.
Conditional comparisons, timing, recalibration and climate scenarios remain
separate. The 2027 table adds mandatory macro/liquidity/materiality topics.

Output unit: `indicator`. Sources: `DIR:article-45`, `DIR:article-45:7`, `DR:article-262`.

Fixed example: `orsa-evidence-baseline-empty`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-evidence-baseline-empty')
context = replace(base, **case.get('context', {}))
result = s2.orsa_core_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "assessment_reference": "SYN-versioned-ORSA-file"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### orsa_phase_in_currency_exemption_2027

```python
solvency2.governance.orsa_phase_in_currency_exemption_2027(currency_cashflows: float, extrapolated_currency_cashflows: float, total_cashflows: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Screen only the Article77a phase-in comparison exemption per currency.

Both denominators are ALL future cashflows. Do not substitute cashflows
in this currency for the denominator of the extrapolated-share test.
Signed raw cashflows need externally qualified aggregation, not abs/netting
guessed by the engine. No exemption for MA, VA or other transition tests.

Output unit: `indicator`. Sources: `DIR:article-45:2a:a-b`.

Fixed example: `orsa-phase-in-five`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-phase-in-five')
context = replace(base, **case.get('context', {}))
result = s2.orsa_phase_in_currency_exemption_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "currency_cashflows": 5,
  "extrapolated_currency_cashflows": 1,
  "total_cashflows": 100,
  "qualification_reference": "SYN-common-77a-cashflow-basis"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### orsa_biennial_captive_conditions_2027

```python
solvency2.governance.orsa_biennial_captive_conditions_2027(is_captive: bool, permitted_policyholders: bool, natural_person_tp_share: float, no_compulsory_liability: bool, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Declared captive eligibility for ORSA frequency, not DR89 simplification.

Permitted insureds/beneficiaries are group legal persons or natural persons
eligible under group insurance contracts. Their TP share must be STRICTLY
below5%. Qualification of persons/contracts and TP allocation is external.

Output unit: `indicator`. Sources: `DIR:article-45:5:b`.

Fixed example: `orsa-frequency-captive-boundary`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-frequency-captive-boundary')
context = replace(base, **case.get('context', {}))
result = s2.orsa_biennial_captive_conditions_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "is_captive": true,
  "permitted_policyholders": true,
  "natural_person_tp_share": 0.05,
  "no_compulsory_liability": true,
  "qualification_reference": "SYN-45-5-not-DR89"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### orsa_max_assessment_interval_2027

```python
solvency2.governance.orsa_max_assessment_interval_2027(small_non_complex: bool, qualifying_captive: bool, *, supervisory_interval_years: float | None = None, non_snc_approval_reference: str | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Maximum periodic interval; an event-triggered ORSA remains immediate.

The reference must cover classifications AND supervisory directions.
None declares no additional shorter supervisory interval, not ignorance.
No calendar deadline, timely completion or supervisory approval is inferred.
A separate29d/327e non-SNC approval can enable the reduced maximum;
classification remains false and the approval is not inferred from size.

Output unit: `years`. Sources: `DIR:article-45:5`.

Fixed example: `orsa-frequency-interval-true-true`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-frequency-interval-true-true')
context = replace(base, **case.get('context', {}))
result = s2.orsa_max_assessment_interval_2027(**case['kwargs'], context=context)
# Independent expected value: 2
```

Example input (JSON):

```json
{
  "small_non_complex": true,
  "qualifying_captive": true,
  "qualification_reference": "SYN-classification-and-supervision"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### orsa_conditional_evidence_check

```python
solvency2.governance.orsa_conditional_evidence_check(adjustments: Mapping[str, bool], uses_internal_model: bool, evidence: Mapping[str, dict], *, qualification_reference: str, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory conditional comparisons/recalibration, never calculate a model.

The phase-in flag means a comparison remains required after externally
qualified currency exemptions. Its false value is not inferred from
missing data. Comparability evidence is technical traceability, not a
prescribed projection method or an isolated-scenario requirement.

Output unit: `indicator`. Sources: `DIR:article-45:2a`, `DIR:article-45:3`.

Fixed example: `orsa-conditional-baseline-ma-missing`. 21 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-conditional-baseline-ma-missing')
context = replace(base, **case.get('context', {}))
result = s2.orsa_conditional_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "adjustments": {
    "matching_adjustment": true,
    "volatility_adjustment": false,
    "transition_308c": false,
    "transition_308d": false
  },
  "uses_internal_model": false,
  "evidence": {},
  "qualification_reference": "SYN-applicability",
  "assessment_reference": "SYN-assessment"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### orsa_additional_macro_analysis_required_2027

```python
solvency2.governance.orsa_additional_macro_analysis_required_2027(reasoned_supervisory_request: bool, small_non_complex: bool, prior_article29d_approval: bool, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Select only additional paragraph1(e) analysis; paragraph1(d) remains.

Group-level analysis is not an automatic exemption: the supervisor must
consider it under paragraph9. Approval/request/classification are external.

Output unit: `indicator`. Sources: `DIR:article-45:1:e`, `DIR:article-45:1b`.

Fixed example: `orsa-macro-true-true-true`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-macro-true-true-true')
context = replace(base, **case.get('context', {}))
result = s2.orsa_additional_macro_analysis_required_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "reasoned_supervisory_request": true,
  "small_non_complex": true,
  "prior_article29d_approval": true,
  "qualification_reference": "SYN"
}
```

### orsa_guidance_evidence_check

```python
solvency2.governance.orsa_guidance_evidence_check(evidence: Mapping[str, dict], conditions: Mapping[str, bool], *, qualification_reference: str, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory archived guideline evidence, not content or legal applicability.

Group/entity applicability and conditional needs are externally qualified.
Incompatible scope flags are rejected. The future table explicitly excludes
archived blanket annual frequency. Future frequency and expanded group scope
are handled by separate APIs, not approved by this inventory.

Output unit: `indicator`. Sources: `ORSA_GUIDANCE:guidelines-1-20`.

Fixed example: `orsa-guidance-future-ordinary-empty`. 27 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-guidance-future-ordinary-empty')
context = replace(base, **case.get('context', {}))
result = s2.orsa_guidance_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "conditions": {
    "group": false,
    "stress_analysis_needed": false,
    "different_valuation_basis": false,
    "single_document": false,
    "translation_requested": false,
    "application_translations_needed": false,
    "third_country_business": false
  },
  "qualification_reference": "SYN-guidance-scope",
  "assessment_reference": "SYN-ORSA"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### orsa_climate_scenario_requirement_2027

```python
solvency2.governance.orsa_climate_scenario_requirement_2027(material_climate_risk: bool, small_non_complex: bool, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Minimum scenario count from externally qualified materiality/SNC status.

Zero exempts no undertaking from the paragraph1 materiality assessment.
This is a requirement selector, not a finding that scenarios exist.

Output unit: `count`. Sources: `DIR:article-45a:1-2`, `DIR:article-45a:5`.

Fixed example: `orsa-climate-required-true-true`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-climate-required-true-true')
context = replace(base, **case.get('context', {}))
result = s2.orsa_climate_scenario_requirement_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "material_climate_risk": true,
  "small_non_complex": true,
  "qualification_reference": "SYN-classification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### orsa_climate_scenario_structure_2027

```python
solvency2.governance.orsa_climate_scenario_structure_2027(scenarios: Mapping[str, dict], impact_analysis_interval_years: float, scenario_review_interval_years: float, *, assessment_reference: str, context: solvency2._core.core.Context)
```

Check required role metadata and maximum intervals, never model adequacy.

'Significantly above' has no invented numeric cutoff: both >2 degrees and
an explicit external qualification are required. Additional scenarios can
remain in the external assessment; this input describes the two roles.
Intervals are declared years, not dates or an automatic scheduling service.

Output unit: `indicator`. Sources: `DIR:article-45a:2-4`.

Fixed example: `orsa-climate-low-boundary`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'orsa-climate-low-boundary')
context = replace(base, **case.get('context', {}))
result = s2.orsa_climate_scenario_structure_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "scenarios": {
    "below_two_degrees": {
      "reference": "SYN-low",
      "temperature_increase_celsius": 2,
      "long_term": true
    },
    "significantly_above_two_degrees": {
      "reference": "SYN-high",
      "temperature_increase_celsius": 3,
      "long_term": true,
      "significantly_above_qualified": true
    }
  },
  "impact_analysis_interval_years": 3,
  "scenario_review_interval_years": 3,
  "assessment_reference": "SYN-climate"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

## solvency2.context

### significant_cross_border_activity_2027

```python
solvency2.context.significant_cross_border_activity_2027(host_gross_premiums: float, *, small_non_complex: bool, host_authority_significant: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

One host state's establishment AND services premiums; strict EUR threshold.

The host authority's materiality decision is explicit, never inferred from
market shares. SNC exclusion applies to both branches. This definition is
not the different significant-branch screen in delegated Article354.

Output unit: `indicator`. Sources: `DIR:article-152aa:1`.

Fixed example: `future-close-cross-host`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-close-cross-host')
context = replace(base, **case.get('context', {}))
result = s2.significant_cross_border_activity_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "host_gross_premiums": 1,
  "small_non_complex": false,
  "host_authority_significant": true,
  "qualification_reference": "SYN-future-closing-qualified"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### proportionality_application_evidence_2027

```python
solvency2.context.proportionality_application_evidence_2027(evidence: Mapping, *, route: str, measure_list_changed: bool, measure_ceased: bool, supervisory_restriction: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Application/notification inventory, separate from annual size screens.

The qualification reference identifies the actual measure, classification,
specific approval/conditions or pre-existing2025 transitional entitlement.
Metadata exposes authority periods without calculating a decision deadline
or manufacturing approval through silence. Fiscal-year counting is external.

Output unit: `indicator`. Sources: `DIR:articles-29c-29e`.

Fixed example: `future-close-prop-snc-missing`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-close-prop-snc-missing')
context = replace(base, **case.get('context', {}))
result = s2.proportionality_application_evidence_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "route": "snc",
  "measure_list_changed": true,
  "measure_ceased": true,
  "supervisory_restriction": false,
  "qualification_reference": "SYN-future-closing-qualified",
  "evidence": {}
}
```

### CalculationError

```python
solvency2.context.CalculationError(code: 'str', field: 'str', message: 'str')
```

Controlled failure with a machine-readable code and offending field.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### Context

```python
solvency2.context.Context(as_of: 'str', known_at: 'str', currency: 'str', profile_id: 'str', mode: 'str' = 'REFERENCE_ONLY', overrides: 'tuple[NumericOverride, ...]' = ()) -> None
```

Snapshot reference context; deliberately not a regulatory sign-off.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### Result

```python
solvency2.context.Result(value: 'float', unit: 'str', formula_id: 'str', sources: 'tuple[str, ...]', context: 'Context', input_hash: 'str', profile_hash: 'str', details: 'dict', status: 'str' = 'REFERENCE_COMPONENT') -> None
```

Result(value: 'float', unit: 'str', formula_id: 'str', sources: 'tuple[str, ...]', context: 'Context', input_hash: 'str', profile_hash: 'str', details: 'dict', status: 'str' = 'REFERENCE_COMPONENT')

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### small_non_complex_annual_conditions_2027

```python
solvency2.context.small_non_complex_annual_conditions_2027(undertaking_type: str, metrics: Mapping, conditions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

One qualified year of Article29a criteria, not two-year status or approval.

The three-year average NET combined ratio is externally qualified: the
source does not prescribe a universal weighting method for its construction.
investment_default_scr is only the listed investment exposures, not the
whole default module. Intangible charge follows the existing Article203 API.
Captive alternative never overrides the Article29a(3) absolute exclusions.

Output unit: `indicator`. Sources: `DIR:article-29a:1-3`, `DR:article-327a`.

Fixed example: `proportionality-scope-parent-small-group`. 25 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'proportionality-scope-parent-small-group')
context = replace(base, **case.get('context', {}))
result = s2.small_non_complex_annual_conditions_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "undertaking_type": "life",
  "metrics": {
    "life_gross_tp": 1000000000,
    "total_gross_tp": 1000000000,
    "nonlife_gwp": 0,
    "total_gwp": 100000000,
    "other_member_states_gwp": 19000000,
    "assumed_reinsurance_gwp": 50000000,
    "interest_scr": 50000000,
    "market_scr": 100000000,
    "investment_default_scr": 50000000,
    "intangible_scr": 50000000,
    "total_investments": 1000000000,
    "restricted_nonlife_gwp": 0,
    "net_combined_ratio_three_year_average": 0.99,
    "eligible_own_funds": 100000000,
    "scr": 100000000,
    "natural_person_tp": 0,
    "group_pension_fund_assets": 0
  },
  "conditions": {
    "is_captive": false,
    "captive_insureds_qualify": false,
    "compulsory_liability": false,
    "approved_internal_model": false,
    "parent_conglomerate_or_group": true,
    "group_is_small_non_complex": true,
    "parent_article228_entity": false
  },
  "qualification_reference": "SYN-one-year-qualified-metrics-not-classification"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### non_snc_proportionality_size_screen_2027

```python
solvency2.context.non_snc_proportionality_size_screen_2027(measure: str, undertaking_type: str, life_gross_tp: float, total_gross_tp: float, nonlife_gwp: float, total_gwp: float, market_shares: Mapping, *, size_exception_confirmed: bool | None, exception_reference: str | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Shared327b/c/d/e/g size component; each measure's other conditions remain.

A declared low-risk supervisory exception applies ONLY to size condition c,
never to all governance/ORSA/liquidity or actual approval requirements.
The existing327f prudent-deterministic screen is separate and unchanged.

Output unit: `indicator`. Sources: `DR:articles-327b-327e`, `DR:article-327g`.

Fixed example: `proportionality-scope-non-snc-rsr`. 13 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'proportionality-scope-non-snc-rsr')
context = replace(base, **case.get('context', {}))
result = s2.non_snc_proportionality_size_screen_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "measure": "rsr",
  "undertaking_type": "composite",
  "life_gross_tp": 12000000000,
  "total_gross_tp": 60000000000,
  "nonlife_gwp": 2000000000,
  "total_gwp": 5000000000,
  "market_shares": {
    "life": 0.05,
    "nonlife": 0.05
  },
  "size_exception_confirmed": false,
  "qualification_reference": "SYN-qualified-home-market-bases"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### regulatory_euro_amount_indexation

```python
solvency2.context.regulatory_euro_amount_indexation(base_amount: float, last_published_amount: float, cumulative_inflation: float, inflation_since_last_adjustment: float, *, review_due: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Original EUR base times HICP change since31Dec2015, rounded upward.

Review schedule, Eurostat aggregate, original base and last publication are
qualified inputs. The output is a calculated proposal; it never changes
the existing ruleset's MCR/scope parameters or asserts national adoption.

Output unit: `EUR`. Sources: `DIR:article-300`.

Fixed example: `group-close-baseline-index-exact-grid`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-close-baseline-index-exact-grid')
context = replace(base, **case.get('context', {}))
result = s2.regulatory_euro_amount_indexation(**case['kwargs'], context=context)
# Independent expected value: 3600000
```

Example input (JSON):

```json
{
  "base_amount": 3000000,
  "last_published_amount": 3700000,
  "cumulative_inflation": 0.2,
  "inflation_since_last_adjustment": 0.05,
  "review_due": true,
  "qualification_reference": "SYN-original2015base-and-HICP-not-official-adoption"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### scope_volume_conditions

```python
solvency2.context.scope_volume_conditions(gross_written_premiums: float, gross_technical_provisions: float, reinsurance_written_premiums: float, reinsurance_technical_provisions: float, *, part_of_group: bool | None, group_gross_technical_provisions: float | None = None, has_disallowed_business: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Screen one year's literal Article4(1) conditions in the selected profile.

Inputs are externally qualified gross EUR amounts. No netting or zero floor
is inferred. Article4(2-5) time rules, authorisation and cross-border business
must be assessed separately; a result of1 is not a scope exemption.

Output unit: `indicator`. Sources: `DIR:article-4:1`, `DIR:article-16:1-2`.

Fixed example: `scope-volume-baseline-zero`. 38 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'scope-volume-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.scope_volume_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "gross_written_premiums": 0,
  "gross_technical_provisions": 0,
  "reinsurance_written_premiums": 0,
  "reinsurance_technical_provisions": 0,
  "part_of_group": false,
  "has_disallowed_business": false,
  "qualification_reference": "SYN-qualified-EUR-gross-volume"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### scope_ancillary_risk_conditions

```python
solvency2.context.scope_ancillary_risk_conditions(ancillary_branch: int, main_branch: int, *, main_risk_authorised: bool | None, linked_to_main: bool | None, same_object: bool | None, same_contract: bool | None, legal_expenses_exception: str | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply Article16's cross-branch conditions to external factual declarations.

Credit/surety remain prohibited. Legal expenses require the assistance main
branch and the explicitly declared travel or sea-vessel exception; all base
conditions still apply. This function does not grant or verify a licence.

Output unit: `indicator`. Sources: `DIR:article-16:1-2`, `DIR:annex-I:A`.

Fixed example: `scope-ancillary-baseline-ordinary`. 34 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'scope-ancillary-baseline-ordinary')
context = replace(base, **case.get('context', {}))
result = s2.scope_ancillary_risk_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "ancillary_branch": 13,
  "main_branch": 3,
  "main_risk_authorised": true,
  "linked_to_main": true,
  "same_object": true,
  "same_contract": true,
  "qualification_reference": "SYN-contract-and-authorisation"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### scope_volume_entry_trigger

```python
solvency2.context.scope_volume_entry_trigger(annual_exceedance: collections.abc.Sequence, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Three-year breach of one identified amount, for the following-year trigger.

Period consecutiveness and historically applicable thresholds are externally
qualified. Different monetary criteria must not be mixed within a series.
This component does not select an effective legal regime for the entity.

Output unit: `indicator`. Sources: `DIR:article-4:2`.

Fixed example: `scope-history-baseline-entry-all`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'scope-history-baseline-entry-all')
context = replace(base, **case.get('context', {}))
result = s2.scope_volume_entry_trigger(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "annual_exceedance": [
    true,
    true,
    true
  ],
  "qualification_reference": "SYN-consecutive-years-and-versioned-thresholds"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### scope_volume_release_history

```python
solvency2.context.scope_volume_release_history(past_any_exceedance: collections.abc.Sequence, forecast_any_exceedance: collections.abc.Sequence, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Only historical/prospective volume conditions, not supervisory release.

Forecasts are external. Cross-border activity, voluntary authorisation and
supervisory satisfaction remain separate, even when this indicator is1.

Output unit: `indicator`. Sources: `DIR:article-4:4:a-b`.

Fixed example: `scope-history-baseline-release-breach-0`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'scope-history-baseline-release-breach-0')
context = replace(base, **case.get('context', {}))
result = s2.scope_volume_release_history(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "past_any_exceedance": [
    true,
    false,
    false
  ],
  "forecast_any_exceedance": [
    false,
    false,
    false,
    false,
    false
  ],
  "qualification_reference": "SYN-consecutive-years-and-versioned-thresholds"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

## solvency2.groups

### group_long_term_equity_limit_2027

```python
solvency2.groups.group_long_term_equity_limit_2027(full_amounts: Mapping, proportional_amounts: Mapping, *, supervisory_recalculation_required: bool, recalculated_full_amount: float | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Method1/combined LTE cap, not group SCR or an automatic classification.

Article335(1)a amounts enter in full,335(1)c proportionally. On a qualified
supervisory request replace only1(a) with the externally recomputed amount.

Output unit: `context currency`. Sources: `DIR:article-233b`, `DR:article-336a`.

Fixed example: `future-close-group-zero`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-close-group-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_long_term_equity_limit_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "full_amounts": {},
  "proportional_amounts": {},
  "supervisory_recalculation_required": false,
  "recalculated_full_amount": null,
  "qualification_reference": "SYN-group-method1"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### group_insurance_holding_conditions_2027

```python
solvency2.groups.group_insurance_holding_conditions_2027(indicator_shares: Mapping, other_supervisory_shares: Mapping, conditions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Declared holding criteria, not an automatic group or entity classification.

Shares must use the precisely qualified212(1)f(vi) consolidated perimeter.
Do not cap ratios at1: offsetting consolidated amounts can change ratios.
Ongoing satisfaction and the other legal conditions remain external facts.

Output unit: `indicator`. Sources: `DIR:article-212:1:f`.

Fixed example: `holding-definition-equal`. 13 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'holding-definition-equal')
context = replace(base, **case.get('context', {}))
result = s2.group_insurance_holding_conditions_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "indicator_shares": {
    "equity": 0.5,
    "assets": 0.5,
    "revenue": 0.5,
    "employees": 0.5
  },
  "other_supervisory_shares": {},
  "conditions": {
    "parent_undertaking": true,
    "not_excluded_regulated_undertaking": true,
    "not_mixed_or_financial_holding": true,
    "insurance_or_reinsurance_subsidiary": true,
    "qualifying_principal_activity": true,
    "continuous_indicator_basis": true
  },
  "qualification_reference": "SYN-consolidated-holding-scope-and-continuous-criteria"
}
```

### group_model_scr_contribution

```python
solvency2.groups.group_model_scr_contribution(entity: str, model_outputs: collections.abc.Mapping, *, complete_scope_confirmed: bool, model_reference: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply externally supplied model percentages; never develop an insurer model.

The full declared entity set is checked before selecting one contribution.
A1e-12 numerical sum tolerance is not regulatory materiality. Percentages
are never renormalised, and neither ownership weights nor the future6a
standard-formula cap are applied to this separate6b branch.

Output unit: `context currency`. Sources: `DR:article-330:6:b`.

Fixed example: `group-model-baseline-zero-share`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-model-baseline-zero-share')
context = replace(base, **case.get('context', {}))
result = s2.group_model_scr_contribution(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "entity": "child",
  "model_outputs": {
    "child": {
      "scr": 625,
      "allocation_share": 0
    },
    "parent": {
      "scr": 250,
      "allocation_share": 1
    }
  },
  "complete_scope_confirmed": true,
  "model_reference": "SYN-approved-model-version-scope",
  "qualification_reference": "SYN-complete-model-output-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### group_nonavailable_own_funds_cap

```python
solvency2.groups.group_nonavailable_own_funds_cap(amount: float, scr_contribution: float, *, qualification_reference: str, context: solvency2._core.core.Context, related_insurer_scr: float | None = None)
```

Cap ONE externally qualified availability scope, without repeating the cap.

The caller must not re-use one entity contribution across separate items
and sum the individual results. This is neither an Article330(4) exemption
nor a computation of total available group own funds.
Historical DIR222(4) additionally limits its qualified(2)/(3)pool to the
related insurer SCR. That optional scope is not imposed on other pools,
nor carried into the future wording which instead uses the contribution.

Output unit: `currency`. Sources: `DR:article-330:5`.

Fixed example: `group-availability-baseline-cap-zero`. 27 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-availability-baseline-cap-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_nonavailable_own_funds_cap(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "amount": 0,
  "scr_contribution": 24,
  "qualification_reference": "SYN-qualified-single-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### group_minority_excess_2027

```python
solvency2.groups.group_minority_excess_2027(eligible_own_funds_net: float, other_nonavailable_own_funds_net: float, scr_contribution: float, parent_subscribed_capital_share: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Literal 2027 minority formula, on explicitly pre-qualified net amounts.

Both own-funds inputs exclude intra-group subordinated liabilities and
ancillary own funds. The other-nonavailable input also excludes paragraph4
items. A negative formula result is NOT an automatic own-funds credit.

Output unit: `currency`. Sources: `DR:article-330:4a`.

Fixed example: `group-availability-future-minority-zero`. 17 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-availability-future-minority-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_minority_excess_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "eligible_own_funds_net": 0,
  "other_nonavailable_own_funds_net": 0,
  "scr_contribution": 0,
  "parent_subscribed_capital_share": 0.75,
  "qualification_reference": "SYN-net-bases-and-subscribed-capital"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_own_funds_transfer_timing_screen

```python
solvency2.groups.group_own_funds_transfer_timing_screen(months_to_availability: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check only the declared nine-month horizon, not effective availability.

Output unit: `indicator`. Sources: `DR:article-330:1:c`.

Fixed example: `group-availability-baseline-timing-zero`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-availability-baseline-timing-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_own_funds_transfer_timing_screen(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "months_to_availability": 0,
  "qualification_reference": "SYN-qualified-timing"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### group_pre_acquisition_scr_exception_2027

```python
solvency2.groups.group_pre_acquisition_scr_exception_2027(related_financial_years: float, *, issued_before_joining: bool, included_in_group_calculation: bool, qualification_reference: str, context: solvency2._core.core.Context, group_supervision_years: float | None = None, orsa_support_confirmed: bool | None = None, issuer_type: str = 'eu_insurer')
```

Future pre-acquisition exception with an explicit issuer-specific effect.

The elapsed FINANCIAL-year measure is externally qualified. This screen
does not rewrite MCR, assign a tier, or waive other own-funds conditions.
Three YEARS of group supervision and the prescribed forward ORSA evidence
are additional mandatory gates. Insurers use331/332's solo-SCR definition;
qualified intermediate holdings/ancillary subsidiaries instead use333(4)'s
temporary disapplication of333(2)(a). These are not interchangeable effects.

Output unit: `indicator`. Sources: `DR:article-331:5`, `DR:article-332:3`, `DR:article-333:4`.

Fixed example: `group-availability-future-pre-acquisition-zero`. 29 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-availability-future-pre-acquisition-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_pre_acquisition_scr_exception_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "related_financial_years": 0,
  "issued_before_joining": true,
  "included_in_group_calculation": true,
  "qualification_reference": "SYN-qualified-financial-year-and-issuance",
  "group_supervision_years": 3,
  "orsa_support_confirmed": true
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_orsa_method1_scr_difference

```python
solvency2.groups.group_orsa_method1_scr_difference(related_scrs: Mapping[str, float], consolidated_scr: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Signed related-SCR sum minus consolidated SCR, never floored.

The externally qualified perimeter must match Article246(4), method1,
valuation date and currency. This arithmetic is not the required substantive
explanation of the difference, nor a release of diversification benefits.

Output unit: `currency`. Sources: `DIR:article-246:4`.

Fixed example: `group-orsa-baseline-zero`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-orsa-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_orsa_method1_scr_difference(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "related_scrs": {
    "A": 0
  },
  "consolidated_scr": 0,
  "qualification_reference": "SYN-method1-perimeter"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### group_orsa_evidence_check

```python
solvency2.groups.group_orsa_evidence_check(evidence: Mapping[str, dict], method1_applied: bool, single_document: bool, *, qualification_reference: str, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory group-ORSA scope, method1 and single-document evidence.

No consent is inferred from availability of a group document. Subsidiary
Article45 duties persist. The future profile separately includes material
non-insurance activities and actual/potential risks/interdependencies.

Output unit: `indicator`. Sources: `DIR:article-246:4`.

Fixed example: `group-orsa-baseline-missing-conditional`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-orsa-baseline-missing-conditional')
context = replace(base, **case.get('context', {}))
result = s2.group_orsa_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {
    "group_assessment": {
      "status": "AVAILABLE",
      "reference": "SYN-group_assessment"
    }
  },
  "method1_applied": true,
  "single_document": true,
  "qualification_reference": "SYN-group-scope",
  "assessment_reference": "SYN-group-ORSA"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### small_non_complex_group_annual_conditions_2027

```python
solvency2.groups.small_non_complex_group_annual_conditions_2027(method: str, metrics: Mapping, conditions: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Group213a annual criteria: NOT the solo29a business-share branching.

Group status/history and each method2 entity's SNC classification remain
externally qualified. Group premium cap is TOTAL GWP; group surplus must
be strictly positive. Two distinct foreign-premium criteria must both pass.
Interest TP basis explicitly excludes method2 entities. Method2-only waives
consolidated interest/investment tests, never the other group conditions.

Output unit: `indicator`. Sources: `DIR:article-213a:1-4`.

Fixed example: `group-close-fail-combined_ratio_three_year_average`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-close-fail-combined_ratio_three_year_average')
context = replace(base, **case.get('context', {}))
result = s2.small_non_complex_group_annual_conditions_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "method": "method1",
  "metrics": {
    "life_gross_tp": 1000000000,
    "consolidated_gross_tp_excluding_method2": 1000000000,
    "total_gwp": 100000000,
    "nonlife_gwp": 40000000,
    "foreign_member_gwp": 19999999,
    "foreign_business_gwp": 19999999,
    "interest_scr": 50000000,
    "market_scr": 100000000,
    "investment_default_scr": 50000000,
    "intangible_scr": 50000000,
    "total_investments": 1000000000,
    "restricted_nonlife_gwp": 12000000,
    "assumed_reinsurance_gwp": 50000000,
    "combined_ratio_three_year_average": 1,
    "group_surplus": 1
  },
  "conditions": {
    "has_non_nonlife_member": true,
    "has_non_life_member": true,
    "all_method2_entities_snc": true,
    "is_conglomerate": false,
    "has_article228_subsidiary": false,
    "approved_group_internal_model": false
  },
  "qualification_reference": "SYN-213a-qualified-group-one-year-no-status"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_sector_capital_requirement_2027

```python
solvency2.groups.group_sector_capital_requirement_2027(sector: str, requirements: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Select the prescribed maximum of complete externally calculated branches.

Bank inputs include applicable buffers/add-ons, not just Pillar1 minima.
Pension inputs cover both the required margin and national requirement.
This component implements no CRR, IFR, IORP or third-country valuation.

Output unit: `context currency`. Sources: `DIR:article-228:3:a:ii`, `DIR:article-228:3:e`.

Fixed example: `future-group-sector-bank-zero`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-sector-bank-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_sector_capital_requirement_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "sector": "credit_institution",
  "requirements": {
    "risk_based": 0,
    "leverage_based": 0
  },
  "qualification_reference": "SYN-sector-requirements-shares-and-availability"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_sector_contribution_2027

```python
solvency2.groups.group_sector_contribution_2027(entities: Mapping, *, measure: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Sum disjoint qualified sector amounts using subscribed-capital shares.

Eligible own funds must already reflect Article228 availability exclusions.
Subgroup inclusion, exclusion of its individual members and supervisory
decisions are externally qualified. Signed own funds are not floored.

Output unit: `context currency`. Sources: `DIR:article-221:1a`, `DIR:article-228:2-4`.

Fixed example: `future-group-sector-empty-eligible_own_funds`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-sector-empty-eligible_own_funds')
context = replace(base, **case.get('context', {}))
result = s2.group_sector_contribution_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "entities": {},
  "measure": "eligible_own_funds",
  "qualification_reference": "SYN-sector-requirements-shares-and-availability"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `UNSUPPORTED_PARAMETER`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_combined_component_surplus_2027

```python
solvency2.groups.group_combined_component_surplus_2027(consolidated_own_funds: float, consolidated_scr: float, minimum: float, method2_related: Mapping, sector_contributions: Mapping, method2_own_funds_adjustment: float, method2_capital_addon: float, *, approval_reference: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Compose externally approved disjoint methods, not a consolidation model.

Consolidated inputs already exclude M2/sector holdings and reflect required
currency sensitivity. Do not repeat pure-M2 participation-value deductions.
M2 insurer subsidiary deficits retain Article221 treatment; sector amounts
are already weighted and availability-adjusted under Article228.

Output unit: `context currency`. Sources: `DIR:article-233a:1-7`, `DIR:article-221:1`.

Fixed example: `future-group-combined-negative`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-combined-negative')
context = replace(base, **case.get('context', {}))
result = s2.group_combined_component_surplus_2027(**case['kwargs'], context=context)
# Independent expected value: -20
```

Example input (JSON):

```json
{
  "consolidated_own_funds": 30,
  "consolidated_scr": 40,
  "minimum": 50,
  "method2_related": {},
  "sector_contributions": {},
  "method2_own_funds_adjustment": 0,
  "method2_capital_addon": 0,
  "approval_reference": "SYN-combined-supervisory",
  "qualification_reference": "SYN-combined-qualified-disjoint-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_combined_currency_exposure_2027

```python
solvency2.groups.group_combined_currency_exposure_2027(participation_value: float, entity_scr: float, share: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Positive holding excess for external consolidated currency scenarios.

Amounts use the same qualified currency. This is not a currency charge and
no equity shock applies to this holding under the cited combined-method rule.

Output unit: `context currency`. Sources: `DIR:article-233a:3`.

Fixed example: `future-group-combined-fx-50-0`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-combined-fx-50-0')
context = replace(base, **case.get('context', {}))
result = s2.group_combined_currency_exposure_2027(**case['kwargs'], context=context)
# Independent expected value: 50
```

Example input (JSON):

```json
{
  "participation_value": 50,
  "entity_scr": 60,
  "share": 0,
  "qualification_reference": "SYN-combined-qualified-disjoint-scope"
}
```

Reference-tested failure codes: `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_consolidated_minimum

```python
solvency2.groups.group_consolidated_minimum(parent_mcr: float, related: Mapping, *, qualification_reference: str, third_country: Optional[Mapping] = None, context: solvency2._core.core.Context)
```

Qualified MCR sum plus future local licence-withdrawal requirements.

Future third-country rows are explicit, including an empty mapping. They
must not duplicate the EU-MCR entity set; legal scope is assessed externally.

Output unit: `context currency`. Sources: `DIR:article-230:2`, `DIR:article-221`.

Fixed example: `future-group-minimum-parent`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-minimum-parent')
context = replace(base, **case.get('context', {}))
result = s2.group_consolidated_minimum(**case['kwargs'], context=context)
# Independent expected value: 30
```

Example input (JSON):

```json
{
  "parent_mcr": 30,
  "related": {},
  "third_country": {},
  "qualification_reference": "SYN-2027-QUALIFIED"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### group_consolidated_surplus

```python
solvency2.groups.group_consolidated_surplus(eligible_own_funds: float, calculated_scr: float, minimum: float, *, qualification_reference: str, sector_contributions: Optional[Mapping] = None, context: solvency2._core.core.Context)
```

External consolidated eligible EOF minus SCR after its qualified minimum.

This is not consolidation by adding individual SCRs. Input SCR must include
externally required add-ons; EOF qualification and minimum coverage remain
externally assessed. A negative surplus is deliberately retained.
Future Article228 sectors must be excluded from consolidated inputs and
added separately, after the minimum is applied to consolidated SCR only.

Output unit: `context currency`. Sources: `DIR:article-230:1-2`.

Fixed example: `group-consolidated-deficit`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-consolidated-deficit')
context = replace(base, **case.get('context', {}))
result = s2.group_consolidated_surplus(**case['kwargs'], context=context)
# Independent expected value: -20
```

Example input (JSON):

```json
{
  "eligible_own_funds": 30,
  "calculated_scr": 40,
  "minimum": 50,
  "qualification_reference": "SYN-qualified-insurer-group-method-and-adjustments"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### group_immaterial_participation_screen_2027

```python
solvency2.groups.group_immaterial_participation_screen_2027(consolidated_assets: float, book_values: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Strict numerical thresholds only, never supervisory permission.

All relevant holdings and consolidated assets are externally qualified.
Exact decimal comparisons avoid a rounding tolerance at either boundary.

Output unit: `indicator`. Sources: `DIR:article-229a:3`.

Fixed example: `future-group-immaterial-zero`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-immaterial-zero')
context = replace(base, **case.get('context', {}))
result = s2.group_immaterial_participation_screen_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "consolidated_assets": 100000,
  "book_values": {
    "a": 0
  },
  "qualification_reference": "SYN-complete-qualified-holdings"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_simplified_participation_scr_2027

```python
solvency2.groups.group_simplified_participation_scr_2027(participation_risk: float, *, entity_type: str, capital_requirement: float | None = None, approval_reference: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Externally approved simplified contribution; no extra ownership weighting.

Article228 entities are outside scope. Third-country capital information
must be supplied, never replaced with zero when unavailable.

Output unit: `context currency`. Sources: `DR:article-336b:1-3`, `DIR:article-229a:1-2`.

Fixed example: `future-group-simplified-other`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-simplified-other')
context = replace(base, **case.get('context', {}))
result = s2.group_simplified_participation_scr_2027(**case['kwargs'], context=context)
# Independent expected value: 12
```

Example input (JSON):

```json
{
  "entity_type": "other",
  "participation_risk": 12,
  "capital_requirement": null,
  "approval_reference": "SYN-approval-unverified",
  "qualification_reference": "SYN-scope-excludes-Article228"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### group_method2_component_surplus

```python
solvency2.groups.group_method2_component_surplus(parent_own_funds: float, parent_scr: float, related: Mapping, own_funds_adjustment: float, capital_addon: float, *, qualification_reference: str, sector_contributions: Optional[Mapping] = None, context: solvency2._core.core.Context)
```

Signed method2 aggregation component, not complete approved group solvency.

Participation values already represent the held direct/indirect investment:
never apply share twice. External EOF adjustments must not duplicate those
values or the full-subsidiary-deficit correction calculated here. Group
availability, tiers, intra-group transactions and scope are not inferred.
Future Article228 sectors are explicit, already weighted and disjoint;
their holding values are deducted once, not passed through insurer deficits.

Output unit: `context currency`. Sources: `DIR:article-233:1-4`, `DIR:article-221:1`, `DIR:article-233:6`.

Fixed example: `group-method2-negative`. 13 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-method2-negative')
context = replace(base, **case.get('context', {}))
result = s2.group_method2_component_surplus(**case['kwargs'], context=context)
# Independent expected value: -20
```

Example input (JSON):

```json
{
  "parent_own_funds": 80,
  "parent_scr": 100,
  "related": {},
  "own_funds_adjustment": 0,
  "capital_addon": 0,
  "qualification_reference": "SYN-qualified-insurer-group-method-and-adjustments"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### group_required_shortfall

```python
solvency2.groups.group_required_shortfall(eligible_own_funds: float, scr: float, share: float, is_subsidiary: bool | None, proportionate_deficit_approved: bool | None, approval_reference: str | None = None, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Full subsidiary deficit unless an explicit externally approved exception applies.

Output unit: `context currency`. Sources: `DIR:article-221:1-2`.

Fixed example: `future-group-shortfall-full`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-shortfall-full')
context = replace(base, **case.get('context', {}))
result = s2.group_required_shortfall(**case['kwargs'], context=context)
# Independent expected value: 20
```

Example input (JSON):

```json
{
  "eligible_own_funds": 40,
  "scr": 60,
  "share": 0.5,
  "is_subsidiary": true,
  "proportionate_deficit_approved": false,
  "approval_reference": null,
  "qualification_reference": "SYN-qualified-insurer-group-method-and-adjustments"
}
```

### group_method2_best_estimate_sum

```python
solvency2.groups.group_method2_best_estimate_sum(parent_best_estimate: float, related: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Parent plus proportionate related BE, preserving signed external valuations.

Calculate before/after removal of intra-group transactions separately; this
component does not invent an EOF-adjustment sign or revalue transactions.

Output unit: `context currency`. Sources: `DR:article-342:2`.

Fixed example: `future-group-be-empty`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-be-empty')
context = replace(base, **case.get('context', {}))
result = s2.group_method2_best_estimate_sum(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "parent_best_estimate": 100,
  "related": {},
  "qualification_reference": "SYN-externally-valued-group-BE"
}
```

### group_standard_scr_contribution

```python
solvency2.groups.group_standard_scr_contribution(entity: str, share: float, diversified_component: float, component_scrs: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Standard-formula contribution for externally qualified consolidated entities.

Numerator uses the entity's proportional SCR; denominator is the sum of the
supplied SCRs, without applying shares a second time. No internal-model
allocation is inferred. Scaling preserves the formula at large magnitudes.

Output unit: `context currency`. Sources: `DR:article-330:6:a`, `DR:article-335:1:a`, `DR:article-335:1:c`.

Fixed example: `future-group-contribution-full`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-contribution-full')
context = replace(base, **case.get('context', {}))
result = s2.group_standard_scr_contribution(**case['kwargs'], context=context)
# Independent expected value: 48
```

Example input (JSON):

```json
{
  "entity": "a",
  "share": 1,
  "diversified_component": 80,
  "component_scrs": {
    "a": 60,
    "b": 40
  },
  "qualification_reference": "SYN-Art335-1-a-c-standard-formula-component"
}
```

### group_consolidated_best_estimate

```python
solvency2.groups.group_consolidated_best_estimate(parent_best_estimate: float, related: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Sum BE already adjusted externally for all intra-group transactions.

Method1 Article335(1)a/c scope and consolidation shares are external. The
receiving reinsurer excludes intra-group fulfilment cashflows; the cedant
excludes corresponding recoverables. This function does not perform netting.

Output unit: `context currency`. Sources: `DR:article-339:1-3`, `DIR:article-221:1:a`.

Fixed example: `future-group-consolidated-be-positive`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-consolidated-be-positive')
context = replace(base, **case.get('context', {}))
result = s2.group_consolidated_best_estimate(**case['kwargs'], context=context)
# Independent expected value: 120
```

Example input (JSON):

```json
{
  "parent_best_estimate": 100,
  "related": {
    "a": {
      "best_estimate": 40,
      "share": 0.5
    }
  },
  "qualification_reference": "SYN-externally-adjusted-335-1-a-c-data"
}
```

### group_consolidated_risk_margin

```python
solvency2.groups.group_consolidated_risk_margin(parent_risk_margin: float, related: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Proportionate sum of externally qualified risk margins, no added diversification.

Output unit: `context currency`. Sources: `DR:article-340`, `DIR:article-221:1:a`.

Fixed example: `future-group-consolidated-rm-empty`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-consolidated-rm-empty')
context = replace(base, **case.get('context', {}))
result = s2.group_consolidated_risk_margin(**case['kwargs'], context=context)
# Independent expected value: 10
```

Example input (JSON):

```json
{
  "parent_risk_margin": 10,
  "related": {},
  "qualification_reference": "SYN-externally-adjusted-335-1-a-c-data"
}
```

### group_consolidated_scr

```python
solvency2.groups.group_consolidated_scr(components: Mapping, capital_addon: float, *, qualification_reference: str, simplified_contributions: Optional[Mapping] = None, context: solvency2._core.core.Context)
```

Sum qualified Article336 amounts plus externally set group add-on.

Contributions b/c already include proportional shares. Components d/e are
externally determined risk amounts, not invented sums of individual SCRs.
From 2027, only a-d belong here; separate Article336b additions must be
explicit and disjoint from those components. Article228 sector contributions
are outside this consolidated amount. Their valuation is not inferred.
Apply the Article230 minimum separately. No sector/Look-through valuation
or supervisory determination is implemented by this composition function.

Output unit: `context currency`. Sources: `DR:article-336`, `DIR:article-232`.

Fixed example: `future-group-scr-four`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-group-scr-four')
context = replace(base, **case.get('context', {}))
result = s2.group_consolidated_scr(**case['kwargs'], context=context)
# Independent expected value: 28
```

Example input (JSON):

```json
{
  "components": {
    "diversified": 3,
    "related_insurers": 4,
    "other_participations": 6,
    "lookthrough_funds": 7
  },
  "capital_addon": 8,
  "simplified_contributions": {},
  "qualification_reference": "SYN-2027-QUALIFIED"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### group_reinsurance_elimination

```python
solvency2.groups.group_reinsurance_elimination(entities: Mapping, transactions: Mapping, *, parent_id: str, measure: str, other_intragroup_adjustments_complete: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Remove qualified internal reinsurance values before consolidation shares.

Entity gross BE and recoverables must include the supplied disjoint internal
transactions, but already exclude all OTHER required intragroup adjustments.
Assumed obligation PV and ceded recoverable need not agree: valuation bases
and shares can differ. Neither side is inferred from the other or floored.
This is a two-sided ledger adjustment, not a projection or legal approval.

Output unit: `context currency`. Sources: `DR:article-339:1-3`, `DIR:article-221:1:a`.

Fixed example: `group-reinsurance-baseline-recoverables`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'group-reinsurance-baseline-recoverables')
context = replace(base, **case.get('context', {}))
result = s2.group_reinsurance_elimination(**case['kwargs'], context=context)
# Independent expected value: 26
```

Example input (JSON):

```json
{
  "entities": {
    "parent": {
      "best_estimate": 1000,
      "recoverables": 100,
      "share": 1
    },
    "child": {
      "best_estimate": 150,
      "recoverables": 20,
      "share": 0.8
    }
  },
  "transactions": {
    "contract1": {
      "cedant": "parent",
      "reinsurer": "child",
      "assumed_best_estimate": 100,
      "recoverable": 90,
      "valuation_reference": "SYN-values"
    }
  },
  "parent_id": "parent",
  "other_intragroup_adjustments_complete": true,
  "qualification_reference": "SYN-disjoint-scope",
  "measure": "recoverables"
}
```

## solvency2.nonlife

### catastrophe_group_weighted_sum

```python
solvency2.nonlife.catastrophe_group_weighted_sum(peril: str, region: str, zone_ordinals: list[int], insured_sum: float, *, qualification_reference: str, exposure_basis_reference: str | None = None, context: solvency2._core.core.Context)
```

Q*max(group zone weights)*qualified group SI; never invent a group matrix.

The named region fixes the common regional scope. Source-blocked weights
remain blocked through the ordinary selector. A group amount cannot be
repeated into every original matrix zone: downstream group treatment must
be qualified separately. Future90b(6) requires120(1a) evidence for wind/soil.

Output unit: `context currency`. Sources: `DR:article-90b`, `DR:article-88`.

Fixed example: `simpl-close-baseline-group-single`. 13 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simpl-close-baseline-group-single')
context = replace(base, **case.get('context', {}))
result = s2.catastrophe_group_weighted_sum(**case['kwargs'], context=context)
# Independent expected value: 0.056
```

Example input (JSON):

```json
{
  "peril": "windstorm",
  "region": "DE",
  "zone_ordinals": [
    2
  ],
  "insured_sum": 100,
  "qualification_reference": "SYN-88-same-region-group"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### simplified_fire_risk

```python
solvency2.nonlife.simplified_fire_risk(exposures: Mapping, average_residential_sum: float, residential_market_shares: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Maximum of qualified top-five building-neighbourhood exposures and theta.

Each category explicitly supplies five ranked centre-neighbourhood sums;
nonexistent centres are qualified zero entries. Actual building geometry,
full/partial200m intersection, LoBs7/19, ranking by building-specific net
insured sum and recoveries not contingent on unrelated claims are external.
No point-distance proxy and no second deduction of reinsurance are used.

Output unit: `context currency`. Sources: `DR:article-90c`, `DR:article-88`.

Fixed example: `simpl-close-baseline-fire-no-residential`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'simpl-close-baseline-fire-no-residential')
context = replace(base, **case.get('context', {}))
result = s2.simplified_fire_risk(**case['kwargs'], context=context)
# Independent expected value: 3000
```

Example input (JSON):

```json
{
  "exposures": {
    "industrial": [
      3000,
      2000,
      1000,
      0,
      0
    ],
    "commercial": [
      100,
      0,
      0,
      0,
      0
    ],
    "residential": [
      0,
      0,
      0,
      0,
      0
    ]
  },
  "average_residential_sum": 0,
  "residential_market_shares": {},
  "qualification_reference": "SYN-88-top5-building-groups-net-ranking-200m"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### premium_reserve_geographic_region

```python
solvency2.nonlife.premium_reserve_geographic_region(territory: str, *, risk_location_reference: str, context: solvency2._core.core.Context)
```

Return the macroregion for an explicitly qualified original territory name.

No translations/current-name aliases or sovereign-to-overseas shortcuts are
inferred. For a parent country, its printed exclusions must already have
been excluded from the caller's risk-location input; they remain in audit.
This lookup neither identifies a NatCat zone nor calculates regional volumes.

Output unit: `region_ordinal`. Sources: `DR:annex-III:8`.

Fixed example: `macroregion-baseline-territory-054`. 584 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'macroregion-baseline-territory-054')
context = replace(base, **case.get('context', {}))
result = s2.premium_reserve_geographic_region(**case['kwargs'], context=context)
# Independent expected value: 5
```

Example input (JSON):

```json
{
  "territory": "Irak",
  "risk_location_reference": "SYN-qualified-risk-territory-not-citizenship-or-all-overseas"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### premium_future_component

```python
solvency2.nonlife.premium_future_component(contracts: Mapping, *, component: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Sum one selected net premium PV component, without long-term weighting.

Month coordinates encode externally qualified calendar boundaries. Premium
rows must be split at relevant earning cutoffs; payment time is not earning
time. Input PVs already include expectations, eligible netting and discounting.
The downstream premium-volume APIs apply the30% long-contract factor once.

Output unit: `context currency`. Sources: `DR:article-116:3:c:d`, `DR:article-147:3:c:d`.

Fixed example: `premium-future-baseline-empty-future_long_pv`. 96 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'premium-future-baseline-empty-future_long_pv')
context = replace(base, **case.get('context', {}))
result = s2.premium_future_component(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "contracts": {},
  "component": "future_long_pv",
  "qualification_reference": "SYN-qualified-earning-times-net-PV-complete-segment"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### premium_net_of_reinsurance

```python
solvency2.nonlife.premium_net_of_reinsurance(gross_premium: float, reinsurance_premiums: Mapping, *, qualification_reference: str, finite_reinsurance_ids: list[str] | tuple = (), context: solvency2._core.core.Context)
```

Return signed net premiums, not recoverables, total volume or capital.

All values refer to the same externally qualified earning/PV/currency basis.
Unknown qualifications cannot silently become either deductions or exclusions.
Excluded amounts are retained by row, not interpreted as zero contracts.
finite_reinsurance_ids declares finite AND economically similar transfers;
the default empty sequence explicitly qualifies all rows as non-finite.

Output unit: `context currency`. Sources: `DR:article-116:5`, `DR:article-147:5`, `DR:article-208:2`.

Fixed example: `premium-netting-baseline-empty`. 72 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'premium-netting-baseline-empty')
context = replace(base, **case.get('context', {}))
result = s2.premium_net_of_reinsurance(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "gross_premium": 100,
  "reinsurance_premiums": {},
  "qualification_reference": "SYN-matched-premium-basis-and-external-eligibility"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### natural_cat_other_diversification

```python
solvency2.nonlife.natural_cat_other_diversification(peril: str, regional_premiums: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Return sum of squared premium shares over all explicit regions5..18.

All amounts must use the externally qualified peril, gross-premium basis,
period, currency/unit and risk-location classification. These region IDs
are AnnexIII macroregions, not NatCat risk-zone IDs. No reserve amounts,
premium/reserve segment exceptions, USP override or implicit default enter
this CAT-only calculation. Zero total is undefined, not an assumed one.

Output unit: `ratio`. Sources: `DR:annex-III:1:8`.

Fixed example: `natural-cat-div-baseline-hail-all-equal`. 104 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'natural-cat-div-baseline-hail-all-equal')
context = replace(base, **case.get('context', {}))
result = s2.natural_cat_other_diversification(**case['kwargs'], context=context)
# Independent expected value: 0.07142857142857142
```

Example input (JSON):

```json
{
  "peril": "hail",
  "regional_premiums": {
    "5": 1,
    "6": 1,
    "7": 1,
    "8": 1,
    "9": 1,
    "10": 1,
    "11": 1,
    "12": 1,
    "13": 1,
    "14": 1,
    "15": 1,
    "16": 1,
    "17": 1,
    "18": 1
  },
  "qualification_reference": "SYN-qualified-premium-basis-period-contracts-and-AnnexIII-regions5to18"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### premium_reserve_parameterised_risk

```python
solvency2.nonlife.premium_reserve_parameterised_risk(risk_type: str, segments: Mapping, *, parameter_reference: str, context: solvency2._core.core.Context)
```

Aggregate supplied effective sigmas, without repeating NP/ADC adjustments.

Parameter admissibility, USP approval, HRES determination and sequencing
are external. Each row declares whether AnnexIII's USP-sigma restriction
applies; the engine enforces that numeric restriction, not its truth.
All12 nonlife or4 health-NSLT segments must be explicit, even when empty.
Existing standard-parameter APIs remain the default automatic selectors.

Output unit: `context currency`. Sources: `DR:article-115`, `DR:article-117:1-2`, `DR:article-146`, `DR:article-148:1-2`, `DR:annex-III:5-7`.

Fixed example: `parameterised-pr-baseline-health_nslt-usp`. 102 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'parameterised-pr-baseline-health_nslt-usp')
context = replace(base, **case.get('context', {}))
result = s2.premium_reserve_parameterised_risk(**case['kwargs'], context=context)
# Independent expected value: 18
```

Example input (JSON):

```json
{
  "risk_type": "health_nslt",
  "segments": {
    "1": {
      "premium_volume": 100,
      "reserve_volume": 0,
      "geographic_diversification": 1,
      "sigma_premium": 0.06,
      "sigma_reserve": 0,
      "uses_usp_sigma": true
    },
    "2": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1,
      "sigma_premium": 0,
      "sigma_reserve": 0,
      "uses_usp_sigma": false
    },
    "3": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1,
      "sigma_premium": 0,
      "sigma_reserve": 0,
      "uses_usp_sigma": false
    },
    "4": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1,
      "sigma_premium": 0,
      "sigma_reserve": 0,
      "uses_usp_sigma": false
    }
  },
  "parameter_reference": "SYN-qualified-effective-sigmas-volume-geography-and-approval-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### captive_nonlife_segment

```python
solvency2.nonlife.captive_nonlife_segment(premium_volume: float, reserve_volume: float, *, eligibility_reference: str, volume_reference: str, context: solvency2._core.core.Context)
```

Calculate a segment charge from already qualified Article116 volumes.

Normalising before squaring avoids overflow for representable charges;
neither reinsurance adjustments nor geographic diversification are repeated.

Output unit: `context currency`. Sources: `DR:article-90:2`, `DR:article-116:3`, `DR:article-116:6`.

Fixed example: `captive-baseline-zero`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'captive-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.captive_nonlife_segment(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "eligibility_reference": "SYN-88-89",
  "volume_reference": "SYN-116",
  "premium_volume": 0,
  "reserve_volume": 0
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### captive_nonlife_aggregation

```python
solvency2.nonlife.captive_nonlife_aggregation(segment_charges: Mapping[str, float], *, eligibility_reference: str, context: solvency2._core.core.Context)
```

Aggregate all twelve DR90 segment charges, with explicit inactive zeros.

Weights are separate profile parameters, not ordinary nonlife correlations.
A full set prevents omitted exposures from silently becoming zero.

Output unit: `context currency`. Sources: `DR:article-90:1`, `DR:annex-II`.

Fixed example: `captive-baseline-aggregate-zero`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'captive-baseline-aggregate-zero')
context = replace(base, **case.get('context', {}))
result = s2.captive_nonlife_aggregation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "segment_charges": {
    "1": 0,
    "2": 0,
    "3": 0,
    "4": 0,
    "5": 0,
    "6": 0,
    "7": 0,
    "8": 0,
    "9": 0,
    "10": 0,
    "11": 0,
    "12": 0
  },
  "eligibility_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### nonlife_adc_recovery_2027

```python
solvency2.nonlife.nonlife_adc_recovery_2027(segment: str, nominal_net_best_estimate: float, attachment_point: float, cover_size: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

One qualified ADC indemnity, before cession/prudence, using AnnexII sigma.

Contract group, distinct tranche and source-defined nominal net valuation
remain externally qualified. This is not discounted claims capital or an
automatic aggregation of several overlapping covers.

Output unit: `context currency`. Sources: `DR:article-117:4:conditions`, `DR:article-117:5`, `DR:annex-II`.

Fixed example: `nonlife-2027-adc-recovery-cover-cap`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'nonlife-2027-adc-recovery-cover-cap')
context = replace(base, **case.get('context', {}))
result = s2.nonlife_adc_recovery_2027(**case['kwargs'], context=context)
# Independent expected value: 20
```

Example input (JSON):

```json
{
  "segment": "1",
  "nominal_net_best_estimate": 100,
  "attachment_point": 100,
  "cover_size": 20,
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### nonlife_adc_reserve_factor_2027

```python
solvency2.nonlife.nonlife_adc_reserve_factor_2027(segment: str, nominal_net_best_estimate: float, recovery: float, cession_share: float, additional_premium: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Qualified reserve-sigma factor, no upper cap; zero denominator needs review.

Recovery is before cession; supplied additional premium is floored at zero
exactly once. No eligibility approval is inferred from the reference string.

Output unit: `ratio`. Sources: `DR:article-117:4`, `DR:annex-II`.

Fixed example: `nonlife-2027-adc-factor-no-upper-cap`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'nonlife-2027-adc-factor-no-upper-cap')
context = replace(base, **case.get('context', {}))
result = s2.nonlife_adc_reserve_factor_2027(**case['kwargs'], context=context)
# Independent expected value: 1.1
```

Example input (JSON):

```json
{
  "segment": "1",
  "nominal_net_best_estimate": 100,
  "recovery": 0,
  "cession_share": 1,
  "additional_premium": 2.7,
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### catastrophe_zone_aggregation

```python
solvency2.nonlife.catastrophe_zone_aggregation(peril: 'str', region: 'str', weighted_sums: 'Mapping[str, float]', *, context: 'Context')
```

sqrt(WSI' C WSI) for one Annex XXII–XXVI peril/region; WSI supplied externally.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-cat-zone-earthquake-GU-one`. 282 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-cat-zone-earthquake-GU-one')
context = replace(base, **case.get('context', {}))
result = s2.catastrophe_zone_aggregation(**case['kwargs'], context=context)
# Independent expected value: 7
```

Example input (JSON):

```json
{
  "peril": "earthquake",
  "region": "GU",
  "weighted_sums": {
    "1": 7
  }
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### catastrophe_region_aggregation

```python
solvency2.nonlife.catastrophe_region_aggregation(peril: 'str', region_charges: 'Mapping[str, float]', other_charge: 'float', *, context: 'Context')
```

Aggregate externally determined regional catastrophe charges plus other-region charge.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-cat-region-subsidence-zero`. 26 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-cat-region-subsidence-zero')
context = replace(base, **case.get('context', {}))
result = s2.catastrophe_region_aggregation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "peril": "subsidence",
  "region_charges": {
    "FR": 0,
    "BE": 0
  },
  "other_charge": 0
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### catastrophe_weighted_sum

```python
solvency2.nonlife.catastrophe_weighted_sum(peril: 'str', region: 'str', zone_ordinal: 'int', insured_sum: 'float', *, context: 'Context')
```

Q*W*SI for an externally qualified zone ordinal, not an address-to-zone mapping.

Future subsidence uses Annex VIIIA Q. Unqualified future geographic links
stay explicitly absent instead of inheriting historical labels.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-cat-weight-zero-si`. 145 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-cat-weight-zero-si')
context = replace(base, **case.get('context', {}))
result = s2.catastrophe_weighted_sum(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "peril": "windstorm",
  "region": "AT",
  "zone_ordinal": 1,
  "insured_sum": 0
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### catastrophe_zone_ordinal

```python
solvency2.nonlife.catastrophe_zone_ordinal(region: str, geographic_code: str, *, context: solvency2._core.core.Context)
```

Resolve an explicitly supplied published code to its zone ordinal.

Callers must first apply the region's documented postcode/province rule.
This function never guesses a prefix from a full address or repairs source
conflicts; the latter produce REVIEW_REQUIRED for the affected code only.

Output unit: `zone_ordinal`. Sources: `DR:annex-IX`.

Fixed example: `future-cat-geography-BE-1`. 70 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-cat-geography-BE-1')
context = replace(base, **case.get('context', {}))
result = s2.catastrophe_zone_ordinal(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "region": "BE",
  "geographic_code": "1"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### premium_reserve_risk

```python
solvency2.nonlife.premium_reserve_risk(segments: Mapping[str, dict], *, premium_nonproportional_cover: Optional[Mapping] = None, reserve_adjustments: Optional[Mapping] = None, adjustment_reference: str | None = None, uses_usp: bool | None = None, context: solvency2._core.core.Context)
```

Nonlife sigma aggregation with explicit2027 reinsurance/USP qualification.

Future premium80% factors require a declared existing nonproportional cover
in segments1/4/5. Reserve factors are supplied separately; no absence of ADC
is inferred from missing input. Historical callers keep the original API.

Output unit: `context currency`. Sources: `DR:article-115`, `DR:article-116:2`, `DR:article-117`, `DR:annex-II`, `DR:annex-IV`.

Fixed example: `nl-segment-one`. 31 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'nl-segment-one')
context = replace(base, **case.get('context', {}))
result = s2.premium_reserve_risk(**case['kwargs'], context=context)
# Independent expected value: 24
```

Example input (JSON):

```json
{
  "segments": {
    "1": {
      "premium_volume": 100,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "2": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "3": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "4": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "5": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "6": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "7": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "8": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "9": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "10": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "11": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "12": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    }
  }
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### nonlife_premium_volume

```python
solvency2.nonlife.nonlife_premium_volume(expected_next_year: float, earned_last_year: float, existing_future_pv: float, future_short_pv: float, future_long_pv: float, *, method: str, cap_evidence: Optional[Mapping[str, str]] = None, context: solvency2._core.core.Context)
```

Article 116 premium volume from externally selected net premium cashflows.

Future short contracts exclude premiums earned in their first twelve months
after recognition; future long contracts use premiums beyond the next twelve
months from valuation. The supplied long-contract PV is still unweighted.
Evidence references record, but cannot substantively verify, paragraph 4.

Output unit: `context currency`. Sources: `DR:article-116:3`, `DR:article-116:4`, `DR:article-116:5`.

Fixed example: `nl-premium-zero`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'nl-premium-zero')
context = replace(base, **case.get('context', {}))
result = s2.nonlife_premium_volume(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "expected_next_year": 0,
  "earned_last_year": 0,
  "existing_future_pv": 0,
  "future_short_pv": 0,
  "future_long_pv": 0,
  "method": "standard"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### nonlife_reserve_volume

```python
solvency2.nonlife.nonlife_reserve_volume(claims_best_estimate: float, eligible_recoverables: float, *, context: solvency2._core.core.Context)
```

Net claims BE; eligible recoverables must exclude208(2) finite/similar RI.

Output unit: `context currency`. Sources: `DR:article-116:6`.

Fixed example: `nl-reserve-zero`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'nl-reserve-zero')
context = replace(base, **case.get('context', {}))
result = s2.nonlife_reserve_volume(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "claims_best_estimate": 0,
  "eligible_recoverables": 0
}
```

### premium_reserve_diversification

```python
solvency2.nonlife.premium_reserve_diversification(*, risk_type: str, segment: str, method: str, uses_usp: bool, regional_volumes: Optional[Mapping[str, dict]] = None, context: solvency2._core.core.Context)
```

Geographic factor from already classified volumes, including mandatory exceptions.

Regional maxima/floors must be calculated regionally: their sum need not
equal the separately calculated segment volume used by the risk function.
This function does not classify countries or validate USP authorisation.

Output unit: `ratio`. Sources: `DR:annex-III:1-8`, `DR:article-116:7`, `DR:article-147:7`.

Fixed example: `geo-div-explicit-default`. 19 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'geo-div-explicit-default')
context = replace(base, **case.get('context', {}))
result = s2.premium_reserve_diversification(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "risk_type": "nonlife",
  "segment": "1",
  "method": "default",
  "uses_usp": false
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### nonlife_lapse_factor

```python
solvency2.nonlife.nonlife_lapse_factor(category: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Event share, not capital multiplier; underlying/worst selection external.

 Article90a permits contract-group selection for118(1)(a) only with88 and
35(a-c) grouping qualification. The external reference must evidence this
 if used; it does not change the event share or remove joint valuation.
 

Output unit: `ratio`. Sources: `DR:article-118:1-3`.

Fixed example: `nonlife-2027-lapse-termination`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'nonlife-2027-lapse-termination')
context = replace(base, **case.get('context', {}))
result = s2.nonlife_lapse_factor(**case['kwargs'], context=context)
# Independent expected value: 0.4
```

Example input (JSON):

```json
{
  "category": "termination",
  "qualification_reference": "SYN"
}
```

### nonprop_property_cat_loss

```python
solvency2.nonlife.nonprop_property_cat_loss(gross_premium: float, diversification: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Next12month eligible LOB28 earned gross premiums; AnnexIII DIV supplied.

Exclude nonproportional obligations relating to LOB9/21. DIV is based on
earned premiums, not the premium/reserve volume measure. Qualification and
DIV derivation remain external; the reference is not regulatory approval.

Output unit: `context currency`. Sources: `DR:article-127:2`.

Fixed example: `cat-premium-2027-property-zero`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'cat-premium-2027-property-zero')
context = replace(base, **case.get('context', {}))
result = s2.nonprop_property_cat_loss(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "gross_premium": 0,
  "diversification": 1,
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### other_nonlife_cat_loss

```python
solvency2.nonlife.other_nonlife_cat_loss(group_premiums: Mapping, *, classification_reference: str, context: solvency2._core.core.Context)
```

All five AnnexXII groups, next12month earned gross premiums.

Classify obligations and exclusions externally, including the conditional
extended-warranty exclusion in group3. Groups1/2 combine before squaring.

Output unit: `context currency`. Sources: `DR:article-135`, `DR:annex-XII`.

Fixed example: `cat-premium-2027-joint`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'cat-premium-2027-joint')
context = replace(base, **case.get('context', {}))
result = s2.other_nonlife_cat_loss(**case['kwargs'], context=context)
# Independent expected value: 13
```

Example input (JSON):

```json
{
  "group_premiums": {
    "1": 3,
    "2": 4,
    "3": 0,
    "4": 0,
    "5": 0
  },
  "classification_reference": "SYN"
}
```

### motor_assumed_limit

```python
solvency2.nonlife.motor_assumed_limit(amounts: Mapping, basis: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Externally choose total, absent-total property/personal, or per-victim basis.

Output unit: `EUR`. Sources: `DR:article-129:2`.

Fixed example: `motor-count-2027-total-limit`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'motor-count-2027-total-limit')
context = replace(base, **case.get('context', {}))
result = s2.motor_assumed_limit(**case['kwargs'], context=context)
# Independent expected value: 32400000
```

Example input (JSON):

```json
{
  "amounts": {
    "total": 32400000
  },
  "basis": "total",
  "qualification_reference": "SYN-qualified"
}
```

### motor_cat_loss

```python
solvency2.nonlife.motor_cat_loss(high_count: float, low_count: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Gross sudden claim, with literal floor even at zero supplied counts.

Counts are already proportionally weighted. Whether this submodule applies
to the undertaking is external; this API does not invent a zero-book waiver.

Output unit: `EUR`. Sources: `DR:article-129:1`.

Fixed example: `motor-floor`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'motor-floor')
context = replace(base, **case.get('context', {}))
result = s2.motor_cat_loss(**case['kwargs'], context=context)
# Independent expected value: 6000000
```

Example input (JSON):

```json
{
  "high_count": 0,
  "low_count": 0,
  "qualification_reference": "Synthetic Article129 scope"
}
```

### motor_vehicle_count

```python
solvency2.nonlife.motor_vehicle_count(vehicles: Mapping, category: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Aggregate qualified LOB4/16 vehicle groups, proportional shares applied once.

Vehicle counts are whole numbers before weighting; the resulting count can
be fractional. Each group must have a single assumed coverage limit/share.

Output unit: `count`. Sources: `DR:article-129:1:a-b`.

Fixed example: `motor-count-2027-empty`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'motor-count-2027-empty')
context = replace(base, **case.get('context', {}))
result = s2.motor_vehicle_count(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "vehicles": {},
  "category": "low",
  "qualification_reference": "SYN-qualified"
}
```

### catastrophe_effective_sum

```python
solvency2.nonlife.catastrophe_effective_sum(gross_sum: float, recoverable: float, use_gross: bool | None, peril: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Qualified recovery subtraction or explicit gross fallback for inadequate risk capture.

Recoveries conditional on unrelated claims must have been excluded externally.
For vessel components apply separately; for other perils use the qualified
combined object/group sum. The returned amount is not a BOF loss or SCR.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `concentration-2027-fire-gross`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'concentration-2027-fire-gross')
context = replace(base, **case.get('context', {}))
result = s2.catastrophe_effective_sum(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "gross_sum": 100,
  "recoverable": 30,
  "use_gross": true,
  "peril": "fire",
  "qualification_reference": "SYN"
}
```

### manmade_concentration_loss

```python
solvency2.nonlife.manmade_concentration_loss(exposures: Mapping, peril: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Maximum combined effective insured sum of externally qualified objects.

Fire inputs are complete, externally qualified building groups, not isolated
points. Components are after qualified recovery/fallback; never deduct twice.
Empty eligible populations return explicitly documented conventional zero.
This is not the hypothetical Article196(a) capital calculation; its2027
object-selection requirements need separate qualification.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `concentration-2027-empty`. 13 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'concentration-2027-empty')
context = replace(base, **case.get('context', {}))
result = s2.manmade_concentration_loss(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposures": {},
  "peril": "vessel",
  "qualification_reference": "SYN"
}
```

### liability_cat_claim_count

```python
solvency2.nonlife.liability_cat_claim_count(loss: float, unlimited: bool | None, largest_limit: float | None = None, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Smallest integer STRICTLY above the ratio, or one for unlimited coverage.

Fraction arithmetic on decimal representations preserves exact boundaries
such as 115/(1.15*100)=1; ceil would be wrong there. Representative loss
allocation across those claims and reinsurance response remain external.

Output unit: `count`. Sources: `DR:article-133:3:a-c`.

Fixed example: `liability-credit-2027-unlimited`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'liability-credit-2027-unlimited')
context = replace(base, **case.get('context', {}))
result = s2.liability_cat_claim_count(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "loss": 1000,
  "unlimited": true,
  "qualification_reference": "SYN"
}
```

### liability_cat_loss

```python
solvency2.nonlife.liability_cat_loss(group: str, gross_premium: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Group factor times next12month earned gross premium before reinsurance.

AnnexXI classifications and exclusions are external, including the group4
exclusions for groups1–3, private households and specified craftsmen.

Output unit: `context currency`. Sources: `DR:article-133:2`, `DR:annex-XI`.

Fixed example: `liability-credit-2027-liability-group1`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'liability-credit-2027-liability-group1')
context = replace(base, **case.get('context', {}))
result = s2.liability_cat_loss(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "group": "1",
  "gross_premium": 100,
  "qualification_reference": "SYN"
}
```

### credit_cat_default_loss

```python
solvency2.nonlife.credit_cat_default_loss(exposures: Mapping, *, qualification_reference: str, selected_exposure_ids: Optional[Sequence[str]] = None, context: solvency2._core.core.Context)
```

Select largest NET default exposures and report their gross scenario claims.

Each recovery is externally valued against this exposure's default claim,
not against its full insured sum. Ambiguous cutoff ties with differing gross
amounts require explicit selection, still constrained to largest net losses.

Output unit: `context currency`. Sources: `DR:article-134:2-3`.

Fixed example: `credit-cat-empty`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'credit-cat-empty')
context = replace(base, **case.get('context', {}))
result = s2.credit_cat_default_loss(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "exposures": {},
  "qualification_reference": "Synthetic LOB9/21 and event recoveries"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### credit_cat_recession_loss

```python
solvency2.nonlife.credit_cat_recession_loss(gross_premium: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Sudden gross claim from next12month earned LOB9/21 premiums, not capital.

Output unit: `context currency`. Sources: `DR:article-134:4`.

Fixed example: `liability-credit-2027-credit-recession`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'liability-credit-2027-credit-recession')
context = replace(base, **case.get('context', {}))
result = s2.credit_cat_recession_loss(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "gross_premium": 100,
  "qualification_reference": "SYN"
}
```

### natural_cat_event_loss

```python
solvency2.nonlife.natural_cat_event_loss(prescribed_loss: float, peril: str, scenario: str, event: int, *, qualification_reference: str, context: solvency2._core.core.Context)
```

One ordered gross event; do not replace sequential recoveries with a sum.

Article126 independence, no new mitigation between events, and realistic
existing reinstatements must be reflected in external sequence valuation.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-natural-event-hail-0`. 25 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-natural-event-hail-0')
context = replace(base, **case.get('context', {}))
result = s2.natural_cat_event_loss(**case['kwargs'], context=context)
# Independent expected value: 70
```

Example input (JSON):

```json
{
  "peril": "hail",
  "prescribed_loss": 100,
  "scenario": "A",
  "event": 1,
  "qualification_reference": "SYN-external-contract-geography-valuation"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### natural_cat_insured_sum

```python
solvency2.nonlife.natural_cat_insured_sum(peril: str, components: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Sum eligible zone exposures; flood/hail motor weights differ.

Classify LOB7/19 property, LOB6/18 onshore property and LOB5/17 motor
externally. Subsidence covers eligible residential property; its region
scope is France historically, Annex VIIIA regions in the 2027 profile.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-natural-si-subsidence`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-natural-si-subsidence')
context = replace(base, **case.get('context', {}))
result = s2.natural_cat_insured_sum(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "peril": "subsidence",
  "components": {
    "residential_property": 100
  },
  "qualification_reference": "SYN-external-contract-geography-valuation"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### natural_cat_other_loss

```python
solvency2.nonlife.natural_cat_other_loss(peril: str, gross_premium: float, diversification: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Outside AnnexXIII: eligible next12month gross premiums and external DIV.

DIV uses the prescribed premium basis for AnnexIII regions5–18, not generic
premium/reserve volumes. Geographic membership is not inferred here.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-natural-other-hail`. 17 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-natural-other-hail')
context = replace(base, **case.get('context', {}))
result = s2.natural_cat_other_loss(**case['kwargs'], context=context)
# Independent expected value: 22.5
```

Example input (JSON):

```json
{
  "peril": "hail",
  "gross_premium": 100,
  "diversification": 0.5,
  "qualification_reference": "SYN-external-contract-geography-valuation"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### natural_cat_scenario_risk

```python
solvency2.nonlife.natural_cat_scenario_risk(peril: str, scenario_charges: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Maximum of externally valued A/B sequence capital, not sum of event losses.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-natural-selection-hail`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-natural-selection-hail')
context = replace(base, **case.get('context', {}))
result = s2.natural_cat_scenario_risk(**case['kwargs'], context=context)
# Independent expected value: 4
```

Example input (JSON):

```json
{
  "peril": "hail",
  "scenario_charges": {
    "A": 3,
    "B": 4
  },
  "qualification_reference": "SYN-external-contract-geography-valuation"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### natural_cat_weighted_cap

```python
solvency2.nonlife.natural_cat_weighted_cap(weighted_sum: float, peril: str, use_alternative: bool | None, potential_gross_loss: float | None = None, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Optional externally justified lower WSI, never a reinsurance-net amount.

Output unit: `context currency`. Sources: selected by the explicit method/parameter inputs; inspect `result.sources`.

Fixed example: `future-natural-primary-hail`. 31 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-natural-primary-hail')
context = replace(base, **case.get('context', {}))
result = s2.natural_cat_weighted_cap(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "peril": "hail",
  "weighted_sum": 100,
  "use_alternative": false,
  "qualification_reference": "SYN-external-contract-geography-valuation"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

## solvency2.mcr

### de_branch_minimum_amount

```python
solvency2.mcr.de_branch_minimum_amount(unadjusted_absolute_floor: float, requirement: str, *, reinsurance_branch: bool, domestic_deposit_relief: bool, relief_reference: str | None = None, source_version: str, applicability_reference: str, context: solvency2._core.core.Context)
```

Calculate a qualified German branch asset minimum or domestic deposit.

The input is the unhalved applicable AMCR, not the branch MCR. A German
deposit waiver does not waive the deposit at the chosen supervisory state.
Asset location, admissibility and any higher actual SCR/MCR stay separate.

Output unit: `EUR`. Sources: `DE_VAG:2026-03-25:69:2;69:5;70:1`.

Fixed example: `de-close-baseline-reinsurer`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'de-close-baseline-reinsurer')
context = replace(base, **case.get('context', {}))
result = s2.de_branch_minimum_amount(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "unadjusted_absolute_floor": 4000000,
  "requirement": "deposit",
  "reinsurance_branch": true,
  "domestic_deposit_relief": false,
  "source_version": "2026-03-25",
  "applicability_reference": "SYN-DE-VAG-69"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### mcr_absolute_floor

```python
solvency2.mcr.mcr_absolute_floor(undertaking_type: str, covers_nonlife_classes_10_to_15: bool | None = None, *, context: solvency2._core.core.Context, third_country_branch: bool = False, qualification_reference: str | None = None, mixed_premiums: Optional[Mapping] = None)
```

Select a printed EUR floor, including qualified Article166 direct branches.

The half-floor is not a half-SCR or half-MCR multiplier. Pass it as the
absolute floor into the ordinary branch-activity MCR calculation. Deposit,
asset location, authorisation and Article167 relief remain separate.

Output unit: `EUR`. Sources: `DIR:article-129:1:d`.

Fixed example: `mcr-2027-amcr-life`. 47 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-2027-amcr-life')
context = replace(base, **case.get('context', {}))
result = s2.mcr_absolute_floor(**case['kwargs'], context=context)
# Independent expected value: 4000000
```

Example input (JSON):

```json
{
  "undertaking_type": "life"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### mcr_combined

```python
solvency2.mcr.mcr_combined(linear: float, scr: float, absolute_floor: float, *, context: solvency2._core.core.Context)
```

Combined MCR including an explicitly supplied applicable absolute floor.

Output unit: `context currency`. Sources: `DR:article-248`.

Fixed example: `mcr-2027-combined-floor`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-2027-combined-floor')
context = replace(base, **case.get('context', {}))
result = s2.mcr_combined(**case['kwargs'], context=context)
# Independent expected value: 25
```

Example input (JSON):

```json
{
  "linear": 10,
  "scr": 100,
  "absolute_floor": 1
}
```

### mcr_life

```python
solvency2.mcr.mcr_life(components: Mapping[str, float], *, context: solvency2._core.core.Context)
```

Linear life MCR; no premature floor on the signed linear total.

Output unit: `context currency`. Sources: `DR:article-251:1`.

Fixed example: `mcr-2027-life-guaranteed`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-2027-life-guaranteed')
context = replace(base, **case.get('context', {}))
result = s2.mcr_life(**case['kwargs'], context=context)
# Independent expected value: 3.7
```

Example input (JSON):

```json
{
  "components": {
    "guaranteed": 100,
    "discretionary": 0,
    "unit_linked": 0,
    "other": 0,
    "capital_at_risk": 0
  }
}
```

### mcr_nonlife

```python
solvency2.mcr.mcr_nonlife(segments: Mapping[str, dict], *, context: solvency2._core.core.Context)
```

Linear nonlife/health MCR using all 16 annex-XIX segments, including explicit zeros.

Output unit: `context currency`. Sources: `DR:article-250:1`, `DR:annex-XIX`.

Fixed example: `mcr-2027-tp-1`. 33 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-2027-tp-1')
context = replace(base, **case.get('context', {}))
result = s2.mcr_nonlife(**case['kwargs'], context=context)
# Independent expected value: 5.4
```

Example input (JSON):

```json
{
  "segments": {
    "1": {
      "technical_provisions": 100,
      "written_premiums": 0
    },
    "2": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "3": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "4": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "5": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "6": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "7": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "8": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "9": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "10": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "11": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "12": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "13": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "14": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "15": {
      "technical_provisions": 0,
      "written_premiums": 0
    },
    "16": {
      "technical_provisions": 0,
      "written_premiums": 0
    }
  }
}
```

### mcr_capital_at_risk

```python
solvency2.mcr.mcr_capital_at_risk(contracts: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Article251 contract-level floors; external benefit/BE qualification unchanged.

Output unit: `context currency`. Sources: `DR:article-251:1:e`.

Fixed example: `mcr-car-baseline-empty`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-car-baseline-empty')
context = replace(base, **case.get('context', {}))
result = s2.mcr_capital_at_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "contracts": {},
  "qualification_reference": "SYN-externally-qualified-net-benefits"
}
```

### mcr_linear

```python
solvency2.mcr.mcr_linear(nonlife: float, life: float, *, context: solvency2._core.core.Context)
```

Add the separately determined Art.250/251 parts; life may be signed.

Output unit: `context currency`. Sources: `DR:article-249`.

Fixed example: `mcr-linear-zero`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-linear-zero')
context = replace(base, **case.get('context', {}))
result = s2.mcr_linear(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "nonlife": 0,
  "life": 0
}
```

### mcr_notional_scr

```python
solvency2.mcr.mcr_notional_scr(nonlife_linear: float, life_linear: float, scr_excluding_addon: float, activity: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Allocate SCR excluding add-ons by the two notional linear MCR components.

Signed linear components are not silently floored. A zero denominator has
no specified allocation here and requires review. Supervisory add-ons are
allocated separately by the supervisor, not by this ratio.

Output unit: `context currency`. Sources: `DR:article-252:6:11`.

Fixed example: `mcr-2027-notional-life`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-2027-notional-life')
context = replace(base, **case.get('context', {}))
result = s2.mcr_notional_scr(**case['kwargs'], context=context)
# Independent expected value: 140
```

Example input (JSON):

```json
{
  "nonlife_linear": 30,
  "life_linear": 70,
  "scr_excluding_addon": 200,
  "activity": "life",
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### mcr_notional_requirement

```python
solvency2.mcr.mcr_notional_requirement(linear: float, notional_scr: float, capital_addon: float, absolute_floor: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Notional activity MCR with a separately supervisor-assigned add-on.

Preserve the printed min(max(...),...) ordering even for signed inputs.
The applicable absolute floor and activity delimitation remain external.
This is not a total-company MCR or an automatic Article253 decision.

Output unit: `context currency`. Sources: `DR:article-252:2:3:7:8`.

Fixed example: `mcr-notional-low`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'mcr-notional-low')
context = replace(base, **case.get('context', {}))
result = s2.mcr_notional_requirement(**case['kwargs'], context=context)
# Independent expected value: 20
```

Example input (JSON):

```json
{
  "linear": 5,
  "notional_scr": 60,
  "capital_addon": 20,
  "absolute_floor": 3,
  "qualification_reference": "SYN"
}
```

## solvency2.valuation

### de_cover_assets_minimum

```python
solvency2.valuation.de_cover_assets_minimum(components: Mapping, *, source_version: str, applicability_reference: str, current_cover_assets: float | None = None, foreign_security_exception: float = 0, foreign_security_reference: str | None = None, context: solvency2._core.core.Context)
```

German book-value cover pool minimum, distinct from Solvency-II TP.

Gross direct-insurance figures precede reinsurance deductions. Eligible
current pool value must already reflect the separate Article126 rules.
Extra supervisory requirements under127(2) are not inferred here.

Output unit: `EUR`. Sources: `DE_VAG:2026-03-25:125:2;126:2;127:1`.

Fixed example: `cover-close-baseline-minimum`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'cover-close-baseline-minimum')
context = replace(base, **case.get('context', {}))
result = s2.de_cover_assets_minimum(**case['kwargs'], context=context)
# Independent expected value: 36
```

Example input (JSON):

```json
{
  "components": {
    "unearned_premiums": 1,
    "mathematical_provision": 2,
    "outstanding_claims_and_repurchases": 3,
    "non_profit_related_refunds": 4,
    "dormant_unused_premiums": 5,
    "allocated_undistributed_profit_shares": 6,
    "direct_policyholder_liabilities": 7,
    "refundable_received_premiums": 8
  },
  "source_version": "2026-03-25",
  "applicability_reference": "SYN-125-gross-direct-qualified"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### de_cover_property_value

```python
solvency2.valuation.de_cover_property_value(book_value: float, market_value: float, *, encumbered: bool, supervisory_value: float | None = None, supervisory_reference: str | None = None, expert_valuation_reference: str | None = None, source_version: str, applicability_reference: str, context: solvency2._core.core.Context)
```

Book/market minimum, or explicitly supervisor-determined property value.

A doubled market-to-book threshold permits review of an increase; it does
not prescribe the increase. Encumbered property always needs an external
supervisory value. Neither value may feed a Solvency-II market valuation
merely because this separate cover-pool rule accepts it.

Output unit: `EUR`. Sources: `DE_VAG:2026-03-25:125:3`.

Fixed example: `cover-close-baseline-property-low`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'cover-close-baseline-property-low')
context = replace(base, **case.get('context', {}))
result = s2.de_cover_property_value(**case['kwargs'], context=context)
# Independent expected value: 80
```

Example input (JSON):

```json
{
  "book_value": 100,
  "market_value": 80,
  "encumbered": false,
  "source_version": "2026-03-25",
  "applicability_reference": "SYN-125-property-qualified"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### valuation_accounts_method_conditions

```python
solvency2.valuation.valuation_accounts_method_conditions(conditions: Mapping[str, bool], *, in_ifrs_consolidation_group: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Check declared Article9(4) facts; never establish method compatibility.

The IFRS-group exclusion is distinct from the four Article9 conditions.
Article13/16 restrictions and substantive comparison evidence remain separate.

Output unit: `indicator`. Sources: `DR:article-9:4`, `VALUATION_GUIDANCE:guideline-12:1.33`.

Fixed example: `valuation-accounts-baseline-group`. 26 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-accounts-baseline-group')
context = replace(base, **case.get('context', {}))
result = s2.valuation_accounts_method_conditions(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "conditions": {
    "article75_compatible": true,
    "risk_proportionate": true,
    "not_ifrs_in_accounts": true,
    "ifrs_cost_disproportionate": true
  },
  "in_ifrs_consolidation_group": true,
  "qualification_reference": "SYN-DR9-4-qualified"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### valuation_method_checked_value

```python
solvency2.valuation.valuation_method_checked_value(qualified_value: float, *, position_type: str, method: str, qualification_reference: str, conditions: collections.abc.Mapping[str, bool] | None = None, deposit_terms: collections.abc.Mapping | None = None, hierarchy: collections.abc.Mapping | None = None, own_credit: collections.abc.Mapping | None = None, context: solvency2._core.core.Context)
```

Forward a value only on an explicitly supported Article16 method path.

The closed method vocabulary describes this component's supported scope; a
rejected unimplemented technique is not thereby declared unlawful. Required
cost flags mean material costs were assessed and adjusted where necessary.
The future deposit exception delegates its profile, threshold and override
checks to the existing component. No zero/default substitutes for missing data.

Output unit: `context currency`. Sources: `DR:article-16:1-7`.

Fixed example: `valuation-method-baseline-16-3-pass`. 72 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-method-baseline-16-3-pass')
context = replace(base, **case.get('context', {}))
result = s2.valuation_method_checked_value(**case['kwargs'], context=context)
# Independent expected value: 80
```

Example input (JSON):

```json
{
  "qualified_value": 80,
  "position_type": "property",
  "method": "replacement_cost",
  "conditions": {},
  "qualification_reference": "SYN-qualified-method"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### valuation_balance_sheet_excess

```python
solvency2.valuation.valuation_balance_sheet_excess(assets: Mapping[str, float], liabilities: Mapping[str, float], *, complete_scope: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Sum externally qualified positions, retaining negative values and surplus.

Own shares remain assets and subordinated debt remains a liability here;
the separate Article88 component subsequently adjusts those exactly once.
A declared complete input scope does not certify a complete insurer balance.

Output unit: `context currency`. Sources: `DIR:article-75`, `DIR:article-88:1`, `DR:article-9:5-6`.

Fixed example: `valuation-balance-baseline-zero`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-balance-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.valuation_balance_sheet_excess(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "assets": {},
  "liabilities": {},
  "complete_scope": true,
  "qualification_reference": "SYN-qualified-chosen-balance-sheet"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### valuation_liability_excluding_own_credit

```python
solvency2.valuation.valuation_liability_excluding_own_credit(current_value: float, own_credit_change: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Remove externally isolated cumulative own-credit value change since initial recognition.

The input is a monetary valuation effect, not a spread or a period-only
delta. Initial-recognition credit is retained; do not also apply this
correction to a bottom-up value already holding initial credit constant.

Output unit: `context currency`. Sources: `DR:article-14:1`.

Fixed example: `valuation-own-credit-baseline-signed`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-own-credit-baseline-signed')
context = replace(base, **case.get('context', {}))
result = s2.valuation_liability_excluding_own_credit(**case['kwargs'], context=context)
# Independent expected value: -5
```

Example input (JSON):

```json
{
  "current_value": 5,
  "own_credit_change": 10,
  "qualification_reference": "SYN-cumulative-own-credit-value-effect-since-initial"
}
```

### valuation_deferred_tax_net

```python
solvency2.valuation.valuation_deferred_tax_net(deferred_tax_assets: float, deferred_tax_liabilities: float, *, legally_enforceable_offset: bool, same_tax_authority: bool, same_taxable_entity: bool, undiscounted: bool, qualification_reference: str, context: solvency2._core.core.Context, excluded_participations: Optional[Mapping] = None, valuation_level: str | None = None, recognition_conditions: Optional[Mapping] = None, recognition_documents: Optional[Mapping] = None)
```

Net externally recognised, undiscounted tax balances only when qualified.

Positive results are net assets; negative results are net liabilities.
No tax rates, taxable-profit projections, expiry or LAC-DT are calculated.

Output unit: `context currency`. Sources: `DR:article-15`, `VALUATION_GUIDANCE:guideline-9:1.26-1.27`.

Fixed example: `valuation-tax-net-baseline-zero`. 30 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-tax-net-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.valuation_deferred_tax_net(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "deferred_tax_assets": 0,
  "deferred_tax_liabilities": 0,
  "legally_enforceable_offset": true,
  "same_tax_authority": true,
  "same_taxable_entity": true,
  "undiscounted": true,
  "qualification_reference": "SYN-recognised-undiscounted-tax-and-offset"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### valuation_short_term_deposit_cost_2027

```python
solvency2.valuation.valuation_short_term_deposit_cost_2027(cost_value: float, term_years: float, *, small_non_complex: bool, no_material_valuation_error: bool, alternative_value: float | None = None, method: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply the 2027 deposit exception, without computing cost or amortisation.

Deposit classification, term basis, SNC status and materiality are external.
Both comparisons are strict; failure does not invent a fair-value fallback.

Output unit: `context currency`. Sources: `DR:article-16:1`.

Fixed example: `valuation-deposit-future-cost`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-deposit-future-cost')
context = replace(base, **case.get('context', {}))
result = s2.valuation_short_term_deposit_cost_2027(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "cost_value": 100,
  "term_years": 0.5,
  "small_non_complex": true,
  "no_material_valuation_error": true,
  "method": "cost",
  "qualification_reference": "SYN-short-term-deposit-SNC-and-materiality"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### valuation_participation_value

```python
solvency2.valuation.valuation_participation_value(*, excluded_from_group_supervision: bool, deducted_from_group_own_funds: bool, qualified_value: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply two externally qualified exclusions, not a group-scope decision.

Flags refer specifically to Directive214(2) and229. Otherwise the external
Article13 value passes through without a floor or a second ownership share.

Output unit: `context currency`. Sources: `DR:article-13:2`, `DIR:article-214:2`, `DIR:article-229`.

Fixed example: `valuation-extra-baseline-retained`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-extra-baseline-retained')
context = replace(base, **case.get('context', {}))
result = s2.valuation_participation_value(**case['kwargs'], context=context)
# Independent expected value: 85
```

Example input (JSON):

```json
{
  "excluded_from_group_supervision": false,
  "deducted_from_group_own_funds": false,
  "qualified_value": 85,
  "qualification_reference": "SYN-DIR214-229-and-DR13"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### valuation_contingent_liability

```python
solvency2.valuation.valuation_contingent_liability(cashflows: Mapping[str, dict], *, recognised_under_article11: bool, runoff_complete: bool, curve_basis: str, qualification_reference: str, curve_reference: str, context: solvency2._core.core.Context)
```

Discount externally expected settlement payments on a basic risk-free curve.

Recognition/materiality, complete runoff, probability weighting and curve
construction are external. In particular VA/MA curves are not accepted.

Output unit: `context currency`. Sources: `DR:article-11`, `DR:article-14:2`.

Fixed example: `valuation-extra-baseline-zero`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-extra-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.valuation_contingent_liability(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "cashflows": {
    "2025-01-17": {
      "expected_payment": 0,
      "discount_factor": 1
    }
  },
  "recognised_under_article11": true,
  "runoff_complete": true,
  "curve_basis": "basic_risk_free",
  "qualification_reference": "SYN-recognised-complete-expected-payments",
  "curve_reference": "SYN-basic-risk-free"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### valuation_intangible_value

```python
solvency2.valuation.valuation_intangible_value(asset_type: str, *, separately_saleable: bool | None = None, active_market_value_evidenced: bool | None = None, qualified_value: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply goodwill/other-intangible zero rules, not a fair-value model.

Positive recognition requires both external Article12 qualifications and a
separately supplied Article10 value. Unused values are rejected, not ignored.

Output unit: `context currency`. Sources: `DR:article-12:1-2`, `DR:article-10`.

Fixed example: `valuation-baseline-goodwill-zero`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-baseline-goodwill-zero')
context = replace(base, **case.get('context', {}))
result = s2.valuation_intangible_value(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "asset_type": "goodwill",
  "qualification_reference": "SYN-qualified-valuation-hierarchy-and-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### valuation_adjusted_equity_component

```python
solvency2.valuation.valuation_adjusted_equity_component(excess_assets_over_liabilities: float, share: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply the held share to externally qualified Article13 net assets.

No floor, method-ranking decision, Article13(2) exclusion determination or
asset/technical-provision valuation is inferred from this arithmetic.

Output unit: `context currency`. Sources: `DR:article-13:3-4`.

Fixed example: `valuation-baseline-equity-zero`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-baseline-equity-zero')
context = replace(base, **case.get('context', {}))
result = s2.valuation_adjusted_equity_component(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "excess_assets_over_liabilities": 100,
  "share": 0,
  "qualification_reference": "SYN-qualified-valuation-hierarchy-and-scope"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### valuation_accounting_equity_adjustment

```python
solvency2.valuation.valuation_accounting_equity_adjustment(participation_value: float, goodwill_amount: float, zero_valued_intangibles_amount: float, *, method: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Deduct already scope-aligned goodwill and Article12-zero intangibles.

Method eligibility, hierarchy and Article13(2) exclusions are external.
Inputs use the same held-participation basis; never apply ownership twice.

Output unit: `context currency`. Sources: `DR:article-13:5-6`, `DR:article-12`.

Fixed example: `valuation-baseline-accounting-negative-ias_equity_fallback`. 10 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'valuation-baseline-accounting-negative-ias_equity_fallback')
context = replace(base, **case.get('context', {}))
result = s2.valuation_accounting_equity_adjustment(**case['kwargs'], context=context)
# Independent expected value: -5
```

Example input (JSON):

```json
{
  "participation_value": 10,
  "goodwill_amount": 10,
  "zero_valued_intangibles_amount": 5,
  "method": "ias_equity_fallback",
  "qualification_reference": "SYN-qualified-valuation-hierarchy-and-scope"
}
```

Reference-tested failure codes: `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

## solvency2.health

### health_biometric_selection

```python
solvency2.health.health_biometric_selection(shock: str, valuations: Mapping, *, valuation_basis: str, grouping_mode: str, grouping_qualified: bool | None = None, valuation_reference: str, context: solvency2._core.core.Context)
```

Select already qualified SLT-health units; no health TP projection or SCR.

Under reinsurance, units represent underlying insurance, not treaty TP.
The result counts valuation units, never infers the number of contracts.

Output unit: `selection_units`. Sources: `DR:articles-152-153:2-3`.

Fixed example: `health-selection-baseline-mortality-qualified-aggregate`. 102 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-selection-baseline-mortality-qualified-aggregate')
context = replace(base, **case.get('context', {}))
result = s2.health_biometric_selection(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "shock": "mortality",
  "valuations": {
    "group": {
      "base_tp_excluding_risk_margin": 200,
      "stressed_tp_excluding_risk_margin": 195
    }
  },
  "valuation_basis": "direct_insurance_contracts",
  "grouping_mode": "article35",
  "grouping_qualified": true,
  "valuation_reference": "SYN-qualified-contract-TP-excluding-RM-and-shock"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### health_module_scope

```python
solvency2.health.health_module_scope(lob: str, module: str, *, classification_reference: str, context: solvency2._core.core.Context)
```

Look up a qualified LOB, not the contract's economic classification.

Both NSLT and SLT health obligations enter the health catastrophe scope.
This does not qualify any individual accident/pandemic scenario or amount.
Zero means outside this module's LOB scope, never zero insurer capital.

Output unit: `indicator`. Sources: `DR:article-113:c`, `DR:article-144:4`.

Fixed example: `health-scope-baseline-1-health`. 308 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-scope-baseline-1-health')
context = replace(base, **case.get('context', {}))
result = s2.health_module_scope(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "lob": "1",
  "module": "health",
  "classification_reference": "SYN-qualified-AnnexI-LOB"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### health_adc_recovery_2027

```python
solvency2.health.health_adc_recovery_2027(segment: str, nominal_net_best_estimate: float, attachment_point: float, cover_size: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Scenario indemnity for one externally qualified ADC, before cession/prudence.

Do not add multiple covers automatically or substitute the discounted
claims volume for the source-defined nominal net best estimate.

Output unit: `context currency`. Sources: `DR:article-148:4:conditions`, `DR:article-148:5`, `DR:annex-XIV`.

Fixed example: `health-nslt-2027-adc-recovery-uncapped`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-nslt-2027-adc-recovery-uncapped')
context = replace(base, **case.get('context', {}))
result = s2.health_adc_recovery_2027(**case['kwargs'], context=context)
# Independent expected value: 17.1
```

Example input (JSON):

```json
{
  "segment": "1",
  "nominal_net_best_estimate": 100,
  "attachment_point": 100,
  "cover_size": 20,
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### health_adc_reserve_factor_2027

```python
solvency2.health.health_adc_reserve_factor_2027(segment: str, nominal_net_best_estimate: float, recovery: float, cession_share: float, additional_premium: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Reserve-sigma adjustment; no invented upper cap or automatic eligibility.

Recovery is the paragraph5 indemnity before applying cession and prudence.
Additional premium is supplied before its prescribed zero floor. A zero
denominator needs review, not an implicit no-adjustment factor.

Output unit: `ratio`. Sources: `DR:article-148:4`, `DR:annex-XIV`.

Fixed example: `health-nslt-2027-adc-factor-zero-floor`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-nslt-2027-adc-factor-zero-floor')
context = replace(base, **case.get('context', {}))
result = s2.health_adc_reserve_factor_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "segment": "1",
  "nominal_net_best_estimate": 100,
  "recovery": 100,
  "cession_share": 1,
  "additional_premium": 0,
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### health_premium_volume

```python
solvency2.health.health_premium_volume(expected_next_year: float, earned_last_year: float, existing_future_pv: float, future_short_pv: float, future_long_pv: float, *, method: str, cap_evidence: Optional[Mapping[str, str]] = None, context: solvency2._core.core.Context)
```

Health-NSLT net premium volume; cohort/time selection and evidence are external.

Output unit: `context currency`. Sources: `DR:article-147:3`, `DR:article-147:4`, `DR:article-147:5`.

Fixed example: `health-nslt-2027-premium-standard`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-nslt-2027-premium-standard')
context = replace(base, **case.get('context', {}))
result = s2.health_premium_volume(**case['kwargs'], context=context)
# Independent expected value: 160
```

Example input (JSON):

```json
{
  "expected_next_year": 80,
  "earned_last_year": 100,
  "existing_future_pv": 10,
  "future_short_pv": 20,
  "future_long_pv": 100,
  "method": "standard"
}
```

### health_reserve_volume

```python
solvency2.health.health_reserve_volume(claims_best_estimate: float, eligible_recoverables: float, *, context: solvency2._core.core.Context)
```

Health-NSLT claims volume; recoverables exclude208(2) finite/similar RI.

Output unit: `context currency`. Sources: `DR:article-147:6`.

Fixed example: `health-reserve-net`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-reserve-net')
context = replace(base, **case.get('context', {}))
result = s2.health_reserve_volume(**case['kwargs'], context=context)
# Independent expected value: 75
```

Example input (JSON):

```json
{
  "claims_best_estimate": 100,
  "eligible_recoverables": 25
}
```

### health_premium_reserve_risk

```python
solvency2.health.health_premium_reserve_risk(segments: Mapping[str, dict], *, uses_usp: bool, uses_hres: bool, reserve_adjustments: Optional[Mapping] = None, adjustment_reference: str | None = None, context: solvency2._core.core.Context)
```

Four-segment standard selector; USP/HRES are deliberately not substituted.

Use premium_reserve_parameterised_risk for already qualified effective
USP/HRES sigmas. This automatic standard selector does not choose them.

The2027 profile requires all four externally qualified reserve factors,
including explicit ones for segments without a qualifying ADC adjustment.
Historical calculations reject these future-only inputs.

Output unit: `context currency`. Sources: `DR:article-146`, `DR:article-147:2`, `DR:article-148`, `DR:annex-XIV`, `DR:annex-XV`.

Fixed example: `health-pr-zero`. 19 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-pr-zero')
context = replace(base, **case.get('context', {}))
result = s2.health_premium_reserve_risk(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "segments": {
    "1": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "2": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "3": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    },
    "4": {
      "premium_volume": 0,
      "reserve_volume": 0,
      "geographic_diversification": 1
    }
  },
  "uses_usp": false,
  "uses_hres": false
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### health_hres_sigma_bound

```python
solvency2.health.health_hres_sigma_bound(segment: str, risk: str, representative_sigma: float, *, context: solvency2._core.core.Context)
```

Bound an external representative estimate; this does not determine an official HRES sigma.

Output unit: `ratio`. Sources: `DR:article-149:2:b-c`, `DR:annex-XIV`.

Fixed example: `future-hres-premium-floor`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-hres-premium-floor')
context = replace(base, **case.get('context', {}))
result = s2.health_hres_sigma_bound(**case['kwargs'], context=context)
# Independent expected value: 0.016666666666666666
```

Example input (JSON):

```json
{
  "segment": "1",
  "risk": "premium",
  "representative_sigma": 0
}
```

### health_hres_mixed_sigma

```python
solvency2.health.health_hres_mixed_sigma(segment: str, risk: str, non_hres_volume: float, hres_volume: float, hres_sigma: float, *, parameter_reference: str, qualification: Optional[Mapping] = None, context: solvency2._core.core.Context)
```

Mix separately calculated volumes; a source reference is not a legal applicability decision.

Bounds are reported independently instead of silently changing a supplied
external parameter. Optional qualification additionally rejects declared
ineligibility or bound contradictions; omission stays explicitly unchecked.
This component is not the complete HRES risk module.

Output unit: `ratio`. Sources: `DR:article-149:3-4`, `DR:annex-XIV`.

Fixed example: `future-hres-premium-mixed`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-hres-premium-mixed')
context = replace(base, **case.get('context', {}))
result = s2.health_hres_mixed_sigma(**case['kwargs'], context=context)
# Independent expected value: 0.032
```

Example input (JSON):

```json
{
  "segment": "1",
  "risk": "premium",
  "non_hres_volume": 40,
  "hres_volume": 60,
  "hres_sigma": 0.02,
  "parameter_reference": "SYN-EXTERNAL-HRES-NOT-LEGAL-SIGNOFF"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### health_income_incidence_stress

```python
solvency2.health.health_income_incidence_stress(rate: float, period: str, *, rate_basis: str, context: solvency2._core.core.Context)
```

Stress incidence for an explicitly assigned period; jointly project all156 changes.

Output unit: `rate`. Sources: `DR:article-156:a-b`.

Fixed example: `health-income-later_years-intensity`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-income-later_years-intensity')
context = replace(base, **case.get('context', {}))
result = s2.health_income_incidence_stress(**case['kwargs'], context=context)
# Independent expected value: 2.5
```

Example input (JSON):

```json
{
  "rate": 2,
  "period": "later_years",
  "rate_basis": "intensity"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### health_income_transition_stress

```python
solvency2.health.health_income_transition_stress(rate: float, transition: str, *, context: solvency2._core.core.Context)
```

Apply strict recovery / inclusive continuation thresholds without normalisation.

No complementary transition is inferred or reconstructed. The supplied
valuation model must define coherent state transitions and joint projection.

Output unit: `probability`. Sources: `DR:article-156:c-d`.

Fixed example: `health-income-recovery-0`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-income-recovery-0')
context = replace(base, **case.get('context', {}))
result = s2.health_income_transition_stress(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "rate": 0,
  "transition": "recovery"
}
```

### health_biometric_stress

```python
solvency2.health.health_biometric_stress(rate: float, shock: str, *, rate_basis: str, selected: bool | None, selection_reference: str, context: solvency2._core.core.Context)
```

Stress only explicitly selected SLT health contracts, not their BOF valuation.

Selection, permitted grouping and underlying reinsurance contracts remain
external. Probability and intensity bases are never silently interconverted.

Output unit: `rate`. Sources: `DR:article-152:1-3`, `DR:article-153:1-3`.

Fixed example: `health-2027-biometric-intensity`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-2027-biometric-intensity')
context = replace(base, **case.get('context', {}))
result = s2.health_biometric_stress(**case['kwargs'], context=context)
# Independent expected value: 1.035
```

Example input (JSON):

```json
{
  "rate": 0.9,
  "shock": "mortality",
  "rate_basis": "intensity",
  "selected": true,
  "selection_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### health_nslt_lapse_factor

```python
solvency2.health.health_nslt_lapse_factor(category: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

NSLT health event share; do not apply SLT's three-scenario selection here.

Output unit: `ratio`. Sources: `DR:article-150:1-3`.

Fixed example: `health-nslt-2027-lapse-termination`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-nslt-2027-lapse-termination')
context = replace(base, **case.get('context', {}))
result = s2.health_nslt_lapse_factor(**case['kwargs'], context=context)
# Independent expected value: 0.4
```

Example input (JSON):

```json
{
  "category": "termination",
  "qualification_reference": "SYN"
}
```

### health_accident_benefit_mean

```python
solvency2.health.health_accident_benefit_mean(benefits: Mapping, *, valuation_reference: str, context: solvency2._core.core.Context, group_counts: Optional[Mapping] = None, grouping_reference: str | None = None)
```

Average only event-insured persons in the externally selected concentration.

The denominator is event-specific Ne, not the whole building count Cc.
Empty event populations require review, never an invented zero mean.

Output unit: `context currency`. Sources: `DR:article-162:4-5`.

Fixed example: `health-cat-2027-benefit-mean`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-cat-2027-benefit-mean')
context = replace(base, **case.get('context', {}))
result = s2.health_accident_benefit_mean(**case['kwargs'], context=context)
# Independent expected value: 2.5
```

Example input (JSON):

```json
{
  "benefits": {
    "a": 2,
    "b": 3
  },
  "valuation_reference": "SYN"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### health_accident_benefit_sum

```python
solvency2.health.health_accident_benefit_sum(benefits: Mapping, *, valuation_reference: str, context: solvency2._core.core.Context, group_counts: Optional[Mapping] = None, grouping_reference: str | None = None)
```

Sum externally qualified event benefits of resident insured persons.

Output unit: `context currency`. Sources: `DR:article-161:3-4`.

Fixed example: `health-accident-benefit-empty`. 11 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-accident-benefit-empty')
context = replace(base, **case.get('context', {}))
result = s2.health_accident_benefit_sum(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "benefits": {},
  "valuation_reference": "SYN-none"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`. Additional shared validation errors can apply.

### health_accident_concentration_loss

```python
solvency2.health.health_accident_concentration_loss(persons: float, mean_benefits: Mapping, *, concentration_reference: str, context: solvency2._core.core.Context)
```

Use the externally identified largest qualified building population, not largest loss.

Output unit: `context currency`. Sources: `DR:article-162:2-3`, `DR:annex-XVI`.

Fixed example: `health-concentration-loss`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-concentration-loss')
context = replace(base, **case.get('context', {}))
result = s2.health_accident_concentration_loss(**case['kwargs'], context=context)
# Independent expected value: 1865
```

Example input (JSON):

```json
{
  "persons": 10,
  "mean_benefits": {
    "death": 100,
    "permanent_disability": 200,
    "twelve_month_disability": 300,
    "medical_treatment": 400
  },
  "concentration_reference": "SYN-largest-building"
}
```

### health_accident_country_aggregation

```python
solvency2.health.health_accident_country_aggregation(country_charges: Mapping, peril: str, *, scope_reference: str, context: solvency2._core.core.Context)
```

Root-sum-square of already valued country BOF charges, never of gross claims.

Output unit: `context currency`. Sources: `DR:article-161:1`, `DR:article-162:1`.

Fixed example: `health-accident-concentration-empty`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-accident-concentration-empty')
context = replace(base, **case.get('context', {}))
result = s2.health_accident_country_aggregation(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "country_charges": {},
  "peril": "concentration",
  "scope_reference": "SYN-none"
}
```

### health_mass_accident_loss

```python
solvency2.health.health_mass_accident_loss(segment: str, event_exposures: Mapping, *, exposure_reference: str, context: solvency2._core.core.Context)
```

Gross claim for one printed AnnexXVI segment, before reinsurance and BOF revaluation.

Output unit: `context currency`. Sources: `DR:article-161:2`, `DR:annex-XVI`.

Fixed example: `health-cat-2027-region-AT`. 63 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-cat-2027-region-AT')
context = replace(base, **case.get('context', {}))
result = s2.health_mass_accident_loss(**case['kwargs'], context=context)
# Independent expected value: 3
```

Example input (JSON):

```json
{
  "segment": "AT",
  "event_exposures": {
    "death": 10000,
    "permanent_disability": 0,
    "twelve_month_disability": 0,
    "medical_treatment": 0
  },
  "exposure_reference": "SYN"
}
```

### health_pandemic_income_exposure

```python
solvency2.health.health_pandemic_income_exposure(benefits: Mapping, *, valuation_reference: str, context: solvency2._core.core.Context)
```

Sum externally valued permanent-disability benefits with no recovery assumed.

Occupational accident obligations are excluded by external classification;
recurring benefits require externally supplied best estimates, not face sums.

Output unit: `context currency`. Sources: `DR:article-163:2`.

Fixed example: `health-pandemic-income-empty`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-pandemic-income-empty')
context = replace(base, **case.get('context', {}))
result = s2.health_pandemic_income_exposure(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "benefits": {},
  "valuation_reference": "SYN-no-income-exposures"
}
```

### health_pandemic_loss

```python
solvency2.health.health_pandemic_loss(income_exposure: float, countries: Mapping, *, exposure_reference: str, context: solvency2._core.core.Context)
```

Gross sudden scenario claim before reinsurance; country residence/scope external.

Output unit: `context currency`. Sources: `DR:article-163:1`.

Fixed example: `health-pandemic-zero`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-pandemic-zero')
context = replace(base, **case.get('context', {}))
result = s2.health_pandemic_loss(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "income_exposure": 0,
  "countries": {},
  "exposure_reference": "SYN-empty"
}
```

### health_pandemic_medical_cost

```python
solvency2.health.health_pandemic_medical_cost(costs: Mapping, *, valuation_reference: str, context: solvency2._core.core.Context)
```

Weight all three externally valued care types; never silently normalise overrides.

Output unit: `context currency`. Sources: `DR:article-163:3`, `DR:annex-XVI`.

Fixed example: `health-cat-2027-care-hospital`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-cat-2027-care-hospital')
context = replace(base, **case.get('context', {}))
result = s2.health_pandemic_medical_cost(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "costs": {
    "hospital": 100,
    "general_practitioner": 0,
    "no_formal_care": 0
  },
  "valuation_reference": "SYN"
}
```

### health_lapse_option_stress

```python
solvency2.health.health_lapse_option_stress(exercise_rate: float, direction: str, *, option_kind: str, selected: bool | None, selection_reference: str, context: solvency2._core.core.Context)
```

Stress relevant exercise/non-exercise probability with health-specific parameters.

Output unit: `probability`. Sources: `DR:article-159:2-5`.

Fixed example: `health-2027-extension-up`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-2027-extension-up')
context = replace(base, **case.get('context', {}))
result = s2.health_lapse_option_stress(**case['kwargs'], context=context)
# Independent expected value: 0.7
```

Example input (JSON):

```json
{
  "exercise_rate": 0.8,
  "direction": "up",
  "option_kind": "extension",
  "selected": true,
  "selection_reference": "SYN"
}
```

### health_lapse_risk

```python
solvency2.health.health_lapse_risk(gross_losses: Mapping, net_losses: Mapping, *, valuation_reference: str, tie_break: str | None = None, context: solvency2._core.core.Context)
```

Select the gross SLT health lapse charge corresponding to maximum net loss.

Output unit: `context currency`. Sources: `DR:article-159:1`, `DR:article-159:7`, `DR:article-206:2`.

Fixed example: `health-2027-lapse-selection`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-2027-lapse-selection')
context = replace(base, **case.get('context', {}))
result = s2.health_lapse_risk(**case['kwargs'], context=context)
# Independent expected value: 20
```

Example input (JSON):

```json
{
  "gross_losses": {
    "up": 10,
    "down": 20,
    "mass": 30
  },
  "net_losses": {
    "up": 5,
    "down": 15,
    "mass": 10
  },
  "valuation_reference": "SYN"
}
```

Reference-tested failure codes: `AMBIGUOUS_SELECTION`. Additional shared validation errors can apply.

### health_mass_lapse_factor

```python
solvency2.health.health_mass_lapse_factor(category: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Return the40% event share, not proportional capital or life special-category70%.

Uniform joint events, underlying reinsurance contracts and the worst
termination form require external qualification in either reference profile.

Output unit: `ratio`. Sources: `DR:article-159:6`.

Fixed example: `health-mass-future_159_6_b`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-mass-future_159_6_b')
context = replace(base, **case.get('context', {}))
result = s2.health_mass_lapse_factor(**case['kwargs'], context=context)
# Independent expected value: 0.4
```

Example input (JSON):

```json
{
  "category": "future_159_6_b",
  "qualification_reference": "SYN-159"
}
```

### health_expense_inflation_stress

```python
solvency2.health.health_expense_inflation_stress(inflation_rate: float, *, context: solvency2._core.core.Context)
```

Add the expense inflation shock without choosing a projection convention.

Output unit: `rate`. Sources: `DR:article-157:b`.

Fixed example: `health-inflation`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-inflation')
context = replace(base, **case.get('context', {}))
result = s2.health_expense_inflation_stress(**case['kwargs'], context=context)
# Independent expected value: 0.03
```

Example input (JSON):

```json
{
  "inflation_rate": 0.02
}
```

### health_expense_level_stress

```python
solvency2.health.health_expense_level_stress(expense: float, *, context: solvency2._core.core.Context)
```

Stress eligible own/cedent costs jointly with inflation in external projection.

Output unit: `context currency`. Sources: `DR:article-157:a`.

Fixed example: `health-expense-zero`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-expense-zero')
context = replace(base, **case.get('context', {}))
result = s2.health_expense_level_stress(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "expense": 0
}
```

### health_revision_stress

```python
solvency2.health.health_revision_stress(annuity_benefit: float, *, revision_exposed: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

Stress externally selected inflation/legal/health revision-exposed annuities.

Output unit: `context currency`. Sources: `DR:article-158`.

Fixed example: `health-2027-revision-true`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-2027-revision-true')
context = replace(base, **case.get('context', {}))
result = s2.health_revision_stress(**case['kwargs'], context=context)
# Independent expected value: 104
```

Example input (JSON):

```json
{
  "annuity_benefit": 100,
  "revision_exposed": true,
  "qualification_reference": "SYN"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### health_disability_risk

```python
solvency2.health.health_disability_risk(medical_charge: float, income_protection_charge: float, *, classification_reference: str, context: solvency2._core.core.Context)
```

Sum disjoint SLT medical/income charges; no diversification or classification inference.

Output unit: `context currency`. Sources: `DR:article-154:1-2`.

Fixed example: `health-2027-disability-sum`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-2027-disability-sum')
context = replace(base, **case.get('context', {}))
result = s2.health_disability_risk(**case['kwargs'], context=context)
# Independent expected value: 7
```

Example input (JSON):

```json
{
  "medical_charge": 4,
  "income_protection_charge": 3,
  "classification_reference": "SYN"
}
```

### health_medical_inflation_stress

```python
solvency2.health.health_medical_inflation_stress(inflation_rate: float, direction: str, *, context: solvency2._core.core.Context)
```

Add/subtract percentage points without inventing a compounding model.

Output unit: `rate`. Sources: `DR:article-155:2:b`, `DR:article-155:3:b`.

Fixed example: `health-medical-inflation-up`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-medical-inflation-up')
context = replace(base, **case.get('context', {}))
result = s2.health_medical_inflation_stress(**case['kwargs'], context=context)
# Independent expected value: 0.03
```

Example input (JSON):

```json
{
  "inflation_rate": 0.02,
  "direction": "up"
}
```

### health_medical_payment_stress

```python
solvency2.health.health_medical_payment_stress(payment: float, direction: str, *, context: solvency2._core.core.Context)
```

Stress payments jointly with inflation in the external permanent projection.

Output unit: `context currency`. Sources: `DR:article-155:2:a`, `DR:article-155:3:a`.

Fixed example: `health-medical-payment-zero`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-medical-payment-zero')
context = replace(base, **case.get('context', {}))
result = s2.health_medical_payment_stress(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "payment": 0,
  "direction": "up"
}
```

### health_medical_risk

```python
solvency2.health.health_medical_risk(up_charge: float, down_charge: float, *, valuation_reference: str, context: solvency2._core.core.Context)
```

Maximum of two joint-scenario charges; no extra net-selection rule is inferred.

Output unit: `context currency`. Sources: `DR:article-155:1`.

Fixed example: `health-2027-medical-maximum`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'health-2027-medical-maximum')
context = replace(base, **case.get('context', {}))
result = s2.health_medical_risk(**case['kwargs'], context=context)
# Independent expected value: 4
```

Example input (JSON):

```json
{
  "up_charge": 3,
  "down_charge": 4,
  "valuation_reference": "SYN"
}
```

## solvency2.provisions

### technical_provision_assumptions_evidence_check

```python
solvency2.provisions.technical_provision_assumptions_evidence_check(evidence: Mapping[str, dict], conditions: Mapping[str, bool], *, assessment_reference: str, scope_reference: str, context: solvency2._core.core.Context)
```

Inventory assumptions, management actions, FDB and behaviour evidence.

Financial models and insurer-specific behaviour remain external. Conditional
evidence is selected from explicit qualified scope decisions. A fully declared
inventory proves neither method appropriateness nor supervisory compliance.

Output unit: `indicator`. Sources: `DR:articles-22-27`.

Fixed example: `tp-assumptions-baseline-all-empty`. 52 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tp-assumptions-baseline-all-empty')
context = replace(base, **case.get('context', {}))
result = s2.technical_provision_assumptions_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "conditions": {
    "entity_specific_information_used": true,
    "financial_market_assumptions_used": true,
    "financial_projection_model_used": true,
    "management_actions_assumed": true,
    "asset_dependent_discretionary_benefits": true,
    "policyholder_options_present": true,
    "behaviour_independence_assumed": true
  },
  "assessment_reference": "SYN-DR-method-inventory",
  "scope_reference": "SYN-external-scope-qualification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### technical_provision_projection_evidence_check

```python
solvency2.provisions.technical_provision_projection_evidence_check(evidence: Mapping[str, dict], conditions: Mapping[str, bool], *, assessment_reference: str, scope_reference: str, context: solvency2._core.core.Context)
```

Inventory projection scope/uncertainty/expenses, not simulate cashflows.

The 2027 expense basis reflects board decisions on new business; it does not
silently inherit the baseline assumption of future new business. Category
controls document relevance and appropriate inclusion, including reasoned
absence. Currency separation and gross reinsurance expenses remain explicit.

Output unit: `indicator`. Sources: `DR:articles-28-34`, `DR:article-36`.

Fixed example: `tp-projection-baseline-all-empty`. 40 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tp-projection-baseline-all-empty')
context = replace(base, **case.get('context', {}))
result = s2.technical_provision_projection_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "conditions": {
    "future_development_uncertainty_practicable": true,
    "options_or_guarantees_present": true,
    "grouped_contract_data_used": true,
    "scenario_dependence_present": true,
    "nonlife_obligations_present": true
  },
  "assessment_reference": "SYN-DR-method-inventory",
  "scope_reference": "SYN-external-scope-qualification"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### technical_provision_data_evidence_check

```python
solvency2.provisions.technical_provision_data_evidence_check(evidence: Mapping[str, dict], *, external_data_used: bool, data_deficiencies_present: bool, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory TP data-quality evidence without certifying data or methods.

External-data use and known deficiencies activate their own controls.
The 2027 climate-history safeguard is unconditional, not a defect-only rule.
AVAILABLE declares a reference, never verified content or legal compliance.

Output unit: `indicator`. Sources: `DR:article-19`, `DR:article-20`.

Fixed example: `tp-data-baseline-external-deficient-empty`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tp-data-baseline-external-deficient-empty')
context = replace(base, **case.get('context', {}))
result = s2.technical_provision_data_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "external_data_used": true,
  "data_deficiencies_present": true,
  "assessment_reference": "SYN-data-quality-inventory"
}
```

### best_estimate_approximation_conditions

```python
solvency2.provisions.best_estimate_approximation_conditions(conditions: Mapping[str, bool], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check declared data-deficiency exception, not create an approximation.

Inadequate internal processes cannot justify this exception. Neither an
invented materiality percentage nor a preferred actuarial model is supplied.

Output unit: `indicator`. Sources: `DR:article-21`.

Fixed example: `be-approx-baseline-combination-31`. 90 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'be-approx-baseline-combination-31')
context = replace(base, **case.get('context', {}))
result = s2.best_estimate_approximation_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "data_insufficient_for_reliable_method": true,
    "internal_processes_appropriate": true,
    "external_data_cannot_remedy": true,
    "data_adjustment_impracticable": true,
    "approximation_appropriate": true
  },
  "qualification_reference": "SYN-DR21-assessment"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### life_cashflow_grouping_conditions

```python
solvency2.provisions.life_cashflow_grouping_conditions(conditions: Mapping[str, bool], *, qualification_reference: str, context: solvency2._core.core.Context)
```

Check declared Article35 grouping safeguards, not a clustering model.

Individual-contract projection is the default. The insurer assesses undue
burden, risk similarity, faithful expenses/risks and comparable best estimates
including guarantees/options. No quantitative materiality cutoff is invented.

Output unit: `indicator`. Sources: `DR:article-35`.

Fixed example: `life-grouping-baseline-combination-15`. 54 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'life-grouping-baseline-combination-15')
context = replace(base, **case.get('context', {}))
result = s2.life_cashflow_grouping_conditions(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "conditions": {
    "individual_projection_unduly_burdensome": true,
    "risk_nature_complexity_not_materially_different": true,
    "risks_and_expenses_not_misrepresented": true,
    "best_estimates_approximately_equivalent_including_options": true
  },
  "qualification_reference": "SYN-DR35-actuarial-assessment"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### risk_margin_reference_asset_balance

```python
solvency2.provisions.risk_margin_reference_asset_balance(reference_scr: float, technical_provisions: float, recoverables: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

SCR + TP - recoverables, not an asset portfolio or optimisation result.

Preserve signs and disclose a negative implied balance. Qualification of
values and a feasible market-risk-minimising portfolio remain external.

Output unit: `currency`. Sources: `DR:article-38:1:g`.

Fixed example: `rm-reference-baseline-negative`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-reference-baseline-negative')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_reference_asset_balance(**case['kwargs'], context=context)
# Independent expected value: -100
```

Example input (JSON):

```json
{
  "reference_scr": 100,
  "technical_provisions": -200,
  "recoverables": 0,
  "qualification_reference": "SYN-38g"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### risk_margin_reference_evidence_check

```python
solvency2.provisions.risk_margin_reference_evidence_check(evidence: Mapping[str, dict], composite_undertaking: bool, material_residual_market_risk: bool, *, qualification_reference: str, assessment_reference: str, context: solvency2._core.core.Context)
```

Inventory reference-undertaking assumptions, never generate SCR runoff.

Composite splitting and residual non-interest market risk have explicit
externally assessed conditions. No quantitative materiality cutoff is
invented; deferred-tax loss absorption must not be assumed.

Output unit: `indicator`. Sources: `DR:article-38:1-3`.

Fixed example: `rm-reference-baseline-tax-missing`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-reference-baseline-tax-missing')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_reference_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {
    "whole_portfolio_transfer": {
      "status": "AVAILABLE",
      "reference": "SYN-whole_portfolio_transfer"
    },
    "reinsurance_spv_transfer": {
      "status": "AVAILABLE",
      "reference": "SYN-reinsurance_spv_transfer"
    },
    "no_preexisting_business_or_funds": {
      "status": "AVAILABLE",
      "reference": "SYN-no_preexisting_business_or_funds"
    },
    "no_new_business": {
      "status": "AVAILABLE",
      "reference": "SYN-no_new_business"
    },
    "own_funds_equal_scr": {
      "status": "AVAILABLE",
      "reference": "SYN-own_funds_equal_scr"
    },
    "asset_balance": {
      "status": "AVAILABLE",
      "reference": "SYN-asset_balance"
    },
    "market_risk_minimisation": {
      "status": "AVAILABLE",
      "reference": "SYN-market_risk_minimisation"
    },
    "underwriting_risk": {
      "status": "AVAILABLE",
      "reference": "SYN-underwriting_risk"
    },
    "credit_risks": {
      "status": "AVAILABLE",
      "reference": "SYN-credit_risks"
    },
    "operational_risk": {
      "status": "AVAILABLE",
      "reference": "SYN-operational_risk"
    },
    "tp_loss_absorption": {
      "status": "AVAILABLE",
      "reference": "SYN-tp_loss_absorption"
    },
    "management_actions": {
      "status": "AVAILABLE",
      "reference": "SYN-management_actions"
    },
    "reference_scr_equivalence": {
      "status": "AVAILABLE",
      "reference": "SYN-reference_scr_equivalence"
    },
    "materiality_basis": {
      "status": "AVAILABLE",
      "reference": "SYN-materiality_basis"
    }
  },
  "composite_undertaking": false,
  "material_residual_market_risk": false,
  "qualification_reference": "SYN-reference-basis",
  "assessment_reference": "SYN-runoff-file"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### risk_margin_proportional_scr

```python
solvency2.provisions.risk_margin_proportional_scr(initial_scr: float, initial_net_best_estimate: float, future_net_best_estimate: float, conditions: Mapping[str, bool], *, eligibility_reference: str, projection_reference: str, context: solvency2._core.core.Context)
```

SCR(t)=SCR(0)*BE_net(t)/BE_net(0); never apply lambda inside SCR(t).

BE(t) is valued AT time t, not a time-zero discounted cashflow surrogate.
Whole-path nonnegative BE and risk-profile assumptions are externally
qualified. No BE forecast or automatic method selection is produced.

Output unit: `currency`. Sources: `DR:article-58:a`, `RM_GUIDANCE:annex-IV:method-2`.

Fixed example: `rm-simple-baseline-m2-zero`. 19 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-simple-baseline-m2-zero')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_proportional_scr(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "initial_scr": 100,
  "initial_net_best_estimate": 1000,
  "future_net_best_estimate": 0,
  "conditions": {
    "proportionality_satisfied": true,
    "risk_profile_stable_or_deviation_immaterial": true,
    "all_net_best_estimates_nonnegative": true
  },
  "eligibility_reference": "SYN-method2",
  "projection_reference": "SYN-net-BE-times"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### risk_margin_percentage

```python
solvency2.provisions.risk_margin_percentage(net_best_estimate: float, percentage: float, conditions: Mapping[str, bool], *, eligibility_reference: str, percentage_reference: str, context: solvency2._core.core.Context)
```

Externally calibrated alpha_lob * BE_net(0), not a prescribed default alpha.

Percentage is a fraction (0.03 means3%). No unsupported100% cap is invented.
Scope, calibration, hierarchy, future BE and options/guarantees restrictions
are documented external qualifications, not inferred from the two numbers.

Output unit: `currency`. Sources: `DR:article-58:b`, `RM_GUIDANCE:annex-IV:method-4`.

Fixed example: `rm-simple-baseline-m4-zero`. 15 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-simple-baseline-m4-zero')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_percentage(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "net_best_estimate": 0,
  "percentage": 0.03,
  "conditions": {
    "proportionality_satisfied": true,
    "more_sophisticated_methods_unavailable": true,
    "all_net_best_estimates_nonnegative": true,
    "percentage_justified": true
  },
  "eligibility_reference": "SYN-method4",
  "percentage_reference": "SYN-calibrated-lob-alpha"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### risk_margin_duration

```python
solvency2.provisions.risk_margin_duration(initial_scr: float, modified_duration: float, discount_rate: float, conditions: Mapping[str, bool], *, eligibility_reference: str, basis_reference: str, context: solvency2._core.core.Context)
```

Baseline life formula including the divisor printed in archived Annex IV.

Duration and rate conventions are externally qualified. No curve fitting,
runoff model or automatic suitability determination is performed.

Output unit: `currency`. Sources: `DR:article-58:b`, `RM_GUIDANCE:annex-IV:method-3`.

Fixed example: `rm-duration-baseline-zero-scr`. 11 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-duration-baseline-zero-scr')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_duration(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "initial_scr": 0,
  "modified_duration": 2,
  "discount_rate": 0,
  "conditions": {
    "proportionality_satisfied": true,
    "risk_profile_stable_or_deviation_immaterial": true,
    "duration_basis_qualified": true,
    "life_insurance_scope": true
  },
  "eligibility_reference": "SYN-duration-qualification",
  "basis_reference": "SYN-duration-basis"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### risk_margin_adjusted_duration_2027

```python
solvency2.provisions.risk_margin_adjusted_duration_2027(initial_scr: float, cashflows: list[float], internal_rate: float, conditions: Mapping[str, bool], *, eligibility_reference: str, basis_reference: str, context: solvency2._core.core.Context)
```

Future life formula from deterministic annual net cashflows, first at k=1.

The supplied rate is the externally qualified IRR under the basic RFR term
structure. Signed individual cashflows are allowed; whole-path BE suitability
remains an external condition. Lambda is included in adjusted duration ONCE.

Output unit: `currency`. Sources: `DR:article-58:b`, `RM_GUIDANCE:annex-IV:method-3`.

Fixed example: `rm-duration-future-zero-scr`. 15 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-duration-future-zero-scr')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_adjusted_duration_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "initial_scr": 0,
  "cashflows": [
    0,
    100
  ],
  "internal_rate": 0,
  "conditions": {
    "proportionality_satisfied": true,
    "risk_profile_stable_or_deviation_immaterial": true,
    "duration_basis_qualified": true,
    "all_net_best_estimates_nonnegative": true,
    "no_material_options_guarantees": true,
    "deterministic_cashflows_without_options_or_rate_dependency": true,
    "life_insurance_scope": true
  },
  "eligibility_reference": "SYN-duration-qualification",
  "basis_reference": "SYN-duration-basis"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### risk_margin_reserve_scr

```python
solvency2.provisions.risk_margin_reserve_scr(net_claims_best_estimate: float, aggregated_reserve_sigma: float, premium_volume: float, conditions: Mapping[str, bool], *, eligibility_reference: str, projection_reference: str, context: solvency2._core.core.Context)
```

Reserve-only 3*sigma_res_mod*PCO_net(t), never the whole nonlife SCR.

Zero premium volume must be externally justified; no materiality threshold
is invented. Sigma and claims projections are external, including any USP
or profile-specific reinsurance adjustments. No lambda is applied here.

Output unit: `currency`. Sources: `DR:article-58:a`, `RM_GUIDANCE:annex-IV:method-1`.

Fixed example: `rm-reserve-baseline-zero`. 26 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-reserve-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_reserve_scr(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "net_claims_best_estimate": 0,
  "aggregated_reserve_sigma": 0.1,
  "premium_volume": 0,
  "conditions": {
    "proportionality_satisfied": true,
    "no_renewals_or_future_business": true,
    "zero_premium_basis_qualified": true,
    "aggregated_reserve_sigma_qualified": true
  },
  "eligibility_reference": "SYN-reserve-simplification",
  "projection_reference": "SYN-claims-runoff-sigma"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### risk_margin_lob_allocation

```python
solvency2.provisions.risk_margin_lob_allocation(total_risk_margin: float, allocation_shares: Mapping[str, float], lob: str, *, lifetime_contributions_qualified: bool, complete_scope_confirmed: bool, allocation_reference: str, context: solvency2._core.core.Context)
```

Apply a nonnegative externally qualified share; never infer it from SCR0.

Shares cover the actual portfolio's LOBs. Omitted unused LOBs are permitted
only with explicit full-scope confirmation. A1e-12 sum tolerance is numerical,
not a regulatory materiality threshold; shares are never renormalised.
Signed allocations are outside this component, not declared legally banned.

Output unit: `currency`. Sources: `DR:article-37:3`, `DIR:article-80`, `DR:annex-I`.

Fixed example: `rm-allocation-baseline-lob-1`. 96 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-allocation-baseline-lob-1')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_lob_allocation(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "total_risk_margin": 100,
  "allocation_shares": {
    "1": 1
  },
  "lob": "1",
  "lifetime_contributions_qualified": true,
  "complete_scope_confirmed": true,
  "allocation_reference": "SYN-qualified-lifetime-Lob"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### risk_margin_internal_model_required

```python
solvency2.provisions.risk_margin_internal_model_required(uses_approved_internal_model: bool, suitable_all_runoff_times: bool | None, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Regulatory selection condition only; insurer supplies the approved model.

A zero result does not approve another method. Suitability covers EVERY
runoff time; no such finding is inferred from one successful valuation.

Output unit: `indicator`. Sources: `DR:article-37:2`.

Fixed example: `rm-model-baseline-required`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rm-model-baseline-required')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin_internal_model_required(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "uses_approved_internal_model": true,
  "suitable_all_runoff_times": true,
  "qualification_reference": "SYN-approved-model-whole-runoff"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### contract_boundary_exclusion

```python
solvency2.provisions.contract_boundary_exclusion(*, coverage_after_qualifying_right: bool | None, premium_payment_enforceable: bool | None, assessment_reference: str, context: solvency2._core.core.Context)
```

Only the Article 18(3) negative screen; zero never proves contract membership.

'After' concerns coverage, not payment dates. Qualification of unilateral
rights, repricing and legal enforceability is supplied externally.

Output unit: `indicator`. Sources: `DR:article-18:3`.

Fixed example: `future-boundary-exclusion-true-true`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-boundary-exclusion-true-true')
context = replace(base, **case.get('context', {}))
result = s2.contract_boundary_exclusion(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "coverage_after_qualifying_right": true,
  "premium_payment_enforceable": true,
  "assessment_reference": "SYN-LEGAL-ASSESSMENT"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### contract_recognition_due

```python
solvency2.provisions.contract_recognition_due(contract_party_date: str, coverage_start_date: str, *, evidence_reference: str, context: solvency2._core.core.Context)
```

Has the first recognition time arrived? This does not reverse later derecognition.

Output unit: `indicator`. Sources: `DR:article-17`.

Fixed example: `future-recognition-party-first`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-recognition-party-first')
context = replace(base, **case.get('context', {}))
result = s2.contract_recognition_due(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "contract_party_date": "2027-01-01",
  "coverage_start_date": "2027-02-01",
  "evidence_reference": "SYN-CONTRACT"
}
```

### obligation_derecognition_condition

```python
solvency2.provisions.obligation_derecognition_condition(obligation_status: str | None, *, evidence_reference: str, context: solvency2._core.core.Context)
```

Qualified obligation state only, never automatic contract-end derecognition.

A terminated policy can retain claims obligations. The supplied status must
concern the specific obligation assessed, and remains externally unverified.

Output unit: `indicator`. Sources: `DR:article-17`.

Fixed example: `derecognition-baseline-active`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'derecognition-baseline-active')
context = replace(base, **case.get('context', {}))
result = s2.obligation_derecognition_condition(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "obligation_status": "ACTIVE",
  "evidence_reference": "SYN-obligation-status-not-contract-end"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### contract_unilateral_right

```python
solvency2.provisions.contract_unilateral_right(right_type: str, facts: Mapping[str, bool | None], *, assessment_reference: str, context: solvency2._core.core.Context)
```

Guideline2 unilateral-right screen, not full contract-boundary membership.

Restrictions must be externally qualified effective restrictions, including
the Article18 economic-effect assessment. Relevant third parties exclude
supervisors/governance bodies. Mere reputation or competition is not a veto.
Full risk reflection and the profile-specific life repricing clause remain
separate for an amendment right, even when this screen returns1.

Output unit: `indicator`. Sources: `DR:article-18:3`, `CB_GUIDANCE:guideline-2`.

Fixed example: `unilateral-baseline-amend-31`. 206 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'unilateral-baseline-amend-31')
context = replace(base, **case.get('context', {}))
result = s2.contract_unilateral_right(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "right_type": "amend",
  "facts": {
    "right_exists": true,
    "policyholder_or_third_party_restriction": true,
    "national_law_restriction": true,
    "sole_policyholder_or_beneficiary_decision": true,
    "claim_event_condition": true
  },
  "assessment_reference": "SYN-external-effective-rights"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### prudent_deterministic_eligibility_2027

```python
solvency2.provisions.prudent_deterministic_eligibility_2027(time_value_options: float, undertaking_scr: float, conditions: Mapping[str, bool], *, route: str, scenario_reference: str, qualification_reference: str, context: solvency2._core.core.Context, approval_evidence: Optional[Mapping] = None)
```

Strict5% time-value screen plus externally qualified route conditions.

SNC requires written method intention; non-SNC requires existing approval
and current conditions instead. This never grants supervisory approval or
computes option time value from an invented scenario set.

Output unit: `indicator`. Sources: `DIR:article-77:7-8`, `DR:article-34a:1`, `DR:article-327f:1`.

Fixed example: `prudent-snc-boundary`. 21 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'prudent-snc-boundary')
context = replace(base, **case.get('context', {}))
result = s2.prudent_deterministic_eligibility_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "time_value_options": 5,
  "undertaking_scr": 100,
  "conditions": {
    "clearly_identified_life_obligations": true,
    "options_guarantees_immaterial": true,
    "valuation_method_appropriate": true,
    "prescribed_scenarios_used": true,
    "scr_lac_loading_treatment_qualified": true,
    "small_non_complex": true,
    "written_method_intention": true
  },
  "route": "snc",
  "scenario_reference": "SYN-qualified-prescribed-scenario-basis",
  "qualification_reference": "SYN-prudent-method-qualification"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### prudent_deterministic_best_estimate_2027

```python
solvency2.provisions.prudent_deterministic_best_estimate_2027(deterministic_best_estimate: float, time_value_options: float, undertaking_scr: float, conditions: Mapping[str, bool], *, route: str, scenario_reference: str, qualification_reference: str, alternative_loading: float | None = None, alternative_loading_demonstrated: bool | None = None, alternative_loading_reference: str | None = None, context: solvency2._core.core.Context, approval_evidence: Optional[Mapping] = None)
```

BE_det + loading*SCR, with default5% or externally demonstrated loading.

The insurer supplies BE, SCR, scenario-based time value and the Article34a(3)
SCR/LAC-TP treatment. No stress valuation or circular SCR solver is invented.
Negative deterministic/net BE is preserved; no unsupported100% loading cap.

Output unit: `currency`. Sources: `DIR:article-77:8`, `DR:article-34a:2-3`, `DR:article-327f:1`.

Fixed example: `prudent-snc-negative-be`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'prudent-snc-negative-be')
context = replace(base, **case.get('context', {}))
result = s2.prudent_deterministic_best_estimate_2027(**case['kwargs'], context=context)
# Independent expected value: -5
```

Example input (JSON):

```json
{
  "time_value_options": 4.9,
  "undertaking_scr": 100,
  "conditions": {
    "clearly_identified_life_obligations": true,
    "options_guarantees_immaterial": true,
    "valuation_method_appropriate": true,
    "prescribed_scenarios_used": true,
    "scr_lac_loading_treatment_qualified": true,
    "small_non_complex": true,
    "written_method_intention": true
  },
  "route": "snc",
  "scenario_reference": "SYN-qualified-prescribed-scenario-basis",
  "qualification_reference": "SYN-prudent-method-qualification",
  "deterministic_best_estimate": -10
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### prudent_deterministic_non_snc_size_screen_2027

```python
solvency2.provisions.prudent_deterministic_non_snc_size_screen_2027(undertaking_type: str, life_gross_technical_provisions: float, total_gross_technical_provisions: float, market_shares: Mapping[str, float | None], *, size_exception_approved: bool, classification_reference: str, context: solvency2._core.core.Context)
```

Only Article327f size/market conditions, NOT supervisory approval.

Use EUR inputs for the absolute threshold. Market shares require the proper
home-state denominators: life gross TP versus nonlife gross written premiums.
Pure nonlife undertakings do not automatically face the life-size cap;
mixed undertakings do only at or above20% life gross TP. Any waiver is an
explicit external supervisory finding under paragraph3, never inferred here.

Output unit: `indicator`. Sources: `DR:article-327f:1:c`, `DR:article-327f:2-3`.

Fixed example: `prudent-size-waived`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'prudent-size-waived')
context = replace(base, **case.get('context', {}))
result = s2.prudent_deterministic_non_snc_size_screen_2027(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "undertaking_type": "life",
  "life_gross_technical_provisions": 13000000000,
  "total_gross_technical_provisions": 13000000000,
  "market_shares": {
    "life": 0.1,
    "nonlife": null
  },
  "size_exception_approved": true,
  "classification_reference": "SYN-DR327f-scope-market-bases"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_PARAMETER`. Additional shared validation errors can apply.

### risk_margin

```python
solvency2.provisions.risk_margin(projected_scr: list[float], basic_rates: list[float], runoff_complete: bool, *, context: solvency2._core.core.Context)
```

Discount SCR(t) of the Art.38 reference undertaking at basic rates t+1.

Output unit: `context currency`. Sources: `DR:article-37:1`, `DR:article-39`.

Fixed example: `risk-margin-2027-one-year`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'risk-margin-2027-one-year')
context = replace(base, **case.get('context', {}))
result = s2.risk_margin(**case['kwargs'], context=context)
# Independent expected value: 4.75
```

Example input (JSON):

```json
{
  "projected_scr": [
    100
  ],
  "basic_rates": [
    0
  ],
  "runoff_complete": true
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### best_estimate_cashflows

```python
solvency2.provisions.best_estimate_cashflows(cashflows: Mapping[str, dict], *, runoff_complete: bool, cashflow_reference: str, curve_reference: str, context: solvency2._core.core.Context)
```

Discount already probability-weighted, gross-of-reinsurance cashflows.

No projection model, curve interpolation or compounding convention is
invented here. Discount factors must match the payment dates and currency.
Inflows include premiums, not separately valued reinsurance recoverables.

Output unit: `context currency`. Sources: `DIR:article-77:2`.

Fixed example: `be-at-valuation-date`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'be-at-valuation-date')
context = replace(base, **case.get('context', {}))
result = s2.best_estimate_cashflows(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "cashflows": {
    "2025-01-17": {
      "expected_inflows": 0,
      "expected_outflows": 100,
      "discount_factor": 1
    }
  },
  "runoff_complete": true,
  "cashflow_reference": "SYN-GROSS-RUNOFF",
  "curve_reference": "SYN-DISCOUNT-FACTORS"
}
```

Reference-tested failure codes: `MISSING_INPUT`. Additional shared validation errors can apply.

### technical_provisions_sum

```python
solvency2.provisions.technical_provisions_sum(best_estimate: float, risk_margin: float, *, replication_applies: bool, context: solvency2._core.core.Context)
```

Separate BE/RM method only; negative best estimates/total provisions are not floored.

Output unit: `context currency`. Sources: `DIR:article-77:1`, `DIR:article-77:4`.

Fixed example: `tp-sum`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tp-sum')
context = replace(base, **case.get('context', {}))
result = s2.technical_provisions_sum(**case['kwargs'], context=context)
# Independent expected value: 118
```

Example input (JSON):

```json
{
  "best_estimate": 112,
  "risk_margin": 6,
  "replication_applies": false
}
```

Reference-tested failure codes: `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### replicated_cashflow_value

```python
solvency2.provisions.replicated_cashflow_value(market_values: Mapping[str, float], *, cashflow_features: Mapping[str, bool | None], replication_reference: str | None = None, market_reference: str | None = None, context: solvency2._core.core.Context)
```

Market-value arithmetic with mandatory exclusions, not replication approval.

Features concern the selected cashflows. References to all-scenario and
market evidence are retained but their substantive adequacy is external.

Output unit: `context currency`. Sources: `DR:article-40:2-4`, `DIR:article-77:4`.

Fixed example: `future-replication-zero-value`. 16 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-replication-zero-value')
context = replace(base, **case.get('context', {}))
result = s2.replicated_cashflow_value(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "market_values": {
    "SYN-A": 0
  },
  "cashflow_features": {
    "policyholder_options": false,
    "biometric_dependency": false,
    "future_servicing_expenses": false
  },
  "replication_reference": "SYN-ALL-SCENARIOS",
  "market_reference": "SYN-MARKET"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REPLICATION_EXCLUDED`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### technical_provisions_transitional_value

```python
solvency2.provisions.technical_provisions_transitional_value(current_gross_provisions: float, base_solvency2_net_provisions: float, base_legacy_net_provisions: float, *, supervisory_deduction_limit: float | None, risk_free_transition_used: bool | None, approval_reference: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Deduct the phased, optionally capped approved difference from current TP.

Base amounts are NET on the Article308d(2) date or approved recalibration;
the current provision is gross, with current recoverables remaining separate.
None limit explicitly means no supervisory cap was imposed, not unknown.
A negative deduction is not silently floored or turned into relief.

Output unit: `context currency`. Sources: `DIR:article-308d:1-5`.

Fixed example: `ltg-transition-baseline-tp-cap-zero`. 17 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'ltg-transition-baseline-tp-cap-zero')
context = replace(base, **case.get('context', {}))
result = s2.technical_provisions_transitional_value(**case['kwargs'], context=context)
# Independent expected value: 1100
```

Example input (JSON):

```json
{
  "approval_reference": "SYN-prior-valid-supervisory-approval",
  "qualification_reference": "SYN-qualified-basis-contracts-VA-and-approval-scope",
  "current_gross_provisions": 1100,
  "base_solvency2_net_provisions": 1200,
  "base_legacy_net_provisions": 1000,
  "supervisory_deduction_limit": 0,
  "risk_free_transition_used": false
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### best_estimate_contract_cashflows

```python
solvency2.provisions.best_estimate_contract_cashflows(obligations: collections.abc.Mapping, *, runoff_complete: bool, cashflow_reference: str, curve_reference: str, context: solvency2._core.core.Context)
```

Select entire qualified obligations, never truncate by a payment date.

Every row identifies a disjoint obligation or contract part. Its evidence
qualifies legal enforceability, unilateral rights, full-risk reflection,
profile-specific life rules, discernibility and any unbundling. Accepted
reinsurance is assessed independently of underlying contract boundaries.
These substantive qualifications remain external, not certified here.

Article18(5)(c) is cross-checked against the same-version English text;
the incomplete German source is preserved. Paid premiums, discernible
cover/guarantee or enforceable future premiums disapply this exception.
Unbundled parts are independently qualified, not inferred from cash flows.

Output unit: `context currency`. Sources: `DR:article-17`, `DR:article-18:1-6`, `CB_GUIDANCE:guideline-0`, `CB_GUIDANCE:guideline-3`, `CB_GUIDANCE:guideline-8`.

Fixed example: `contract-exception-baseline-enforceable`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'contract-exception-baseline-enforceable')
context = replace(base, **case.get('context', {}))
result = s2.best_estimate_contract_cashflows(**case['kwargs'], context=context)
# Independent expected value: 90
```

Example input (JSON):

```json
{
  "obligations": {
    "part": {
      "contract_party_date": "2020-01-01",
      "coverage_start_date": "2020-02-01",
      "obligation_status": "ACTIVE",
      "related_to_contract": true,
      "boundary": {
        "coverage_after_qualifying_right": false,
        "premium_payment_enforceable": true,
        "related_to_paid_premiums": false,
        "discernible_uncertain_event_cover": false,
        "discernible_financial_guarantee": false
      },
      "cashflows": {
        "2028-01-01": {
          "expected_inflows": 0,
          "expected_outflows": 100,
          "discount_factor": 0.9
        }
      },
      "assessment_reference": "SYN-independent-qualified-part-economics"
    }
  },
  "runoff_complete": true,
  "cashflow_reference": "SYN-complete",
  "curve_reference": "SYN-discount"
}
```

## solvency2.audit

### technical_provision_validation_evidence_check

```python
solvency2.audit.technical_provision_validation_evidence_check(evidence: Mapping[str, dict], conditions: Mapping[str, bool], declared_interval_years: float, *, assessment_reference: str, scope_reference: str, context: solvency2._core.core.Context)
```

Inventory validation and documentation references for an externally qualified scope.

The declared interval is not a calendar or proof of actual completion.
Scope must identify all homogeneous groups and applicable segregated parts;
references alone do not prove completeness, adequacy, or expert review.

Output unit: `indicator`. Sources: `DR:article-264`, `DR:article-265`.

Fixed example: `tp-validation-audit-baseline-empty-evidence`. 132 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'tp-validation-audit-baseline-empty-evidence')
context = replace(base, **case.get('context', {}))
result = s2.technical_provision_validation_evidence_check(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "evidence": {},
  "conditions": {
    "inadequacy_indications": true,
    "significant_management_action_impact": true,
    "matching_adjustment_used": true,
    "nonlife_obligations_present": true,
    "data_use_changed": true
  },
  "declared_interval_years": 1,
  "assessment_reference": "SYN-external-assessment-no-expert-review-by-engine",
  "scope_reference": "SYN-qualified-complete-homogeneous-groups-and-separate-TP-parts"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`. Additional shared validation errors can apply.

## solvency2.parameters

### NumericOverride

```python
solvency2.parameters.NumericOverride(resource: 'str', path: 'tuple[str | int, ...]', value: 'float', reason: 'str') -> None
```

One explicit analyst scenario value; path addresses an existing numeric resource cell.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### rule_profiles

```python
solvency2.parameters.rule_profiles() -> 'dict'
```

Return explicit profile intervals and supported scope, not legal approval.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### parameter

```python
solvency2.parameters.parameter(parameter_id: 'str', *, context: 'Context') -> 'dict'
```

Return a scalar, labelled matrix or table, including source and profile.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

## solvency2.workflow

### Engine

```python
solvency2.workflow.Engine()
```

Execute a DAG of documented atomic APIs; reuse identical nodes within an instance.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### calculate

```python
solvency2.workflow.calculate(nodes: 'dict', *, context: 'Context') -> 'dict'
```

Run atomic dependency nodes; pending full scope is always reported as PARTIAL.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

## solvency2.reference

### coverage

```python
solvency2.reference.coverage() -> 'dict'
```

Return machine-readable achieved scope and remaining limitations.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reference_cases

```python
solvency2.reference.reference_cases() -> 'dict'
```

Return a fresh copy of bundled synthetic cases and independent derivations.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reference_portfolios

```python
solvency2.reference.reference_portfolios() -> 'dict'
```

Return executable synthetic integration DAGs with independent expected values.

These partial reference portfolios retain explicit external valuation assumptions;
their baseline expectations do not certify analyst-overridden scenarios.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### export_resources

```python
solvency2.reference.export_resources(destination: 'str | Path', *, context: 'Context | None' = None) -> 'dict'
```

Export verified resources or a marked analyst scenario to a new directory.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### rfr_monthly_data

```python
solvency2.reference.rfr_monthly_data() -> 'dict'
```

Return a fresh synthetic market-data demo and the local-input schema.

No observed market values are bundled. Dates and coordinates are illustrative.
Production callers pass their own tables through the explicit market_data
keyword of the five rfr_archived_* functions, or use solvency2.data curves.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

## solvency2.rates

### rfr_credit_risk_adjustment

```python
solvency2.rates.rfr_credit_risk_adjustment(annual_mean_spread: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Bound half the externally qualified one-year mean spread (decimal rates).

The mean's observation calendar, market quality and maturity matching are
external inputs. This component does not bootstrap or extrapolate a curve.
Under the 2027 Article44 rule this arithmetic is only for qualified non-OIS
swaps requiring adjustment; the external reference must establish that scope.

Output unit: `rate`. Sources: `DR:article-45`.

Fixed example: `future-rfr-cra-2`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-cra-2')
context = replace(base, **case.get('context', {}))
result = s2.rfr_credit_risk_adjustment(**case['kwargs'], context=context)
# Independent expected value: 0.001
```

Example input (JSON):

```json
{
  "annual_mean_spread": 0,
  "qualification_reference": "SYN-qualified-one-year-mean"
}
```

### rfr_currency_risk_adjustment

```python
solvency2.rates.rfr_currency_risk_adjustment(*, qualification_reference: str, context: solvency2._core.core.Context, calibration: Optional[Mapping] = None)
```

Signed CURA: archived uniform value or a qualified formula illustration.

EIOPA-BoS-24-533 8.3.2 / EIOPA-BoS-26-198 7.3.2. A company's formula
result is NOT the uniform adjustment published for all undertakings.
Qualification includes Article48(1), currency/date and input convention.
In particular, lac_ratio is the source ratio, not a negative LAC amount.

Output unit: `rate`. Sources: `DR:article-48:2`.

Fixed example: `rfr-cura-baseline-published-dkk`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-cura-baseline-published-dkk')
context = replace(base, **case.get('context', {}))
result = s2.rfr_currency_risk_adjustment(**case['kwargs'], context=context)
# Independent expected value: -0.0001
```

Example input (JSON):

```json
{
  "qualification_reference": "SYN-Art48-qualified-currency-date-and-source-convention"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### rfr_market_rate_adjustment

```python
solvency2.rates.rfr_market_rate_adjustment(market_rate: float, credit_adjustment: float, currency_adjustment: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Apply CRA and signed CURA once before existing curve construction.

Positive CRA is subtracted; nonpositive CURA is added. No zero floor.
Inputs must refer to the same qualified market instrument/tenor/date;
this is not a shift to an already extrapolated curve or a VA/MA operation.

Output unit: `rate`. Sources: `DR:article-44:1`, `DR:article-48:2`.

Fixed example: `rfr-cura-baseline-market-no-adjustments`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-cura-baseline-market-no-adjustments')
context = replace(base, **case.get('context', {}))
result = s2.rfr_market_rate_adjustment(**case['kwargs'], context=context)
# Independent expected value: -0.01
```

Example input (JSON):

```json
{
  "qualification_reference": "SYN-Art48-qualified-currency-date-and-source-convention",
  "market_rate": -0.01,
  "credit_adjustment": 0,
  "currency_adjustment": 0
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### rfr_transitional_spot_rate

```python
solvency2.rates.rfr_transitional_spot_rate(spot_rate: float, legacy_rate: float, equivalent_annual_rate: float, *, matching_adjustment_used: bool | None, technical_provisions_transition_used: bool | None, approval_reference: str, qualification_reference: str, context: solvency2._core.core.Context)
```

Add the approved currency-specific annual transition to one curve point.

The equivalent annual rate must value the eligible portfolio on the matching
basis including applicable VA. Existing rfr_equivalent_annual_rate can solve
nonnegative cashflows; mixed-sign portfolios need qualified external roots.
Do not include eligible obligations in VA calculation or combine with MA/308d.

Output unit: `rate`. Sources: `DIR:article-308c:1-4`.

Fixed example: `ltg-transition-baseline-rate-2025-01-17`. 17 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'ltg-transition-baseline-rate-2025-01-17')
context = replace(base, **case.get('context', {}))
result = s2.rfr_transitional_spot_rate(**case['kwargs'], context=context)
# Independent expected value: 0.02875
```

Example input (JSON):

```json
{
  "approval_reference": "SYN-prior-valid-supervisory-approval",
  "qualification_reference": "SYN-qualified-basis-contracts-VA-and-approval-scope",
  "spot_rate": 0.02,
  "legacy_rate": 0.04,
  "equivalent_annual_rate": 0.02,
  "matching_adjustment_used": false,
  "technical_provisions_transition_used": false
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### rfr_risk_correction_2027

```python
solvency2.rates.rfr_risk_correction_2027(spread: float, long_term_average_spread: float, asset_class: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Piecewise correction for a qualified homogeneous spread bucket, decimal rates.

EEA sovereign classification, matching duration/quality and 30-year LTAS
estimation are external. This is not a choice of portfolio-weight denominator.

Output unit: `rate`. Sources: `DR:article-51:2-3`.

Fixed example: `future-rc-other-0`. 20 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rc-other-0')
context = replace(base, **case.get('context', {}))
result = s2.rfr_risk_correction_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "spread": 0,
  "long_term_average_spread": 0.01,
  "asset_class": "other",
  "qualification_reference": "SYN-explicit-qualified-2027-inputs"
}
```

### rfr_credit_spread_sensitivity

```python
solvency2.rates.rfr_credit_spread_sensitivity(asset_pvbp: float | None, liability_pvbp: float | None, *, qualification_reference: str, context: solvency2._core.core.Context, reuse: dict | None = None)
```

CSSR from separately qualified PVBP amounts, not their revaluation model.

Output unit: `ratio`. Sources: `DR:article-51a:1`.

Fixed example: `future-cssr-0`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-cssr-0')
context = replace(base, **case.get('context', {}))
result = s2.rfr_credit_spread_sensitivity(**case['kwargs'], context=context)
# Independent expected value: 0.5
```

Example input (JSON):

```json
{
  "asset_pvbp": 2,
  "liability_pvbp": 4,
  "qualification_reference": "SYN-explicit-qualified-2027-inputs"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### rfr_volatility_adjustment_2027

```python
solvency2.rates.rfr_volatility_adjustment_2027(risk_corrected_spread: float, credit_spread_sensitivity: float, *, qualification_reference: str, context: solvency2._core.core.Context, firm_adjustment: dict | None = None)
```

Currency VA only; no automatic macro addition or undertaking-specific approval.

Output unit: `rate`. Sources: `DIR:article-77d:3`.

Fixed example: `future-va-2`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-va-2')
context = replace(base, **case.get('context', {}))
result = s2.rfr_volatility_adjustment_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "risk_corrected_spread": 0.02,
  "credit_spread_sensitivity": 0,
  "qualification_reference": "SYN-explicit-qualified-2027-inputs"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### rfr_macro_country_factor

```python
solvency2.rates.rfr_macro_country_factor(country_risk_corrected_spread: float, debt_asset_share: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Country debt/all-assets share, not an insurer's own portfolio weight.

Output unit: `ratio`. Sources: `DIR:article-77d:4`.

Fixed example: `future-country-factor-3`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-country-factor-3')
context = replace(base, **case.get('context', {}))
result = s2.rfr_macro_country_factor(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "country_risk_corrected_spread": 0.006,
  "debt_asset_share": 1,
  "qualification_reference": "SYN-explicit-qualified-2027-inputs"
}
```

### rfr_macro_volatility_adjustment

```python
solvency2.rates.rfr_macro_volatility_adjustment(country_risk_corrected_spread: float, euro_risk_corrected_spread: float, credit_spread_sensitivity: float, country_factor: float, *, undertaking_specific_adjustment_applies: bool, qualification_reference: str, context: solvency2._core.core.Context)
```

Euro macro add-on; explicitly incompatible with undertaking-specific adjustment.

Output unit: `rate`. Sources: `DIR:article-77d:4`, `DIR:article-77d:1c`.

Fixed example: `future-macro-va-2`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-macro-va-2')
context = replace(base, **case.get('context', {}))
result = s2.rfr_macro_volatility_adjustment(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "country_risk_corrected_spread": 0.02,
  "euro_risk_corrected_spread": 0.01,
  "credit_spread_sensitivity": 0,
  "country_factor": 0.5,
  "undertaking_specific_adjustment_applies": false,
  "qualification_reference": "SYN-explicit-qualified-2027-inputs"
}
```

### rfr_va_pvbp

```python
solvency2.rates.rfr_va_pvbp(unadjusted_value: float, adjusted_value: float, notional_va: float, valuation_kind: str, *, qualification_reference: str, context: solvency2._core.core.Context, pegged_currency: str | None = None, pegged_notional_va: float | None = None)
```

Literal revaluation difference/VA*, not a valuation model or per-bp rescaling.

Qualified asset values exclude immaterial unit-linked spread exposure.
Qualified BEL includes future discretionary benefits without feeding back
the asset spread shock. Paired values are already in one reporting currency.

Output unit: `currency_per_rate`. Sources: `DR:article-51a:2-3`, `DR:article-51b:2-3`.

Fixed example: `future-pvbp-0`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-pvbp-0')
context = replace(base, **case.get('context', {}))
result = s2.rfr_va_pvbp(**case['kwargs'], context=context)
# Independent expected value: 200
```

Example input (JSON):

```json
{
  "unadjusted_value": 100,
  "adjusted_value": 98,
  "notional_va": 0.01,
  "valuation_kind": "assets",
  "qualification_reference": "SYN-qualified-revaluation-and-currency-scope"
}
```

### rfr_pegged_credit_spread_sensitivity

```python
solvency2.rates.rfr_pegged_credit_spread_sensitivity(asset_pvbp: float, liability_pvbp: float, pegged_currency: str, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Common CSSR from qualified combined amounts, never average individual CSSRs.

Peg eligibility and use of the adjusted euro curve under Article48 are
external. The currency identifier alone is not evidence of their validity.

Output unit: `ratio`. Sources: `DR:article-51b:1`.

Fixed example: `future-cssr-pegged-3`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-cssr-pegged-3')
context = replace(base, **case.get('context', {}))
result = s2.rfr_pegged_credit_spread_sensitivity(**case['kwargs'], context=context)
# Independent expected value: 1
```

Example input (JSON):

```json
{
  "asset_pvbp": 100,
  "liability_pvbp": 0,
  "pegged_currency": "DKK",
  "qualification_reference": "SYN-qualified-revaluation-and-currency-scope"
}
```

### rfr_fundamental_spread

```python
solvency2.rates.rfr_fundamental_spread(long_term_average_spread: float, asset_class: str, default_statistics_reliable: bool, *, default_spread: float | None = None, downgrade_spread: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Compose external credit spreads with the class floor or exact fallback.

eu_central means EU member-state central governments/central banks, not
all public-sector entities. Statistics and 30-year history qualification
remain external; this does not derive PDs or downgrade replacement losses.

Output unit: `rate`. Sources: `DIR:article-77c:2`.

Fixed example: `future-rfr-fs-6`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-fs-6')
context = replace(base, **case.get('context', {}))
result = s2.rfr_fundamental_spread(**case['kwargs'], context=context)
# Independent expected value: 0.0035
```

Example input (JSON):

```json
{
  "long_term_average_spread": 0.01,
  "asset_class": "other",
  "default_statistics_reliable": false,
  "qualification_reference": "SYN"
}
```

### rfr_downgrade_expected_loss

```python
solvency2.rates.rfr_downgrade_expected_loss(scenarios: Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Weight qualified immediate replacement losses, not a rating/migration model.

Distinct downgrade states share a horizon and valuation basis. Residual
probability is no downgrade, with no downgrade loss; never renormalize.
The result is a currency amount, NOT a spread or a market-value percentage.

Output unit: `context currency`. Sources: `DR:article-54:4`, `DIR:article-77c:2:a:ii`.

Fixed example: `rfr-downgrade-baseline-zero`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-downgrade-baseline-zero')
context = replace(base, **case.get('context', {}))
result = s2.rfr_downgrade_expected_loss(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "scenarios": {
    "zero": {
      "probability": 0,
      "replacement_loss": 10,
      "conditions": {
        "downgrade_event": true,
        "immediate_replacement": true,
        "same_cashflow_pattern": true,
        "same_asset_class": true,
        "replacement_quality_at_least_pre_downgrade": true
      }
    }
  },
  "qualification_reference": "SYN"
}
```

### rfr_smith_wilson_spot

```python
solvency2.rates.rfr_smith_wilson_spot(payment_times, cashflows, prices, maturity, *, ufr, qualification_reference: str, output_maturities=(), alpha_search_max=2.0, volatility_adjustment=None, matching_adjustment=None, context: solvency2._core.core.Context)
```

Fit qualified instruments once and return annual spot plus optional grid.

Cashflow rows are payment dates, columns are instruments. Prices share
their cashflows' nominal basis. Signed coupons are allowed (section9.15).
The last payment time is the externally qualified LLP. Qualification
includes DLT selection, input availability, dates, CRA and currency basis.
Alpha search is the documented heuristic, not a global optimality proof.
The technical search bound is explicit and is NOT a regulatory alpha cap.

Output unit: `rate`. Sources: `DR:article-43:1-2`, `DR:article-44:1`, `DR:article-46:1`.

Fixed example: `rfr-smith-wilson-flat-zero`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-smith-wilson-flat-zero')
context = replace(base, **case.get('context', {}))
result = s2.rfr_smith_wilson_spot(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "payment_times": [
    1,
    2
  ],
  "cashflows": [
    [
      1,
      0
    ],
    [
      0,
      1
    ]
  ],
  "prices": [
    1,
    1
  ],
  "maturity": 60,
  "ufr": 0,
  "qualification_reference": "SYN-flat-zero"
}
```

Reference-tested failure codes: `INVALID_INPUT`. Additional shared validation errors can apply.

### rfr_ultimate_forward_rate

```python
solvency2.rates.rfr_ultimate_forward_rate(annual_rates: collections.abc.Mapping, previous_real_rate: float, previous_ufr: float, inflation: collections.abc.Mapping, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Derive the context year's UFR using the prior year's annual calculation.

Annual history ends one year before that calculation, hence two years
before application. AMECO/OECD source qualification and any no-target
ARMA projection remain external. No term premium is added. Fractions
preserve decimal grid/threshold boundaries and never fill missing years.

Output unit: `rate`. Sources: `DR:article-47:1-2`.

Fixed example: `rfr-ufr-complete-history-baseline`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-ufr-complete-history-baseline')
context = replace(base, **case.get('context', {}))
result = s2.rfr_ultimate_forward_rate(**case['kwargs'], context=context)
# Independent expected value: 0.0405
```

Inspect `case['kwargs']` for the complete nested input mapping (kept in the bundled dataset rather than duplicated here).

### rfr_curve_spot_2027

```python
solvency2.rates.rfr_curve_spot_2027(market_rates: collections.abc.Mapping, first_smoothing_point: float, maturity: float, *, instrument_kind: str, coupon_frequency: int | None = None, average_notionals: collections.abc.Mapping | None = None, ufr: float, phase_in: bool | None, approval_reference: str | None = None, volatility_adjustment: float | None = None, matching_adjustment: float | None = None, interest_stress: str | None = None, output_maturities=(), qualification_reference: str, context: solvency2._core.core.Context)
```

Build a basic/VA/MA curve once, including all requested output maturities.

Market rates are already CRA/CURA-adjusted and selected under external
DLT, FSP/RVC and missing-data/previous-trading-day qualification. Keys are
canonical positive integer years. VA is an annual decimal rate already
rounded to whole basis points; its continuous equivalent enters LLFR.
This is a numerical engine component, not an official publication.

Output unit: `rate`. Sources: `DR:article-44:1`, `DR:article-46:1a-1c`, `DR:article-46a:1-2`.

Fixed example: `rfr-curve-2027-flat`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-curve-2027-flat')
context = replace(base, **case.get('context', {}))
result = s2.rfr_curve_spot_2027(**case['kwargs'], context=context)
# Independent expected value: 0.04
```

Example input (JSON):

```json
{
  "market_rates": {
    "2": 0.04,
    "5": 0.04
  },
  "first_smoothing_point": 5,
  "maturity": 100,
  "instrument_kind": "par_swap",
  "coupon_frequency": 1,
  "ufr": 0.04,
  "phase_in": false,
  "qualification_reference": "SYN-flat-qualified-2027"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`. Additional shared validation errors can apply.

### rfr_fsp_currency_percentage_2027

```python
solvency2.rates.rfr_fsp_currency_percentage_2027(minimum_euro_share: float, *, calibration: str = 'initial', last_liquid_maturity_2027: float | None = None, rounded_preserves_fsp: bool | None = None, lower_preserving_share: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Prescribed percentage, not a market-data calibration or an FSP maturity.

Initial EUR minimum is qualified at28Jan2025 for20years. A EUR source-change
minimum is qualified at the first new-source date against the previous
calendar-year FSP. A next-lower preserving value is externally identified;
Article43a(2) does not justify inventing a market selection algorithm here.
Other-currency initial LLP is qualified at29Jan2027, not today's maturity.

Output unit: `ratio`. Sources: `DR:article-43a`.

Fixed example: `closing-rules-fsp-zero`. 13 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'closing-rules-fsp-zero')
context = replace(base, **case.get('context', {}))
result = s2.rfr_fsp_currency_percentage_2027(**case['kwargs'], context=context)
# Independent expected value: 0.015
```

Example input (JSON):

```json
{
  "minimum_euro_share": 0,
  "qualification_reference": "SYN-EUR-minimum-28Jan2025-FSP20-not-official"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_METHOD`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### rfr_matching_adjustment

```python
solvency2.rates.rfr_matching_adjustment(asset_equivalent_rate: float, liability_equivalent_rate: float, residual_fundamental_spread: float, *, qualification_reference: str, context: solvency2._core.core.Context, application: Optional[Mapping] = None, restructured_assets: Optional[Mapping] = None, subinvestment_grade_comparison: Optional[Mapping] = None)
```

Subtract effective annual rates on the SAME liability cashflows and residual FS.

The asset-equivalent rate matches their PV to eligible assigned asset value;
the liability-equivalent rate matches their PV to the basic-curve BE.
The residual FS excludes any part already included in asset cashflow
adjustment. Optional declared application/asset comparisons add controlled
eligibility and FS limits; without them these aspects stay NOT_ASSESSED.
No asset coupon substitution, automatic rating, permission or curve application.

Output unit: `rate`. Sources: `DIR:article-77c:1:a-b`, `DR:article-53:2`.

Fixed example: `future-rfr-ma-5`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-ma-5')
context = replace(base, **case.get('context', {}))
result = s2.rfr_matching_adjustment(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "asset_equivalent_rate": 0.02,
  "liability_equivalent_rate": 0.02,
  "residual_fundamental_spread": 0,
  "qualification_reference": "SYN-qualified-liability-cashflow-rates-and-residual-FS"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`. Additional shared validation errors can apply.

### rfr_equivalent_annual_rate

```python
solvency2.rates.rfr_equivalent_annual_rate(cashflows: Mapping, present_value: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Solve the unique annual rate for nonnegative externally qualified cashflows.

Times are supplied year fractions, not an implicit day-count convention.
Mixed signs need external review because uniqueness is not guaranteed.
Numerical tolerances below are implementation choices, not legal parameters.

Output unit: `rate`. Sources: `DIR:article-77c:1:a`.

Fixed example: `future-rfr-rate-negative`. 18 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-rate-negative')
context = replace(base, **case.get('context', {}))
result = s2.rfr_equivalent_annual_rate(**case['kwargs'], context=context)
# Independent expected value: -0.05
```

Example input (JSON):

```json
{
  "cashflows": {
    "a": {
      "amount": 95,
      "time_years": 1
    }
  },
  "present_value": 100,
  "qualification_reference": "SYN-liability-cashflows-and-qualified-target-PV"
}
```

### rfr_spot_discount_factor

```python
solvency2.rates.rfr_spot_discount_factor(spot_rate: float, time_years: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Convert a matching annual zero-coupon spot rate to a discount factor.

Year fractions and curve qualification are explicit external inputs; this
performs no interpolation, day-count choice or VA/MA eligibility decision.

Output unit: `ratio`. Sources: `DR:article-37:1`.

Fixed example: `rfr-discount-future-five-two`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-discount-future-five-two')
context = replace(base, **case.get('context', {}))
result = s2.rfr_spot_discount_factor(**case['kwargs'], context=context)
# Independent expected value: 0.9070294784580499
```

Example input (JSON):

```json
{
  "spot_rate": 0.05,
  "time_years": 2,
  "qualification_reference": "SYN-ANNUAL-ZERO-FUTURE"
}
```

### rfr_archived_spot_rate

```python
solvency2.rates.rfr_archived_spot_rate(series_id: str, maturity_years: float, variant: str, *, qualification_reference: str, context: solvency2._core.core.Context, market_data: dict | None = None)
```

Read one published annual zero-coupon rate, preserving cell provenance.

Archive retrieval date is a conservative knowledge bound for this exact file
revision, not an inferred original publication date. Raw currency matches are
necessary but not sufficient qualification; known anomalies remain blocked.

Output unit: `rate`. Sources: `DIR:article-77e:1:a-c`, `DIR:article-77e:3`.

Fixed example: `synthetic-market-spot-no_va`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'synthetic-market-spot-no_va')
context = replace(base, **case.get('context', {}))
result = s2.rfr_archived_spot_rate(**case['kwargs'], context=context)
# Independent expected value: 0.05
```

Example input (JSON):

```json
{
  "series_id": "EUR",
  "variant": "no_va",
  "maturity_years": 1,
  "qualification_reference": "SYNTHETIC_DEMO_ONLY"
}
```

### rfr_archived_government_spread

```python
solvency2.rates.rfr_archived_government_spread(country_id: str, maturity_years: float, table: str, *, qualification_reference: str, context: solvency2._core.core.Context, market_data: dict | None = None)
```

Read a published government LTAS/FS parameter and convert percent to decimal.

Country is the published parameter axis, including the EUR aggregate; it is
not a currency inference or automatic asset classification. Do not transfer
spot-curve currency metadata blocks to this distinct government-table axis.

Output unit: `rate`. Sources: `DIR:article-77e:1:b`, `DIR:article-77e:3`, `DR:article-54:3`.

Fixed example: `synthetic-market-government-ltas`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'synthetic-market-government-ltas')
context = replace(base, **case.get('context', {}))
result = s2.rfr_archived_government_spread(**case['kwargs'], context=context)
# Independent expected value: -0.001
```

Example input (JSON):

```json
{
  "country_id": "EUR",
  "table": "ltas",
  "maturity_years": 30,
  "qualification_reference": "SYNTHETIC_DEMO_ONLY"
}
```

### rfr_archived_corporate_pd

```python
solvency2.rates.rfr_archived_corporate_pd(series_id: str, sector: str, maturity_years: float, credit_quality_step: float, *, qualification_reference: str, context: solvency2._core.core.Context, market_data: dict | None = None)
```

Read the default probability, NOT the similarly named PD credit spread.

Output unit: `ratio`. Sources: `DIR:article-77e:1:b`, `DR:article-54:2`.

Fixed example: `synthetic-market-pd-financial`. 2 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'synthetic-market-pd-financial')
context = replace(base, **case.get('context', {}))
result = s2.rfr_archived_corporate_pd(**case['kwargs'], context=context)
# Independent expected value: 0.03
```

Example input (JSON):

```json
{
  "series_id": "EUR",
  "sector": "financial",
  "maturity_years": 30,
  "credit_quality_step": 2,
  "qualification_reference": "SYNTHETIC_DEMO_ONLY"
}
```

### rfr_archived_corporate_spread

```python
solvency2.rates.rfr_archived_corporate_spread(series_id: str, sector: str, maturity_years: float, credit_quality_step: float, table: str, *, qualification_reference: str, context: solvency2._core.core.Context, market_data: dict | None = None)
```

Read published PD/FS/downgrade spreads, converting percent to decimal rates.

Exact published tenors only: no interpolation or automatic extension beyond
year 30. Classification and applicability remain externally qualified.

Output unit: `rate`. Sources: `DIR:article-77e:1:b`, `DR:article-54:2-4`.

Fixed example: `synthetic-market-pd_spread-financial`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'synthetic-market-pd_spread-financial')
context = replace(base, **case.get('context', {}))
result = s2.rfr_archived_corporate_spread(**case['kwargs'], context=context)
# Independent expected value: 0.003
```

Example input (JSON):

```json
{
  "series_id": "EUR",
  "sector": "financial",
  "maturity_years": 30,
  "credit_quality_step": 2,
  "table": "pd_spread",
  "qualification_reference": "SYNTHETIC_DEMO_ONLY"
}
```

### rfr_archived_ltas

```python
solvency2.rates.rfr_archived_ltas(table: str, series_id: str, maturity_years: float | None = None, *, qualification_reference: str, context: solvency2._core.core.Context, market_data: dict | None = None)
```

Read supplemental LTAS cells with explicit original row identifiers.

Corporate, country-relative basic-RFR and named-index axes are different;
none is automatically assigned from context currency. The specific index
scalar has no maturity axis. Qualification remains external.

Output unit: `rate`. Sources: `DR:article-54:3`.

Fixed example: `synthetic-market-specific_ltas`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'synthetic-market-specific_ltas')
context = replace(base, **case.get('context', {}))
result = s2.rfr_archived_ltas(**case['kwargs'], context=context)
# Independent expected value: 0.006
```

Example input (JSON):

```json
{
  "table": "specific_ltas",
  "series_id": "DEMO_INDEX",
  "qualification_reference": "SYNTHETIC_DEMO_ONLY"
}
```

### rfr_matching_mortality_selected_be

```python
solvency2.rates.rfr_matching_mortality_selected_be(scenarios: Mapping, *, selected_scenario: str | None = None, qualification_reference: str, context: solvency2._core.core.Context, contract_selection: Optional[Mapping] = None)
```

Return BE from the worst BOF scenario, not the scenario with maximum BE.

Scenario valuations must share a base and currency. Equal BOF with distinct
BE values requires explicit selection among the ties; there is no legal
worst-BE tie rule invented here. Valuation and overall eligibility stay external.

Output unit: `context currency`. Sources: `DR:article-52:1`.

Fixed example: `future-rfr-ma-selection-6`. 14 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-ma-selection-6')
context = replace(base, **case.get('context', {}))
result = s2.rfr_matching_mortality_selected_be(**case['kwargs'], context=context)
# Independent expected value: -5
```

Example input (JSON):

```json
{
  "scenarios": {
    "permanent": {
      "basic_own_funds": 80,
      "best_estimate": -5
    },
    "next_twelve_months": {
      "basic_own_funds": 90,
      "best_estimate": -2
    }
  },
  "qualification_reference": "SYN-common-base-and-currency-scenario-valuations"
}
```

### rfr_matching_mortality_stress

```python
solvency2.rates.rfr_matching_mortality_stress(rate: float, scenario: str, *, rate_basis: str, selected: bool | None, qualification_reference: str, context: solvency2._core.core.Context)
```

MA qualification stress assumption, not life SCR or automatic scenario selection.

Output unit: `rate`. Sources: `DR:article-52:1-3`.

Fixed example: `future-rfr-ma-mortality-6`. 12 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-ma-mortality-6')
context = replace(base, **case.get('context', {}))
result = s2.rfr_matching_mortality_stress(**case['kwargs'], context=context)
# Independent expected value: 2.3
```

Example input (JSON):

```json
{
  "rate": 2,
  "scenario": "permanent",
  "rate_basis": "intensity",
  "selected": true,
  "qualification_reference": "SYN-DR52-contract-selection"
}
```

### rfr_default_loss_on_market_value

```python
solvency2.rates.rfr_default_loss_on_market_value(market_value: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Loss conditional on default under the fundamental-spread recovery assumption.

Output unit: `context currency`. Sources: `DR:article-54:2`.

Fixed example: `future-rfr-default-loss-2`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-default-loss-2')
context = replace(base, **case.get('context', {}))
result = s2.rfr_default_loss_on_market_value(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "market_value": 0,
  "qualification_reference": "SYN-DR54-market-value"
}
```

### rfr_matching_mortality_headroom

```python
solvency2.rates.rfr_matching_mortality_headroom(base_best_estimate: float, stressed_best_estimate: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Headroom against the 5% BE condition, using the externally BOF-selected stress.

Nonnegative means this numerical condition passes, not overall MA eligibility.
Nonpositive base BE is deliberately referred for review, not reinterpreted.

Output unit: `context currency`. Sources: `DIR:article-77b:1:f`.

Fixed example: `future-rfr-ma-headroom-1`. 8 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-rfr-ma-headroom-1')
context = replace(base, **case.get('context', {}))
result = s2.rfr_matching_mortality_headroom(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "base_best_estimate": 100,
  "stressed_best_estimate": 105,
  "qualification_reference": "SYN-DR52-BOF-worst-scenario-BE"
}
```

### rfr_reference_portfolio_spread

```python
solvency2.rates.rfr_reference_portfolio_spread(government_weight: float, corporate_weight: float, government_spread: float, corporate_spread: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Whole-portfolio weights: do not renormalize the two bond categories.

Output unit: `rate`. Sources: `DR:article-50`.

Fixed example: `rfr-refspread-4`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-refspread-4')
context = replace(base, **case.get('context', {}))
result = s2.rfr_reference_portfolio_spread(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "government_weight": 0,
  "corporate_weight": 0,
  "government_spread": 0.01,
  "corporate_spread": 0.02,
  "qualification_reference": "SYN"
}
```

### rfr_risk_corrected_spread

```python
solvency2.rates.rfr_risk_corrected_spread(spread: float, risk_correction: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Subtract an externally qualified risk correction without an output floor.

Output unit: `rate`. Sources: `DIR:article-77d:3`, `DR:article-51`.

Fixed example: `rfr-riskspread-3`. 3 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-riskspread-3')
context = replace(base, **case.get('context', {}))
result = s2.rfr_risk_corrected_spread(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "spread": 0,
  "risk_correction": 0,
  "qualification_reference": "SYN"
}
```

### rfr_volatility_adjustment

```python
solvency2.rates.rfr_volatility_adjustment(currency_spread: float, country_applicable: bool, *, country_spread: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Compute VA from risk-corrected spreads; neither authorize nor apply it.

Country uplift is added BEFORE the factor and requires both strict tests.
Official data, MA exclusion and pre-extrapolation application remain external.

Output unit: `rate`. Sources: `DIR:article-77d:3-4`.

Fixed example: `rfr-va-1`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-va-1')
context = replace(base, **case.get('context', {}))
result = s2.rfr_volatility_adjustment(**case['kwargs'], context=context)
# Independent expected value: 0.0026
```

Example input (JSON):

```json
{
  "currency_spread": 0.004,
  "country_applicable": false,
  "qualification_reference": "SYN"
}
```

### rfr_portfolio_risk_correction

```python
solvency2.rates.rfr_portfolio_risk_correction(government_weight: float, corporate_weight: float, government_risk_correction: float | None, corporate_risk_correction: float | None, *, qualification_reference: str, context: solvency2._core.core.Context, fundamental_spread_inputs: Optional[Mapping] = None)
```

Aggregate category corrections under EIOPA-BoS-24-533 section 10.3.5.

Weights refer to the whole reference portfolio, not just bonds. Category
corrections and classifications remain externally qualified inputs. This
published positive-part formula is distinct from calibrating each input.

Output unit: `rate`. Sources: `DR:article-51`.

Fixed example: `rfr-portfolio-rc-4`. 6 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-portfolio-rc-4')
context = replace(base, **case.get('context', {}))
result = s2.rfr_portfolio_risk_correction(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "government_weight": 0,
  "corporate_weight": 0,
  "government_risk_correction": 0.002,
  "corporate_risk_correction": 0.003,
  "qualification_reference": "SYN"
}
```

### rfr_default_adjusted_cashflow

```python
solvency2.rates.rfr_default_adjusted_cashflow(cashflow: float, default_probability: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

De-risk one asset cashflow under EIOPA-BoS-24-533 section 12.5.9.

The probability must match this cashflow's horizon; it is not a credit
spread. Do not apply this twice to already adjusted cashflows. This does
not project cashflows, select eligible assets or authorize matching.

Output unit: `context currency`. Sources: `DR:article-53:1`, `DR:article-54:2`.

Fixed example: `rfr-derisk-zero-pd`. 5 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-derisk-zero-pd')
context = replace(base, **case.get('context', {}))
result = s2.rfr_default_adjusted_cashflow(**case['kwargs'], context=context)
# Independent expected value: 100
```

Example input (JSON):

```json
{
  "cashflow": 100,
  "default_probability": 0,
  "qualification_reference": "SYN"
}
```

### rfr_fundamental_spread_other_than_pd

```python
solvency2.rates.rfr_fundamental_spread_other_than_pd(fundamental_spread: float, default_spread: float, downgrade_spread: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Published corporate residual-FS rule: max(CoD, FS-PD), decimal rates.

Requires matching externally qualified sector/CQS/tenor inputs. Not an
automatic residual selection for every possible matching portfolio.

Output unit: `rate`. Sources: `DR:article-53:2`.

Fixed example: `rfr-rest-fs-zero`. 4 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'rfr-rest-fs-zero')
context = replace(base, **case.get('context', {}))
result = s2.rfr_fundamental_spread_other_than_pd(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "fundamental_spread": 0,
  "default_spread": 0,
  "downgrade_spread": 0,
  "qualification_reference": "SYN"
}
```

### rfr_extrapolation_alpha_2027

```python
solvency2.rates.rfr_extrapolation_alpha_2027(*, phase_in: bool | None, approval_reference: str | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Own versioned alpha, with annual approved transition and no post-2032 trend.

Output unit: `ratio`. Sources: `DR:article-46:1b`, `DR:article-46a:1-2`.

Fixed example: `future-extrap-alpha-EUR-final`. 21 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-extrap-alpha-EUR-final')
context = replace(base, **case.get('context', {}))
result = s2.rfr_extrapolation_alpha_2027(**case['kwargs'], context=context)
# Independent expected value: 0.11
```

Example input (JSON):

```json
{
  "phase_in": false,
  "approval_reference": null,
  "qualification_reference": "SYN-qualified-UFR-LLFR-FSP-not-official"
}
```

Reference-tested failure codes: `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### rfr_extrapolated_forward_2027

```python
solvency2.rates.rfr_extrapolated_forward_2027(ufr: float, last_liquid_forward: float, time_after_fsp: float, *, phase_in: bool | None, approval_reference: str | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Return the continuous forward from annual-discrete UFR and continuous LLFR.

LLFR determination, UFR publication and VA treatment are external. Alpha
comes from the profile, not an untracked arbitrary caller coefficient.

Output unit: `rate`. Sources: `DR:article-46:1b`, `DR:article-46a:1-2`.

Fixed example: `future-extrap-forward-zero`. 9 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-extrap-forward-zero')
context = replace(base, **case.get('context', {}))
result = s2.rfr_extrapolated_forward_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "ufr": 0,
  "last_liquid_forward": 0,
  "time_after_fsp": 10,
  "phase_in": false,
  "qualification_reference": "SYN-qualified-UFR-LLFR-FSP-not-official"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### rfr_extrapolated_spot_2027

```python
solvency2.rates.rfr_extrapolated_spot_2027(fsp_years: float, spot_at_fsp: float, time_after_fsp: float, extrapolated_forward: float, *, qualification_reference: str, context: solvency2._core.core.Context)
```

Convert the FSP spot and a matching continuous forward to an annual spot.

Scaled time weights avoid overflow. This API is strictly beyond FSP; it
neither selects FSP nor adds VA/MA automatically.

Output unit: `rate`. Sources: `DR:article-46:1a`.

Fixed example: `future-extrap-spot-zero`. 7 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-extrap-spot-zero')
context = replace(base, **case.get('context', {}))
result = s2.rfr_extrapolated_spot_2027(**case['kwargs'], context=context)
# Independent expected value: 0
```

Example input (JSON):

```json
{
  "fsp_years": 20,
  "spot_at_fsp": 0,
  "time_after_fsp": 10,
  "extrapolated_forward": 0,
  "qualification_reference": "SYN-qualified-UFR-LLFR-FSP-not-official"
}
```

Reference-tested failure codes: `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

### rfr_last_liquid_forward_2027

```python
solvency2.rates.rfr_last_liquid_forward_2027(fsp_forward: float, later_forwards: collections.abc.Mapping, *, liquid_swaps_beyond_fsp: bool | None, fsp_average_notional: float | None = None, apply_volatility_adjustment: bool | None, volatility_adjustment: float | None = None, qualification_reference: str, context: solvency2._core.core.Context)
```

Aggregate externally qualified continuous forwards using swap notionals.

Component a is the one-year forward immediately preceding FSP in the
SRC-0211 construction; components b run
from FSP to later liquid maturities. Only a receives the explicit VA.
Market selection, forward derivation and VA qualification are external.
Here volatility_adjustment is a CONTINUOUS forward increment; the
integrated rfr_curve_spot_2027 converts annual VA using log1p first.

Output unit: `rate`. Sources: `DR:article-46:1c`.

Fixed example: `future-llfr-fallback`. 22 bundled cases for this function.

```python
from dataclasses import replace
import solvency2 as s2
base = s2.Context('2025-01-17', '2026-09-23', 'EUR', 'EU-S2-DOCUMENTS-2024-2025-v0.1')
case = next(c for c in s2.reference_cases()['cases']
            if c['id'] == 'future-llfr-fallback')
context = replace(base, **case.get('context', {}))
result = s2.rfr_last_liquid_forward_2027(**case['kwargs'], context=context)
# Independent expected value: 0.02
```

Example input (JSON):

```json
{
  "fsp_forward": 0.02,
  "later_forwards": {},
  "liquid_swaps_beyond_fsp": false,
  "fsp_average_notional": null,
  "apply_volatility_adjustment": false,
  "qualification_reference": "SYN-external-qualified-forwards-and-volumes"
}
```

Reference-tested failure codes: `INVALID_INPUT`, `MISSING_INPUT`, `REVIEW_REQUIRED`, `UNSUPPORTED_RULESET`. Additional shared validation errors can apply.

## solvency2.data

### DiscountCurve

```python
solvency2.data.DiscountCurve(curve_id: 'str', as_of: 'str', currency: 'str', curve_kind: 'str', source_reference: 'str', points: 'tuple[tuple[str, float], ...]') -> None
```

Immutable external factors keyed by payment date, with content provenance.

Factors above one are valid. No curve is considered an official or approved
curve merely because its format is valid. Values are never interpolated.

Usage and return contract: [guide](DATA.md), [shared types and limitations](LIMITATIONS.md).

### load_discount_curve_json

```python
solvency2.data.load_discount_curve_json(path: 'str | Path') -> 'DiscountCurve'
```

Load a local UTF-8 version-1 curve; reject duplicate JSON keys.

Usage and return contract: [guide](DATA.md), [shared types and limitations](LIMITATIONS.md).

### load_discount_curve_csv

```python
solvency2.data.load_discount_curve_csv(path: 'str | Path', *, curve_id: 'str', as_of: 'str', currency: 'str', curve_kind: 'str', source_reference: 'str') -> 'DiscountCurve'
```

Load date,discount_factor CSV; metadata must be supplied explicitly.

UTF-8, comma separator, decimal point, no unit or locale guessing. Source
paths are not added to result provenance; use a suitable source reference.

Usage and return contract: [guide](DATA.md), [shared types and limitations](LIMITATIONS.md).

### best_estimate_with_curve

```python
solvency2.data.best_estimate_with_curve(cashflows: 'Mapping[str, Mapping]', *, curve: 'DiscountCurve', runoff_complete: 'bool', cashflow_reference: 'str', context: 'Context') -> 'Result'
```

Bind external factors to expected cashflows and call the existing BE formula.

Rows contain expected_inflows and expected_outflows in the context currency.
No projection, curve qualification, VA/MA addition or currency conversion.

Usage and return contract: [guide](DATA.md), [shared types and limitations](LIMITATIONS.md).

### discount_curve_from_spot_rates

```python
solvency2.data.discount_curve_from_spot_rates(points: 'Mapping[str, Mapping]', *, curve_id: 'str', curve_kind: 'str', source_reference: 'str', time_basis_reference: 'str', context: 'Context') -> 'DiscountCurve'
```

Convert annual-effective decimal spot rates using the existing RFR formula.

Each payment date maps to annual_effective_rate and time_years. The caller
supplies year fractions and their convention: no calendar/day-count guess,
percent conversion, interpolation, or extrapolation is performed. The full
raw input and convention are fingerprinted in the source reference.

Usage and return contract: [guide](DATA.md), [shared types and limitations](LIMITATIONS.md).

## solvency2.scenarios

### numeric_overrides_from_dict

```python
solvency2.scenarios.numeric_overrides_from_dict(payload: Mapping) -> tuple[solvency2._core.core.NumericOverride, ...]
```

Parse schema_version=1 and an overrides list; apply with Context.overrides.

Resource names and existing numeric paths are validated by the selected
Context when used. Parsing is not regulatory qualification. Empty batches
are allowed and mean the original, unmodified parameter set.

Usage and return contract: [guide](PARAMETERS.md), [shared types and limitations](LIMITATIONS.md).

### load_numeric_overrides_json

```python
solvency2.scenarios.load_numeric_overrides_json(path: str | pathlib.Path) -> tuple[solvency2._core.core.NumericOverride, ...]
```

Load an explicit local UTF-8 scenario file; never edit installed data.

Usage and return contract: [guide](PARAMETERS.md), [shared types and limitations](LIMITATIONS.md).

## solvency2.catalogue

### api_catalogue

```python
solvency2.catalogue.api_catalogue() -> dict
```

Return fresh function names, domain paths, signatures and contracts.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reference_datasets

```python
solvency2.catalogue.reference_datasets() -> list[str]
```

Names of additional synthetic reporting datasets (no filesystem paths).

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### reference_dataset

```python
solvency2.catalogue.reference_dataset(name: str) -> dict
```

Read an explicitly named dataset, independent of the working directory.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).

### documentation

```python
solvency2.catalogue.documentation(topic: str = 'README') -> str
```

Return bundled English Markdown without needing a browser or source tree.

Topics: README, API, DATA, PARAMETERS, RECIPES, LIMITATIONS, DEVELOPMENT,
ACCEPTANCE, DISCLAIMER, SECURITY, THIRD_PARTY_NOTICES, CHANGELOG.
Names are case-sensitive.

Usage and return contract: [guide](RECIPES.md), [shared types and limitations](LIMITATIONS.md).
