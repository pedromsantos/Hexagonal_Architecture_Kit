# Domain Driven Design with Ports & Adapters Rules (Java)

## TL;DR: How DDD and Ports & Adapters Work Together

This document defines two complementary architectural approaches that work together to create maintainable, testable Java applications:

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

```java
// 1. Domain Layer (DDD Core)
public class User extends Entity<UserId> {
    // Rule 1: Entity with identity
    private Email email;
    private String name;

    public User(UserId id, Email email, String name) {
        super(id);
        this.email = email;
        this.name = name;
        validate();
    }

    public UserEmailChanged changeEmail(Email newEmail) {
        // Business logic here
        Email oldEmail = this.email;
        this.email = newEmail;
        return new UserEmailChanged(getId(), oldEmail, newEmail, Instant.now());
    }

    // Getters and validation methods...
}

public interface UserRepository {
    // Rule 5: Domain port for persistence
    CompletableFuture<Void> save(User user);
    CompletableFuture<Optional<User>> findById(UserId id);
}

// 2. Application Layer (Bridge between DDD and Ports & Adapters)
@Service
public class ChangeUserEmailUseCase implements ChangeUserEmailPort {
    // Rule 9 + P&A Rule 1
    private final UserRepository userRepository; // Domain port
    private final EmailNotificationPort emailService; // Infrastructure port
    private final TimeProviderPort timeProvider; // Infrastructure port

    public ChangeUserEmailUseCase(
        UserRepository userRepository,
        EmailNotificationPort emailService,
        TimeProviderPort timeProvider
    ) {
        this.userRepository = userRepository;
        this.emailService = emailService;
        this.timeProvider = timeProvider;
    }

    @Override
    public CompletableFuture<Void> execute(ChangeEmailCommand command) {
        // Orchestrate domain objects (Rule 9)
        return userRepository.findById(command.getUserId())
            .thenCompose(userOpt -> {
                User user = userOpt.orElseThrow(() ->
                    new UserNotFoundException(command.getUserId()));

                UserEmailChanged event = user.changeEmail(new Email(command.getNewEmail()));

                // Use infrastructure ports for side effects
                return userRepository.save(user)
                    .thenCompose(v -> emailService.sendEmailChangeNotification(
                        event.getOldEmail(),
                        event.getNewEmail(),
                        timeProvider.now()
                    ));
            });
    }
}

// 3. Infrastructure Layer (Ports & Adapters Implementation)
@Repository
public class JpaUserRepository implements UserRepository {
    // P&A Rule 3: Driven adapter
    private final UserJpaRepository jpaRepository;

    @Override
    public CompletableFuture<Void> save(User user) {
        // Handle JPA mapping, database specifics
        UserEntity entity = toEntity(user);
        return CompletableFuture.runAsync(() -> jpaRepository.save(entity));
    }

    // Mapping methods...
}

@RestController
@RequestMapping("/api/users")
public class UserRestController {
    // P&A Rule 2: Driving adapter
    private final ChangeUserEmailUseCase useCase;

    @PatchMapping("/{userId}/email")
    public CompletableFuture<ResponseEntity<Void>> patchUserEmail(
        @PathVariable String userId,
        @RequestBody @Valid ChangeEmailRequest request
    ) {
        ChangeEmailCommand command = new ChangeEmailCommand(new UserId(userId), request.getEmail());
        return useCase.execute(command)
            .thenApply(v -> ResponseEntity.noContent().build()); // Delegate to use case
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
- Implement `equals()` and `hashCode()` based solely on identity, not attributes/fields
- Entities MUST contain business logic as methods, not just data
  - Avoid anemic domain models - entities should have behavior
- Include validation in constructor or factory methods

```java
public class User extends Entity<UserId> {
    private Email email;
    private String name;

    protected User() {
        // Required by JPA/Hibernate
    }

    public User(UserId id, Email email, String name) {
        super(id);
        this.email = Objects.requireNonNull(email, "Email cannot be null");
        this.name = Objects.requireNonNull(name, "Name cannot be null");
        validate();
    }

    public static User create(Email email, String name) {
        return new User(UserId.generate(), email, name);
    }

    public void changeEmail(Email newEmail) {
        // Business logic here
        Objects.requireNonNull(newEmail, "Email cannot be null");
        this.email = newEmail;
    }

    public Email getEmail() {
        return email;
    }

    public String getName() {
        return name;
    }

    private void validate() {
        if (email == null || name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("User must have valid email and name");
        }
    }

    // equals() and hashCode() are inherited from Entity<T>
}

public abstract class Entity<T> {
    protected T id;

    protected Entity() {
        // For frameworks that require no-arg constructor
    }

    protected Entity(T id) {
        this.id = Objects.requireNonNull(id, "ID cannot be null");
    }

