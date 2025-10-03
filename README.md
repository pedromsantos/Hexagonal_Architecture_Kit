# Hexagonal Architecture Kit

A comprehensive reference kit for implementing Domain Driven Design (DDD) with Ports & Adapters (Hexagonal Architecture) and CQRS patterns in Python, TypeScript, Java, C#, Rust, and Go.

## What is This?

This repository contains:

- **[RULES.md](RULES.md)** - Complete implementation rules and guidelines with detailed code examples across multiple languages
- **[AI_PROMPT_TEMPLATE.md](AI_PROMPT_TEMPLATE.md)** - Template AI assistant instructions for Test-Driven Development (TDD) and architectural best practices to copy to your projects

These files serve as reference materials that you can copy into your own projects to maintain consistent architectural patterns.

## How to Use This Kit in Your Project

### Option 1: For AI-Assisted Development (Recommended)

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

### Option 2: For Other AI Coding Assistants

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

This work is licensed under the European Union Public Licence v. 1.2. You may obtain a copy of the License at https://eupl.eu/1.2/en/

This is a reference kit for educational and development purposes. You are free to use, modify, and distribute this work under the terms of the EUPL-1.2 license.

## Learn More

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Growing Object-Oriented Software, Guided by Tests](http://www.growing-object-oriented-software.com/)

---

For the complete implementation rules and detailed code examples, see **[RULES.md](RULES.md)**.
