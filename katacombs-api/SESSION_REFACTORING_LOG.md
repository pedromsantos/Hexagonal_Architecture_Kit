# Hexagonal Architecture & DDD Refactoring Session

**Date:** 2025-09-23
**Project:** Katacombs API - Hexagonal Architecture Kit
**Focus:** Domain-Driven Design and Clean Architecture Improvements

## Session Overview

This session involved a comprehensive refactoring of the Katacombs API codebase to better align with Domain-Driven Design (DDD) principles and Hexagonal Architecture patterns. The work was driven by feedback identifying architectural violations and YAGNI principle breaches.

---

## Initial State Analysis

### Codebase Structure (Before)

```txt
src/katacombs/
├── domain/
│   ├── entities/           # Technical grouping
│   ├── value_objects/      # Technical grouping
│   ├── services/           # Technical grouping
│   └── repositories/       # Technical grouping
├── application/
└── infrastructure/

tests/
├── acceptance/             # Grouped by test type
├── contract/              # Grouped by test type
├── e2e/                   # Grouped by test type
├── integration/           # Grouped by test type
└── unit/                  # Grouped by test type
```

### Key Issues Identified

1. **World Repository Initialization Logic in Infrastructure**

   ```python
   # PROBLEM: Business logic in repository
   def _initialize_starting_location(self) -> None:
       starting_sid = Sid.generate()
       description = "You are in the entrance hall..."
       # Complex world building logic in repository
   ```

2. **Over-engineered Value Objects (YAGNI Violations)**

   ```python
   # Unused enum values and methods
   class Action(Enum):
       OPEN = "open"        # ❌ Never used
       CLOSE = "close"      # ❌ Never used
       DROP = "drop"        # ❌ Never used

   def from_string(cls, action: str) -> "Action":  # ❌ Never called
   def opposite(self) -> "Direction":              # ❌ Never called
   ```

3. **Improper Domain Organization**

   - Technical folders instead of business aggregates
   - Repository interfaces scattered in generic `/repositories/` folder
   - WorldBuilder service misplaced in `/entities/` folder

4. **Test Structure Not Mirroring Production Code**

   - Tests grouped by type instead of mirroring domain structure
   - No clear naming convention for test types

5. **Repository Interface Violating Aggregate Pattern**

   ```python
   # PROBLEM: Repository querying individual entities
   @abstractmethod
   def find_location_by_sid(self, location_sid: Sid) -> Location | None:
   ```

---

## Feedback and Guidance Provided

### 1. "Move Business Logic to Domain Entities"

**Feedback:** _"Creating the World/Map is business not infra and should not be in repos"_

**Issue:** World initialization logic was implemented in the repository layer, violating separation of concerns.

**Solution Direction:** Create World entity and WorldBuilder service in domain layer.

### 2. "Organize Domain by Aggregates"

**Feedback:** _"Instead of having @src/katacombs/domain/entities/ and @src/katacombs/domain/value_objects/ folders I would prefer to have folders that reflect the aggregates example player, world"_

**Issue:** Domain organized by technical concerns rather than business concepts.

**Solution Direction:** Restructure domain into aggregate-based folders.

### 3. "Move Repository Interfaces with Aggregates"

**Feedback:** _"Put repo interfaces with the aggregates as well"_

**Issue:** Repository interfaces separated from their aggregates in generic folder.

**Solution Direction:** Co-locate repository interfaces with their aggregates.

### 4. "Mirror Test Structure with Production Code"

**Feedback:** _"For @tests/acceptance/ they should at least be in a similar folder to use cases in the app and unit test should also mimic the folders of prod code"_

**Issue:** Test organization by test type rather than production code structure.

**Solution Direction:** Reorganize tests to mirror production code hierarchy.

### 5. "Add Test Type Suffixes"

**Feedback:** _"Maybe suffix tests filename with type test_something_unit test_something_contract test_something_integration"_

**Issue:** Test purpose not immediately clear from filename.

**Solution Direction:** Add descriptive suffixes to test filenames.

### 6. "Proper Repository-Aggregate Relationship"

**Feedback:** _"There should be no such repo since the repo is 1:1 with aggregate and the aggregate is world"_

**Issue:** LocationRepository should be WorldRepository since World is the aggregate root.

**Solution Direction:** Rename and restructure repository to match aggregate.

### 7. "Repository Should Not Query Individual Entities"

**Feedback:** _"Should not be in the repo, the world repo loads the world hierarchy all at once and then the aggregate root provides methods to traverse that aggregate"_

