"""Domain ports (abstract interfaces) implemented by infrastructure adapters."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol

from app.domain.entities import Household, Item, Member
from app.domain.enums import Category, ItemStatus, Urgency


@dataclass(frozen=True)
class ExtractedItem:
    name: str
    quantity_text: str | None
    category: Category
    urgency: Urgency
    requested_by: str | None
    source_snippet: str
    confidence: float


@dataclass(frozen=True)
class ExtractionResult:
    items: list[ExtractedItem]
    ignored: list[str]
    engine: Literal["llm", "rules"]


class ItemExtractor(Protocol):
    async def extract(self, text: str, known_members: list[str]) -> ExtractionResult: ...


class HouseholdRepo(Protocol):
    async def create(self, household: Household) -> Household: ...
    async def get_by_id(self, household_id: str) -> Household | None: ...
    async def get_by_invite_code(self, invite_code: str) -> Household | None: ...
    async def update_invite_code(self, household_id: str, new_code: str) -> Household: ...


class MemberRepo(Protocol):
    async def create(self, member: Member) -> Member: ...
    async def get_by_id(self, member_id: str) -> Member | None: ...
    async def get_by_token_hash(self, token_hash: str) -> Member | None: ...
    async def list_by_household(self, household_id: str) -> list[Member]: ...


class ItemRepo(Protocol):
    async def create(self, item: Item) -> Item: ...
    async def get_by_id(self, household_id: str, item_id: str) -> Item | None: ...
    async def find_open_by_normalized_name(
        self, household_id: str, name_normalized: str
    ) -> Item | None: ...
    async def list_by_household(
        self,
        household_id: str,
        *,
        status: ItemStatus | None = None,
        include_archived: bool = False,
    ) -> list[Item]: ...
    async def update(self, item: Item) -> Item: ...
    async def archive_bought_before(
        self, household_id: str, cutoff: datetime, now: datetime
    ) -> int: ...
    async def list_recent_bought(self, household_id: str, limit: int) -> list[Item]: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class EventBus(Protocol):
    async def publish(
        self, household_id: str, event_type: str, payload: dict[str, Any]
    ) -> None: ...


class RateLimiter(Protocol):
    async def check_and_record(self, key: str, *, success: bool) -> None: ...


class TicketSigner(Protocol):
    def issue(self, household_id: str, member_id: str) -> str: ...
    def verify_and_consume(self, ticket: str) -> tuple[str, str] | None: ...
