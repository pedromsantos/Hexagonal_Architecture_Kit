# Architecture Review Agent - Usage Example

This document demonstrates how to use the Architecture Review Agent to validate code against Hexagonal Architecture and DDD patterns.

## Scenario: Reviewing a User Management Module

### Project Structure

```txt
src/
├── domain/
│   ├── entities/
│   │   └── user.py
│   ├── value_objects/
│   │   └── email.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── user_profile_repository.py  # ⚠️ Potential issue
│   └── services/
│       └── user_service.py
├── application/
│   ├── use_cases/
│   │   └── create_user.py
│   └── ports/
│       └── email_service_port.py
└── infrastructure/
    ├── repositories/
    │   └── postgres_user_repository.py
    └── adapters/
        └── smtp_email_service.py
```

## Agent Invocation

```bash
# Using the Architecture Review Agent
claude --prompt="@agents/architecture_review.md" \
       --context="@RULES.md" \
       --files="src/**/*.py"
```

## Agent Output

````markdown
# Architecture Review Report

## ✅ Compliant Patterns

### Domain Layer - Value Objects

- `Email` value object at `src/domain/value_objects/email.py:8`
  - Immutable (frozen dataclass) ✓
  - Validation in constructor ✓
  - Domain methods present (domain(), is_from_domain()) ✓

### Application Layer - Use Cases

- `CreateUserUseCase` at `src/application/use_cases/create_user.py:12`
  - Orchestration only (no business logic) ✓
  - Returns DTO (CreateUserResponse) ✓
  - Single responsibility ✓

### Infrastructure Layer - Adapters

- `PostgresUserRepository` at `src/infrastructure/repositories/postgres_user_repository.py:15`
  - Technology in name ✓
  - Implements domain port ✓
  - Handles ORM mapping internally ✓

---

## ❌ Violations

### VIOLATION #1: Extra Repository for Non-Aggregate Entity

**Location**: `src/domain/repositories/user_profile_repository.py:1`
**Severity**: HIGH
**Rule**: RULES.md Section 6 - Repository Pattern Rules (lines 1218-1227)
**Description**: Repository created for `UserProfile` which is not an aggregate root

**Current Code**:

```python
# user_profile_repository.py
from abc import ABC, abstractmethod

class UserProfileRepository(ABC):
    @abstractmethod
    def find_profile_by_user_id(self, user_id: UserId) -> UserProfile | None:
        pass

    @abstractmethod
    def save_profile(self, profile: UserProfile) -> None:
        pass
```
````

**Analysis**:

- `UserProfile` is part of the `User` aggregate
- Should be accessed through `User` aggregate root
- Creating separate repository violates 1:1 aggregate-repository pattern

**Impact**:

- Breaks aggregate boundary
- Allows inconsistent state (user and profile out of sync)
- Makes transaction management difficult

**Fix**:

```python
# Remove user_profile_repository.py entirely

# In domain/entities/user.py - UserProfile becomes internal entity
@dataclass
class User:  # Aggregate Root
    id: UserId
    email: Email
    name: str
    _profile: UserProfile = field(default_factory=UserProfile, init=False)

    def update_profile(self, bio: str, avatar_url: str) -> UserProfileUpdated:
        """Business logic for profile updates"""
        self._profile = UserProfile(bio=bio, avatar_url=avatar_url)
        return UserProfileUpdated(self.id, self._profile)

    @property
    def profile(self) -> UserProfile:
        """Read-only access to profile"""
        return self._profile

# In domain/repositories/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: UserId) -> User | None:
        """Loads complete User aggregate including profile"""
        pass

    @abstractmethod
    def save(self, user: User) -> None:
        """Saves complete User aggregate including profile"""
        pass
```

---

### VIOLATION #2: Anemic Entity

**Location**: `src/domain/entities/user.py:12-25`
**Severity**: MEDIUM
**Rule**: RULES.md Section 1 - Entity Rules (lines 110-139)
**Description**: `User` entity lacks business behavior methods

**Current Code**:

```python
@dataclass
class User:
    id: UserId
    email: Email
    name: str
    is_active: bool = True

    # Only has getters, no business logic!
```

**Issue**: Entity is anemic - no business methods, only data

**Fix**:

```python
@dataclass
class User:
    id: UserId
    email: Email
    name: str
    is_active: bool = True
    _profile: UserProfile = field(default_factory=UserProfile, init=False)

    def change_email(self, new_email: Email) -> UserEmailChanged:
        """Business logic for email changes"""
        if self.email == new_email:
            raise ValueError("New email must be different")

        old_email = self.email
        self.email = new_email
        return UserEmailChanged(self.id, old_email, new_email)

    def deactivate(self) -> UserDeactivated:
        """Business logic for deactivation"""
        if not self.is_active:
            raise ValueError("User already inactive")

        self.is_active = False
        return UserDeactivated(self.id)

    def activate(self) -> UserActivated:
        """Business logic for activation"""
        if self.is_active:
            raise ValueError("User already active")

        self.is_active = True
        return UserActivated(self.id)

    def update_profile(self, bio: str, avatar_url: str) -> UserProfileUpdated:
        self._profile = UserProfile(bio=bio, avatar_url=avatar_url)
        return UserProfileUpdated(self.id, self._profile)

    @property
    def profile(self) -> UserProfile:
        return self._profile
```

