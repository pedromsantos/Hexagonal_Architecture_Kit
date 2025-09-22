# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **documentation-only repository** containing comprehensive rules and guidelines for implementing Domain Driven Design (DDD) with Ports & Adapters (Hexagonal Architecture) patterns in Python. The project serves as a reference kit for developers building applications using these architectural patterns.

## Repository Structure

- `README.md` - Comprehensive DDD and Hexagonal Architecture implementation rules with detailed code examples in Python, Typescript, Java, C#, Rust and Go

## Key Architecture Patterns Documented

This repository documents the integration of:

1. **Domain Driven Design (DDD)** patterns:

   - Entity and Value Object design
   - Aggregate boundaries and rules
   - Domain Services
   - Repository patterns
   - Domain Events

2. **Ports & Adapters (Hexagonal Architecture)** patterns:

   - Primary Ports (driving adapters - web controllers, CLI)
   - Secondary Ports (driven adapters - databases, external APIs)
   - Adapter implementations organized by technology
   - Dependency injection and configuration

3. **Integration patterns** combining DDD and Hexagonal Architecture:
   - Repositories as secondary ports
   - Use cases as primary port implementations
   - Event-driven architecture
   - Cross-cutting concerns handling

## Development Context

Since this is a documentation project:

- No build, test, or compilation commands are needed
- Changes involve editing markdown files
- Focus is on clarity, accuracy, and completeness of architectural guidance
- Examples should be syntactically correct Python code that demonstrates patterns

## Content Guidelines

When working with this repository:

- Maintain consistency with existing code examples and naming conventions
- Follow the established pattern of showing both interface definitions and implementations
- Ensure Python code examples are syntactically correct and follow PEP 8
- Keep examples focused on demonstrating architectural patterns, not full applications
- Use domain-neutral examples (User, Order, etc.) that are universally understood
