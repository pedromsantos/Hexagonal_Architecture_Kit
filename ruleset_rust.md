# Domain Driven Design with Ports & Adapters Rules (Rust)

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

- **Driving Ports** define what your application can do (use case interfaces)
- **Driven Ports** define what your application needs (repositories, external services)
- **Driving Adapters** translate external requests into domain operations (REST controllers, CLI)
- **Driven Adapters** implement external integrations (databases, APIs, file systems)

### How They Connect in Practice

```rust
use std::sync::Arc;
use async_trait::async_trait;
use uuid::Uuid;
use chrono::{DateTime, Utc};

// 1. Domain Layer (DDD Core)
#[derive(Debug, Clone, PartialEq)]
pub struct User {
    id: UserId,
    email: Email,
    name: String,
}

impl User {
    // Rule 1: Entity with identity
    pub fn change_email(&mut self, email: Email) -> UserEmailChanged {
        let old_email = self.email.clone();
        self.email = email.clone();
        UserEmailChanged::new(self.id.clone(), old_email, email)
    }

    pub fn id(&self) -> &UserId { &self.id }
    pub fn email(&self) -> &Email { &self.email }
    pub fn name(&self) -> &str { &self.name }
}

#[async_trait]
pub trait UserRepository {
    // Rule 5: Domain port for persistence
    async fn save(&self, user: &User) -> Result<(), DomainError>;
    async fn find_by_id(&self, id: &UserId) -> Result<Option<User>, DomainError>;
}

// 2. Application Layer (Bridge between DDD and Ports & Adapters)
pub struct ChangeUserEmailUseCase {
    user_repo: Arc<dyn UserRepository>,
    email_service: Arc<dyn EmailNotificationPort>,
    time_provider: Arc<dyn TimeProviderPort>,
}

impl ChangeUserEmailUseCase {
    pub fn new(
        user_repo: Arc<dyn UserRepository>,
        email_service: Arc<dyn EmailNotificationPort>,
        time_provider: Arc<dyn TimeProviderPort>,
    ) -> Self {
        Self {
            user_repo,
            email_service,
            time_provider,
        }
    }
}

#[async_trait]
impl ChangeUserEmailPort for ChangeUserEmailUseCase {
    // Rule 9 + P&A Rule 1
    async fn execute(&self, command: ChangeEmailCommand) -> Result<(), UseCaseError> {
        // Orchestrate domain objects (Rule 9)
        let mut user = self.user_repo
            .find_by_id(&command.user_id)
            .await
            .map_err(UseCaseError::Repository)?
            .ok_or(UseCaseError::UserNotFound)?;

        let email = Email::new(&command.new_email)
            .map_err(UseCaseError::InvalidEmail)?;
        let event = user.change_email(email);

        // Use infrastructure ports for side effects
        self.user_repo.save(&user).await.map_err(UseCaseError::Repository)?;
        self.email_service
            .send_email_change_notification(
                &event.old_email,
                &event.new_email,
                self.time_provider.now(),
            )
            .await
            .map_err(UseCaseError::EmailService)?;

        Ok(())
    }
}

// 3. Infrastructure Layer (Ports & Adapters Implementation)
pub struct SqlUserRepository {
    pool: sqlx::PgPool,
}

#[async_trait]
impl UserRepository for SqlUserRepository {
    // P&A Rule 3: Driven adapter
    async fn save(&self, user: &User) -> Result<(), DomainError> {
        // Handle ORM mapping, database specifics
        sqlx::query!(
            "INSERT INTO users (id, email, name) VALUES ($1, $2, $3)
             ON CONFLICT (id) DO UPDATE SET email = $2, name = $3",
            user.id().value(),
            user.email().value(),
            user.name()
        )
        .execute(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(e.to_string()))?;

        Ok(())
    }

    async fn find_by_id(&self, id: &UserId) -> Result<Option<User>, DomainError> {
        let row = sqlx::query!(
            "SELECT id, email, name FROM users WHERE id = $1",
            id.value()
        )
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(e.to_string()))?;

        if let Some(row) = row {
            let user_id = UserId::from_str(&row.id).map_err(DomainError::InvalidId)?;
            let email = Email::new(&row.email).map_err(DomainError::InvalidEmail)?;
            Ok(Some(User::new(user_id, email, row.name)))
        } else {
            Ok(None)
        }
    }
}

pub struct RestUserController {
    use_case: Arc<dyn ChangeUserEmailPort>,
}

impl RestUserController {
    // P&A Rule 2: Driving adapter
    pub async fn patch_user_email(
        &self,
        user_id: String,
        request: ChangeEmailRequest
    ) -> Result<(), ControllerError> {
        let user_id = UserId::from_str(&user_id)
            .map_err(ControllerError::InvalidUserId)?;
        let command = ChangeEmailCommand::new(user_id, request.email);

        self.use_case.execute(command)
            .await
            .map_err(ControllerError::UseCase)
    }
}
```

### Key Integration Principles

1. **Domain Objects** (Entities, Value Objects, Aggregates) contain business logic and know nothing about persistence or external systems

2. **Use Cases** orchestrate domain objects and coordinate with external systems through **Driven Ports**

3. **Driving Adapters** translate external requests into domain commands and delegate to **Use Cases** through **Driving Ports**

4. **Driven Adapters** implement **Driven Ports** and handle all external system complexity (databases, APIs, file systems, etc.)

5. **Dependency Flow**: External → Driving Adapter → Use Case → Domain Objects → Driven Ports → Driven Adapters

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
- Implement `PartialEq` and `Hash` based solely on identity, not attributes/fields
- Entities MUST contain business logic as methods, not just data
  - Avoid anemic domain models - entities should have behavior
- Include validation in constructor

```rust
use uuid::Uuid;
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(Uuid);

impl UserId {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    pub fn from_str(s: &str) -> Result<Self, InvalidUserIdError> {
        Uuid::parse_str(s)
            .map(Self)
            .map_err(|_| InvalidUserIdError)
    }

    pub fn value(&self) -> &Uuid {
        &self.0
    }
}

#[derive(Debug, Clone)]
pub struct User {
    id: UserId,
    email: Email,
    name: String,
}

impl User {
    pub fn new(id: UserId, email: Email, name: String) -> Result<Self, DomainError> {
        let user = Self { id, email, name };
        user.validate()?;
        Ok(user)
    }

    pub fn create(email: Email, name: String) -> Result<Self, DomainError> {
        Self::new(UserId::new(), email, name)
    }

    pub fn change_email(&mut self, new_email: Email) -> UserEmailChanged {
        let old_email = self.email.clone();
        self.email = new_email.clone();
        UserEmailChanged::new(self.id.clone(), old_email, new_email)
    }

    pub fn id(&self) -> &UserId {
        &self.id
    }

    pub fn email(&self) -> &Email {
        &self.email
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    fn validate(&self) -> Result<(), DomainError> {
        if self.name.trim().is_empty() {
            return Err(DomainError::Validation("User must have a name".to_string()));
        }
        Ok(())
    }
}

// Equality based on identity only
impl PartialEq for User {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}

impl Eq for User {}

impl Hash for User {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
    }
}

// Base entity trait for shared behavior
pub trait Entity<T> {
    fn id(&self) -> &T;

    fn equals(&self, other: &Self) -> bool
    where
        T: PartialEq,
    {
        self.id() == other.id()
    }
}

impl Entity<UserId> for User {
    fn id(&self) -> &UserId {
        &self.id
    }
}
```

### 2. Value Object Rules

- Value objects MUST be immutable
- Equality is based on ALL attributes, not identity
- Should be small, focused, and represent a concept from the domain
- Include validation in constructor
- Should have meaningful methods that operate on the value

