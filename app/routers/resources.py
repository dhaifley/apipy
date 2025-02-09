"""
API routing for resources.
"""
import json
import uuid
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
    r: Resource,
    current_user: Annotated[User, UserSecurity(scopes=["resources:write"])],
    session: SessionDep,
) -> Resource:
    """
    Create a resource.
    """
    try:
        r.model_validate(r)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[jsonable_encoder(Error(type=ErrorType.INVALID_REQUEST,
                msg="invalid resource",
                input=r.model_dump(warnings="none"),
                ctx=json.loads(e.json()),
            ))])

    try:
        session.add(r)
        session.commit()
        session.refresh(r)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to create resource",
                input=r,
                ctx={"error":str(e)},
            ))]) from e

    return r

@router.patch("/{id}", tags=["resources"],
    summary="Update resource")
def update_resource(
    id: Annotated[uuid.UUID, Path()],
    r: Resource,
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
                input={"id":id, "resource":r.model_dump(warnings="none")},
                ctx={"error":str(e)},
            ))]) from e

    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail=[jsonable_encoder(Error(type=ErrorType.NOT_FOUND,
                msg="resource not found",
                input={"id":id, "resource":r.model_dump(warnings="none")},
            ))])

    r.id = id
    data = r.model_dump(exclude_unset=True)

    current.sqlmodel_update(data)

    try:
        current.model_validate(current)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[jsonable_encoder(Error(type=ErrorType.INVALID_REQUEST,
                msg="invalid resource",
                input={"id":id, "resource":r.model_dump(warnings="none")},
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
                input={"id":id, "resource":r.model_dump(warnings="none")},
                ctx={"error":str(e)},
            ))]) from e

    return r

@router.put("/{id}", tags=["resources"],
    summary="Replace resource")
def replace_resource(
    id: Annotated[uuid.UUID, Path()],
    r: Resource,
    current_user: Annotated[User, UserSecurity(scopes=["resources:write"])],
    session: SessionDep,
) -> Resource:
    """
    Replace a resource.
    """
    try:
        r.id = id
        r.model_validate(r)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[jsonable_encoder(Error(type=ErrorType.INVALID_REQUEST,
                msg="invalid resource",
                input=r.model_dump(warnings="none"),
                ctx=json.loads(e.json()),
            ))])

    try:
        session.add(r)
        session.commit()
        session.refresh(r)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[jsonable_encoder(Error(type=ErrorType.DATABASE,
                msg="unable to replace resource",
                input=r,
                ctx={"error":str(e)},
            ))]) from e

    return r

@router.delete("/{id}", tags=["resources"],
    summary="Delete resource",
    status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(id: Annotated[uuid.UUID, Path()],
    current_user: Annotated[User, UserSecurity(scopes=["resources:write"])],
    session: SessionDep):
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
