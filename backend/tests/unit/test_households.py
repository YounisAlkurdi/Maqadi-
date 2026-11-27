"""Unit tests for household use cases and join rate limiting."""

import pytest

from app.application.households import (
    INVITE_CODE_ALPHABET,
    CreateHousehold,
    GetMe,
    JoinHousehold,
    RotateInviteCode,
    hash_token,
)
from app.domain.enums import MEMBER_COLORS
from app.domain.errors import NotFoundError, RateLimitedError, ValidationError
from app.infrastructure.rate_limit import InMemoryRateLimiter
from tests.unit.fakes import FakeClock, FakeEventBus, FakeHouseholdRepo, FakeMemberRepo


async def test_create_household_stores_hashed_token_and_unambiguous_code() -> None:
    hh_repo = FakeHouseholdRepo()
    mem_repo = FakeMemberRepo()
    clock = FakeClock()
    use_case = CreateHousehold(hh_repo, mem_repo, clock)

    res = await use_case.execute(
        household_name="  بيت أبو أحمد  ",
        display_name="  أمي  ",
        color=MEMBER_COLORS[0],
    )

    assert res.household.name == "بيت أبو أحمد"
    assert res.member.display_name == "أمي"
    assert len(res.invite_code) == 8
    assert all(ch in INVITE_CODE_ALPHABET for ch in res.invite_code)
    assert res.member.token_hash == hash_token(res.member_token)
    assert res.member.token_hash != res.member_token


async def test_create_household_validates_color_and_display_name() -> None:
    use_case = CreateHousehold(FakeHouseholdRepo(), FakeMemberRepo(), FakeClock())

    with pytest.raises(ValidationError):
        await use_case.execute(household_name="بيتنا", display_name="   ", color=MEMBER_COLORS[0])

    with pytest.raises(ValidationError):
        await use_case.execute(
            household_name="بيتنا", display_name="أ" * 31, color=MEMBER_COLORS[0]
        )

    with pytest.raises(ValidationError):
        await use_case.execute(household_name="بيتنا", display_name="أمي", color="#000000")


async def test_join_household_normalizes_code_and_publishes_event() -> None:
    hh_repo = FakeHouseholdRepo()
    mem_repo = FakeMemberRepo()
    clock = FakeClock()
    limiter = InMemoryRateLimiter(clock)
    bus = FakeEventBus()

    created = await CreateHousehold(hh_repo, mem_repo, clock).execute(
        household_name="بيت أبو أحمد",
        display_name="أمي",
        color=MEMBER_COLORS[0],
    )
    dashed_code = f"{created.invite_code[:4].lower()}-{created.invite_code[4:].lower()}"

    joined = await JoinHousehold(hh_repo, mem_repo, limiter, clock, bus).execute(
        invite_code=dashed_code,
        display_name="يونس",
        color=MEMBER_COLORS[1],
        client_ip="10.0.0.1",
    )

    assert joined.household.id == created.household.id
    assert joined.member.display_name == "يونس"
    assert len(bus.events) == 1
    assert bus.events[0][1] == "member.joined"

    me = await GetMe(mem_repo).execute(member=joined.member, household=joined.household)
    assert len(me.members) == 2


async def test_join_throttling_per_ip_and_per_code_expires_after_15_minutes() -> None:
    hh_repo = FakeHouseholdRepo()
    mem_repo = FakeMemberRepo()
    clock = FakeClock()
    limiter = InMemoryRateLimiter(clock, max_failures=5, lock_seconds=900)

    created = await CreateHousehold(hh_repo, mem_repo, clock).execute(
        household_name="بيت أبو أحمد",
        display_name="أمي",
        color=MEMBER_COLORS[0],
    )
    join_uc = JoinHousehold(hh_repo, mem_repo, limiter, clock)

    # 5 failed attempts on the same IP (different codes) -> IP gets locked
    for i in range(5):
        with pytest.raises(NotFoundError):
            await join_uc.execute(
                invite_code=f"BADCODE{i}",
                display_name="يونس",
                color=MEMBER_COLORS[1],
                client_ip="192.168.1.50",
            )

    with pytest.raises(RateLimitedError):
        await join_uc.execute(
            invite_code=created.invite_code,
            display_name="يونس",
            color=MEMBER_COLORS[1],
            client_ip="192.168.1.50",
        )

    # 5 failed attempts on the same code from different IPs -> code gets locked
    for i in range(5):
        with pytest.raises(NotFoundError):
            await join_uc.execute(
                invite_code="TARGET99",
                display_name="يونس",
                color=MEMBER_COLORS[1],
                client_ip=f"10.0.0.{i + 1}",
            )

    with pytest.raises(RateLimitedError):
        await join_uc.execute(
            invite_code="TARGET99",
            display_name="يونس",
            color=MEMBER_COLORS[1],
            client_ip="10.0.0.99",
        )

    # Advance 15 minutes -> IP lock is lifted and valid join succeeds
    clock.advance(minutes=15)
    res = await join_uc.execute(
        invite_code=created.invite_code,
        display_name="يونس",
        color=MEMBER_COLORS[1],
        client_ip="192.168.1.50",
    )
    assert res.member.display_name == "يونس"


async def test_rotate_invite_code_invalidates_old_code() -> None:
    hh_repo = FakeHouseholdRepo()
    mem_repo = FakeMemberRepo()
    clock = FakeClock()

    created = await CreateHousehold(hh_repo, mem_repo, clock).execute(
        household_name="بيت أبو أحمد",
        display_name="أمي",
        color=MEMBER_COLORS[0],
    )
    new_code = await RotateInviteCode(hh_repo).execute(household_id=created.household.id)

    assert new_code != created.invite_code
    assert await hh_repo.get_by_invite_code(created.invite_code) is None
    assert await hh_repo.get_by_invite_code(new_code) is not None
