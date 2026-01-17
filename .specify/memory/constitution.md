<!--
Sync Impact Report - Constitution v1.0.0

Version Change: Initial version → 1.0.0
Rationale: Initial constitution creation for mybudget project

Core Principles Established:
1. Test-First Development (TDD) - MANDATORY red-green-refactor cycle
2. Comprehensive Unit Testing - 100% coverage goal
3. Type Safety - Full type hints with mypy strict mode
4. Code Quality - Automated linting and formatting
5. Simplicity First - YAGNI and minimal viable implementation

Templates Status:
- ✅ plan-template.md - Constitution Check section aligns with principles
- ✅ spec-template.md - User scenarios support testable requirements
- ✅ tasks-template.md - Test-first workflow matches TDD principle

Follow-up Actions:
- None - all templates align with constitution requirements

Date: 2026-01-16
-->

# MyBudget Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

**TDD MUST be strictly followed**:
- Write failing tests BEFORE any implementation code
- Follow Red-Green-Refactor cycle without exception
- Tests define the contract and expected behavior
- Implementation emerges from making tests pass
- Refactoring happens only when tests are green

**Rationale**: Test-first development ensures code is inherently testable, requirements are clear before coding begins, and prevents over-engineering. The discipline of watching tests fail first proves they actually test something meaningful.

### II. Comprehensive Unit Testing

**Every module, class, and function MUST have unit tests**:
- Target: 100% code coverage (measure with pytest-cov)
- Unit tests MUST be isolated (no database, network, or filesystem dependencies)
- Use mocks, fakes, and stubs for external dependencies
- Each test MUST verify one specific behavior
- Tests MUST be fast (<10ms per unit test)

**Rationale**: Comprehensive unit testing creates a safety net for refactoring, documents expected behavior, and catches regressions early. Fast, isolated tests enable rapid feedback during development.

### III. Type Safety

**Python type hints MUST be used throughout the codebase**:
- All function signatures MUST include type annotations
- All class attributes MUST be typed
- Use `mypy` in strict mode for type checking
- Generic types MUST be properly parameterized (List[str], Dict[str, int])
- Type ignore comments require justification

**Rationale**: Type hints catch bugs at development time, serve as inline documentation, enable better IDE support, and make refactoring safer.

### IV. Code Quality Standards

**Automated quality gates MUST pass before merge**:
- `ruff` for linting (no warnings allowed)
- `black` for formatting (line length: 100)
- `mypy` for type checking (strict mode)
- `pytest` for test execution (all tests must pass)
- Pre-commit hooks enforce these checks locally

**Rationale**: Consistent code quality standards reduce cognitive load, prevent bugs, and make code reviews focus on logic rather than style.

### V. Simplicity First

**YAGNI (You Aren't Gonna Need It) principle is mandatory**:
- Implement only what is specified, no extra features
- No premature optimization or abstraction
- No "just in case" code or configuration
- Prefer explicit over clever
- Delete unused code immediately

**Rationale**: Simplicity reduces maintenance burden, minimizes bugs, and keeps the codebase understandable. Future requirements should drive future changes, not speculation.

## Development Workflow

### Test-Driven Development Cycle

**Every feature follows this exact workflow**:

1. **Red**: Write a failing test that defines desired behavior
   - Test MUST fail for the right reason
   - Test MUST be as simple as possible
   - Verify the test actually fails before proceeding

2. **Green**: Write minimal code to make the test pass
   - No extra functionality
   - Simplest possible implementation
   - Test MUST pass

3. **Refactor**: Improve code quality while keeping tests green
   - Eliminate duplication
   - Improve naming
   - Extract reusable components
   - Tests MUST remain green throughout

4. **Commit**: Commit after each complete cycle
   - Each commit represents working, tested code
   - Commit message describes behavior added

### Testing Hierarchy

**Tests MUST follow this organization**:

```
tests/
├── unit/           # Fast, isolated tests (MOST tests go here)
├── integration/    # Tests involving multiple components
└── contract/       # API/interface contract tests
```

**Coverage Requirements**:
- Unit tests: 100% of business logic
- Integration tests: Critical user journeys
- Contract tests: All public APIs and interfaces

### Code Review Requirements

**All pull requests MUST**:
- Include tests that fail without the implementation
- Pass all CI checks (linting, type checking, tests)
- Maintain or improve code coverage
- Include clear commit messages following conventional commits
- Have at least one approved review

## Python Project Standards

### Project Structure

**Standard Python project layout**:

```
src/mybudget/       # Source code
    __init__.py
    models/         # Domain models
    services/       # Business logic
    cli/            # Command-line interface
    lib/            # Shared utilities

tests/              # Test code mirrors src structure
    unit/
        test_models/
        test_services/
    integration/
    contract/

pyproject.toml      # Project configuration and dependencies
README.md           # Project documentation
.gitignore          # Git ignore patterns
```

### Dependency Management

**Dependencies MUST be managed carefully**:
- Use `pyproject.toml` for dependency specification
- Pin exact versions for reproducibility
- Minimize dependencies (each dependency is a liability)
- All dependencies MUST be justified
- Development dependencies separate from runtime dependencies

### Python Version

**Target**: Python 3.11 or later
- Use modern Python features (match statements, type union syntax)
- No backwards compatibility with Python 3.10 or earlier required

## Quality Gates

### Pre-Commit Checks (Local)

MUST pass before commit:
- `ruff check .` - Linting
- `black --check .` - Formatting
- `mypy src/` - Type checking
- `pytest tests/` - All tests pass

### CI/CD Pipeline (Required)

MUST pass before merge:
- All pre-commit checks
- Code coverage ≥ 90% (target 100%)
- No security vulnerabilities (safety check)
- Documentation builds successfully

### Manual Review Checklist

Reviewers MUST verify:
- Tests were written BEFORE implementation
- Tests fail without the implementation
- Code follows YAGNI principle (no speculative features)
- Type hints are complete and accurate
- Edge cases are tested
- Error handling is appropriate

## Governance

### Amendment Process

**This constitution can be amended when**:
- Team consensus is reached (all active contributors agree)
- Amendment is documented in git history
- All templates and documentation are updated to reflect changes
- Version is bumped according to semantic versioning

### Compliance

**Constitution compliance is MANDATORY**:
- All code reviews MUST verify compliance
- Any violation MUST be justified and documented
- Repeated violations indicate need for constitution amendment or team discussion
- PRs that violate principles without justification will be rejected

### Version Control

**Constitution versioning follows semantic versioning**:
- MAJOR: Backward incompatible changes (removing or fundamentally changing principles)
- MINOR: New principles or sections added
- PATCH: Clarifications, typo fixes, non-semantic changes

### Living Document

This constitution is a living document that evolves with the project. When practices consistently conflict with principles, update the constitution rather than ignore violations.

**Version**: 1.0.0 | **Ratified**: 2026-01-16 | **Last Amended**: 2026-01-16
