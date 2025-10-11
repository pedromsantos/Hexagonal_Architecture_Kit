# Agent Catalog

This directory contains specialized agents for implementing features following Pedro's Algorithm with hexagonal architecture and DDD patterns.

## 🎯 Getting Started

**Start here**: [orchestrator.md](orchestrator.md) - Coordinates all agents and determines workflow entry points.

## 📋 Agent Organization

### 📝 Writers (`/writers/`)

#### Planning (`/writers/planning/`)

| Agent                                            | Purpose                                            | When to Use                  |
| ------------------------------------------------ | -------------------------------------------------- | ---------------------------- |
| [user_story](writers/planning/user_story.md)     | Creates user stories from business requirements    | No user stories exist        |
| [story_slicer](writers/planning/story_slicer.md) | Breaks large stories into vertical slices          | Stories too large (>5 days)  |
| [architect](writers/planning/architect.md)       | Plans architecture (aggregates, ports, CQRS split) | Before implementation starts |

#### Tests (`/writers/tests/`)

| Agent                                       | Purpose                                                | When to Use                        |
| ------------------------------------------- | ------------------------------------------------------ | ---------------------------------- |
| [acceptance](writers/tests/acceptance.md)   | Writes failing acceptance tests for complete use cases | Start of TDD cycle                 |
| [unit](writers/tests/unit.md)               | Writes failing unit tests for individual components    | Inside TDD red-green-refactor loop |
| [integration](writers/tests/integration.md) | Tests driven adapters with real external systems       | After repositories implemented     |
| [contract](writers/tests/contract.md)       | Tests driving adapters for API contract compliance     | After controllers implemented      |
| [e2e](writers/tests/e2e.md)                 | Tests complete system with real infrastructure         | Optional - full system validation  |

#### Domain (`/writers/domain/`)

| Agent                                              | Purpose                                                        | When to Use                        |
| -------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------- |
| [aggregate](writers/domain/aggregate.md)           | Implements domain aggregates (root + entities + value objects) | Unit test requires domain behavior |
| [domain_service](writers/domain/domain_service.md) | Implements cross-aggregate business logic                      | Logic spans multiple aggregates    |
| [events](writers/domain/events.md)                 | Implements domain events for state changes                     | Need to notify other contexts      |

#### Application (`/writers/application/`)

| Agent                                     | Purpose                                             | When to Use                   |
| ----------------------------------------- | --------------------------------------------------- | ----------------------------- |
| [command](writers/application/command.md) | Implements CQRS command handlers (write operations) | Need write operation use case |
| [query](writers/application/query.md)     | Implements CQRS query handlers (read operations)    | Need read operation use case  |

#### Infrastructure (`/writers/infrastructure/`)

| Agent                                                                  | Purpose                                       | When to Use                       |
| ---------------------------------------------------------------------- | --------------------------------------------- | --------------------------------- |
| [repository_interface](writers/infrastructure/repository_interface.md) | Designs repository interfaces in domain layer | Before repository implementation  |
| [repository](writers/infrastructure/repository.md)                     | Implements database-specific repositories     | After integration tests written   |
| [migration](writers/infrastructure/migration.md)                       | Creates database schema migrations            | Schema changes needed             |
| [controller](writers/infrastructure/controller.md)                     | Implements HTTP controllers and CLI handlers  | After contract tests written      |
| [external_adapter](writers/infrastructure/external_adapter.md)         | Implements adapters for external APIs         | Integration with external systems |

#### Utilities (`/writers/utilities/`)

| Agent                                               | Purpose                           | When to Use                         |
| --------------------------------------------------- | --------------------------------- | ----------------------------------- |
| [dto](writers/utilities/dto.md)                     | Generates data transfer objects   | API request/response objects needed |
| [id_generator](writers/utilities/id_generator.md)   | Implements ID generation adapters | Custom ID generation strategy       |
| [time_provider](writers/utilities/time_provider.md) | Implements time provider adapters | Testable time operations needed     |

### 🔍 Reviewers (`/reviewers/`)

| Agent                                 | Purpose                                                    | When to Use                     |
| ------------------------------------- | ---------------------------------------------------------- | ------------------------------- |
| [user_story](reviewers/user_story.md) | Validates story quality (INVEST criteria, domain concepts) | Stories need quality validation |
| [test](reviewers/test.md)             | Validates test taxonomy and mock discipline                | Before final commit             |
| [code](reviewers/code.md)             | Reviews code against RULES.md patterns                     | Before final commit             |
| [hexagonal](reviewers/hexagonal.md)   | Validates hexagonal architecture boundaries                | Before final commit             |
| [cqrs](reviewers/cqrs.md)             | Validates CQRS pattern compliance                          | Before final commit             |
| [ddd](reviewers/ddd.md)               | Validates DDD tactical pattern usage                       | Before final commit             |

## 🔄 Typical Agent Flow

### For New Features

1. **Planning**: `writers/planning/user_story` → `reviewers/user_story` → `writers/planning/story_slicer` → `writers/planning/architect`
2. **TDD Cycle**: `writers/tests/acceptance` → (`writers/tests/unit` → domain/application implementers)\* → `writers/tests/integration` → `writers/tests/contract`
3. **Review**: All reviewer agents validate before final commit

### Entry Points by Situation

- **No stories**: Start with `writers/planning/user_story`
- **Have stories**: Start with `reviewers/user_story`
- **Ready stories**: Start with `writers/planning/architect`
- **Have architecture**: Start with `writers/tests/acceptance`

## 📖 Usage Guidelines

### Agent Coordination

- **Always use orchestrator** to coordinate agent sequence
- **Follow Pedro's Algorithm** as defined in orchestrator
- **Maintain proper boundaries** between agent responsibilities

### Quality Gates

- **User stories must pass review** (85%+ quality score) before implementation
- **All tests must be GREEN** before commits
- **All review agents must pass** before final commit

### Common Patterns

- **One repository per aggregate** - Use repository_interface_designer + repository_implementer
- **CQRS separation** - Use command_handler_implementer OR query_handler_implementer
- **Test taxonomy** - Different test types have specific agents and boundaries
- **Mock discipline** - Only mock adapters, never domain objects

## 🎯 Success Indicators

- ✅ Acceptance test stays RED until complete feature implemented
- ✅ Each agent produces working, tested output
- ✅ Clean commits on each green cycle
- ✅ All review agents pass quality gates
- ✅ Real business value delivered

## 🔗 Related Documentation

- [RULES.md](../RULES.md) - Complete DDD and hexagonal architecture implementation rules
- [AI_PROMPT_TEMPLATE.md](../AI_PROMPT_TEMPLATE.md) - Quick reference for Claude
- [CLAUDE.md](../CLAUDE.md) - Comprehensive guidance for Claude Code

---

**Remember**: The orchestrator coordinates everything. Individual agents focus on their specific expertise while the orchestrator ensures proper sequencing and quality gates.
