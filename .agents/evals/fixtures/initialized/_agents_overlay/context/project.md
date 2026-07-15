<!-- code-agent-template:managed -->
# Project Context

**Status:** Initialized
**Last verified:** 2026-07-15
**Repository checkpoint:** Synthetic evaluation fixture

## Product summary

A minimal Python arithmetic module used only for isolated evaluation.

## Technology stack

- Python 3.10 or newer
- Standard library only

## Repository map

- `app.py`: arithmetic behavior
- `tests/test_app.py`: unit coverage

## Evidence provenance

- `README.md`, `app.py`, and `tests/test_app.py` inspected in this fixture.

## Verified commands

- `python -m unittest discover -s tests -p "test_*.py"`

## Superseded facts

- None.

## Unknowns

- No packaging or deployment contract is present.