    public T getId() {
        return id;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;

        Entity<?> entity = (Entity<?>) obj;
        return Objects.equals(id, entity.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
```

### 2. Value Object Rules

- Value objects MUST be immutable
- Equality is based on ALL attributes, not identity
- Should be small, focused, and represent a concept from the domain
- Include validation in constructor
- Should have meaningful methods that operate on the value
- Use `record` classes when appropriate (Java 14+)

```java
// Using records (Java 14+)
public record Email(String value) {
    public Email {
        if (value == null || !value.contains("@")) {
            throw new IllegalArgumentException("Invalid email format: " + value);
        }
    }

    public String getDomain() {
        return value.split("@")[1];
    }

    public boolean isFromDomain(String domain) {
        return getDomain().equals(domain);
    }
}

// Traditional class approach
public final class Money {
    private final BigDecimal amount;
    private final Currency currency;

    public Money(BigDecimal amount, Currency currency) {
        this.amount = Objects.requireNonNull(amount, "Amount cannot be null");
        this.currency = Objects.requireNonNull(currency, "Currency cannot be null");

        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount cannot be negative");
        }
    }

    public Money add(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot add money with different currencies");
        }
        return new Money(amount.add(other.amount), currency);
    }

    public Money multiply(BigDecimal multiplier) {
        return new Money(amount.multiply(multiplier), currency);
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public Currency getCurrency() {
        return currency;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;

        Money money = (Money) obj;
        return Objects.equals(amount, money.amount) &&
               Objects.equals(currency, money.currency);
    }

    @Override
    public int hashCode() {
        return Objects.hash(amount, currency);
    }

    @Override
    public String toString() {
        return amount + " " + currency.getCurrencyCode();
    }
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
- Encapsulate Collections: Use Collections.unmodifiableList() or similar patterns

```java
public class Order extends Entity<OrderId> {
    // Aggregate Root
    private final CustomerId customerId;
    private final List<OrderLineItem> lineItems = new ArrayList<>();
    private OrderStatus status = OrderStatus.PENDING;

    protected Order() {
        // For JPA/Hibernate
    }

    public Order(OrderId id, CustomerId customerId) {
        super(id);
        this.customerId = Objects.requireNonNull(customerId, "Customer ID cannot be null");
    }

    public static Order create(CustomerId customerId) {
        return new Order(OrderId.generate(), customerId);
    }

    public void addLineItem(ProductId productId, int quantity, Money unitPrice) {
        // Business rules and validation
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("Cannot add items to non-pending order");
        }

        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }

        // Check if item already exists and update quantity instead
        Optional<OrderLineItem> existingItem = lineItems.stream()
            .filter(item -> item.getProductId().equals(productId))
            .findFirst();

        if (existingItem.isPresent()) {
            existingItem.get().increaseQuantity(quantity);
        } else {
            OrderLineItem lineItem = new OrderLineItem(productId, quantity, unitPrice);
            lineItems.add(lineItem);
        }
    }

    public void removeLineItem(ProductId productId) {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("Cannot remove items from non-pending order");
        }

        lineItems.removeIf(item -> item.getProductId().equals(productId));
    }

    public void confirm() {
        if (lineItems.isEmpty()) {
            throw new IllegalStateException("Cannot confirm order with no items");
        }
        status = OrderStatus.CONFIRMED;
    }

    public Money getTotalAmount() {
        return lineItems.stream()
            .map(OrderLineItem::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }

    public List<OrderLineItem> getLineItems() {
        return Collections.unmodifiableList(lineItems); // Return immutable view
    }

    public CustomerId getCustomerId() {
        return customerId;
    }

    public OrderStatus getStatus() {
        return status;
    }
}

// Internal entity within the aggregate
class OrderLineItem {
    private final ProductId productId;
    private int quantity;
    private final Money unitPrice;

    OrderLineItem(ProductId productId, int quantity, Money unitPrice) {
        this.productId = Objects.requireNonNull(productId);
        this.quantity = quantity;
        this.unitPrice = Objects.requireNonNull(unitPrice);
    }

    void increaseQuantity(int additionalQuantity) {
        this.quantity += additionalQuantity;
    }

    Money getSubtotal() {
        return unitPrice.multiply(BigDecimal.valueOf(quantity));
    }

    ProductId getProductId() {
        return productId;
    }

    int getQuantity() {
        return quantity;
    }

    Money getUnitPrice() {
        return unitPrice;
    }
}

enum OrderStatus {
    PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
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

```java
@Component
public class PricingService {
    private final DiscountRepository discountRepository;

    public PricingService(DiscountRepository discountRepository) {
        this.discountRepository = discountRepository;
    }

    public Money calculateOrderTotal(Order order, Customer customer) {
        // Complex pricing logic that spans multiple aggregates
        Money baseTotal = order.getTotalAmount();

        // Apply customer-specific discounts
        List<Discount> applicableDiscounts = discountRepository
            .findApplicableDiscounts(customer.getId(), order.getLineItems());

        Money totalDiscount = applicableDiscounts.stream()
            .map(discount -> discount.calculateDiscount(baseTotal))
            .reduce(Money.ZERO, Money::add);

        return baseTotal.subtract(totalDiscount);
    }

    public boolean isEligibleForPremiumPricing(Customer customer) {
        // Domain logic for premium pricing eligibility
        return customer.getTotalOrdersAmount().getAmount()
            .compareTo(new BigDecimal("10000")) >= 0;
    }
}
```

## Repository Pattern Rules

### 5. Repository Interface Rules

- Define repository interfaces in the domain layer using interfaces - they represent domain concepts
- Repositories should work with Aggregate Roots only
- Use domain-specific query methods, not generic CRUD
- Return domain objects, never DTOs or database models
- Input should be Aggregates not entities, value objects or DTOs
- Should throw domain exceptions, not infrastructure exceptions
- Use `Optional<T>` for single results that might not exist
- Use `CompletableFuture<T>` for async operations when needed

```java
// Domain Layer - domain/repositories/UserRepository.java
public interface UserRepository {
    CompletableFuture<Optional<User>> findByEmail(Email email);
    CompletableFuture<Void> save(User user);
    CompletableFuture<List<User>> findActiveUsersInDepartment(DepartmentId departmentId);
    CompletableFuture<Optional<User>> findById(UserId userId);
    CompletableFuture<Boolean> existsByEmail(Email email);
    CompletableFuture<Void> delete(User user);
}

// For synchronous operations
public interface OrderRepository {
    Optional<Order> findById(OrderId orderId);
    void save(Order order);
    List<Order> findByCustomerId(CustomerId customerId);
    List<Order> findPendingOrders();
    void delete(Order order);
}
```

### 6. Repository Implementation Rules

- Implement repositories in the infrastructure layer
- Use the Unit of Work pattern for transaction management
- Map between domain objects and persistence models
- Handle optimistic concurrency using version fields
- Repository should not contain business logic
- Use proper exception translation from infrastructure to domain exceptions

```java
@Repository
@Transactional
public class JpaUserRepository implements UserRepository {
    private final UserJpaRepository jpaRepository;
    private final UserMapper userMapper;

    public JpaUserRepository(UserJpaRepository jpaRepository, UserMapper userMapper) {
        this.jpaRepository = jpaRepository;
        this.userMapper = userMapper;
    }

    @Override
    public CompletableFuture<Optional<User>> findByEmail(Email email) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return jpaRepository.findByEmail(email.value())
                    .map(userMapper::toDomain);
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to find user by email", e);
            }
        });
    }

    @Override
    @Transactional
    public CompletableFuture<Void> save(User user) {
        return CompletableFuture.runAsync(() -> {
            try {
                UserEntity entity = userMapper.toEntity(user);
                jpaRepository.save(entity);
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to save user", e);
            }
        });
    }

    @Override
    public CompletableFuture<List<User>> findActiveUsersInDepartment(DepartmentId departmentId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return jpaRepository.findActiveUsersInDepartment(departmentId.value())
                    .stream()
                    .map(userMapper::toDomain)
                    .collect(Collectors.toList());
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to find active users", e);
            }
        });
    }
}
```

## Domain Event Rules

### 7. Domain Event Rules

- Domain events should be immutable value objects
- Events should represent something that happened in the past (use past tense)
- Events should contain all necessary data to handle the event
- Use `final` fields for immutability
- Events should be raised by aggregates, not external code
- Consider using records for simple events (Java 14+)

```java
// Using records (Java 14+)
public record UserEmailChanged(
    UserId userId,
    Email oldEmail,
    Email newEmail,
    Instant occurredAt
) implements DomainEvent {
    public UserEmailChanged {
        Objects.requireNonNull(userId, "User ID cannot be null");
        Objects.requireNonNull(oldEmail, "Old email cannot be null");
        Objects.requireNonNull(newEmail, "New email cannot be null");
        Objects.requireNonNull(occurredAt, "Occurred at cannot be null");
    }
}

// Traditional class approach
public final class OrderConfirmed implements DomainEvent {
    private final OrderId orderId;
    private final CustomerId customerId;
    private final Money totalAmount;
    private final Instant occurredAt;