```rust
use regex::Regex;
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email {
    value: String,
}

impl Email {
    pub fn new(value: &str) -> Result<Self, InvalidEmailError> {
        if !Self::is_valid_email(value) {
            return Err(InvalidEmailError::new(value));
        }
        Ok(Self {
            value: value.to_lowercase(),
        })
    }

    pub fn value(&self) -> &str {
        &self.value
    }

    pub fn domain(&self) -> &str {
        self.value.split('@').nth(1).unwrap()
    }

    pub fn local_part(&self) -> &str {
        self.value.split('@').next().unwrap()
    }

    fn is_valid_email(value: &str) -> bool {
        let email_regex = Regex::new(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
            .unwrap();
        email_regex.is_match(value)
    }
}

impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.value)
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct InvalidEmailError {
    email: String,
}

impl InvalidEmailError {
    pub fn new(email: &str) -> Self {
        Self {
            email: email.to_string(),
        }
    }
}

impl fmt::Display for InvalidEmailError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Invalid email format: {}", self.email)
    }
}

impl std::error::Error for InvalidEmailError {}
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
- Encapsulate Collections: Use proper collection encapsulation

```rust
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct OrderId(Uuid);

impl OrderId {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    pub fn value(&self) -> &Uuid {
        &self.0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CustomerId(Uuid);

impl CustomerId {
    pub fn value(&self) -> &Uuid {
        &self.0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ProductId(Uuid);

#[derive(Debug, Clone)]
pub struct OrderLineItem {
    product_id: ProductId,
    quantity: u32,
}

impl OrderLineItem {
    pub fn new(product_id: ProductId, quantity: u32) -> Result<Self, DomainError> {
        if quantity == 0 {
            return Err(DomainError::Validation("Quantity must be greater than 0".to_string()));
        }
        Ok(Self {
            product_id,
            quantity,
        })
    }

    pub fn product_id(&self) -> &ProductId {
        &self.product_id
    }

    pub fn quantity(&self) -> u32 {
        self.quantity
    }
}

#[derive(Debug, Clone)]
pub struct Order {
    // Aggregate Root
    id: OrderId,
    customer_id: CustomerId,
    line_items: Vec<OrderLineItem>,
}

impl Order {
    pub fn new(id: OrderId, customer_id: CustomerId) -> Self {
        Self {
            id,
            customer_id,
            line_items: Vec::new(),
        }
    }

    pub fn add_line_item(&mut self, product_id: ProductId, quantity: u32) -> Result<(), DomainError> {
        // Business rules and validation
        let line_item = OrderLineItem::new(product_id, quantity)?;
        self.line_items.push(line_item);
        Ok(())
    }

    pub fn line_items(&self) -> &[OrderLineItem] {
        &self.line_items
    }

    pub fn id(&self) -> &OrderId {
        &self.id
    }

    pub fn customer_id(&self) -> &CustomerId {
        &self.customer_id
    }
}

impl Entity<OrderId> for Order {
    fn id(&self) -> &OrderId {
        &self.id
    }
}
```

### 4. Domain Service Rules

Handles business logic that spans multiple entities (e.g., transferring money between two accounts)

- Create domain services ONLY when business logic doesn't naturally fit in entities or value objects
- Domain services should be stateless
- Use dependency injection for external dependencies
- Should operate on domain objects, not primitives
- Should not use Driven ports/adapters
- Name services with domain language (not technical terms)

```rust
use std::sync::Arc;

#[derive(Debug, Clone)]
pub struct Money {
    amount: rust_decimal::Decimal,
    currency: Currency,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Currency {
    USD,
    EUR,
    GBP,
}

pub struct PricingService {
    discount_repository: Arc<dyn DiscountRepository>,
}

impl PricingService {
    pub fn new(discount_repository: Arc<dyn DiscountRepository>) -> Self {
        Self {
            discount_repository,
        }
    }

    pub async fn calculate_order_total(
        &self,
        order: &Order,
        customer: &Customer,
    ) -> Result<Money, DomainError> {
        // Complex pricing logic that spans multiple aggregates
        todo!("Implement pricing calculation")
    }
}

#[async_trait]
pub trait DiscountRepository {
    async fn find_applicable_discounts(&self, customer: &Customer) -> Result<Vec<Discount>, DomainError>;
}

pub struct Customer {
    // Customer implementation
}

pub struct Discount {
    // Discount implementation
}
```

## Repository Pattern Rules

### 5. Repository Interface Rules

- Define repository interfaces in the domain layer using traits - they represent domain concepts
- Repositories should work with Aggregate Roots only
- Use domain-specific query methods, not generic CRUD
- Return domain objects, never DTOs or database models
- Input should be Aggregates not entities, value objects or DTOs
- Should return domain errors, not infrastructure errors

```rust
use async_trait::async_trait;

// Domain Layer - domain/repositories/user_repository.rs
#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_email(&self, email: &Email) -> Result<Option<User>, DomainError>;
    async fn save(&self, user: &User) -> Result<(), DomainError>;
    async fn find_active_users_in_department(&self, department_id: &DepartmentId) -> Result<Vec<User>, DomainError>;
    async fn find_by_id(&self, user_id: &UserId) -> Result<Option<User>, DomainError>;
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct DepartmentId(Uuid);
```

### 6. Repository Implementation Rules

- Implement repositories in the infrastructure layer
- Use transaction management for consistency
- Map between domain objects and persistence models
- Handle optimistic concurrency using version fields
- Repository should not contain business logic

```rust
use sqlx::{PgPool, Row};
use async_trait::async_trait;

pub struct SqlUserRepository {
    pool: PgPool,
}

impl SqlUserRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl UserRepository for SqlUserRepository {
    async fn save(&self, user: &User) -> Result<(), DomainError> {
        sqlx::query!(
            r#"
            INSERT INTO users (id, email, name, version)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                name = EXCLUDED.name,
                version = users.version + 1
            "#,
            user.id().value(),
            user.email().value(),
            user.name(),
            1i32
        )
        .execute(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Failed to save user: {}", e)))?;

        Ok(())
    }

    async fn find_by_email(&self, email: &Email) -> Result<Option<User>, DomainError> {
        let row = sqlx::query!(
            "SELECT id, email, name FROM users WHERE email = $1",
            email.value()
        )
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Database error: {}", e)))?;

        match row {
            Some(row) => {
                let user_id = UserId::from_str(&row.id.to_string())
                    .map_err(|_| DomainError::InvalidId("Invalid user ID in database".to_string()))?;
                let email = Email::new(&row.email)
                    .map_err(|e| DomainError::InvalidEmail(e.to_string()))?;
                let user = User::new(user_id, email, row.name)
                    .map_err(|e| DomainError::InvalidUser(e.to_string()))?;
                Ok(Some(user))
            }
            None => Ok(None),
        }
    }

    async fn find_by_id(&self, user_id: &UserId) -> Result<Option<User>, DomainError> {
        let row = sqlx::query!(
            "SELECT id, email, name FROM users WHERE id = $1",
            user_id.value()
        )
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Database error: {}", e)))?;

        match row {
            Some(row) => {
                let user_id = UserId::from_str(&row.id.to_string())
                    .map_err(|_| DomainError::InvalidId("Invalid user ID in database".to_string()))?;
                let email = Email::new(&row.email)
                    .map_err(|e| DomainError::InvalidEmail(e.to_string()))?;
                let user = User::new(user_id, email, row.name)
                    .map_err(|e| DomainError::InvalidUser(e.to_string()))?;
                Ok(Some(user))
            }
            None => Ok(None),
        }
    }

    async fn find_active_users_in_department(&self, department_id: &DepartmentId) -> Result<Vec<User>, DomainError> {
        let rows = sqlx::query!(
            "SELECT u.id, u.email, u.name
             FROM users u
             JOIN user_departments ud ON u.id = ud.user_id
             WHERE ud.department_id = $1 AND u.is_active = true",
            department_id.value()
        )
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Database error: {}", e)))?;

        let mut users = Vec::new();
        for row in rows {
            let user_id = UserId::from_str(&row.id.to_string())
                .map_err(|_| DomainError::InvalidId("Invalid user ID in database".to_string()))?;
            let email = Email::new(&row.email)
                .map_err(|e| DomainError::InvalidEmail(e.to_string()))?;
            let user = User::new(user_id, email, row.name)
                .map_err(|e| DomainError::InvalidUser(e.to_string()))?;
            users.push(user);
        }

        Ok(users)
    }
}
```

## Domain Event Rules

### 7. Domain Event Rules

- Domain events should be immutable value objects
- Events should represent something that happened in the past (use past tense)
- Events should contain all necessary data to handle the event
- Events should be raised by aggregates, not external code

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UserEmailChanged {
    pub user_id: UserId,
    pub old_email: Email,
    pub new_email: Email,
    pub occurred_at: DateTime<Utc>,
}

impl UserEmailChanged {
    pub fn new(user_id: UserId, old_email: Email, new_email: Email) -> Self {
        Self {
            user_id,
            old_email,
            new_email,
            occurred_at: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UserCreated {
    pub user_id: UserId,
    pub email: Email,
    pub name: String,
    pub occurred_at: DateTime<Utc>,
}

impl UserCreated {
    pub fn new(user_id: UserId, email: Email, name: String) -> Self {
        Self {
            user_id,
            email,
            name,
            occurred_at: Utc::now(),
        }
    }
}

// Base trait for all domain events
pub trait DomainEvent: Send + Sync {
    fn occurred_at(&self) -> DateTime<Utc>;
    fn event_type(&self) -> &'static str;
}

impl DomainEvent for UserEmailChanged {
    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "user_email_changed"
    }
}

impl DomainEvent for UserCreated {
    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "user_created"
    }
}
```

### 8. Event Handling Rules

- Domain event handlers should be in the application layer
- Handlers should be idempotent
- Use dependency injection for handler dependencies
- Handlers should not directly modify other aggregates
- Consider eventual consistency for cross-aggregate operations

```rust
use async_trait::async_trait;

#[async_trait]
pub trait EventHandler<T: DomainEvent>: Send + Sync {
    async fn handle(&self, event: &T) -> Result<(), EventHandlerError>;
}

pub struct SendWelcomeEmailHandler {
    email_service: Arc<dyn EmailNotificationPort>,
}

impl SendWelcomeEmailHandler {
    pub fn new(email_service: Arc<dyn EmailNotificationPort>) -> Self {
        Self { email_service }
    }
}

#[async_trait]
impl EventHandler<UserCreated> for SendWelcomeEmailHandler {
    async fn handle(&self, event: &UserCreated) -> Result<(), EventHandlerError> {
        self.email_service
            .send_welcome_email(&event.email, &event.name)
            .await
            .map_err(|e| EventHandlerError::EmailService(e.to_string()))?;
        Ok(())
    }
}

#[derive(Debug)]
pub enum EventHandlerError {
    EmailService(String),
    Repository(String),
}

impl std::fmt::Display for EventHandlerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::EmailService(msg) => write!(f, "Email service error: {}", msg),
            Self::Repository(msg) => write!(f, "Repository error: {}", msg),
        }
    }
}

impl std::error::Error for EventHandlerError {}
```

## Application Service Rules

### 9. Use Case Rules

- Use cases represent single business operations that the application can perform
- Each use case should handle exactly one business workflow
- Use cases orchestrate domain objects but contain no business logic
- Should be stateless and focused on a single responsibility
- Handle cross-cutting concerns (transactions, events, etc.)
- Should not return domain objects directly - use DTOs
- Name use cases after business operations using domain language

```rust
use async_trait::async_trait;
use std::sync::Arc;

#[derive(Debug, Clone)]
pub struct CreateUserCommand {
    pub email: String,
    pub name: String,
}

impl CreateUserCommand {
    pub fn new(email: String, name: String) -> Self {
        Self { email, name }
    }
}

#[derive(Debug, Clone)]
pub struct CreateUserResponse {
    pub user_id: String,
}

#[async_trait]
pub trait CreateUserPort: Send + Sync {
    async fn execute(&self, command: CreateUserCommand) -> Result<CreateUserResponse, UseCaseError>;
}

pub struct CreateUserUseCase {
    user_repository: Arc<dyn UserRepository>,
    unit_of_work: Arc<dyn UnitOfWork>,
    event_publisher: Arc<dyn EventPublisherPort>,
}

impl CreateUserUseCase {
    pub fn new(
        user_repository: Arc<dyn UserRepository>,
        unit_of_work: Arc<dyn UnitOfWork>,
        event_publisher: Arc<dyn EventPublisherPort>,
    ) -> Self {
        Self {
            user_repository,
            unit_of_work,
            event_publisher,
        }
    }
}

#[async_trait]
impl CreateUserPort for CreateUserUseCase {
    async fn execute(&self, command: CreateUserCommand) -> Result<CreateUserResponse, UseCaseError> {
        let result = self.unit_of_work.execute(|| async {
            // Orchestration logic only
            let email = Email::new(&command.email)
                .map_err(|e| UseCaseError::InvalidInput(e.to_string()))?;

            let user = User::create(email.clone(), command.name)
                .map_err(|e| UseCaseError::DomainError(e.to_string()))?;

            self.user_repository.save(&user)
                .await
                .map_err(UseCaseError::Repository)?;

            let event = UserCreated::new(user.id().clone(), email, user.name().to_string());
            self.event_publisher.publish(Box::new(event))
                .await
                .map_err(UseCaseError::EventPublisher)?;

            Ok(CreateUserResponse {
                user_id: user.id().value().to_string(),
            })
        }).await;

        result
    }
}

#[derive(Debug, Clone)]
pub struct ChangeEmailCommand {
    pub user_id: UserId,
    pub new_email: String,
}

impl ChangeEmailCommand {
    pub fn new(user_id: UserId, new_email: String) -> Self {
        Self { user_id, new_email }
    }
}

#[async_trait]
pub trait ChangeUserEmailPort: Send + Sync {
    async fn execute(&self, command: ChangeEmailCommand) -> Result<(), UseCaseError>;
}

pub struct ChangeUserEmailUseCase {
    user_repository: Arc<dyn UserRepository>,
    unit_of_work: Arc<dyn UnitOfWork>,
}

impl ChangeUserEmailUseCase {
    pub fn new(
        user_repository: Arc<dyn UserRepository>,
        unit_of_work: Arc<dyn UnitOfWork>,
    ) -> Self {
        Self {
            user_repository,
            unit_of_work,
        }
    }
}

#[async_trait]
impl ChangeUserEmailPort for ChangeUserEmailUseCase {
    async fn execute(&self, command: ChangeEmailCommand) -> Result<(), UseCaseError> {
        self.unit_of_work.execute(|| async {
            let mut user = self.user_repository
                .find_by_id(&command.user_id)
                .await
                .map_err(UseCaseError::Repository)?
                .ok_or(UseCaseError::UserNotFound)?;

            let new_email = Email::new(&command.new_email)
                .map_err(|e| UseCaseError::InvalidInput(e.to_string()))?;

            user.change_email(new_email);

            self.user_repository.save(&user)
                .await
                .map_err(UseCaseError::Repository)?;

            Ok(())
        }).await
    }
}

#[async_trait]
pub trait UnitOfWork: Send + Sync {
    async fn execute<F, R>(&self, work: F) -> Result<R, UseCaseError>
    where
        F: FnOnce() -> futures::future::BoxFuture<'static, Result<R, UseCaseError>> + Send,
        R: Send;
}

#[derive(Debug)]
pub enum UseCaseError {
    Repository(DomainError),
    InvalidInput(String),
    DomainError(String),
    EventPublisher(String),
    UserNotFound,
    EmailService(String),
}

impl std::fmt::Display for UseCaseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Repository(err) => write!(f, "Repository error: {}", err),
            Self::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            Self::DomainError(msg) => write!(f, "Domain error: {}", msg),
            Self::EventPublisher(msg) => write!(f, "Event publisher error: {}", msg),
            Self::UserNotFound => write!(f, "User not found"),
            Self::EmailService(msg) => write!(f, "Email service error: {}", msg),
        }
    }
}

impl std::error::Error for UseCaseError {}
```

### 10. Event Integration Rules

- Domain events should be published through infrastructure ports
- Event handlers can be implemented as separate use cases
- Use event-driven architecture for cross-bounded context communication
- Events enable loose coupling between adapters and domain logic
- Consider eventual consistency for distributed operations

```rust
use async_trait::async_trait;

// Event Publishing through Infrastructure Port
#[async_trait]
pub trait EventPublisherPort: Send + Sync {  // Application layer
    async fn publish(&self, event: Box<dyn DomainEvent>) -> Result<(), String>;
}

pub struct CreateUserUseCase {
    user_repo: Arc<dyn UserRepository>,  // Domain port
    event_publisher: Arc<dyn EventPublisherPort>,  // Infrastructure port
}

impl CreateUserUseCase {
    pub fn new(
        user_repo: Arc<dyn UserRepository>,
        event_publisher: Arc<dyn EventPublisherPort>,
    ) -> Self {
        Self {
            user_repo,
            event_publisher,
        }
    }
}

#[async_trait]
impl CreateUserPort for CreateUserUseCase {
    async fn execute(&self, command: CreateUserCommand) -> Result<CreateUserResponse, UseCaseError> {
        let email = Email::new(&command.email)
            .map_err(|e| UseCaseError::InvalidInput(e.to_string()))?;

        let user = User::create(email.clone(), command.name)
            .map_err(|e| UseCaseError::DomainError(e.to_string()))?;

        self.user_repo.save(&user)  // Domain port
            .await
            .map_err(UseCaseError::Repository)?;

        let event = UserCreated::new(user.id().clone(), user.email().clone(), user.name().to_string());
        self.event_publisher.publish(Box::new(event))  // Infrastructure port
            .await
            .map_err(UseCaseError::EventPublisher)?;

        Ok(CreateUserResponse {
            user_id: user.id().value().to_string(),
        })
    }
}

// Event Handler as Use Case
pub struct SendWelcomeEmailUseCase {
    email_service: Arc<dyn EmailNotificationPort>,  // Infrastructure port
}

impl SendWelcomeEmailUseCase {
    pub fn new(email_service: Arc<dyn EmailNotificationPort>) -> Self {
        Self { email_service }
    }

    pub async fn handle(&self, event: &UserCreated) -> Result<(), EventHandlerError> {
        self.email_service
            .send_welcome_email(&event.email, &event.name)
            .await
            .map_err(|e| EventHandlerError::EmailService(e.to_string()))?;
        Ok(())
    }
}
```

## Testing Rules

- Test domain logic in isolation without any adapters
- Test driving adapters by mocking driving ports
- Test driven adapters by mocking external dependencies
- Use in-memory implementations of driven ports for integration tests
- Test the full flow from driving adapter to driven adapter for end-to-end tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;
    use std::sync::{Arc, Mutex};
    use async_trait::async_trait;
    use tokio;

    // In-memory adapter for testing
    #[derive(Default)]
    pub struct InMemoryUserRepository {
        users: Arc<Mutex<HashMap<UserId, User>>>,
    }

    impl InMemoryUserRepository {
        pub fn new() -> Self {
            Self::default()
        }
    }

    #[async_trait]
    impl UserRepository for InMemoryUserRepository {
        async fn save(&self, user: &User) -> Result<(), DomainError> {
            let mut users = self.users.lock().unwrap();
            users.insert(user.id().clone(), user.clone());
            Ok(())
        }

        async fn find_by_email(&self, email: &Email) -> Result<Option<User>, DomainError> {
            let users = self.users.lock().unwrap();
            for user in users.values() {
                if user.email() == email {
                    return Ok(Some(user.clone()));
                }
            }
            Ok(None)
        }

        async fn find_by_id(&self, user_id: &UserId) -> Result<Option<User>, DomainError> {
            let users = self.users.lock().unwrap();
            Ok(users.get(user_id).cloned())
        }

        async fn find_active_users_in_department(&self, _department_id: &DepartmentId) -> Result<Vec<User>, DomainError> {
            Ok(Vec::new())
        }
    }

    #[derive(Default)]
    pub struct MockEventPublisher {
        published_events: Arc<Mutex<Vec<String>>>,
    }

    #[async_trait]
    impl EventPublisherPort for MockEventPublisher {
        async fn publish(&self, event: Box<dyn DomainEvent>) -> Result<(), String> {
            let mut events = self.published_events.lock().unwrap();
            events.push(event.event_type().to_string());
            Ok(())
        }
    }

    #[derive(Default)]
    pub struct MockUnitOfWork;

    #[async_trait]
    impl UnitOfWork for MockUnitOfWork {
        async fn execute<F, R>(&self, work: F) -> Result<R, UseCaseError>
        where
            F: FnOnce() -> futures::future::BoxFuture<'static, Result<R, UseCaseError>> + Send,
            R: Send,
        {
            work().await
        }
    }

    #[tokio::test]
    async fn test_create_user_success() {
        // Arrange
        let mock_repo = Arc::new(InMemoryUserRepository::new());
        let mock_events = Arc::new(MockEventPublisher::default());
        let mock_uow = Arc::new(MockUnitOfWork);
        let use_case = CreateUserUseCase::new(mock_repo.clone(), mock_uow, mock_events.clone());

        // Act
        let command = CreateUserCommand::new("test@example.com".to_string(), "John Doe".to_string());
        let result = use_case.execute(command).await;

        // Assert
        assert!(result.is_ok());
        let response = result.unwrap();
        assert!(!response.user_id.is_empty());

        // Verify user was saved
        let email = Email::new("test@example.com").unwrap();
        let saved_user = mock_repo.find_by_email(&email).await.unwrap();
        assert!(saved_user.is_some());

        // Verify event was published
        let events = mock_events.published_events.lock().unwrap();
        assert_eq!(events.len(), 1);
        assert_eq!(events[0], "user_created");
    }

    #[tokio::test]
    async fn test_change_user_email_user_not_found() {
        // Arrange
        let mock_repo = Arc::new(InMemoryUserRepository::new());
        let mock_uow = Arc::new(MockUnitOfWork);
        let use_case = ChangeUserEmailUseCase::new(mock_repo, mock_uow);

        // Act
        let command = ChangeEmailCommand::new(UserId::new(), "new@example.com".to_string());
        let result = use_case.execute(command).await;

        // Assert
        assert!(matches!(result, Err(UseCaseError::UserNotFound)));
    }

    // Contract test for all UserRepository implementations
    async fn test_user_repository_contract<T: UserRepository>(repository: Arc<T>) {
        let email = Email::new("test@example.com").unwrap();
        let user = User::create(email.clone(), "John Doe".to_string()).unwrap();

        // Test save and find
        repository.save(&user).await.unwrap();
        let found = repository.find_by_email(&email).await.unwrap();

        assert!(found.is_some());
        let found_user = found.unwrap();
        assert_eq!(found_user.email(), &email);
        assert_eq!(found_user.name(), "John Doe");
    }

    #[tokio::test]
    async fn test_in_memory_repository_contract() {
        let repository = Arc::new(InMemoryUserRepository::new());
        test_user_repository_contract(repository).await;
    }
}
```

### 11. Validation and Error Handling Rules

- Domain validation should happen in domain objects (entities, value objects)
- Use domain-specific error types that implement the `Error` trait
- Validation should be explicit and fail fast
- Input validation in application services should be minimal
- Use factory methods for complex validation scenarios

```rust
use std::fmt;

#[derive(Debug)]
pub enum DomainError {
    Validation(String),
    Repository(String),
    InvalidId(String),
    InvalidEmail(String),
    InvalidUser(String),
}

impl fmt::Display for DomainError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Validation(msg) => write!(f, "Validation error: {}", msg),
            Self::Repository(msg) => write!(f, "Repository error: {}", msg),
            Self::InvalidId(msg) => write!(f, "Invalid ID: {}", msg),
            Self::InvalidEmail(msg) => write!(f, "Invalid email: {}", msg),
            Self::InvalidUser(msg) => write!(f, "Invalid user: {}", msg),
        }
    }
}

impl std::error::Error for DomainError {}

#[derive(Debug)]
pub struct InvalidEmailError {
    email: String,
}

impl InvalidEmailError {
    pub fn new(email: &str) -> Self {
        Self {
            email: email.to_string(),
        }
    }
}

impl fmt::Display for InvalidEmailError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Invalid email: {}", self.email)
    }
}