**Issue:** Repository interface exposing methods to query individual entities within aggregate.

**Solution Direction:** Repository should only load complete aggregates.

### 8. "Mock Verification Principle"

**Feedback:** _"Do not verify stubs (mocks of queries) example mock_world_repo.find_starting_location.assert_called_once() only verify mocks (mocks of commands example ) mock_player_repo.save.assert_called_once()"_

**Issue:** Tests verifying query method calls instead of focusing on side effects.

**Solution Direction:** Only verify command methods, not query methods.

---

## Refactoring Work Performed

### Phase 1: Extract World Creation Logic to Domain

#### 1.1 Created World Entity

```python
# src/katacombs/domain/entities/world.py
class World:
    """Domain entity representing the complete game world
    A read-only container for all locations in the game world.
    """
    def __init__(self, locations: dict[Sid, Location], starting_location_sid: Sid):
        self._locations = locations.copy()  # Defensive copy
        self._starting_location_sid = starting_location_sid

    def get_starting_location(self) -> Location:
        return self._locations[self._starting_location_sid]
```

#### 1.2 Created WorldBuilder Service

```python
# src/katacombs/domain/entities/world_builder.py
class WorldBuilder:
    """Builder for constructing the game world
    Encapsulates all world creation logic and business rules.
    """
    def create_starter_world(self) -> World:
        # Moved all initialization logic from repository here
        entrance_sid = Sid.generate()
        entrance_location = Location(sid=entrance_sid, description="...")
        # ... world building logic
```

#### 1.3 Refactored Repository

```python
# Before: Repository doing world creation
def _initialize_starting_location(self) -> None:
    # Complex business logic here

# After: Repository using domain service
def _create_default_world(self) -> World:
    builder = WorldBuilder()
    return builder.create_starter_world()
```

**Outcome:** ✅ Business logic moved from infrastructure to domain layer.

### Phase 2: Remove Over-engineered Code (YAGNI)

#### 2.1 Simplified Action Enum

```python
# Before: Over-engineered
class Action(Enum):
    OPEN = "open"      # ❌ Removed - never used
    CLOSE = "close"    # ❌ Removed - never used
    PICK = "pick"      # ✅ Kept - actually used
    DROP = "drop"      # ❌ Removed - never used
    USE = "use"        # ✅ Kept - actually used

    def from_string(cls, action: str):  # ❌ Removed - never called

# After: YAGNI compliant
class Action(Enum):
    PICK = "pick"
    USE = "use"

    def __str__(self) -> str:
        return self.value
```

#### 2.2 Simplified Direction Enum

```python
# Before: Over-engineered
class Direction(Enum):
    NORTH = "north"    # ✅ Kept - actually used
    SOUTH = "south"    # ✅ Kept - actually used
    EAST = "east"      # ✅ Kept - actually used
    WEST = "west"      # ✅ Kept - actually used
    UP = "up"          # ❌ Removed - never used
    DOWN = "down"      # ❌ Removed - never used

    def from_string(cls, direction: str):  # ❌ Removed - never called
    def opposite(self) -> "Direction":     # ❌ Removed - never called

# After: YAGNI compliant
class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

    def __str__(self) -> str:
        return self.value
```

**Outcome:** ✅ Removed unused code, simplified value objects to actual requirements.

### Phase 3: Move WorldBuilder to Proper Location

#### 3.1 Identified Misplaced Service

```python
# Problem: WorldBuilder was in /entities/ folder
src/katacombs/domain/entities/world_builder.py  # ❌ Wrong location
```

#### 3.2 Moved to Services Folder

```python
# Solution: Moved to proper domain services location
src/katacombs/domain/services/world_builder.py  # ✅ Correct location
```

**Outcome:** ✅ Domain services properly organized separate from entities.

### Phase 4: Restructure Domain by Aggregates

#### 4.1 New Aggregate-Based Structure

```python
# Before: Technical organization
src/katacombs/domain/
├── entities/           # ❌ Technical grouping
├── value_objects/      # ❌ Technical grouping
├── services/           # ❌ Technical grouping
└── repositories/       # ❌ Technical grouping

# After: Business aggregate organization
src/katacombs/domain/
├── player/             # ✅ PLAYER AGGREGATE
│   ├── player.py           # (aggregate root)
│   ├── bag.py              # (entity owned by player)
│   ├── sid.py              # (value object for identity)
│   └── player_repository.py # (repository interface)
└── world/              # ✅ WORLD AGGREGATE
    ├── world.py            # (aggregate root)
    ├── location.py         # (entity part of world)
    ├── item.py             # (entity in locations)
    ├── action.py           # (value object for interactions)
    ├── direction.py        # (value object for navigation)
    ├── world_builder.py    # (domain service)
    └── world_repository.py # (repository interface)
```