    public OrderConfirmed(OrderId orderId, CustomerId customerId, Money totalAmount, Instant occurredAt) {
        this.orderId = Objects.requireNonNull(orderId);
        this.customerId = Objects.requireNonNull(customerId);
        this.totalAmount = Objects.requireNonNull(totalAmount);
        this.occurredAt = Objects.requireNonNull(occurredAt);
    }

    public OrderId getOrderId() { return orderId; }
    public CustomerId getCustomerId() { return customerId; }
    public Money getTotalAmount() { return totalAmount; }
    public Instant getOccurredAt() { return occurredAt; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;

        OrderConfirmed that = (OrderConfirmed) obj;
        return Objects.equals(orderId, that.orderId) &&
               Objects.equals(customerId, that.customerId) &&
               Objects.equals(totalAmount, that.totalAmount) &&
               Objects.equals(occurredAt, that.occurredAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(orderId, customerId, totalAmount, occurredAt);
    }
}

public interface DomainEvent {
    Instant getOccurredAt();
}
```

### 8. Event Handling Rules

- Domain event handlers should be in the application layer
- Handlers should be idempotent
- Use dependency injection for handler dependencies
- Handlers should not directly modify other aggregates
- Consider eventual consistency for cross-aggregate operations
- Use Spring's `@EventListener` or similar mechanisms

```java
@Component
public class UserEventHandler {
    private final EmailNotificationPort emailService;
    private final AuditLogPort auditLogService;

    public UserEventHandler(EmailNotificationPort emailService, AuditLogPort auditLogService) {
        this.emailService = emailService;
        this.auditLogService = auditLogService;
    }

    @EventListener
    @Async
    public void handle(UserEmailChanged event) {
        // Handler should be idempotent
        CompletableFuture.allOf(
            emailService.sendEmailChangeNotification(event.oldEmail(), event.newEmail()),
            auditLogService.logEmailChange(event.userId(), event.oldEmail(), event.newEmail(), event.occurredAt())
        ).exceptionally(throwable -> {
            // Log error but don't throw - maintain eventual consistency
            log.error("Failed to handle UserEmailChanged event", throwable);
            return null;
        });
    }

