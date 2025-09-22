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

```csharp
// 1. Domain Layer (DDD Core)
public class User : Entity<UserId>
{
    // Rule 1: Entity with identity
    public UserEmailChanged ChangeEmail(Email email)
    {
        // Business logic here
        return new UserEmailChanged(Id, Email, email);
    }
}

public interface IUserRepository
{
    // Rule 5: Domain port for persistence
    Task SaveAsync(User user, CancellationToken cancellationToken = default);
}

// 2. Application Layer (Bridge between DDD and Ports & Adapters)
public class ChangeUserEmailUseCase : IChangeUserEmailPort
{
    // Rule 9 + P&A Rule 1
    private readonly IUserRepository _userRepository; // Domain port
    private readonly IEmailNotificationPort _emailService; // Infrastructure port
    private readonly ITimeProviderPort _timeProvider; // Infrastructure port

    public ChangeUserEmailUseCase(
        IUserRepository userRepository,
        IEmailNotificationPort emailService,
        ITimeProviderPort timeProvider)
    {
        _userRepository = userRepository;
        _emailService = emailService;
        _timeProvider = timeProvider;
    }

    public async Task ExecuteAsync(ChangeEmailCommand command, CancellationToken cancellationToken = default)
    {
        // Orchestrate domain objects (Rule 9)
        var user = await _userRepository.FindByIdAsync(command.UserId, cancellationToken);
        var eventData = user.ChangeEmail(new Email(command.NewEmail));

        // Use infrastructure ports for side effects
        await _userRepository.SaveAsync(user, cancellationToken);
        await _emailService.SendEmailChangeNotificationAsync(
            eventData.OldEmail,
            eventData.NewEmail,
            _timeProvider.Now(),
            cancellationToken);
    }
}

// 3. Infrastructure Layer (Ports & Adapters Implementation)
public class SqlUserRepository : IUserRepository
{
    // P&A Rule 3: Driven adapter
    public async Task SaveAsync(User user, CancellationToken cancellationToken = default)
    {
        // Handle ORM mapping, database specifics
    }
}

[ApiController]
[Route("api/[controller]")]
public class UserController : ControllerBase
{
    // P&A Rule 2: Driving adapter
    [HttpPatch("{userId}/email")]
    public async Task<IActionResult> PatchUserEmailAsync(
        Guid userId,
        [FromBody] ChangeEmailRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new ChangeEmailCommand(new UserId(userId), request.Email);
        await _useCase.ExecuteAsync(command, cancellationToken); // Delegate to use case
        return NoContent();
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
- Implement `Equals` and `GetHashCode` based solely on identity, not attributes/fields
- Entities MUST contain business logic as methods, not just data
  - Avoid anemic domain models - entities should have behavior
- Include validation in constructor

```csharp
public class User : Entity<UserId>
{
    private Email _email;
    private string _name;

    public User(UserId id, Email email, string name) : base(id)
    {
        _email = email ?? throw new ArgumentNullException(nameof(email));
        _name = name ?? throw new ArgumentNullException(nameof(name));
        Validate();
    }

    public static User Create(Email email, string name)
    {
        return new User(UserId.Generate(), email, name);
    }

    public void ChangeEmail(Email newEmail)
    {
        // Business logic here
        _email = newEmail ?? throw new ArgumentNullException(nameof(newEmail));
    }

    public Email Email => _email;
    public string Name => _name;

    private void Validate()
    {
        if (_email is null || string.IsNullOrWhiteSpace(_name))
        {
            throw new InvalidOperationException("User must have email and name");
        }
    }
}

public abstract class Entity<TId> : IEquatable<Entity<TId>>
    where TId : notnull
{
    protected Entity(TId id)
    {
        Id = id;
    }

    public TId Id { get; }

    public bool Equals(Entity<TId>? other)
    {
        return other is not null && EqualityComparer<TId>.Default.Equals(Id, other.Id);
    }

    public override bool Equals(object? obj)
    {
        return obj is Entity<TId> entity && Equals(entity);
    }

    public override int GetHashCode()
    {
        return EqualityComparer<TId>.Default.GetHashCode(Id);
    }
}
```

### 2. Value Object Rules

- Value objects MUST be immutable
- Equality is based on ALL attributes, not identity
- Should be small, focused, and represent a concept from the domain
- Include validation in constructor
- Should have meaningful methods that operate on the value

```csharp
public sealed record Email
{
    public Email(string value)
    {
        if (string.IsNullOrWhiteSpace(value) || !value.Contains('@'))
        {
            throw new InvalidEmailException(value);
        }
        Value = value;
    }

    public string Value { get; }

    public string Domain => Value.Split('@')[1];

    public override string ToString() => Value;
}

