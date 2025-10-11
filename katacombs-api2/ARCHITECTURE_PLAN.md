# Architecture Plan: Katacombs Game API

## Domain Layer

### Aggregates

#### Player (Root)

- **Root Entity**: Player

  - Identity: Sid (value object, pattern: `^[0-9]{6}-[0-9]{12}-[00-9]{8}$`)
  - PlayerName: PlayerName (value object, 1-50 chars)
  - location_sid: Sid (reference to current Location)
  - Bag: Bag (value object, max 10 items + gold)
  - is_active: bool (starts True, set False on quit)

- **Domain Methods**:

  - `move_to_location(world: World, direction: Direction) -> None` - Validates exit exists and moves player
  - `pick_item(world: World, item_sid: Sid) -> None` - Validates item at location and adds to bag
  - `drop_item(item_sid: Sid) -> None` - Removes item from bag
  - `use_item(world: World, item_sid: Sid, action: Action) -> None` - Validates action and executes
  - `quit_game() -> None` - Marks player as inactive

- **Business Rules**:

  - Player SID must be unique across all active players
  - Player name validation (1-50 characters, non-empty)
  - Bag capacity constraint (maximum 10 items)
  - Only active players can perform game actions
  - Gold collection is automatic and doesn't count toward item limit
  - Player can only move through exits that exist at current location
  - Player can only pick items present at current location
  - Player can only use actions available on items

- **Repository**: PlayerRepository
  - `save(player: Player) -> None`
  - `find_by_sid(sid: Sid) -> Player | None`
  - `delete(sid: Sid) -> None`

#### World (Root - Read-Only)

- **Root Entity**: World

  - starting_location_sid: Sid
  - locations: Dict[Sid, Location] (all game locations)
  - items: Dict[Sid, Item] (global item registry)

- **Internal Entities**:

  - **Location**: sid, description, exits: Dict[Direction, Sid], items: List[Sid]
  - **Item**: sid, name, description, available_actions: List[Action], gold: Optional[int]

- **Domain Methods**:

  - `get_location(location_sid: Sid) -> Location` - Retrieve location by SID
  - `get_item(item_sid: Sid) -> Item` - Retrieve item by SID
  - `can_move(from_location: Sid, direction: Direction) -> bool` - Check if exit exists
  - `get_destination(from_location: Sid, direction: Direction) -> Sid` - Get destination SID
  - `is_item_at_location(item_sid: Sid, location_sid: Sid) -> bool` - Check item presence
  - `get_starting_location() -> Location` - Get the starting location

- **Business Rules**:

  - World is immutable during gameplay (read-only aggregate)
  - All locations must be reachable from starting location
  - Bidirectional exits must be consistent (if A->north->B, then B->south->A)
  - Items have unique SIDs across entire world
  - Items can only have predefined actions (OPEN, CLOSE, PICK, DROP, USE)

- **Repository**: WorldRepository
  - `get_world() -> World`

### Value Objects

- **Sid**: Unique identifier (pattern: `^[0-9]{6}-[0-9]{12}-[00-9]{8}$`)

  - Validation: Format compliance
  - Immutable, comparable

- **PlayerName**: String validation (1-50 chars, non-empty)

  - Validation: Length and content rules
  - Immutable

- **Direction**: Enum (NORTH, SOUTH, EAST, WEST, UP, DOWN)

  - Predefined cardinal directions for movement

- **Action**: Enum (OPEN, CLOSE, PICK, DROP, USE)

  - Available item interaction types