impl std::error::Error for InvalidEmailError {}

impl Email {
    pub fn new(value: &str) -> Result<Self, InvalidEmailError> {
        if !Self::is_valid_email(value) {
            return Err(InvalidEmailError::new(value));
        }
        Ok(Self {
            value: value.to_lowercase(),
        })
    }

    fn is_valid_email(value: &str) -> bool {
        value.contains('@') && value.len() > 3
    }

    pub fn value(&self) -> &str {
        &self.value
    }
}
```

### 12. Naming Convention Rules

- Use domain language (Ubiquitous Language) for all struct and method names
- Avoid technical terms in domain layer (no "Manager", "Helper", "Util")
- Use intention-revealing names for methods
- Value objects should be named after the concept they represent
- Repository methods should reflect business queries
- **Port Naming**: End driving ports with "Port", driven ports with "Port"
- **Adapter Naming**: Include the technology/framework in driven adapter names
- **Clear Port vs Adapter distinction**: Ports define interfaces, Adapters implement them
- Use `snake_case` for functions and variables, `PascalCase` for types and traits

```rust
// Good port names
#[async_trait]
pub trait UserManagementPort {} // Driving port

#[async_trait]
pub trait EmailNotificationPort {} // Driven port

#[async_trait]
pub trait PaymentProcessingPort {} // Driven port

