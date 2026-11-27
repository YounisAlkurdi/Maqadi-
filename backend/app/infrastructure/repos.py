"""SQLAlchemy repository implementations mapping ORM rows to domain entities."""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.entities import Household, Item, Member
from app.domain.enums import Category, ItemSource, ItemStatus, Urgency
from app.domain.errors import DuplicateItemError, NotFoundError
from app.infrastructure.models import HouseholdORM, ItemORM, MemberORM


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _ensure_utc_opt(dt: datetime | None) -> datetime | None:
    return _ensure_utc(dt) if dt is not None else None


def _to_household(row: HouseholdORM) -> Household:
    return Household(
        id=row.id,
        name=row.name,
        invite_code=row.invite_code,
        created_at=_ensure_utc(row.created_at),
    )


def _to_member(row: MemberORM) -> Member:
    return Member(
        id=row.id,
        household_id=row.household_id,
        display_name=row.display_name,
        color=row.color,
        token_hash=row.token_hash,
        created_at=_ensure_utc(row.created_at),
    )


def _to_item(row: ItemORM) -> Item:
    return Item(
        id=row.id,
        household_id=row.household_id,
        name=row.name,
        name_normalized=row.name_normalized,
        quantity_text=row.quantity_text,
        note=row.note,
        category=Category(row.category),
        status=ItemStatus(row.status),
        urgency=Urgency(row.urgency),
        requested_by_member_id=row.requested_by_member_id,
        bought_by_member_id=row.bought_by_member_id,
        source=ItemSource(row.source),
        created_at=_ensure_utc(row.created_at),
        updated_at=_ensure_utc(row.updated_at),
        bought_at=_ensure_utc_opt(row.bought_at),
        archived_at=_ensure_utc_opt(row.archived_at),
    )