- **Bag**: Collection with capacity constraint
  - `item_sids: List[Sid]` (max 10 items)
  - `gold: int` (no limit, doesn't count toward item capacity)
  - Methods: `add_item()`, `remove_item()`, `has_item()`, `is_full()`, `item_count()`

### Domain Services

**Note**: Domain logic is encapsulated within the aggregates themselves. No separate domain services are needed for this bounded context.

### Domain Events

#### Player Lifecycle Events

- **GameStarted**: player_sid, player_name, starting_location_sid, timestamp
- **PlayerCreated**: player_sid, player_name, timestamp
- **GameEnded**: player_sid, final_location_sid, items_collected_count, timestamp
- **PlayerRemoved**: player_sid, timestamp

#### Movement Events

- **PlayerMovedToLocation**: player_sid, from_location_sid, to_location_sid, direction, timestamp
- **PlayerPlacedAtLocation**: player_sid, location_sid, timestamp

#### Item Events

- **ItemPickedUp**: player_sid, item_sid, location_sid, timestamp
- **ItemDropped**: player_sid, item_sid, location_sid, timestamp
- **ItemOpened**: player_sid, item_sid, location_sid, timestamp
- **ItemClosed**: player_sid, item_sid, location_sid, timestamp
- **ItemUsed**: player_sid, item_sid, location_sid, timestamp
- **GoldCollected**: player_sid, amount, item_sid, timestamp

#### Capacity Events

- **BagCapacityReached**: player_sid, attempted_item_sid, timestamp

## Application Layer

### Commands (Write Operations)

#### StartGameCommand

- **Handler**: StartGameCommandHandler
- **Input**: StartGameDto(name: str, sid: str)
- **Output**: StartGameResponse(sid, name, location, bag)
- **Goes through**: Player aggregate, World aggregate (read)
- **Business rules enforced**:
  - Player SID format validation
  - Player name validation
  - SID uniqueness check
  - Place player at starting location
- **Events published**: GameStarted, PlayerCreated, PlayerPlacedAtLocation

#### MovePlayerCommand

- **Handler**: MovePlayerCommandHandler
- **Input**: MovePlayerDto(player_sid: str, direction: str)
- **Output**: Success (200 OK, no body per OpenAPI)
- **Goes through**: Player aggregate, World aggregate (read)
- **Business rules enforced**:
  - Player exists and is active
  - Exit exists in requested direction
  - Destination location exists
- **Events published**: PlayerMovedToLocation

#### PickItemCommand

- **Handler**: PickItemCommandHandler
- **Input**: PickItemDto(player_sid: str, item_sid: str)
- **Output**: ActionResponse(message: "Action completed successfully")
- **Goes through**: Player aggregate, World aggregate (read)
- **Business rules enforced**:
  - Item exists at player's current location
  - Bag not full (< 10 items)
  - Item has "pick" action available
- **Events published**: ItemPickedUp

#### DropItemCommand

- **Handler**: DropItemCommandHandler
- **Input**: DropItemDto(player_sid: str, item_sid: str)
- **Output**: ActionResponse(message: "Action completed successfully")
- **Goes through**: Player aggregate, World aggregate (read)
- **Business rules enforced**:
  - Item exists in player's bag
  - Player at valid location
- **Events published**: ItemDropped

#### UseItemCommand

- **Handler**: UseItemCommandHandler
- **Input**: UseItemDto(player_sid: str, item_sid: str, action: str)
- **Output**: ActionResponse(message: "Action completed successfully")
- **Goes through**: Player aggregate, World aggregate (read)
- **Business rules enforced**:
  - Item exists at player's location or in bag (depending on action)
  - Action is available for item
  - Auto-collect gold if opening container
- **Events published**: ItemOpened, ItemClosed, ItemUsed, GoldCollected

#### QuitGameCommand

- **Handler**: QuitGameCommandHandler
- **Input**: QuitGameDto(player_sid: str)
- **Output**: QuitGameResponse(message: "Game Over")
- **Goes through**: Player aggregate
- **Business rules enforced**:
  - Player exists
  - Mark player as inactive before deletion
- **Events published**: GameEnded, PlayerRemoved

### Queries (Read Operations)

#### GetPlayerLocationQuery

- **Handler**: GetPlayerLocationQueryHandler
- **Input**: GetPlayerLocationDto(player_sid: str)
- **Output**: LocationResponse(description, exits, items)
- **Bypasses domain**: Yes
- **Data source**: player_location_view (joins player + world data)

#### LookInDirectionQuery

- **Handler**: LookInDirectionQueryHandler
- **Input**: LookInDirectionDto(player_sid: str, direction: str)
- **Output**: LocationResponse(description, exits, items)
- **Bypasses domain**: Yes
- **Data source**: world_navigation_view

#### GetItemDetailsQuery

- **Handler**: GetItemDetailsQueryHandler
- **Input**: GetItemDetailsDto(item_sid: str)
- **Output**: ItemResponse(sid, name, description, actions)
- **Bypasses domain**: Yes
- **Data source**: world_items_view

#### GetPlayerBagQuery

- **Handler**: GetPlayerBagQueryHandler
- **Input**: GetPlayerBagDto(player_sid: str)
- **Output**: BagResponse(items: List[ItemResponse], gold: int)
- **Bypasses domain**: Yes
- **Data source**: player_bag_view

### Driven Ports (Application needs)

- **TimeProviderPort**: Provide current timestamp
  - `now() -> datetime`

## Infrastructure Layer

### Driving Adapters (Entry Points)

#### FastApiGameController (HTTP)

- **Protocol**: HTTP REST API
- **Endpoints**:
  - `POST /game/player` → StartGameCommand
  - `PUT /player/{playerSid}/move/{direction}` → MovePlayerCommand
  - `GET /player/{playerSid}/location` → GetPlayerLocationQuery
  - `GET /player/{playerSid}/look/{direction}` → LookInDirectionQuery
  - `GET /player/items/{itemSid}` → GetItemDetailsQuery
  - `GET /player/{playerSid}/bag` → GetPlayerBagQuery
  - `PUT /player/{playerSid}/item/{itemSid}/use/{action}` → PickItemCommand/DropItemCommand/UseItemCommand
  - `DELETE /game/{playerSid}` → QuitGameCommand

### Driven Adapters (Exit Points)

#### InMemoryPlayerRepository

- **Technology**: Python dict (simple in-memory storage)
- **Implements**: PlayerRepository (domain)
- **Data**: `players: Dict[Sid, Player]`

#### InMemoryWorldRepository

- **Technology**: Python dict with pre-loaded game world
- **Implements**: WorldRepository (domain)
- **Data**: Single World aggregate with all locations and items
- **Initialization**: Load from YAML/JSON configuration file

#### SystemTimeProvider

- **Technology**: Python datetime.now()
- **Implements**: TimeProviderPort (application)
- **Returns**: Current system timestamp

### Database Schema

**Note**: Starting with in-memory implementation, but designed for future database migration.

**Write Model (Future - Normalized)**:

```sql
CREATE TABLE players (
    sid VARCHAR(25) PRIMARY KEY,  -- XXXXXX-XXXXXXXXXXXX-XXXXXXXX format
    name VARCHAR(50) NOT NULL,
    location_sid VARCHAR(25) NOT NULL,
    bag_items JSONB,  -- Array of item SIDs
    gold INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE world_config (
    id INTEGER PRIMARY KEY,
    world_data JSONB NOT NULL  -- Complete world configuration
);
```

**Read Model (Future - Denormalized Views)**:

```sql
CREATE VIEW player_location_view AS
SELECT
    p.sid as player_sid,
    p.name,
    p.location_sid,
    w.location_data->p.location_sid as current_location,
    p.bag_items,
    p.gold
FROM players p
CROSS JOIN (SELECT world_data FROM world_config LIMIT 1) w
WHERE p.is_active = true;

CREATE VIEW player_bag_view AS
SELECT
    p.sid as player_sid,
    p.bag_items,
    p.gold,
    w.world_data->'items' as world_items
FROM players p
CROSS JOIN (SELECT world_data FROM world_config LIMIT 1) w
WHERE p.is_active = true;
```

## CQRS Split

### Write Side

- **Commands**: StartGame, MovePlayer, PickItem, DropItem, UseItem, QuitGame
- **Through domain**: Yes - enforces all business rules and invariants
- **Aggregates**: Player (primary), World (read-only reference)
- **Storage**: Normalized player table + world configuration
- **Consistency**: Strong consistency within aggregate boundaries

### Read Side

- **Queries**: GetPlayerLocation, LookInDirection, GetItemDetails, GetPlayerBag
- **Bypass domain**: Yes - optimized for read performance
- **Storage**: Denormalized views joining player + world data
- **Consistency**: Eventually consistent (same database, real-time views)

## Testing Strategy

### Unit Tests

**Domain Layer**:

- Sid value object format validation
- PlayerName value object validation
- Bag capacity constraints and item management
- Player aggregate business methods (move_to_location, add_to_bag, etc.)
- World aggregate navigation methods
- MovementValidator and ItemActionValidator logic

**Application Layer**:

- StartGameCommandHandler orchestration (with mocked repositories)
- MovePlayerCommandHandler with mocked World and Player repositories
- All query handlers with mocked data sources

### Integration Tests

**Repository Tests**:

- InMemoryPlayerRepository save/find/delete operations
- InMemoryWorldRepository world loading and navigation
- Integration between Player and World aggregates

**Service Tests**:

- SystemTimeProvider returns correct timestamps

### Contract Tests

**HTTP API Tests**:

- POST /game/player returns 201 with correct schema on success
- POST /game/player returns 400 on invalid name/SID
- PUT /player/{sid}/move/{direction} returns 200 on valid move
- PUT /player/{sid}/move/{direction} returns 405 on blocked direction
- GET endpoints return correct JSON schemas
- All endpoints return 404 for non-existent players

### Acceptance Tests

**Complete User Journey Tests**:

- Full game flow: Start → Move → Look → Pick items → Drop items → Quit
- Multi-player scenarios: Multiple active players
- Error handling: Invalid inputs at each step
- Edge cases: Full bag, non-existent items, blocked moves

## Implementation Order (Outside-In TDD - Pedro's Algorithm)

**Following London School TDD - Start from outside and work inward:**

### Phase 1: Story 1 (Start Game) - Foundation

1. **Acceptance Test Sketch** (RED) - Outline `test_start_game_acceptance()`

   - Sketch: POST /game/player → Player created → Starting location assigned
   - Identify needed ports: PlayerRepository, WorldRepository
   - Test fails to compile (ports don't exist yet)

2. **Infrastructure Port Interfaces** (CRITICAL: Define BEFORE acceptance test can run)

   - `PlayerRepository` interface (`save`, `find_by_sid`)
   - `WorldRepository` interface (`get_world`)
   - **Without these defined, cannot create test doubles!**

3. **Acceptance Test** (RED) - Complete `test_start_game_acceptance()` with fakes/mocks

   - `fake_player_repo = FakePlayerRepository()`
   - `fake_world_repo = FakeWorldRepository()`
   - Test executes but fails (StartGameCommandHandler not implemented)

4. **StartGameCommandHandler** - Application orchestration layer

5. **Domain Objects** (emerge from use case needs):

   - Sid value object (validation)
   - PlayerName value object (validation)
   - Player aggregate with business methods
   - World aggregate with location navigation
   - Bag value object with capacity constraints
   - GameStarted, PlayerCreated domain events

6. **Repository Interfaces** (domain ports) - Already defined in step 2

7. **Integration Tests** - `test_inmemory_player_repository_integration()`

8. **Repository Implementations**:

   - InMemoryPlayerRepository (driven adapter)
   - InMemoryWorldRepository with game data loading

9. **External Service Adapters**:

   - SystemSidGenerator implementation

10. **FastApiGameController** - POST /game/player endpoint (driving adapter)

11. **Contract Tests** - HTTP endpoint contract validation

### Phase 2: Story 2 (Move Through Locations) - Core Mechanics

1. **Acceptance Test Sketch** - `test_move_player_acceptance()`
2. **MovementValidator** domain service
3. **MovePlayerCommandHandler**
4. **Direction value object and validation**
5. **Player.move_to_location()** domain method
6. **PlayerMovedToLocation** domain event
7. **PUT /player/{sid}/move/{direction}** endpoint

### Phase 3: Story 3 (Look Around) - Information Discovery

1. **Acceptance Test Sketch** - `test_look_around_acceptance()`
2. **Query handlers** (bypass domain, direct data access)
3. **GetPlayerLocationQueryHandler**
4. **LookInDirectionQueryHandler**
5. **GetItemDetailsQueryHandler**
6. **GET endpoints** for location and item queries

### Phase 4: Story 4 (Manage Inventory) - Item Interaction

1. **Acceptance Test Sketch** - `test_inventory_management_acceptance()`
2. **ItemActionValidator** domain service
3. **PickItemCommandHandler** and **DropItemCommandHandler**
4. **Bag value object** methods (add_item, remove_item, is_full)
5. **Item pickup/drop domain methods** on Player aggregate
6. **Item-related domain events**
7. **Bag query handler** and **GET /player/{sid}/bag** endpoint

### Phase 5: Story 5 (Use Items) - Advanced Interactions

1. **Acceptance Test Sketch** - `test_use_items_acceptance()`
2. **UseItemCommandHandler** with action-specific logic
3. **Action value object** and validation
4. **Item interaction domain methods** (open, close, use)
5. **Gold collection logic** for containers
6. **PUT /player/{sid}/item/{itemSid}/use/{action}** endpoint

### Phase 6: Story 6 (Quit Game) - Lifecycle Management

1. **Acceptance Test Sketch** - `test_quit_game_acceptance()`
2. **QuitGameCommandHandler**
3. **Player.quit_game()** domain method
4. **GameEnded, PlayerRemoved** domain events
5. **DELETE /game/{playerSid}** endpoint

## Sequence Diagrams

### Start Game Flow

```txt
Client → FastApiController → StartGameCommandHandler → Player(new) → PlayerRepository → Database
                                     ↓
                            WorldRepository → World → starting_location
                                     ↓
                            DomainEvent → GameStarted
```

### Move Player Flow

```txt
Client → FastApiController → MovePlayerCommandHandler → PlayerRepository → Player(loaded)
                                     ↓                         ↓
                            WorldRepository → World → validate_exit → Player.move_to_location()
                                     ↓                         ↓
                            PlayerRepository → save → DomainEvent → PlayerMovedToLocation
```

### Look Around Flow (Query)

```txt
Client → FastApiController → GetPlayerLocationQueryHandler → PlayerLocationView → Response
                                     ↓ (bypass domain)
                            DirectQuery → JoinedData → LocationResponse
```

## Dependencies

### External Systems

- **None initially** - Self-contained game with in-memory storage
- **Future**: Database (PostgreSQL), Logging service, Monitoring

### Driven Ports Needed

- **PlayerRepository**: Abstract player persistence
- **WorldRepository**: Abstract world configuration loading
- **TimeProviderPort**: Abstract time provider for testing

## Decision Guidelines Applied

### Aggregate Boundaries

- ✅ **Player**: Independent identity, lifecycle, transactional boundary for player state
- ✅ **World**: Read-only aggregate, separate lifecycle, immutable during gameplay
- ❌ **Location as separate aggregate**: No - Location is entity within World aggregate

### CQRS Split Rationale

- **Commands**: All player actions modify state → Go through domain for business rule validation
- **Queries**: Location viewing, item inspection → Bypass domain for performance, use direct views

### Repository Pattern

- ✅ **PlayerRepository**: One repository per aggregate root (Player)
- ✅ **WorldRepository**: One repository per aggregate root (World)
- ❌ **LocationRepository**: Wrong - Location is entity within World aggregate

## Key Architectural Decisions

1. **In-Memory Start**: Begin with simple in-memory storage, design for future database migration
2. **Immutable World**: Game world is read-only during gameplay for consistency
3. **Bag as Value Object**: Encapsulates capacity rules and item management logic
4. **Domain Events**: Enable future features (notifications, statistics, auditing)
5. **Clear CQRS**: Commands enforce business rules, queries optimize for reads
6. **Testable Design**: All external dependencies abstracted behind ports

This architecture provides a solid foundation for the Katacombs API while maintaining flexibility for future enhancements and scaling requirements.
