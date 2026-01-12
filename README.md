# D&D Monster Manager

A **portfolio / bootcamp project** for managing *Dungeons & Dragons* monsters using a
**server-side rendered (SSR)** FastAPI application.

The app allows authenticated users to create, view, and manage monsters with a
structured **D&D 5e–style stat block**, including traits, actions, legendary actions,
lair actions, and more.

---

## Tech Stack

- **Backend:** FastAPI (Python 3.12)
- **Frontend:** Server-Side Rendering (Jinja2 templates)
- **Database:** PostgreSQL (local)
- **ORM:** SQLAlchemy (async)
- **Migrations:** Alembic
- **Authentication:** Session-based auth with role-based access control
- **Styling:** Tailwind CSS (via CDN)

---

## Project Goals

- Demonstrate clean backend architecture
- Strong validation with Pydantic schemas
- SSR forms with full error preservation
- Role-based permissions (ADMIN / DM / PLAYER)
- Portfolio-quality structure and documentation

---

## Architecture Notes

- Server-side rendering (SSR) is used intentionally to keep the stack simple and backend-focused.
- All business rules and authorization are enforced exclusively on the backend.
- Templates are presentation-only and contain no domain logic.
- Validation happens at the schema and service layers, not in templates.

---

## Features

### Monster Creation (SSR)

- Full D&D-style stat block
- Strict **all-or-nothing validation**
- Dynamic repeatable fields:
  - Movement
  - Senses
  - Languages
  - Damage immunities / resistances / vulnerabilities
  - Condition immunities
- Structured blocks:
  - Traits
  - Actions
  - Reactions
  - Legendary Actions
- Narrative sections:
  - Lair Actions
  - Regional Effects
  - Backstory

### Monster Detail Page

- Clean stat block presentation
- Sections rendered only when data exists
- Official vs community submission indicator

---

## Roles

### ADMIN
- Create, edit, approve, and delete monsters

### DM
- Submit community monsters (pending approval)

### PLAYER
- Read-only access (official monsters only)

---

## Environment Setup

### Requirements

- Python 3.12
- PostgreSQL running locally on `localhost:5432`
- Virtual environment recommended

---

### Create and Activate Virtual Environment

```bash

python -m venv .venv

```
 
### Linux / macOS

```bash

source .venv/bin/activate

```

### Windows (PowerShell)

```bash

.venv\Scripts\Activate.ps1

```

```bash

pip install -r requirements.txt

```

### Environment Variables

Create a .env file in the project root:

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/monster_manager
SECRET_KEY=your-secret-key

### Database Setup

Apply migrations:

```bash

alembic upgrade head

```

### Demo Users

Run the demo seed script (PowerShell):

```powershell

$env:ALLOW_SEED_DEMO="1"
python -m backend.scripts.seed_demo

```

### Demo Accounts
Email					Role				Password

admin@example.com		ADMIN				demo-password-123
dm@example.com			DM					demo-password-123
player@example.com		PLAYER				demo-password-123

To reset passwords on re-run:

```powershell

$env:RESET_DEMO_PASSWORDS="1"

```

### Running the App

```bash

python -m uvicorn backend.app:app --reload

```

⚠️ Windows Note

--reload may leave a process holding port 8000.

If that happens (PowerShell):

```powershell

netstat -ano | findstr :8000
taskkill /PID <PID> /F

```

### Testing

This project uses integration-level HTTP tests that exercise full request/response
cycles against the FastAPI application.

Because the application is SSR-first and form-driven, tests operate at the
HTTP/HTML level rather than using browser automation.

What Is Covered

Authentication and authorization

Anonymous users are redirected appropriately

Role-based access enforced on the server (ADMIN / DM / PLAYER)

Monster visibility rules

Players can only view official monsters

DM-created monsters are hidden until approved

Core workflows

Admin monster creation (POST → redirect → detail page)

DM monster creation with pending state

Server-enforced admin-only routes

Edit/delete routes return 403 Forbidden for non-admin users

Why No Browser-Based E2E Tests?

Browser-driven E2E testing (e.g. Playwright / Selenium) was intentionally avoided:

The UI is SSR-first with minimal JavaScript

HTTP-level tests already validate complete user-facing behavior

This reduces flakiness and maintenance overhead

The result is a smaller, higher-signal test suite suitable for a first portfolio project.


### Running Tests

```bash

pytest

```

Tests require a dedicated test database configured via TEST_DATABASE_URL.
The schema is reset automatically between tests.

Domain Rules

See: docs/monster_domain.md

This project was built as a first bootcamp portfolio submission, with an emphasis on
clarity, correctness, and maintainability over feature breadth.