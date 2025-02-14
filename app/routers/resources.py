"""
API routing for resources.
"""
import json, uuid
from typing import Annotated
from pydantic import ValidationError
from fastapi import APIRouter, Path, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlmodel import select
from ..errors import Error, ErrorType
from ..query import QueryParamsDep
from ..db import SessionDep
from .users import User, UserSecurity
from ..models import Resource

router = APIRouter(
    prefix="/resources",
    tags=["resources"],
)

@router.get("/", tags=["resources"],
    summary="Get resources")
def get_resources(
    query: QueryParamsDep,
    current_user: Annotated[User, UserSecurity(scopes=["resources:read"])],
    session: SessionDep,
) -> list[Resource]:
    """
    Get a list of resources.
    """
    try:
        q = select(Resource).offset(query.skip).limit(query.size)
        r = session.exec(q).all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to get resources",
                input=query,
                ctx={"error":str(e)},
            ))]) from e

    return list(r)

@router.get("/{id}", tags=["resources"],
    summary="Get resource")
def get_resource(
    id: Annotated[uuid.UUID, Path()],
    current_user: Annotated[User, UserSecurity(scopes=["resources:read"])],
    session: SessionDep,
) -> Resource:
    """
    Get a single resource.
    """
    try:
        r = session.get(Resource, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to get resource",
                input=id,
                ctx={"error":str(e)},
            ))]) from e
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail=[jsonable_encoder(Error(type=ErrorType.NOT_FOUND,
                msg="resource not found",
                input=id,
            ))])
    return r

@router.post("/", tags=["resources"],
    summary="Create resource",
    status_code=status.HTTP_201_CREATED)
def create_resource(
    resource: Resource,
    current_user: Annotated[User, UserSecurity(scopes=["resources:write"])],
    session: SessionDep,
) -> Resource:
    """
    Create a resource.
    """
    try:
        resource.model_validate(resource)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[jsonable_encoder(Error(type=ErrorType.INVALID_REQUEST,
                msg="invalid resource",
                input=resource.model_dump(warnings="none"),
                ctx=json.loads(e.json()),
            ))])
    try:
        session.add(resource)
        session.commit()
        session.refresh(resource)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to create resource",
                input=resource.model_dump(warnings="none"),
                ctx={"error":str(e)},
            ))]) from e
    return resource

@router.patch("/{id}", tags=["resources"],
    summary="Update resource")
def update_resource(
    id: Annotated[uuid.UUID, Path()],
    resource: Resource,
    current_user: Annotated[User, UserSecurity(scopes=["resources:write"])],
    session: SessionDep,
) -> Resource:
    """
    Update a resource.
    """
    try:
        current = session.get(Resource, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to get existing resource",
                input={
                    "id":id,
                    "resource":resource.model_dump(warnings="none"),
                },
                ctx={"error":str(e)},
            ))]) from e
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail=[jsonable_encoder(Error(type=ErrorType.NOT_FOUND,
                msg="resource not found",
                input={
                    "id":id,
                    "resource":resource.model_dump(warnings="none"),
                },
            ))])
    resource.id = id
    current.sqlmodel_update(resource.model_dump(exclude_unset=True))
    try:
        current.model_validate(current)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[jsonable_encoder(Error(type=ErrorType.INVALID_REQUEST,
                msg="invalid resource",
                input={
                    "id":id,
                    "resource":current.model_dump(warnings="none"),
                },
                ctx=json.loads(e.json()),
            ))])
    try:
        session.add(current)
        session.commit()
        session.refresh(current)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to update resource",
                input={
                    "id":id,
                    "resource":current.model_dump(warnings="none"),
                },
                ctx={"error":str(e)},
            ))]) from e
    return current

@router.put("/{id}", tags=["resources"],
    summary="Replace resource")
def replace_resource(
    id: Annotated[uuid.UUID, Path()],
    resource: Resource,
    current_user: Annotated[User, UserSecurity(scopes=["resources:write"])],
    session: SessionDep,
) -> Resource:
    """
    Replace a resource.
    """
    try:
        current = session.get(Resource, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to get existing resource",
                input={
                    "id":id,
                    "resource":resource.model_dump(warnings="none"),
                },
                ctx={"error":str(e)},
            ))]) from e
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail=[jsonable_encoder(Error(type=ErrorType.NOT_FOUND,
                msg="resource not found",
                input={
                    "id":id,
                    "resource":resource.model_dump(warnings="none"),
                },
            ))])
    resource.id = id
    current.sqlmodel_update(resource.model_dump(exclude_unset=False))
    try:
        current.model_validate(current)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[jsonable_encoder(Error(type=ErrorType.INVALID_REQUEST,
                msg="invalid resource",
                input=current.model_dump(warnings="none"),
                ctx=json.loads(e.json()),
            ))])
    try:
        session.add(current)
        session.commit()
        session.refresh(current)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to replace resource",
                input=current.model_dump(warnings="none"),
                ctx={"error":str(e)},
            ))]) from e
    return resource

@router.delete("/{id}", tags=["resources"],
    summary="Delete resource",
    status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    id: Annotated[uuid.UUID, Path()],
    current_user: Annotated[User, UserSecurity(scopes=["resources:write"])],
    session: SessionDep,
) -> None:
    """
    Delete a resource.
    """
    try:
       r = session.get(Resource, id)
    except Exception as e:
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
               msg="unable to get resource for delete",
               input=id,
               ctx={"error":str(e)},
           ))]) from e
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail=[jsonable_encoder(Error(type=ErrorType.NOT_FOUND,
                msg="resource not found",
                input=id,
            ))])
    try:
        session.delete(r)
        session.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to delete resource",
                input=id,
                ctx={"error":str(e)},
            ))]) from e