// Alternative implementation using class for more complex scenarios
public sealed class EmailClass : IEquatable<EmailClass>
{
    public EmailClass(string value)
    {
        if (string.IsNullOrWhiteSpace(value) || !value.Contains('@'))
        {
            throw new InvalidEmailException(value);
        }
        Value = value;
    }

    public string Value { get; }
    public string Domain => Value.Split('@')[1];

    public bool Equals(EmailClass? other)
    {
        return other is not null && Value == other.Value;
    }

    public override bool Equals(object? obj)
    {
        return obj is EmailClass email && Equals(email);
    }

    public override int GetHashCode()
    {
        return Value.GetHashCode();
    }

    public override string ToString() => Value;
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
- Encapsulate Collections: Use first class collection from Object Calisthenics

```csharp
public class Order : Entity<OrderId>
{
    // Aggregate Root
    private readonly CustomerId _customerId;
    private readonly List<OrderLineItem> _lineItems = new();

    public Order(OrderId id, CustomerId customerId) : base(id)
    {
        _customerId = customerId;
    }

    public void AddLineItem(ProductId productId, int quantity)
    {
        // Business rules and validation
        var lineItem = new OrderLineItem(productId, quantity);
        _lineItems.Add(lineItem);
    }

    public IReadOnlyList<OrderLineItem> LineItems => _lineItems.AsReadOnly();
    public CustomerId CustomerId => _customerId;
}

public record OrderLineItem(ProductId ProductId, int Quantity);
```

### 4. Domain Service Rules

Handles business logic that spans multiple entities (e.g., transferring money between two accounts)

- Create domain services ONLY when business logic doesn't naturally fit in entities or value objects
- Domain services should be stateless
- Use dependency injection for external dependencies
- Should operate on domain objects, not primitives
- Should not use Driven ports/adapters
- Name services with domain language (not technical terms)

```csharp
public class PricingService
{
    private readonly IDiscountRepository _discountRepository;

    public PricingService(IDiscountRepository discountRepository)
    {
        _discountRepository = discountRepository;
    }

    public Money CalculateOrderTotal(Order order, Customer customer)
    {
        // Complex pricing logic that spans multiple aggregates
        throw new NotImplementedException();
    }
}
```

## Repository Pattern Rules

### 5. Repository Interface Rules

- Define repository interfaces in the domain layer using interfaces - they represent domain concepts
- Repositories should work with Aggregate Roots only
- Use domain-specific query methods, not generic CRUD
- Return domain objects, never DTOs or database models
- Input should be Aggregates not entities, value objects or DTO's
- Should throw domain exceptions, not infrastructure exceptions

```csharp
// Domain Layer - Domain/Repositories/IUserRepository.cs
public interface IUserRepository
{
    Task<User?> FindByEmailAsync(Email email, CancellationToken cancellationToken = default);
    Task SaveAsync(User user, CancellationToken cancellationToken = default);
    Task<IReadOnlyList<User>> FindActiveUsersInDepartmentAsync(DepartmentId departmentId, CancellationToken cancellationToken = default);
    Task<User?> FindByIdAsync(UserId userId, CancellationToken cancellationToken = default);
}
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
- Use readonly properties for events
- Events should be raised by aggregates, not external code

```csharp
public sealed record UserEmailChanged(
    UserId UserId,
    Email OldEmail,
    Email NewEmail,
    DateTime OccurredAt);
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

```csharp
public class CreateUserUseCase
{
    private readonly IUserRepository _userRepository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IEventPublisherPort _eventPublisher;

    public CreateUserUseCase(
        IUserRepository userRepository,
        IUnitOfWork unitOfWork,
        IEventPublisherPort eventPublisher)
    {
        _userRepository = userRepository;
        _unitOfWork = unitOfWork;
        _eventPublisher = eventPublisher;
    }

    public async Task<CreateUserResponse> ExecuteAsync(CreateUserCommand command, CancellationToken cancellationToken = default)
    {
        return await _unitOfWork.ExecuteAsync(async () =>
        {
            // Orchestration logic only
            var email = new Email(command.Email);
            var user = User.Create(email, command.Name);
            await _userRepository.SaveAsync(user, cancellationToken);
            await _eventPublisher.PublishAsync(new UserCreated(user.Id, email), cancellationToken);
            return new CreateUserResponse(user.Id.Value);
        }, cancellationToken);
    }
}

public class ChangeUserEmailUseCase
{
    private readonly IUserRepository _userRepository;
    private readonly IUnitOfWork _unitOfWork;

    public ChangeUserEmailUseCase(IUserRepository userRepository, IUnitOfWork unitOfWork)
    {
        _userRepository = userRepository;
        _unitOfWork = unitOfWork;
    }

    public async Task ExecuteAsync(ChangeEmailCommand command, CancellationToken cancellationToken = default)
    {
        await _unitOfWork.ExecuteAsync(async () =>
        {
            var user = await _userRepository.FindByIdAsync(command.UserId, cancellationToken);
            if (user is null)
            {
                throw new UserNotFoundException(command.UserId);
            }
            user.ChangeEmail(new Email(command.NewEmail));
            await _userRepository.SaveAsync(user, cancellationToken);
        }, cancellationToken);
    }
}
```

### 10. Event Integration Rules

- Domain events should be published through infrastructure ports
- Event handlers can be implemented as separate use cases
- Use event-driven architecture for cross-bounded context communication
- Events enable loose coupling between adapters and domain logic
- Consider eventual consistency for distributed operations

```csharp
// Event Publishing through Infrastructure Port
public interface IEventPublisherPort  // Application layer
{
    Task PublishAsync<T>(T domainEvent, CancellationToken cancellationToken = default) where T : IDomainEvent;
}

public class CreateUserUseCase : ICreateUserPort
{
    private readonly IUserRepository _userRepository;  // Domain port
    private readonly IEventPublisherPort _eventPublisher;  // Infrastructure port

    public CreateUserUseCase(IUserRepository userRepository, IEventPublisherPort eventPublisher)
    {
        _userRepository = userRepository;
        _eventPublisher = eventPublisher;
    }

    public async Task<CreateUserResponse> ExecuteAsync(CreateUserCommand command, CancellationToken cancellationToken = default)
    {
        var user = User.Create(new Email(command.Email), command.Name);
        await _userRepository.SaveAsync(user, cancellationToken);  // Domain port
        await _eventPublisher.PublishAsync(new UserCreated(user.Id, user.Email), cancellationToken);  // Infrastructure port
        return new CreateUserResponse(user.Id.Value);
    }
}

// Event Handler as Use Case
public class SendWelcomeEmailUseCase
{
    private readonly IEmailNotificationPort _emailService;  // Infrastructure port

    public SendWelcomeEmailUseCase(IEmailNotificationPort emailService)
    {
        _emailService = emailService;
    }

    public async Task HandleAsync(UserCreated eventData, CancellationToken cancellationToken = default)
    {
        await _emailService.SendWelcomeEmailAsync(eventData.Email, eventData.Name, cancellationToken);
    }
}
```

## Validation and Error Handling Rules

- Test domain logic in isolation without any adapters
- Test driving adapters by mocking driving ports
- Test driven adapters by mocking external dependencies
- Use in-memory implementations of driven ports for integration tests
- Test the full flow from driving adapter to driven adapter for end-to-end tests

```csharp
// Testing with port isolation
[Fact]
public async Task CreateUser_Success_ReturnsUserId()
{
    // Arrange
    var mockRepo = Substitute.For<IUserRepository>();
    var mockEvents = Substitute.For<IEventPublisherPort>();
    var service = new UserManagementService(mockRepo, mockEvents);

    // Act
    var result = await service.CreateUserAsync(new CreateUserCommand("test@example.com", "John"));

    // Assert
    await mockRepo.Received(1).SaveAsync(Arg.Any<User>(), Arg.Any<CancellationToken>());
    await mockEvents.Received(1).PublishAsync(Arg.Any<UserCreated>(), Arg.Any<CancellationToken>());
    Assert.NotNull(result.UserId);
}

// In-memory adapter for testing
public class InMemoryUserRepository : IUserRepository
{
    private readonly Dictionary<Guid, User> _users = new();

    public Task SaveAsync(User user, CancellationToken cancellationToken = default)
    {
        _users[user.Id.Value] = user;
        return Task.CompletedTask;
    }

    public Task<User?> FindByEmailAsync(Email email, CancellationToken cancellationToken = default)
    {
        var user = _users.Values.FirstOrDefault(u => u.Email.Equals(email));
        return Task.FromResult(user);
    }

    public Task<User?> FindByIdAsync(UserId userId, CancellationToken cancellationToken = default)
    {
        _users.TryGetValue(userId.Value, out var user);
        return Task.FromResult(user);
    }

    public Task<IReadOnlyList<User>> FindActiveUsersInDepartmentAsync(DepartmentId departmentId, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<IReadOnlyList<User>>(new List<User>());
    }
}
```

### 11. Validation and Error Handling Rules

- Domain validation should happen in domain objects (entities, value objects)
- Use domain exceptions that extend a base domain exception
- Validation should be explicit and fail fast
- Input validation in application services should be minimal
- Use factory methods for complex validation scenarios

```csharp
public class DomainException : Exception
{
    protected DomainException(string message) : base(message)
    {
    }

    protected DomainException(string message, Exception innerException) : base(message, innerException)
    {
    }
}

public class InvalidEmailException : DomainException
{
    public InvalidEmailException(string email) : base($"Invalid email: {email}")
    {
        Email = email;
    }

    public string Email { get; }
}

public sealed record Email
{
    public Email(string value)
    {
        if (!IsValidEmail(value))
        {
            throw new InvalidEmailException(value);
        }
        Value = value;
    }

    private static bool IsValidEmail(string value)
    {
        return !string.IsNullOrWhiteSpace(value) && value.Contains('@');
    }

    public string Value { get; }
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

```csharp
// Good port names
public interface IUserManagementPort { } // Driving port
public interface IEmailNotificationPort { } // Driven port
public interface IPaymentProcessingPort { } // Driven port

// Good adapter names
public class RestUserController { } // Driving adapter (REST)
public class GraphQLUserController { } // Driving adapter (GraphQL)
public class SqlUserRepository : IUserRepository { } // Driven adapter (SQL)
public class MongoUserRepository : IUserRepository { } // Driven adapter (MongoDB)
public class SmtpEmailAdapter : IEmailNotificationPort { } // Driven adapter (SMTP)
public class SendGridEmailAdapter : IEmailNotificationPort { } // Driven adapter (SendGrid)
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

```csharp
// Domain layer - can depend on domain ports
public class User
{
    // Domain entity
    public User(UserId id, Email email, string name)
    {
        Id = id;
        Email = email;
        Name = name;
    }

    public UserId Id { get; }
    public Email Email { get; private set; }
    public string Name { get; }

    public void ChangeEmail(Email newEmail)
    {
        // Business logic here
        Email = newEmail;
    }
}

public class UserDomainService
{
    // Domain service
    private readonly IUserRepository _userRepository; // Domain port dependency

    public UserDomainService(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<bool> IsEmailUniqueAsync(Email email, CancellationToken cancellationToken = default)
    {
        var existingUser = await _userRepository.FindByEmailAsync(email, cancellationToken);
        return existingUser is null;
    }
}

// Application layer - depends on domain + infrastructure ports
public class CreateUserUseCase : ICreateUserPort
{
    private readonly IUserRepository _userRepository; // Domain port
    private readonly UserDomainService _userDomainService; // Domain service
    private readonly IEmailNotificationPort _emailService; // Infrastructure port
    private readonly IEventPublisherPort _eventPublisher; // Infrastructure port

    public CreateUserUseCase(
        IUserRepository userRepository,
        UserDomainService userDomainService,
        IEmailNotificationPort emailService,
        IEventPublisherPort eventPublisher)
    {
        _userRepository = userRepository;
        _userDomainService = userDomainService;
        _emailService = emailService;
        _eventPublisher = eventPublisher;
    }
}

// Infrastructure layer - implements ports with external dependencies
public class SqlUserRepository : IUserRepository
{
    // Implements domain port
    private readonly ApplicationDbContext _context; // External dependency

    public SqlUserRepository(ApplicationDbContext context)
    {
        _context = context;
    }
}

public class SmtpEmailAdapter : IEmailNotificationPort
{
    // Implements infrastructure port
    private readonly SmtpClient _smtpClient; // External dependency

    public SmtpEmailAdapter(SmtpClient smtpClient)
    {
        _smtpClient = smtpClient;
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

```csharp
// Contract test for all IUserRepository implementations
[Theory]
[InlineData(typeof(SqlUserRepository))]
[InlineData(typeof(MongoUserRepository))]
public async Task UserRepository_SaveAndFind_ShouldWork(Type repositoryType)
{
    // This test should pass for all IUserRepository implementations
    var repository = CreateRepository(repositoryType);
    var user = User.Create(new Email("test@example.com"), "John");

    await repository.SaveAsync(user);
    var found = await repository.FindByEmailAsync(new Email("test@example.com"));

    Assert.NotNull(found);
    Assert.Equal(user.Email, found.Email);
}

// Use Case Integration Test
[Fact]
public async Task CreateUserUseCase_FullWorkflow_WithInMemoryAdapters()
{
    // Arrange
    var userRepo = new InMemoryUserRepository();
    var emailService = new InMemoryEmailService();
    var eventPublisher = new InMemoryEventPublisher();
    var useCase = new CreateUserUseCase(userRepo, emailService, eventPublisher);

    // Act
    var result = await useCase.ExecuteAsync(new CreateUserCommand("test@example.com", "John"));

    // Assert
    Assert.NotEmpty(result.UserId);
    var savedUser = await userRepo.FindByEmailAsync(new Email("test@example.com"));
    Assert.NotNull(savedUser);
    Assert.Single(emailService.SentEmails);
    Assert.Single(eventPublisher.PublishedEvents);
}

// Technology-specific adapter testing
[Fact]
public async Task SqlUserRepository_SaveUser_WithSqlModels()
{
    // Arrange
    using var context = CreateTestDbContext();
    var repository = new SqlUserRepository(context);
    var user = User.Create(new Email("test@example.com"), "John");

    // Act
    await repository.SaveAsync(user);

    // Assert
    var savedUser = await repository.FindByEmailAsync(new Email("test@example.com"));
    Assert.NotNull(savedUser);
    Assert.Equal(user.Email, savedUser.Email);

    // Verify SQL model was created correctly
    var userModel = await context.Users.FirstOrDefaultAsync(u => u.Email == "test@example.com");
    Assert.NotNull(userModel);
    Assert.Equal("John", userModel.Name);
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

```csharp
// Driving Ports (Application Layer) - Application/Ports/Driving/
public interface ICreateUserPort
{
    Task<CreateUserResponse> ExecuteAsync(CreateUserCommand command, CancellationToken cancellationToken = default);
}

public interface IChangeUserEmailPort
{
    Task ExecuteAsync(ChangeEmailCommand command, CancellationToken cancellationToken = default);
}

// Domain-Driven Driven Ports (Domain Layer) - Domain/Repositories/
public interface IUserRepository
{
    // Already shown in rule 5
    Task<User?> FindByEmailAsync(Email email, CancellationToken cancellationToken = default);
}

// Domain Services (Domain Layer) - Domain/Services/
public interface IPricingServicePort
{
    Task<Money> CalculateProductPriceAsync(Product product, Customer customer, CancellationToken cancellationToken = default);
}

// Infrastructure Driven Ports (Application Layer) - Application/Ports/Driven/
public interface IEmailNotificationPort
{
    Task SendWelcomeEmailAsync(Email userEmail, string userName, CancellationToken cancellationToken = default);
    Task SendEmailChangeNotificationAsync(Email oldEmail, Email newEmail, DateTime timestamp, CancellationToken cancellationToken = default);
}

public interface IEventPublisherPort
{
    Task PublishAsync<T>(T domainEvent, CancellationToken cancellationToken = default) where T : IDomainEvent;
}

public interface ITimeProviderPort
{
    DateTime Now();
    DateTimeOffset UtcNow();
}

public interface IFileSystemPort
{
    Task<string> ReadAllTextAsync(string filePath, CancellationToken cancellationToken = default);
    Task WriteAllTextAsync(string filePath, string content, CancellationToken cancellationToken = default);
    Task<bool> ExistsAsync(string filePath, CancellationToken cancellationToken = default);
    Task DeleteAsync(string filePath, CancellationToken cancellationToken = default);
}

public interface IRandomNumberGeneratorPort
{
    int Next(int minValue, int maxValue);
    double NextDouble();
    Guid NextGuid();
}

public interface IExternalApiPort
{
    Task<TResponse> GetAsync<TResponse>(string endpoint, CancellationToken cancellationToken = default);
    Task<TResponse> PostAsync<TRequest, TResponse>(string endpoint, TRequest request, CancellationToken cancellationToken = default);
}

public interface IIdGeneratorPort
{
    Guid GenerateId();
    string GenerateStringId();
}
```

### 2. Driving Adapter Rules

- Driving adapters are the entry points (web controllers, CLI, message consumers)
- Should translate external requests to domain commands/queries
- Must not contain business logic - only translation and validation
- Should handle framework-specific concerns (HTTP status codes, serialization)
- Should be thin and delegate to use cases through driving ports

```csharp
// ASP.NET Core Controller (Driving Adapter)
using Microsoft.AspNetCore.Mvc;
using System.ComponentModel.DataAnnotations;

public record CreateUserRequest(
    [Required] [EmailAddress] string Email,
    [Required] [StringLength(100, MinimumLength = 1)] string Name);

public record ChangeEmailRequest(
    [Required] [EmailAddress] string Email);

public record CreateUserResponse(string UserId);

[ApiController]
[Route("api/[controller]")]
public class UserController : ControllerBase
{
    private readonly ICreateUserPort _createUserUseCase;
    private readonly IChangeUserEmailPort _changeEmailUseCase;

    public UserController(
        ICreateUserPort createUserUseCase,
        IChangeUserEmailPort changeEmailUseCase)
    {
        _createUserUseCase = createUserUseCase;
        _changeEmailUseCase = changeEmailUseCase;
    }

    [HttpPost]
    public async Task<ActionResult<CreateUserResponse>> CreateUserAsync(
        [FromBody] CreateUserRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var command = new CreateUserCommand(request.Email, request.Name);
            var response = await _createUserUseCase.ExecuteAsync(command, cancellationToken);
            return CreatedAtAction(nameof(GetUser), new { userId = response.UserId }, response);
        }
        catch (InvalidEmailException ex)
        {
            return BadRequest($"Invalid email: {ex.Message}");
        }
        catch (UserAlreadyExistsException ex)
        {
            return Conflict(ex.Message);
        }
        catch (DomainException ex)
        {
            return BadRequest(ex.Message);
        }
        catch (Exception)
        {
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPatch("{userId}/email")]
    public async Task<IActionResult> ChangeUserEmailAsync(
        Guid userId,
        [FromBody] ChangeEmailRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var command = new ChangeEmailCommand(new UserId(userId), request.Email);
            await _changeEmailUseCase.ExecuteAsync(command, cancellationToken);
            return NoContent();
        }
        catch (UserNotFoundException)
        {
            return NotFound("User not found");
        }
        catch (InvalidEmailException ex)
        {
            return BadRequest($"Invalid email: {ex.Message}");
        }
        catch (DomainException ex)
        {
            return BadRequest(ex.Message);
        }
        catch (Exception)
        {
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{userId}")]
    public async Task<ActionResult<UserResponse>> GetUser(Guid userId)
    {
        // Implementation would query user
        throw new NotImplementedException();
    }
}

// CLI Adapter
public class CliUserAdapter
{
    private readonly ICreateUserPort _createUserUseCase;

    public CliUserAdapter(ICreateUserPort createUserUseCase)
    {
        _createUserUseCase = createUserUseCase;
    }

    public async Task<int> CreateUserAsync(string[] args)
    {
        if (args.Length != 2)
        {
            Console.WriteLine("Usage: create-user <email> <name>");
            return 1;
        }

        try
        {
            var command = new CreateUserCommand(args[0], args[1]);
            var response = await _createUserUseCase.ExecuteAsync(command);
            Console.WriteLine($"User created with ID: {response.UserId}");
            return 0;
        }
        catch (DomainException ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            return 1;
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

```csharp
// SQL Database Adapter - Infrastructure/Adapters/Driven/Sql/SqlUserRepository.cs
using Microsoft.EntityFrameworkCore;

public class UserEntity
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public int Version { get; set; }
}

public class SqlUserRepository : IUserRepository
{
    private readonly ApplicationDbContext _context;

