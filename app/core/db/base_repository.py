from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel as BaseSchema
from pydantic import ConfigDict, Field
from sqlalchemy import Select, delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_model import BaseModel, SoftDeleteMixin
from app.core.db.exceptions import DatabaseException
from app.core.services.log import get_log_service


class SortOrder(str, Enum):
    asc = 'asc'
    desc = 'desc'


class SortParam(BaseSchema):
    field: str
    order: SortOrder = SortOrder.asc


class FilterParam(BaseSchema):
    field: str
    value: int | str | list


class ListParams(BaseSchema):
    sort: list[SortParam] | None = Field(None, description='Sorting parameters')
    filters: list[FilterParam] | None = Field(None, description='Filtering parameters')
    page: int = Field(1, ge=1, description='Page number')
    per_page: int = Field(10, ge=1, le=100, description='Items per page')


class Pagination(BaseSchema):
    total: int
    page: int
    per_page: int


T = TypeVar('T')


class PaginatedResult(BaseSchema, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    pagination: Pagination


ModelType = TypeVar('ModelType', bound=BaseModel)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseSchema)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseSchema)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, model_id: str | int, with_deleted: bool = False) -> ModelType | None:
        if self._is_soft_deletable() and not with_deleted:
            result = await db.execute(self.model.select_not_deleted().where(self.model.id == model_id))  # type: ignore
            return result.scalars().first()
        else:
            return await db.get(self.model, model_id)

    async def get_list(
        self, db: AsyncSession, params: ListParams, schema: type[BaseSchema] | None = None, with_deleted: bool = False
    ) -> PaginatedResult:
        if self._is_soft_deletable() and not with_deleted:
            query = self.model.select_not_deleted()  # type: ignore
        else:
            query = select(self.model)

        query = self._filter(query=query, params=params)
        query = self._sort(query=query, params=params)

        return await self._paginate(db=db, query=query, params=params, schema=schema)

    async def create(self, db: AsyncSession, data: CreateSchemaType) -> ModelType:
        model = self.model(**data.model_dump(exclude_unset=True, exclude_none=True))
        db.add(model)

        return model

    async def update(self, db: AsyncSession, model: ModelType, data: UpdateSchemaType) -> ModelType:
        update_data = data if isinstance(data, dict) else data.model_dump(exclude_unset=True, exclude_none=True)
        model.update(update_data)
        db.add(model)

        return model

    async def delete(
        self, db: AsyncSession, model_id: int | None = None, model: ModelType | None = None, is_soft: bool = True
    ) -> None:
        if model is None and model_id is not None:
            model = await self.get(db, model_id, not is_soft)

        if not model:
            return None

        if is_soft and self._is_soft_deletable():
            model.soft_delete()  # type: ignore
        else:
            await db.delete(model)

    async def delete_all(self, db: AsyncSession, model_ids: list[int]) -> None:
        await db.execute(delete(self.model).where(self.model.id.in_(model_ids)))  # type: ignore

    async def commit(self, db: AsyncSession) -> None:
        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            await get_log_service().a_exception('database_error')
            raise DatabaseException('Database error occurred')

    def _filter(self, query: Select, params: ListParams) -> Select:
        if params.filters:
            for item in params.filters:
                if isinstance(item.value, list):
                    query = query.where(getattr(self.model, item.field).in_(item.value))
                else:
                    query = query.where(getattr(self.model, item.field) == item.value)  # type: ignore

        return query

    def _sort(self, query: Select, params: ListParams) -> Select:
        if params.sort:
            for item in params.sort:
                column = getattr(self.model, item.field)
                query = query.order_by(column.desc() if item.order == SortOrder.desc else column)

        return query

    async def _paginate(
        self, db: AsyncSession, query: Select, params: ListParams, schema: type[BaseSchema] | None = None
    ) -> PaginatedResult[BaseSchema]:
        total = await db.scalar(select(func.count()).select_from(query.subquery()))

        query = query.offset((params.page - 1) * params.per_page).limit(params.per_page)
        result = await db.execute(query)

        items = result.scalars().all()
        if schema:
            items = [schema.model_validate(item) for item in items]

        return PaginatedResult(
            items=items,  # type: ignore
            pagination=Pagination(total=total, page=params.page, per_page=params.per_page),  # type: ignore
        )

    def _is_soft_deletable(self) -> bool:
        return issubclass(self.model, SoftDeleteMixin)
