# FastAPI Modular Monolith Starter Kit

This project is intended to speed up the process of creating Rest API applications on the [FastAPI](https://fastapi.tiangolo.com) framework built on the Layered Architecture and Modular Monolith principles. This is not a ready-made solution, but a set of basic functions and approaches that can be easily customized and used as a foundation for a project. 

This Starter Kit was inspired by the official template from FastAPI [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template), best practices from here [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) and a lot of other resource related to this topics.

The project emphasizes the modern approaches and best practices for creation of web applications on Python and maximizes the use of asynchronous communication. All libraries that interact with external services or the file system are asynchronous.

**The Project Goals:**

- To provide a basic structure and architecture for a FastAPI application based on the principles of layering and modularity, which will allow for comfortable development, scaling and maintenance of the project in the long run.
- To provide a basic implementation for a FastAPI application of key functionalities such as DB layer, Authorization/Authentication, Events, Cache, Rate Limiter, Queue, Mails, Testing, Logging, etc., which are often required in the backend applications.

> [!WARNING]
> The implementation is not perfect and, of course, subjective. There are nuances with violation of abstraction between layers (for the sake of simplicity and convenience) and many other things that could be done differently, added or improved. If you have any ideas how to make it better, please let me know.

## General

### Database Layer

**Used:**

- Database: [PostgreSQL](https://www.postgresql.org)
- PostgreSQL adapter: [psycopg3](https://www.psycopg.org)
- ORM: [SQLAlchemy](https://www.sqlalchemy.org) 2.0+ (async)
- Migration tool: [Alembic](https://github.com/sqlalchemy/alembic)

**Key Notes:**

- `app.core.db.BaseModel` - implements general model logic. All custom models should inherit it. `BaseModel` itself inherits from `sqlalchemy.orm.DeclarativeBase`.
- `app.core.db.SoftDeleteMixin` - implements soft delete functionality. To add soft delete logic for your particular model you just need to inherit `SoftDeleteMixin`.
- `app.core.db.BaseRepository` - implements general CRUD operations as well as list retrieval with sorting, filtering `app.core.db.ListParams` and pagination `app.core.db.PaginatedResult`.
- `DBSession` form `app.core.deps dependency` should be used to retrieve `sqlalchemy.ext.asyncio.AsyncSession` from FastAPI DI system.
- All models must be imported in `app/core/models.py`, so Alembic will be able to see and work with them.

There is some violation of the interaction between the abstraction layers here, as `sqlalchemy.ext.asyncio.AsyncSession` is passed into services rather than being encapsulated in repositories as is often happens. This is done consciously and there are several reasons for this:

1. I'm absolutely certain that I won't change SQLAlchemy for something else. So there is no need to build a layer of abstraction around it and overcomplicate the architecture.
    
2. I am also pretty sure that my primary database will remain a SQL database. Other databases may be added, such as ElasticSearch, but they will not be a replacement for the main database.
    
3. This allows service-level transaction management, which makes it possible to combine calls to multiple methods of different repositories within a single transaction. For example:
    
    ```python
    async def delete(self, user_id: int | None = None, user: User | None = None) -> None:
        ...
        await self._refresh_token_repository.delete_by_user_id(db=self._db, user_id=user_id)
        await self._user_repository.delete(db=self._db, model_id=user_id, model=user)
        await self._user_repository.commit(db=self._db)
        ...
    ```
    

### API Layer

**Used:**

- Rate limiting tool: [fastapi-limiter](https://github.com/long2ice/fastapi-limiter)
- Storage provider: [Redis](https://redis.io)

**Key Notes:**

- `APIRouter` from `fastapi` should be used to group related routes together. They should be placed into separate files located in `routes.v<api-version>` of your modules. For example: `app.auth.routes.v1.users.py` .
    
- Each module has a top level router, which combines all group routers in one main router. For example: `app.auth.routers.py` .
    
- Top level router from each module should be registered in the app router in `app.core.routers.py`
    
- `app.core.api.ListParamsBuilder` - dependency, that parse and build the list request parameters. It uses `app.core.db.ListParams`, `app.core.db.SortParam` , `app.core.db.FilterParam` Pydantic models. So we can extend them and customize validation rules. For example in `app.auth.schemas.user.py`:
    
    ```python
    from app.core.db import FilterParam, ListParams, SortParam
    
    class UserSortParam(SortParam):
        field: Literal['id', 'username', 'status_id', 'created_at']
    
    class UserFilterParam(FilterParam):
        field: Literal['id', 'username', 'status_id']
    
    class UserListParams(ListParams):
        sort: list[UserSortParam] | None = Field(None, description='Sorting parameters')
        filters: list[UserFilterParam] | None = Field(None, description='Filtering parameters')
    ```
    
    Then we create instance of `app.core.api.ListParamsBuilder` and use it in path operation function:
    
    ```python
    from app.auth.schemas.user import UserFilterParam, UserListParams, UserResponse, UserSortParam
    from app.core.api import ListParamsBuilder, PaginatedResponse
    
    list_params_builder = ListParamsBuilder(UserListParams, UserSortParam, UserFilterParam)
    
    @router.get('')
    async def get_list(request: UserListParams = Depends(list_params_builder)
    ) -> PaginatedResponse[list[UserResponse]]:
        ...
    ```
    
- `app.core.api.ConfigurableRateLimiter` - it is just a simple wrapper for `RateLimiter` dependency from `fastapi_limiter` package, that adds the ability to enable/disable limiting from config.
    
    Here is how limiter can be used `APIRouter` :
    
    ```python
    from app.core.api import ConfigurableRateLimiter
    
    router = APIRouter(dependencies=[Depends(ConfigurableRateLimiter(times=3, seconds=60))])
    ```
    
    Pretty the same for pass operation function:
    
    ```python
    from app.core.api import ConfigurableRateLimiter
    
    @app.get("/", dependencies=[Depends(ConfigurableRateLimiter(times=3, seconds=60))])
    async def index():
        ...
    ```
    
    And thanks to configurable nature, in `.test.env` you can set `RATE_LIMITER_ENABLED=False` , that will disable the limiter for testing environment.
    

### Config

**Key Notes:**
- Application configurations can be obtained via `app.core.configs.app_config`.
- Each module should have its own `config.py` (if necessary), which should be inherited from the `app.core.configs.BaseConfig`.
- All configs retrieve the parameters from the `.env` file.
- `.test.env` - overrides the configuration parameters for the `testing` environment.
- `.sample.env` - is just a sample describing all the parameters that are used. It should be copied into `.env` on the first deploy of our application.

### Dependency Injection.

Usage of external DI containers like [python-dependency-injector](https://github.com/ets-labs/python-dependency-injector) can make some of the solutions in this code more elegant and greatly improve portability of the code to other frameworks, but for simplicity and consistency I've decided to stick with built-in FastAPI DI capabilities for now.

### Policies. Action access logic.

**Key Notes:**

- All policy files should be placed in the `policies` directory in our module.

I found it really useful to separate action access logic and action logic itself. This approach works great on medium to large size projects and makes it much easier to support them over the long term. We don't need to install any third-party library to implement this. I don’t have a place for this logic in the Starter Kit at the moment, so I will just show you an example. It's quite simple.

In your `app.our_module.policies.users.py` :

```python
from app.auth.deps import ActiveUser
from app.auth.exceptions import ActionNotAllowed

async def can_update(user: ActiveUser) bool:
    # Any logic we need to restrict access to this action.
    if not user.is_admin:
        raise ActionNotAllowed("You don't have permission to update the user")
    
    return True
```

Then we can use it in our path operation function:

```python
@router.patch('/{user_id}', dependencies=[Depends(can_update)])
async def update(user_id: int) -> None:
    ...
```

As you can see, the FastAPI DI system allows us to easily and quite elegantly add these checks to our routes. Also we can use it anywhere in our code, for example in your services. We just have to pass the necessary parameters in our function:

```python
from app.auth.exceptions import ActionNotAllowed

async def update_status(user_id: int, status_id: UserStatus) -> User:
    user = await self.get(user_id)

    if not await can_update(user):
        raise ActionNotAllowed("You don't have permission to update the user.")
```

This approach allows us to keep our action access logic in a single place and reuse it if needed. Also it better aligns with SRP from SOLID.

### Gateways. Sync cross-module communication.

**Key Notes:**

- Gateways should be placed into `gateway.py` of each module.

It would be great to create a single entry point for all external sync calls to our module. I suggest we call it Gateway. If we need to call some actions from our module, we should do it through the Gateway. So, first, we create interface which we will use in our dependency and show everyone outside the module:

```python
from app.auth.schemas.user import UserDTO
from app.core.db import ListParams, PaginatedResult

class AuthGatewayInterface(ABC):
    @abstractmethod
    async def get_user(self, user_id: int) -> UserDTO:
        """
        Returns User model by given user_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_list(self, params: ListParams) -> PaginatedResult[UserDTO]:
        """
        Returns PaginatedResult with a list of User models. ListParams input parameter can be used
        to pass pagination, sort and filter parameters
        """
        raise NotImplementedError
```

Next, we have to implement it:

```python
from app.auth.services.user import UserService

class AuthGateway(AuthGatewayInterface):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    async def get_user(self, user_id: int) -> UserDTO:
        user = await self._user_service.get(user_id)

        return UserDTO(**user.to_dict()) if user else None

    async def get_user_list(self, params: ListParams) -> PaginatedResult[UserDTO]:
        return await self._user_service.get_list(params, UserDTO)
```

We can use our dependencies here, because it will be a dependency itself and the FastAPI DI system will resolve everything for us.

Then, we can create function that will be responsible for creating an instance of our `AuthGateway` and define the dependency:

```python
from app.auth.gateway import AuthGateway as AuthGatewayClass
from app.auth.gateway import AuthGatewayInterface
from app.auth.services.user import UserService as UserServiceClass

async def get_gateway(user_service: Annotated[UserServiceClass, Depends(get_user_service)]) -> AuthGatewayInterface:
    return AuthGatewayClass(user_service=user_service)
    
AuthGateway = Annotated[AuthGatewayInterface, Depends(get_gateway)]
```

In `__init__.py` of any module we explicitly define what we want to expose from it.

```python
from app.auth.deps import CurrentUser, ActiveUser, AuthGateway
from app.auth.events import UserCreated, UserDeleted
from app.auth.schemas.user import UserDTO
from app.auth.routers import router_v1

__all__ = [
    'router_v1',
    'CurrentUser',
    'ActiveUser',
    'AuthGateway',
    'UserDTO',
    'UserCreated',
    'UserDeleted'
]
```

And finally in any other module we can retrieve it from FastAPI DI system and make a call:

```python
from app.auth import AuthGateway

@router.get('/comments/{comment_id}')
async def get(auth_gateway: AuthGateway) -> Response:
    ...
    user = auth_gateway.get_user(user_id)
    ...
```

In such a project structure, the module should expose only dependencies, entity DTOs, events and routers. It would be a more clear approach if we could expose only `AuthGateway` dependency to keep all external logic of our module in one place, but I want to leverage the power of the FastAPI DI system, so I also expose `ActiveUser` and `CurrentUser` dependencies. But we will still do all external call to our module through one entry point - our Gateway.

My preference is not to maximize the level of abstraction wherever we can, but to strike a healthy balance between the level of abstraction and simplicity. The main thing is that the chosen approach should meet our specific needs for the project and allow us to easily refactor and scale our code in the long run.

Another interesting thing that Gateway allows us to do is that if we decide to take our module to a separate microservice in the future, we only need to implement a new version of Gateway that will make HTTP requests to the external microservice. Pretty the same we will have to do with `CurrentUser`, `ActiveUser` and events. We are exposing here only `UserDTO`, not the users model, so we don't have to change too much here, just pack response into `UserDTO` and return. Meanwhile, other modules interacting with our module will feel no difference and continue to work as before.

## Services

### Events service. Async cross-module communication.

**Used:**

- Event dispatching/handling: [fastapi-events](https://github.com/melvinkcx/fastapi-events)

**Key Notes:**

- All Events should be placed into `events.py` and Listeners into `listeners.py` of each module.
- `@listener` decorator from `app.core.deps` should be used to define the event listener.
- All `listeners.py` from our modules should be imported in `app.core.listeners.py` .This will make listeners work properly.
- `EventsService` dependency from `app.core.deps` should be used to retrieve an instance that implements `app.core.services.events.EventsServiceInterface` from FastAPI DI system.
- To create Event we have to create child class from `app.core.services.events.BaseEvent` and define our event’s fields. `BaseEvent` just inherit Pydantic `BaseModel`, so probably you already know how to deal with it.

Events Service built on top of the `fastapi-events`. This library is the closest in interface to what I wanted to get, so I'll stick with it. But you can implement another provider if you need it.

This is implementation of the async event-driven communication between our modules. We have Events and Listeners. We can dispatch Events from one module and execute any business logic in response to this event (our Listeners) from any modules of our application completely independently. This is probably the best level of abstraction between modules, which is very cool in theory, but it is very difficult to use only this approach in real-world application.

This approach will also allow us to transition relatively easily to using message brokers like RabbitMQ, Redis or Kafka if we decide to make our module a separate microservice in the future.

Event can look like this:

```python
class UserCreated(BaseEvent):
    __event_name__ = 'user_created'

    id: int
    email: EmailStr
    username: str
```

To create Listener we should utilize the `@listener` decorator and pass the Event class we want to listen to:

```python
@listener(UserCreated)
async def user_created_listener(event: ListenedEvent) -> None:
    print(event)
```

As a parameter in a Listener `app.core.services.events.ListenedEvent` object will be passed. It’s just simple `dataclass` with event name and data fields:

```python
@dataclass
class ListenedEvent:
    name: str
    data: Any
```

To dispatch the Event we should use `EventsService` :

```python
from app.core.deps import EventsService

@router.get('/')
async def index(events_service: EventsService) -> Response:
    ...
    events_service.dispatch(UserCreated(**user.to_dict()))
    ...
```

### Cache service

**Used:**

- Async caching tool: [aiocache](https://github.com/aio-libs/aiocache)
- Storage provider: [Redis](https://redis.io)

**Key Notes:**

- `@cached` decorator from `app.core.deps` should be used to add caching for path operation function.
- `CacheService` dependency from `app.core.deps` should be used to retrieve an instance that implements `app.core.services.cache.CacheServiceInterface` from FastAPI DI system.

This is just typical cache service that provides a convenient way to cache path operation functions:

```python
from app.core.deps import cached

@app.get("/items/{item_id}")
@cached(ttl=60, key_builder=lambda f, *args, **kwargs: f"item:{kwargs['item_id']}")
async def get(item_id: int):
    ...
```

As well as any arbitrary data:

```python
from app.core.deps import CacheService

@router.get('/')
async def index(cache_service: CacheService) -> Response:
    ...
    cache_service.set(key='key', value='value', ttl=60)
    ...
    cache_service.get('key')
    ...
    cache_service.delete('key')
```

### Queue service

**Used:**

- Async distributed task manager: [Taskiq](https://taskiq-python.github.io)
- Taskiq Redis broker: [Taskiq-Redis](https://github.com/taskiq-python/taskiq-redis)
- Message broker: [Redis](https://redis.io)

**Key Notes:**

- `@queued` decorator from `app.core.deps` should be used to define the queue task.
- Each queue task should be inherited from `app.core.services.queue.BaseTask`, has a `__task_name__` attribute and implements `run(...)` method.
- `QueueService` dependency from `app.core.deps` should be used to retrieve an instance that implements `app.core.services.queue.QueueServiceInterface` from FastAPI DI system.
- All module tasks should be placed into `tasks.py` in our module. Then we should import `tasks.py` from our modules into `app.core.tasks.py` to make them visible for queue workers.

Here is how queue tasks might look like:

```python
from app.core.deps import queued
from app.core.services.queue import BaseTask

@queued
class SendEmail(BaseTask):
    __task_name__ = 'mail.send'

    async def run(self, content: str, email_data: dict) -> None:
        ...
        message = EmailMessage()  
        ... 
  
        await aiosmtplib.send(message, **smtp_config)
```

To send it to the queue we should use `QueueService`:

```python
from app.core.deps import QueueService

@router.get('/')
async def index(queue_service: QueueService) -> Response:
    ...
    await queue_service.push(
        task=SendEmail,  
        data={'content': template.render(), 'email_data': email_data},
    )
```

### Mail service

**Used:**

- Async email handling: [aiosmtplib](https://aiosmtplib.readthedocs.io/en/stable)
- Test SMTP server: [MailHog](https://github.com/mailhog/MailHog)
- Template engine: [Jinja2](https://jinja.palletsprojects.com)

**Key Notes:**

- `MailService` dependency from `app.core.deps` should be used to retrieve an instance that implements `app.core.services.mail.MailServiceInterface` from FastAPI DI system.
- Each email template should inherit `app.core.services.mail.BaseTemplate` and implement `_get_dir(...)` and `_get_name(...)` methods.
- All email template classes should be placed into `emails.templates.py` in each module. Actual HTML templates should be placed in the `emails.views` directory.
- Mail sending operation can be executed in the background using `QueueService`.

An email template class example:

```python
from app.core.services.mail import BaseTemplate

class UserRegistration(BaseTemplate):
    def __init__(self, username: str, project_name: str):
        self.username = username
        self.project_name = project_name
        
    def _get_dir(self) -> Path:
        return Path('app/auth/emails/views')

    def _get_name(self) -> str:
        return 'user_registration.html'
```

And HTML template `user_registration.html`:

```python
<h1> Hello {{ username }}!</h1>

<p>You have successfully registered on <b>{{ project_name }}</b>.</p>
<p>Thank you and welcome to your new account!</p>
```

To send an email we should use `MailService`:

```python
from app.core.services.mail import EmailData
from app.core.deps import MailService

@router.get('/')
async def index(mail_service: MailService) -> Response:
    ...
    email_data = EmailData(subject='Successful registration', recipient=user.email)
    template = UserRegistration(username=user.username, project_name=app_config.PROJECT_NAME)
    self._mail.send(template=template, email_data=email_data)
    
    # Or to send on background using QueueService
    self._mail.queue(template=template, email_data=email_data)
```

### Logging service

**Used:**

- Logging solution: [structlog](https://www.structlog.org/en/stable)

**Key Notes:**

- We can customize structlog configuration in `app/core/config/structlog.py` .
- `logger` instance is designed as a Singleton that implements `app.core.services.log.LogServiceInterface` and can be found in `app.core.deps.py`.
- Both sync and async methods can be used.

The `logger` can be used in this way:

```python
from app.core.deps import logger

await logger.a_info('Something happened')
```

## Modules

### **Authorization**/**Authentication** module.

**Used:**

- JWT manipulations: [PyJWT](https://pyjwt.readthedocs.io/en/stable)
- Hashing: [PassLib](https://passlib.readthedocs.io/en/stable)

**Key Notes**:

- Login endpoint:
    - **POST** `/auth/login`.
- Registration endpoint:
    - **POST** `/auth/register`.
- Tokens refreshing endpoint:
    - **POST** `/auth/refresh-token`.
- Password restoration endpoints:
    - **POST** `/auth/restore-password`
    - **POST**`/auth/reset-password`
- Users CRUD endpoints:
    - **GET** `/users?sort=id:desc,username:asc&page=1&per_page=3&filters=id:[1,2]`
    - **GET** `/users/2`
- Profile CRUD endpoints:
    - **GET** `/profile`
    - **PATCH** `/profile`
    - **DEL** `/profile`
- Dependencies `CurrentUser` and `ActiveUser` should be used for retrieving current user by access_token in headers in path operation function.
- Gateway dependency `AuthGateway` provides centralized access to the module functions.
- Module provides basic events `UserCreated`, `UserDeleted` on which any module can subscribe.

Auth module implements basic authorization/authentication logic based on JWT tokens. It is located in the `app.auth` directory. In `app.auth.__init__.py` we can find what is explicitly exposed from the module and what can be used to communicate with it.

## Development Environment and Tooling

### Package manager and deployment

**Used:**

- Package manager: [Poetry](https://python-poetry.org)
- Development environment: [Docker](https://www.docker.com) and [Docker Compose](https://docs.docker.com/compose)

> [!WARNING]
> This environment is designed for convenient local development and is not optimized for production. Please do not use these `docker-compose.yaml` and `Dockerfile` on your production servers.

**Getting started**

1. Install Docker and Docker Compose.
2. Copy `.sample.env` into `.env` and update configuration parameters.
3. Build app image `docker compose build`
4. Run server `docker compose up -d`

**Check the app logs**
- `docker compose logs app`

**Create Alembic migrations locally**

- `docker compose exec app alembic revision --autogenerate -m "create some table."`

### Static code analyzers, linters and formatters

**Used:**

- Linter and code formatter: [Ruff](https://docs.astral.sh/ruff)
- Type checker: [mypy](https://mypy-lang.org)

**Key Notes:**
- `Ruff` helps to follow the best code style practices, while `mypy` ensures that all types are used properly.
- We can customize configuration for `Ruff` and `mypy` in `pyproject.toml`

**Ruff**

- For linter check only: `ruff check .`
- For linter check and fix: `ruff check --fix .`
- For formatting: `ruff format .`

**mypy**

- `mypy .`.

### Testing

**Used:**

- Test framework: [pytest](https://docs.pytest.org/en/stable)
- Environment management: [pytest-dotenv](https://pypi.org/project/pytest-dotenv)
- AsyncIO support: [pytest-asyncio](https://pypi.org/project/pytest-asyncio)
- Fake data generator: [Faker](https://faker.readthedocs.io/en/master)
- Factories: [Factory Boy](https://factoryboy.readthedocs.io/en/stable)
- Datetime mocking: [freezegun](https://github.com/spulec/freezegun)
- Data validation: [Cerberus](https://docs.python-cerberus.org)
- Tests coverage: [Coverage.py](https://coverage.readthedocs.io/en/7.6.1)
- Async HTTP client: [HTTPX](https://www.python-httpx.org/)

**Key Notes:**

- `.test.env` is used to override main environment parameters from `.env` for testing environment.
- All database tables are created once before all tests and dropped once after all tests accordingly to speed up test execution, so you have to handle cleaning for tables that you need in `db` fixture in `tests/conftest.py`.
- To login users in your integration tests `tests.utils.login_user` helper can be used.
- All factories must inherit `tests.factories.async_alchemy_factory.AsyncSQLAlchemyModelFactory` This class extends `factory.alchemy.SQLAlchemyModelFactory` and adds the support for async database sessions.
-  We can customize configuration for `pytest` in `pyproject.toml`

**pytest**

- `docker compose exec app pytest` to run all tests.
- `docker compose exec app pytest -v -s` to run tests with extended info and stdout.
- `docker compose exec app pytest tests/auth/unit/repositories/test_user.py` to run tests from specific file.

**Coverage**

- `docker compose exec app coverage run -m pytest` to run tests with coverage.
- `docker compose exec app coverage report` to generate coverage report.
- `docker compose exec app coverage html` to generate more detailed HTML report.