    public SqlUserRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task SaveAsync(User user, CancellationToken cancellationToken = default)
    {
        var userEntity = new UserEntity
        {
            Id = user.Id.Value,
            Email = user.Email.Value,
            Name = user.Name,
            Version = user.Version
        };

        var existing = await _context.Users.FindAsync(new object[] { user.Id.Value }, cancellationToken);
        if (existing is null)
        {
            _context.Users.Add(userEntity);
        }
        else
        {
            _context.Entry(existing).CurrentValues.SetValues(userEntity);
        }

        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task<User?> FindByEmailAsync(Email email, CancellationToken cancellationToken = default)
    {
        var userEntity = await _context.Users
            .FirstOrDefaultAsync(u => u.Email == email.Value, cancellationToken);
        return userEntity is not null ? ToDomain(userEntity) : null;
    }

    public async Task<User?> FindByIdAsync(UserId userId, CancellationToken cancellationToken = default)
    {
        var userEntity = await _context.Users.FindAsync(new object[] { userId.Value }, cancellationToken);
        return userEntity is not null ? ToDomain(userEntity) : null;
    }

    public async Task<IReadOnlyList<User>> FindActiveUsersInDepartmentAsync(
        DepartmentId departmentId,
        CancellationToken cancellationToken = default)
    {
        // Implementation would include proper SQL query with joins
        var userEntities = await _context.Users.ToListAsync(cancellationToken);
        return userEntities.Select(ToDomain).ToList();
    }

    private static User ToDomain(UserEntity entity)
    {
        return new User(new UserId(entity.Id), new Email(entity.Email), entity.Name);
    }
}

// HTTP External Service Adapter - Infrastructure/Adapters/Driven/Http/HttpEmailNotificationAdapter.cs
using System.Text.Json;

public record EmailApiConfig(string BaseUrl, string ApiKey);

public record EmailPayload(string To, string Template, Dictionary<string, object> Variables);

public class HttpEmailNotificationAdapter : IEmailNotificationPort
{
    private readonly HttpClient _httpClient;
    private readonly EmailApiConfig _config;

