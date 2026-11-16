---
mode: edit
description: Add focused pytest unit tests for boundary cases and invalid inputs found during review.
---

Write focused unit tests for the selected module using pytest. Use
`@pytest.mark.parametrize` for related boundary cases and malformed inputs.
Cover every issue reported by `/analyze-legacy`, preserve the public API, and
do not change production code. Run the relevant tests and report the results.
