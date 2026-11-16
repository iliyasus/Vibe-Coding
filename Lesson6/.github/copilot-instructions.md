# Repository instructions

- Target Python 3.12 or newer.
- Add type annotations to every function argument and return value.
- Do not use `print()` in business logic; use logging or project-specific exceptions.
- Use Pydantic v2 APIs only; do not use deprecated v1 validators, `Config`, or serialization methods.
- Keep functions at 25 lines or fewer by decomposing longer operations into focused helpers.
- After making changes, run `ruff check .` and `pytest`.