    public HttpEmailNotificationAdapter(HttpClient httpClient, EmailApiConfig config)
    {
        _httpClient = httpClient;
        _config = config;
        _httpClient.BaseAddress = new Uri(config.BaseUrl);
        _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {config.ApiKey}");
    }

    public async Task SendWelcomeEmailAsync(
        Email userEmail,
        string userName,
        CancellationToken cancellationToken = default)
    {
        var payload = new EmailPayload(
            userEmail.Value,
            "welcome",
            new Dictionary<string, object> { ["name"] = userName });

        await SendEmailAsync(payload, cancellationToken);
    }

    public async Task SendEmailChangeNotificationAsync(
        Email oldEmail,
        Email newEmail,
        DateTime timestamp,
        CancellationToken cancellationToken = default)
    {
        var payload = new EmailPayload(
            newEmail.Value,
            "email-changed",
            new Dictionary<string, object>
            {
                ["oldEmail"] = oldEmail.Value,
                ["newEmail"] = newEmail.Value,
                ["timestamp"] = timestamp.ToString("O")
            });

        await SendEmailAsync(payload, cancellationToken);
    }

    private async Task SendEmailAsync(EmailPayload payload, CancellationToken cancellationToken = default)
    {
        try
        {
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync("/send", content, cancellationToken);
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
                throw new EmailDeliveryException($"Failed to send email: {response.StatusCode} - {errorContent}");
            }
        }
        catch (HttpRequestException ex)
        {
            throw new EmailDeliveryException($"Failed to send email: {ex.Message}", ex);
        }
        catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
        {
            throw new EmailDeliveryException("Email service timeout", ex);
        }
    }
}

// File System Adapter - Infrastructure/Adapters/Driven/FileSystem/LocalFileSystemAdapter.cs
public class LocalFileSystemAdapter : IFileSystemPort
{
    public async Task<string> ReadAllTextAsync(string filePath, CancellationToken cancellationToken = default)
    {
        try
        {
            return await File.ReadAllTextAsync(filePath, cancellationToken);
        }
        catch (FileNotFoundException ex)
        {
            throw new FileSystemException($"File not found: {filePath}", ex);
        }
        catch (DirectoryNotFoundException ex)
        {
            throw new FileSystemException($"Directory not found for file: {filePath}", ex);
        }
        catch (UnauthorizedAccessException ex)
        {
            throw new FileSystemException($"Access denied to file: {filePath}", ex);
        }
    }

