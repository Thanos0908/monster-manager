"""
Monster Create — SSR Form Parsing
Purpose:
    Parse and validate Monster Create SSR form submissions into a
    MonsterCreate payload.
Responsibilities:
    - Extract raw form values (strings)
    - Normalize and parse structured inputs (lists, JSON blocks, numbers)
    - Preserve user-entered values for SSR re-rendering
    - Collect field-level and global validation errors
    - Validate against MonsterCreate Pydantic schema
Non-responsibilities:
    - No database access
    - No persistence
    - No authorization decisions (service enforces final rules)
    - No side effects
Used by:
    POST /monsters/new
Dependencies:
    - pydantic
    - starlette (FormData)
"""

from __future__ import annotations
import json
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from pydantic import ValidationError
from starlette.datastructures import FormData
from backend.schemas.monster.pydantic_models import MonsterCreate


_INDEXED_RE = re.compile(r"^(?P<prefix>\w+)\[(?P<idx>\d+)\]\.(?P<field>\w+)$")

CR_FRACTIONS = {
    "1/8": Decimal("0.125"),
    "1/4": Decimal("0.25"),
    "1/2": Decimal("0.5"),
}


def _as_str(form: FormData, key: str) -> Optional[str]:
    """Return stripped string or None if missing or blank."""
    v = form.get(key)
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _as_bool_checkbox(form: FormData, key: str) -> bool:
    """HTML checkbox convention: present => True, absent => False."""
    return form.get(key) is not None


def _split_lines(text: Optional[str]) -> List[str]:
    """Split newline-separated textarea into a list of non-empty lines."""
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def _parse_json_list(
    text: Optional[str], *, field_label: str
) -> Tuple[Optional[List[Any]], Optional[str]]:
    """
    Parse a JSON textarea expected to contain a list.
    Empty => []
    Invalid JSON => global error
    Non-list JSON => global error
    """
    if text is None or text.strip() == "":
        return [], None

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None, f"invalid JSON in {field_label}"

    if not isinstance(obj, list):
        return None, f"{field_label} must be a JSON list"

    return obj, None


def _collect_indexed_objects(form: FormData, prefix: str) -> Dict[int, Dict[str, str]]:
    """
    Collect indexed rows like:
        movement[0].type, movement[0].speed
    into:
        {0: {"type": "...", "speed": "..."}}
    """
    buckets: Dict[int, Dict[str, str]] = {}
    for key in form.keys():
        match = _INDEXED_RE.match(key)
        if not match or match.group("prefix") != prefix:
            continue

        idx = int(match.group("idx"))
        field = match.group("field")
        value = _as_str(form, key)
        if value is None:
            continue

        buckets.setdefault(idx, {})[field] = value

    return buckets


def _pydantic_errors_to_maps(
    exc: ValidationError,
) -> Tuple[Dict[str, List[str]], List[str]]:
    """Convert Pydantic ValidationError into SSR-friendly error maps."""
    field_errors: Dict[str, List[str]] = {}
    global_errors: List[str] = []

    for err in exc.errors():
        loc = err.get("loc", ())
        msg = err.get("msg", "invalid value")
        path = ".".join(str(p) for p in loc) if loc else ""

        if path:
            field_errors.setdefault(path, []).append(msg)
        else:
            global_errors.append(msg)

    return field_errors, global_errors


