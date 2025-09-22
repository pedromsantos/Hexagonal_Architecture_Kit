# Domain Driven Design with Ports & Adapters Rules

## TL;DR: How DDD and Ports & Adapters Work Together

This document defines two complementary architectural approaches that work together to create maintainable, testable applications:

### The Integration Pattern

**Core Domain Model** (Rules 1-14) focuses on business logic and domain concepts:

- **Entities** (Rule 1) contain business behavior and have unique identity
- **Value Objects** (Rule 2) represent immutable domain concepts
- **Aggregates** (Rule 3) enforce business invariants and transaction boundaries
- **Domain Services** (Rule 4) handle business logic spanning multiple entities
- **Use Cases** (Rule 9) orchestrate domain objects without containing business logic

**Ports & Adapters** (Rules 1-12) focuses on architectural boundaries and external concerns:

- **Primary Ports** define what your application can do (use case interfaces)
- **Secondary Ports** define what your application needs (repositories, external services)
- **Primary Adapters** translate external requests into domain operations (REST controllers, CLI)
- **Secondary Adapters** implement external integrations (databases, APIs, file systems)

### How They Connect in Practice

```python
# 1. Domain Layer (DDD Core)
class User(Entity):                    # Rule 1: Entity with identity
    def change_email(self, email: Email) -> UserEmailChanged:
        # Business logic here
        return UserEmailChanged(self.id, self.email, email)

class UserRepository(ABC):             # Rule 5: Domain port for persistence
    def save(self, user: User) -> None: pass

# 2. Application Layer (Bridge between DDD and Ports & Adapters)
class ChangeUserEmailUseCase(ChangeUserEmailPort):  # Rule 9 + P&A Rule 1
    def __init__(self,
                 user_repo: UserRepository,           # Domain port
                 email_service: EmailNotificationPort, # Infrastructure port
                 time_provider: TimeProviderPort):     # Infrastructure port
        self._user_repo = user_repo
        self._email_service = email_service
        self._time_provider = time_provider

    def execute(self, command: ChangeEmailCommand) -> None:
        # Orchestrate domain objects (Rule 9)
        user = self._user_repo.find_by_id(command.user_id)
        event = user.change_email(Email(command.new_email))

        # Use infrastructure ports for side effects
        self._user_repo.save(user)
        self._email_service.send_email_change_notification(
            event.old_email, event.new_email, self._time_provider.now()
        )

# 3. Infrastructure Layer (Ports & Adapters Implementation)
class SqlUserRepository(UserRepository):      # P&A Rule 3: Secondary adapter
    def save(self, user: User) -> None:
        # Handle ORM mapping, database specifics

class RestUserController:                     # P&A Rule 2: Primary adapter
    def patch_user_email(self, user_id: str, request: ChangeEmailRequest):
        command = ChangeEmailCommand(user_id, request.email)
        self._use_case.execute(command)        # Delegate to use case
```

### Key Integration Principles

1. **Domain Objects** (Entities, Value Objects, Aggregates) contain business logic and know nothing about persistence or external systems

2. **Use Cases** orchestrate domain objects and coordinate with external systems through **Secondary Ports**

3. **Primary Adapters** translate external requests into domain commands and delegate to **Use Cases** through **Primary Ports**

4. **Secondary Adapters** implement **Secondary Ports** and handle all external system complexity (databases, APIs, file systems, etc.)

5. **Dependency Flow**: External → Primary Adapter → Use Case → Domain Objects → Secondary Ports → Secondary Adapters

This creates a clean separation where:

- **Business logic** lives in domain objects (DDD)
- **Orchestration** lives in use cases (DDD + P&A bridge)
- **External concerns** are isolated in adapters (P&A)
- **Interfaces** define clear contracts between layers (P&A)

---

## Core Domain Model Rules

### 1. Entity Rules

- Entities MUST have a unique identity that persists throughout their lifecycle
- Identity should be immutable once set
- Implement `equality` and `hash` based solely on identity, not attributes/fields
- Entities MUST contain business logic as methods, not just data
  - Avoid anemic domain models - entities should have behavior
- Include validation in constructor

```python
@dataclass
class User:
    id: UserId = field(init=False)
    email: Email
    name: str

    def __post_init__(self):
        if not hasattr(self, 'id'):
            self.id = UserId.generate()

    def change_email(self, new_email: Email) -> None:
        # Business logic here
        self.email = new_email
```

### 2. Value Object Rules

- Value objects MUST be immutable
- Equality is based on ALL attributes, not identity
- Should be small, focused, and represent a concept from the domain
- Include validation in constructor
- Should have meaningful methods that operate on the value

```python
@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if '@' not in self.value:
            raise ValueError("Invalid email format")

    @property
    def domain(self) -> str:
        return self.value.split('@')[1]
```

### 3. Aggregate Rules

Aggregates are clusters of domain objects that are treated as a single unit. Ensure that all changes to the domain model are done through aggregates. This means that Entities are not directly modified, but rather through the Aggregate Root

- Aggregates MUST have a single Aggregate Root (an Entity)
- Only the Aggregate Root should be directly accessible from outside
- Internal entities within an aggregate should be accessed only through the root
- Aggregate boundaries should align with transaction boundaries
- Use factory methods on aggregates for complex creation logic
- Aggregates should be small and focused
- The root Entity has global identity and is ultimately responsible for checking invariants
- Root Entities have global identity. Entities inside the boundary have local identity, unique only within the Aggregate.
- Nothing outside the Aggregate boundary can hold a reference to anything inside, except to the root Entity. The root Entity can hand references to the internal Entities to other objects, but they can only use them transiently (within a single method or block).
- Only Aggregate Roots can be obtained directly with database queries. Everything else must be done through traversal.
- Objects within the Aggregate can hold references to other Aggregate roots.
- A delete operation must remove everything within the Aggregate boundary all at once
- When a change to any object within the Aggregate boundary is committed, all invariants of the whole Aggregate must be satisfied.
- Hide Internal State: Keep the internal state of the aggregate private and provide methods to interact with the state safely
- Encapsulate Collections: Use first class collection from Object Calisthenics