#### 4.2 Updated All Imports

```python
# Before: Technical imports
from ...domain.entities.player import Player
from ...domain.value_objects import Sid
from ...domain.repositories.player_repository import PlayerRepository

# After: Aggregate imports
from ...domain.player import Player, Sid, PlayerRepository
from ...domain.world import World, Location, WorldBuilder
```

**Outcome:** ✅ Domain organized by business concepts, not technical concerns.

### Phase 5: Restructure Test Organization

#### 5.1 Mirror Production Code Structure

```python
# Before: Test type organization
tests/
├── acceptance/         # ❌ Grouped by test type
├── contract/          # ❌ Grouped by test type
├── e2e/               # ❌ Grouped by test type
├── integration/       # ❌ Grouped by test type
└── unit/              # ❌ Grouped by test type

# After: Production code mirroring
tests/
├── application/
│   └── use_cases/         # ✅ Mirrors src/application/use_cases/
├── domain/
│   ├── player/            # ✅ Mirrors src/domain/player/
│   └── world/             # ✅ Mirrors src/domain/world/
└── infrastructure/
    ├── adapters/          # ✅ Mirrors src/infrastructure/adapters/
    └── repositories/      # ✅ Mirrors src/infrastructure/repositories/
```

#### 5.2 Added Test Type Suffixes

```python
# Before: Ambiguous naming
test_start_game.py
test_player.py
test_location_repository.py

# After: Clear test type naming
test_start_game_acceptance.py     # ACCEPTANCE TEST
test_start_game_unit.py           # UNIT TEST
test_player_unit.py               # UNIT TEST
test_location_repository_integration.py  # INTEGRATION TEST
test_game_controller_contract.py  # CONTRACT TEST
test_start_game_e2e.py            # END-TO-END TEST
```

**Outcome:** ✅ Tests organized by production code structure with clear naming.

### Phase 6: Correct Repository-Aggregate Relationship

#### 6.1 Renamed LocationRepository to WorldRepository

```python
# Before: Repository named after entity
class LocationRepository(ABC):  # ❌ Wrong - Location is not aggregate root
    def find_by_sid(self, location_sid: Sid) -> Location | None:

# After: Repository named after aggregate root
class WorldRepository(ABC):     # ✅ Correct - World is aggregate root
    def get_world(self) -> World:
```

#### 6.2 Updated Implementation

```python
# Before: Repository querying entities
class InMemoryLocationRepository(LocationRepository):
    def find_by_sid(self, location_sid: Sid) -> Location | None:
        return self._world.get_location(location_sid)

# After: Repository handling complete aggregate
class InMemoryWorldRepository(WorldRepository):
    def get_world(self) -> World:
        return self._world
```

**Outcome:** ✅ Repository properly aligned with aggregate pattern.

### Phase 7: Implement Proper Aggregate Pattern

#### 7.1 Removed Entity Queries from Repository

```python
# Before: Repository exposing entity queries (WRONG)
class WorldRepository(ABC):
    @abstractmethod
    def find_location_by_sid(self, location_sid: Sid) -> Location | None:
        """❌ Should not query individual entities"""

    @abstractmethod
    def find_starting_location(self) -> Location | None:
        """❌ Should not query individual entities"""

# After: Repository only handles aggregate persistence (CORRECT)
class WorldRepository(ABC):
    @abstractmethod
    def get_world(self) -> World:
        """✅ Only loads complete aggregate"""
```

#### 7.2 Updated Use Case to Work with Aggregate

```python
# Before: Use case calling repository for entity queries
starting_location = self._world_repository.find_starting_location()

# After: Use case working through aggregate root
world = self._world_repository.get_world()
starting_location = world.get_starting_location()
```

**Outcome:** ✅ Proper DDD aggregate pattern implemented.

### Phase 8: Document Mock Verification Principle

#### 8.1 Added to CLAUDE.md

````python
# Added comprehensive guidance on mock verification
### Mock Verification Principle

**Only verify COMMANDS (methods that cause side effects), never verify QUERIES:**