    public async Task WriteAllTextAsync(string filePath, string content, CancellationToken cancellationToken = default)
    {
        try
        {
            var directory = Path.GetDirectoryName(filePath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            await File.WriteAllTextAsync(filePath, content, cancellationToken);
        }
        catch (UnauthorizedAccessException ex)
        {
            throw new FileSystemException($"Access denied when writing to file: {filePath}", ex);
        }
        catch (DirectoryNotFoundException ex)
        {
            throw new FileSystemException($"Directory not found for file: {filePath}", ex);
        }
    }

    public Task<bool> ExistsAsync(string filePath, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(File.Exists(filePath));
    }

    public Task DeleteAsync(string filePath, CancellationToken cancellationToken = default)
    {
        try
        {
            if (File.Exists(filePath))
            {
                File.Delete(filePath);
            }
            return Task.CompletedTask;
        }
        catch (UnauthorizedAccessException ex)
        {
            throw new FileSystemException($"Access denied when deleting file: {filePath}", ex);
        }
        catch (IOException ex)
        {
            throw new FileSystemException($"IO error when deleting file: {filePath}", ex);
        }
    }
}

// Time Provider Adapter - Infrastructure/Adapters/Driven/Time/SystemTimeProviderAdapter.cs
public class SystemTimeProviderAdapter : ITimeProviderPort
{
    public DateTime Now() => DateTime.Now;
    public DateTimeOffset UtcNow() => DateTimeOffset.UtcNow;
}

// Random Number Generator Adapter - Infrastructure/Adapters/Driven/Random/SystemRandomAdapter.cs
public class SystemRandomAdapter : IRandomNumberGeneratorPort
{
    private readonly Random _random = new();