```python
@dataclass
class Order:  # Aggregate Root
    id: OrderId
    customer_id: CustomerId
    _line_items: list[OrderLineItem] = field(default_factory=list, init=False)

    def add_line_item(self, product_id: ProductId, quantity: int) -> None:
        # Business rules and validation
        line_item = OrderLineItem(product_id, quantity)
        self._line_items.append(line_item)

    @property
    def line_items(self) -> tuple[OrderLineItem, ...]:
        return tuple(self._line_items)  # Return immutable view
```

### 4. Domain Service Rules

Handles business logic that spans multiple entities (e.g., transferring money between two accounts)

- Create domain services ONLY when business logic doesn't naturally fit in entities or value objects
- Domain services should be stateless
- Use dependency injection for external dependencies
- Should operate on domain objects, not primitives
- Should not use Driven ports/adapters
- Name services with domain language (not technical terms)

```python
class PricingService:
    def __init__(self, discount_repository: DiscountRepository):
        self._discount_repository = discount_repository

    def calculate_order_total(self, order: Order, customer: Customer) -> Money:
        # Complex pricing logic that spans multiple aggregates
        pass
```

## Repository Pattern Rules

### 5. Repository Interface Rules

- Define repository interfaces in the domain layer using ABC - they represent domain concepts
- Repositories should work with Aggregate Roots only
- Use domain-specific query methods, not generic CRUD
- Return domain objects, never DTOs or database models
- Input should be Aggregates not entities, value objects or DTO's
- Should throw domain exceptions, not infrastructure exceptions

```python
# Domain Layer - domain/repositories/user_repository.py
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        pass

    @abstractmethod
    def save(self, user: User) -> None:
        pass

    @abstractmethod
    def find_active_users_in_department(self, department_id: DepartmentId) -> list[User]:
        pass

    @abstractmethod
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        pass
```

### 6. Repository Implementation Rules

- Implement repositories in the infrastructure layer
- Use the Unit of Work pattern for transaction management
- Map between domain objects and persistence models
- Handle optimistic concurrency using version fields
- Repository should not contain business logic

## Domain Event Rules

### 7. Domain Event Rules

- Domain events should be immutable value objects
- Events should represent something that happened in the past (use past tense)
- Events should contain all necessary data to handle the event
- Use `@dataclass(frozen=True)` for events
- Events should be raised by aggregates, not external code

```python
@dataclass(frozen=True)
class UserEmailChanged:
    user_id: UserId
    old_email: Email
    new_email: Email
    occurred_at: datetime
```

### 8. Event Handling Rules

- Domain event handlers should be in the application layer
- Handlers should be idempotent
- Use dependency injection for handler dependencies
- Handlers should not directly modify other aggregates
- Consider eventual consistency for cross-aggregate operations

## Application Service Rules

### 9. Use Case Rules

- Use cases represent single business operations that the application can perform
- Each use case should handle exactly one business workflow
- Use cases orchestrate domain objects but contain no business logic
- Should be stateless and focused on a single responsibility
- Handle cross-cutting concerns (transactions, events, etc.)
- Should not return domain objects directly - use DTOs
- Name use cases after business operations using domain language

```python
class CreateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work
        self._event_publisher = event_publisher

    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        with self._unit_of_work:
            # Orchestration logic only
            email = Email(command.email)
            user = User.create(email, command.name)
            self._user_repository.save(user)
            self._event_publisher.publish(UserCreated(user.id, email))
            return CreateUserResponse(user.id.value)

class ChangeUserEmailUseCase:
    def __init__(self, user_repository: UserRepository, unit_of_work: UnitOfWork):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    def execute(self, command: ChangeEmailCommand) -> None:
        with self._unit_of_work:
            user = self._user_repository.find_by_id(command.user_id)
            if not user:
                raise UserNotFoundError(command.user_id)
            user.change_email(Email(command.new_email))
            self._user_repository.save(user)
```

### 10. Event Integration Rules

- Domain events should be published through infrastructure ports
- Event handlers can be implemented as separate use cases
- Use event-driven architecture for cross-bounded context communication
- Events enable loose coupling between adapters and domain logic
- Consider eventual consistency for distributed operations

```python
# Event Publishing through Infrastructure Port
class EventPublisherPort(ABC):  # Application layer
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        pass

class CreateUserUseCase(CreateUserPort):
    def __init__(
        self,
        user_repo: UserRepository,  # Domain port
        event_publisher: EventPublisherPort  # Infrastructure port
    ):
        self._user_repo = user_repo
        self._event_publisher = event_publisher

    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        user = User.create(Email(command.email), command.name)
        self._user_repo.save(user)  # Domain port
        self._event_publisher.publish(UserCreated(user.id, user.email))  # Infrastructure port
        return CreateUserResponse(user.id.value)

# Event Handler as Use Case
class SendWelcomeEmailUseCase:
    def __init__(self, email_service: EmailNotificationPort):  # Infrastructure port
        self._email_service = email_service

    def handle(self, event: UserCreated) -> None:
        self._email_service.send_welcome_email(event.email, event.name)
```

## Validation and Error Handling Rules

