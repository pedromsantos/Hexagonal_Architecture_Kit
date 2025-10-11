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

**Follow [agents/orchestrator.md](agents/orchestrator.md) for complete workflow.**

**See [agents/README.md](agents/README.md) for complete agent catalog.**

### Workflow Entry Points

The orchestrator adapts to your starting point:

- **No user stories**: Start with `agents/writers/planning/user_story`
- **Have stories, need validation**: Start with `agents/reviewers/user_story`
- **Have validated stories**: Start with `agents/writers/planning/architect`
- **Ready to implement**: Start with `agents/writers/tests/acceptance`
