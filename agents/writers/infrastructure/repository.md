# Repository Implementer Agent

Implement database-specific repositories using the Memento pattern to preserve rich domain model encapsulation.

## The Memento Pattern for Domain Persistence

The memento pattern allows aggregates to expose their internal state for persistence without breaking encapsulation. The aggregate creates a snapshot (memento) of its state and can later restore from that snapshot.

### Why Memento Over ORM Mapping?

- **Preserves Encapsulation**: No need to expose internal fields or break domain invariants
- **Rich Domain Models**: Domain objects remain focused on behavior, not persistence concerns
- **Clean Separation**: Persistence logic completely separated from domain logic
- **Framework Independence**: Works with any persistence technology (SQL, NoSQL, files)
- **Testability**: Easy to test domain logic without persistence concerns

## Template

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Domain-defined memento (what the aggregate exposes)
@dataclass(frozen=True)
class [Aggregate]Snapshot:
    """Memento containing aggregate's state for persistence"""
    # Root entity data
    aggregate_id: str
    [aggregate_fields]: Any

    # Internal entities data (as primitive structures)
    [internal_entities]: List[Dict[str, Any]]

    # Version for optimistic concurrency
    version: int

    # Metadata
    created_at: str
    updated_at: str

# Repository interface (in domain layer)
class [Aggregate]Repository(ABC):
    @abstractmethod
    def save(self, aggregate: [Aggregate]) -> None:
        pass

    @abstractmethod
    def find_by_id(self, aggregate_id: [AggregateId]) -> Optional[[Aggregate]]:
        pass