- Test domain logic in isolation without any adapters
- Test primary adapters by mocking primary ports
- Test secondary adapters by mocking external dependencies
- Use in-memory implementations of secondary ports for integration tests
- Test the full flow from primary adapter to secondary adapter for end-to-end tests

```python
# Testing with port isolation
class TestUserManagementService:
    def test_create_user_success(self):
        # Arrange
        mock_repo = Mock(spec=UserRepository)
        mock_events = Mock(spec=EventPublisherPort)
        service = UserManagementService(mock_repo, mock_events)

        # Act
        result = service.create_user(CreateUserCommand("test@example.com", "John"))

        # Assert
        mock_repo.save.assert_called_once()
        mock_events.publish.assert_called_once()
        assert isinstance(result.user_id, str)

# In-memory adapter for testing
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users: dict[UserId, User] = {}

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def find_by_email(self, email: Email) -> Optional[User]:
        return next((u for u in self._users.values() if u.email == email), None)
```

### 11. Validation and Error Handling Rules

- Domain validation should happen in domain objects (entities, value objects)
- Use domain exceptions that extend a base domain exception
- Validation should be explicit and fail fast
- Input validation in application services should be minimal
- Use factory methods for complex validation scenarios

```python
class DomainException(Exception):
    pass

class InvalidEmailError(DomainException):
    pass

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise InvalidEmailError(f"Invalid email: {self.value}")
```

### 12. Naming Convention Rules

- Use domain language (Ubiquitous Language) for all class and method names
- Avoid technical terms in domain layer (no "Manager", "Helper", "Util")
- Use intention-revealing names for methods
- Value objects should be named after the concept they represent
- Repository methods should reflect business queries
- **Port Naming**: End primary ports with "Port", secondary ports with "Port"
- **Adapter Naming**: Include the technology/framework in secondary adapter names
- **Clear Port vs Adapter distinction**: Ports define interfaces, Adapters implement them

```python
# Good port names
class UserManagementPort(ABC): pass           # Primary port
class EmailNotificationPort(ABC): pass       # Secondary port
class PaymentProcessingPort(ABC): pass       # Secondary port

# Good adapter names
class RestUserController:                    # Primary adapter (REST)
class GraphQLUserController:                 # Primary adapter (GraphQL)
class SqlUserRepository(UserRepository):     # Secondary adapter (SQL)
class MongoUserRepository(UserRepository):   # Secondary adapter (MongoDB)
class SmtpEmailAdapter(EmailNotificationPort): # Secondary adapter (SMTP)
class SendGridEmailAdapter(EmailNotificationPort): # Secondary adapter (SendGrid)
```

### 13. Dependency Rules

- Domain layer should have no external dependencies except standard library
- Application layer can depend on domain but should use dependency inversion for external concerns
- Infrastructure layer implements all external dependencies through adapters
- **Domain Port Dependencies**: Domain objects can depend on domain ports (repositories, domain services)
- **Infrastructure Port Dependencies**: Use cases depend on infrastructure ports for external concerns
- **Port Placement**: Domain ports in domain layer, infrastructure ports in application layer
- **Inversion of Control**: Use DI container to wire adapters to ports at startup
- Use dependency inversion - depend on abstractions, not concretions
- Inject dependencies through constructors
- Use factory pattern for complex object creation

```python
# Domain layer - can depend on domain ports
class User:  # Domain entity
    def __init__(self, id: UserId, email: Email, name: str):
        self.id = id
        self.email = email
        self.name = name

    def change_email(self, new_email: Email) -> None:
        # Business logic here
        self.email = new_email

class UserDomainService:  # Domain service
    def __init__(self, user_repo: UserRepository):  # Domain port dependency
        self._user_repo = user_repo

    def is_email_unique(self, email: Email) -> bool:
        existing_user = self._user_repo.find_by_email(email)
        return existing_user is None

# Application layer - depends on domain + infrastructure ports
class CreateUserUseCase(CreateUserPort):
    def __init__(
        self,
        user_repo: UserRepository,  # Domain port
        user_domain_service: UserDomainService,  # Domain service
        email_service: EmailNotificationPort,  # Infrastructure port
        event_publisher: EventPublisherPort  # Infrastructure port
    ):
        self._user_repo = user_repo
        self._user_domain_service = user_domain_service
        self._email_service = email_service
        self._event_publisher = event_publisher

# Infrastructure layer - implements ports with external dependencies
class SqlUserRepository(UserRepository):  # Implements domain port
    def __init__(self, session: SqlAlchemySession):  # External dependency
        self._session = session

class SmtpEmailAdapter(EmailNotificationPort):  # Implements infrastructure port
    def __init__(self, smtp_client: SMTPClient):  # External dependency
        self._smtp_client = smtp_client
```

### 14. Testing Rules

- Write unit tests for domain logic without mocking domain objects
- **Test Ports in Isolation**: Mock secondary ports when testing use cases
- **Test Adapters Separately**: Test each adapter implementation independently
- **Integration Testing**: Use in-memory adapters for full workflow testing
- Test domain events are raised correctly
- Integration tests should test aggregate boundaries
- Use builders or factories for test data creation
- **Contract Testing**: Ensure all adapter implementations satisfy their port contracts
- **Use Case Testing**: Test each use case independently with mocked dependencies

