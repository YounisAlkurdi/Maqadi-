"""Use cases for household creation, joining, invite rotation, and member lookup."""

import hashlib
import secrets
import uuid
from dataclasses import dataclass

from app.domain.entities import Household, Member
from app.domain.enums import MEMBER_COLORS
from app.domain.errors import NotFoundError, ValidationError
from app.domain.normalize import normalize_ar
from app.domain.ports import Clock, EventBus, HouseholdRepo, MemberRepo, RateLimiter

INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
INVITE_CODE_LENGTH = 8


def hash_token(token: str) -> str:
    """Return SHA-256 hex digest of a raw member token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> str:
    """Generate a cryptographically secure URL-safe member token."""
    return secrets.token_urlsafe(32)


def generate_invite_code() -> str:
    """Generate an 8-character unambiguous invite code."""
    return "".join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(INVITE_CODE_LENGTH))


def normalize_invite_code(code: str) -> str:
    """Strip whitespace/hyphens and uppercase an invite code."""
    return code.replace("-", "").replace(" ", "").strip().upper()


def validate_display_name(name: str) -> str:
    trimmed = name.strip()
    if not (1 <= len(trimmed) <= 30):
        raise ValidationError("Display name must be between 1 and 30 characters")
    return trimmed


def validate_household_name(name: str) -> str:
    trimmed = name.strip()
    if not (1 <= len(trimmed) <= 60):
        raise ValidationError("Household name must be between 1 and 60 characters")
    return trimmed


def validate_member_color(color: str) -> str:
    if color not in MEMBER_COLORS:
        raise ValidationError("Invalid member color")
    return color


@dataclass(frozen=True)
class CreateHouseholdResult:
    household: Household
    member: Member
    member_token: str
    invite_code: str


@dataclass(frozen=True)
class JoinHouseholdResult:
    household: Household
    member: Member
    member_token: str


@dataclass(frozen=True)
class MeResult:
    member: Member
    household: Household
    members: list[Member]


class CreateHousehold:
    """Create a new household and its founding member."""

    def __init__(
        self,
        household_repo: HouseholdRepo,
        member_repo: MemberRepo,
        clock: Clock,
    ) -> None:
        self._household_repo = household_repo
        self._member_repo = member_repo
        self._clock = clock

    async def execute(
        self,
        *,
        household_name: str,
        display_name: str,
        color: str,
    ) -> CreateHouseholdResult:
        clean_hh_name = validate_household_name(household_name)
        clean_display_name = validate_display_name(display_name)
        clean_color = validate_member_color(color)

        invite_code = await self._unique_invite_code()
        now = self._clock.now()
        household = Household(
            id=str(uuid.uuid4()),
            name=clean_hh_name,
            invite_code=invite_code,
            created_at=now,
        )
        created_hh = await self._household_repo.create(household)

        raw_token = generate_token()
        member = Member(
            id=str(uuid.uuid4()),
            household_id=created_hh.id,
            display_name=clean_display_name,
            color=clean_color,
            token_hash=hash_token(raw_token),
            created_at=now,
        )
        created_member = await self._member_repo.create(member)
        return CreateHouseholdResult(
            household=created_hh,
            member=created_member,
            member_token=raw_token,
            invite_code=created_hh.invite_code,
        )

    async def _unique_invite_code(self) -> str:
        for _ in range(10):
            candidate = generate_invite_code()
            if await self._household_repo.get_by_invite_code(candidate) is None:
                return candidate
        raise RuntimeError("Failed to generate unique invite code")


class JoinHousehold:
    """Join an existing household using an invite code, with IP and code throttling."""

    def __init__(
        self,
        household_repo: HouseholdRepo,
        member_repo: MemberRepo,
        rate_limiter: RateLimiter,
        clock: Clock,
        event_bus: EventBus | None = None,
    ) -> None:
        self._household_repo = household_repo
        self._member_repo = member_repo
        self._rate_limiter = rate_limiter
        self._clock = clock
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        invite_code: str,
        display_name: str,
        color: str,
        client_ip: str,
    ) -> JoinHouseholdResult:
        clean_display_name = validate_display_name(display_name)
        clean_color = validate_member_color(color)
        normalized_code = normalize_invite_code(invite_code)

        ip_key = f"join:ip:{client_ip}"
        code_key = f"join:code:{normalized_code}"

        await self._rate_limiter.check(ip_key)
        await self._rate_limiter.check(code_key)

        household = await self._household_repo.get_by_invite_code(normalized_code)
        if household is None:
            await self._rate_limiter.record_failure(ip_key)
            await self._rate_limiter.record_failure(code_key)
            raise NotFoundError("Invalid invite code", code="invalid_invite_code")

        await self._rate_limiter.reset(ip_key)
        await self._rate_limiter.reset(code_key)

        existing_members = await self._member_repo.list_by_household(household.id)
        normalized_name = normalize_ar(clean_display_name)
        existing_member = next(
            (m for m in existing_members if normalize_ar(m.display_name) == normalized_name),
            None,
        )

        raw_token = generate_token()
        if existing_member is not None:
            rejoined_member = await self._member_repo.update_token_and_color(
                existing_member.id,
                hash_token(raw_token),
                clean_color,
            )
            return JoinHouseholdResult(
                household=household,
                member=rejoined_member,
                member_token=raw_token,
            )

        now = self._clock.now()
        member = Member(
            id=str(uuid.uuid4()),
            household_id=household.id,
            display_name=clean_display_name,
            color=clean_color,
            token_hash=hash_token(raw_token),
            created_at=now,
        )
        created_member = await self._member_repo.create(member)

        if self._event_bus is not None:
            await self._event_bus.publish(
                household.id,
                "member.joined",
                {"member_id": created_member.id, "display_name": created_member.display_name},
            )

        return JoinHouseholdResult(
            household=household,
            member=created_member,
            member_token=raw_token,
        )


class RotateInviteCode:
    """Issue a new invite code for the household, invalidating the old one."""

    def __init__(self, household_repo: HouseholdRepo) -> None:
        self._household_repo = household_repo

    async def execute(self, *, household_id: str) -> str:
        for _ in range(10):
            candidate = generate_invite_code()
            if await self._household_repo.get_by_invite_code(candidate) is None:
                updated = await self._household_repo.update_invite_code(household_id, candidate)
                return updated.invite_code
        raise RuntimeError("Failed to generate unique invite code")


class GetMe:
    """Fetch current member, household, and all household members."""

    def __init__(self, member_repo: MemberRepo) -> None:
        self._member_repo = member_repo

    async def execute(self, *, member: Member, household: Household) -> MeResult:
        members = await self._member_repo.list_by_household(household.id)
        return MeResult(member=member, household=household, members=members)


class RemoveMember:
    """Remove another member from the household."""

    def __init__(self, member_repo: MemberRepo) -> None:
        self._member_repo = member_repo

    async def execute(
        self, *, household_id: str, actor_member_id: str, target_member_id: str
    ) -> None:
        if target_member_id == actor_member_id:
            raise ValidationError(
                "لا يمكنك إزالة نفسك من العائلة",
                code="cannot_remove_self",
            )
        deleted = await self._member_repo.delete(household_id, target_member_id)
        if not deleted:
            raise NotFoundError("Member not found")
