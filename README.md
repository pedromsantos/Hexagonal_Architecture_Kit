# Hexagonal Architecture and Domain Driven Design (DDD) Kit

A comprehensive reference kit for implementing Domain Driven Design (DDD) with Ports & Adapters (Hexagonal Architecture) and CQRS patterns in Python, TypeScript, Java, C#, Rust, and Go.

## What is This?

This repository contains:

- **[RULES.md](RULES.md)** - Complete implementation rules and guidelines with detailed code examples across multiple languages
- **[AI_PROMPT_TEMPLATE.md](AI_PROMPT_TEMPLATE.md)** - Template AI assistant instructions for Test-Driven Development (TDD) and architectural best practices to copy to your projects
- **[agents/](agents/)** - Specialized Claude Code agents for architecture review, TDD guidance, and rules compliance checking
- **[examples/](examples/)** - Usage demonstrations showing agents in action

These files serve as reference materials that you can copy into your own projects to maintain consistent architectural patterns and executable architectural governance.

## Specialized Claude Code Agents

This kit includes an **orchestrator-based agent system** that provides **executable architectural governance** by coordinating specialized agents through Pedro's Algorithm (London School TDD).

### The Orchestrator-Agent System

The agent system follows a **conductor-orchestra model**:

- **🎼 [Orchestrator](agents/orchestrator.md)** - The conductor who coordinates everything
- **🎻 Specialized Agents** - The musicians, each expert in their domain

**You interact with the ORCHESTRATOR, not individual agents directly.**

The orchestrator:

1. Assesses what you have (requirements, stories, architecture plan, etc.)
2. Determines the correct workflow entry point
3. Invokes specialized agents in the proper sequence
4. Enforces quality gates and Pedro's Algorithm
5. Ensures acceptance tests stay RED until feature complete
6. Maintains commit discipline (only on GREEN)

### How to Use the Orchestrator

**Step 1: Tell the orchestrator what you have**

The orchestrator will automatically determine where to start based on your situation:

| You Have                  | Orchestrator Starts At               | Skips                      |
| ------------------------- | ------------------------------------ | -------------------------- |
| Raw business requirements | Planning (user story creation)       | None                       |
| Written user stories      | Story validation & quality review    | User story writing         |
| Validated user stories    | Architecture planning                | Story writing & review     |
| Architecture plan ready   | Acceptance test writing (TDD starts) | All planning phases        |
| Acceptance test written   | TDD implementation cycle             | Planning & acceptance test |

**Step 2: Example conversations**

```
"I need to implement user registration with email confirmation"
→ Orchestrator: No stories exist, starts planning phase

"I have this user story: 'As a user, I want to register...'"
→ Orchestrator: Story exists, validates quality first

"I have a validated story and architecture plan ready"
→ Orchestrator: Ready for TDD, writes acceptance test first
```

**Step 3: Follow the orchestrator's guidance**

The orchestrator will:

- Invoke the right agents at the right time
- Keep you in the RED → GREEN → REFACTOR cycle
- Ensure proper test boundaries (unit vs acceptance vs integration)
- Run review agents before allowing commits
- Deliver working, tested, architecturally-sound features

### Complete Workflow Example

```txt
You: "I need user registration with email confirmation"

Orchestrator Assessment:
- No user stories exist
- Entry Point: writers/planning/user_story
- Workflow: Planning → TDD → Review

Orchestrator Execution:
1. writers/planning/user_story → Creates story
2. reviewers/user_story → ❌ Too large (8 days)
3. writers/planning/story_slicer → Splits into 2 slices
4. reviewers/user_story → ✅ Both slices pass
5. writers/planning/architect → Architecture plan

For each slice:
6. writers/tests/acceptance → Failing test (RED)
7. Loop while RED:
   - writers/tests/unit → Failing unit test
   - writers/domain/aggregate → Domain objects (GREEN)
   - Commit
8. writers/tests/integration → Real database tests
9. writers/infrastructure/repository → Repository implementation
10. writers/tests/contract → API contract tests
11. writers/infrastructure/controller → HTTP endpoints
12. All reviewers → Quality gates
13. Final commit → Feature complete ✅
```

### Quick Reference

**For complete documentation on the agent system, see [agents/README.md](agents/README.md)**

**Key Resources:**

- [orchestrator.md](agents/orchestrator.md) - How the orchestrator coordinates agents
- [agents/README.md](agents/README.md) - Complete agent catalog and usage guide
- Individual agent files - Detailed instructions for each specialized agent

### Available Agents

#### Orchestrator Agent

**[orchestrator.md](agents/orchestrator.md)** - Main workflow coordinator

Orchestrates all specialized agents through Pedro's Algorithm TDD cycle:

- Coordinates planning → test-writing → implementation → review workflow
- Enforces acceptance test stays RED until feature complete
- Manages commit discipline (only on green)
- Ensures proper agent sequencing and quality gates

#### Planning Agents

**[user_story.md](agents/writers/planning/user_story.md)** - Translates business requirements into well-formed user stories with acceptance criteria and domain concepts.

**[story_slicer.md](agents/writers/planning/story_slicer.md)** - Breaks large stories into vertical slices that deliver business value independently.

**[architect.md](agents/writers/planning/architect.md)** - Plans architecture: aggregates, ports, adapters, CQRS split, testing strategy.

#### Test-Writing Agents

**[acceptance.md](agents/writers/tests/acceptance.md)** - Writes failing acceptance tests for COMPLETE use case execution with ALL adapters mocked/faked.

**[unit.md](agents/writers/tests/unit.md)** - Writes unit tests for domain behavior with proper mocking discipline (mock ports only, never domain objects).

**[integration.md](agents/writers/tests/integration.md)** - Tests driven adapters with real external systems (databases, APIs).

**[contract.md](agents/writers/tests/contract.md)** - Tests driving adapter contracts (HTTP status codes, validation, response schemas).

**[e2e.md](agents/writers/tests/e2e.md)** - Optional full system tests with real infrastructure.

#### Domain Layer Implementation Agents

**[aggregate.md](agents/writers/domain/aggregate.md)** - Implements complete aggregates (root + entities + value objects) with proper boundaries and invariant enforcement.

**[services.md](agents/writers/domain/services.md)** - Implements stateless domain services for logic spanning multiple aggregates.

**[events.md](agents/writers/domain/events.md)** - Creates immutable domain events (past tense) representing state changes.

#### Application Layer Implementation Agents

**[command_handler.md](agents/writers/application/command_handler.md)** - Implements CQRS write operations (commands) that go THROUGH domain for business rule enforcement.

**[query_handler.md](agents/writers/application/query_handler.md)** - Implements CQRS read operations (queries) that BYPASS domain for optimized performance.

**[repository_interface.md](agents/writers/domain/repository_interface.md)** - Designs repository interfaces in domain layer (one per aggregate root, domain language).

#### Infrastructure Layer Implementation Agents

**[driving_adapter.md](agents/writers/infrastructure/driving_adapter.md)** - Implements HTTP controllers, CLI handlers that translate external requests to commands/queries.

**[repository.md](agents/writers/infrastructure/repository.md)** - Implements database-specific repositories with ORM mapping.

**[external_service_adapter.md](agents/writers/infrastructure/external_service_adapter.md)** - Implements adapters for external APIs with authentication, retries, error handling.

**[database_migration.md](agents/writers/infrastructure/database_migration.md)** - Creates database migration scripts for schema and data changes.

#### Utility Agents

**[dto_generator.md](agents/writers/utilities/dto_generator.md)** - Generates Data Transfer Objects for commands, queries, and responses.

**[id_generator.md](agents/writers/utilities/id_generator.md)** - Provides external ID/SID generation (IDs generated OUTSIDE application).

**[time_provider.md](agents/writers/utilities/time_provider.md)** - Abstracts system time for testability.

#### Review Agents

**[hexagonal.md](agents/reviewers/hexagonal.md)** - Reviews code against Hexagonal Architecture and DDD patterns (1:1 aggregate-repository, dependency flow, layer boundaries).

**[cqrs.md](agents/reviewers/cqrs.md)** - Validates CQRS implementation (command/query separation, commands through domain, queries bypass domain).

**[ddd.md](agents/reviewers/ddd.md)** - Validates DDD tactical patterns (entities, value objects, aggregates, repositories, domain services, domain events).

**[code.md](agents/reviewers/code.md)** - Reviews code quality (functional programming over loops, code smells, Object Calisthenics principles).

**[tests.md](agents/reviewers/tests.md)** - Validates proper test taxonomy and boundaries (unit vs acceptance, mocking discipline, verification rules).