def parse_monster_create_form(
    form: FormData,
    *,
    actor_role: str,
) -> Tuple[
    Optional[MonsterCreate],
    Dict[str, List[str]],
    List[str],
    Dict[str, Any],
]:
    """
    Parse and validate Monster Create SSR form submission.
    Returns: (payload_or_none, field_errors, global_errors, raw_form_values)
    All-or-nothing: If any parsing or validation error occurs, payload is None.
    """
    field_errors: Dict[str, List[str]] = {}
    global_errors: List[str] = []
    raw_form: Dict[str, Any] = {}

    def grab(key: str) -> Optional[str]:
        raw_form[key] = form.get(key, "")
        return _as_str(form, key)

    def parse_int(key: str) -> Optional[int]:
        raw_form[key] = form.get(key, "")
        s = _as_str(form, key)
        if s is None:
            return None
        try:
            return int(s)
        except ValueError:
            field_errors.setdefault(key, []).append(f"{key} must be a number")
            return None

    def parse_cr(key: str) -> Optional[Decimal]:
        raw_form[key] = form.get(key, "")
        s = _as_str(form, key)
        if s is None:
            return None

        if s in CR_FRACTIONS:
            return CR_FRACTIONS[s]

        try:
            d = Decimal(s)
        except Exception:
            field_errors.setdefault(key, []).append("challenge_rating must be a valid CR")
            return None

        if d != d.to_integral_value():
            field_errors.setdefault(key, []).append("challenge_rating must be a valid CR")
            return None

        if d < 0 or d > 30:
            field_errors.setdefault(key, []).append("challenge_rating must be between 0 and 30")
            return None

        return d

    # Scalars
    name = grab("name")
    size = grab("size")
    main_type = grab("main_type")
    subtype = grab("subtype")
    alignment = grab("alignment")

    armor_class_text = grab("armor_class_text")
    hit_points_dice = grab("hit_points_dice")
    backstory = grab("backstory")

    challenge_rating = parse_cr("challenge_rating")
    xp_override = parse_int("xp_override")
    hit_points = parse_int("hit_points")
    passive_perception = parse_int("passive_perception")
    telepathy_range = parse_int("telepathy_range")

    required = {
        "name": name,
        "size": size,
        "main_type": main_type,
        "alignment": alignment,
        "challenge_rating": challenge_rating,
        "armor_class_text": armor_class_text,
        "hit_points": hit_points,
        "hit_points_dice": hit_points_dice,
        "passive_perception": passive_perception,
    }
    for field, value in required.items():
        if value is None:
            field_errors.setdefault(field, []).append(f"{field} is required")

    # Ability scores
    ability_scores: Dict[str, int] = {}
    for stat in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
        key_upper = f"ability_scores.{stat}"
        key_lower = f"ability_scores.{stat.lower()}"
        raw_form[key_upper] = form.get(key_upper, form.get(key_lower, ""))
        s = _as_str(form, key_upper) or _as_str(form, key_lower)
        if s is None:
            field_errors.setdefault(key_upper, []).append(f"{key_upper} is required")
            continue
        try:
            ability_scores[stat] = int(s)
        except ValueError:
            field_errors.setdefault(key_upper, []).append(f"{key_upper} must be a number")

    # Saving throw proficiencies (optional)
    saving_throw_bonuses: Dict[str, int] = {}
    for ab in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
        key = f"saving_throws.bonuses.{ab}"
        raw_form[key] = form.get(key, "")
        raw = (form.get(key) or "").strip()
        if raw == "":
            continue
        try:
            saving_throw_bonuses[ab] = int(raw)
        except ValueError:
            field_errors[key] = ["Must be an integer."]

    saving_throws = {"bonuses": saving_throw_bonuses} if saving_throw_bonuses else None

    # Skill proficiencies (optional)
    skill_bonuses: Dict[str, int] = {}
    for sk in (
        "Acrobatics",
        "Animal Handling",
        "Arcana",
        "Athletics",
        "Deception",
        "History",
        "Insight",
        "Intimidation",
        "Investigation",
        "Medicine",
        "Nature",
        "Perception",
        "Performance",
        "Persuasion",
        "Religion",
        "Sleight of Hand",
        "Stealth",
        "Survival",
    ):
        key = f"skills.bonuses.{sk}"
        raw_form[key] = form.get(key, "")
        raw = (form.get(key) or "").strip()
        if raw == "":
            continue
        try:
            skill_bonuses[sk] = int(raw)
        except ValueError:
            field_errors[key] = ["Must be an integer."]

    skills = {"bonuses": skill_bonuses} if skill_bonuses else None

    # Indexed lists
    movement: List[Dict[str, Any]] = []
    for idx, row in _collect_indexed_objects(form, "movement").items():
        raw_form[f"movement[{idx}].type"] = form.get(f"movement[{idx}].type", "")
        raw_form[f"movement[{idx}].speed"] = form.get(f"movement[{idx}].speed", "")
        raw_form[f"movement[{idx}].hover"] = (
            "on" if _as_bool_checkbox(form, f"movement[{idx}].hover") else ""
        )

        if not row:
            continue

        if "type" not in row:
            field_errors.setdefault(f"movement[{idx}].type", []).append("movement type is required")
            continue
        if "speed" not in row:
            field_errors.setdefault(f"movement[{idx}].speed", []).append("movement speed is required")
            continue

        try:
            speed = int(row["speed"])
        except ValueError:
            field_errors.setdefault(f"movement[{idx}].speed", []).append("movement speed must be a number")
            continue

        movement.append(
            {
                "type": row["type"],
                "speed": speed,
                "hover": _as_bool_checkbox(form, f"movement[{idx}].hover"),
            }
        )

    senses: List[Dict[str, Any]] = []
    for idx, row in _collect_indexed_objects(form, "senses").items():
        raw_form[f"senses[{idx}].sense"] = form.get(f"senses[{idx}].sense", "")
        raw_form[f"senses[{idx}].range"] = form.get(f"senses[{idx}].range", "")

        if not row:
            continue

        if "sense" not in row:
            field_errors.setdefault(f"senses[{idx}].sense", []).append("sense is required")
            continue
        if "range" not in row:
            field_errors.setdefault(f"senses[{idx}].range", []).append("sense range is required")
            continue

        try:
            sense_range = int(row["range"])
        except ValueError:
            field_errors.setdefault(f"senses[{idx}].range", []).append("sense range must be a number")
            continue

        senses.append({"sense": row["sense"], "range": sense_range})

    languages: List[Dict[str, Any]] = []
    for idx, row in _collect_indexed_objects(form, "languages").items():
        raw_form[f"languages[{idx}].language"] = form.get(f"languages[{idx}].language", "")

        if not row:
            continue

        if "language" not in row:
            field_errors.setdefault(f"languages[{idx}].language", []).append("language is required")
            continue

        # LanguageItem field name in schema
        languages.append({"LanguageItem": row["language"]})

    damage_resistances: List[Dict[str, Any]] = []
    for _, row in _collect_indexed_objects(form, "damage_resistances").items():
        if not row:
            continue
        if "type" not in row or not row["type"]:
            continue
        damage_resistances.append({"type": row["type"]})

    damage_immunities: List[Dict[str, Any]] = []
    for _, row in _collect_indexed_objects(form, "damage_immunities").items():
        if not row:
            continue
        if "type" not in row or not row["type"]:
            continue
        damage_immunities.append({"type": row["type"]})

    damage_vulnerabilities: List[Dict[str, Any]] = []
    for _, row in _collect_indexed_objects(form, "damage_vulnerabilities").items():
        if not row:
            continue
        if "type" not in row or not row["type"]:
            continue
        damage_vulnerabilities.append({"type": row["type"]})

    condition_immunities: List[Dict[str, Any]] = []
    for _, row in _collect_indexed_objects(form, "condition_immunities").items():
        if not row:
            continue
        if "condition" not in row or not row["condition"]:
            continue
        condition_immunities.append({"condition": row["condition"]})

    # JSON builder blocks
    traits, err = _parse_json_list(grab("traits_json"), field_label="traits")
    if err:
        global_errors.append(err)

    actions, err = _parse_json_list(grab("actions_json"), field_label="actions")
    if err:
        global_errors.append(err)

    reactions, err = _parse_json_list(grab("reactions_json"), field_label="reactions")
    if err:
        global_errors.append(err)

    legendary_actions, err = _parse_json_list(
        grab("legendary_actions_json"),
        field_label="legendary_actions",
    )
    if err:
        global_errors.append(err)

    # Newline lists
    lair_actions = _split_lines(grab("lair_actions_text"))
    regional_effects = _split_lines(grab("regional_effects_text"))

    if field_errors or global_errors:
        return None, field_errors, global_errors, raw_form

    data: Dict[str, Any] = {
        "name": name,
        "size": size,
        "main_type": main_type,
        "subtype": subtype,
        "alignment": alignment,
        "challenge_rating": challenge_rating,
        "xp_override": xp_override,
        "armor_class_text": armor_class_text,
        "hit_points": hit_points,
        "hit_points_dice": hit_points_dice,
        "passive_perception": passive_perception,
        "telepathy_range": telepathy_range,
        "ability_scores": ability_scores,
        "movement": movement,
        "senses": senses,
        "languages": languages,
        "traits": traits or [],
        "actions": actions or [],
        "reactions": reactions or [],
        "legendary_actions": legendary_actions or [],
        "lair_actions": lair_actions,
        "regional_effects": regional_effects,
        "backstory": backstory,
        "damage_resistances": damage_resistances,
        "damage_immunities": damage_immunities,
        "damage_vulnerabilities": damage_vulnerabilities,
        "condition_immunities": condition_immunities,
        "saving_throws": saving_throws,
        "skills": skills,
    }

    try:
        payload = MonsterCreate.model_validate(data)
    except ValidationError as exc:
        p_field, p_global = _pydantic_errors_to_maps(exc)
        for k, msgs in p_field.items():
            field_errors.setdefault(k, []).extend(msgs)
        global_errors.extend(p_global)
        return None, field_errors, global_errors, raw_form

    return payload, field_errors, global_errors, raw_form