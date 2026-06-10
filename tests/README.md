# Tests

Canonical automated checks for the repository.

## Intended Internal Shape

- `unit/` - fast backend and domain tests
- `integration/` - tests that cross service boundaries
- `e2e/` - full journey coverage for the web experience

Keep the highest-value scenarios here so each phase can prove that the slice really works. The old `backend/tests/` split has been retired so there is one obvious test tree.
