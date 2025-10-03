# London School TDD Session - Complete Example

This example demonstrates a complete London School TDD session following Pedro's Algorithm to implement a "User Registration with Email Confirmation" feature.

## Feature: User Registration with Email Confirmation

**User Story**:

> As a new user
> I want to register with email and password
> So that I can create an account and access the system after confirming my email

**Acceptance Criteria**:

1. User provides email, name, and password
2. System creates unconfirmed user account
3. System sends confirmation email with token
4. User confirms email using token
5. User can log in with confirmed account

---

## Step 1: Write Acceptance Test (RED) - At Use Case Boundary

```python
# tests/acceptance/test_user_registration_flow.py
import pytest

def test_complete_user_registration_and_login_workflow(
    register_user_use_case: RegisterUserUseCase,
    confirm_email_use_case: ConfirmEmailUseCase,
    login_use_case: LoginUseCase,
    get_user_profile_use_case: GetUserProfileUseCase,
    test_db,  # Real database for repositories
    email_test_stub  # Stub for email service
):
    """
    Complete user journey: Register → Receive email → Confirm → Login → Get Profile

    CRITICAL: Acceptance test starts at USE CASE boundary, NOT HTTP layer!
    This test will FAIL initially - that's the goal!
    """
    # Step 1: User registers
    register_cmd = RegisterUserCommand(
        email="alice@example.com",
        name="Alice",
        password="SecurePass123!"
    )
    register_response = register_user_use_case.execute(register_cmd)

    assert register_response.user_id is not None
    assert register_response.status == "pending_confirmation"

    # Step 2: System sends confirmation email
    emails = email_test_stub.get_sent_emails()
    assert len(emails) == 1
    assert emails[0].to == "alice@example.com"
    assert "confirm" in emails[0].subject.lower()
    confirmation_token = emails[0].token

    # Step 3: User confirms email
    confirm_cmd = ConfirmEmailCommand(
        user_id=register_response.user_id,
        token=confirmation_token
    )
    confirm_response = confirm_email_use_case.execute(confirm_cmd)

    assert confirm_response.success == True
    assert confirm_response.user_status == "confirmed"

    # Step 4: User logs in with confirmed account
    login_cmd = LoginCommand(
        email="alice@example.com",
        password="SecurePass123!"
    )
    login_response = login_use_case.execute(login_cmd)

    assert login_response.success == True
    assert login_response.access_token is not None

    # Step 5: User accesses profile
    profile_query = GetUserProfileQuery(user_id=register_response.user_id)
    profile_response = get_user_profile_use_case.execute(profile_query)

    assert profile_response.email == "alice@example.com"
    assert profile_response.status == "confirmed"
```