**[london_tdd.md](agents/reviewers/london_tdd.md)** - Guides implementation using London School TDD (Pedro's Algorithm) with proper mocking and verification discipline.

**[chicago_tdd.md](agents/reviewers/chicago_tdd.md)** - Guides implementation using Classical TDD (Chicago/Detroit School) with minimal mocking and state verification.

### Agent Usage Example

```txt
# Start with planning
"Write a user story for user registration with email confirmation"
→ writers/planning/user_story

"Slice this story into deliverable pieces"
→ writers/planning/story_slicer

"Plan the architecture for user registration"
→ writers/planning/architect

# Implement with TDD
"Implement user registration following Pedro's Algorithm"
→ orchestrator
  → writers/tests/acceptance (writes failing test)
  → writers/tests/unit + writers/domain/aggregate (domain objects)
  → writers/application/command_handler (use case)
  → writers/tests/integration + writers/infrastructure/repository (persistence)
  → writers/tests/contract + writers/infrastructure/driving_adapter (HTTP API)

# Review before commit
"Review my implementation for architectural compliance"
→ reviewers/hexagonal, reviewers/cqrs, reviewers/ddd, reviewers/code, reviewers/tests
```

### How Agents Work

Agents transform architectural documentation into **executable governance**:

1. **Load** RULES.md and AI_PROMPT_TEMPLATE.md as context
2. **Apply** specialized instructions for their domain
3. **Reference** specific rules sections in feedback
4. **Demonstrate** compliance with code examples
5. **Maintain** consistency across all languages

### Benefits of Using Agents

- **Automated Reviews**: Catch architectural violations early
- **Consistent Guidance**: Same standards across team members
- **Specific Fixes**: Get actionable code examples, not just descriptions
- **Learning Tool**: Understand patterns through detailed feedback
- **Continuous Governance**: Run reviews on every commit/PR

## Alternative Ways to Use This Kit

While the **Claude Code orchestrator system** (described above) is the recommended approach, you can also use this kit with other tools:

### Option 1: With Claude Code (Integrates with Orchestrator)

#### If Starting a New Project (using Claude Code `/init`)

1. **Run `/init`** in your new project to generate a basic CLAUDE.md file
2. **Copy [RULES.md](RULES.md)** into your project's root directory
3. **Merge the architecture guidelines** into your generated CLAUDE.md:
   - Open both your generated `CLAUDE.md` and this kit's [AI_PROMPT_TEMPLATE.md](AI_PROMPT_TEMPLATE.md)
   - Copy these sections from AI_PROMPT_TEMPLATE.md into your CLAUDE.md:
     - `## Architecture Rules` (complete section)
     - `## TDD & Development Methodology` (complete section)
     - `## Aggregate-Repository Pattern & Traversal` (complete section)
   - Keep the project-specific sections from your generated CLAUDE.md

#### If Adding to an Existing Project

1. **Copy [AI_PROMPT_TEMPLATE.md](AI_PROMPT_TEMPLATE.md)** to your project as `CLAUDE.md` (or `.claude/CLAUDE.md`)

   - Update the "Project Overview" section with your specific project details
   - All TDD and architecture guidelines are already included

2. **Copy [RULES.md](RULES.md)** into your project's root directory
   - This provides detailed implementation rules and code examples
   - Referenced from your CLAUDE.md for easy lookup

### Option 2: With Other AI Assistants (Manual Workflow)

#### Using with Cursor

1. **Copy [RULES.md](RULES.md)** into your project's root directory
2. **Create `.cursorrules`** file in your project root
3. **Copy the content** from [AI_PROMPT_TEMPLATE.md](AI_PROMPT_TEMPLATE.md) into `.cursorrules`
4. Cursor will automatically read and follow these rules when assisting with code

#### Using with GitHub Copilot

1. **Copy [RULES.md](RULES.md)** into your project's root directory or `docs/` folder
2. **Create a `CONTRIBUTING.md`** or add to your project's README:
   - Reference the architectural patterns from RULES.md
   - Include key principles in your documentation
3. **Use Copilot Chat** with prompts like:
   - "Follow the DDD patterns in RULES.md to create a User entity"
   - "Implement this use case following the patterns in RULES.md"
4. Copilot will use your project documentation as context

#### Using with Windsurf

1. **Copy [RULES.md](RULES.md)** into your project's root directory
2. **Create `.windsurfrules`** file in your project root
3. **Copy the content** from [AI_PROMPT_TEMPLATE.md](AI_PROMPT_TEMPLATE.md) into `.windsurfrules`
4. Windsurf will automatically read and follow these rules when generating code

### Option 3: Manual Reference

Use this repository as a reference while coding:

1. Keep the [RULES.md](RULES.md) open in a browser or editor
2. Refer to specific sections as you implement features
3. Copy relevant code examples and adapt them to your domain

### What to Include in Your Project

**Essential files to copy:**

- `AI_PROMPT_TEMPLATE.md` → your project's AI assistant config file (CLAUDE.md, .cursorrules, .windsurfrules, etc.)
- `RULES.md` - Implementation rules and code examples
- `agents/` directory (optional) - For automated architecture reviews and TDD guidance
- `examples/` directory (optional) - For reference on using agents

**What NOT to copy:**

- This README (it's specific to the kit repository)
- The `.git` directory

## Key Patterns Documented

### Domain Driven Design (DDD)

- Entity and Value Object design
- Aggregate boundaries and rules
- Domain Services
- Repository patterns
- Domain Events

### Ports & Adapters (Hexagonal Architecture)

- Primary Ports (driving adapters - web controllers, CLI)
- Secondary Ports (driven adapters - databases, external APIs)
- Adapter implementations organized by technology
- Dependency injection and configuration

### Test-Driven Development (Pedro's Algorithm - London School)

- Outside-In TDD: Start with acceptance test, work inside-out
- Complete TDD cycle: Acceptance (RED) → Unit Tests → Integration → Contract → E2E
- Mock ONLY adapters (driven ports), never domain entities
- Separate verification of commands (side effects) vs queries (data retrieval)

### Integration Patterns

- Repositories as secondary ports
- Use cases as primary port implementations
- Event-driven architecture
- Cross-cutting concerns handling

## Quick Start Example

Here's how the patterns work together:

```python
# Domain Layer - Business logic, no infrastructure concerns
class User:  # Entity
    def __init__(self, sid: Sid, email: Email):
        self._sid = sid
        self._email = email

    def change_email(self, new_email: Email) -> UserEmailChanged:
        old_email = self._email
        self._email = new_email
        return UserEmailChanged(user_sid=self._sid, old_email=old_email, new_email=new_email)

# Domain Layer - Exit point interface (Driven Port)
class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        pass

# Application Layer - Orchestration (Use Case)
class ChangeUserEmailUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, command: ChangeUserEmailCommand) -> None:
        user = self._user_repo.find_by_sid(command.user_sid)
        event = user.change_email(command.new_email)
        self._user_repo.save(user)

# Infrastructure Layer - Entry point (Driving Adapter)
@app.post("/users/{user_id}/email")
def change_email_endpoint(user_id: str, request: ChangeEmailRequest):
    command = ChangeUserEmailCommand(user_sid=Sid(user_id), new_email=Email(request.email))
    use_case.execute(command)
    return {"status": "success"}

# Infrastructure Layer - Exit point implementation (Driven Adapter)
class PostgresUserRepository(UserRepository):
    def save(self, user: User) -> None:
        # SQL implementation details
        pass
```

## Language Support

The [RULES.md](RULES.md) includes complete examples in:

- Python
- TypeScript
- Java
- C#
- Rust
- Go

> **Note:** Examples were converted using LLMs. Some languages may have room for improvement. Pull requests welcome!

## Project Structure in Your Application

Recommended directory structure when using these patterns:

```txt
your-project/
├── CLAUDE.md                 # AI instructions (copied from this kit)
├── RULES.md                  # Architecture rules (copied from this kit)
├── agents/                   # (Optional) Specialized agents
│   ├── writers/             # Code generation agents
│   │   ├── planning/        # Architecture and story planning
│   │   ├── tests/           # Tests (acceptance, unit, integration, etc.)
│   │   ├── domain/          # Domain layer (aggregates, events, services)
│   │   ├── application/     # Application layer (command/query handlers)
│   │   ├── infrastructure/  # Infrastructure layer (adapters, repositories)
│   │   └── utilities/       # Cross-cutting utilities (DTOs, ID/time providers)
│   └── reviewers/           # Review agents (user stories, code, ddd, architecture, tests)
├── examples/                 # (Optional) Agent usage examples
│   ├── architecture_review_example.md
│   └── london_tdd_session_example.md
├── src/
│   ├── domain/              # Business logic (entities, value objects, aggregates)
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── services/
│   │   └── repositories/    # Repository interfaces (driven ports)
│   ├── application/         # Use cases and application services
│   │   └── use_cases/
│   └── infrastructure/      # Adapters and external concerns
│       ├── driving/         # Entry points (HTTP, CLI, etc.)
│       └── driven/          # Exit point implementations (databases, APIs)
└── tests/
    ├── acceptance/          # Complete business flows
    ├── unit/               # Domain logic
    ├── integration/        # Adapter implementations
    └── contract/           # API contracts
```

## Contributing

Found an issue or want to improve the examples? Pull requests welcome!

## License

Copyright (c) 2025 Pedro Santos

Licensed under the EUPL-1.2

This work is licensed under the European Union Public Licence v. 1.2. You may obtain a copy of the License at <https://eupl.eu/1.2/en/>

This is a reference kit for educational and development purposes. You are free to use, modify, and distribute this work under the terms of the EUPL-1.2 license.

## Learn More

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Growing Object-Oriented Software, Guided by Tests](http://www.growing-object-oriented-software.com/)

---

For the complete implementation rules and detailed code examples, see **[RULES.md](RULES.md)**.
