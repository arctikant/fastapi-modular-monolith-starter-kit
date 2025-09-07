from factory.alchemy import SQLAlchemyModelFactory, SQLAlchemyOptions
from sqlalchemy.ext.asyncio import AsyncSession


class AsyncSQLAlchemyOptions(SQLAlchemyOptions):
    sqlalchemy_session: AsyncSession


class AsyncSQLAlchemyModelFactory(SQLAlchemyModelFactory):
    _meta: AsyncSQLAlchemyOptions

    class Meta:
        abstract = True

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        await cls._meta.sqlalchemy_session.commit()
        return instance

    @classmethod
    async def create_batch_async(cls, size: int, *args, **kwargs) -> list:
        return [await cls.create(**kwargs) for _ in range(size)]