```python
# Contract test for all UserRepository implementations
class UserRepositoryContractTest:
    def test_save_and_find_user(self, repository: UserRepository):
        # This test should pass for SqlUserRepository, MongoUserRepository, etc.
        user = User.create(Email("test@example.com"), "John")
        repository.save(user)
        found = repository.find_by_email(Email("test@example.com"))
        assert found is not None
        assert found.email == user.email

# Use Case Integration Test
class TestCreateUserUseCaseIntegration:
    def test_full_workflow_with_in_memory_adapters(self):
        # Arrange
        user_repo = InMemoryUserRepository()
        email_service = InMemoryEmailService()
        event_publisher = InMemoryEventPublisher()
        use_case = CreateUserUseCase(user_repo, email_service, event_publisher)

        # Act
        result = use_case.execute(CreateUserCommand("test@example.com", "John"))

        # Assert
        assert result.user_id is not None
        saved_user = user_repo.find_by_email(Email("test@example.com"))
        assert saved_user is not None
        assert len(email_service.sent_emails) == 1
        assert len(event_publisher.published_events) == 1

# Technology-specific adapter testing
class TestSqlUserRepository:
    def test_save_user_with_sql_models(self):
        # Arrange
        session = create_test_sql_session()
        repository = SqlUserRepository(session)
        user = User.create(Email("test@example.com"), "John")

        # Act
        repository.save(user)

        # Assert
        saved_user = repository.find_by_email(Email("test@example.com"))
        assert saved_user is not None
        assert saved_user.email == user.email

        # Verify SQL model was created correctly
        user_model = session.query(UserModel).filter_by(email="test@example.com").first()
        assert user_model is not None
        assert user_model.name == "John"

class TestMongoUserRepository:
    def test_save_user_with_mongo_schemas(self):
        # Arrange
        mongo_client = create_test_mongo_client()
        repository = MongoUserRepository(mongo_client)
        user = User.create(Email("test@example.com"), "John")

        # Act
        repository.save(user)

        # Assert
        saved_user = repository.find_by_email(Email("test@example.com"))
        assert saved_user is not None
        assert saved_user.email == user.email
```

## Ports & Adapters (Hexagonal Architecture) Rules

### 1. Port Definition Rules

- Ports define interfaces between layers and external systems
- **Primary ports** (driving) define application use cases - belong in application layer
- **Domain-driven secondary ports** (repositories, domain services) - belong in domain layer
- **Infrastructure secondary ports** (email, messaging, external APIs) - belong in application layer
- Port interfaces should use domain language, not technical terms
- Ports should be focused and follow Single Responsibility Principle

```python
# Primary Ports (Application Layer) - application/ports/primary/
class CreateUserPort(ABC):
    @abstractmethod
    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        pass

class ChangeUserEmailPort(ABC):
    @abstractmethod
    def execute(self, command: ChangeEmailCommand) -> None:
        pass

# Domain-Driven Secondary Ports (Domain Layer) - domain/repositories/
class UserRepository(ABC):  # Already shown in rule 5
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        pass

# Domain Services (Domain Layer) - domain/services/
class PricingServicePort(ABC):
    @abstractmethod
    def calculate_product_price(self, product: Product, customer: Customer) -> Money:
        pass

# Infrastructure Secondary Ports (Application Layer) - application/ports/secondary/
class EmailNotificationPort(ABC):
    @abstractmethod
    def send_welcome_email(self, user_email: Email, user_name: str) -> None:
        pass

    @abstractmethod
    def send_email_change_notification(self, old_email: Email, new_email: Email) -> None:
        pass

class EventPublisherPort(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        pass
```

### 2. Primary Adapter Rules

- Primary adapters are the entry points (web controllers, CLI, message consumers)
- Should translate external requests to domain commands/queries
- Must not contain business logic - only translation and validation
- Should handle framework-specific concerns (HTTP status codes, serialization)
- Should be thin and delegate to use cases through primary ports

```python
# FastAPI Controller (Primary Adapter)
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    email: str
    name: str

class ChangeEmailRequest(BaseModel):
    email: str

class CreateUserResponse(BaseModel):
    user_id: str

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserPort = Depends()
) -> CreateUserResponse:
    try:
        command = CreateUserCommand(
            email=request.email,
            name=request.name
        )
        response = use_case.execute(command)
        return CreateUserResponse(user_id=response.user_id)
    except InvalidEmailError as e:
        raise HTTPException(status_code=400, detail=f"Invalid email: {str(e)}")
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{user_id}/email", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_email(
    user_id: str,
    request: ChangeEmailRequest,
    use_case: ChangeUserEmailPort = Depends()
) -> None:
    try:
        command = ChangeEmailCommand(
            user_id=UserId(user_id),
            new_email=request.email
        )
        use_case.execute(command)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except InvalidEmailError as e:
        raise HTTPException(status_code=400, detail=f"Invalid email: {str(e)}")
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=GetUserResponse)
async def get_user(
    user_id: str,
    use_case: GetUserPort = Depends()
) -> GetUserResponse:
    try:
        query = GetUserQuery(user_id=UserId(user_id))
        response = use_case.execute(query)
        return GetUserResponse(
            user_id=response.user_id,
            email=response.email,
            name=response.name
        )
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    use_case: DeactivateUserPort = Depends()
) -> None:
    try:
        command = DeactivateUserCommand(user_id=UserId(user_id))
        use_case.execute(command)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except UserAlreadyDeactivatedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 3. Secondary Adapter Rules

- Secondary adapters implement secondary ports defined in domain/application layers
- Organize secondary adapters by technology for shared infrastructure and easier maintenance
- Should handle all external system complexities (database mapping, API calls, etc.)
- Must translate between domain objects and external representations
- Should not expose external system details to the domain
- Include error handling and retry logic when appropriate
- Keep technology-specific models/schemas within their adapter implementations

```python
# SQL Database Adapter - infrastructure/adapters/secondary/sql/sql_user_repository.py
class SqlUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, user: User) -> None:
        user_model = UserModel(
            id=user.id.value,
            email=user.email.value,
            name=user.name,
            version=user.version
        )
        self._session.merge(user_model)

    def find_by_email(self, email: Email) -> Optional[User]:
        model = self._session.query(UserModel).filter_by(email=email.value).first()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=UserId(model.id),
            email=Email(model.email),
            name=model.name
        )

