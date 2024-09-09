from abc import ABC, abstractmethod


class BaseTask(ABC):
    @classmethod
    def get_name(cls) -> str:
        """
        Each subclass should define '__task_name__' property
        """
        name = getattr(cls, '__task_name__', None)
        if name is None:
            raise ValueError(f'The task {cls.__name__} does not have a "__task_name__" attribute')

        return name

    @abstractmethod
    def run(self, *args, **kwargs):
        raise NotImplementedError