// Good adapter names
pub struct AxumUserController {} // Driving adapter (Axum web framework)
pub struct TarantoolUserRepository {} // Driven adapter (Tarantool database)
pub struct SqlxUserRepository {} // Driven adapter (SQLx)
pub struct SmtpEmailAdapter {} // Driven adapter (SMTP)
pub struct SendGridEmailAdapter {} // Driven adapter (SendGrid)

impl EmailNotificationPort for SmtpEmailAdapter {}
impl EmailNotificationPort for SendGridEmailAdapter {}
```

### 13. Dependency Rules

- Domain layer should have no external dependencies except standard library and common crates (uuid, chrono, etc.)
- Application layer can depend on domain but should use dependency inversion for external concerns
- Infrastructure layer implements all external dependencies through adapters
- **Domain Port Dependencies**: Domain objects can depend on domain ports (repositories, domain services)
- **Infrastructure Port Dependencies**: Use cases depend on infrastructure ports for external concerns
- **Port Placement**: Domain ports in domain layer, infrastructure ports in application layer
- **Inversion of Control**: Use DI container or manual injection to wire adapters to ports at startup
- Use dependency inversion - depend on abstractions, not concretions
- Inject dependencies through constructors
- Use builder pattern for complex object creation

```rust
use std::sync::Arc;

