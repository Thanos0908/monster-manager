from __future__ import annotations

# Create our Mixins classes that can be used to help us avoid writing the __str and __repr__ in every class we make  
class ReprMixin:
    """Generic __repr__ that shows class name and a few key attrs."""
    __repr_attrs__ = ("id",)

    def __repr__(self) -> str:
        parts = []
        for attr in self.__repr_attrs__:
            if hasattr(self, attr):
                parts.append(f"{attr}={getattr(self, attr)!r}")
        return f"<{self.__class__.__name__} {' '.join(parts)}>"

class StrMixin:
    """Friendly __str__ ."""
    def __str__(self) -> str:
        for field in ("username", "name", "email"):
            if hasattr(self, field) and getattr(self, field):
                return str(getattr(self, field))
        return repr(self)