# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

[Describe your project here]

## Architecture Rules

This project follows Domain Driven Design (DDD) with Ports & Adapters (Hexagonal Architecture).

**IMPORTANT:** Before implementing any domain objects, use cases, or adapters, you MUST read and follow the complete implementation rules in [RULES.md](RULES.md). This file contains:

- Detailed rules for Entities, Value Objects, Aggregates, Domain Services
- Repository pattern implementation guidelines
- Domain Event patterns
- Use Case (Application Service) rules
- Ports & Adapters (Hexagonal Architecture) rules
- Complete code examples in multiple languages

Whenever you are implementing domain logic, creating repositories, or building adapters, refer to RULES.md for the specific patterns and rules.

### Key Principles (Summary)

- Entities contain business behavior and have unique identity
- Value Objects are immutable domain concepts
- Aggregates enforce business invariants and transaction boundaries
- Use Cases orchestrate domain objects without containing business logic
- Repositories have a 1:1 relationship with aggregate roots
- Dependency flow: External → Driving Adapter → Use Case → Domain → Driven Port → Driven Adapter

For detailed rules and code examples, see [RULES.md](RULES.md).

## TDD & Development Methodology

### Core Development Principles

I follow **Pedro's Algorithm (London School TDD)** as documented in the RULES.md precisely:

- **Outside-In TDD**: Start with acceptance test, work inside-out with unit tests
- Always follow the complete TDD cycle: **Acceptance (RED) → Unit Tests → Integration → Contract → E2E**
- Write failing tests first that define the complete behavior
- Follow London School approach with mocking for driven ports
- Implement domain behavior first, then orchestration, then adapters
- Maintain clean separation between layers throughout development

### Pedro's Algorithm Implementation

Follow this exact sequence for each user story:

1. **ACCEPTANCE TEST (RED)**: Write failing acceptance test covering complete business flow
2. **UNIT TEST CYCLE**: While acceptance test is failing, write unit tests for each component
3. **INTEGRATION TESTS**: Test driven adapter implementations with real external systems
4. **CONTRACT TESTS**: Test driving adapters (HTTP controllers) for API contract compliance
5. **E2E TESTS (Optional)**: Test complete system with real transport and infrastructure

### Critical Test Distinctions

**ACCEPTANCE TESTS** must cover **complete business flows**, not single operations:

- ❌ **Wrong**: Testing single use case execution with mocks (this is a unit test)
- ✅ **Right**: Testing complete user journey with multiple API calls representing real user behavior
- Example: Start game → Player created → Location assigned → Can view description → Ready to play

**Test Boundaries and Responsibilities**:

- **Unit Tests**: Single class/module, mock external dependencies, test domain behavior
- **Integration Tests**: Adapter to external system, no mocks in boundary, test data transformation
- **Contract Tests**: HTTP to use case, verify API contracts (status codes, headers, validation)
- **Acceptance Tests**: Complete business flow, multiple operations, real user journey
- **E2E Tests**: Full system, HTTP to database, test complete user workflows

### London School TDD Principles

- **Start with Acceptance Test**: Define complete user behavior before implementation
- **Mock ONLY Adapters**: Mock driven ports (repositories, APIs) in unit tests - NEVER mock domain entities
- **Use Real Domain Objects**: Always use real entities, value objects, and aggregates in tests
- **Test Real Adapters**: Use real implementations in integration tests
- **Outside-In Flow**: Work from external interface down to domain objects
- **Behavior Focus**: Test what the system does, not how it does it
- **Commit on Green**: Make small, frequent commits when tests pass
- **Layer Separation**: Test each architectural layer with appropriate boundaries

### Common Testing Mistakes to Avoid

- **Calling Unit Tests "Acceptance Tests"**: If it mocks domain dependencies, it's a unit test
- **Testing Single Operations as Full Flows**: Acceptance tests need multiple steps
- **Mocking Domain Entities**: NEVER mock `User`, `Order`, `Location` - use real domain objects
- **Mocking Value Objects**: NEVER mock `Email`, `Sid`, `Money` - create real instances
- **Over-mocking in Unit Tests**: Only mock adapters (driven ports), never domain objects
- **Mixing Test Types**: Each test type has specific boundaries and responsibilities
- **Over-mocking in Integration Tests**: Integration tests should use real external systems
- **Under-testing Business Flows**: Focus on complete user journeys, not just technical integration

### What to Mock vs What to Use Real

**ALWAYS MOCK** (Driven Ports/Adapters):

- `UserRepository`, `OrderRepository` interfaces
- `EmailService`, `PaymentGateway` interfaces
- `DatabaseConnection`, `HttpClient` interfaces
- External system adapters

**NEVER MOCK** (Domain Objects):

- `User`, `Order`, `Product` entities
- `Email`, `Money`, `Sid` value objects
- `ShoppingCart`, `Invoice` aggregates
- Domain events and domain services

### Mock Verification Principle

**Only verify COMMANDS (methods that cause side effects), never verify QUERIES (methods that return data):**

**ALWAYS VERIFY** (Commands - Side Effects):

```python
# ✅ Verify commands that cause state changes
mock_player_repo.save.assert_called_once()
mock_email_service.send.assert_called_once()
mock_payment_gateway.charge.assert_called_once()
```

**NEVER VERIFY** (Queries - Data Retrieval):

```python
# ❌ Do NOT verify queries - this makes tests brittle
mock_world_repo.find_starting_location.assert_called_once()  # Wrong!
mock_user_repo.find_by_id.assert_called_once()              # Wrong!
mock_config.get_setting.assert_called_once()                # Wrong!
```

**Why this matters:**

- **Queries are implementation details** - how data is retrieved shouldn't matter to the test
- **Commands are behaviors** - side effects must happen for the system to work correctly
- **Brittle tests** - verifying queries makes tests break when you refactor data access
- **Focus on outcomes** - test what the system does, not how it gets information