    public int Next(int minValue, int maxValue) => _random.Next(minValue, maxValue);
    public double NextDouble() => _random.NextDouble();
    public Guid NextGuid() => Guid.NewGuid();
}

// ID Generator Adapter - Infrastructure/Adapters/Driven/Id/GuidIdGeneratorAdapter.cs
public class GuidIdGeneratorAdapter : IIdGeneratorPort
{
    public Guid GenerateId() => Guid.NewGuid();
    public string GenerateStringId() => Guid.NewGuid().ToString();
}

// External API Adapter - Infrastructure/Adapters/Driven/Http/HttpExternalApiAdapter.cs
public class HttpExternalApiAdapter : IExternalApiPort
{
    private readonly HttpClient _httpClient;

    public HttpExternalApiAdapter(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<TResponse> GetAsync<TResponse>(string endpoint, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetAsync(endpoint, cancellationToken);
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync(cancellationToken);
            var result = JsonSerializer.Deserialize<TResponse>(json, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            return result ?? throw new ExternalApiException($"Failed to deserialize response from {endpoint}");
        }
        catch (HttpRequestException ex)
        {
            throw new ExternalApiException($"HTTP error calling {endpoint}: {ex.Message}", ex);
        }
        catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
        {
            throw new ExternalApiException($"Timeout calling {endpoint}", ex);
        }
        catch (JsonException ex)
        {
            throw new ExternalApiException($"Failed to deserialize response from {endpoint}: {ex.Message}", ex);
        }
    }

    public async Task<TResponse> PostAsync<TRequest, TResponse>(string endpoint, TRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync(endpoint, content, cancellationToken);
            response.EnsureSuccessStatusCode();

            var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
            var result = JsonSerializer.Deserialize<TResponse>(responseJson, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            return result ?? throw new ExternalApiException($"Failed to deserialize response from {endpoint}");
        }
        catch (HttpRequestException ex)
        {
            throw new ExternalApiException($"HTTP error calling {endpoint}: {ex.Message}", ex);
        }
        catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
        {
            throw new ExternalApiException($"Timeout calling {endpoint}", ex);
        }
        catch (JsonException ex)
        {
            throw new ExternalApiException($"Failed to serialize request or deserialize response for {endpoint}: {ex.Message}", ex);
        }
    }
}

// Event Publisher Adapter using MassTransit - Infrastructure/Adapters/Driven/Messaging/MassTransitEventPublisherAdapter.cs
using MassTransit;

public class MassTransitEventPublisherAdapter : IEventPublisherPort
{
    private readonly IPublishEndpoint _publishEndpoint;

