from pydantic import BaseModel


class BaseEvent(BaseModel):
    @classmethod
    def get_name(cls) -> str:
        """
        Each subclass should define '__event_name__' property
        """
        name = getattr(cls, '__event_name__', None)
        if name is None:
            raise ValueError(f'The task {cls.__name__} does not have a "__event_name__" attribute')

        return name
