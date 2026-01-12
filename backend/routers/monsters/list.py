"""
SSR monster list + filter UI.
- Filters only apply when `submitted=1` so the initial page load is fast and stable.
- Monster visibility is always enforced via `monster_filter_for_user(current_user)`.
"""

from __future__ import annotations
from pathlib import Path
from math import ceil
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates
from backend.authorization.dependencies import require_authenticated, monster_filter_for_user
from backend.core.database import get_session
from backend.enums.monster_enums import (
    Alignment,
    Condition,
    DamageType,
    Language,
    MovementType,
    Sense,
    Size,
)
from backend.models.monster import Monster
from backend.models.user import User

router = APIRouter()

_BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
templates = Jinja2Templates(directory=str(_BACKEND_DIR / "templates"))

PAGE_SIZE = 25


@router.get("/monsters", response_class=HTMLResponse)
async def list_monsters(
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_authenticated),
):
    actor_role = getattr(current_user.role, "value", str(current_user.role))

    qp = request.query_params
    filters = {
        "submitted": qp.get("submitted"),
        "page": qp.get("page"),
        # Admin-only scope (ignored for non-admins)
        "vis": qp.get("vis"),
        # Single
        "size": qp.get("size"),
        "alignment": qp.get("alignment"),
        # Multi (repeat param)
        "languages": qp.getlist("languages"),
        "movements": qp.getlist("movements"),
        "hover": qp.get("hover"),
        "senses": qp.getlist("senses"),
        "condition_immunities": qp.getlist("condition_immunities"),
        "damage_immunities": qp.getlist("damage_immunities"),
        "damage_resistances": qp.getlist("damage_resistances"),
        "damage_vulnerabilities": qp.getlist("damage_vulnerabilities"),
        # Ability comparators
        "str_op": qp.get("str_op"),
        "str_val": qp.get("str_val"),
        "dex_op": qp.get("dex_op"),
        "dex_val": qp.get("dex_val"),
        "con_op": qp.get("con_op"),
        "con_val": qp.get("con_val"),
        "int_op": qp.get("int_op"),
        "int_val": qp.get("int_val"),
        "wis_op": qp.get("wis_op"),
        "wis_val": qp.get("wis_val"),
        "cha_op": qp.get("cha_op"),
        "cha_val": qp.get("cha_val"),
    }

    # Normalize role-specific fields
    if actor_role != "ADMIN":
        filters["vis"] = None

    # Normalize pagination (1-based)
    try:
        page = int(filters.get("page") or 1)
    except ValueError:
        page = 1
    page = max(page, 1)
    filters["page"] = page

    # Normalize ability ops/vals
    allowed_ops = {"eq", "lt", "lte", "gt", "gte"}
    for key in ("str", "dex", "con", "int", "wis", "cha"):
        op_key = f"{key}_op"
        val_key = f"{key}_val"

        if filters.get(op_key) not in allowed_ops:
            filters[op_key] = None

        raw_val = filters.get(val_key)
        try:
            filters[val_key] = int(raw_val) if raw_val not in (None, "") else None
        except (TypeError, ValueError):
            filters[val_key] = None

    # Default admin scope selection
    if actor_role == "ADMIN" and filters["vis"] not in {"all", "official", "community"}:
        filters["vis"] = "all"

    # Only execute filtering queries after the user submits the form.
    submitted = filters.get("submitted") == "1"

    # Defaults for template (when not submitted)
    monsters: list[Monster] = []
    total_count = 0
    total_pages = 1
    active_filters: list[str] = []
    page_q_prefix = "/monsters?page="

    if submitted:
        # Start from authorization visibility
        base_filter = monster_filter_for_user(current_user)

        if actor_role == "ADMIN":
            vis = filters.get("vis") or "all"
            if vis == "official":
                stmt_filter = base_filter & (Monster.is_official.is_(True))
            elif vis == "community":
                stmt_filter = base_filter & (Monster.is_official.is_(False))
            else:
                stmt_filter = base_filter
        else:
            stmt_filter = base_filter

        # Single filters
        if filters.get("size"):
            stmt_filter = stmt_filter & (Monster.size == filters["size"])

        if filters.get("alignment"):
            stmt_filter = stmt_filter & (Monster.alignment == filters["alignment"])

        # Ability comparators
        ability_columns = {
            "str": Monster.str_score,
            "dex": Monster.dex_score,
            "con": Monster.con_score,
            "int": Monster.int_score,
            "wis": Monster.wis_score,
            "cha": Monster.cha_score,
        }

        for key, col in ability_columns.items():
            op = filters.get(f"{key}_op")
            val = filters.get(f"{key}_val")

            if not op or val is None:
                continue

            if op == "eq":
                stmt_filter = stmt_filter & (col == val)
            elif op == "lt":
                stmt_filter = stmt_filter & (col < val)
            elif op == "lte":
                stmt_filter = stmt_filter & (col <= val)
            elif op == "gt":
                stmt_filter = stmt_filter & (col > val)
            elif op == "gte":
                stmt_filter = stmt_filter & (col >= val)

        # Multi filters (must include ALL selected)
        for lang in filters.get("languages", []):
            stmt_filter = stmt_filter & Monster.languages.any(language=lang)

        for mv in filters.get("movements", []):
            stmt_filter = stmt_filter & Monster.movements.any(movement_type=mv)

        if filters.get("hover") == "1":
            stmt_filter = stmt_filter & Monster.movements.any(
                movement_type="fly",
                hover=True,
            )

        for s in filters.get("senses", []):
            stmt_filter = stmt_filter & Monster.senses.any(sense=s)

        for c in filters.get("condition_immunities", []):
            stmt_filter = stmt_filter & Monster.condition_immunities.any(condition=c)

        for dt in filters.get("damage_immunities", []):
            stmt_filter = stmt_filter & Monster.damage_immunities.any(damage_type=dt)

        for dt in filters.get("damage_resistances", []):
            stmt_filter = stmt_filter & Monster.damage_resistances.any(damage_type=dt)

        for dt in filters.get("damage_vulnerabilities", []):
            stmt_filter = stmt_filter & Monster.damage_vulnerabilities.any(damage_type=dt)

        # Total count for "X results" + pagination
        count_stmt = select(func.count(Monster.id)).where(stmt_filter)
        total_count = await db.scalar(count_stmt) or 0
        total_pages = max(1, ceil(total_count / PAGE_SIZE))

        # Clamp page to available range
        page = min(filters["page"], total_pages)
        filters["page"] = page
        offset = (page - 1) * PAGE_SIZE

        # Fetch paginated results
        stmt = (
            select(Monster)
            .where(stmt_filter)
            .order_by(Monster.name.asc())
            .offset(offset)
            .limit(PAGE_SIZE)
        )
        result = await db.execute(stmt)
        monsters = result.scalars().all()

        # Active filters summary
        op_symbol = {"eq": "=", "lt": "<", "lte": "≤", "gt": ">", "gte": "≥"}
        ability_labels = {"str": "STR", "dex": "DEX", "con": "CON", "int": "INT", "wis": "WIS", "cha": "CHA"}

        if actor_role == "ADMIN":
            vis = filters.get("vis") or "all"
            vis_label = {
                "all": "All monsters",
                "official": "Official only",
                "community": "Community only",
            }.get(vis, "All monsters")
            active_filters.append(f"Scope: {vis_label}")

        if filters.get("size"):
            active_filters.append(f"Size: {filters['size']}")

        if filters.get("alignment"):
            active_filters.append(f"Alignment: {filters['alignment']}")

        for key, label in ability_labels.items():
            op = filters.get(f"{key}_op")
            val = filters.get(f"{key}_val")
            if op and val is not None:
                active_filters.append(f"{label} {op_symbol.get(op, op)} {val}")

        def _join(values: list[str], title_case: bool = False) -> str:
            if not values:
                return ""
            if title_case:
                values = [v.title() for v in values]
            return ", ".join(values)

        if filters.get("languages"):
            active_filters.append(f"Languages: {_join(filters['languages'])}")

        if filters.get("movements"):
            active_filters.append(f"Movements: {_join(filters['movements'], title_case=True)}")

        if filters.get("hover") == "1":
            active_filters.append("Hover: Yes")

        if filters.get("senses"):
            active_filters.append(f"Senses: {_join(filters['senses'], title_case=True)}")

        if filters.get("condition_immunities"):
            active_filters.append(f"Condition immunities: {_join(filters['condition_immunities'])}")

        if filters.get("damage_immunities"):
            active_filters.append(f"Damage immunities: {_join(filters['damage_immunities'])}")

        if filters.get("damage_resistances"):
            active_filters.append(f"Damage resistances: {_join(filters['damage_resistances'])}")

        if filters.get("damage_vulnerabilities"):
            active_filters.append(f"Damage vulnerabilities: {_join(filters['damage_vulnerabilities'])}")

        # Build pagination URL prefix preserving all current params except page
        params = list(request.query_params.multi_items())
        params = [(k, v) for (k, v) in params if k != "page"]
        base_qs = urlencode(params, doseq=True)
        page_q_prefix = f"/monsters?{base_qs}&page=" if base_qs else "/monsters?page="

    success = request.query_params.get("success")

    return templates.TemplateResponse(
        request,
        "monsters/list.html",
        {
            "monsters": monsters,
            "actor_role": actor_role,
            "success": success,
            "filters": filters,
            "total_count": total_count,
            "total_pages": total_pages,
            "page": filters["page"],
            "page_size": PAGE_SIZE,
            "active_filters": active_filters,
            "page_q_prefix": page_q_prefix,
            "enums": {
                "Size": [e.value for e in Size],
                "Alignment": [e.value for e in Alignment],
                "Language": [e.value for e in Language],
                "MovementType": [e.value for e in MovementType],
                "Sense": [e.value for e in Sense],
                "Condition": [e.value for e in Condition],
                "DamageType": [e.value for e in DamageType],
            },
        },
    )