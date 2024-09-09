from factory.alchemy import SQLAlchemyModelFactory


class AsyncSQLAlchemyModelFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        await cls._meta.sqlalchemy_session.commit()
        return instance

    @classmethod
    async def create_batch(cls, size: int, *args, **kwargs) -> list:
        return [await cls.create(**kwargs) for _ in range(size)]