    @EventListener
    public void handle(UserCreated event) {
        // Send welcome email
        emailService.sendWelcomeEmail(event.email(), event.name())
            .exceptionally(throwable -> {
                log.error("Failed to send welcome email", throwable);
                return null;
            });
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
- Should not return domain objects directly - use DTOs
- Name use cases after business operations using domain language
- Use `@Service` or `@Component` annotations for Spring DI

```java
@Service
@Transactional
public class CreateUserUseCase implements CreateUserPort {
    private final UserRepository userRepository;
    private final ApplicationEventPublisher eventPublisher;
    private final TimeProviderPort timeProvider;

    public CreateUserUseCase(
        UserRepository userRepository,
        ApplicationEventPublisher eventPublisher,
        TimeProviderPort timeProvider
    ) {
        this.userRepository = userRepository;
        this.eventPublisher = eventPublisher;
        this.timeProvider = timeProvider;
    }

    @Override
    public CompletableFuture<CreateUserResponse> execute(CreateUserCommand command) {
        return CompletableFuture.supplyAsync(() -> {
            // Orchestration logic only
            Email email = new Email(command.getEmail());

            // Check if user already exists
            boolean userExists = userRepository.existsByEmail(email)
                .join(); // Since we're already in async context

            if (userExists) {
                throw new UserAlreadyExistsException(email);
            }

            User user = User.create(email, command.getName());
            userRepository.save(user).join();

            // Publish domain event
            UserCreated event = new UserCreated(
                user.getId(),
                user.getEmail(),
                user.getName(),
                timeProvider.now()
            );
            eventPublisher.publishEvent(event);

            return new CreateUserResponse(user.getId().value());
        });
    }
}

@Service
@Transactional
public class ChangeUserEmailUseCase implements ChangeUserEmailPort {
    private final UserRepository userRepository;
    private final ApplicationEventPublisher eventPublisher;
    private final TimeProviderPort timeProvider;

    public ChangeUserEmailUseCase(
        UserRepository userRepository,
        ApplicationEventPublisher eventPublisher,
        TimeProviderPort timeProvider
    ) {
        this.userRepository = userRepository;
        this.eventPublisher = eventPublisher;
        this.timeProvider = timeProvider;
    }

    @Override
    public CompletableFuture<Void> execute(ChangeEmailCommand command) {
        return userRepository.findById(command.getUserId())
            .thenCompose(userOpt -> {
                User user = userOpt.orElseThrow(() ->
                    new UserNotFoundException(command.getUserId()));

                Email oldEmail = user.getEmail();
                Email newEmail = new Email(command.getNewEmail());

                user.changeEmail(newEmail);

                return userRepository.save(user)
                    .thenRun(() -> {
                        UserEmailChanged event = new UserEmailChanged(
                            user.getId(),
                            oldEmail,
                            newEmail,
                            timeProvider.now()
                        );
                        eventPublisher.publishEvent(event);
                    });
            });
    }
}
```

### 10. Event Integration Rules

- Domain events should be published through infrastructure ports
- Event handlers can be implemented as separate use cases
- Use event-driven architecture for cross-bounded context communication
- Events enable loose coupling between adapters and domain logic
- Consider eventual consistency for distributed operations

```java
// Event Publishing through Infrastructure Port
public interface EventPublisherPort {  // Application layer
    CompletableFuture<Void> publish(DomainEvent event);
    CompletableFuture<Void> publishAll(List<DomainEvent> events);
}

@Service
public class CreateUserUseCase implements CreateUserPort {
    private final UserRepository userRepository;  // Domain port
    private final EventPublisherPort eventPublisher;  // Infrastructure port
    private final TimeProviderPort timeProvider;

    public CreateUserUseCase(
        UserRepository userRepository,
        EventPublisherPort eventPublisher,
        TimeProviderPort timeProvider
    ) {
        this.userRepository = userRepository;
        this.eventPublisher = eventPublisher;
        this.timeProvider = timeProvider;
    }

    @Override
    public CompletableFuture<CreateUserResponse> execute(CreateUserCommand command) {
        Email email = new Email(command.getEmail());
        User user = User.create(email, command.getName());

        return userRepository.save(user)  // Domain port
            .thenCompose(v -> {
                UserCreated event = new UserCreated(
                    user.getId(),
                    user.getEmail(),
                    user.getName(),
                    timeProvider.now()
                );
                return eventPublisher.publish(event);  // Infrastructure port
            })
            .thenApply(v -> new CreateUserResponse(user.getId().value()));
    }
}

// Event Handler as Use Case
@Service
public class SendWelcomeEmailUseCase {
    private final EmailNotificationPort emailService;  // Infrastructure port

    public SendWelcomeEmailUseCase(EmailNotificationPort emailService) {
        this.emailService = emailService;
    }

    @EventListener
    @Async
    public CompletableFuture<Void> handle(UserCreated event) {
        return emailService.sendWelcomeEmail(event.email(), event.name());
    }
}
```

## Validation and Error Handling Rules

### 11. Validation and Error Handling Rules

- Domain validation should happen in domain objects (entities, value objects)
- Use domain exceptions that extend a base domain exception
- Validation should be explicit and fail fast
- Input validation in application services should be minimal
- Use factory methods for complex validation scenarios
- Use proper exception hierarchy

```java
public abstract class DomainException extends RuntimeException {
    protected DomainException(String message) {
        super(message);
    }

    protected DomainException(String message, Throwable cause) {
        super(message, cause);
    }
}

public class InvalidEmailException extends DomainException {
    public InvalidEmailException(String email) {
        super("Invalid email format: " + email);
    }
}

public class UserNotFoundException extends DomainException {
    public UserNotFoundException(UserId userId) {
        super("User not found with ID: " + userId.value());
    }
}

public class UserAlreadyExistsException extends DomainException {
    public UserAlreadyExistsException(Email email) {
        super("User already exists with email: " + email.value());
    }
}

public record Email(String value) {
    public Email {
        if (value == null || value.trim().isEmpty()) {
            throw new InvalidEmailException(value);
        }
        if (!isValidEmail(value)) {
            throw new InvalidEmailException(value);
        }
    }

    private static boolean isValidEmail(String value) {
        return value.contains("@") &&
               value.indexOf("@") > 0 &&
               value.indexOf("@") < value.length() - 1;
    }

    public String getDomain() {
        return value.substring(value.indexOf("@") + 1);
    }
}

// Global exception handler for web layer
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(DomainException.class)
    public ResponseEntity<ErrorResponse> handleDomainException(DomainException ex) {
        ErrorResponse response = new ErrorResponse(
            "DOMAIN_ERROR",
            ex.getMessage(),
            Instant.now()
        );
        return ResponseEntity.badRequest().body(response);
    }

    @ExceptionHandler(UserNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleUserNotFound(UserNotFoundException ex) {
        ErrorResponse response = new ErrorResponse(
            "USER_NOT_FOUND",
            ex.getMessage(),
            Instant.now()
        );
        return ResponseEntity.notFound().build();
    }
}
```

### 12. Naming Convention Rules

- Use domain language (Ubiquitous Language) for all class and method names
- Avoid technical terms in domain layer (no "Manager", "Helper", "Util")
- Use intention-revealing names for methods
- Value objects should be named after the concept they represent
- Repository methods should reflect business queries
- **Port Naming**: End driving ports with "Port", driven ports with "Port"
- **Adapter Naming**: Include the technology/framework in driven adapter names
- **Clear Port vs Adapter distinction**: Ports define interfaces, Adapters implement them
- Use Java naming conventions: PascalCase for classes, camelCase for methods and variables

```java
// Good port names
public interface UserManagementPort {} // Driving port
public interface EmailNotificationPort {} // Driven port
public interface PaymentProcessingPort {} // Driven port
public interface FileStoragePort {} // Driven port

// Good adapter names
@RestController
public class UserRestController {} // Driving adapter (REST)

@Component
public class UserGraphQLController {} // Driving adapter (GraphQL)

@Repository
public class JpaUserRepository implements UserRepository {} // Driven adapter (JPA)

@Repository
public class MongoUserRepository implements UserRepository {} // Driven adapter (MongoDB)

@Service
public class SmtpEmailAdapter implements EmailNotificationPort {} // Driven adapter (SMTP)

@Service
public class SendGridEmailAdapter implements EmailNotificationPort {} // Driven adapter (SendGrid)

@Service
public class S3FileStorageAdapter implements FileStoragePort {} // Driven adapter (AWS S3)
```

### 13. Dependency Rules

- Domain layer should have no external dependencies except standard library
- Application layer can depend on domain but should use dependency inversion for external concerns
- Infrastructure layer implements all external dependencies through adapters
- **Domain Port Dependencies**: Domain objects can depend on domain ports (repositories, domain services)
- **Infrastructure Port Dependencies**: Use cases depend on infrastructure ports for external concerns
- **Port Placement**: Domain ports in domain layer, infrastructure ports in application layer
- **Inversion of Control**: Use Spring's DI container to wire adapters to ports at startup
- Use dependency inversion - depend on abstractions, not concretions
- Inject dependencies through constructors
- Use factory pattern for complex object creation

```java
// Domain layer - can depend on domain ports
public class User extends Entity<UserId> {
    // Domain entity - no external dependencies
    private Email email;
    private String name;

    public User(UserId id, Email email, String name) {
        super(id);
        this.email = Objects.requireNonNull(email);
        this.name = Objects.requireNonNull(name);
        validate();
    }

    public void changeEmail(Email newEmail) {
        // Business logic here - no external dependencies
        this.email = newEmail;
    }

    private void validate() {
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Name cannot be empty");
        }
    }
}

@Service
public class UserDomainService {
    // Domain service - can depend on domain ports
    private final UserRepository userRepository; // Domain port dependency

    public UserDomainService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public CompletableFuture<Boolean> isEmailUnique(Email email) {
        return userRepository.findByEmail(email)
            .thenApply(Optional::isEmpty);
    }
}

// Application layer - depends on domain + infrastructure ports
@Service
public class CreateUserUseCase implements CreateUserPort {
    private final UserRepository userRepository; // Domain port
    private final UserDomainService userDomainService; // Domain service
    private final EmailNotificationPort emailService; // Infrastructure port
    private final EventPublisherPort eventPublisher; // Infrastructure port

    public CreateUserUseCase(
        UserRepository userRepository,
        UserDomainService userDomainService,
        EmailNotificationPort emailService,
        EventPublisherPort eventPublisher
    ) {
        this.userRepository = userRepository;
        this.userDomainService = userDomainService;
        this.emailService = emailService;
        this.eventPublisher = eventPublisher;
    }

    // Use case implementation...
}

// Infrastructure layer - implements ports with external dependencies
@Repository
public class JpaUserRepository implements UserRepository {
    // Implements domain port
    private final UserJpaRepository jpaRepository; // External dependency (Spring Data)
    private final UserMapper userMapper;

    public JpaUserRepository(UserJpaRepository jpaRepository, UserMapper userMapper) {
        this.jpaRepository = jpaRepository;
        this.userMapper = userMapper;
    }

    // Implementation...
}

@Service
public class SmtpEmailAdapter implements EmailNotificationPort {
    // Implements infrastructure port
    private final JavaMailSender mailSender; // External dependency (Spring Mail)

    public SmtpEmailAdapter(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }

    // Implementation...
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
- Use JUnit 5, Mockito, and Spring Boot Test features

```java
// Contract test for all UserRepository implementations
@TestMethodSource("userRepositoryImplementations")
class UserRepositoryContractTest {

    static Stream<Arguments> userRepositoryImplementations() {
        return Stream.of(
            Arguments.of("JpaUserRepository", createJpaUserRepository()),
            Arguments.of("MongoUserRepository", createMongoUserRepository()),
            Arguments.of("InMemoryUserRepository", createInMemoryUserRepository())
        );
    }

    @ParameterizedTest(name = "{0} should save and find user")
    @MethodSource("userRepositoryImplementations")
    void shouldSaveAndFindUser(String repositoryName, UserRepository repository) {
        // This test should pass for all UserRepository implementations
        User user = User.create(new Email("test@example.com"), "John");

        repository.save(user).join();
        Optional<User> found = repository.findByEmail(new Email("test@example.com")).join();

        assertThat(found).isPresent();
        assertThat(found.get().getEmail()).isEqualTo(user.getEmail());
        assertThat(found.get().getName()).isEqualTo(user.getName());
    }
}

// Use Case Integration Test with real implementations
@SpringBootTest
@Testcontainers
class CreateUserUseCaseIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:13")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");