class SqlHouseholdRepo:
    """SQLAlchemy implementation of HouseholdRepo."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, household: Household) -> Household:
        row = HouseholdORM(
            id=household.id,
            name=household.name,
            invite_code=household.invite_code,
            created_at=_ensure_utc(household.created_at),
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_household(row)

    async def get_by_id(self, household_id: str) -> Household | None:
        async with self._session_factory() as session:
            row = await session.get(HouseholdORM, household_id)
            return _to_household(row) if row is not None else None

    async def get_by_invite_code(self, invite_code: str) -> Household | None:
        async with self._session_factory() as session:
            stmt = select(HouseholdORM).where(HouseholdORM.invite_code == invite_code)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _to_household(row) if row is not None else None

    async def update_invite_code(self, household_id: str, new_code: str) -> Household:
        async with self._session_factory() as session:
            row = await session.get(HouseholdORM, household_id)
            if row is None:
                raise NotFoundError("Household not found")
            row.invite_code = new_code
            await session.commit()
            await session.refresh(row)
            return _to_household(row)


class SqlMemberRepo:
    """SQLAlchemy implementation of MemberRepo."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, member: Member) -> Member:
        row = MemberORM(
            id=member.id,
            household_id=member.household_id,
            display_name=member.display_name,
            color=member.color,
            token_hash=member.token_hash,
            created_at=_ensure_utc(member.created_at),
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_member(row)

    async def get_by_id(self, member_id: str) -> Member | None:
        async with self._session_factory() as session:
            row = await session.get(MemberORM, member_id)
            return _to_member(row) if row is not None else None

    async def get_by_token_hash(self, token_hash: str) -> Member | None:
        async with self._session_factory() as session:
            stmt = select(MemberORM).where(MemberORM.token_hash == token_hash)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _to_member(row) if row is not None else None

    async def list_by_household(self, household_id: str) -> list[Member]:
        async with self._session_factory() as session:
            stmt = (
                select(MemberORM)
                .where(MemberORM.household_id == household_id)
                .order_by(MemberORM.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_member(row) for row in rows]

    async def update_token_and_color(self, member_id: str, token_hash: str, color: str) -> Member:
        async with self._session_factory() as session:
            row = await session.get(MemberORM, member_id)
            if row is None:
                raise NotFoundError("Member not found")
            row.token_hash = token_hash
            row.color = color
            await session.commit()
            await session.refresh(row)
            return _to_member(row)

    async def delete(self, household_id: str, member_id: str) -> bool:
        async with self._session_factory() as session:
            stmt = select(MemberORM).where(
                MemberORM.id == member_id,
                MemberORM.household_id == household_id,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
            return True


class SqlItemRepo:
    """SQLAlchemy implementation of ItemRepo."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, item: Item) -> Item:
        row = ItemORM(
            id=item.id,
            household_id=item.household_id,
            name=item.name,
            name_normalized=item.name_normalized,
            quantity_text=item.quantity_text,
            note=item.note,
            category=item.category.value,
            status=item.status.value,
            urgency=item.urgency.value,
            requested_by_member_id=item.requested_by_member_id,
            bought_by_member_id=item.bought_by_member_id,
            source=item.source.value,
            created_at=_ensure_utc(item.created_at),
            updated_at=_ensure_utc(item.updated_at),
            bought_at=_ensure_utc_opt(item.bought_at),
            archived_at=_ensure_utc_opt(item.archived_at),
        )
        async with self._session_factory() as session:
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                if "ix_items_open_unique" in str(exc) or "UNIQUE constraint failed" in str(exc):
                    raise DuplicateItemError() from exc
                raise
            await session.refresh(row)
            return _to_item(row)

    async def get_by_id(self, household_id: str, item_id: str) -> Item | None:
        async with self._session_factory() as session:
            stmt = select(ItemORM).where(
                ItemORM.id == item_id,
                ItemORM.household_id == household_id,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _to_item(row) if row is not None else None

    async def find_open_by_normalized_name(
        self, household_id: str, name_normalized: str
    ) -> Item | None:
        async with self._session_factory() as session:
            stmt = select(ItemORM).where(
                ItemORM.household_id == household_id,
                ItemORM.name_normalized == name_normalized,
                ItemORM.status == ItemStatus.OPEN.value,
                ItemORM.archived_at.is_(None),
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _to_item(row) if row is not None else None

    async def list_by_household(
        self,
        household_id: str,
        *,
        status: ItemStatus | None = None,
        include_archived: bool = False,
    ) -> list[Item]:
        async with self._session_factory() as session:
            stmt = select(ItemORM).where(ItemORM.household_id == household_id)
            if status is not None:
                stmt = stmt.where(ItemORM.status == status.value)
            if not include_archived:
                stmt = stmt.where(ItemORM.archived_at.is_(None))
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_item(row) for row in rows]

    async def update(self, item: Item) -> Item:
        async with self._session_factory() as session:
            stmt = select(ItemORM).where(
                ItemORM.id == item.id,
                ItemORM.household_id == item.household_id,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise NotFoundError("Item not found")

            row.name = item.name
            row.name_normalized = item.name_normalized
            row.quantity_text = item.quantity_text
            row.note = item.note
            row.category = item.category.value
            row.status = item.status.value
            row.urgency = item.urgency.value
            row.requested_by_member_id = item.requested_by_member_id
            row.bought_by_member_id = item.bought_by_member_id
            row.source = item.source.value
            row.updated_at = _ensure_utc(item.updated_at)
            row.bought_at = _ensure_utc_opt(item.bought_at)
            row.archived_at = _ensure_utc_opt(item.archived_at)

            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                if "ix_items_open_unique" in str(exc) or "UNIQUE constraint failed" in str(exc):
                    raise DuplicateItemError() from exc
                raise
            await session.refresh(row)
            return _to_item(row)

    async def archive_bought_before(
        self, household_id: str, cutoff: datetime, now: datetime
    ) -> int:
        async with self._session_factory() as session:
            stmt = (
                update(ItemORM)
                .where(
                    ItemORM.household_id == household_id,
                    ItemORM.status == ItemStatus.BOUGHT.value,
                    ItemORM.archived_at.is_(None),
                    ItemORM.bought_at.is_not(None),
                    ItemORM.bought_at <= _ensure_utc(cutoff),
                )
                .values(archived_at=_ensure_utc(now), updated_at=_ensure_utc(now))
            )
            result = await session.execute(stmt)
            await session.commit()
            return int(result.rowcount or 0)

    async def list_recent_bought(self, household_id: str, limit: int) -> list[Item]:
        async with self._session_factory() as session:
            stmt = (
                select(ItemORM)
                .where(
                    ItemORM.household_id == household_id,
                    ItemORM.status == ItemStatus.BOUGHT.value,
                )
                .order_by(ItemORM.bought_at.desc())
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_item(row) for row in rows]
