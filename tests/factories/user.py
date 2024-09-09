import factory

from app.auth.models.user import User, UserStatus
from app.auth.security import generate_hash
from tests.factories.async_alchemy_factory import AsyncSQLAlchemyModelFactory


class UserFactory(AsyncSQLAlchemyModelFactory):
    class Meta:
        model = User

    @staticmethod
    def get_password():
        return '1234567890'

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    password_hash = factory.LazyAttribute(lambda obj: generate_hash(UserFactory.get_password()))
    status_id = UserStatus.ACTIVE.value