# HTTP External Service Adapter - infrastructure/adapters/secondary/http/http_email_service.py
class HttpEmailNotificationAdapter(EmailNotificationPort):
    def __init__(self, http_client: HTTPClient, api_config: EmailAPIConfig):
        self._http_client = http_client
        self._api_config = api_config

    def send_welcome_email(self, user_email: Email, user_name: str) -> None:
        payload = {
            'to': user_email.value,
            'template': 'welcome',
            'variables': {'name': user_name}
        }
        response = self._http_client.post(
            f"{self._api_config.base_url}/send",
            json=payload,
            headers={'Authorization': f'Bearer {self._api_config.api_key}'}
        )
        if response.status_code != 200:
            raise EmailDeliveryError(f"Failed to send email: {response.text}")
```

### 4. Adapter Configuration Rules

- Use Dependency Injection container to wire adapters to ports
- Configuration should happen at application startup in a composition root
- Adapters should be configurable through environment variables or config files
- Use factory patterns for complex adapter creation
- Keep configuration separate from business logic
- Configuration layer manages all technology-specific adapter instantiation

```python
# Configuration Layer - configuration/di_container.py
class DIContainer:
    def __init__(self, config: Config):
        self._config = config
        self._sql_session = self._create_sql_session()
        self._mongo_client = self._create_mongo_client()
        self._http_client = self._create_http_client()

    # Domain port implementations (SQL technology)
    def sql_user_repository(self) -> UserRepository:
        return SqlUserRepository(self._sql_session)

    # Domain port implementations (MongoDB technology)
    def mongo_user_repository(self) -> UserRepository:
        return MongoUserRepository(self._mongo_client)

    # Infrastructure port implementations
    def http_email_notification_service(self) -> EmailNotificationPort:
        return HttpEmailNotificationAdapter(
            self._http_client,
            self._config.email_api_config
        )

    def rabbitmq_event_publisher(self) -> EventPublisherPort:
        return RabbitMqEventPublisher(
            connection=self._create_rabbitmq_connection()
        )

    # Use case implementations
    def create_user_use_case(self) -> CreateUserPort:
        return CreateUserUseCase(
            user_repository=self.sql_user_repository(),  # Choose technology
            email_service=self.http_email_notification_service(),
            event_publisher=self.rabbitmq_event_publisher(),
            unit_of_work=UnitOfWork(self._sql_session)
        )
```

### 5. Integration Flow Rules

- Primary adapters call primary ports (use cases)
- Use cases orchestrate domain objects and use secondary ports for external systems
- Secondary adapters implement secondary ports and handle external complexities
- Domain objects should never directly depend on adapters
- Use events for loose coupling between bounded contexts

```python
# Flow Example: Web Request → Controller → Use Case → Repository
class UserController:  # Primary Adapter
    def create_user(self, request) -> Response:
        command = CreateUserCommand(request.email, request.name)
        response = self._create_user_use_case.execute(command)  # → Primary Port
        return Response(201, {'user_id': response.user_id})

class CreateUserUseCase(CreateUserPort):  # Primary Port Implementation
    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        email = Email(command.email)
        user = User.create(email, command.name)
        self._user_repository.save(user)  # → Secondary Port
        self._email_service.send_welcome_email(email, command.name)  # → Secondary Port
        return CreateUserResponse(user.id.value)
```

### 6. Repository as Secondary Port Rules

- Repository interfaces are domain ports (interfaces in domain layer)
- Repository implementations are secondary adapters (in infrastructure layer)
- Repositories should work with Aggregate Roots and use domain language
- Repository adapters handle ORM mapping and database specifics
- Keep repository interfaces focused on domain needs, not database capabilities

### 7. Time Abstraction Adapter Rules

- Abstract system time through secondary ports to enable testing and deterministic behavior
- Time ports should be infrastructure concerns, not domain concerns
- Use domain-appropriate time concepts (business hours, deadlines, schedules)
- Enable easy mocking and testing of time-dependent business logic

```python
# Infrastructure Secondary Port (Application Layer) - application/ports/secondary/
class TimeProviderPort(ABC):
    @abstractmethod
    def now(self) -> datetime:
        pass

    @abstractmethod
    def today(self) -> date:
        pass

    @abstractmethod
    def business_hours_start(self, date: date) -> datetime:
        pass

# Infrastructure Adapter Implementation
class SystemTimeProvider(TimeProviderPort):
    def __init__(self, timezone: str = "UTC"):
        self._timezone = ZoneInfo(timezone)

    def now(self) -> datetime:
        return datetime.now(self._timezone)

    def today(self) -> date:
        return date.today()

    def business_hours_start(self, date: date) -> datetime:
        return datetime.combine(date, time(9, 0), self._timezone)

# Test Implementation
class FixedTimeProvider(TimeProviderPort):
    def __init__(self, fixed_time: datetime):
        self._fixed_time = fixed_time

    def now(self) -> datetime:
        return self._fixed_time

    def today(self) -> date:
        return self._fixed_time.date()
```

### 8. File System Adapter Rules

- Abstract file system operations through secondary ports for testability
- Handle different storage backends (local, cloud, network) through adapters
- Use domain-specific file operations rather than generic file I/O
- Include proper error handling for file operations

```python
# Infrastructure Secondary Port (Application Layer) - application/ports/secondary/
class FileStoragePort(ABC):
    @abstractmethod
    def save_document(self, document_id: DocumentId, content: bytes) -> None:
        pass

    @abstractmethod
    def load_document(self, document_id: DocumentId) -> bytes:
        pass

    @abstractmethod
    def delete_document(self, document_id: DocumentId) -> None:
        pass

    @abstractmethod
    def document_exists(self, document_id: DocumentId) -> bool:
        pass

