# Technology Research: MyBudget MVP

**Date**: 2026-01-16
**Feature**: Spending Targets MVP
**Purpose**: Document technology decisions for implementation phase

## Summary

This document captures research findings and technology decisions for the MyBudget MVP. All decisions prioritize:
1. Security for financial data
2. Simplicity (YAGNI principle from constitution)
3. Test-driven development support
4. Fast time-to-market for MVP validation

---

## Frontend Framework

**Decision**: **React 19 with TypeScript**

**Rationale**:

1. **Best-in-class form handling**: React Hook Form provides optimal performance for the extensive financial input requirements (transaction inbox, budget assignments, target modals). Uses uncontrolled components to minimize re-renders - critical when users are rapidly entering transaction data.

2. **Enterprise component ecosystem**: Blueprint UI library is purpose-built for financial/data-dense interfaces. Provides tables, data grids, and charts optimized for budget month views with 20-50 categories. PrimeReact and Ant Design offer additional enterprise components if needed.

3. **Mature testing ecosystem**: React Testing Library + Vitest provides first-class TypeScript support for achieving the constitution's 100% coverage goal. Largest community means abundant testing patterns for financial calculations and user workflows.

**Alternatives Considered**:

- **Vue 3**: Easier learning curve, excellent TypeScript support with Vuelidate. Smaller component ecosystem for financial UIs (15.4% adoption vs React's 39.5%). Chose React for larger talent pool and specialized financial components.

- **Svelte**: Best performance (3x faster, 87KB vs React's 487KB), cleanest syntax. Smallest component ecosystem and 6.5% adoption creates hiring risk. Testing ecosystem still maturing. Too risky for solo developer needing battle-tested solutions.

**Trade-offs**:

*Gaining*:
- 50M weekly npm downloads worth of ecosystem packages
- Blueprint UI library for financial interfaces
- Largest talent pool (39.5% adoption)
- Most tested patterns for financial applications

*Losing*:
- ~400KB larger bundle vs Vue, 5x larger vs Svelte
- Steeper learning curve (JSX, hooks)
- More boilerplate than Vue/Svelte

**Technology Stack**:
```
- Framework: React 19
- Language: TypeScript 5.8
- Build Tool: Vite
- Forms: React Hook Form
- UI Library: Blueprint or shadcn/ui (Tailwind-based)
- Testing: Vitest + React Testing Library + Playwright (E2E)
- State: React Context API (defer Redux until multi-user)
```

---

## Bank Sync Integration

**Decision**: **Build Mock/CSV Import for MVP, defer real integration to Phase 2**

**Rationale**:

1. **GoCardless discontinued**: The previously free bank sync provider (Nordigen) stopped accepting new users in July 2025, eliminating the bootstrapped startup option.

2. **Cost-prohibitive alternatives**: TrueLayer, Tink, and Plaid all require enterprise sales contact with estimated €0.50+ per user/month. This creates €500/month cost at just 1,000 users before revenue validation.

3. **Validate core value first**: Spending targets, reconciliation, and category management provide budgeting value independent of bank sync. CSV import allows real user data without API costs.

**MVP Approach**:

### Phase 1 (Weeks 1-4): Mock + CSV Import
- Build CSV import with drag-drop uploader
- Support standard bank export formats
- Create mock "Connect Bank" UI flow
- Route imports through same inbox → approval → categorization workflow

### Phase 2 (Month 2-3): Real Integration Decision
- Validate with 50-100 users using CSV
- Survey which banks users need (ING, KBC, BNP Paribas)
- Request pricing quotes from Enable Banking and Salt Edge
- Decision point: If users pay €5-10/month subscription → can afford API costs

### Phase 3 (Month 3-4): Integration if Viable
- Implement OAuth flow for selected provider
- Build real sync adapter maintaining same inbox workflow
- Gradual rollout with CSV as fallback

**Alternatives Considered**:

- **TrueLayer**: €0.50+ per user/month, strong European coverage (3,000+ banks), PSD2 compliant. Too expensive for unproven MVP.
- **Tink**: Fixed €0.50/user/month (€500/month at 1,000 users), excellent coverage (6,000+ banks). Linear scaling costs problematic for bootstrapped startup.
- **Plaid**: US-focused, limited European coverage, custom enterprise pricing. Not ideal for EU-first application.
- **Enable Banking / Salt Edge**: Potential alternatives with less pricing transparency. Worth exploring in Phase 2 with user data.

**Cost Estimates**:

*MVP Phase (Months 1-3)*:
- API fees: €0 (mock/CSV only)
- Infrastructure: €20-50/month
- Total: €60-150 for validation

*Post-Launch with Real Integration (at 1,000 users)*:
- API cost: €300-500/month (assuming volume discount to €0.30-0.50/user)
- Infrastructure: €150-300/month
- Total: €450-800/month (€0.45-0.80 per user)
- Revenue needed: €2-3/month per user minimum

---

## Authentication Strategy

**Decision**: **Session-based authentication with HTTP-only cookies**

**Rationale**:

1. **XSS protection**: HTTP-only cookies cannot be accessed by JavaScript, protecting against XSS attacks - critical for financial data security.

2. **Simplicity for single-user MVP**: No need for stateless JWT complexity in a single-user application. Aligns with constitution's YAGNI principle.

3. **PSD2 compliance path**: Easier to implement Strong Customer Authentication (SCA) / MFA on top of secure sessions.

4. **FastAPI native support**: fastapi-sessions provides maintained, production-ready session management with PostgreSQL backend support.

**Alternatives Considered**:

- **JWT in localStorage**: Stateless, good for distributed systems. REJECTED: Vulnerable to XSS (JavaScript can steal tokens from localStorage). Unacceptable for financial data.

- **JWT in HTTP-only cookies**: Protected from XSS, still stateless. REJECTED: Adds complexity (CSRF protection + token blacklist) without benefit for single-user MVP. Overkill.

- **OAuth2/OIDC (Google, GitHub)**: Strong authentication, no password management. REJECTED: Creates dependency on external services, privacy concerns (users linking bank data to Google account), violation of simplicity principle.

**Security Implementation**:

### Core Security Layers:
1. **HTTP-only cookies**: XSS protection (session tokens inaccessible to JavaScript)
2. **CSRF protection**: fastapi-csrf-protect library (Double Submit Cookie pattern)
3. **SameSite=Lax**: Baseline CSRF protection from browser
4. **Argon2id password hashing**: pwdlib library (OWASP 2026 standard)
5. **HTTPS enforcement**: All session cookies transmitted securely
6. **30-minute session timeout**: Standard for financial applications
7. **8-hour absolute timeout**: Force re-authentication

### Technical Stack:
```python
# Libraries
- fastapi-sessions: Session management with SQLite/PostgreSQL backend
- fastapi-csrf-protect: CSRF token validation
- pwdlib: Argon2id password hashing

# Configuration
- Session storage: PostgreSQL (persistent, queryable)
- Session ID: secrets.token_urlsafe(32) (cryptographically secure)
- Cookie params: HttpOnly=True, Secure=True, SameSite=Lax
- Password hash: Argon2id (memory_cost=19456, time_cost=2, parallelism=1)
```

### Future Enhancements (post-MVP):
- Multi-factor authentication (TOTP, WebAuthn/passkeys) for PSD2 SCA
- Session management UI (view active sessions, logout from all devices)
- OAuth2 for bank connections (separate from user auth)

**Why Session-based for MyBudget**:
- ✅ Appropriate security for financial data
- ✅ Simple to implement and test (TDD-friendly)
- ✅ No over-engineering (matches YAGNI principle)
- ✅ Future-proof (can add MFA without architectural changes)
- ✅ FastAPI ecosystem best practice

---

## Additional Technology Decisions

### Decimal Precision

**Decision**: Python's built-in `decimal.Decimal`

**Rationale**: Standard library solution for precise financial calculations. No external dependencies. Industry standard for avoiding floating-point errors in currency.

**Usage**: All monetary amounts stored as DECIMAL(19, 4) in PostgreSQL, handled as decimal.Decimal in Python.

---

### Database Migrations

**Decision**: Alembic

**Rationale**: De facto standard for SQLAlchemy. Version-controlled schema changes essential for TDD workflow (tests need consistent database state).

**Integration**: Auto-generate migrations from SQLAlchemy model changes, review before applying.

---

### API Documentation

**Decision**: FastAPI's built-in OpenAPI/Swagger

**Rationale**: Auto-generated from code (no manual maintenance), interactive testing UI, supports contract testing, aligns with constitution's testing requirements.

**Benefits**: Pydantic schemas become OpenAPI specs automatically, enabling contract tests to validate API behavior.

---

## Implementation Priorities

### Week 1-2: Foundation
1. Project setup (Vite + React + TypeScript)
2. FastAPI backend with SQLAlchemy models
3. PostgreSQL database with Alembic migrations
4. Session-based auth implementation
5. Testing infrastructure (pytest + Vitest)

### Week 3-4: Core Features
1. CSV import for transactions
2. Transaction inbox UI (approve/categorize)
3. Category management (groups, categories, assignments)
4. Budget month view (basic)

### Month 2: Spending Targets
1. Target CRUD (Monthly Needed, Target Balance, Target by Date)
2. Underfunded calculations (FR-028)
3. Funding actions (Fund Underfunded, Fund All)
4. Month rollover behavior

### Month 3: Polish & Decision
1. Reconciliation workflow
2. Categorization rules
3. Performance optimization
4. User testing with CSV import
5. **Decision point**: Evaluate bank sync provider based on user feedback

---

## Risk Mitigation

### Frontend Bundle Size
**Risk**: React's 487KB bundle may be large for some users
**Mitigation**: Code-splitting, lazy loading, compression. Monitor bundle size in CI. Consider Svelte migration only if production metrics show user impact.

### Bank Sync Dependency
**Risk**: May never afford real bank sync if API costs remain high
**Mitigation**: CSV import remains viable product (market as "bank-independent"). Freemium model (free CSV, paid sync) or self-hosted option for technical users.

### Authentication Complexity
**Risk**: Future mobile app may need JWT-based auth
**Mitigation**: Session-based auth works with mobile apps (store session cookie in Keychain/KeyStore). Can add JWT for mobile later without changing web auth.

### Solo Developer Knowledge Gaps
**Risk**: React ecosystem has learning curve
**Mitigation**: Excellent documentation, large community, abundant Stack Overflow answers. Blueprint UI reduces custom component development.

---

## References

All research findings derived from comprehensive web searches conducted 2026-01-16. Key sources included:
- Official framework documentation (React, Vue, Svelte)
- Open Banking API provider websites (TrueLayer, Tink, Plaid, Enable Banking, Salt Edge)
- FastAPI security documentation and community libraries
- OWASP password hashing guidelines (2026)
- PSD2 compliance requirements

Detailed source URLs available in research agent outputs (agent IDs: a805ff9, afcc9f0, acbe907).

---

---

## Clarification Session Additions (2026-01-18)

The following decisions were made during the `/speckit.clarify` session:

### Password Storage

**Decision**: Argon2/bcrypt hashing only (stateless, standard)

**Rationale**: Modern password hashing is a security baseline. Argon2id already configured in pwdlib dependency.

### Bank Sync Failure Handling

**Decision**: Show sync status indicator + manual retry button on failure

**Rationale**: Users need visibility into sync status without automatic retries that might mask persistent issues.

**Implementation**: Added FR-010a and FR-010b to spec for sync status indicator and manual retry.

### Observability

**Decision**: Full observability - logging, metrics, health checks + Prometheus endpoint

**Rationale**: Production-ready monitoring from day one. Essential for debugging financial data issues.

**Implementation**:
- FR-OBS-001: Structured logging for errors and key user actions
- FR-OBS-002: Prometheus-compatible metrics endpoint
- FR-OBS-003: Health check endpoint
- FR-OBS-004: Metrics for latency, error rates, sessions, transaction counts

**Libraries**:
- prometheus-fastapi-instrumentator for automatic metrics
- structlog for JSON logging

### Availability/Uptime

**Decision**: Best effort (no explicit SLA, standard hosting)

**Rationale**: MVP phase doesn't require SLA commitments. Focus on feature validation first.

---

**Status**: Phase 0 research complete. Ready to proceed to Phase 1: Data Model & API Contracts.
