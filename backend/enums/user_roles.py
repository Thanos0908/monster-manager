from enum import Enum

class UserRole(str, Enum):
    """
    Defines the roles a user can have in the system.

    - ADMIN: Full control over all resources and settings.
    - DM: Dungeon Master, can manage monsters and game-related content.
    - PLAYER: Standard player, limited to viewing and personal monster management.
    """
    ADMIN = "ADMIN"
    DM = "DM"
    PLAYER = "PLAYER"