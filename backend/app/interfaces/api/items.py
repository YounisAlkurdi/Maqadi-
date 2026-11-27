"""Items endpoints."""

from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from app.domain.enums import ItemStatus
from app.interfaces.api.deps import AuthDep, ContainerDep
from app.interfaces.schemas import (
    ClearBoughtRequest,
    ClearBoughtResponse,
    CreateItemRequest,
    ItemHistoryResponse,
    ItemOut,
    ListItemsResponse,
    SetStatusRequest,
    UpdateItemRequest,
)

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ListItemsResponse)
async def list_items(
    auth: AuthDep,
    container: ContainerDep,
    response: Response,
    item_status: Annotated[ItemStatus | None, Query(alias="status")] = None,
    if_none_match: Annotated[str | None, Header()] = None,
) -> ListItemsResponse | Response:
    _, household = auth
    result = await container.list_items.execute(household_id=household.id, status=item_status)

    if if_none_match is not None and if_none_match.strip() == result.etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": result.etag})

    response.headers["ETag"] = result.etag
    return ListItemsResponse(items=[ItemOut.from_domain(i) for i in result.items])


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    body: CreateItemRequest,
    auth: AuthDep,
    container: ContainerDep,
) -> ItemOut:
    member, household = auth
    item = await container.add_item.execute(
        household_id=household.id,
        member_id=member.id,
        name=body.name,
        quantity_text=body.quantity_text,
        note=body.note,
        category=body.category,
        urgency=body.urgency,
    )
    return ItemOut.from_domain(item)


@router.get("/history", response_model=ItemHistoryResponse)
async def get_item_history(
    auth: AuthDep,
    container: ContainerDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> ItemHistoryResponse:
    _, household = auth
    items = await container.list_recent_bought.execute(household_id=household.id, limit=limit)
    return ItemHistoryResponse(items=[ItemOut.from_domain(i) for i in items])


@router.patch("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: str,
    body: UpdateItemRequest,
    auth: AuthDep,
    container: ContainerDep,
) -> ItemOut:
    _, household = auth
    fields = body.model_fields_set
    kwargs: dict[str, object] = {}
    if "name" in fields and body.name is not None:
        kwargs["name"] = body.name
    if "quantity_text" in fields:
        kwargs["quantity_text"] = body.quantity_text
    if "note" in fields:
        kwargs["note"] = body.note
    if "category" in fields and body.category is not None:
        kwargs["category"] = body.category
    if "urgency" in fields and body.urgency is not None:
        kwargs["urgency"] = body.urgency

    item = await container.update_item.execute(
        household_id=household.id,
        item_id=item_id,
        **kwargs,
    )
    return ItemOut.from_domain(item)


@router.post("/{item_id}/status", response_model=ItemOut)
async def set_item_status(
    item_id: str,
    body: SetStatusRequest,
    auth: AuthDep,
    container: ContainerDep,
) -> ItemOut:
    member, household = auth
    item = await container.set_status.execute(
        household_id=household.id,
        item_id=item_id,
        member_id=member.id,
        status=body.status,
    )
    return ItemOut.from_domain(item)


@router.post("/clear-bought", response_model=ClearBoughtResponse)
async def clear_bought(
    auth: AuthDep,
    container: ContainerDep,
    body: ClearBoughtRequest | None = None,
) -> ClearBoughtResponse:
    _, household = auth
    older_than_hours = body.older_than_hours if body is not None else 0
    count = await container.archive_bought.execute(
        household_id=household.id,
        older_than_hours=older_than_hours,
    )
    return ClearBoughtResponse(archived_count=count)