// Domain layer - can depend on domain ports
pub struct User {
    // Domain entity
    id: UserId,
    email: Email,
    name: String,
}

impl User {
    pub fn new(id: UserId, email: Email, name: String) -> Result<Self, DomainError> {
        let user = Self { id, email, name };
        user.validate()?;
        Ok(user)
    }

    pub fn change_email(&mut self, new_email: Email) -> UserEmailChanged {
        let old_email = self.email.clone();
        self.email = new_email.clone();
        UserEmailChanged::new(self.id.clone(), old_email, new_email)
    }

    fn validate(&self) -> Result<(), DomainError> {
        if self.name.trim().is_empty() {
            return Err(DomainError::Validation("User must have a name".to_string()));
        }
        Ok(())
    }
}

pub struct UserDomainService {
    // Domain service
    user_repo: Arc<dyn UserRepository>, // Domain port dependency
}

impl UserDomainService {
    pub fn new(user_repo: Arc<dyn UserRepository>) -> Self {
        Self { user_repo }
    }

    pub async fn is_email_unique(&self, email: &Email) -> Result<bool, DomainError> {
        let existing_user = self.user_repo.find_by_email(email).await?;
        Ok(existing_user.is_none())
    }
}

// Application layer - depends on domain + infrastructure ports
pub struct CreateUserUseCase {
    user_repo: Arc<dyn UserRepository>, // Domain port
    user_domain_service: Arc<UserDomainService>, // Domain service
    email_service: Arc<dyn EmailNotificationPort>, // Infrastructure port
    event_publisher: Arc<dyn EventPublisherPort>, // Infrastructure port
}

impl CreateUserUseCase {
    pub fn new(
        user_repo: Arc<dyn UserRepository>,
        user_domain_service: Arc<UserDomainService>,
        email_service: Arc<dyn EmailNotificationPort>,
        event_publisher: Arc<dyn EventPublisherPort>,
    ) -> Self {
        Self {
            user_repo,
            user_domain_service,
            email_service,
            event_publisher,
        }
    }
}

// Infrastructure layer - implements ports with external dependencies
pub struct SqlxUserRepository {
    // Implements domain port
    pool: sqlx::PgPool, // External dependency
}

impl SqlxUserRepository {
    pub fn new(pool: sqlx::PgPool) -> Self {
        Self { pool }
    }
}

pub struct SmtpEmailAdapter {
    // Implements infrastructure port
    smtp_client: lettre::SmtpTransport, // External dependency
}

impl SmtpEmailAdapter {
    pub fn new(smtp_client: lettre::SmtpTransport) -> Self {
        Self { smtp_client }
    }
}
```

### 14. Testing Rules

- Write unit tests for domain logic without mocking domain objects
- **Test Ports in Isolation**: Mock driven ports when testing use cases
- **Test Adapters Separately**: Test each adapter implementation independently
- **Integration Testing**: Use in-memory adapters for full workflow testing
- Test domain events are raised correctly
- Integration tests should test aggregate boundaries
- Use builders or factories for test data creation
- **Contract Testing**: Ensure all adapter implementations satisfy their port contracts
- **Use Case Testing**: Test each use case independently with mocked dependencies

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Arc, Mutex};
    use tokio_test;

    // Contract test for all UserRepository implementations
    async fn user_repository_contract_test<T: UserRepository>(repository: Arc<T>) {
        // This test should pass for all UserRepository implementations
        let email = Email::new("test@example.com").unwrap();
        let user = User::create(email.clone(), "John Doe".to_string()).unwrap();

        repository.save(&user).await.unwrap();
        let found = repository.find_by_email(&email).await.unwrap();

        assert!(found.is_some());
        let found_user = found.unwrap();
        assert_eq!(found_user.email(), &email);
    }

    #[tokio::test]
    async fn sqlx_user_repository_satisfies_contract() {
        let pool = create_test_pool().await;
        let repository = Arc::new(SqlxUserRepository::new(pool));
        user_repository_contract_test(repository).await;
    }

    #[tokio::test]
    async fn in_memory_user_repository_satisfies_contract() {
        let repository = Arc::new(InMemoryUserRepository::new());
        user_repository_contract_test(repository).await;
    }

    // Use Case Integration Test
    #[tokio::test]
    async fn create_user_use_case_full_workflow_with_in_memory_adapters() {
        // Arrange
        let user_repo = Arc::new(InMemoryUserRepository::new());
        let email_service = Arc::new(InMemoryEmailService::new());
        let event_publisher = Arc::new(InMemoryEventPublisher::new());
        let use_case = CreateUserUseCase::new(user_repo.clone(), email_service.clone(), event_publisher.clone());

        // Act
        let command = CreateUserCommand::new("test@example.com".to_string(), "John".to_string());
        let result = use_case.execute(command).await;

        // Assert
        assert!(result.is_ok());
        let response = result.unwrap();
        assert!(!response.user_id.is_empty());

        let email = Email::new("test@example.com").unwrap();
        let saved_user = user_repo.find_by_email(&email).await.unwrap();
        assert!(saved_user.is_some());
        assert_eq!(email_service.sent_emails().len(), 1);
        assert_eq!(event_publisher.published_events().len(), 1);
    }

    // Technology-specific adapter testing
    #[tokio::test]
    async fn sqlx_user_repository_save_user_with_sql_models() {
        // Arrange
        let pool = create_test_pool().await;
        let repository = SqlxUserRepository::new(pool.clone());
        let email = Email::new("test@example.com").unwrap();
        let user = User::create(email.clone(), "John".to_string()).unwrap();

        // Act
        repository.save(&user).await.unwrap();

        // Assert
        let saved_user = repository.find_by_email(&email).await.unwrap();
        assert!(saved_user.is_some());
        let saved_user = saved_user.unwrap();
        assert_eq!(saved_user.email(), &email);

        // Verify SQL model was created correctly
        let row = sqlx::query!("SELECT * FROM users WHERE email = $1", "test@example.com")
            .fetch_one(&pool)
            .await
            .unwrap();
        assert_eq!(row.name, "John");
    }

    async fn create_test_pool() -> sqlx::PgPool {
        // Test database setup
        sqlx::PgPoolOptions::new()
            .max_connections(5)
            .connect("postgres://test:test@localhost/test_db")
            .await
            .unwrap()
    }
}
```