---

### VIOLATION #3: Technical Term in Domain Service Name

**Location**: `src/domain/services/user_service.py:8`
**Severity**: LOW
**Rule**: RULES.md Section 12 - Naming Convention Rules (lines 1846-1851)
**Description**: "Service" is overused and generic - use domain-specific name

**Current Code**:

```python
class UserService:  # Generic technical name
    def validate_unique_email(self, email: Email, user_repo: UserRepository) -> bool:
        pass
```

**Issue**: "Service" doesn't convey domain meaning

**Fix**:

```python
class UserRegistrationValidator:  # Domain-specific name
    """Domain service for user registration validation rules"""

    def __init__(self):
        pass  # Stateless

    def ensure_unique_email(self, email: Email, existing_users: list[User]) -> None:
        """Validates email uniqueness - business rule"""
        for user in existing_users:
            if user.email == email:
                raise UserEmailAlreadyExistsError(email)

# Usage in CreateUserUseCase
class CreateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        validator: UserRegistrationValidator
    ):
        self._user_repository = user_repository
        self._validator = validator

    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        email = Email(command.email)

        # Use domain service for validation
        existing = self._user_repository.find_by_email(email)
        if existing:
            raise UserEmailAlreadyExistsError(email)

        user = User.create(email, command.name)
        self._user_repository.save(user)
        return CreateUserResponse(user.id.value)
```

---

## 📊 Architecture Metrics

- **Aggregate Roots**: 1 (User)
- **Repositories**: 2 ❌ (should be 1)
- **Entities**: 2 (User, UserProfile)
- **Value Objects**: 3 (UserId, Email, UserProfile)
- **Use Cases**: 1
- **Domain Services**: 1
- **Driving Adapters**: Not reviewed
- **Driven Adapters**: 2 (PostgresUserRepository, SmtpEmailService)

## 🎯 Priority Recommendations

1. **HIGH**: Remove `UserProfileRepository` - violates aggregate-repository pattern (Violation #1)
2. **MEDIUM**: Add business methods to `User` entity (Violation #2)
3. **LOW**: Rename `UserService` to domain-specific name (Violation #3)

## ✅ After Fixes

**Expected Structure**:

```
src/
├── domain/
│   ├── entities/
│   │   └── user.py  # Aggregate root with UserProfile inside
│   ├── value_objects/
│   │   ├── email.py
│   │   ├── user_id.py
│   │   └── user_profile.py  # Value object, not entity
│   ├── repositories/
│   │   └── user_repository.py  # Only one repository
│   ├── services/
│   │   └── user_registration_validator.py  # Domain-specific name
│   └── events/
│       ├── user_email_changed.py
│       ├── user_deactivated.py
│       └── user_profile_updated.py
├── application/
│   └── use_cases/
│       ├── create_user.py
│       ├── change_user_email.py
│       ├── deactivate_user.py
│       └── update_user_profile.py
└── infrastructure/
    ├── repositories/
    │   └── postgres_user_repository.py  # Handles User + UserProfile
    └── adapters/
        └── smtp_email_service.py
```

**Key Improvements**:

- ✅ 1:1 aggregate-repository relationship
- ✅ User aggregate contains business behavior
- ✅ UserProfile accessed through User aggregate root
- ✅ Domain-specific naming
- ✅ Clear aggregate boundaries

## 📚 Reference Sections

For implementation guidance:

- **Aggregate-Repository Pattern**: RULES.md lines 235-305, 1218-1444
- **Entity Rules**: RULES.md lines 110-360
- **Naming Conventions**: RULES.md lines 1846-1855

## Key Takeaways

1. **Repository Count = Aggregate Root Count**: Most common violation is creating repositories for non-aggregate entities
2. **Anemic Entities**: Entities must have business behavior, not just data
3. **Domain Language**: Use domain-specific names, avoid technical terms (Manager, Helper, Service)
4. **Aggregate Boundaries**: Access internal entities through aggregate root
5. **Clear Violations with Fixes**: Agent provides specific code examples showing both problem and solution

## Next Steps

After receiving this review:

1. Fix HIGH priority violations first
2. Verify fixes don't break existing tests
3. Add business methods to entities with proper unit tests
4. Re-run architecture review to confirm compliance
5. Document aggregate boundaries in team documentation
