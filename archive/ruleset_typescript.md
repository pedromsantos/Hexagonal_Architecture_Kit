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

```typescript
// 1. Domain Layer (DDD Core)
class User extends Entity {
  // Rule 1: Entity with identity
  changeEmail(email: Email): UserEmailChanged {
    // Business logic here
    return new UserEmailChanged(this.id, this.email, email);
  }
}

interface UserRepository {
  // Rule 5: Domain port for persistence
  save(user: User): Promise<void>;
}

// 2. Application Layer (Bridge between DDD and Ports & Adapters)
class ChangeUserEmailUseCase implements ChangeUserEmailPort {
  // Rule 9 + P&A Rule 1
  constructor(
    private readonly userRepo: UserRepository, // Domain port
    private readonly emailService: EmailNotificationPort, // Infrastructure port
    private readonly timeProvider: TimeProviderPort // Infrastructure port
  ) {}

  async execute(command: ChangeEmailCommand): Promise<void> {
    // Orchestrate domain objects (Rule 9)
    const user = await this.userRepo.findById(command.userId);
    const event = user.changeEmail(new Email(command.newEmail));

    // Use infrastructure ports for side effects
    await this.userRepo.save(user);
    await this.emailService.sendEmailChangeNotification(
      event.oldEmail,
      event.newEmail,
      this.timeProvider.now()
    );
  }
}

// 3. Infrastructure Layer (Ports & Adapters Implementation)
class SqlUserRepository implements UserRepository {
  // P&A Rule 3: Driven adapter
  async save(user: User): Promise<void> {
    // Handle ORM mapping, database specifics
  }
}

class RestUserController {
  // P&A Rule 2: Driving adapter
  patchUserEmail(userId: string, request: ChangeEmailRequest): Promise<void> {
    const command = new ChangeEmailCommand(userId, request.email);
    return this.useCase.execute(command); // Delegate to use case
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
- Implement `equality` and `hash` based solely on identity, not attributes/fields
- Entities MUST contain business logic as methods, not just data
  - Avoid anemic domain models - entities should have behavior
- Include validation in constructor

```typescript
class User extends Entity<UserId> {
  private _email: Email;
  private _name: string;

  constructor(id: UserId, email: Email, name: string) {
    super(id);
    this._email = email;
    this._name = name;
    this.validate();
  }

  static create(email: Email, name: string): User {
    return new User(UserId.generate(), email, name);
  }

  changeEmail(newEmail: Email): void {
    // Business logic here
    this._email = newEmail;
  }

  get email(): Email {
    return this._email;
  }

  get name(): string {
    return this._name;
  }

  private validate(): void {
    if (!this._email || !this._name) {
      throw new Error('User must have email and name');
    }
  }
}

abstract class Entity<T> {
  protected readonly _id: T;

  constructor(id: T) {
    this._id = id;
  }

  get id(): T {
    return this._id;
  }

  equals(other: Entity<T>): boolean {
    return this._id === other._id;
  }
}
```

### 2. Value Object Rules

- Value objects MUST be immutable
- Equality is based on ALL attributes, not identity
- Should be small, focused, and represent a concept from the domain
- Include validation in constructor
- Should have meaningful methods that operate on the value

```typescript
class Email {
  private readonly _value: string;

  constructor(value: string) {
    if (!value.includes('@')) {
      throw new Error('Invalid email format');
    }
    this._value = value;
  }

  get value(): string {
    return this._value;
  }

  get domain(): string {
    return this._value.split('@')[1];
  }

  equals(other: Email): boolean {
    return this._value === other._value;
  }

