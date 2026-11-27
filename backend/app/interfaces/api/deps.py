"""FastAPI dependencies for container access and Bearer token authentication."""

from typing import Annotated, Any

from fastapi import Depends, Header, Request

from app.application.households import hash_token
from app.domain.entities import Household, Member
from app.domain.errors import UnauthorizedError


def get_container(request: Request) -> Any:
    """Retrieve the wired application container from FastAPI app state."""
    return request.app.state.container


ContainerDep = Annotated[Any, Depends(get_container)]


async def get_current_auth(
    container: ContainerDep,
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[Member, Household]:
    """Resolve Authorization: Bearer <token> into (Member, Household)."""
    if not authorization:
        raise UnauthorizedError("Missing authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise UnauthorizedError("Invalid authorization scheme")

    token_hash = hash_token(token.strip())
    member = await container.member_repo.get_by_token_hash(token_hash)
    if member is None:
        raise UnauthorizedError("Invalid or expired token")

    household = await container.household_repo.get_by_id(member.household_id)
    if household is None:
        raise UnauthorizedError("Household not found for member")

    return member, household


AuthDep = Annotated[tuple[Member, Household], Depends(get_current_auth)]