# Local File System Adapter
class LocalFileStorageAdapter(FileStoragePort):
    def __init__(self, base_path: Path):
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    def save_document(self, document_id: DocumentId, content: bytes) -> None:
        file_path = self._base_path / f"{document_id.value}.bin"
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
        except IOError as e:
            raise DocumentStorageError(f"Failed to save document {document_id}: {e}")

    def load_document(self, document_id: DocumentId) -> bytes:
        file_path = self._base_path / f"{document_id.value}.bin"
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise DocumentNotFoundError(document_id)
        except IOError as e:
            raise DocumentStorageError(f"Failed to load document {document_id}: {e}")

# Cloud Storage Adapter
class S3FileStorageAdapter(FileStoragePort):
    def __init__(self, s3_client, bucket_name: str):
        self._s3_client = s3_client
        self._bucket_name = bucket_name

    def save_document(self, document_id: DocumentId, content: bytes) -> None:
        try:
            self._s3_client.put_object(
                Bucket=self._bucket_name,
                Key=f"documents/{document_id.value}",
                Body=content
            )
        except Exception as e:
            raise DocumentStorageError(f"Failed to save document to S3: {e}")
```

### 9. External API Adapter Rules

- Abstract external service calls through secondary ports
- Handle authentication, rate limiting, and retry logic in adapters
- Map external API models to domain concepts
- Provide fallback mechanisms and circuit breakers
- Include comprehensive error handling for network issues

```python
# Infrastructure Secondary Port (Application Layer) - application/ports/secondary/
class PaymentProcessorPort(ABC):
    @abstractmethod
    def process_payment(self, amount: Money, payment_method: PaymentMethod) -> PaymentResult:
        pass

    @abstractmethod
    def refund_payment(self, transaction_id: TransactionId) -> RefundResult:
        pass

class NotificationServicePort(ABC):
    @abstractmethod
    def send_sms(self, phone_number: PhoneNumber, message: str) -> None:
        pass

    @abstractmethod
    def send_push_notification(self, device_token: str, title: str, body: str) -> None:
        pass

# Stripe Payment Adapter
class StripePaymentAdapter(PaymentProcessorPort):
    def __init__(self, api_key: str, timeout: int = 30):
        self._client = stripe.StripeClient(api_key)
        self._timeout = timeout

    def process_payment(self, amount: Money, payment_method: PaymentMethod) -> PaymentResult:
        try:
            response = self._client.charges.create(
                amount=int(amount.cents),
                currency=amount.currency.lower(),
                source=payment_method.token,
                timeout=self._timeout
            )
            return PaymentResult.success(
                transaction_id=TransactionId(response.id),
                amount=amount
            )
        except stripe.CardError as e:
            return PaymentResult.declined(e.user_message)
        except stripe.APIError as e:
            raise PaymentProcessingError(f"Stripe API error: {e}")
        except Exception as e:
            raise PaymentProcessingError(f"Unexpected payment error: {e}")

# Twilio SMS Adapter
class TwilioNotificationAdapter(NotificationServicePort):
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self._client = TwilioClient(account_sid, auth_token)
        self._from_number = from_number

    def send_sms(self, phone_number: PhoneNumber, message: str) -> None:
        try:
            self._client.messages.create(
                to=phone_number.value,
                from_=self._from_number,
                body=message
            )
        except TwilioException as e:
            raise NotificationDeliveryError(f"Failed to send SMS: {e}")

    def send_push_notification(self, device_token: str, title: str, body: str) -> None:
        # Implementation would depend on push notification service
        raise NotImplementedError("Push notifications not implemented in Twilio adapter")
```

### 10. Random Number Generation Adapter Rules

- Abstract random number generation through secondary ports for deterministic testing
- Provide both cryptographically secure and pseudo-random implementations
- Enable seeded randomness for reproducible test scenarios
- Use domain-appropriate random operations rather than raw random numbers

```python
# Infrastructure Secondary Port (Application Layer) - application/ports/secondary/
class RandomNumberProviderPort(ABC):
    @abstractmethod
    def random_int(self, min_value: int, max_value: int) -> int:
        pass

    @abstractmethod
    def random_float(self) -> float:
        pass

    @abstractmethod
    def random_choice(self, choices: list[T]) -> T:
        pass

    @abstractmethod
    def random_boolean(self, probability: float = 0.5) -> bool:
        pass

# System Random Adapter (Cryptographically secure)
class SecureRandomProvider(RandomNumberProviderPort):
    def __init__(self):
        self._random = secrets.SystemRandom()

    def random_int(self, min_value: int, max_value: int) -> int:
        return self._random.randint(min_value, max_value)

    def random_float(self) -> float:
        return self._random.random()

    def random_choice(self, choices: list[T]) -> T:
        return self._random.choice(choices)

    def random_boolean(self, probability: float = 0.5) -> bool:
        return self._random.random() < probability

# Pseudo-Random Adapter (Seedable for testing)
class SeededRandomProvider(RandomNumberProviderPort):
    def __init__(self, seed: int = None):
        self._random = random.Random(seed)

    def random_int(self, min_value: int, max_value: int) -> int:
        return self._random.randint(min_value, max_value)

    def random_float(self) -> float:
        return self._random.random()

    def random_choice(self, choices: list[T]) -> T:
        return self._random.choice(choices)

    def random_boolean(self, probability: float = 0.5) -> bool:
        return self._random.random() < probability