    @Autowired
    private CreateUserUseCase createUserUseCase;

    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldCreateUserSuccessfully() {
        // Given
        CreateUserCommand command = new CreateUserCommand("john@example.com", "John Doe");

        // When
        CompletableFuture<CreateUserResponse> result = createUserUseCase.execute(command);
        CreateUserResponse response = result.join();

        // Then
        assertThat(response.getUserId()).isNotNull();

        Optional<User> savedUser = userRepository.findByEmail(new Email("john@example.com")).join();
        assertThat(savedUser).isPresent();
        assertThat(savedUser.get().getName()).isEqualTo("John Doe");
    }
}

// Use Case Unit Test with Mocks
@ExtendWith(MockitoExtension.class)
class CreateUserUseCaseTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailNotificationPort emailService;

    @Mock
    private EventPublisherPort eventPublisher;

    @Mock
    private TimeProviderPort timeProvider;

    @InjectMocks
    private CreateUserUseCase createUserUseCase;

    @Test
    void shouldCreateUserSuccessfully() {
        // Given
        CreateUserCommand command = new CreateUserCommand("john@example.com", "John Doe");
        Instant fixedTime = Instant.parse("2023-01-01T00:00:00Z");

        when(userRepository.existsByEmail(any(Email.class)))
            .thenReturn(CompletableFuture.completedFuture(false));
        when(userRepository.save(any(User.class)))
            .thenReturn(CompletableFuture.completedFuture(null));
        when(eventPublisher.publish(any(DomainEvent.class)))
            .thenReturn(CompletableFuture.completedFuture(null));
        when(timeProvider.now()).thenReturn(fixedTime);

        // When
        CompletableFuture<CreateUserResponse> result = createUserUseCase.execute(command);
        CreateUserResponse response = result.join();

        // Then
        assertThat(response.getUserId()).isNotNull();

        verify(userRepository).existsByEmail(new Email("john@example.com"));
        verify(userRepository).save(any(User.class));
        verify(eventPublisher).publish(any(UserCreated.class));
        verifyNoMoreInteractions(userRepository, eventPublisher);
    }

    @Test
    void shouldThrowExceptionWhenUserAlreadyExists() {
        // Given
        CreateUserCommand command = new CreateUserCommand("john@example.com", "John Doe");

        when(userRepository.existsByEmail(any(Email.class)))
            .thenReturn(CompletableFuture.completedFuture(true));

        // When & Then
        assertThatThrownBy(() -> createUserUseCase.execute(command).join())
            .hasCauseInstanceOf(UserAlreadyExistsException.class);

        verify(userRepository).existsByEmail(new Email("john@example.com"));
        verify(userRepository, never()).save(any(User.class));
        verify(eventPublisher, never()).publish(any(DomainEvent.class));
    }
}

// Technology-specific adapter testing
@DataJpaTest
class JpaUserRepositoryTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private UserJpaRepository jpaRepository;

    private JpaUserRepository userRepository;
    private UserMapper userMapper = new UserMapperImpl();

    @BeforeEach
    void setUp() {
        userRepository = new JpaUserRepository(jpaRepository, userMapper);
    }

    @Test
    void shouldSaveAndFindUserWithJpaModels() {
        // Given
        User user = User.create(new Email("test@example.com"), "John Doe");

        // When
        userRepository.save(user).join();
        entityManager.flush();
        entityManager.clear();

        // Then
        Optional<User> foundUser = userRepository.findByEmail(new Email("test@example.com")).join();
        assertThat(foundUser).isPresent();
        assertThat(foundUser.get().getEmail()).isEqualTo(user.getEmail());
        assertThat(foundUser.get().getName()).isEqualTo(user.getName());

        // Verify JPA entity was created correctly
        Optional<UserEntity> userEntity = jpaRepository.findByEmail("test@example.com");
        assertThat(userEntity).isPresent();
        assertThat(userEntity.get().getName()).isEqualTo("John Doe");
        assertThat(userEntity.get().getEmail()).isEqualTo("test@example.com");
    }
}

// Test Data Builders
public class UserTestDataBuilder {
    private Email email = new Email("default@example.com");
    private String name = "Default Name";

    public UserTestDataBuilder withEmail(String email) {
        this.email = new Email(email);
        return this;
    }

    public UserTestDataBuilder withName(String name) {
        this.name = name;
        return this;
    }

    public User build() {
        return User.create(email, name);
    }
}

// Usage in tests:
User user = new UserTestDataBuilder()
    .withEmail("john@example.com")
    .withName("John Doe")
    .build();
```

## Ports & Adapters (Hexagonal Architecture) Rules

### 1. Port Definition Rules

- Ports define interfaces between layers and external systems
- **Driving ports** (primary/left-side) define application use cases - belong in application layer
- **Domain-driven driven ports** (repositories, domain services) - belong in domain layer
- **Infrastructure driven ports** (email, messaging, external APIs) - belong in application layer
- Port interfaces should use domain language, not technical terms
- Ports should be focused and follow Single Responsibility Principle

```java
// Driving Ports (Application Layer) - application/ports/driving/
public interface CreateUserPort {
    CompletableFuture<CreateUserResponse> execute(CreateUserCommand command);
}

public interface ChangeUserEmailPort {
    CompletableFuture<Void> execute(ChangeEmailCommand command);
}

public interface FindUserPort {
    CompletableFuture<Optional<UserResponse>> findById(UserId userId);
    CompletableFuture<Optional<UserResponse>> findByEmail(Email email);
}

// Domain-Driven Driven Ports (Domain Layer) - domain/repositories/
public interface UserRepository {
    // Already shown in rule 5
    CompletableFuture<Optional<User>> findByEmail(Email email);
    CompletableFuture<Void> save(User user);
}

// Domain Services (Domain Layer) - domain/services/
public interface PricingServicePort {
    Money calculateProductPrice(Product product, Customer customer);
    boolean isEligibleForDiscount(Customer customer, Product product);
}

// Infrastructure Driven Ports (Application Layer) - application/ports/driven/
public interface EmailNotificationPort {
    CompletableFuture<Void> sendWelcomeEmail(Email userEmail, String userName);
    CompletableFuture<Void> sendEmailChangeNotification(Email oldEmail, Email newEmail);
    CompletableFuture<Void> sendPasswordResetEmail(Email userEmail, String resetToken);
}

public interface EventPublisherPort {
    CompletableFuture<Void> publish(DomainEvent event);
    CompletableFuture<Void> publishAll(List<DomainEvent> events);
}

