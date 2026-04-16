"""Software category enum used by install-path suggestion flow."""

from enum import Enum


class SoftwareCategory(str, Enum):
    """Controlled software categories for routing decisions."""

    DEVELOPMENT_ENVIRONMENT = "development_environment"
    ENGINEERING = "engineering"
    PRODUCTIVITY = "productivity"
    MEDIA_DESIGN = "media_design"
    SYSTEM_UTILITIES = "system_utilities"
    GAMES_ENTERTAIN = "games_entertain"
    UNKNOWN = "unknown"
