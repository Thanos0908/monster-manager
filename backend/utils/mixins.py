from __future__ import annotations

"""
Reusable utility mixins for model representations.
These are intended for ORM/domain models to avoid repeating common
__repr__ and __str__ implementations.
"""


class ReprMixin:
    """
    Generic __repr__ mixin that shows the class name and selected attributes.
    Subclasses may override __repr_attrs__ to control which attributes
    are included (e.g., ("id", "email")).
    """
    __repr_attrs__ = ("id",)

    def __repr__(self) -> str:
        parts = []
        for attr in self.__repr_attrs__:
            if hasattr(self, attr):
                parts.append(f"{attr}={getattr(self, attr)!r}")

        if parts:
            return f"<{self.__class__.__name__} {' '.join(parts)}>"
        return f"<{self.__class__.__name__}>"


class StrMixin:
    """
    Friendly __str__ mixin.
    Attempts to return a human-readable identifier if present,
    falling back to __repr__.
    """
    def __str__(self) -> str:
        for field in ("username", "name", "email"):
            if hasattr(self, field):
                value = getattr(self, field)
                if value:
                    return str(value)
        return repr(self)