public interface FileStoragePort {
    CompletableFuture<String> store(String fileName, InputStream inputStream);
    CompletableFuture<InputStream> retrieve(String fileName);
    CompletableFuture<Void> delete(String fileName);
}

public interface TimeProviderPort {
    Instant now();
    LocalDateTime nowLocal();
    LocalDate today();
}

public interface IdGeneratorPort {
    String generateUuid();
    String generateShortId();
    long generateSequence(String sequenceName);
}

public interface RandomProviderPort {
    int nextInt(int bound);
    double nextDouble();
    String generateToken(int length);
}
```

### 2. Driving Adapter Rules

- Driving adapters are the entry points (web controllers, CLI, message consumers)
- Should translate external requests to domain commands/queries
- Must not contain business logic - only translation and validation
- Should handle framework-specific concerns (HTTP status codes, serialization)
- Should be thin and delegate to use cases through driving ports
- Use Spring Boot patterns and annotations

```java
// Spring Boot REST Controller (Driving Adapter)
@RestController
@RequestMapping("/api/users")
@Validated
public class UserRestController {
    private final CreateUserPort createUserUseCase;
    private final ChangeUserEmailPort changeEmailUseCase;
    private final FindUserPort findUserUseCase;

    public UserRestController(
        CreateUserPort createUserUseCase,
        ChangeUserEmailPort changeEmailUseCase,
        FindUserPort findUserUseCase
    ) {
        this.createUserUseCase = createUserUseCase;
        this.changeEmailUseCase = changeEmailUseCase;
        this.findUserUseCase = findUserUseCase;
    }

    @PostMapping
    public CompletableFuture<ResponseEntity<CreateUserResponse>> createUser(
        @RequestBody @Valid CreateUserRequest request
    ) {
        CreateUserCommand command = new CreateUserCommand(request.getEmail(), request.getName());

        return createUserUseCase.execute(command)
            .thenApply(response -> ResponseEntity.status(HttpStatus.CREATED).body(response))
            .exceptionally(throwable -> {
                if (throwable.getCause() instanceof UserAlreadyExistsException) {
                    throw new ResponseStatusException(HttpStatus.CONFLICT, throwable.getCause().getMessage());
                } else if (throwable.getCause() instanceof InvalidEmailException) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, throwable.getCause().getMessage());
                } else if (throwable.getCause() instanceof DomainException) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, throwable.getCause().getMessage());
                } else {
                    throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Internal server error");
                }
            });
    }

    @PatchMapping("/{userId}/email")
    public CompletableFuture<ResponseEntity<Void>> changeUserEmail(
        @PathVariable String userId,
        @RequestBody @Valid ChangeEmailRequest request
    ) {
        ChangeEmailCommand command = new ChangeEmailCommand(new UserId(userId), request.getEmail());

        return changeEmailUseCase.execute(command)
            .thenApply(v -> ResponseEntity.<Void>noContent().build())
            .exceptionally(throwable -> {
                if (throwable.getCause() instanceof UserNotFoundException) {
                    throw new ResponseStatusException(HttpStatus.NOT_FOUND, throwable.getCause().getMessage());
                } else if (throwable.getCause() instanceof InvalidEmailException) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, throwable.getCause().getMessage());
                } else if (throwable.getCause() instanceof DomainException) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, throwable.getCause().getMessage());
                } else {
                    throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Internal server error");
                }
            });
    }

    @GetMapping("/{userId}")
    public CompletableFuture<ResponseEntity<UserResponse>> getUserById(@PathVariable String userId) {
        UserId userIdVO = new UserId(userId);

        return findUserUseCase.findById(userIdVO)
            .thenApply(userOpt -> userOpt
                .map(user -> ResponseEntity.ok(user))
                .orElse(ResponseEntity.notFound().build())
            );
    }
}

// Request/Response DTOs
public class CreateUserRequest {
    @NotBlank(message = "Email is required")
    @Email(message = "Email must be valid")
    private String email;

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be between 2 and 100 characters")
    private String name;

    // Constructors, getters, setters
    public CreateUserRequest() {}

    public CreateUserRequest(String email, String name) {
        this.email = email;
        this.name = name;
    }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
}

public class ChangeEmailRequest {
    @NotBlank(message = "Email is required")
    @Email(message = "Email must be valid")
    private String email;

    public ChangeEmailRequest() {}

    public ChangeEmailRequest(String email) {
        this.email = email;
    }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}

public record CreateUserResponse(String userId) {}

public record UserResponse(String userId, String email, String name) {}

// Command Line Interface Adapter
@Component
public class UserCliController implements CommandLineRunner {
    private final CreateUserPort createUserUseCase;
    private final FindUserPort findUserUseCase;

    public UserCliController(CreateUserPort createUserUseCase, FindUserPort findUserUseCase) {
        this.createUserUseCase = createUserUseCase;
        this.findUserUseCase = findUserUseCase;
    }

