"""Paste preview and confirmation endpoints (never logs or stores raw text)."""

from fastapi import APIRouter

from app.application.paste_import import ConfirmItemInput
from app.interfaces.api.deps import AuthDep, ContainerDep
from app.interfaces.schemas import (
    ItemOut,
    PasteConfirmRequest,
    PasteConfirmResponse,
    PastePreviewRequest,
    PastePreviewResponse,
    PreviewItemOut,
)

router = APIRouter(prefix="/paste", tags=["paste"])


@router.post("/preview", response_model=PastePreviewResponse)
async def preview_paste(
    body: PastePreviewRequest,
    auth: AuthDep,
    container: ContainerDep,
) -> PastePreviewResponse:
    _, household = auth
    result = await container.preview_paste.execute(
        household_id=household.id,
        text=body.text,
    )
    return PastePreviewResponse(
        items=[
            PreviewItemOut(
                name=i.name,
                quantity_text=i.quantity_text,
                category=i.category,
                urgency=i.urgency,
                requested_by=i.requested_by,
                source_snippet=i.source_snippet,
                confidence=i.confidence,
                merge_with_item_id=i.merge_with_item_id,
            )
            for i in result.items
        ],
        ignored=result.ignored,
        engine=result.engine,
    )


@router.post("/confirm", response_model=PasteConfirmResponse)
async def confirm_paste(
    body: PasteConfirmRequest,
    auth: AuthDep,
    container: ContainerDep,
) -> PasteConfirmResponse:
    member, household = auth
    inputs = [
        ConfirmItemInput(
            name=i.name,
            quantity_text=i.quantity_text,
            category=i.category,
            urgency=i.urgency,
            requested_by=i.requested_by,
            merge_with_item_id=i.merge_with_item_id,
        )
        for i in body.items
    ]
    saved = await container.confirm_paste.execute(
        household_id=household.id,
        current_member_id=member.id,
        items=inputs,
    )
    return PasteConfirmResponse(items=[ItemOut.from_domain(i) for i in saved])
