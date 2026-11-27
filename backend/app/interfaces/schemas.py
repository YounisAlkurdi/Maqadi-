"""Pydantic request and response schemas for the HTTP API."""

from datetime import datetime

from pydantic import BaseModel

from app.domain.entities import Household, Member


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