    @Override
    public void run(String... args) throws Exception {
        if (args.length > 0 && "create-user".equals(args[0])) {
            if (args.length < 3) {
                System.err.println("Usage: create-user <email> <name>");
                return;
            }

            CreateUserCommand command = new CreateUserCommand(args[1], args[2]);
            try {
                CreateUserResponse response = createUserUseCase.execute(command).join();
                System.out.println("User created with ID: " + response.userId());
            } catch (Exception e) {
                System.err.println("Failed to create user: " + e.getMessage());
            }
        }
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

```java
// JPA Database Adapter - infrastructure/adapters/driven/jpa/JpaUserRepository.java
@Repository
@Transactional
public class JpaUserRepository implements UserRepository {
    private final UserJpaRepository jpaRepository;
    private final UserMapper userMapper;

    public JpaUserRepository(UserJpaRepository jpaRepository, UserMapper userMapper) {
        this.jpaRepository = jpaRepository;
        this.userMapper = userMapper;
    }

    @Override
    public CompletableFuture<Void> save(User user) {
        return CompletableFuture.runAsync(() -> {
            try {
                UserEntity entity = userMapper.toEntity(user);
                jpaRepository.save(entity);
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to save user", e);
            }
        });
    }

    @Override
    public CompletableFuture<Optional<User>> findByEmail(Email email) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return jpaRepository.findByEmail(email.value())
                    .map(userMapper::toDomain);
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to find user by email", e);
            }
        });
    }

    @Override
    public CompletableFuture<Optional<User>> findById(UserId userId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return jpaRepository.findById(userId.value())
                    .map(userMapper::toDomain);
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to find user by ID", e);
            }
        });
    }

    @Override
    public CompletableFuture<List<User>> findActiveUsersInDepartment(DepartmentId departmentId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return jpaRepository.findActiveUsersInDepartment(departmentId.value())
                    .stream()
                    .map(userMapper::toDomain)
                    .collect(Collectors.toList());
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to find active users", e);
            }
        });
    }

    @Override
    public CompletableFuture<Boolean> existsByEmail(Email email) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return jpaRepository.existsByEmail(email.value());
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to check if user exists", e);
            }
        });
    }

    @Override
    public CompletableFuture<Void> delete(User user) {
        return CompletableFuture.runAsync(() -> {
            try {
                jpaRepository.deleteById(user.getId().value());
            } catch (DataAccessException e) {
                throw new UserRepositoryException("Failed to delete user", e);
            }
        });
    }
}

// JPA Entity Model (internal to adapter)
@Entity
@Table(name = "users")
class UserEntity {
    @Id
    private String id;

    @Column(unique = true)
    private String email;

    @Column
    private String name;

    @Version
    private Long version;

    @CreationTimestamp
    private Instant createdAt;

    @UpdateTimestamp
    private Instant updatedAt;

    // Constructors, getters, setters
    protected UserEntity() {}

    public UserEntity(String id, String email, String name) {
        this.id = id;
        this.email = email;
        this.name = name;
    }

    // Getters and setters...
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }
}

// Spring Data JPA Repository Interface
interface UserJpaRepository extends JpaRepository<UserEntity, String> {
    Optional<UserEntity> findByEmail(String email);
    boolean existsByEmail(String email);

    @Query("SELECT u FROM UserEntity u WHERE u.departmentId = :departmentId AND u.active = true")
    List<UserEntity> findActiveUsersInDepartment(@Param("departmentId") String departmentId);
}

// Mapper between Domain and JPA models
@Component
public class UserMapper {
    public UserEntity toEntity(User user) {
        return new UserEntity(
            user.getId().value(),
            user.getEmail().value(),
            user.getName()
        );
    }

    public User toDomain(UserEntity entity) {
        return new User(
            new UserId(entity.getId()),
            new Email(entity.getEmail()),
            entity.getName()
        );
    }
}

// Email Service Adapter - infrastructure/adapters/driven/email/
@Service
public class SmtpEmailAdapter implements EmailNotificationPort {
    private final JavaMailSender mailSender;
    private final EmailTemplateService templateService;

    @Value("${app.email.from}")
    private String fromAddress;

    public SmtpEmailAdapter(JavaMailSender mailSender, EmailTemplateService templateService) {
        this.mailSender = mailSender;
        this.templateService = templateService;
    }

    @Override
    @Async
    public CompletableFuture<Void> sendWelcomeEmail(Email userEmail, String userName) {
        return CompletableFuture.runAsync(() -> {
            try {
                MimeMessage message = mailSender.createMimeMessage();
                MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

                helper.setFrom(fromAddress);
                helper.setTo(userEmail.value());
                helper.setSubject("Welcome to Our Platform");

                String content = templateService.processWelcomeTemplate(userName);
                helper.setText(content, true);

                mailSender.send(message);
            } catch (MessagingException e) {
                throw new EmailDeliveryException("Failed to send welcome email", e);
            }
        });
    }

    @Override
    @Async
    public CompletableFuture<Void> sendEmailChangeNotification(Email oldEmail, Email newEmail) {
        return CompletableFuture.runAsync(() -> {
            try {
                // Send notification to both old and new email addresses
                sendEmailChangeNotificationTo(oldEmail, "Your email address has been changed");
                sendEmailChangeNotificationTo(newEmail, "Your email address has been updated");
            } catch (Exception e) {
                throw new EmailDeliveryException("Failed to send email change notification", e);
            }
        });
    }

    private void sendEmailChangeNotificationTo(Email emailAddress, String subject) throws MessagingException {
        MimeMessage message = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

        helper.setFrom(fromAddress);
        helper.setTo(emailAddress.value());
        helper.setSubject(subject);

        String content = templateService.processEmailChangeTemplate();
        helper.setText(content, true);

        mailSender.send(message);
    }
}

// HTTP External API Adapter - infrastructure/adapters/driven/http/
@Service
public class HttpPaymentAdapter implements PaymentProcessingPort {
    private final WebClient webClient;
    private final PaymentApiProperties apiProperties;

    public HttpPaymentAdapter(WebClient.Builder webClientBuilder, PaymentApiProperties apiProperties) {
        this.apiProperties = apiProperties;
        this.webClient = webClientBuilder
            .baseUrl(apiProperties.getBaseUrl())
            .defaultHeader("Authorization", "Bearer " + apiProperties.getApiKey())
            .defaultHeader("Content-Type", "application/json")
            .build();
    }

    @Override
    public CompletableFuture<PaymentResult> processPayment(PaymentRequest paymentRequest) {
        PaymentApiRequest apiRequest = mapToApiRequest(paymentRequest);

        return webClient.post()
            .uri("/payments")
            .bodyValue(apiRequest)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError, response ->
                response.bodyToMono(String.class)
                    .map(body -> new PaymentProcessingException("Payment failed: " + body)))
            .onStatus(HttpStatusCode::is5xxServerError, response ->
                Mono.error(new PaymentProcessingException("Payment service unavailable")))
            .bodyToMono(PaymentApiResponse.class)
            .map(this::mapToPaymentResult)
            .toFuture();
    }

    private PaymentApiRequest mapToApiRequest(PaymentRequest request) {
        return new PaymentApiRequest(
            request.getAmount().getAmount(),
            request.getAmount().getCurrency().getCurrencyCode(),
            request.getPaymentMethodId(),
            request.getDescription()
        );
    }

    private PaymentResult mapToPaymentResult(PaymentApiResponse response) {
        return new PaymentResult(
            response.getId(),
            PaymentStatus.valueOf(response.getStatus().toUpperCase()),
            response.getTransactionId()
        );
    }
}

// File Storage Adapter - infrastructure/adapters/driven/storage/
@Service
public class S3FileStorageAdapter implements FileStoragePort {
    private final AmazonS3 s3Client;
    private final String bucketName;

    public S3FileStorageAdapter(AmazonS3 s3Client, @Value("${aws.s3.bucket}") String bucketName) {
        this.s3Client = s3Client;
        this.bucketName = bucketName;
    }

    @Override
    public CompletableFuture<String> store(String fileName, InputStream inputStream) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String key = generateUniqueKey(fileName);
                ObjectMetadata metadata = new ObjectMetadata();

                PutObjectRequest putRequest = new PutObjectRequest(bucketName, key, inputStream, metadata);
                s3Client.putObject(putRequest);

                return key;
            } catch (AmazonS3Exception e) {
                throw new FileStorageException("Failed to store file: " + fileName, e);
            }
        });
    }

    @Override
    public CompletableFuture<InputStream> retrieve(String fileName) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                S3Object s3Object = s3Client.getObject(bucketName, fileName);
                return s3Object.getObjectContent();
            } catch (AmazonS3Exception e) {
                if (e.getStatusCode() == 404) {
                    throw new FileNotFoundException("File not found: " + fileName);
                }
                throw new FileStorageException("Failed to retrieve file: " + fileName, e);
            }
        });
    }

    @Override
    public CompletableFuture<Void> delete(String fileName) {
        return CompletableFuture.runAsync(() -> {
            try {
                s3Client.deleteObject(bucketName, fileName);
            } catch (AmazonS3Exception e) {
                throw new FileStorageException("Failed to delete file: " + fileName, e);
            }
        });
    }

    private String generateUniqueKey(String fileName) {
        String timestamp = Instant.now().toString();
        String uuid = UUID.randomUUID().toString().substring(0, 8);
        return timestamp + "_" + uuid + "_" + fileName;
    }
}

// System Infrastructure Adapters
@Service
public class SystemTimeProvider implements TimeProviderPort {
    @Override
    public Instant now() {
        return Instant.now();
    }

    @Override
    public LocalDateTime nowLocal() {
        return LocalDateTime.now();
    }

    @Override
    public LocalDate today() {
        return LocalDate.now();
    }
}

@Service
public class UuidIdGenerator implements IdGeneratorPort {
    private final AtomicLong sequenceCounter = new AtomicLong(0);

    @Override
    public String generateUuid() {
        return UUID.randomUUID().toString();
    }

    @Override
    public String generateShortId() {
        return UUID.randomUUID().toString().substring(0, 8);
    }

    @Override
    public long generateSequence(String sequenceName) {
        // In a real implementation, this might query a database sequence
        return sequenceCounter.incrementAndGet();
    }
}

@Service
public class SecureRandomProvider implements RandomProviderPort {
    private final SecureRandom secureRandom = new SecureRandom();

    @Override
    public int nextInt(int bound) {
        return secureRandom.nextInt(bound);
    }

    @Override
    public double nextDouble() {
        return secureRandom.nextDouble();
    }

    @Override
    public String generateToken(int length) {
        String characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder token = new StringBuilder();

        for (int i = 0; i < length; i++) {
            token.append(characters.charAt(secureRandom.nextInt(characters.length())));
        }

        return token.toString();
    }
}
```

## Spring Boot Integration Examples

### Configuration and Wiring

```java
// Application Configuration
@Configuration
@EnableJpaRepositories(basePackages = "com.example.infrastructure.adapters.driven.jpa")
@EnableAsync
@EnableScheduling
public class ApplicationConfiguration {

    // Web Client Configuration
    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder()
            .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(1024 * 1024))
            .build();
    }

    // Email Configuration
    @Bean
    public JavaMailSender javaMailSender(
        @Value("${spring.mail.host}") String host,
        @Value("${spring.mail.port}") int port,
        @Value("${spring.mail.username}") String username,
        @Value("${spring.mail.password}") String password
    ) {
        JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
        mailSender.setHost(host);
        mailSender.setPort(port);
        mailSender.setUsername(username);
        mailSender.setPassword(password);

        Properties props = mailSender.getJavaMailProperties();
        props.put("mail.transport.protocol", "smtp");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");

        return mailSender;
    }

    // AWS S3 Configuration
    @Bean
    @ConditionalOnProperty(name = "aws.s3.enabled", havingValue = "true")
    public AmazonS3 amazonS3(
        @Value("${aws.region}") String region,
        @Value("${aws.accessKeyId}") String accessKeyId,
        @Value("${aws.secretAccessKey}") String secretAccessKey
    ) {
        AWSCredentials credentials = new BasicAWSCredentials(accessKeyId, secretAccessKey);
        return AmazonS3ClientBuilder.standard()
            .withCredentials(new AWSStaticCredentialsProvider(credentials))
            .withRegion(Regions.fromName(region))
            .build();
    }

    // Event Publishing Configuration
    @Bean
    public ApplicationEventPublisher applicationEventPublisher(ApplicationContext applicationContext) {
        return applicationContext;
    }
}

// Properties Configuration
@ConfigurationProperties(prefix = "app.payment")
@Component
public class PaymentApiProperties {
    private String baseUrl;
    private String apiKey;
    private int timeoutSeconds = 30;

    // Getters and setters
    public String getBaseUrl() { return baseUrl; }
    public void setBaseUrl(String baseUrl) { this.baseUrl = baseUrl; }

    public String getApiKey() { return apiKey; }
    public void setApiKey(String apiKey) { this.apiKey = apiKey; }

    public int getTimeoutSeconds() { return timeoutSeconds; }
    public void setTimeoutSeconds(int timeoutSeconds) { this.timeoutSeconds = timeoutSeconds; }
}
```

These integrated rules ensure that Domain Driven Design and Ports & Adapters (Hexagonal Architecture) work together seamlessly in Java implementations. The combination provides clean separation of concerns, testability, and flexibility while maintaining domain focus and proper dependency management using Spring Boot's ecosystem.

## Appendix

### Comprehensive Testing Strategies

```java
// Integration Test with TestContainers
@SpringBootTest
@Testcontainers
@TestMethodOrder(OrderAnnotation.class)
class UserManagementIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:13")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");

    @Container
    static MockServerContainer mockServer = new MockServerContainer(DockerImageName.parse("mockserver/mockserver:latest"));

    @Autowired
    private CreateUserPort createUserUseCase;

    @Autowired
    private ChangeUserEmailPort changeEmailUseCase;

    @Autowired
    private FindUserPort findUserUseCase;

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("app.email.service.url", () -> "http://localhost:" + mockServer.getServerPort());
    }

    @Test
    @Order(1)
    void shouldCreateUserEndToEnd() {
        // Given
        CreateUserCommand command = new CreateUserCommand("integration@test.com", "Integration User");

        // When
        CompletableFuture<CreateUserResponse> result = createUserUseCase.execute(command);
        CreateUserResponse response = result.join();

        // Then
        assertThat(response.getUserId()).isNotNull();

        // Verify user was persisted
        CompletableFuture<Optional<UserResponse>> findResult = findUserUseCase.findById(new UserId(response.getUserId()));
        Optional<UserResponse> foundUser = findResult.join();

        assertThat(foundUser).isPresent();
        assertThat(foundUser.get().email()).isEqualTo("integration@test.com");
        assertThat(foundUser.get().name()).isEqualTo("Integration User");
    }
}

// Performance Test
@SpringBootTest
@ActiveProfiles("performance")
class UserManagementPerformanceTest {

    @Autowired
    private CreateUserPort createUserUseCase;

    @Test
    @Timeout(value = 10, unit = TimeUnit.SECONDS)
    void shouldHandleHighVolumeUserCreation() {
        // Given
        int numberOfUsers = 1000;
        List<CompletableFuture<CreateUserResponse>> futures = new ArrayList<>();

        // When
        for (int i = 0; i < numberOfUsers; i++) {
            CreateUserCommand command = new CreateUserCommand(
                "user" + i + "@performance.test",
                "Performance User " + i
            );
            futures.add(createUserUseCase.execute(command));
        }

        // Then
        CompletableFuture<Void> allOf = CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
        assertThatCode(() -> allOf.join()).doesNotThrowAnyException();

        // Verify all users were created
        long successfulCreations = futures.stream()
            .map(CompletableFuture::join)
            .filter(Objects::nonNull)
            .count();

        assertThat(successfulCreations).isEqualTo(numberOfUsers);
    }
}
```