# Fixed Random Provider (For deterministic testing)
class FixedRandomProvider(RandomNumberProviderPort):
    def __init__(self, fixed_int: int = 42, fixed_float: float = 0.5, fixed_boolean: bool = True):
        self._fixed_int = fixed_int
        self._fixed_float = fixed_float
        self._fixed_boolean = fixed_boolean

    def random_int(self, min_value: int, max_value: int) -> int:
        return max(min_value, min(self._fixed_int, max_value))

    def random_float(self) -> float:
        return self._fixed_float

    def random_choice(self, choices: list[T]) -> T:
        return choices[0] if choices else None

    def random_boolean(self, probability: float = 0.5) -> bool:
        return self._fixed_boolean
```

### 11. ID Generation Adapter Rules

- Abstract ID generation through secondary ports for consistent and testable ID creation
- Support different ID formats (UUID, sequential, custom formats)
- Enable deterministic ID generation for testing scenarios
- Ensure ID uniqueness and appropriate format for domain needs

```python
# Infrastructure Secondary Port (Application Layer) - application/ports/secondary/
class IdGeneratorPort(ABC):
    @abstractmethod
    def generate_uuid(self) -> str:
        pass

    @abstractmethod
    def generate_short_id(self, length: int = 8) -> str:
        pass

    @abstractmethod
    def generate_sequential_id(self, prefix: str = "") -> str:
        pass

# UUID Generator Adapter
class UUIDGeneratorAdapter(IdGeneratorPort):
    def generate_uuid(self) -> str:
        return str(uuid4())

    def generate_short_id(self, length: int = 8) -> str:
        # Generate a shorter, URL-safe ID
        return secrets.token_urlsafe(length)[:length]

    def generate_sequential_id(self, prefix: str = "") -> str:
        # Note: This is a simple implementation, production would need proper sequence management
        timestamp = int(time.time() * 1000000)  # microsecond precision
        return f"{prefix}{timestamp}" if prefix else str(timestamp)

# Deterministic ID Generator (For testing)
class DeterministicIdGenerator(IdGeneratorPort):
    def __init__(self, base_uuid: str = "12345678-1234-1234-1234-123456789abc"):
        self._base_uuid = base_uuid
        self._counter = 0

    def generate_uuid(self) -> str:
        # Generate predictable UUIDs for testing
        counter_hex = f"{self._counter:012x}"
        uuid_parts = self._base_uuid.split('-')
        uuid_parts[-1] = counter_hex
        self._counter += 1
        return '-'.join(uuid_parts)

    def generate_short_id(self, length: int = 8) -> str:
        self._counter += 1
        return f"test{self._counter:04d}"[:length]

    def generate_sequential_id(self, prefix: str = "") -> str:
        self._counter += 1
        return f"{prefix}{self._counter}"

# Custom Domain ID Generators
class UserIdGenerator:
    def __init__(self, id_generator: IdGeneratorPort):
        self._id_generator = id_generator

    def generate(self) -> UserId:
        return UserId(self._id_generator.generate_uuid())

class OrderIdGenerator:
    def __init__(self, id_generator: IdGeneratorPort):
        self._id_generator = id_generator

    def generate(self) -> OrderId:
        return OrderId(self._id_generator.generate_sequential_id("ORD-"))

class ProductCodeGenerator:
    def __init__(self, id_generator: IdGeneratorPort):
        self._id_generator = id_generator

    def generate(self) -> ProductCode:
        return ProductCode(self._id_generator.generate_short_id(6).upper())

# Usage in Use Cases
class CreateUserUseCase(CreateUserPort):
    def __init__(
        self,
        user_repository: UserRepository,
        user_id_generator: UserIdGenerator,  # Domain-specific ID generator
        time_provider: TimeProviderPort,
        unit_of_work: UnitOfWork
    ):
        self._user_repository = user_repository
        self._user_id_generator = user_id_generator
        self._time_provider = time_provider
        self._unit_of_work = unit_of_work

    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        with self._unit_of_work:
            user_id = self._user_id_generator.generate()
            created_at = self._time_provider.now()

            user = User.create(
                id=user_id,
                email=Email(command.email),
                name=command.name,
                created_at=created_at
            )

            self._user_repository.save(user)
            return CreateUserResponse(user_id.value)
```

### 12. Use Case as Primary Port Implementation Rules

- Use cases implement primary ports and orchestrate domain objects
- They use both domain ports (repositories) and infrastructure ports (email, messaging)
- Should not contain business logic - delegate to domain objects
- Handle cross-cutting concerns like transactions and event publishing
- Serve as the application's use case boundary
- Each use case should represent exactly one business workflow

```python
class CreateUserUseCase(CreateUserPort):
    def __init__(
        self,
        user_repository: UserRepository,  # Domain port
        email_service: EmailNotificationPort,  # Infrastructure port
        event_publisher: EventPublisherPort,  # Infrastructure port
        unit_of_work: UnitOfWork
    ):
        self._user_repository = user_repository
        self._email_service = email_service
        self._event_publisher = event_publisher
        self._unit_of_work = unit_of_work

    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        with self._unit_of_work:
            email = Email(command.email)
            user = User.create(email, command.name)
            self._user_repository.save(user)  # Domain port
            self._email_service.send_welcome_email(email, command.name)  # Infrastructure port
            self._event_publisher.publish(UserCreated(user.id, email))  # Infrastructure port
            return CreateUserResponse(user.id.value)