## Ports & Adapters (Hexagonal Architecture) Rules

### 1. Port Definition Rules

- Ports define interfaces between layers and external systems using traits
- **Driving ports** (primary/left-side) define application use cases - belong in application layer
- **Domain-driven driven ports** (repositories, domain services) - belong in domain layer
- **Infrastructure driven ports** (email, messaging, external APIs) - belong in application layer
- Port interfaces should use domain language, not technical terms
- Ports should be focused and follow Single Responsibility Principle

```rust
use async_trait::async_trait;

// Driving Ports (Application Layer) - application/ports/driving/
#[async_trait]
pub trait CreateUserPort: Send + Sync {
    async fn execute(&self, command: CreateUserCommand) -> Result<CreateUserResponse, UseCaseError>;
}

#[async_trait]
pub trait ChangeUserEmailPort: Send + Sync {
    async fn execute(&self, command: ChangeEmailCommand) -> Result<(), UseCaseError>;
}

// Domain-Driven Driven Ports (Domain Layer) - domain/repositories/
#[async_trait]
pub trait UserRepository: Send + Sync {
    // Already shown in rule 5
    async fn find_by_email(&self, email: &Email) -> Result<Option<User>, DomainError>;
    async fn save(&self, user: &User) -> Result<(), DomainError>;
    async fn find_by_id(&self, user_id: &UserId) -> Result<Option<User>, DomainError>;
}

// Domain Services (Domain Layer) - domain/services/
#[async_trait]
pub trait PricingServicePort: Send + Sync {
    async fn calculate_product_price(&self, product: &Product, customer: &Customer) -> Result<Money, DomainError>;
}

// Infrastructure Driven Ports (Application Layer) - application/ports/driven/
#[async_trait]
pub trait EmailNotificationPort: Send + Sync {
    async fn send_welcome_email(&self, user_email: &Email, user_name: &str) -> Result<(), String>;
    async fn send_email_change_notification(&self, old_email: &Email, new_email: &Email, timestamp: DateTime<Utc>) -> Result<(), String>;
}

#[async_trait]
pub trait EventPublisherPort: Send + Sync {
    async fn publish(&self, event: Box<dyn DomainEvent>) -> Result<(), String>;
}

#[async_trait]
pub trait TimeProviderPort: Send + Sync {
    fn now(&self) -> DateTime<Utc>;
}
```

### 2. Driving Adapter Rules

- Driving adapters are the entry points (web controllers, CLI, message consumers)
- Should translate external requests to domain commands/queries
- Must not contain business logic - only translation and validation
- Should handle framework-specific concerns (HTTP status codes, serialization)
- Should be thin and delegate to use cases through driving ports

```rust
use axum::{
    extract::{Path, Json},
    http::StatusCode,
    response::{Json as ResponseJson, IntoResponse},
    routing::{post, patch},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[derive(Debug, Deserialize)]
pub struct CreateUserRequest {
    pub email: String,
    pub name: String,
}

#[derive(Debug, Deserialize)]
pub struct ChangeEmailRequest {
    pub email: String,
}

#[derive(Debug, Serialize)]
pub struct CreateUserResponse {
    pub user_id: String,
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
}

pub struct AxumUserController {
    create_user_use_case: Arc<dyn CreateUserPort>,
    change_email_use_case: Arc<dyn ChangeUserEmailPort>,
}

impl AxumUserController {
    pub fn new(
        create_user_use_case: Arc<dyn CreateUserPort>,
        change_email_use_case: Arc<dyn ChangeUserEmailPort>,
    ) -> Self {
        Self {
            create_user_use_case,
            change_email_use_case,
        }
    }

    pub async fn create_user(
        &self,
        Json(request): Json<CreateUserRequest>,
    ) -> Result<impl IntoResponse, impl IntoResponse> {
        // Input validation
        if request.email.is_empty() || request.name.is_empty() {
            return Err((
                StatusCode::BAD_REQUEST,
                ResponseJson(ErrorResponse {
                    error: "Email and name are required".to_string(),
                }),
            ));
        }

        let command = CreateUserCommand::new(request.email, request.name);

        match self.create_user_use_case.execute(command).await {
            Ok(response) => Ok((
                StatusCode::CREATED,
                ResponseJson(CreateUserResponse {
                    user_id: response.user_id,
                }),
            )),
            Err(UseCaseError::InvalidInput(msg)) => Err((
                StatusCode::BAD_REQUEST,
                ResponseJson(ErrorResponse { error: msg }),
            )),
            Err(UseCaseError::DomainError(msg)) => Err((
                StatusCode::BAD_REQUEST,
                ResponseJson(ErrorResponse { error: msg }),
            )),
            Err(UseCaseError::Repository(_)) => Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                ResponseJson(ErrorResponse {
                    error: "Internal server error".to_string(),
                }),
            )),
            Err(_) => Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                ResponseJson(ErrorResponse {
                    error: "Internal server error".to_string(),
                }),
            )),
        }
    }

    pub async fn change_user_email(
        &self,
        Path(user_id): Path<String>,
        Json(request): Json<ChangeEmailRequest>,
    ) -> Result<impl IntoResponse, impl IntoResponse> {
        let user_id = match UserId::from_str(&user_id) {
            Ok(id) => id,
            Err(_) => {
                return Err((
                    StatusCode::BAD_REQUEST,
                    ResponseJson(ErrorResponse {
                        error: "Invalid user ID".to_string(),
                    }),
                ))
            }
        };

        let command = ChangeEmailCommand::new(user_id, request.email);

        match self.change_email_use_case.execute(command).await {
            Ok(_) => Ok(StatusCode::NO_CONTENT),
            Err(UseCaseError::UserNotFound) => Err((
                StatusCode::NOT_FOUND,
                ResponseJson(ErrorResponse {
                    error: "User not found".to_string(),
                }),
            )),
            Err(UseCaseError::InvalidInput(msg)) => Err((
                StatusCode::BAD_REQUEST,
                ResponseJson(ErrorResponse { error: msg }),
            )),
            Err(UseCaseError::DomainError(msg)) => Err((
                StatusCode::BAD_REQUEST,
                ResponseJson(ErrorResponse { error: msg }),
            )),
            Err(_) => Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                ResponseJson(ErrorResponse {
                    error: "Internal server error".to_string(),
                }),
            )),
        }
    }

    pub fn router(self: Arc<Self>) -> Router {
        Router::new()
            .route("/users", post({
                let controller = self.clone();
                move |request| async move { controller.create_user(request).await }
            }))
            .route("/users/:user_id/email", patch({
                let controller = self.clone();
                move |path, request| async move { controller.change_user_email(path, request).await }
            }))
    }
}
```

### 3. Driven Adapter Rules

- Driven adapters implement driven ports defined in domain/application layers
- Organize driven adapters by technology for shared infrastructure and easier maintenance
- Should handle all external system complexities (database mapping, API calls, etc.)
- Must translate between domain objects and external representations
- Should not expose external system details to the domain
- Include error handling and retry logic when appropriate
- Keep technology-specific models/schemas within their adapter implementations

```rust
use sqlx::{PgPool, FromRow};
use async_trait::async_trait;
use reqwest::Client;
use serde::{Deserialize, Serialize};

// SQL Database Adapter - infrastructure/adapters/driven/sqlx/sqlx_user_repository.rs
#[derive(FromRow)]
struct UserModel {
    id: sqlx::types::Uuid,
    email: String,
    name: String,
    version: i32,
}

pub struct SqlxUserRepository {
    pool: PgPool,
}

impl SqlxUserRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    fn to_domain(&self, model: UserModel) -> Result<User, DomainError> {
        let user_id = UserId::from_str(&model.id.to_string())
            .map_err(|_| DomainError::InvalidId("Invalid user ID in database".to_string()))?;
        let email = Email::new(&model.email)
            .map_err(|e| DomainError::InvalidEmail(e.to_string()))?;
        User::new(user_id, email, model.name)
    }

    fn to_model(&self, user: &User) -> UserModel {
        UserModel {
            id: *user.id().value(),
            email: user.email().value().to_string(),
            name: user.name().to_string(),
            version: 1,
        }
    }
}

#[async_trait]
impl UserRepository for SqlxUserRepository {
    async fn save(&self, user: &User) -> Result<(), DomainError> {
        let model = self.to_model(user);

        sqlx::query!(
            r#"
            INSERT INTO users (id, email, name, version)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                name = EXCLUDED.name,
                version = users.version + 1
            "#,
            model.id,
            model.email,
            model.name,
            model.version
        )
        .execute(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Failed to save user: {}", e)))?;

        Ok(())
    }

    async fn find_by_email(&self, email: &Email) -> Result<Option<User>, DomainError> {
        let model = sqlx::query_as::<_, UserModel>(
            "SELECT id, email, name, version FROM users WHERE email = $1"
        )
        .bind(email.value())
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Database error: {}", e)))?;

        match model {
            Some(model) => Ok(Some(self.to_domain(model)?)),
            None => Ok(None),
        }
    }

    async fn find_by_id(&self, user_id: &UserId) -> Result<Option<User>, DomainError> {
        let model = sqlx::query_as::<_, UserModel>(
            "SELECT id, email, name, version FROM users WHERE id = $1"
        )
        .bind(user_id.value())
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Database error: {}", e)))?;

        match model {
            Some(model) => Ok(Some(self.to_domain(model)?)),
            None => Ok(None),
        }
    }

    async fn find_active_users_in_department(&self, department_id: &DepartmentId) -> Result<Vec<User>, DomainError> {
        let models = sqlx::query_as::<_, UserModel>(
            r#"
            SELECT u.id, u.email, u.name, u.version
            FROM users u
            JOIN user_departments ud ON u.id = ud.user_id
            WHERE ud.department_id = $1 AND u.is_active = true
            "#
        )
        .bind(department_id.value())
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::Repository(format!("Database error: {}", e)))?;

        let mut users = Vec::new();
        for model in models {
            users.push(self.to_domain(model)?);
        }

        Ok(users)
    }
}

// HTTP External Service Adapter - infrastructure/adapters/driven/http/http_email_service.rs
#[derive(Serialize)]
struct EmailPayload {
    to: String,
    template: String,
    variables: serde_json::Value,
}

#[derive(Deserialize)]
struct EmailResponse {
    message_id: String,
}

pub struct HttpEmailNotificationAdapter {
    client: Client,
    base_url: String,
    api_key: String,
}

impl HttpEmailNotificationAdapter {
    pub fn new(base_url: String, api_key: String) -> Self {
        Self {
            client: Client::new(),
            base_url,
            api_key,
        }
    }
}

#[async_trait]
impl EmailNotificationPort for HttpEmailNotificationAdapter {
    async fn send_welcome_email(&self, user_email: &Email, user_name: &str) -> Result<(), String> {
        let payload = EmailPayload {
            to: user_email.value().to_string(),
            template: "welcome".to_string(),
            variables: serde_json::json!({ "name": user_name }),
        };

        let response = self
            .client
            .post(&format!("{}/send", self.base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&payload)
            .send()
            .await
            .map_err(|e| format!("Failed to send request: {}", e))?;

        if !response.status().is_success() {
            return Err(format!("Email service returned error: {}", response.status()));
        }

        let _response_body: EmailResponse = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse response: {}", e))?;

        Ok(())
    }

    async fn send_email_change_notification(
        &self,
        old_email: &Email,
        new_email: &Email,
        _timestamp: DateTime<Utc>,
    ) -> Result<(), String> {
        let payload = EmailPayload {
            to: new_email.value().to_string(),
            template: "email-changed".to_string(),
            variables: serde_json::json!({
                "old_email": old_email.value(),
                "new_email": new_email.value()
            }),
        };

        let response = self
            .client
            .post(&format!("{}/send", self.base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&payload)
            .send()
            .await
            .map_err(|e| format!("Failed to send request: {}", e))?;

        if !response.status().is_success() {
            return Err(format!("Email service returned error: {}", response.status()));
        }

        Ok(())
    }
}

// Time Provider Adapter
pub struct SystemTimeProvider;

impl SystemTimeProvider {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl TimeProviderPort for SystemTimeProvider {
    fn now(&self) -> DateTime<Utc> {
        Utc::now()
    }
}

// Test Time Provider for deterministic testing
pub struct MockTimeProvider {
    fixed_time: DateTime<Utc>,
}

impl MockTimeProvider {
    pub fn new(fixed_time: DateTime<Utc>) -> Self {
        Self { fixed_time }
    }
}

#[async_trait]
impl TimeProviderPort for MockTimeProvider {
    fn now(&self) -> DateTime<Utc> {
        self.fixed_time
    }
}
```

## Comprehensive Infrastructure Adapter Patterns

### File System Adapter

```rust
use async_trait::async_trait;
use tokio::fs;
use std::path::Path;

#[async_trait]
pub trait FileSystemPort: Send + Sync {
    async fn read_file(&self, path: &str) -> Result<String, String>;
    async fn write_file(&self, path: &str, content: &str) -> Result<(), String>;
    async fn file_exists(&self, path: &str) -> Result<bool, String>;
    async fn delete_file(&self, path: &str) -> Result<(), String>;
}

pub struct TokioFileSystemAdapter;

impl TokioFileSystemAdapter {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl FileSystemPort for TokioFileSystemAdapter {
    async fn read_file(&self, path: &str) -> Result<String, String> {
        fs::read_to_string(path)
            .await
            .map_err(|e| format!("Failed to read file {}: {}", path, e))
    }

    async fn write_file(&self, path: &str, content: &str) -> Result<(), String> {
        if let Some(parent) = Path::new(path).parent() {
            fs::create_dir_all(parent)
                .await
                .map_err(|e| format!("Failed to create directory: {}", e))?;
        }

        fs::write(path, content)
            .await
            .map_err(|e| format!("Failed to write file {}: {}", path, e))
    }

    async fn file_exists(&self, path: &str) -> Result<bool, String> {
        Ok(Path::new(path).exists())
    }

    async fn delete_file(&self, path: &str) -> Result<(), String> {
        fs::remove_file(path)
            .await
            .map_err(|e| format!("Failed to delete file {}: {}", path, e))
    }
}

// In-memory implementation for testing
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

pub struct InMemoryFileSystemAdapter {
    files: Arc<Mutex<HashMap<String, String>>>,
}

impl InMemoryFileSystemAdapter {
    pub fn new() -> Self {
        Self {
            files: Arc::new(Mutex::new(HashMap::new())),
        }
    }
}

#[async_trait]
impl FileSystemPort for InMemoryFileSystemAdapter {
    async fn read_file(&self, path: &str) -> Result<String, String> {
        let files = self.files.lock().unwrap();
        files
            .get(path)
            .cloned()
            .ok_or_else(|| format!("File not found: {}", path))
    }

    async fn write_file(&self, path: &str, content: &str) -> Result<(), String> {
        let mut files = self.files.lock().unwrap();
        files.insert(path.to_string(), content.to_string());
        Ok(())
    }

    async fn file_exists(&self, path: &str) -> Result<bool, String> {
        let files = self.files.lock().unwrap();
        Ok(files.contains_key(path))
    }

    async fn delete_file(&self, path: &str) -> Result<(), String> {
        let mut files = self.files.lock().unwrap();
        files.remove(path);
        Ok(())
    }
}
```

### Random Number Generation Adapter

```rust
use async_trait::async_trait;
use rand::{Rng, thread_rng};

#[async_trait]
pub trait RandomNumberGeneratorPort: Send + Sync {
    fn generate_u32(&self) -> u32;
    fn generate_range(&self, min: i32, max: i32) -> i32;
    fn generate_boolean(&self) -> bool;
}

pub struct ThreadRngAdapter;

impl ThreadRngAdapter {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl RandomNumberGeneratorPort for ThreadRngAdapter {
    fn generate_u32(&self) -> u32 {
        thread_rng().gen()
    }

    fn generate_range(&self, min: i32, max: i32) -> i32 {
        thread_rng().gen_range(min..=max)
    }

    fn generate_boolean(&self) -> bool {
        thread_rng().gen()
    }
}

// Deterministic implementation for testing
pub struct MockRandomNumberGenerator {
    fixed_value: u32,
}

impl MockRandomNumberGenerator {
    pub fn new(fixed_value: u32) -> Self {
        Self { fixed_value }
    }
}

#[async_trait]
impl RandomNumberGeneratorPort for MockRandomNumberGenerator {
    fn generate_u32(&self) -> u32 {
        self.fixed_value
    }

    fn generate_range(&self, _min: i32, _max: i32) -> i32 {
        self.fixed_value as i32
    }

    fn generate_boolean(&self) -> bool {
        self.fixed_value % 2 == 0
    }
}
```

### ID Generation Adapter

```rust
use async_trait::async_trait;
use uuid::Uuid;

#[async_trait]
pub trait IdGeneratorPort: Send + Sync {
    fn generate_user_id(&self) -> UserId;
    fn generate_order_id(&self) -> OrderId;
    fn generate_uuid(&self) -> Uuid;
}

pub struct UuidGeneratorAdapter;

impl UuidGeneratorAdapter {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl IdGeneratorPort for UuidGeneratorAdapter {
    fn generate_user_id(&self) -> UserId {
        UserId::new()
    }

    fn generate_order_id(&self) -> OrderId {
        OrderId::new()
    }

    fn generate_uuid(&self) -> Uuid {
        Uuid::new_v4()
    }
}

// Predictable implementation for testing
pub struct MockIdGenerator {
    fixed_id: Uuid,
}

impl MockIdGenerator {
    pub fn new(fixed_id: Uuid) -> Self {
        Self { fixed_id }
    }
}

#[async_trait]
impl IdGeneratorPort for MockIdGenerator {
    fn generate_user_id(&self) -> UserId {
        UserId(self.fixed_id)
    }

    fn generate_order_id(&self) -> OrderId {
        OrderId(self.fixed_id)
    }

    fn generate_uuid(&self) -> Uuid {
        self.fixed_id
    }
}
```

### External API Adapter

```rust
use async_trait::async_trait;
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentRequest {
    pub amount: rust_decimal::Decimal,
    pub currency: String,
    pub payment_method: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentResponse {
    pub payment_id: String,
    pub status: String,
}

#[async_trait]
pub trait PaymentProcessingPort: Send + Sync {
    async fn process_payment(&self, request: PaymentRequest) -> Result<PaymentResponse, String>;
    async fn get_payment_status(&self, payment_id: &str) -> Result<String, String>;
}

pub struct StripePaymentAdapter {
    client: Client,
    api_key: String,
    base_url: String,
}

impl StripePaymentAdapter {
    pub fn new(api_key: String) -> Self {
        Self {
            client: Client::new(),
            api_key,
            base_url: "https://api.stripe.com/v1".to_string(),
        }
    }
}

#[async_trait]
impl PaymentProcessingPort for StripePaymentAdapter {
    async fn process_payment(&self, request: PaymentRequest) -> Result<PaymentResponse, String> {
        let stripe_request = serde_json::json!({
            "amount": (request.amount * rust_decimal::Decimal::new(100, 0)).to_u64().unwrap(),
            "currency": request.currency.to_lowercase(),
            "payment_method": request.payment_method,
            "confirm": true
        });

        let response = self
            .client
            .post(&format!("{}/payment_intents", self.base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&stripe_request)
            .send()
            .await
            .map_err(|e| format!("Failed to send payment request: {}", e))?;

        if !response.status().is_success() {
            return Err(format!("Payment failed with status: {}", response.status()));
        }

        let stripe_response: serde_json::Value = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse payment response: {}", e))?;

        Ok(PaymentResponse {
            payment_id: stripe_response["id"]
                .as_str()
                .unwrap_or_default()
                .to_string(),
            status: stripe_response["status"]
                .as_str()
                .unwrap_or_default()
                .to_string(),
        })
    }

    async fn get_payment_status(&self, payment_id: &str) -> Result<String, String> {
        let response = self
            .client
            .get(&format!("{}/payment_intents/{}", self.base_url, payment_id))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .send()
            .await
            .map_err(|e| format!("Failed to get payment status: {}", e))?;

        if !response.status().is_success() {
            return Err(format!("Failed to get payment status: {}", response.status()));
        }

        let payment_intent: serde_json::Value = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse payment status response: {}", e))?;

        Ok(payment_intent["status"]
            .as_str()
            .unwrap_or("unknown")
            .to_string())
    }
}

// Mock implementation for testing
pub struct MockPaymentProcessor {
    should_succeed: bool,
}

impl MockPaymentProcessor {
    pub fn new(should_succeed: bool) -> Self {
        Self { should_succeed }
    }
}

#[async_trait]
impl PaymentProcessingPort for MockPaymentProcessor {
    async fn process_payment(&self, request: PaymentRequest) -> Result<PaymentResponse, String> {
        if self.should_succeed {
            Ok(PaymentResponse {
                payment_id: "mock_payment_123".to_string(),
                status: "succeeded".to_string(),
            })
        } else {
            Err("Payment processing failed".to_string())
        }
    }

    async fn get_payment_status(&self, _payment_id: &str) -> Result<String, String> {
        Ok("succeeded".to_string())
    }
}
```

These integrated rules ensure that Domain Driven Design and Ports & Adapters (Hexagonal Architecture) work together seamlessly in Rust implementations. The combination provides clean separation of concerns, testability, and flexibility while maintaining domain focus and proper dependency management.

## Appendix

### Cargo.toml Dependencies

Here's a typical `Cargo.toml` for a DDD + Ports & Adapters Rust project:

```toml
[package]
name = "ddd-ports-adapters-example"
version = "0.1.0"
edition = "2021"

[dependencies]
# Core async runtime
tokio = { version = "1.0", features = ["full"] }
futures = "0.3"
async-trait = "0.1"

# Web framework (choose one)
axum = { version = "0.7", features = ["macros"] }
# warp = "0.3" # Alternative web framework

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Database (choose based on your needs)
sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "postgres", "uuid", "chrono"] }
# diesel = { version = "2.0", features = ["postgres", "uuid", "chrono"] } # Alternative ORM

# HTTP client
reqwest = { version = "0.11", features = ["json"] }

# Utilities
uuid = { version = "1.0", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
rust_decimal = { version = "1.0", features = ["serde"] }
regex = "1.0"
rand = "0.8"

# Email
lettre = "0.10" # SMTP client

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

[dev-dependencies]
tokio-test = "0.4"
mockall = "0.11" # For creating mocks
```
