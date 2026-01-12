"""
HTTP routing layer (SSR endpoints and any future JSON API endpoints).
Routers should:
- Parse request inputs (forms/query params)
- Enforce authorization via dependencies
- Delegate business rules to services
- Render templates / return redirects
"""