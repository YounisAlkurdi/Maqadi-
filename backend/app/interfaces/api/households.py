"""Household and member endpoints."""

from fastapi import APIRouter, Request, status

from app.interfaces.api.deps import AuthDep, ContainerDep
from app.interfaces.schemas import (
    CreateHouseholdRequest,
    CreateHouseholdResponse,
    HouseholdOut,
    JoinHouseholdRequest,
    JoinHouseholdResponse,
    MemberOut,
    MeResponse,
    RotateInviteResponse,
)

router = APIRouter(tags=["households"])


@router.post(
    "/households",
    response_model=CreateHouseholdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_household(
    body: CreateHouseholdRequest,
    container: ContainerDep,
) -> CreateHouseholdResponse:
    result = await container.create_household.execute(
        household_name=body.household_name,
        display_name=body.display_name,
        color=body.color,
    )
    return CreateHouseholdResponse(
        household=HouseholdOut.from_domain(result.household),
        member=MemberOut.from_domain(result.member),
        member_token=result.member_token,
        invite_code=result.invite_code,
    )


@router.post("/households/join", response_model=JoinHouseholdResponse)
async def join_household(
    body: JoinHouseholdRequest,
    request: Request,
    container: ContainerDep,
) -> JoinHouseholdResponse:
    client_ip = request.client.host if request.client else "unknown"
    result = await container.join_household.execute(
        invite_code=body.invite_code,
        display_name=body.display_name,
        color=body.color,
        client_ip=client_ip,
    )
    return JoinHouseholdResponse(
        household=HouseholdOut.from_domain(result.household),
        member=MemberOut.from_domain(result.member),
        member_token=result.member_token,
    )


@router.post("/households/invite/rotate", response_model=RotateInviteResponse)
async def rotate_invite_code(
    auth: AuthDep,
    container: ContainerDep,
) -> RotateInviteResponse:
    _, household = auth
    new_code = await container.rotate_invite_code.execute(household_id=household.id)
    return RotateInviteResponse(invite_code=new_code)


@router.get("/me", response_model=MeResponse)
async def get_me(
    auth: AuthDep,
    container: ContainerDep,
) -> MeResponse:
    member, household = auth
    result = await container.get_me.execute(member=member, household=household)
    return MeResponse(
        member=MemberOut.from_domain(result.member),
        household=HouseholdOut.from_domain(result.household),
        members=[MemberOut.from_domain(m) for m in result.members],
    )


@router.delete("/households/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: str,
    auth: AuthDep,
    container: ContainerDep,
) -> None:
    member, household = auth
    await container.remove_member.execute(
        household_id=household.id,
        actor_member_id=member.id,
        target_member_id=member_id,
    )