**Query verification is redundant** - if the system works correctly, the query must have been called.

### External ID Generation Principle

**IDs/SIDs should be generated OUTSIDE the application**, not by domain objects:

- ❌ **Wrong**: `player_sid = Sid.generate()` inside use case or domain
- ✅ **Right**: SID provided by external caller (UI, API client, external system)

**Why this matters**:

- **Separation of Concerns**: ID generation is an external system responsibility
- **Testability**: Tests can provide predictable IDs for assertions
- **Flexibility**: External systems can use their own ID generation strategies
- **Domain Focus**: Domain objects focus on business logic, not technical concerns

**Implementation**:

```python
# API receives both name and SID from external caller
class StartGameRequest(BaseModel):
    name: str
    sid: str  # Generated by external system

# Use case accepts the provided SID
command = StartGameCommand(player_name=request.name, player_sid=request.sid)
```

### Tidy First Approach

Separate all changes into two distinct types:

1. **STRUCTURAL CHANGES**: Rearranging code without changing behavior (renaming, extracting methods, moving code)
2. **BEHAVIORAL CHANGES**: Adding or modifying actual functionality

- Never mix structural and behavioral changes in the same commit
- Always make structural changes first when both are needed
- Validate structural changes do not alter behavior by running tests before and after

### Commit Discipline

Only commit when:

1. ALL tests are passing
2. ALL compiler/linter warnings have been resolved
3. The change represents a single logical unit of work
4. Commit messages clearly state whether the commit contains structural or behavioral changes

Use small, frequent commits rather than large, infrequent ones.

### Code Quality Standards

- Eliminate duplication ruthlessly
- Express intent clearly through naming and structure
- Make dependencies explicit
- Keep methods small and focused on a single responsibility
- Minimize state and side effects
- Use the simplest solution that could possibly work
- Use comments only as a last option if it's not possible to describe code behaviour using better names and abstractions

### Refactoring Guidelines

- Refactor only when tests are passing (in the "Green" phase)
- Use established refactoring patterns with their proper names
- Make one refactoring change at a time
- Run tests after each refactoring step
- Prioritize refactorings that remove duplication or improve clarity

### Development Workflow (Pedro's Algorithm)

When implementing a new user story:

1. **Write Acceptance Test (RED)**: Define complete business flow with multiple API calls
2. **Create Infrastructure Interfaces**: Define driven ports (repositories, external services)
3. **Unit Test Cycle**: While acceptance test failing:
   - Write unit test for domain behavior (RED)
   - Implement domain objects (GREEN)
   - Refactor if needed
   - Commit on green
4. **Integration Tests**: Test driven adapter implementations with real systems
5. **Contract Tests**: Test driving adapters for HTTP API compliance
6. **E2E Tests**: Optional complete system validation
7. **Final Commit**: All tests green, feature complete

### Key Success Indicators

- **Acceptance test stays RED** until complete behavior is implemented
- **Each layer tested appropriately** with correct boundaries
- **Clean commits** on each green cycle
- **Real business value** delivered through complete user journeys
- **Proper test taxonomy** - acceptance tests test flows, not single operations

Always follow the test pyramid: more unit tests, fewer E2E tests, but make sure acceptance tests cover **real business workflows**.

## Aggregate-Repository Pattern & Traversal

### Critical Repository-Aggregate Relationship

**The repository pattern has a 1:1 relationship with aggregate roots**:

- ❌ **Wrong**: `LocationRepository`, `ItemRepository` for individual entities
- ✅ **Right**: `WorldRepository` for the World aggregate root

**Repository loads the complete aggregate, aggregate root handles traversal**:

```python
# ❌ Wrong: Repository provides entity-specific query methods
class WorldRepository(ABC):
    @abstractmethod
    def find_location_by_sid(self, location_sid: Sid) -> Location | None:
        pass

    @abstractmethod
    def find_starting_location(self) -> Location | None:
        pass

# ✅ Right: Repository loads aggregate, aggregate provides traversal
class WorldRepository(ABC):
    @abstractmethod
    def get_world(self) -> World:
        """Get the complete world aggregate with all locations loaded"""
        pass

# Aggregate root provides traversal methods
class World:
    def get_location(self, location_sid: Sid) -> Location | None:
        return self._locations.get(location_sid)

    def get_starting_location(self) -> Location | None:
        return self._locations.get(self._starting_location_sid)
```

### Why This Pattern Matters

**Aggregate Integrity**: The aggregate root maintains consistency and business rules across all entities within the aggregate boundary.

**Performance**: Loading the complete aggregate once is more efficient than multiple entity queries.

**Domain Clarity**: Traversal logic belongs in the domain layer (aggregate root), not infrastructure layer (repository).

**Testing**: Easier to test domain behavior when aggregate handles its own traversal rather than depending on repository query methods.

### Implementation Guidelines

1. **One Repository Per Aggregate**: Each aggregate root gets exactly one repository interface
2. **Load Complete Aggregate**: Repository methods load all related entities within the aggregate boundary
3. **Aggregate Handles Queries**: All entity lookup and traversal logic resides in the aggregate root
4. **No Entity Repositories**: Individual entities within an aggregate do not get their own repositories

### Usage Example

```python
# Use case gets aggregate from repository, then uses aggregate methods
class StartGameUseCase:
    def execute(self, command: StartGameCommand) -> StartGameResponse:
        # Repository loads complete aggregate
        world = self._world_repository.get_world()

        # Aggregate root handles traversal
        starting_location = world.get_starting_location()

        # Domain logic continues...
```

This pattern ensures proper separation of concerns and maintains aggregate boundaries as designed in Domain-Driven Design.
