"""Pydantic request and response schemas for the HTTP API."""

from datetime import datetime

from pydantic import BaseModel

from app.domain.entities import Household, Item, Member
from app.domain.enums import Category, ItemSource, ItemStatus, Urgency


class ErrorDetail(BaseModel):
    code: str
    message: str
    existing_item_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HouseholdOut(BaseModel):
    id: str
    name: str
    invite_code: str
    created_at: datetime

    @classmethod
    def from_domain(cls, household: Household) -> "HouseholdOut":
        return cls(
            id=household.id,
            name=household.name,
            invite_code=household.invite_code,
            created_at=household.created_at,
        )


class MemberOut(BaseModel):
    id: str
    household_id: str
    display_name: str
    color: str
    created_at: datetime

    @classmethod
    def from_domain(cls, member: Member) -> "MemberOut":
        return cls(
            id=member.id,
            household_id=member.household_id,
            display_name=member.display_name,
            color=member.color,
            created_at=member.created_at,
        )


class CreateHouseholdRequest(BaseModel):
    household_name: str
    display_name: str
    color: str


class CreateHouseholdResponse(BaseModel):
    household: HouseholdOut
    member: MemberOut
    member_token: str
    invite_code: str


class JoinHouseholdRequest(BaseModel):
    invite_code: str
    display_name: str
    color: str


class JoinHouseholdResponse(BaseModel):
    household: HouseholdOut
    member: MemberOut
    member_token: str


class RotateInviteResponse(BaseModel):
    invite_code: str


class MeResponse(BaseModel):
    member: MemberOut
    household: HouseholdOut
    members: list[MemberOut]


class ItemOut(BaseModel):
    id: str
    household_id: str
    name: str
    name_normalized: str
    quantity_text: str | None
    note: str | None
    category: Category
    status: ItemStatus
    urgency: Urgency
    requested_by_member_id: str | None
    bought_by_member_id: str | None
    source: ItemSource
    created_at: datetime
    updated_at: datetime
    bought_at: datetime | None

    @classmethod
    def from_domain(cls, item: Item) -> "ItemOut":
        return cls(
            id=item.id,
            household_id=item.household_id,
            name=item.name,
            name_normalized=item.name_normalized,
            quantity_text=item.quantity_text,
            note=item.note,
            category=item.category,
            status=item.status,
            urgency=item.urgency,
            requested_by_member_id=item.requested_by_member_id,
            bought_by_member_id=item.bought_by_member_id,
            source=item.source,
            created_at=item.created_at,
            updated_at=item.updated_at,
            bought_at=item.bought_at,
        )


class ListItemsResponse(BaseModel):
    items: list[ItemOut]


class ItemHistoryResponse(BaseModel):
    items: list[ItemOut]


class CreateItemRequest(BaseModel):
    name: str
    quantity_text: str | None = None
    note: str | None = None
    category: Category = Category.OTHER
    urgency: Urgency = Urgency.NORMAL


class UpdateItemRequest(BaseModel):
    name: str | None = None
    quantity_text: str | None = None
    note: str | None = None
    category: Category | None = None
    urgency: Urgency | None = None


class SetStatusRequest(BaseModel):
    status: ItemStatus


class ClearBoughtRequest(BaseModel):
    older_than_hours: int = 0


class ClearBoughtResponse(BaseModel):
    archived_count: int


class PastePreviewRequest(BaseModel):
    text: str


class PreviewItemOut(BaseModel):
    name: str
    quantity_text: str | None
    category: Category
    urgency: Urgency
    requested_by: str | None
    source_snippet: str
    confidence: float
    merge_with_item_id: str | None


class PastePreviewResponse(BaseModel):
    items: list[PreviewItemOut]
    ignored: list[str]
    engine: str


class ConfirmItemIn(BaseModel):
    name: str
    quantity_text: str | None = None
    category: Category = Category.OTHER
    urgency: Urgency = Urgency.NORMAL
    requested_by: str | None = None
    merge_with_item_id: str | None = None


class PasteConfirmRequest(BaseModel):
    items: list[ConfirmItemIn]


class PasteConfirmResponse(BaseModel):
    items: list[ItemOut]