```

These integrated rules ensure that Domain Driven Design and Ports & Adapters (Hexagonal Architecture) work together seamlessly in Python implementations. The combination provides clean separation of concerns, testability, and flexibility while maintaining domain focus and proper dependency management.

## Apendix

### Prompt to generate a DDD aggregate with AI

NOTE: Taken from -> <https://codely.com/en/blog/how-to-implement-ddd-code-using-ai>

Copy and paste the following prompt into your editor and modify from the User variables section to fit your code.

It is important to run it in agent mode:

```text
# Codely Aggregate Design Blueprint structure:

'''
* Name: The name of the aggregate.
* Description: A brief description of the aggregate.
* Context: The context where the aggregate belongs.
* Properties: A list of properties that the aggregate has. Optionally, you can specify the type of each property.
* Enforced Invariants: A list of invariants that the aggregate enforces.
* Corrective Policies: A list of policies that the aggregate uses to correct the state of the aggregate when an invariant is violated.
* Domain Events: A list of events that the aggregate emits.
* Ways to access: A list of ways to access the aggregate.
'''

# Instructions to transform the Aggregate Design Blueprint to code:

You have to create:
* A module for the aggregate:
    * The module name should be the name of the aggregate in plural.
    * Should be written in $FOLDERS_CASE.
    * Should be inside the `src/contexts/$CONTEXT_NAME` directory.
* Every module contains 3 folders: `domain`, `application`, and `infrastructure`.
* Inside the `domain` folder, you'll have to create:
    * An `$AGGREGATE_NAME.$FILES_FORMAT file that contains the aggregate class:
        * The file name should be the name of the aggregate in PascalCase.
        * The aggregate class should have the properties, invariants, policies, and events that the aggregate has.
        * You should take a look to other aggregates to see the format.
    * A `$DOMAIN_EVENT.$FILES_FORMAT file per every event that the aggregate emits:
        * The file name should be the name of the event in PascalCase.
        * The event should have only the mutated properties.
        * You should take a look to other events to see the format.
    * A `$DOMAIN_ERROR.$FILES_FORMAT file per every invariant that the aggregate enforces:
        * The file name should be the name of the invariant in PascalCase.
        * You should take a look to other errors to see the format.
    * A `$REPOSITORY.$FILES_FORMAT file that contains the repository interface:
        * The file name should be the name of the aggregate in PascalCase with the suffix `Repository`.
        * The repository should have the methods to save and retrieve the aggregate.
        * You should take a look to other repositories to see the format.
* Inside the `application` folder, you'll have to create:
    * A folder using $FOLDERS_CASE for every mutation that the aggregate has (inferred by the domain events) and for every query that the aggregate has.
    * Inside every query/mutation folder, you'll have to create an `$USE_CASE.$FILES_FORMAT file that contains the query/mutation use case.
        * The file name should be the name of the query/mutation in PascalCase in a service mode. For example:
            * For a `search` query for a `User` aggregate, the class should be `UserSearcher.$FILES_FORMAT.
            * For a `create` mutation for a `User` aggregate, the class should be `UserCreator.$FILES_FORMAT.
        * You should take a look to other queries/mutations to see the format.
* Inside the `infrastructure` folder, you'll have to create:
    * A `$REPOSITORY.$FILES_FORMAT file that contains the repository implementation:
        * The file name should be the name of the aggregate in PascalCase with the suffix `Repository`.
        * Also, the file should have an implementation prefix. For example, for a `User` aggregate and a Postgres implementation, the file should be `PostgresUserRepository.$FILES_FORMAT.
        * The repository should implement the repository interface from the domain layer.
        * You should take a look to other repositories to see the format and use the most used implementation.
* You'll have to create a test per every use case:
    * The test should be inside the `tests/contexts/$CONTEXT_NAME/$MODULE_NAME/application` directory.
    * You should create an Object Mother per every aggregate and value object that you create inside `tests/contexts/$CONTEXT_NAME/$MODULE_NAME/domain`.
    * Take a look inside the `tests/contexts` folder to see the format of the Object Mothers and the tests.
    * You should only create a test per every use case, don't create any extra test case.
* You should create a test for the repository implementation:
    * The test should be inside the `tests/contexts/$CONTEXT_NAME/$MODULE_NAME/infrastructure` directory.

# Protocol to execute the transformation:

## 1. Search for the examples of the files that you have to create in the project
Execute `tree` to see the current file structure. Then use `cat` to see the content of similar files.

## 2. Create the test folders structure
If the module folder doesn't fit inside any of the existing contexts, create a new one.

## 3. Create the test for the first use case
* We should create use case by use case, starting with the first one.
* We're doing TDD, so we'll create the first use case test first.
* Also, we'll create all the object mothers.
* Then all the domain objects (if needed).
* Then the use case.
* Do it until the created test passes.
* Repeat this per every use case.

## 4. Create the repository implementation test
* We should create the repository implementation test after all the use cases are created.
* First, create the repository implementation test.
* Then, create the repository implementation.
* Do it until the created test passes.

# User variables:

$FOLDERS_CASE = kebab-case
$FILES_FORMAT = ts

# User Codely Aggregate Design Blueprint:

'''
* Name: Naive Bank Account
* Description: An aggregate modeling in a very naive way a personal bank account. The account once it's opened will aggregate all transactions until it's closed (possibly years later).
* Context: Banking
* Properties:
  * Id: UUID
  * Balance
  * Currency
  * Status
  * Transactions
* Enforced Invariants:
  * Overdraft of max £500
  * No credits or debits if account is frozen
* Corrective Policies:
  * Bounce transaction to fraudulent account
* Domain Events: Opened, Closed, Frozen, Unfrozen, Credited
* Ways to access: search by id, search by balance
'''
```