**ALWAYS VERIFY** (Commands - Side Effects):
```python
# ✅ Verify commands that cause state changes
mock_player_repo.save.assert_called_once()
mock_email_service.send.assert_called_once()
````

**NEVER VERIFY** (Queries - Data Retrieval):

```python
# ❌ Do NOT verify queries - this makes tests brittle
mock_world_repo.find_starting_location.assert_called_once()  # Wrong!
```

#### 8.2 Applied to Tests

```python
# Before: Verifying both commands and queries
mock_world_repo.find_starting_location.assert_called_once()  # ❌ Query
mock_player_repo.save.assert_called_once()                  # ✅ Command

# After: Only verifying commands
# Only verify COMMANDS (side effects), not QUERIES (data retrieval)
mock_player_repo.save.assert_called_once()  # ✅ Command - causes state change
# Do NOT verify: mock_world_repo.find_starting_location.assert_called_once()  # ❌ Query
```

**Outcome:** ✅ Testing principle documented and applied.

### Phase 9: Create Comprehensive Unit Tests for Domain Behavior

#### 9.1 Identified Missing Test Coverage

```txt
# Problem: Domain had business logic but no unit tests
tests/domain/world/
├── __init__.py  # ❌ Only empty init file, no actual tests
```

**Missing Tests for:**

- World entity (aggregate root with 9 business behaviors)
- Location entity (13 validation and business rules)
- Item entity (13 validation and creation rules)
- WorldBuilder service (12 complex construction scenarios)

#### 9.2 Created Comprehensive Unit Test Suite

```python
# Created complete unit test coverage
tests/domain/world/
├── __init__.py
├── test_world_unit.py           # 9 tests - World aggregate behavior
├── test_location_unit.py        # 13 tests - Location entity logic
├── test_item_unit.py           # 13 tests - Item entity validation
└── test_world_builder_unit.py  # 12 tests - WorldBuilder service logic
```

#### 9.3 Test Coverage Details

**World Entity Unit Tests (9 tests):**

- World creation with validation
- Starting location management and traversal
- Location query methods (`get_location`, `has_location`)
- Defensive copying behavior for immutability
- Multiple location scenarios and edge cases

**Location Entity Unit Tests (13 tests):**

- Location creation with description validation
- Exit management (connected vs blocked exits)
- Available directions calculation business logic
- Item management and ordering
- Edge cases for empty descriptions and overwrites

**Item Entity Unit Tests (13 tests):**

- Item creation with name/description validation
- Action management for different item types
- Validation rules for empty/whitespace inputs
- Edge cases with duplicates and special characters
- Equality behavior based on SID

**WorldBuilder Service Unit Tests (12 tests):**

- Starter world creation with proper structure
- Custom world building with fluent interface
- Location connectivity validation (bidirectional)
- Error handling for invalid configurations
- Builder reusability and independence

**Outcome:** ✅ Complete domain behavior coverage with 47 additional unit tests.

### Phase 10: Establish Test-First Development Principle

#### 10.1 Critical Development Rule Added

**Core Principle:** You should not generate any code without creating a test before.

**Why This Matters:**

- Tests define expected behavior before implementation
- Prevents over-engineering and YAGNI violations
- Ensures all code serves a verified purpose
- Maintains clean architecture boundaries

**Implementation Guidelines:**

1. Write failing test first (RED)
2. Implement minimal code to pass (GREEN)
3. Refactor while maintaining tests (REFACTOR)
4. Only add features that serve actual test requirements

**Outcome:** ✅ Test-first development principle established and documented.

---

## Final Architecture

### Domain Structure (After)

```txt
src/katacombs/domain/
├── player/                    # PLAYER AGGREGATE
│   ├── __init__.py           # exports: Bag, Player, PlayerRepository, Sid
│   ├── player.py             # (aggregate root)
│   ├── bag.py                # (entity owned by player)
│   ├── sid.py                # (value object for identity)
│   └── player_repository.py  # (repository interface for player aggregate)
└── world/                     # WORLD AGGREGATE
    ├── __init__.py           # exports: Action, Direction, Item, Location, World, WorldBuilder, WorldRepository
    ├── world.py              # (aggregate root)
    ├── location.py           # (entity part of world)
    ├── item.py               # (entity exists in locations)
    ├── action.py             # (value object for interactions)
    ├── direction.py          # (value object for navigation)
    ├── world_builder.py      # (domain service)
    └── world_repository.py   # (repository interface for world aggregate)