    public MassTransitEventPublisherAdapter(IPublishEndpoint publishEndpoint)
    {
        _publishEndpoint = publishEndpoint;
    }

    public async Task PublishAsync<T>(T domainEvent, CancellationToken cancellationToken = default) where T : IDomainEvent
    {
        try
        {
            await _publishEndpoint.Publish(domainEvent, cancellationToken);
        }
        catch (Exception ex)
        {
            throw new EventPublishingException($"Failed to publish event of type {typeof(T).Name}", ex);
        }
    }
}

// Exception classes for infrastructure concerns
public class EmailDeliveryException : Exception
{
    public EmailDeliveryException(string message) : base(message) { }
    public EmailDeliveryException(string message, Exception innerException) : base(message, innerException) { }
}

public class FileSystemException : Exception
{
    public FileSystemException(string message) : base(message) { }
    public FileSystemException(string message, Exception innerException) : base(message, innerException) { }
}

public class ExternalApiException : Exception
{
    public ExternalApiException(string message) : base(message) { }
    public ExternalApiException(string message, Exception innerException) : base(message, innerException) { }
}

public class EventPublishingException : Exception
{
    public EventPublishingException(string message) : base(message) { }
    public EventPublishingException(string message, Exception innerException) : base(message, innerException) { }
}
```

### 4. Dependency Injection and Startup Configuration

Use Microsoft.Extensions.DependencyInjection for proper dependency injection setup:

```csharp
// Infrastructure/DependencyInjection/ServiceCollectionExtensions.cs
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddDomainServices(this IServiceCollection services)
    {
        services.AddScoped<UserDomainService>();
        services.AddScoped<PricingService>();
        return services;
    }

    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        // Use cases
        services.AddScoped<ICreateUserPort, CreateUserUseCase>();
        services.AddScoped<IChangeUserEmailPort, ChangeUserEmailUseCase>();

