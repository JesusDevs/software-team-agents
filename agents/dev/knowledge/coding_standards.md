# Coding Standards & Best Practices

## Python Standards
- **Style:** PEP8 + Black formatter (line length 88)
- **Type hints:** Required on all public functions
- **Docstrings:** Google style for public functions
- **Imports:** isort, group: stdlib → third-party → local
- **Naming:** snake_case for vars/functions, PascalCase for classes

## Project Structure (Python)
```
src/
├── api/
│   ├── routes/          # One file per resource
│   └── middleware/
├── core/
│   ├── config.py        # Settings with Pydantic
│   └── security.py
├── models/              # Database models
├── schemas/             # Pydantic schemas (request/response)
├── services/            # Business logic
├── repositories/        # Database queries
└── utils/
tests/
├── unit/
├── integration/
└── conftest.py
```

## Function Contract Template
```python
def process_payment(
    user_id: int,
    amount: Decimal,
    currency: str = "USD",
) -> PaymentResult:
    """Process a payment for a user.

    Args:
        user_id: The ID of the user making the payment.
        amount: The payment amount (must be positive).
        currency: ISO 4217 currency code.

    Returns:
        PaymentResult with transaction_id and status.

    Raises:
        InsufficientFundsError: If balance is too low.
        PaymentProviderError: If external provider fails.
    """
```

## Testing Strategy
- **Unit tests:** Pure functions, no I/O, fast (<10ms each)
- **Integration tests:** Database, external services, use fixtures
- **E2E tests:** Critical user paths only (happy path + main errors)
- **Coverage target:** 80% overall, 100% for business logic

## Git Conventions
- Branches: `feature/US-XXX-short-description`
- Commits: `feat: add OAuth login` / `fix: handle empty state` / `chore: update deps`
- PRs: max 400 lines changed, linked to Linear/Jira ticket
- Reviews: min 2 approvals, all CI checks passing