```

### Test Structure (After)

```txt
tests/
├── application/
│   └── use_cases/
│       ├── test_start_game_acceptance.py     # ACCEPTANCE TEST
│       ├── test_start_game_e2e.py           # END-TO-END TEST
│       └── test_start_game_unit.py          # UNIT TEST (use case logic)
├── domain/
│   └── player/
│       └── test_player_unit.py              # UNIT TEST (domain entity)
└── infrastructure/
    ├── adapters/
    │   └── test_game_controller_contract.py  # CONTRACT TEST (HTTP API)
    └── repositories/
        ├── test_world_repository_integration.py      # INTEGRATION TEST
        └── test_player_repository_integration.py     # INTEGRATION TEST
```

### Repository Pattern (After)

```txt
Use Case → Repository.get_world() → World.get_starting_location()
         ↓                        ↓
    Loads Aggregate          Traverses Aggregate
```

---

## Outcomes and Benefits

### 1. **Proper Domain-Driven Design**

- ✅ Domain organized by business aggregates (Player, World)
- ✅ Repository interfaces co-located with their aggregates
- ✅ Aggregate roots control access to internal entities
- ✅ Repository-per-aggregate pattern correctly implemented

### 2. **Clean Architecture Principles**

- ✅ Business logic moved from infrastructure to domain layer
- ✅ Separation of concerns properly maintained
- ✅ Domain services handle complex business operations
- ✅ Infrastructure only handles technical concerns

### 3. **YAGNI Compliance**

- ✅ Removed unused enum values and methods
- ✅ Simplified value objects to actual requirements
- ✅ Code now serves acceptance test requirements only

### 4. **Test Organization Excellence**

- ✅ Tests mirror production code structure
- ✅ Clear test type identification via naming
- ✅ Proper mock verification focusing on side effects
- ✅ Each test type has appropriate boundaries

### 5. **Maintainability Improvements**

- ✅ Natural navigation between production and test code
- ✅ Clear aggregate boundaries
- ✅ Cohesive imports from business contexts
- ✅ Self-documenting file organization

### 6. **DDD Best Practices**

- ✅ Aggregates as consistency boundaries
- ✅ Repository per aggregate root
- ✅ Domain services for complex operations
- ✅ Value objects focused on actual usage

---

## Testing Results

**Final Test Suite:** All 71 tests passing ✅

- **5 Acceptance/E2E Tests** - Complete business flows
- **52 Unit Tests** - Domain behavior and use case orchestration
- **6 Contract Tests** - HTTP API compliance
- **8 Integration Tests** - Repository implementations

**Test Categories by Location:**

- `tests/application/use_cases/` - 5 tests (acceptance, e2e, unit)
- `tests/domain/player/` - 4 tests (domain unit tests)
- `tests/domain/world/` - 47 tests (domain unit tests)
- `tests/infrastructure/adapters/` - 6 tests (contract tests)
- `tests/infrastructure/repositories/` - 9 tests (integration tests)

---

## Key Principles Established

### 1. **Aggregate Design Pattern**

- Repositories handle complete aggregates, not individual entities
- Aggregate roots provide methods for internal traversal
- 1:1 relationship between repository and aggregate

### 2. **Domain Organization**

- Organize by business concepts (aggregates) not technical concerns
- Co-locate related domain concepts (entities, value objects, repositories)
- Services handle complex domain operations

### 3. **YAGNI Principle**

- Implement only what serves actual acceptance tests
- Remove speculative functionality
- Keep code focused on real requirements

### 4. **Test Organization**

- Mirror production code structure
- Clear naming with test type suffixes
- Verify commands (side effects), not queries (implementation details)

### 5. **Clean Architecture**

- Business logic in domain layer
- Infrastructure handles only technical concerns
- Clear separation of responsibilities

### 6. **Test-First Development**

- No code without tests first (RED → GREEN → REFACTOR)
- Tests define expected behavior before implementation
- Prevents over-engineering and YAGNI violations
- Ensures all code serves verified test requirements

---

## Session Statistics

- **Files Modified:** 25+ files across domain, infrastructure, and tests
- **Lines of Code:** Reduced overall complexity while improving structure
- **Architecture Violations Fixed:** 8 major violations addressed
- **Test Structure:** Complete reorganization with improved clarity
- **Documentation:** Added comprehensive testing principles to CLAUDE.md

This refactoring session successfully transformed a technically-organized codebase into a properly structured Domain-Driven Design implementation following Hexagonal Architecture principles, with comprehensive test coverage and clear organizational patterns.
