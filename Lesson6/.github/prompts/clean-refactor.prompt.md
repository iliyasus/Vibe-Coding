---
mode: edit
description: Refactor the selected module to repository standards while preserving public function compatibility.
---

Refactor the selected module to follow `.github/copilot-instructions.md`.
Preserve the names, parameters, and observable behavior of its public functions
unless a reported defect requires a behavior correction. Keep functions focused,
validate inputs at boundaries, and use project-specific exceptions rather
than `print()`. Run `ruff check .` and `pytest`, and report any failures.