# Infrastructure implementation
class [Technology][Aggregate]Repository([Aggregate]Repository):
    def __init__(self, connection):
        self._connection = connection

    def save(self, aggregate: [Aggregate]) -> None:
        """Save aggregate using its memento"""
        # 1. Get snapshot from aggregate (memento pattern)
        snapshot = aggregate.create_snapshot()

        # 2. Convert to storage format
        storage_data = self._snapshot_to_storage(snapshot)

        # 3. Persist to database
        self._persist_to_database(storage_data)

    def find_by_id(self, aggregate_id: [AggregateId]) -> Optional[[Aggregate]]:
        """Load aggregate from its memento"""
        # 1. Load from database
        storage_data = self._load_from_database(aggregate_id.value)
        if not storage_data:
            return None

        # 2. Convert to snapshot
        snapshot = self._storage_to_snapshot(storage_data)

        # 3. Restore aggregate from snapshot
        return [Aggregate].restore_from_snapshot(snapshot)

    def _snapshot_to_storage(self, snapshot: [Aggregate]Snapshot) -> Dict[str, Any]:
        """Convert domain snapshot to storage format"""
        return {
            'aggregate_id': snapshot.aggregate_id,
            'aggregate_data': {
                '[field]': snapshot.[field],
                # Map other aggregate fields
            },
            'internal_entities': snapshot.[internal_entities],
            'version': snapshot.version,
            'created_at': snapshot.created_at,
            'updated_at': snapshot.updated_at
        }

    def _storage_to_snapshot(self, storage_data: Dict[str, Any]) -> [Aggregate]Snapshot:
        """Convert storage format to domain snapshot"""
        return [Aggregate]Snapshot(
            aggregate_id=storage_data['aggregate_id'],
            [field]=storage_data['aggregate_data']['[field]'],
            [internal_entities]=storage_data['internal_entities'],
            version=storage_data['version'],
            created_at=storage_data['created_at'],
            updated_at=storage_data['updated_at']
        )

    def _persist_to_database(self, storage_data: Dict[str, Any]) -> None:
        """Technology-specific persistence logic"""
        # SQL example:
        # self._connection.execute(
        #     "INSERT OR REPLACE INTO aggregates (id, data) VALUES (?, ?)",
        #     (storage_data['aggregate_id'], json.dumps(storage_data))
        # )

        # NoSQL example:
        # self._collection.replace_one(
        #     {'_id': storage_data['aggregate_id']},
        #     storage_data,
        #     upsert=True
        # )
        pass

    def _load_from_database(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """Technology-specific loading logic"""
        # SQL example:
        # row = self._connection.execute(
        #     "SELECT data FROM aggregates WHERE id = ?",
        #     (aggregate_id,)
        # ).fetchone()
        # return json.loads(row[0]) if row else None

        # NoSQL example:
        # return self._collection.find_one({'_id': aggregate_id})
        pass
```

## Domain Aggregate Implementation

The aggregate must implement memento creation and restoration:

```python
@dataclass
class [Aggregate]:
    # Private fields (encapsulated)
    _id: [AggregateId]
    _[fields]: [Type]
    _[internal_entities]: List[[InternalEntity]]
    _version: int = field(default=0, init=False)

    def create_snapshot(self) -> [Aggregate]Snapshot:
        """Create memento of current state"""
        return [Aggregate]Snapshot(
            aggregate_id=self._id.value,
            [field]=self._[field],
            [internal_entities]=[
                {
                    'local_id': entity.local_id.value,
                    '[entity_field]': entity.[entity_field],
                    # Serialize all entity state as primitives
                }
                for entity in self._[internal_entities]
            ],
            version=self._version,
            created_at=self._created_at.isoformat(),
            updated_at=datetime.now().isoformat()
        )

    @classmethod
    def restore_from_snapshot(cls, snapshot: [Aggregate]Snapshot) -> '[Aggregate]':
        """Restore aggregate from memento"""
        # Restore internal entities
        internal_entities = [
            [InternalEntity](
                local_id=[LocalId](entity_data['local_id']),
                [entity_field]=entity_data['[entity_field]'],
                # Restore all entity fields
            )
            for entity_data in snapshot.[internal_entities]
        ]

        # Create aggregate instance
        aggregate = cls.__new__(cls)  # Skip __init__ validation
        aggregate._id = [AggregateId](snapshot.aggregate_id)
        aggregate._[field] = snapshot.[field]
        aggregate._[internal_entities] = internal_entities
        aggregate._version = snapshot.version
        aggregate._created_at = datetime.fromisoformat(snapshot.created_at)

        # Validate restored state
        aggregate._validate_all_invariants()

        return aggregate
```

## Complete Example: Order Aggregate with Memento

```python
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Memento (snapshot)
@dataclass(frozen=True)
class OrderSnapshot:
    aggregate_id: str
    customer_id: str
    status: str
    line_items: List[Dict[str, Any]]
    version: int
    created_at: str
    updated_at: str

# Domain aggregate with memento support
@dataclass
class Order:
    _id: OrderId
    _customer_id: CustomerId
    _status: OrderStatus = field(default=OrderStatus.PENDING, init=False)
    _line_items: List[OrderLineItem] = field(default_factory=list, init=False)
    _version: int = field(default=0, init=False)
    _created_at: datetime = field(default_factory=datetime.now, init=False)

    def add_line_item(self, product_id: ProductId, quantity: int, unit_price: Money) -> None:
        # Business logic (unchanged)
        if self._status != OrderStatus.PENDING:
            raise ValueError("Cannot add items to confirmed order")

        line_item = OrderLineItem(product_id, quantity, unit_price)
        self._line_items.append(line_item)
        self._version += 1

    def create_snapshot(self) -> OrderSnapshot:
        """Create memento for persistence"""
        return OrderSnapshot(
            aggregate_id=self._id.value,
            customer_id=self._customer_id.value,
            status=self._status.value,
            line_items=[
                {
                    'product_id': item.product_id.value,
                    'quantity': item.quantity,
                    'unit_price_amount': str(item.unit_price.amount),
                    'unit_price_currency': item.unit_price.currency
                }
                for item in self._line_items
            ],
            version=self._version,
            created_at=self._created_at.isoformat(),
            updated_at=datetime.now().isoformat()
        )

    @classmethod
    def restore_from_snapshot(cls, snapshot: OrderSnapshot) -> 'Order':
        """Restore from memento"""
        # Restore line items
        line_items = [
            OrderLineItem(
                product_id=ProductId(item_data['product_id']),
                quantity=item_data['quantity'],
                unit_price=Money(
                    amount=Decimal(item_data['unit_price_amount']),
                    currency=item_data['unit_price_currency']
                )
            )
            for item_data in snapshot.line_items
        ]

        # Create instance without running __init__
        order = cls.__new__(cls)
        order._id = OrderId(snapshot.aggregate_id)
        order._customer_id = CustomerId(snapshot.customer_id)
        order._status = OrderStatus(snapshot.status)
        order._line_items = line_items
        order._version = snapshot.version
        order._created_at = datetime.fromisoformat(snapshot.created_at)

        return order

# Repository implementation
class SqlOrderRepository(OrderRepository):
    def __init__(self, connection):
        self._connection = connection

    def save(self, order: Order) -> None:
        snapshot = order.create_snapshot()
        storage_data = {
            'id': snapshot.aggregate_id,
            'customer_id': snapshot.customer_id,
            'status': snapshot.status,
            'line_items': json.dumps(snapshot.line_items),
            'version': snapshot.version,
            'created_at': snapshot.created_at,
            'updated_at': snapshot.updated_at
        }

        self._connection.execute("""
            INSERT OR REPLACE INTO orders
            (id, customer_id, status, line_items, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(storage_data.values()))

    def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        row = self._connection.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id.value,)
        ).fetchone()

        if not row:
            return None

        snapshot = OrderSnapshot(
            aggregate_id=row['id'],
            customer_id=row['customer_id'],
            status=row['status'],
            line_items=json.loads(row['line_items']),
            version=row['version'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

        return Order.restore_from_snapshot(snapshot)
```

## Key Benefits

### 1. **Encapsulation Preserved**

- Domain objects remain fully encapsulated
- No need for public setters or ORM annotations
- Business logic stays pure

### 2. **Framework Independence**

- Works with any persistence technology
- Easy to switch from SQL to NoSQL to files
- No ORM framework coupling

### 3. **Optimistic Concurrency**

- Version field enables optimistic locking
- Concurrent modification detection

### 4. **Testability**

- Domain logic completely separate from persistence
- Easy to test snapshots in isolation
- Mock repositories trivial to implement

### 5. **Performance**

- Minimal object creation overhead
- Efficient serialization/deserialization
- Control over what gets persisted

## Implementation Guidelines

### 1. **Snapshot Design**

- Use primitive types only (strings, numbers, lists, dicts)
- Keep snapshots immutable (frozen dataclass)
- Include version for concurrency control

### 2. **Aggregate Responsibilities**

- `create_snapshot()` - expose current state
- `restore_from_snapshot()` - reconstitute from state
- Skip validation during restoration, validate after

### 3. **Repository Responsibilities**

- Convert between snapshot and storage format
- Handle technology-specific persistence
- Manage transactions and error handling

### 4. **Technology Mapping**

- SQL: JSON columns or separate tables
- NoSQL: Direct document storage
- Files: Serialized formats (JSON, XML, binary)

Follow RULES.md Section 6 for repository interfaces and dependency inversion.
