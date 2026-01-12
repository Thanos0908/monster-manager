"""User role definitions used for authentication and authorization."""

from enum import Enum

class UserRole(str, Enum):
    """
    Defines the roles a user can have in the system.
    - ADMIN: Full control over all resources and settings.
    - DM: Dungeon Master, can create unofficial monsters and view official monsters.
    - PLAYER: Standard player, limited to viewing official monsters.
    """
    ADMIN = "ADMIN"
    DM = "DM"
    PLAYER = "PLAYER"
    
__all__ = ["UserRole"]