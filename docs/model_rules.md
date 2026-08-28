# Non-negotiable Model Rules

1. **Reality is not observation.** Agent policies receive only `Observation` values produced by an
   observation system. They never read environment arrays.
2. **Observation is not belief.** Decision policies consume `BeliefState`, even when the baseline
   belief is a direct copy.
3. **Intention is not action.** Agents produce side-effect-free intents. Institutional and physical
   resolution occur centrally.
4. **Stocks remain distinct.** Resource, energy, action capacity, holdings, debt, and belief cannot be
   overloaded into a generic `wealth` variable.
5. **Process order is scientific content.** The documented scheduler and executable stage trace must
   match and are protected by regression tests.
6. **One run has one random origin.** Scientific code receives the model-owned generator explicitly;
   global random calls are prohibited.
7. **Competition is explicit.** The baseline resolves contested harvest simultaneously and
   proportionally. Activation order is not an implicit institution.
8. **Mortality does not erase evidence.** Dead agents leave activation but stay in cohort records and
   outcome calculations.
9. **Configuration is part of provenance.** Every scientific parameter is validated and serialisable.
10. **A mechanism needs evidence.** Before entering executable source, each non-trivial scientific
    mechanism needs a literature note, a relevance statement, and a testable implementation target.

