"""
Service layer for domain logic.
Services:
- Enforce business rules and invariants
- Coordinate database writes
- Remain framework-agnostic (no FastAPI / Request / Response objects)
Called by:
- Routers (HTTP layer)
"""