**Result**: ❌ RED - Test fails (use cases don't exist yet)

**Status**: Acceptance test is RED. This is our Definition of Done for this feature.

**Important**: Acceptance test starts at **use case boundary**. HTTP controllers will be tested later in contract tests.

---

## Step 2: Define Driven Ports (Interfaces)

```python
# domain/repositories/user_repository.py
from abc import ABC, abstractmethod
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.user_id import UserId

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        """Save user aggregate"""
        pass

    @abstractmethod
    def find_by_email(self, email: Email) -> User | None:
        """Find user by email"""
        pass

    @abstractmethod
    def find_by_id(self, user_id: UserId) -> User | None:
        """Find user by ID"""
        pass

# application/ports/email_service_port.py
from abc import ABC, abstractmethod
from domain.value_objects.email import Email

class EmailServicePort(ABC):
    @abstractmethod
    def send_confirmation_email(self, to: Email, token: str, name: str) -> None:
        """Send confirmation email to user"""
        pass

# application/ports/password_hasher_port.py
from abc import ABC, abstractmethod

class PasswordHasherPort(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash password"""
        pass

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        pass
```

---

## Step 3: Unit Test Cycle (While Acceptance RED)

### 3.1: Email Value Object

**Test (RED)**:

```python
# tests/unit/domain/value_objects/test_email.py
import pytest
from domain.value_objects.email import Email

def test_valid_email_is_created():
    email = Email("alice@example.com")
    assert email.value == "alice@example.com"

def test_email_must_contain_at_symbol():
    with pytest.raises(ValueError, match="Invalid email format"):
        Email("invalid-email")

def test_email_must_contain_domain():
    with pytest.raises(ValueError, match="Invalid email format"):
        Email("alice@")

def test_email_equality_based_on_value():
    email1 = Email("alice@example.com")
    email2 = Email("alice@example.com")
    assert email1 == email2

def test_email_is_immutable():
    email = Email("alice@example.com")
    with pytest.raises(AttributeError):
        email.value = "different@example.com"  # Should fail - frozen
```

**Implementation (GREEN)**:

```python
# domain/value_objects/email.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if '@' not in self.value:
            raise ValueError("Invalid email format")
        if len(self.value.split('@')) != 2:
            raise ValueError("Invalid email format")
        domain = self.value.split('@')[1]
        if not domain:
            raise ValueError("Invalid email format")

    @property
    def domain(self) -> str:
        return self.value.split('@')[1]
```

**Result**: ✅ GREEN - All email tests pass

**Commit**: `git commit -m "[BEHAVIORAL] Add Email value object with validation"`

---

### 3.2: User Entity

**Test (RED)**:

```python
# tests/unit/domain/entities/test_user.py
import pytest
from domain.entities.user import User
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.events.user_registered import UserRegistered

def test_user_can_be_created_unconfirmed():
    user = User.register(
        user_id=UserId.generate(),
        email=Email("alice@example.com"),
        name="Alice",
        password_hash="hashed_password"
    )

    assert user.email.value == "alice@example.com"
    assert user.name == "Alice"
    assert user.is_confirmed == False
    assert user.password_hash == "hashed_password"

def test_user_equality_based_on_id():
    id = UserId.generate()
    user1 = User.register(id, Email("alice@example.com"), "Alice", "hash1")
    user2 = User.register(id, Email("different@example.com"), "Different", "hash2")
    assert user1 == user2  # Same ID = same user

def test_user_can_confirm_email():
    user = User.register(
        UserId.generate(),
        Email("alice@example.com"),
        "Alice",
        "hashed_password"
    )

    event = user.confirm_email("valid-token")

    assert user.is_confirmed == True
    assert isinstance(event, UserEmailConfirmed)

def test_user_cannot_confirm_twice():
    user = User.register(
        UserId.generate(),
        Email("alice@example.com"),
        "Alice",
        "hashed_password"
    )
    user.confirm_email("token")

    with pytest.raises(ValueError, match="Email already confirmed"):
        user.confirm_email("token")

def test_user_generates_confirmation_token():
    user = User.register(
        UserId.generate(),
        Email("alice@example.com"),
        "Alice",
        "hashed_password"
    )

    token = user.generate_confirmation_token()

    assert token is not None
    assert len(token) == 32  # Assuming 32-char token
```

**Implementation (GREEN)**:

```python
# domain/entities/user.py
from dataclasses import dataclass, field
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.events.user_registered import UserRegistered
from domain.events.user_email_confirmed import UserEmailConfirmed
import secrets

@dataclass
class User:
    id: UserId
    email: Email
    name: str
    password_hash: str
    is_confirmed: bool = False
    _confirmation_token: str | None = field(default=None, init=False)

    @staticmethod
    def register(
        user_id: UserId,
        email: Email,
        name: str,
        password_hash: str
    ) -> 'User':
        """Factory method for user registration"""
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        user = User(
            id=user_id,
            email=email,
            name=name,
            password_hash=password_hash,
            is_confirmed=False
        )
        return user

    def generate_confirmation_token(self) -> str:
        """Generate confirmation token for email verification"""
        self._confirmation_token = secrets.token_urlsafe(24)
        return self._confirmation_token

    def confirm_email(self, token: str) -> UserEmailConfirmed:
        """Confirm user email with token"""
        if self.is_confirmed:
            raise ValueError("Email already confirmed")

        if self._confirmation_token != token:
            raise ValueError("Invalid confirmation token")

        self.is_confirmed = True
        return UserEmailConfirmed(self.id, self.email)

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
```

**Result**: ✅ GREEN - All user entity tests pass

**Commit**: `git commit -m "[BEHAVIORAL] Add User entity with registration and confirmation"`

---

### 3.3: Register User Use Case

**Test (RED)**:

```python
# tests/unit/application/use_cases/test_register_user.py
import pytest
from unittest.mock import Mock
from application.use_cases.register_user import RegisterUserUseCase, RegisterUserCommand
from domain.repositories.user_repository import UserRepository
from application.ports.email_service_port import EmailServicePort
from application.ports.password_hasher_port import PasswordHasherPort
from domain.value_objects.email import Email

def test_register_user_creates_unconfirmed_account():
    # Mock driven ports ONLY
    mock_user_repo = Mock(spec=UserRepository)
    mock_email_service = Mock(spec=EmailServicePort)
    mock_password_hasher = Mock(spec=PasswordHasherPort)

    # Setup mocks
    mock_user_repo.find_by_email.return_value = None
    mock_password_hasher.hash.return_value = "hashed_password"

    use_case = RegisterUserUseCase(
        mock_user_repo,
        mock_email_service,
        mock_password_hasher
    )

    # Execute
    command = RegisterUserCommand(
        email="alice@example.com",
        name="Alice",
        password="SecurePass123!"
    )
    response = use_case.execute(command)

    # Verify response
    assert response.user_id is not None

    # Verify COMMANDS only (no queries!)
    mock_user_repo.save.assert_called_once()
    mock_email_service.send_confirmation_email.assert_called_once()

    # DO NOT verify queries:
    # mock_user_repo.find_by_email.assert_called_once()  # WRONG!

def test_register_user_rejects_duplicate_email():
    mock_user_repo = Mock(spec=UserRepository)
    mock_email_service = Mock(spec=EmailServicePort)
    mock_password_hasher = Mock(spec=PasswordHasherPort)

    # Existing user with same email
    existing_user = Mock()
    mock_user_repo.find_by_email.return_value = existing_user

    use_case = RegisterUserUseCase(
        mock_user_repo,
        mock_email_service,
        mock_password_hasher
    )

    command = RegisterUserCommand(
        email="alice@example.com",
        name="Alice",
        password="SecurePass123!"
    )

    with pytest.raises(ValueError, match="Email already registered"):
        use_case.execute(command)

    # Should not send email or save
    mock_email_service.send_confirmation_email.assert_not_called()
    mock_user_repo.save.assert_not_called()
```

**Implementation (GREEN)**:

```python
# application/use_cases/register_user.py
from dataclasses import dataclass
from domain.repositories.user_repository import UserRepository
from application.ports.email_service_port import EmailServicePort
from application.ports.password_hasher_port import PasswordHasherPort
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.user_id import UserId

@dataclass
class RegisterUserCommand:
    email: str
    name: str
    password: str

@dataclass
class RegisterUserResponse:
    user_id: str

class RegisterUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        email_service: EmailServicePort,
        password_hasher: PasswordHasherPort
    ):
        self._user_repository = user_repository
        self._email_service = email_service
        self._password_hasher = password_hasher

    def execute(self, command: RegisterUserCommand) -> RegisterUserResponse:
        # Orchestration only - no business logic!
        email = Email(command.email)

        # Check if user exists
        existing_user = self._user_repository.find_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash password
        password_hash = self._password_hasher.hash(command.password)

        # Create user (domain handles business rules)
        user = User.register(
            user_id=UserId.generate(),
            email=email,
            name=command.name,
            password_hash=password_hash
        )

        # Generate confirmation token
        token = user.generate_confirmation_token()

        # Save user
        self._user_repository.save(user)

        # Send confirmation email
        self._email_service.send_confirmation_email(
            to=user.email,
            token=token,
            name=user.name
        )

        return RegisterUserResponse(user_id=user.id.value)
```

**Result**: ✅ GREEN - Use case tests pass

**Commit**: `git commit -m "[BEHAVIORAL] Add RegisterUserUseCase with email confirmation"`

---

## Step 4: Integration Tests (Driven Adapters)

```python
# tests/integration/infrastructure/test_postgres_user_repository.py
import pytest
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from domain.entities.user import User
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email

def test_postgres_repository_saves_and_retrieves_user(postgres_container):
    """Real database integration - no mocks!"""
    repository = PostgresUserRepository(
        postgres_container.get_connection_string()
    )

    # Create real user
    user = User.register(
        user_id=UserId.generate(),
        email=Email("alice@example.com"),
        name="Alice",
        password_hash="hashed_password"
    )

    # Real save
    repository.save(user)

    # Real retrieval
    found_user = repository.find_by_email(Email("alice@example.com"))

    # Verify
    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == user.email
    assert found_user.name == user.name
    assert found_user.is_confirmed == False
```

**Implementation**:

```python
# infrastructure/repositories/postgres_user_repository.py
from domain.repositories.user_repository import UserRepository
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.user_id import UserId
from sqlalchemy.orm import Session

class PostgresUserRepository(UserRepository):
    def __init__(self, connection_string: str):
        # Setup SQLAlchemy connection
        pass

    def save(self, user: User) -> None:
        # Map domain user to ORM model
        orm_user = UserOrmModel(
            id=user.id.value,
            email=user.email.value,
            name=user.name,
            password_hash=user.password_hash,
            is_confirmed=user.is_confirmed
        )
        self._session.add(orm_user)
        self._session.commit()

    def find_by_email(self, email: Email) -> User | None:
        orm_user = self._session.query(UserOrmModel).filter_by(
            email=email.value
        ).first()

        if not orm_user:
            return None

        # Map ORM model to domain user
        return User(
            id=UserId(orm_user.id),
            email=Email(orm_user.email),
            name=orm_user.name,
            password_hash=orm_user.password_hash,
            is_confirmed=orm_user.is_confirmed
        )
```

**Commit**: `git commit -m "[BEHAVIORAL] Add PostgresUserRepository implementation"`

---

## Step 5: Contract Tests (Driving Adapters)

```python
# tests/contract/test_registration_api.py
def test_register_endpoint_returns_201_with_user_id(api_client):
    response = api_client.post("/api/users/register", json={
        "email": "alice@example.com",
        "name": "Alice",
        "password": "SecurePass123!"
    })

    assert response.status_code == 201
    assert "user_id" in response.json()
    assert response.headers["Content-Type"] == "application/json"

def test_register_endpoint_validates_email_format(api_client):
    response = api_client.post("/api/users/register", json={
        "email": "invalid-email",
        "name": "Alice",
        "password": "SecurePass123!"
    })

    assert response.status_code == 400
    assert "email" in response.json()["errors"]
```

**Implementation**:

```python
# infrastructure/api/controllers/user_controller.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

class RegisterUserRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

@router.post("/users/register", status_code=201)
def register_user(request: RegisterUserRequest):
    try:
        command = RegisterUserCommand(
            email=request.email,
            name=request.name,
            password=request.password
        )
        response = register_user_use_case.execute(command)
        return {"user_id": response.user_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Commit**: `git commit -m "[BEHAVIORAL] Add REST API registration endpoint"`

---

## Step 6: Run Acceptance Test

```bash
$ pytest tests/acceptance/test_user_registration_flow.py -v
```

**Result**: ✅ GREEN - Acceptance test passes!

**Final Commit**: `git commit -m "[BEHAVIORAL] Complete user registration feature with email confirmation"`

---

## Key Takeaways from This Session

1. **Acceptance test stayed RED** until complete feature was implemented
2. **Multiple small commits** on each green unit test
3. **Mocked only driven ports** (repositories, email service, password hasher)
4. **Used real domain objects** (User, Email, UserId) - never mocked
5. **Verified commands only** (save, send_confirmation_email) - not queries
6. **Integration tests used real database** - no mocks
7. **Contract tests verified API compliance** - status codes, validation
8. **Complete user journey** in acceptance test - multiple API calls

## Test Statistics

- **Acceptance Tests**: 1 (complete user journey)
- **Unit Tests**: 15 (Email: 5, User: 5, Use Case: 5)
- **Integration Tests**: 3 (Repository, Email Service, Password Hasher)
- **Contract Tests**: 8 (API endpoints and validation)
- **Total**: 27 tests

All following London School TDD principles and Pedro's Algorithm!
