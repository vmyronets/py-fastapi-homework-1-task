from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema


SessionDep = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: SessionDep,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(
            10, ge=1, le=20, description="Items per page"
        )
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    offset = (page - 1) * per_page

    result = await db.scalars(
        select(MovieModel)
        .offset(offset)
        .limit(per_page)
    )
    movies = result.all()

    base_url = "/theater/movies/"

    prev_page = None
    if page > 1:
        prev_page = f"{base_url}?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"{base_url}?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema
)
async def get_movie_by_id(
        movie_id: int,
        db: SessionDep
):
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie
