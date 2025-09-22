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

- **Driving Ports** define what your application can do (use case interfaces)
- **Driven Ports** define what your application needs (repositories, external services)
- **Driving Adapters** translate external requests into domain operations (REST controllers, CLI)
- **Driven Adapters** implement external integrations (databases, APIs, file systems)

### How They Connect in Practice

```go
package main

import (
    "context"
    "time"
)

// 1. Domain Layer (DDD Core)
type User struct {
    id    UserID
    email Email
    name  string
}

func NewUser(id UserID, email Email, name string) (*User, error) {
    if err := email.Validate(); err != nil {
        return nil, err
    }
    if name == "" {
        return nil, errors.New("name cannot be empty")
    }
    return &User{id: id, email: email, name: name}, nil
}

// Rule 1: Entity with identity and business behavior
func (u *User) ChangeEmail(newEmail Email) (*UserEmailChanged, error) {
    if err := newEmail.Validate(); err != nil {
        return nil, err
    }
    oldEmail := u.email
    u.email = newEmail
    return &UserEmailChanged{
        UserID:     u.id,
        OldEmail:   oldEmail,
        NewEmail:   newEmail,
        OccurredAt: time.Now(),
    }, nil
}

// Rule 5: Domain port for persistence
type UserRepository interface {
    Save(ctx context.Context, user *User) error
    FindByID(ctx context.Context, id UserID) (*User, error)
}

// 2. Application Layer (Bridge between DDD and Ports & Adapters)
type ChangeUserEmailUseCase struct {
    userRepo      UserRepository                // Domain port
    emailService  EmailNotificationPort         // Infrastructure port
    timeProvider  TimeProviderPort              // Infrastructure port
}

func NewChangeUserEmailUseCase(
    userRepo UserRepository,
    emailService EmailNotificationPort,
    timeProvider TimeProviderPort,
) *ChangeUserEmailUseCase {
    return &ChangeUserEmailUseCase{
        userRepo:     userRepo,
        emailService: emailService,
        timeProvider: timeProvider,
    }
}

// Rule 9 + P&A Rule 1: Use case orchestrates domain objects
func (uc *ChangeUserEmailUseCase) Execute(ctx context.Context, cmd ChangeEmailCommand) error {
    user, err := uc.userRepo.FindByID(ctx, cmd.UserID)
    if err != nil {
        return err
    }
    if user == nil {
        return NewUserNotFoundError(cmd.UserID)
    }

    event, err := user.ChangeEmail(cmd.NewEmail)
    if err != nil {
        return err
    }

    if err := uc.userRepo.Save(ctx, user); err != nil {
        return err
    }

    return uc.emailService.SendEmailChangeNotification(
        ctx,
        event.OldEmail,
        event.NewEmail,
        uc.timeProvider.Now(),
    )
}

// 3. Infrastructure Layer (Ports & Adapters Implementation)
type SQLUserRepository struct {
    db *sql.DB
}

func NewSQLUserRepository(db *sql.DB) *SQLUserRepository {
    return &SQLUserRepository{db: db}
}

// P&A Rule 3: Driven adapter implementation
func (r *SQLUserRepository) Save(ctx context.Context, user *User) error {
    // Handle SQL mapping, database specifics
    query := `UPDATE users SET email = ?, name = ? WHERE id = ?`
    _, err := r.db.ExecContext(ctx, query, user.email.Value(), user.name, user.id.Value())
    return err
}

type RestUserController struct {
    useCase ChangeUserEmailPort
}

func NewRestUserController(useCase ChangeUserEmailPort) *RestUserController {
    return &RestUserController{useCase: useCase}
}

// P&A Rule 2: Driving adapter
func (c *RestUserController) PatchUserEmail(ctx *gin.Context) {
    var req ChangeEmailRequest
    if err := ctx.ShouldBindJSON(&req); err != nil {
        ctx.JSON(400, gin.H{"error": err.Error()})
        return
    }

    userID, err := ParseUserID(ctx.Param("id"))
    if err != nil {
        ctx.JSON(400, gin.H{"error": "invalid user ID"})
        return
    }

    cmd := ChangeEmailCommand{
        UserID:   userID,
        NewEmail: NewEmail(req.Email),
    }

    if err := c.useCase.Execute(ctx.Request.Context(), cmd); err != nil {
        switch err.(type) {
        case *UserNotFoundError:
            ctx.JSON(404, gin.H{"error": err.Error()})
        case *InvalidEmailError:
            ctx.JSON(400, gin.H{"error": err.Error()})
        default:
            ctx.JSON(500, gin.H{"error": "internal server error"})
        }
        return
    }

    ctx.Status(204)
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
- Implement `equality` based solely on identity, not attributes/fields
- Entities MUST contain business logic as methods, not just data
  - Avoid anemic domain models - entities should have behavior
- Include validation in constructor
- Use proper Go error handling with explicit error returns

```go
package domain

import (
    "errors"
    "fmt"
)

type UserID struct {
    value string
}

func NewUserID(value string) (UserID, error) {
    if value == "" {
        return UserID{}, errors.New("user ID cannot be empty")
    }
    return UserID{value: value}, nil
}

func GenerateUserID() UserID {
    // Use UUID library or similar
    return UserID{value: uuid.New().String()}
}

func (id UserID) Value() string {
    return id.value
}

func (id UserID) Equals(other UserID) bool {
    return id.value == other.value
}

type User struct {
    id    UserID
    email Email
    name  string
}

func NewUser(id UserID, email Email, name string) (*User, error) {
    user := &User{
        id:    id,
        email: email,
        name:  name,
    }
    if err := user.validate(); err != nil {
        return nil, err
    }
    return user, nil
}

func CreateUser(email Email, name string) (*User, error) {
    return NewUser(GenerateUserID(), email, name)
}

// Business behavior - not just getters and setters
func (u *User) ChangeEmail(newEmail Email) error {
    if err := newEmail.Validate(); err != nil {
        return fmt.Errorf("invalid email: %w", err)
    }
    u.email = newEmail
    return nil
}

func (u *User) ID() UserID {
    return u.id
}

func (u *User) Email() Email {
    return u.email
}

func (u *User) Name() string {
    return u.name
}

func (u *User) Equals(other *User) bool {
    if other == nil {
        return false
    }
    return u.id.Equals(other.id)
}

func (u *User) validate() error {
    if err := u.email.Validate(); err != nil {
        return fmt.Errorf("invalid email: %w", err)
    }
    if u.name == "" {
        return errors.New("user must have a name")
    }
    return nil
}
```

### 2. Value Object Rules

- Value objects MUST be immutable
- Equality is based on ALL attributes, not identity
- Should be small, focused, and represent a concept from the domain
- Include validation in constructor
- Should have meaningful methods that operate on the value
- Use struct values in Go, not pointers, to ensure immutability

```go
package domain

import (
    "errors"
    "strings"
)

type Email struct {
    value string
}

func NewEmail(value string) (Email, error) {
    if !strings.Contains(value, "@") {
        return Email{}, errors.New("invalid email format")
    }
    return Email{value: strings.ToLower(value)}, nil
}

func (e Email) Value() string {
    return e.value
}

func (e Email) Domain() string {
    parts := strings.Split(e.value, "@")
    if len(parts) != 2 {
        return ""
    }
    return parts[1]
}

func (e Email) Validate() error {
    if !strings.Contains(e.value, "@") {
        return errors.New("invalid email format")
    }
    return nil
}

func (e Email) Equals(other Email) bool {
    return e.value == other.value
}

func (e Email) String() string {
    return e.value
}

// Money value object example
type Money struct {
    amount   int64  // Store as cents to avoid floating point issues
    currency string
}

func NewMoney(amount int64, currency string) (Money, error) {
    if currency == "" {
        return Money{}, errors.New("currency cannot be empty")
    }
    return Money{amount: amount, currency: strings.ToUpper(currency)}, nil
}

func (m Money) Amount() int64 {
    return m.amount
}

func (m Money) Currency() string {
    return m.currency
}

func (m Money) Add(other Money) (Money, error) {
    if m.currency != other.currency {
        return Money{}, errors.New("cannot add money with different currencies")
    }
    return Money{
        amount:   m.amount + other.amount,
        currency: m.currency,
    }, nil
}

func (m Money) Equals(other Money) bool {
    return m.amount == other.amount && m.currency == other.currency
}
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
- Encapsulate Collections: Use proper encapsulation for collections

```go
package domain

import (
    "errors"
    "fmt"
)

type OrderID struct {
    value string
}

func NewOrderID(value string) (OrderID, error) {
    if value == "" {
        return OrderID{}, errors.New("order ID cannot be empty")
    }
    return OrderID{value: value}, nil
}

func GenerateOrderID() OrderID {
    return OrderID{value: uuid.New().String()}
}

func (id OrderID) Value() string {
    return id.value
}

func (id OrderID) Equals(other OrderID) bool {
    return id.value == other.value
}

type ProductID struct {
    value string
}

func NewProductID(value string) (ProductID, error) {
    if value == "" {
        return ProductID{}, errors.New("product ID cannot be empty")
    }
    return ProductID{value: value}, nil
}

func (id ProductID) Value() string {
    return id.value
}

type CustomerID struct {
    value string
}

func NewCustomerID(value string) (CustomerID, error) {
    if value == "" {
        return CustomerID{}, errors.New("customer ID cannot be empty")
    }
    return CustomerID{value: value}, nil
}

func (id CustomerID) Value() string {
    return id.value
}

type OrderLineItem struct {
    productID ProductID
    quantity  int
    unitPrice Money
}

func NewOrderLineItem(productID ProductID, quantity int, unitPrice Money) (*OrderLineItem, error) {
    if quantity <= 0 {
        return nil, errors.New("quantity must be positive")
    }
    return &OrderLineItem{
        productID: productID,
        quantity:  quantity,
        unitPrice: unitPrice,
    }, nil
}

func (oli *OrderLineItem) ProductID() ProductID {
    return oli.productID
}

func (oli *OrderLineItem) Quantity() int {
    return oli.quantity
}

func (oli *OrderLineItem) UnitPrice() Money {
    return oli.unitPrice
}

func (oli *OrderLineItem) Total() (Money, error) {
    totalAmount := oli.unitPrice.Amount() * int64(oli.quantity)
    return NewMoney(totalAmount, oli.unitPrice.Currency())
}

// Order is the Aggregate Root
type Order struct {
    id         OrderID
    customerID CustomerID
    lineItems  []*OrderLineItem
    status     OrderStatus
}

type OrderStatus int

const (
    OrderStatusPending OrderStatus = iota
    OrderStatusConfirmed
    OrderStatusShipped
    OrderStatusDelivered
    OrderStatusCancelled
)

func NewOrder(id OrderID, customerID CustomerID) *Order {
    return &Order{
        id:         id,
        customerID: customerID,
        lineItems:  make([]*OrderLineItem, 0),
        status:     OrderStatusPending,
    }
}

func CreateOrder(customerID CustomerID) *Order {
    return NewOrder(GenerateOrderID(), customerID)
}

// Business logic through the aggregate root
func (o *Order) AddLineItem(productID ProductID, quantity int, unitPrice Money) error {
    // Business rules and validation
    if o.status != OrderStatusPending {
        return errors.New("cannot add items to non-pending order")
    }

    lineItem, err := NewOrderLineItem(productID, quantity, unitPrice)
    if err != nil {
        return fmt.Errorf("failed to create line item: %w", err)
    }

    // Check for duplicate products and combine quantities
    for _, existingItem := range o.lineItems {
        if existingItem.productID.Equals(productID) {
            existingItem.quantity += quantity
            return nil
        }
    }

    o.lineItems = append(o.lineItems, lineItem)
    return nil
}

func (o *Order) RemoveLineItem(productID ProductID) error {
    if o.status != OrderStatusPending {
        return errors.New("cannot remove items from non-pending order")
    }

    for i, item := range o.lineItems {
        if item.productID.Equals(productID) {
            o.lineItems = append(o.lineItems[:i], o.lineItems[i+1:]...)
            return nil
        }
    }
    return errors.New("line item not found")
}

func (o *Order) Confirm() error {
    if o.status != OrderStatusPending {
        return errors.New("order can only be confirmed from pending status")
    }
    if len(o.lineItems) == 0 {
        return errors.New("cannot confirm empty order")
    }
    o.status = OrderStatusConfirmed
    return nil
}

// Return immutable view of line items
func (o *Order) LineItems() []*OrderLineItem {
    items := make([]*OrderLineItem, len(o.lineItems))
    copy(items, o.lineItems)
    return items
}

func (o *Order) ID() OrderID {
    return o.id
}

func (o *Order) CustomerID() CustomerID {
    return o.customerID
}

func (o *Order) Status() OrderStatus {
    return o.status
}

func (o *Order) Total() (Money, error) {
    if len(o.lineItems) == 0 {
        return NewMoney(0, "USD")
    }

    firstItem := o.lineItems[0]
    total, err := firstItem.Total()
    if err != nil {
        return Money{}, err
    }

    for i := 1; i < len(o.lineItems); i++ {
        itemTotal, err := o.lineItems[i].Total()
        if err != nil {
            return Money{}, err
        }
        total, err = total.Add(itemTotal)
        if err != nil {
            return Money{}, err
        }
    }

    return total, nil
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

```go
package domain

import (
    "context"
    "errors"
)

type PricingService struct {
    discountRepo DiscountRepository
}

func NewPricingService(discountRepo DiscountRepository) *PricingService {
    return &PricingService{
        discountRepo: discountRepo,
    }
}

func (ps *PricingService) CalculateOrderTotal(ctx context.Context, order *Order, customer *Customer) (Money, error) {
    baseTotal, err := order.Total()
    if err != nil {
        return Money{}, err
    }

    discount, err := ps.discountRepo.FindApplicableDiscount(ctx, customer.ID(), baseTotal)
    if err != nil {
        return Money{}, err
    }

    if discount == nil {
        return baseTotal, nil
    }

    return discount.Apply(baseTotal)
}

type MoneyTransferService struct{}

func NewMoneyTransferService() *MoneyTransferService {
    return &MoneyTransferService{}
}

func (mts *MoneyTransferService) Transfer(fromAccount *Account, toAccount *Account, amount Money) error {
    if !fromAccount.CanWithdraw(amount) {
        return errors.New("insufficient funds")
    }

    if err := fromAccount.Withdraw(amount); err != nil {
        return err
    }

    if err := toAccount.Deposit(amount); err != nil {
        // Rollback withdrawal
        fromAccount.Deposit(amount)
        return err
    }

    return nil
}
```

## Repository Pattern Rules

### 5. Repository Interface Rules

- Define repository interfaces in the domain layer using interfaces - they represent domain concepts
- Repositories should work with Aggregate Roots only
- Use domain-specific query methods, not generic CRUD
- Return domain objects, never DTOs or database models
- Input should be Aggregates not entities, value objects or DTOs
- Should return domain errors, not infrastructure errors
- Use context.Context for cancellation and timeouts

```go
// Domain Layer - domain/repositories/user_repository.go
package repositories

import "context"

type UserRepository interface {
    Save(ctx context.Context, user *User) error
    FindByID(ctx context.Context, userID UserID) (*User, error)
    FindByEmail(ctx context.Context, email Email) (*User, error)
    FindActiveUsersInDepartment(ctx context.Context, departmentID DepartmentID) ([]*User, error)
    Delete(ctx context.Context, userID UserID) error
}

type OrderRepository interface {
    Save(ctx context.Context, order *Order) error
    FindByID(ctx context.Context, orderID OrderID) (*Order, error)
    FindByCustomerID(ctx context.Context, customerID CustomerID) ([]*Order, error)
    FindPendingOrders(ctx context.Context) ([]*Order, error)
}
```

### 6. Repository Implementation Rules

- Implement repositories in the infrastructure layer
- Use proper Go error handling and context for cancellation
- Map between domain objects and persistence models
- Handle optimistic concurrency using version fields
- Repository should not contain business logic
- Use transactions appropriately

```go
// Infrastructure layer implementation will be shown in the Driven Adapter Rules section
```

## Domain Event Rules

### 7. Domain Event Rules

- Domain events should be immutable value objects
- Events should represent something that happened in the past (use past tense)
- Events should contain all necessary data to handle the event
- Use struct fields for events (immutable by design)
- Events should be raised by aggregates, not external code
- Include timestamp information

```go
package domain

import (
    "time"
)

type DomainEvent interface {
    OccurredAt() time.Time
    EventType() string
}

type UserEmailChanged struct {
    userID     UserID
    oldEmail   Email
    newEmail   Email
    occurredAt time.Time
}

func NewUserEmailChanged(userID UserID, oldEmail, newEmail Email) *UserEmailChanged {
    return &UserEmailChanged{
        userID:     userID,
        oldEmail:   oldEmail,
        newEmail:   newEmail,
        occurredAt: time.Now(),
    }
}

func (e *UserEmailChanged) UserID() UserID {
    return e.userID
}

func (e *UserEmailChanged) OldEmail() Email {
    return e.oldEmail
}

func (e *UserEmailChanged) NewEmail() Email {
    return e.newEmail
}

func (e *UserEmailChanged) OccurredAt() time.Time {
    return e.occurredAt
}

func (e *UserEmailChanged) EventType() string {
    return "UserEmailChanged"
}

type UserCreated struct {
    userID     UserID
    email      Email
    name       string
    occurredAt time.Time
}

func NewUserCreated(userID UserID, email Email, name string) *UserCreated {
    return &UserCreated{
        userID:     userID,
        email:      email,
        name:       name,
        occurredAt: time.Now(),
    }
}

func (e *UserCreated) UserID() UserID {
    return e.userID
}

func (e *UserCreated) Email() Email {
    return e.email
}

func (e *UserCreated) Name() string {
    return e.name
}

func (e *UserCreated) OccurredAt() time.Time {
    return e.occurredAt
}

func (e *UserCreated) EventType() string {
    return "UserCreated"
}
```

### 8. Event Handling Rules

- Domain event handlers should be in the application layer
- Handlers should be idempotent
- Use dependency injection for handler dependencies
- Handlers should not directly modify other aggregates
- Consider eventual consistency for cross-aggregate operations
- Use channels and goroutines for async event processing

```go
package application

import (
    "context"
    "log"
)

type EventHandler interface {
    Handle(ctx context.Context, event DomainEvent) error
    CanHandle(event DomainEvent) bool
}

type UserEmailChangedHandler struct {
    emailService EmailNotificationPort
}

func NewUserEmailChangedHandler(emailService EmailNotificationPort) *UserEmailChangedHandler {
    return &UserEmailChangedHandler{
        emailService: emailService,
    }
}

func (h *UserEmailChangedHandler) Handle(ctx context.Context, event DomainEvent) error {
    emailChangedEvent, ok := event.(*UserEmailChanged)
    if !ok {
        return errors.New("invalid event type")
    }

    return h.emailService.SendEmailChangeNotification(
        ctx,
        emailChangedEvent.OldEmail(),
        emailChangedEvent.NewEmail(),
    )
}

func (h *UserEmailChangedHandler) CanHandle(event DomainEvent) bool {
    _, ok := event.(*UserEmailChanged)
    return ok
}

type EventDispatcher struct {
    handlers []EventHandler
}

func NewEventDispatcher() *EventDispatcher {
    return &EventDispatcher{
        handlers: make([]EventHandler, 0),
    }
}

func (ed *EventDispatcher) RegisterHandler(handler EventHandler) {
    ed.handlers = append(ed.handlers, handler)
}

func (ed *EventDispatcher) Dispatch(ctx context.Context, event DomainEvent) {
    for _, handler := range ed.handlers {
        if handler.CanHandle(event) {
            go func(h EventHandler, e DomainEvent) {
                if err := h.Handle(ctx, e); err != nil {
                    log.Printf("Error handling event %s: %v", e.EventType(), err)
                }
            }(handler, event)
        }
    }
}
```

## Application Service Rules

### 9. Use Case Rules

- Use cases represent single business operations that the application can perform
- Each use case should handle exactly one business workflow
- Use cases orchestrate domain objects but contain no business logic
- Should be stateless and focused on a single responsibility
- Handle cross-cutting concerns (transactions, events, etc.)
- Should not return domain objects directly - use DTOs or response objects
- Name use cases after business operations using domain language
- Use context.Context for cancellation and request scoping

```go
package application

import (
    "context"
    "errors"
)

type CreateUserCommand struct {
    Email string
    Name  string
}

type CreateUserResponse struct {
    UserID string
}

type CreateUserUseCase struct {
    userRepo      UserRepository
    unitOfWork    UnitOfWork
    eventPublisher EventPublisherPort
}

func NewCreateUserUseCase(
    userRepo UserRepository,
    unitOfWork UnitOfWork,
    eventPublisher EventPublisherPort,
) *CreateUserUseCase {
    return &CreateUserUseCase{
        userRepo:       userRepo,
        unitOfWork:     unitOfWork,
        eventPublisher: eventPublisher,
    }
}

func (uc *CreateUserUseCase) Execute(ctx context.Context, cmd CreateUserCommand) (*CreateUserResponse, error) {
    return uc.unitOfWork.Execute(ctx, func(ctx context.Context) (*CreateUserResponse, error) {
        // Validation and orchestration logic only
        email, err := NewEmail(cmd.Email)
        if err != nil {
            return nil, err
        }

        // Check if user already exists
        existingUser, err := uc.userRepo.FindByEmail(ctx, email)
        if err != nil {
            return nil, err
        }
        if existingUser != nil {
            return nil, NewUserAlreadyExistsError(email)
        }

        user, err := CreateUser(email, cmd.Name)
        if err != nil {
            return nil, err
        }

        if err := uc.userRepo.Save(ctx, user); err != nil {
            return nil, err
        }

        event := NewUserCreated(user.ID(), user.Email(), user.Name())
        if err := uc.eventPublisher.Publish(ctx, event); err != nil {
            return nil, err
        }

        return &CreateUserResponse{UserID: user.ID().Value()}, nil
    })
}

type ChangeEmailCommand struct {
    UserID   UserID
    NewEmail Email
}

type ChangeUserEmailUseCase struct {
    userRepo   UserRepository
    unitOfWork UnitOfWork
}

func NewChangeUserEmailUseCase(
    userRepo UserRepository,
    unitOfWork UnitOfWork,
) *ChangeUserEmailUseCase {
    return &ChangeUserEmailUseCase{
        userRepo:   userRepo,
        unitOfWork: unitOfWork,
    }
}

func (uc *ChangeUserEmailUseCase) Execute(ctx context.Context, cmd ChangeEmailCommand) error {
    return uc.unitOfWork.Execute(ctx, func(ctx context.Context) error {
        user, err := uc.userRepo.FindByID(ctx, cmd.UserID)
        if err != nil {
            return err
        }
        if user == nil {
            return NewUserNotFoundError(cmd.UserID)
        }

        if err := user.ChangeEmail(cmd.NewEmail); err != nil {
            return err
        }

        return uc.userRepo.Save(ctx, user)
    })
}

// Unit of Work pattern for transaction management
type UnitOfWork interface {
    Execute(ctx context.Context, fn func(context.Context) error) error
    ExecuteWithResult[T any](ctx context.Context, fn func(context.Context) (T, error)) (T, error)
}
```

### 10. Event Integration Rules

- Domain events should be published through infrastructure ports
- Event handlers can be implemented as separate use cases
- Use event-driven architecture for cross-bounded context communication
- Events enable loose coupling between adapters and domain logic
- Consider eventual consistency for distributed operations
- Use Go channels and goroutines for async processing

```go
package application

import "context"

// Event Publishing through Infrastructure Port
type EventPublisherPort interface {
    Publish(ctx context.Context, event DomainEvent) error
    PublishBatch(ctx context.Context, events []DomainEvent) error
}

type CreateUserUseCase struct {
    userRepo       UserRepository
    eventPublisher EventPublisherPort
}

func NewCreateUserUseCase(
    userRepo UserRepository,
    eventPublisher EventPublisherPort,
) *CreateUserUseCase {
    return &CreateUserUseCase{
        userRepo:       userRepo,
        eventPublisher: eventPublisher,
    }
}

func (uc *CreateUserUseCase) Execute(ctx context.Context, cmd CreateUserCommand) (*CreateUserResponse, error) {
    email, err := NewEmail(cmd.Email)
    if err != nil {
        return nil, err
    }

    user, err := CreateUser(email, cmd.Name)
    if err != nil {
        return nil, err
    }

    if err := uc.userRepo.Save(ctx, user); err != nil {
        return nil, err
    }

    // Publish event through infrastructure port
    event := NewUserCreated(user.ID(), user.Email(), user.Name())
    if err := uc.eventPublisher.Publish(ctx, event); err != nil {
        return nil, err
    }

    return &CreateUserResponse{UserID: user.ID().Value()}, nil
}

// Event Handler as Use Case
type SendWelcomeEmailUseCase struct {
    emailService EmailNotificationPort
}

func NewSendWelcomeEmailUseCase(emailService EmailNotificationPort) *SendWelcomeEmailUseCase {
    return &SendWelcomeEmailUseCase{
        emailService: emailService,
    }
}

func (uc *SendWelcomeEmailUseCase) Handle(ctx context.Context, event *UserCreated) error {
    return uc.emailService.SendWelcomeEmail(ctx, event.Email(), event.Name())
}
```

## Validation and Error Handling Rules

### 11. Validation and Error Handling Rules

- Domain validation should happen in domain objects (entities, value objects)
- Use custom error types that implement the error interface
- Validation should be explicit and fail fast
- Input validation in application services should be minimal
- Use factory methods for complex validation scenarios
- Follow Go error handling conventions with explicit error returns

```go
package domain

import (
    "errors"
    "fmt"
)

// Base domain error
type DomainError struct {
    message string
    code    string
}

func NewDomainError(code, message string) *DomainError {
    return &DomainError{
        code:    code,
        message: message,
    }
}

func (e *DomainError) Error() string {
    return e.message
}

func (e *DomainError) Code() string {
    return e.code
}

// Specific domain errors
type InvalidEmailError struct {
    *DomainError
    email string
}

func NewInvalidEmailError(email string) *InvalidEmailError {
    return &InvalidEmailError{
        DomainError: NewDomainError("INVALID_EMAIL", fmt.Sprintf("Invalid email: %s", email)),
        email:       email,
    }
}

func (e *InvalidEmailError) Email() string {
    return e.email
}

type UserNotFoundError struct {
    *DomainError
    userID UserID
}

func NewUserNotFoundError(userID UserID) *UserNotFoundError {
    return &UserNotFoundError{
        DomainError: NewDomainError("USER_NOT_FOUND", fmt.Sprintf("User not found: %s", userID.Value())),
        userID:      userID,
    }
}

func (e *UserNotFoundError) UserID() UserID {
    return e.userID
}

type UserAlreadyExistsError struct {
    *DomainError
    email Email
}

func NewUserAlreadyExistsError(email Email) *UserAlreadyExistsError {
    return &UserAlreadyExistsError{
        DomainError: NewDomainError("USER_ALREADY_EXISTS", fmt.Sprintf("User already exists: %s", email.Value())),
        email:       email,
    }
}

func (e *UserAlreadyExistsError) Email() Email {
    return e.email
}

// Email value object with validation
type Email struct {
    value string
}

func NewEmail(value string) (Email, error) {
    if err := validateEmail(value); err != nil {
        return Email{}, NewInvalidEmailError(value)
    }
    return Email{value: strings.ToLower(strings.TrimSpace(value))}, nil
}

func (e Email) Validate() error {
    return validateEmail(e.value)
}

func validateEmail(value string) error {
    if value == "" {
        return errors.New("email cannot be empty")
    }
    if !strings.Contains(value, "@") {
        return errors.New("email must contain @ symbol")
    }
    parts := strings.Split(value, "@")
    if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
        return errors.New("email must have valid format")
    }
    return nil
}

func (e Email) Value() string {
    return e.value
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
- Follow Go naming conventions (PascalCase for exported, camelCase for unexported)

```go
// Good port names
type UserManagementPort interface {} // Driving port
type EmailNotificationPort interface {} // Driven port
type PaymentProcessingPort interface {} // Driven port

// Good adapter names
type RestUserController struct {} // Driving adapter (REST)
type GraphQLUserController struct {} // Driving adapter (GraphQL)

type SQLUserRepository struct {} // Driven adapter (SQL)
// Implements UserRepository interface

type MongoUserRepository struct {} // Driven adapter (MongoDB)
// Implements UserRepository interface

type SMTPEmailAdapter struct {} // Driven adapter (SMTP)
// Implements EmailNotificationPort interface

type SendGridEmailAdapter struct {} // Driven adapter (SendGrid)
// Implements EmailNotificationPort interface
```

### 13. Dependency Rules

- Domain layer should have no external dependencies except standard library
- Application layer can depend on domain but should use dependency inversion for external concerns
- Infrastructure layer implements all external dependencies through adapters
- **Domain Port Dependencies**: Domain objects can depend on domain ports (repositories, domain services)
- **Infrastructure Port Dependencies**: Use cases depend on infrastructure ports for external concerns
- **Port Placement**: Domain ports in domain layer, infrastructure ports in application layer
- **Inversion of Control**: Use DI container or constructor injection to wire adapters to ports at startup
- Use dependency inversion - depend on abstractions, not concretions
- Inject dependencies through constructors
- Use factory pattern for complex object creation

```go
// Domain layer - can depend on domain ports
type User struct {
    id    UserID
    email Email
    name  string
}

func NewUser(id UserID, email Email, name string) (*User, error) {
    if err := email.Validate(); err != nil {
        return nil, err
    }
    if name == "" {
        return nil, errors.New("name cannot be empty")
    }
    return &User{id: id, email: email, name: name}, nil
}

func (u *User) ChangeEmail(newEmail Email) error {
    if err := newEmail.Validate(); err != nil {
        return err
    }
    u.email = newEmail
    return nil
}

type UserDomainService struct {
    userRepo UserRepository // Domain port dependency
}

func NewUserDomainService(userRepo UserRepository) *UserDomainService {
    return &UserDomainService{
        userRepo: userRepo,
    }
}

func (uds *UserDomainService) IsEmailUnique(ctx context.Context, email Email) (bool, error) {
    existingUser, err := uds.userRepo.FindByEmail(ctx, email)
    if err != nil {
        return false, err
    }
    return existingUser == nil, nil
}

// Application layer - depends on domain + infrastructure ports
type CreateUserUseCase struct {
    userRepo           UserRepository         // Domain port
    userDomainService  *UserDomainService     // Domain service
    emailService       EmailNotificationPort  // Infrastructure port
    eventPublisher     EventPublisherPort     // Infrastructure port
}

func NewCreateUserUseCase(
    userRepo UserRepository,
    userDomainService *UserDomainService,
    emailService EmailNotificationPort,
    eventPublisher EventPublisherPort,
) *CreateUserUseCase {
    return &CreateUserUseCase{
        userRepo:          userRepo,
        userDomainService: userDomainService,
        emailService:      emailService,
        eventPublisher:    eventPublisher,
    }
}

// Infrastructure layer - implements ports with external dependencies
type SQLUserRepository struct {
    db *sql.DB // External dependency
}

func NewSQLUserRepository(db *sql.DB) *SQLUserRepository {
    return &SQLUserRepository{db: db}
}

func (r *SQLUserRepository) Save(ctx context.Context, user *User) error {
    // Implementation with database operations
    return nil
}

type SMTPEmailAdapter struct {
    client *smtp.Client // External dependency
}

func NewSMTPEmailAdapter(client *smtp.Client) *SMTPEmailAdapter {
    return &SMTPEmailAdapter{client: client}
}

func (a *SMTPEmailAdapter) SendWelcomeEmail(ctx context.Context, email Email, name string) error {
    // Implementation with SMTP client
    return nil
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
- Use Go's testing package and testify for assertions

```go
package application_test

import (
    "context"
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

// Mock implementations for testing
type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) Save(ctx context.Context, user *User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockUserRepository) FindByID(ctx context.Context, userID UserID) (*User, error) {
    args := m.Called(ctx, userID)
    return args.Get(0).(*User), args.Error(1)
}

func (m *MockUserRepository) FindByEmail(ctx context.Context, email Email) (*User, error) {
    args := m.Called(ctx, email)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*User), args.Error(1)
}

// Contract test for all UserRepository implementations
func TestUserRepositoryContract(t *testing.T) {
    testCases := []struct {
        name string
        repo UserRepository
    }{
        {"SQLUserRepository", NewSQLUserRepository(mockDB)},
        {"MongoUserRepository", NewMongoUserRepository(mockClient)},
    }

    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            ctx := context.Background()
            email, _ := NewEmail("test@example.com")
            user, _ := CreateUser(email, "John")

            err := tc.repo.Save(ctx, user)
            assert.NoError(t, err)

            found, err := tc.repo.FindByEmail(ctx, email)
            assert.NoError(t, err)
            assert.NotNil(t, found)
            assert.True(t, found.Email().Equals(user.Email()))
        })
    }
}

// Use Case Unit Test
func TestCreateUserUseCase_Execute_Success(t *testing.T) {
    // Arrange
    mockRepo := new(MockUserRepository)
    mockEventPublisher := new(MockEventPublisher)
    mockUnitOfWork := new(MockUnitOfWork)

    useCase := NewCreateUserUseCase(mockRepo, mockUnitOfWork, mockEventPublisher)

    ctx := context.Background()
    cmd := CreateUserCommand{
        Email: "test@example.com",
        Name:  "John",
    }

    email, _ := NewEmail(cmd.Email)
    mockRepo.On("FindByEmail", ctx, email).Return(nil, nil)
    mockRepo.On("Save", ctx, mock.AnythingOfType("*User")).Return(nil)
    mockEventPublisher.On("Publish", ctx, mock.AnythingOfType("*UserCreated")).Return(nil)
    mockUnitOfWork.On("Execute", ctx, mock.AnythingOfType("func(context.Context) (*CreateUserResponse, error)")).Return(&CreateUserResponse{UserID: "some-id"}, nil)

    // Act
    result, err := useCase.Execute(ctx, cmd)

    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, result)
    assert.NotEmpty(t, result.UserID)
    mockRepo.AssertExpectations(t)
    mockEventPublisher.AssertExpectations(t)
}

// In-memory adapter for integration testing
type InMemoryUserRepository struct {
    users map[string]*User
}

func NewInMemoryUserRepository() *InMemoryUserRepository {
    return &InMemoryUserRepository{
        users: make(map[string]*User),
    }
}

func (r *InMemoryUserRepository) Save(ctx context.Context, user *User) error {
    r.users[user.ID().Value()] = user
    return nil
}

func (r *InMemoryUserRepository) FindByEmail(ctx context.Context, email Email) (*User, error) {
    for _, user := range r.users {
        if user.Email().Equals(email) {
            return user, nil
        }
    }
    return nil, nil
}

func (r *InMemoryUserRepository) FindByID(ctx context.Context, userID UserID) (*User, error) {
    user, exists := r.users[userID.Value()]
    if !exists {
        return nil, nil
    }
    return user, nil
}

// Integration Test
func TestCreateUserUseCase_Integration(t *testing.T) {
    // Arrange
    userRepo := NewInMemoryUserRepository()
    emailService := NewInMemoryEmailService()
    eventPublisher := NewInMemoryEventPublisher()
    unitOfWork := NewInMemoryUnitOfWork()

    useCase := NewCreateUserUseCase(userRepo, unitOfWork, eventPublisher)

    ctx := context.Background()
    cmd := CreateUserCommand{
        Email: "test@example.com",
        Name:  "John",
    }

    // Act
    result, err := useCase.Execute(ctx, cmd)

    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, result)

    email, _ := NewEmail("test@example.com")
    savedUser, err := userRepo.FindByEmail(ctx, email)
    assert.NoError(t, err)
    assert.NotNil(t, savedUser)
    assert.Equal(t, "John", savedUser.Name())
    assert.Equal(t, 1, len(eventPublisher.PublishedEvents()))
}

// Technology-specific adapter testing
func TestSQLUserRepository_Save(t *testing.T) {
    // Arrange
    db := setupTestDatabase(t)
    defer cleanupTestDatabase(t, db)

    repository := NewSQLUserRepository(db)
    email, _ := NewEmail("test@example.com")
    user, _ := CreateUser(email, "John")

    ctx := context.Background()

    // Act
    err := repository.Save(ctx, user)

    // Assert
    assert.NoError(t, err)

    savedUser, err := repository.FindByEmail(ctx, email)
    assert.NoError(t, err)
    assert.NotNil(t, savedUser)
    assert.True(t, savedUser.Email().Equals(user.Email()))

    // Verify SQL model was created correctly
    var count int
    err = db.QueryRowContext(ctx, "SELECT COUNT(*) FROM users WHERE email = ?", "test@example.com").Scan(&count)
    assert.NoError(t, err)
    assert.Equal(t, 1, count)
}
```

## Ports & Adapters (Hexagonal Architecture) Rules

### 1. Port Definition Rules

- Ports define interfaces between layers and external systems
- **Driving ports** (primary/left-side) define application use cases - belong in application layer
- **Domain-driven driven ports** (repositories, domain services) - belong in domain layer
- **Infrastructure driven ports** (email, messaging, external APIs) - belong in application layer
- Port interfaces should use domain language, not technical terms
- Ports should be focused and follow Single Responsibility Principle
- Use context.Context parameter for cancellation and request scoping

```go
// Driving Ports (Application Layer) - application/ports/driving/
type CreateUserPort interface {
    Execute(ctx context.Context, cmd CreateUserCommand) (*CreateUserResponse, error)
}

type ChangeUserEmailPort interface {
    Execute(ctx context.Context, cmd ChangeEmailCommand) error
}

type GetUserPort interface {
    Execute(ctx context.Context, query GetUserQuery) (*GetUserResponse, error)
}

// Domain-Driven Driven Ports (Domain Layer) - domain/repositories/
type UserRepository interface {
    Save(ctx context.Context, user *User) error
    FindByID(ctx context.Context, userID UserID) (*User, error)
    FindByEmail(ctx context.Context, email Email) (*User, error)
    FindActiveUsersInDepartment(ctx context.Context, departmentID DepartmentID) ([]*User, error)
    Delete(ctx context.Context, userID UserID) error
}

// Domain Services (Domain Layer) - domain/services/
type PricingServicePort interface {
    CalculateProductPrice(ctx context.Context, product *Product, customer *Customer) (Money, error)
}

// Infrastructure Driven Ports (Application Layer) - application/ports/driven/
type EmailNotificationPort interface {
    SendWelcomeEmail(ctx context.Context, userEmail Email, userName string) error
    SendEmailChangeNotification(ctx context.Context, oldEmail, newEmail Email) error
}

type EventPublisherPort interface {
    Publish(ctx context.Context, event DomainEvent) error
    PublishBatch(ctx context.Context, events []DomainEvent) error
}

type TimeProviderPort interface {
    Now() time.Time
    UTCNow() time.Time
}

type FileSystemPort interface {
    WriteFile(ctx context.Context, path string, data []byte) error
    ReadFile(ctx context.Context, path string) ([]byte, error)
    FileExists(ctx context.Context, path string) (bool, error)
    DeleteFile(ctx context.Context, path string) error
}

type RandomGeneratorPort interface {
    GenerateInt(min, max int) int
    GenerateUUID() string
    GenerateBytes(length int) []byte
}

type IDGeneratorPort interface {
    GenerateUserID() UserID
    GenerateOrderID() OrderID
    GenerateProductID() ProductID
}
```

### 2. Driving Adapter Rules

- Driving adapters are the entry points (web controllers, CLI, message consumers)
- Should translate external requests to domain commands/queries
- Must not contain business logic - only translation and validation
- Should handle framework-specific concerns (HTTP status codes, serialization)
- Should be thin and delegate to use cases through driving ports
- Use proper Go HTTP handling patterns

```go
package adapters

import (
    "net/http"
    "github.com/gin-gonic/gin"
    "github.com/go-playground/validator/v10"
)

type CreateUserRequest struct {
    Email string `json:"email" validate:"required,email"`
    Name  string `json:"name" validate:"required,min=1"`
}

type ChangeEmailRequest struct {
    Email string `json:"email" validate:"required,email"`
}

type CreateUserResponse struct {
    UserID string `json:"userId"`
}

type RestUserController struct {
    createUserUseCase  CreateUserPort
    changeEmailUseCase ChangeUserEmailPort
    validator          *validator.Validate
}

func NewRestUserController(
    createUserUseCase CreateUserPort,
    changeEmailUseCase ChangeUserEmailPort,
) *RestUserController {
    return &RestUserController{
        createUserUseCase:  createUserUseCase,
        changeEmailUseCase: changeEmailUseCase,
        validator:          validator.New(),
    }
}

func (c *RestUserController) CreateUser(ctx *gin.Context) {
    var req CreateUserRequest
    if err := ctx.ShouldBindJSON(&req); err != nil {
        ctx.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON format"})
        return
    }

    if err := c.validator.Struct(req); err != nil {
        ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    cmd := CreateUserCommand{
        Email: req.Email,
        Name:  req.Name,
    }

    response, err := c.createUserUseCase.Execute(ctx.Request.Context(), cmd)
    if err != nil {
        c.handleError(ctx, err)
        return
    }

    ctx.JSON(http.StatusCreated, CreateUserResponse{UserID: response.UserID})
}

func (c *RestUserController) ChangeUserEmail(ctx *gin.Context) {
    userIDStr := ctx.Param("userId")
    userID, err := NewUserID(userIDStr)
    if err != nil {
        ctx.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user ID"})
        return
    }

    var req ChangeEmailRequest
    if err := ctx.ShouldBindJSON(&req); err != nil {
        ctx.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON format"})
        return
    }

    if err := c.validator.Struct(req); err != nil {
        ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    email, err := NewEmail(req.Email)
    if err != nil {
        ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    cmd := ChangeEmailCommand{
        UserID:   userID,
        NewEmail: email,
    }

    if err := c.changeEmailUseCase.Execute(ctx.Request.Context(), cmd); err != nil {
        c.handleError(ctx, err)
        return
    }

    ctx.Status(http.StatusNoContent)
}

func (c *RestUserController) handleError(ctx *gin.Context, err error) {
    switch e := err.(type) {
    case *UserNotFoundError:
        ctx.JSON(http.StatusNotFound, gin.H{"error": e.Error()})
    case *InvalidEmailError:
        ctx.JSON(http.StatusBadRequest, gin.H{"error": e.Error()})
    case *UserAlreadyExistsError:
        ctx.JSON(http.StatusConflict, gin.H{"error": e.Error()})
    case *DomainError:
        ctx.JSON(http.StatusBadRequest, gin.H{"error": e.Error()})
    default:
        ctx.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
    }
}

// CLI Adapter
type CLIUserController struct {
    createUserUseCase CreateUserPort
}

func NewCLIUserController(createUserUseCase CreateUserPort) *CLIUserController {
    return &CLIUserController{
        createUserUseCase: createUserUseCase,
    }
}

func (c *CLIUserController) CreateUser(email, name string) error {
    ctx := context.Background()
    cmd := CreateUserCommand{
        Email: email,
        Name:  name,
    }

    response, err := c.createUserUseCase.Execute(ctx, cmd)
    if err != nil {
        return fmt.Errorf("failed to create user: %w", err)
    }

    fmt.Printf("User created successfully with ID: %s\n", response.UserID)
    return nil
}

// Message Consumer Adapter (using channels)
type MessageUserConsumer struct {
    createUserUseCase CreateUserPort
    messageChan       <-chan CreateUserMessage
}

type CreateUserMessage struct {
    Email string `json:"email"`
    Name  string `json:"name"`
}

func NewMessageUserConsumer(
    createUserUseCase CreateUserPort,
    messageChan <-chan CreateUserMessage,
) *MessageUserConsumer {
    return &MessageUserConsumer{
        createUserUseCase: createUserUseCase,
        messageChan:       messageChan,
    }
}

func (c *MessageUserConsumer) Start(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case msg := <-c.messageChan:
            if err := c.handleMessage(ctx, msg); err != nil {
                log.Printf("Error handling message: %v", err)
            }
        }
    }
}

func (c *MessageUserConsumer) handleMessage(ctx context.Context, msg CreateUserMessage) error {
    cmd := CreateUserCommand{
        Email: msg.Email,
        Name:  msg.Name,
    }
    _, err := c.createUserUseCase.Execute(ctx, cmd)
    return err
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

```go
package adapters

import (
    "context"
    "database/sql"
    "time"
    "encoding/json"
    "net/http"
    "os"
    "math/rand"
    "crypto/rand"
    "fmt"

    "gorm.io/gorm"
    "github.com/go-redis/redis/v8"
    _ "github.com/lib/pq"
)

// SQL Database Adapter - infrastructure/adapters/driven/sql/
type UserModel struct {
    ID      string    `gorm:"primaryKey"`
    Email   string    `gorm:"uniqueIndex"`
    Name    string
    Version int
    CreatedAt time.Time
    UpdatedAt time.Time
}

type GORMUserRepository struct {
    db *gorm.DB
}

func NewGORMUserRepository(db *gorm.DB) *GORMUserRepository {
    return &GORMUserRepository{db: db}
}

func (r *GORMUserRepository) Save(ctx context.Context, user *User) error {
    userModel := r.fromDomain(user)
    result := r.db.WithContext(ctx).Save(&userModel)
    return result.Error
}

func (r *GORMUserRepository) FindByEmail(ctx context.Context, email Email) (*User, error) {
    var userModel UserModel
    result := r.db.WithContext(ctx).Where("email = ?", email.Value()).First(&userModel)
    if result.Error != nil {
        if result.Error == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, result.Error
    }
    return r.toDomain(&userModel)
}

func (r *GORMUserRepository) FindByID(ctx context.Context, userID UserID) (*User, error) {
    var userModel UserModel
    result := r.db.WithContext(ctx).Where("id = ?", userID.Value()).First(&userModel)
    if result.Error != nil {
        if result.Error == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, result.Error
    }
    return r.toDomain(&userModel)
}

func (r *GORMUserRepository) FindActiveUsersInDepartment(ctx context.Context, departmentID DepartmentID) ([]*User, error) {
    // Implementation would include proper GORM query with joins
    return []*User{}, nil
}

func (r *GORMUserRepository) Delete(ctx context.Context, userID UserID) error {
    result := r.db.WithContext(ctx).Delete(&UserModel{}, "id = ?", userID.Value())
    return result.Error
}

func (r *GORMUserRepository) fromDomain(user *User) UserModel {
    return UserModel{
        ID:      user.ID().Value(),
        Email:   user.Email().Value(),
        Name:    user.Name(),
        Version: 1, // In real implementation, handle optimistic locking
    }
}

func (r *GORMUserRepository) toDomain(model *UserModel) (*User, error) {
    userID, err := NewUserID(model.ID)
    if err != nil {
        return nil, err
    }

    email, err := NewEmail(model.Email)
    if err != nil {
        return nil, err
    }

    return NewUser(userID, email, model.Name)
}

// HTTP External Service Adapter - infrastructure/adapters/driven/http/
type EmailAPIConfig struct {
    BaseURL string
    APIKey  string
    Timeout time.Duration
}

type HTTPEmailNotificationAdapter struct {
    client *http.Client
    config EmailAPIConfig
}

func NewHTTPEmailNotificationAdapter(config EmailAPIConfig) *HTTPEmailNotificationAdapter {
    return &HTTPEmailNotificationAdapter{
        client: &http.Client{Timeout: config.Timeout},
        config: config,
    }
}

type EmailPayload struct {
    To       string            `json:"to"`
    Template string            `json:"template"`
    Variables map[string]interface{} `json:"variables"`
}

func (a *HTTPEmailNotificationAdapter) SendWelcomeEmail(ctx context.Context, userEmail Email, userName string) error {
    payload := EmailPayload{
        To:       userEmail.Value(),
        Template: "welcome",
        Variables: map[string]interface{}{
            "name": userName,
        },
    }

    return a.sendEmail(ctx, payload)
}

func (a *HTTPEmailNotificationAdapter) SendEmailChangeNotification(ctx context.Context, oldEmail, newEmail Email) error {
    payload := EmailPayload{
        To:       newEmail.Value(),
        Template: "email-changed",
        Variables: map[string]interface{}{
            "oldEmail": oldEmail.Value(),
            "newEmail": newEmail.Value(),
        },
    }

    return a.sendEmail(ctx, payload)
}

func (a *HTTPEmailNotificationAdapter) sendEmail(ctx context.Context, payload EmailPayload) error {
    jsonData, err := json.Marshal(payload)
    if err != nil {
        return fmt.Errorf("failed to marshal email payload: %w", err)
    }

    req, err := http.NewRequestWithContext(ctx, "POST", a.config.BaseURL+"/send", bytes.NewBuffer(jsonData))
    if err != nil {
        return fmt.Errorf("failed to create request: %w", err)
    }

    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("Authorization", "Bearer "+a.config.APIKey)

    resp, err := a.client.Do(req)
    if err != nil {
        return fmt.Errorf("failed to send email: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("email service returned status %d", resp.StatusCode)
    }

    return nil
}

// Redis Event Publisher Adapter
type RedisEventPublisherAdapter struct {
    client *redis.Client
    stream string
}

func NewRedisEventPublisherAdapter(client *redis.Client, stream string) *RedisEventPublisherAdapter {
    return &RedisEventPublisherAdapter{
        client: client,
        stream: stream,
    }
}

func (a *RedisEventPublisherAdapter) Publish(ctx context.Context, event DomainEvent) error {
    eventData := map[string]interface{}{
        "eventType":   event.EventType(),
        "occurredAt":  event.OccurredAt().Format(time.RFC3339),
        "eventData":   event,
    }

    return a.client.XAdd(ctx, &redis.XAddArgs{
        Stream: a.stream,
        Values: eventData,
    }).Err()
}

func (a *RedisEventPublisherAdapter) PublishBatch(ctx context.Context, events []DomainEvent) error {
    pipe := a.client.Pipeline()

    for _, event := range events {
        eventData := map[string]interface{}{
            "eventType":  event.EventType(),
            "occurredAt": event.OccurredAt().Format(time.RFC3339),
            "eventData":  event,
        }

        pipe.XAdd(ctx, &redis.XAddArgs{
            Stream: a.stream,
            Values: eventData,
        })
    }

    _, err := pipe.Exec(ctx)
    return err
}

// File System Adapter
type OSFileSystemAdapter struct{}

func NewOSFileSystemAdapter() *OSFileSystemAdapter {
    return &OSFileSystemAdapter{}
}

func (a *OSFileSystemAdapter) WriteFile(ctx context.Context, path string, data []byte) error {
    return os.WriteFile(path, data, 0644)
}

func (a *OSFileSystemAdapter) ReadFile(ctx context.Context, path string) ([]byte, error) {
    return os.ReadFile(path)
}

func (a *OSFileSystemAdapter) FileExists(ctx context.Context, path string) (bool, error) {
    _, err := os.Stat(path)
    if err == nil {
        return true, nil
    }
    if os.IsNotExist(err) {
        return false, nil
    }
    return false, err
}

func (a *OSFileSystemAdapter) DeleteFile(ctx context.Context, path string) error {
    return os.Remove(path)
}

// Time Provider Adapter
type SystemTimeProviderAdapter struct{}

func NewSystemTimeProviderAdapter() *SystemTimeProviderAdapter {
    return &SystemTimeProviderAdapter{}
}

func (a *SystemTimeProviderAdapter) Now() time.Time {
    return time.Now()
}

func (a *SystemTimeProviderAdapter) UTCNow() time.Time {
    return time.Now().UTC()
}

// Random Generator Adapter
type SystemRandomGeneratorAdapter struct {
    rand *rand.Rand
}

func NewSystemRandomGeneratorAdapter() *SystemRandomGeneratorAdapter {
    return &SystemRandomGeneratorAdapter{
        rand: rand.New(rand.NewSource(time.Now().UnixNano())),
    }
}

func (a *SystemRandomGeneratorAdapter) GenerateInt(min, max int) int {
    return a.rand.Intn(max-min) + min
}

func (a *SystemRandomGeneratorAdapter) GenerateUUID() string {
    return uuid.New().String()
}

func (a *SystemRandomGeneratorAdapter) GenerateBytes(length int) []byte {
    bytes := make([]byte, length)
    rand.Read(bytes)
    return bytes
}

// ID Generator Adapter
type UUIDGeneratorAdapter struct{}

func NewUUIDGeneratorAdapter() *UUIDGeneratorAdapter {
    return &UUIDGeneratorAdapter{}
}

func (a *UUIDGeneratorAdapter) GenerateUserID() UserID {
    return UserID{value: uuid.New().String()}
}

func (a *UUIDGeneratorAdapter) GenerateOrderID() OrderID {
    return OrderID{value: uuid.New().String()}
}

func (a *UUIDGeneratorAdapter) GenerateProductID() ProductID {
    return ProductID{value: uuid.New().String()}
}

// Unit of Work with Database Transaction
type GORMUnitOfWork struct {
    db *gorm.DB
}

func NewGORMUnitOfWork(db *gorm.DB) *GORMUnitOfWork {
    return &GORMUnitOfWork{db: db}
}

func (uow *GORMUnitOfWork) Execute(ctx context.Context, fn func(context.Context) error) error {
    return uow.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
        return fn(ctx)
    })
}

func (uow *GORMUnitOfWork) ExecuteWithResult(ctx context.Context, fn func(context.Context) (*CreateUserResponse, error)) (*CreateUserResponse, error) {
    var result *CreateUserResponse
    var err error

    txErr := uow.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
        result, err = fn(ctx)
        return err
    })

    if txErr != nil {
        return nil, txErr
    }

    return result, err
}
```

These integrated rules ensure that Domain Driven Design and Ports & Adapters (Hexagonal Architecture) work together seamlessly in Go implementations. The combination provides clean separation of concerns, testability, and flexibility while maintaining domain focus and proper dependency management.

## Appendix

### Complete Project Structure Example

```
project/
├── cmd/
│   ├── api/
│   │   └── main.go                 # REST API entry point
│   ├── cli/
│   │   └── main.go                 # CLI entry point
│   └── worker/
│       └── main.go                 # Background worker entry point
│
├── internal/
│   ├── domain/                     # Domain Layer (DDD Core)
│   │   ├── entities/
│   │   │   ├── user.go
│   │   │   └── order.go
│   │   ├── valueobjects/
│   │   │   ├── email.go
│   │   │   ├── money.go
│   │   │   └── user_id.go
│   │   ├── aggregates/
│   │   │   └── order.go
│   │   ├── services/
│   │   │   ├── pricing_service.go
│   │   │   └── transfer_service.go
│   │   ├── repositories/
│   │   │   ├── user_repository.go
│   │   │   └── order_repository.go
│   │   ├── events/
│   │   │   ├── user_created.go
│   │   │   └── user_email_changed.go
│   │   └── errors/
│   │       ├── domain_error.go
│   │       ├── user_not_found_error.go
│   │       └── invalid_email_error.go
│   │
│   ├── application/                # Application Layer (Use Cases)
│   │   ├── usecases/
│   │   │   ├── create_user.go
│   │   │   ├── change_user_email.go
│   │   │   └── get_user.go
│   │   ├── ports/
│   │   │   ├── driving/
│   │   │   │   ├── create_user_port.go
│   │   │   │   └── change_user_email_port.go
│   │   │   └── driven/
│   │   │       ├── email_notification_port.go
│   │   │       ├── event_publisher_port.go
│   │   │       └── time_provider_port.go
│   │   ├── commands/
│   │   │   ├── create_user_command.go
│   │   │   └── change_email_command.go
│   │   ├── queries/
│   │   │   └── get_user_query.go
│   │   └── responses/
│   │       ├── create_user_response.go
│   │       └── get_user_response.go
│   │
│   └── infrastructure/             # Infrastructure Layer (Adapters)
│       └── adapters/
│           ├── driving/
│           │   ├── rest/
│           │   │   ├── user_controller.go
│           │   │   └── routes.go
│           │   ├── cli/
│           │   │   └── user_cli.go
│           │   └── messaging/
│           │       └── user_consumer.go
│           └── driven/
│               ├── sql/
│               │   ├── gorm_user_repository.go
│               │   ├── gorm_unit_of_work.go
│               │   └── models.go
│               ├── mongodb/
│               │   └── mongo_user_repository.go
│               ├── redis/
│               │   └── redis_event_publisher.go
│               ├── http/
│               │   └── http_email_service.go
│               ├── filesystem/
│               │   └── os_filesystem.go
│               ├── time/
│               │   └── system_time_provider.go
│               └── random/
│                   └── system_random_generator.go
│
├── config/
│   ├── config.go                   # Configuration management
│   └── dependencies.go             # Dependency injection setup
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   ├── integration/
│   └── e2e/
│
├── go.mod
├── go.sum
├── Dockerfile
└── README.md
```

### Dependency Injection Setup Example

```go
package config

import (
    "database/sql"
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type Dependencies struct {
    // Repositories (Domain Ports)
    UserRepository UserRepository

    // Infrastructure Ports
    EmailService   EmailNotificationPort
    EventPublisher EventPublisherPort
    TimeProvider   TimeProviderPort
    FileSystem     FileSystemPort
    RandomGen      RandomGeneratorPort
    IDGenerator    IDGeneratorPort

    // Use Cases (Driving Ports)
    CreateUserUseCase     CreateUserPort
    ChangeUserEmailUseCase ChangeUserEmailPort

    // Controllers (Driving Adapters)
    UserController *RestUserController

    // Infrastructure
    UnitOfWork UnitOfWork
}

func NewDependencies(db *gorm.DB, config *Config) *Dependencies {
    // Infrastructure adapters
    userRepo := NewGORMUserRepository(db)
    emailService := NewHTTPEmailNotificationAdapter(config.EmailAPI)
    eventPublisher := NewRedisEventPublisherAdapter(config.Redis)
    timeProvider := NewSystemTimeProviderAdapter()
    fileSystem := NewOSFileSystemAdapter()
    randomGen := NewSystemRandomGeneratorAdapter()
    idGenerator := NewUUIDGeneratorAdapter()
    unitOfWork := NewGORMUnitOfWork(db)

    // Use cases
    createUserUseCase := NewCreateUserUseCase(userRepo, unitOfWork, eventPublisher)
    changeEmailUseCase := NewChangeUserEmailUseCase(userRepo, unitOfWork)

    // Controllers
    userController := NewRestUserController(createUserUseCase, changeEmailUseCase)

    return &Dependencies{
        UserRepository:         userRepo,
        EmailService:          emailService,
        EventPublisher:        eventPublisher,
        TimeProvider:          timeProvider,
        FileSystem:            fileSystem,
        RandomGen:             randomGen,
        IDGenerator:           idGenerator,
        CreateUserUseCase:     createUserUseCase,
        ChangeUserEmailUseCase: changeEmailUseCase,
        UserController:        userController,
        UnitOfWork:           unitOfWork,
    }
}

func SetupRoutes(deps *Dependencies) *gin.Engine {
    r := gin.Default()

    v1 := r.Group("/api/v1")
    {
        users := v1.Group("/users")
        {
            users.POST("/", deps.UserController.CreateUser)
            users.PATCH("/:userId/email", deps.UserController.ChangeUserEmail)
        }
    }

    return r
}
```

### Go-Specific Best Practices Integration

- **Error Handling**: Use explicit error returns and proper error wrapping with `fmt.Errorf`
- **Context Usage**: Pass `context.Context` for cancellation and request scoping
- **Interfaces**: Keep interfaces small and focused (Go's implicit interface satisfaction)
- **Struct Embedding**: Use embedding for shared behavior when appropriate
- **Goroutines and Channels**: Use for async processing and event handling
- **Testing**: Leverage Go's built-in testing package with testify for assertions
- **Package Organization**: Follow Go's package naming conventions and structure
- **Zero Values**: Design structs to have useful zero values when possible
- **Constructor Functions**: Use `New*` functions for complex initialization
- **Method Receivers**: Use pointer receivers for entities, value receivers for value objects

This comprehensive ruleset provides a complete guide for implementing Domain Driven Design with Ports & Adapters architecture in Go, maintaining clean separation of concerns while leveraging Go's language features and idioms.