        return services;
    }

    public static IServiceCollection AddInfrastructureServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // Database
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("DefaultConnection")));

        // Repository implementations
        services.AddScoped<IUserRepository, SqlUserRepository>();

        // Infrastructure ports
        services.AddScoped<IEmailNotificationPort, HttpEmailNotificationAdapter>();
        services.AddScoped<IFileSystemPort, LocalFileSystemAdapter>();
        services.AddSingleton<ITimeProviderPort, SystemTimeProviderAdapter>();
        services.AddSingleton<IRandomNumberGeneratorPort, SystemRandomAdapter>();
        services.AddSingleton<IIdGeneratorPort, GuidIdGeneratorAdapter>();

        // HTTP clients
        services.AddHttpClient<HttpEmailNotificationAdapter>(client =>
        {
            var config = configuration.GetSection("EmailApi").Get<EmailApiConfig>()!;
            client.BaseAddress = new Uri(config.BaseUrl);
        });

        services.AddHttpClient<HttpExternalApiAdapter>();

        // Event publishing
        services.AddMassTransit(x =>
        {
            x.UsingRabbitMq((context, cfg) =>
            {
                cfg.Host(configuration.GetConnectionString("RabbitMq"));
                cfg.ConfigureEndpoints(context);
            });
        });
        services.AddScoped<IEventPublisherPort, MassTransitEventPublisherAdapter>();

        return services;
    }
}

// Program.cs for minimal API or Startup.cs for traditional setup
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add layers
builder.Services.AddDomainServices();
builder.Services.AddApplicationServices();
builder.Services.AddInfrastructureServices(builder.Configuration);

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.MapControllers();
app.Run();
```

These integrated rules ensure that Domain Driven Design and Ports & Adapters (Hexagonal Architecture) work together seamlessly in C# implementations. The combination provides clean separation of concerns, testability, and flexibility while maintaining domain focus and proper dependency management using modern C# patterns and conventions.
