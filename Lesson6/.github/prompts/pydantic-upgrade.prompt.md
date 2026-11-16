---
mode: agent
description: Migrate the selected order module to Pydantic v2 using Context7, Ruff, and pytest.
---

Refactor the selected order-processing module autonomously:

1. Use the Context7 MCP tools to resolve `/pydantic/pydantic` and load current
   documentation for `BaseModel`, `Field`, `field_validator`, `ConfigDict`,
   `model_validate`, and `model_dump`/`model_dump_json`. Do not claim to have
   consulted Context7 if its tools are unavailable; report that limitation.
2. Replace untyped order dictionaries and manual checks with typed Pydantic v2
   models. Validate that the order amount is finite and greater than zero, the
   email is valid, item quantities are positive integers, and status is one of
   the supported values. Support ORM-style objects through `ConfigDict` with
   `from_attributes=True`, and retain dictionary and JSON serialization.
3. Update and add pytest cases for valid input, invalid fields, boundary values,
   ORM-style attribute input, and serialization. Keep existing public functions
   compatible where possible.
4. Do not use Pydantic v1 APIs such as `@validator`, nested `class Config`,
   `orm_mode`, `.dict()`, or `.json()`.
5. Run `ruff check --fix .`, then `ruff check .` and `pytest`. Fix failures
   caused by the migration and rerun the checks. Report commands and results.