  toString(): string {
    return this._value;
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
- Encapsulate Collections: Use first class collection from Object Calisthenics

```typescript
class Order extends Entity<OrderId> {
  // Aggregate Root
  private readonly _customerId: CustomerId;
  private readonly _lineItems: OrderLineItem[] = [];

  constructor(id: OrderId, customerId: CustomerId) {
    super(id);
    this._customerId = customerId;
  }

  addLineItem(productId: ProductId, quantity: number): void {
    // Business rules and validation
    const lineItem = new OrderLineItem(productId, quantity);
    this._lineItems.push(lineItem);
  }

  get lineItems(): readonly OrderLineItem[] {
    return Object.freeze([...this._lineItems]); // Return immutable view
  }

  get customerId(): CustomerId {
    return this._customerId;
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

```typescript
class PricingService {
  constructor(private readonly discountRepository: DiscountRepository) {}

  calculateOrderTotal(order: Order, customer: Customer): Money {
    // Complex pricing logic that spans multiple aggregates
    throw new Error('Not implemented');
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

```typescript
// Domain Layer - domain/repositories/UserRepository.ts
interface UserRepository {
  findByEmail(email: Email): Promise<User | null>;
  save(user: User): Promise<void>;
  findActiveUsersInDepartment(departmentId: DepartmentId): Promise<User[]>;
  findById(userId: UserId): Promise<User | null>;
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

```typescript
class UserEmailChanged {
  constructor(
    public readonly userId: UserId,
    public readonly oldEmail: Email,
    public readonly newEmail: Email,
    public readonly occurredAt: Date
  ) {}
}
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

````typescript
class CreateUserUseCase {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly unitOfWork: UnitOfWork,
    private readonly eventPublisher: EventPublisher
  ) {}

  async execute(command: CreateUserCommand): Promise<CreateUserResponse> {
    return await this.unitOfWork.execute(async () => {
      // Orchestration logic only
      const email = new Email(command.email);
      const user = User.create(email, command.name);
      await this.userRepository.save(user);
      await this.eventPublisher.publish(new UserCreated(user.id, email));
      return new CreateUserResponse(user.id.value);
    });
  }
}

class ChangeUserEmailUseCase {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly unitOfWork: UnitOfWork
  ) {}

  async execute(command: ChangeEmailCommand): Promise<void> {
    return await this.unitOfWork.execute(async () => {
      const user = await this.userRepository.findById(command.userId);
      if (!user) {
        throw new UserNotFoundError(command.userId);
      }
      user.changeEmail(new Email(command.newEmail));
      await this.userRepository.save(user);
    });
  }
}

### 10. Event Integration Rules

- Domain events should be published through infrastructure ports
- Event handlers can be implemented as separate use cases
- Use event-driven architecture for cross-bounded context communication
- Events enable loose coupling between adapters and domain logic
- Consider eventual consistency for distributed operations

```typescript
// Event Publishing through Infrastructure Port
interface EventPublisherPort {  // Application layer
  publish(event: DomainEvent): Promise<void>;
}

class CreateUserUseCase implements CreateUserPort {
  constructor(
    private readonly userRepo: UserRepository,  // Domain port
    private readonly eventPublisher: EventPublisherPort  // Infrastructure port
  ) {}

  async execute(command: CreateUserCommand): Promise<CreateUserResponse> {
    const user = User.create(new Email(command.email), command.name);
    await this.userRepo.save(user);  // Domain port
    await this.eventPublisher.publish(new UserCreated(user.id, user.email));  // Infrastructure port
    return new CreateUserResponse(user.id.value);
  }
}

// Event Handler as Use Case
class SendWelcomeEmailUseCase {
  constructor(
    private readonly emailService: EmailNotificationPort  // Infrastructure port
  ) {}

  async handle(event: UserCreated): Promise<void> {
    await this.emailService.sendWelcomeEmail(event.email, event.name);
  }
}
````

## Validation and Error Handling Rules

- Test domain logic in isolation without any adapters
- Test driving adapters by mocking driving ports
- Test driven adapters by mocking external dependencies
- Use in-memory implementations of driven ports for integration tests
- Test the full flow from driving adapter to driven adapter for end-to-end tests

```typescript
// Testing with port isolation
describe('UserManagementService', () => {
  test('create user success', async () => {
    // Arrange
    const mockRepo = jest.createMockFromModule<UserRepository>('UserRepository');
    const mockEvents = jest.createMockFromModule<EventPublisherPort>('EventPublisherPort');
    const service = new UserManagementService(mockRepo, mockEvents);

    // Act
    const result = await service.createUser(new CreateUserCommand('test@example.com', 'John'));

    // Assert
    expect(mockRepo.save).toHaveBeenCalledTimes(1);
    expect(mockEvents.publish).toHaveBeenCalledTimes(1);
    expect(typeof result.userId).toBe('string');
  });
});

// In-memory adapter for testing
class InMemoryUserRepository implements UserRepository {
  private users: Map<string, User> = new Map();

  async save(user: User): Promise<void> {
    this.users.set(user.id.value, user);
  }

  async findByEmail(email: Email): Promise<User | null> {
    return Array.from(this.users.values()).find((u) => u.email.equals(email)) || null;
  }

  async findById(userId: UserId): Promise<User | null> {
    return this.users.get(userId.value) || null;
  }

  async findActiveUsersInDepartment(departmentId: DepartmentId): Promise<User[]> {
    return [];
  }
}
```

### 11. Validation and Error Handling Rules

- Domain validation should happen in domain objects (entities, value objects)
- Use domain exceptions that extend a base domain exception
- Validation should be explicit and fail fast
- Input validation in application services should be minimal
- Use factory methods for complex validation scenarios

```typescript
class DomainException extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

class InvalidEmailError extends DomainException {
  constructor(email: string) {
    super(`Invalid email: ${email}`);
  }
}

class Email {
  private readonly _value: string;

  constructor(value: string) {
    if (!this.isValidEmail(value)) {
      throw new InvalidEmailError(value);
    }
    this._value = value;
  }

  private isValidEmail(value: string): boolean {
    return value.includes('@');
  }

  get value(): string {
    return this._value;
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

```typescript
// Good port names
interface UserManagementPort {} // Driving port
interface EmailNotificationPort {} // Driven port
interface PaymentProcessingPort {} // Driven port

// Good adapter names
class RestUserController {} // Driving adapter (REST)
class GraphQLUserController {} // Driving adapter (GraphQL)
class SqlUserRepository implements UserRepository {} // Driven adapter (SQL)
class MongoUserRepository implements UserRepository {} // Driven adapter (MongoDB)
class SmtpEmailAdapter implements EmailNotificationPort {} // Driven adapter (SMTP)
class SendGridEmailAdapter implements EmailNotificationPort {} // Driven adapter (SendGrid)
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

```typescript
// Domain layer - can depend on domain ports
class User {
  // Domain entity
  constructor(private readonly id: UserId, private email: Email, private name: string) {}

  changeEmail(newEmail: Email): void {
    // Business logic here
    this.email = newEmail;
  }
}

class UserDomainService {
  // Domain service
  constructor(
    private readonly userRepo: UserRepository // Domain port dependency
  ) {}

  async isEmailUnique(email: Email): Promise<boolean> {
    const existingUser = await this.userRepo.findByEmail(email);
    return existingUser === null;
  }
}

// Application layer - depends on domain + infrastructure ports
class CreateUserUseCase implements CreateUserPort {
  constructor(
    private readonly userRepo: UserRepository, // Domain port
    private readonly userDomainService: UserDomainService, // Domain service
    private readonly emailService: EmailNotificationPort, // Infrastructure port
    private readonly eventPublisher: EventPublisherPort // Infrastructure port
  ) {}
}

// Infrastructure layer - implements ports with external dependencies
class SqlUserRepository implements UserRepository {
  // Implements domain port
  constructor(
    private readonly connection: DatabaseConnection // External dependency
  ) {}
}

class SmtpEmailAdapter implements EmailNotificationPort {
  // Implements infrastructure port
  constructor(
    private readonly smtpClient: SMTPClient // External dependency
  ) {}
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

```typescript
// Contract test for all UserRepository implementations
describe('UserRepository Contract', () => {
  test.each([
    ['SqlUserRepository', new SqlUserRepository(mockConnection)],
    ['MongoUserRepository', new MongoUserRepository(mockClient)],
  ])('%s should save and find user', async (name, repository: UserRepository) => {
    // This test should pass for all UserRepository implementations
    const user = User.create(new Email('test@example.com'), 'John');
    await repository.save(user);
    const found = await repository.findByEmail(new Email('test@example.com'));
    expect(found).not.toBeNull();
    expect(found!.email.equals(user.email)).toBe(true);
  });
});

// Use Case Integration Test
describe('CreateUserUseCase Integration', () => {
  test('full workflow with in-memory adapters', async () => {
    // Arrange
    const userRepo = new InMemoryUserRepository();
    const emailService = new InMemoryEmailService();
    const eventPublisher = new InMemoryEventPublisher();
    const useCase = new CreateUserUseCase(userRepo, emailService, eventPublisher);

    // Act
    const result = await useCase.execute(new CreateUserCommand('test@example.com', 'John'));

    // Assert
    expect(result.userId).toBeDefined();
    const savedUser = await userRepo.findByEmail(new Email('test@example.com'));
    expect(savedUser).not.toBeNull();
    expect(emailService.sentEmails.length).toBe(1);
    expect(eventPublisher.publishedEvents.length).toBe(1);
  });
});

// Technology-specific adapter testing
describe('SqlUserRepository', () => {
  test('save user with SQL models', async () => {
    // Arrange
    const connection = createTestSqlConnection();
    const repository = new SqlUserRepository(connection);
    const user = User.create(new Email('test@example.com'), 'John');

    // Act
    await repository.save(user);

    // Assert
    const savedUser = await repository.findByEmail(new Email('test@example.com'));
    expect(savedUser).not.toBeNull();
    expect(savedUser!.email.equals(user.email)).toBe(true);

    // Verify SQL model was created correctly
    const userModel = await connection.query('SELECT * FROM users WHERE email = ?', [
      'test@example.com',
    ]);
    expect(userModel).toBeDefined();
    expect(userModel.name).toBe('John');
  });
});
```

## Ports & Adapters (Hexagonal Architecture) Rules

### 1. Port Definition Rules

- Ports define interfaces between layers and external systems
- **Driving ports** (primary/left-side) define application use cases - belong in application layer
- **Domain-driven driven ports** (repositories, domain services) - belong in domain layer
- **Infrastructure driven ports** (email, messaging, external APIs) - belong in application layer
- Port interfaces should use domain language, not technical terms
- Ports should be focused and follow Single Responsibility Principle

```typescript
// Driving Ports (Application Layer) - application/ports/driving/
interface CreateUserPort {
  execute(command: CreateUserCommand): Promise<CreateUserResponse>;
}

interface ChangeUserEmailPort {
  execute(command: ChangeEmailCommand): Promise<void>;
}

// Domain-Driven Driven Ports (Domain Layer) - domain/repositories/
interface UserRepository {
  // Already shown in rule 5
  findByEmail(email: Email): Promise<User | null>;
}

// Domain Services (Domain Layer) - domain/services/
interface PricingServicePort {
  calculateProductPrice(product: Product, customer: Customer): Promise<Money>;
}

// Infrastructure Driven Ports (Application Layer) - application/ports/driven/
interface EmailNotificationPort {
  sendWelcomeEmail(userEmail: Email, userName: string): Promise<void>;
  sendEmailChangeNotification(oldEmail: Email, newEmail: Email): Promise<void>;
}

interface EventPublisherPort {
  publish(event: DomainEvent): Promise<void>;
}
```

### 2. Driving Adapter Rules

- Driving adapters are the entry points (web controllers, CLI, message consumers)
- Should translate external requests to domain commands/queries
- Must not contain business logic - only translation and validation
- Should handle framework-specific concerns (HTTP status codes, serialization)
- Should be thin and delegate to use cases through driving ports

```typescript
// Express.js Controller (Driving Adapter)
import { Request, Response } from 'express';
import { body, validationResult } from 'express-validator';

interface CreateUserRequest {
  email: string;
  name: string;
}

interface ChangeEmailRequest {
  email: string;
}

interface CreateUserResponse {
  userId: string;
}

class RestUserController {
  constructor(
    private readonly createUserUseCase: CreateUserPort,
    private readonly changeEmailUseCase: ChangeUserEmailPort
  ) {}

  async createUser(req: Request, res: Response): Promise<void> {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        res.status(400).json({ errors: errors.array() });
        return;
      }

      const request = req.body as CreateUserRequest;
      const command = new CreateUserCommand(request.email, request.name);
      const response = await this.createUserUseCase.execute(command);

      res.status(201).json({ userId: response.userId });
    } catch (error) {
      if (error instanceof InvalidEmailError) {
        res.status(400).json({ error: `Invalid email: ${error.message}` });
      } else if (error instanceof UserAlreadyExistsError) {
        res.status(409).json({ error: error.message });
      } else if (error instanceof DomainException) {
        res.status(400).json({ error: error.message });
      } else {
        res.status(500).json({ error: 'Internal server error' });
      }
    }
  }

  async changeUserEmail(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.params.userId;
      const request = req.body as ChangeEmailRequest;
      const command = new ChangeEmailCommand(new UserId(userId), request.email);

      await this.changeEmailUseCase.execute(command);
      res.status(204).send();
    } catch (error) {
      if (error instanceof UserNotFoundError) {
        res.status(404).json({ error: 'User not found' });
      } else if (error instanceof InvalidEmailError) {
        res.status(400).json({ error: `Invalid email: ${error.message}` });
      } else if (error instanceof DomainException) {
        res.status(400).json({ error: error.message });
      } else {
        res.status(500).json({ error: 'Internal server error' });
      }
    }
  }
}

// Validation middleware
export const createUserValidation = [
  body('email').isEmail().withMessage('Must be a valid email'),
  body('name').trim().isLength({ min: 1 }).withMessage('Name is required'),
];
```

### 3. Driven Adapter Rules

- Driven adapters implement driven ports defined in domain/application layers
- Organize driven adapters by technology for shared infrastructure and easier maintenance
- Should handle all external system complexities (database mapping, API calls, etc.)
- Must translate between domain objects and external representations
- Should not expose external system details to the domain
- Include error handling and retry logic when appropriate
- Keep technology-specific models/schemas within their adapter implementations

```typescript
// SQL Database Adapter - infrastructure/adapters/driven/sql/SqlUserRepository.ts
import { Repository } from 'typeorm';

interface UserModel {
  id: string;
  email: string;
  name: string;
  version: number;
}

class SqlUserRepository implements UserRepository {
  constructor(private readonly repository: Repository<UserModel>) {}

  async save(user: User): Promise<void> {
    const userModel: UserModel = {
      id: user.id.value,
      email: user.email.value,
      name: user.name,
      version: user.version,
    };
    await this.repository.save(userModel);
  }

  async findByEmail(email: Email): Promise<User | null> {
    const model = await this.repository.findOne({ where: { email: email.value } });
    return model ? this.toDomain(model) : null;
  }

  async findById(userId: UserId): Promise<User | null> {
    const model = await this.repository.findOne({ where: { id: userId.value } });
    return model ? this.toDomain(model) : null;
  }

  async findActiveUsersInDepartment(departmentId: DepartmentId): Promise<User[]> {
    // Implementation would include proper SQL query
    return [];
  }

  private toDomain(model: UserModel): User {
    return new User(new UserId(model.id), new Email(model.email), model.name);
  }
}

// HTTP External Service Adapter - infrastructure/adapters/driven/http/HttpEmailService.ts
import axios, { AxiosInstance } from 'axios';

interface EmailAPIConfig {
  baseUrl: string;
  apiKey: string;
}

class HttpEmailNotificationAdapter implements EmailNotificationPort {
  private readonly httpClient: AxiosInstance;

  constructor(private readonly apiConfig: EmailAPIConfig) {
    this.httpClient = axios.create({
      baseURL: apiConfig.baseUrl,
      headers: { Authorization: `Bearer ${apiConfig.apiKey}` },
    });
  }

  async sendWelcomeEmail(userEmail: Email, userName: string): Promise<void> {
    const payload = {
      to: userEmail.value,
      template: 'welcome',
      variables: { name: userName },
    };

    try {
      const response = await this.httpClient.post('/send', payload);
      if (response.status !== 200) {
        throw new EmailDeliveryError(`Failed to send email: ${response.statusText}`);
      }
    } catch (error) {
      throw new EmailDeliveryError(`Failed to send email: ${error}`);
    }
  }

  async sendEmailChangeNotification(oldEmail: Email, newEmail: Email): Promise<void> {
    const payload = {
      to: newEmail.value,
      template: 'email-changed',
      variables: { oldEmail: oldEmail.value, newEmail: newEmail.value },
    };

    try {
      await this.httpClient.post('/send', payload);
    } catch (error) {
      throw new EmailDeliveryError(`Failed to send email change notification: ${error}`);
    }
  }
}
```

These integrated rules ensure that Domain Driven Design and Ports & Adapters (Hexagonal Architecture) work together seamlessly in TypeScript implementations. The combination provides clean separation of concerns, testability, and flexibility while maintaining domain focus and proper dependency management.
