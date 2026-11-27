"""Domain enumerations and value constants."""

from enum import StrEnum


class ItemStatus(StrEnum):
    OPEN = "open"
    BOUGHT = "bought"
    CANCELLED = "cancelled"


class Urgency(StrEnum):
    NORMAL = "normal"
    URGENT = "urgent"


class ItemSource(StrEnum):
    MANUAL = "manual"
    PASTE = "paste"


class Category(StrEnum):
    PRODUCE = "produce"
    DAIRY_EGGS = "dairy_eggs"
    MEAT_POULTRY = "meat_poultry"
    BAKERY = "bakery"
    PANTRY = "pantry"
    CLEANING = "cleaning"
    PHARMACY = "pharmacy"
    OTHER = "other"


MEMBER_COLORS: tuple[str, ...] = (
    "#2A7F85",
    "#7A4A7D",
    "#B5622F",
    "#4A5AA8",
    "#6E8B3D",
    "#B84A6B",
)
