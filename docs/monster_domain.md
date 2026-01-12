# Monster Domain Rules

This document defines the **domain rules and invariants** for monsters in the  
D&D Monster Manager project.

It is the single source of truth for:
- visibility rules
- submission and ownership semantics
- moderation workflow
- CR / XP behavior

All CRUD implementations must respect the rules defined here.

---

## Roles

The system defines three roles:

- **admin**
- **dm** (Dungeon Master)
- **player**

Role enforcement happens exclusively on the backend  
(routers + authorization layer), never in templates.

---

## Monster Ownership & Attribution

- A monster is either **system-owned** or **user-submitted**.
- The `owner_id` field records **who submitted the monster for moderation**.
- `owner_id` is used for **attribution, accountability, and admin evaluation**.
- `owner_id` does **not** grant visibility or editing rights.

Ownership rules:
- Monsters submitted by DMs have `owner_id = dm_user.id`.
- Monsters created or approved by admins are **system-owned** (`owner_id = NULL`).
- If a DM is deleted, monsters they submitted remain in the system.

This allows admins to:
- identify DMs who submit low-quality or excessive content
- recognize DMs who consistently submit high-quality monsters
- make informed promotion or demotion decisions

---

## Official vs Unofficial Monsters

### `is_official = true`
- Represents curated, approved monsters
- System-owned (`owner_id = NULL`)
- Visible to **all roles** (admin, dm, player)
- Editable **only by admins**
- Represents authoritative content

Monsters created by admins are immediately official.

---

### `is_official = false`
- Represents monsters **pending moderation**
- Submitted by DMs
- Visible **only to admins**
- Not visible to DMs or players
- Used to evaluate submission quality and DM behavior

Updates made by an admin automatically sets the `is_official` field to True.

---

## Visibility Rules (Summary)

| Role    | Can see official | Can see unofficial |
|-------- |-----------------|-------------------|
| Admin   | ✅ Yes           | ✅ Yes (all)       |
| DM      | ✅ Yes           | ❌ No              |
| Player  | ✅ Yes           | ❌ No              |

Visibility is enforced centrally in the authorization layer.

---

## Approval Workflow

- Monsters submitted by DMs start as `is_official = false`
- Submitting a monster immediately places it in the **admin moderation queue**
- Admins may approve a monster, making it official and system-owned by editing it (even if they change nothing in the edit)

This creates a clear moderation pipeline without introducing complex states.

---

## Challenge Rating (CR) and XP Rules

### Challenge Rating
- CR ranges from **0 to 30**
- Stored as `Decimal` to support fractional CRs (e.g. 0.25, 0.5)

### XP Calculation
- XP is derived from CR using a fixed mapping (D&D 5e rules)
- Implemented in `backend/utils/cr_xp.py`

### CR 0 Special Case
- CR 0 monsters may define an `xp_override`
- Allowed values: `0` or `10`
- For all other CR values, `xp_override` must be `NULL`

These rules are enforced at the schema and service level.

---

## Data Integrity Guarantees

- A damage type cannot appear in more than one of:
  - immunities
  - resistances
  - vulnerabilities
- Movement with `hover = true` requires a `fly` movement type
- Ability scores are constrained to valid D&D ranges

Validation happens in schemas; persistence rules live in services.

---

## Scope Notes

- Search, filtering, and pagination are **read concerns**
  and do not alter domain rules.
- Templates are presentation-only and must not implement domain logic.
- Database schema changes are managed using Alembic migrations.
- The current migration set reflects the stable schema used by the application and tests.

---

## Guiding Principle

> **All monster-related behavior must be explainable using this document.**

If a CRUD operation violates a rule defined here, the implementation is incorrect.