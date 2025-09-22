# Domain Driven Design with Ports & Adapters Rules

## TL;DR: How to: DDD and Ports & Adapters Work Together

This document defines three complementary approaches that work together to create maintainable, testable applications across multiple programming languages.

- Domain Driven Design (DDD)
- Hexagonal Architecture or Ports & Adapters Architecture.
- Command Query Responsability Segregations (CQRS)

Note: I used an LLM to convert the examples from Python to other languages, some of them I don't know well enough to judge on the quality of the examples.

### The Integration Pattern

```txt
                               HEXAGONAL ARCHITECTURE
                                 (Ports & Adapters)

                                  External Systems
                                ┌─────────────────┐
                                │   REST Client   │
                                │   Web Browser   │
                                │   CLI Command   │
                                └─────────────────┘
                                        │
                                        │ HTTP/CLI
                                        ▼
                                ┌─────────────────┐
                                │ Driving Adapter │
                                │  (Controllers)  │
                                └─────────────────┘
                                        │
                                        │ Domain Commands
                                        ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                          APPLICATION LAYER                          │
    │           ┌─────────────────┐          ┌─────────────────┐          │
    │           │    Use Case     │          │    Use Case     │          │
    │           │   (Register)    │          │   (Find User)   │          │
    │           └─────────────────┘          └─────────────────┘          │
    └──────────────────────────────────┬──────────────────────────────────┘
                                       │ Domain Operations
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                      DOMAIN LAYER (DDD Core)                        │
    │    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
    │    │    Aggregate    │  │  Value Object   │  │  Domain Event   │    │
    │    │      (User)     │  │    (Email)      │  │ (UserRegistered)│    │
    │    └─────────────────┘  └─────────────────┘  └─────────────────┘    │
    │                                                                     │
    │    ┌─────────────────┐  ┌─────────────────┐                         │
    │    │ Domain Service  │  │  Driven Port    │                         │
    │    │ (UserValidator) │  │ (UserRepository)│   (Exit Points)         │
    │    └─────────────────┘  └─────────────────┘   Interface only        │
    └─────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ External Operations
                                        ▼
                                ┌─────────────────┐
                                │ Driven Adapter  │
                                │ (Repositories)  │
                                └─────────────────┘
                                         │
                                         │ (SQL)
                                         ▼
                                 External Systems
                                ┌─────────────────┐
                                │    Database     │
                                │   Email API     │
                                │   File System   │
                                └─────────────────┘
```

**Core Domain Model** (Rules 1-14) focuses on business logic and domain concepts:

- **Entities** (Rule 1) contain business behavior and have unique identity
- **Value Objects** (Rule 2) represent immutable domain concepts
- **Aggregates** (Rule 3) enforce business invariants and transaction boundaries
- **Domain Services** (Rule 4) handle business logic spanning multiple entities
- **Use Cases** (Rule 9) orchestrate domain objects without containing business logic

**Ports & Adapters** (Rules 1-12) focuses on architectural boundaries and external concerns:

- **Driving Ports** define what your application can do AKA "**Entry Points**" (use case interfaces)
- **Driven Ports** define what your application needs AKA "**Exit Points**" (repositories, external services)
- **Driving Adapters** translate external requests into domain operations (REST controllers, CLI)
- **Driven Adapters** implement external integrations (databases, APIs, file systems)

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

#### Entity Rules - Examples

**Python:**

```python
@dataclass
class User:
    id: UserId = field(init=False)
    email: Email
    name: str

    def __post_init__(self):
        if not hasattr(self, 'id'):
            self.id = UserId.generate()

    def change_email(self, new_email: Email) -> UserEmailChanged:
        # Business logic here
        old_email = self.email
        self.email = new_email
        return UserEmailChanged(self.id, old_email, new_email)
```

**TypeScript:**

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

  changeEmail(newEmail: Email): UserEmailChanged {
    // Business logic here
    const oldEmail = this._email;
    this._email = newEmail;
    return new UserEmailChanged(this.id, oldEmail, newEmail);
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
```

**Java:**

```java
public class User extends Entity<UserId> {
    private Email email;
    private String name;

    protected User() {
        // Required by JPA/Hibernate
    }

    public User(UserId id, Email email, String name) {
        super(id);
        this.email = Objects.requireNonNull(email, "Email cannot be null");
        this.name = Objects.requireNonNull(name, "Name cannot be null");
        validate();
    }

    public static User create(Email email, String name) {
        return new User(UserId.generate(), email, name);
    }

    public UserEmailChanged changeEmail(Email newEmail) {
        // Business logic here
        Objects.requireNonNull(newEmail, "Email cannot be null");
        Email oldEmail = this.email;
        this.email = newEmail;
        return new UserEmailChanged(getId(), oldEmail, newEmail, Instant.now());
    }

    public Email getEmail() { return email; }
    public String getName() { return name; }

    private void validate() {
        if (email == null || name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("User must have valid email and name");
        }
    }
}
```

**C#:**

```csharp
public class User : Entity<UserId>
{
    private Email _email;
    private string _name;

    public User(UserId id, Email email, string name) : base(id)
    {
        _email = email ?? throw new ArgumentNullException(nameof(email));
        _name = name ?? throw new ArgumentNullException(nameof(name));
        Validate();
    }

    public static User Create(Email email, string name)
    {
        return new User(UserId.Generate(), email, name);
    }

    public UserEmailChanged ChangeEmail(Email newEmail)
    {
        // Business logic here
        var oldEmail = _email;
        _email = newEmail ?? throw new ArgumentNullException(nameof(newEmail));
        return new UserEmailChanged(Id, oldEmail, newEmail, DateTime.UtcNow);
    }

    public Email Email => _email;
    public string Name => _name;

    private void Validate()
    {
        if (_email is null || string.IsNullOrWhiteSpace(_name))
        {
            throw new InvalidOperationException("User must have email and name");
        }
    }
}
```

**Rust:**

```rust
#[derive(Debug, Clone)]
pub struct User {
    id: UserId,
    email: Email,
    name: String,
}

impl User {
    pub fn new(id: UserId, email: Email, name: String) -> Result<Self, DomainError> {
        let user = Self { id, email, name };
        user.validate()?;
        Ok(user)
    }

    pub fn create(email: Email, name: String) -> Result<Self, DomainError> {
        Self::new(UserId::new(), email, name)
    }

    pub fn change_email(&mut self, new_email: Email) -> UserEmailChanged {
        let old_email = self.email.clone();
        self.email = new_email.clone();
        UserEmailChanged::new(self.id.clone(), old_email, new_email)
    }

    pub fn id(&self) -> &UserId { &self.id }
    pub fn email(&self) -> &Email { &self.email }
    pub fn name(&self) -> &str { &self.name }

    fn validate(&self) -> Result<(), DomainError> {
        if self.name.trim().is_empty() {
            return Err(DomainError::Validation("User must have a name".to_string()));
        }
        Ok(())
    }
}

// Equality based on identity only
impl PartialEq for User {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}
```

**Go:**

```go
type User struct {
    id    UserID
    email Email
    name  string
}

func NewUser(id UserID, email Email, name string) (*User, error) {
    if err := email.Validate(); err != nil {
        return nil, err
    }
    if name == "" {
        return nil, errors.New("name cannot be empty")
    }
    user := &User{id: id, email: email, name: name}
    return user, nil
}

func CreateUser(email Email, name string) (*User, error) {
    return NewUser(GenerateUserID(), email, name)
}

// Business behavior - not just getters and setters
func (u *User) ChangeEmail(newEmail Email) (*UserEmailChanged, error) {
    if err := newEmail.Validate(); err != nil {
        return nil, fmt.Errorf("invalid email: %w", err)
    }
    oldEmail := u.email
    u.email = newEmail
    return &UserEmailChanged{
        UserID:     u.id,
        OldEmail:   oldEmail,
        NewEmail:   newEmail,
        OccurredAt: time.Now(),
    }, nil
}

func (u *User) ID() UserID { return u.id }
func (u *User) Email() Email { return u.email }
func (u *User) Name() string { return u.name }

func (u *User) Equals(other *User) bool {
    if other == nil {
        return false
    }
    return u.id.Equals(other.id)
}
```

### 2. Value Object Rules

- Value objects MUST be immutable
- Equality is based on ALL attributes, not identity
- Should be small, focused, and represent a concept from the domain
- Include validation in constructor
- Should have meaningful methods that operate on the value

#### Value Object Rules - Examples

**Python:**

```python
@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if '@' not in self.value:
            raise ValueError("Invalid email format")

    @property
    def domain(self) -> str:
        return self.value.split('@')[1]

    def is_from_domain(self, domain: str) -> bool:
        return self.domain == domain
```

**TypeScript:**

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

**Java:**

```java
public record Email(String value) {
    public Email {
        if (value == null || !value.contains("@")) {
            throw new IllegalArgumentException("Invalid email format: " + value);
        }
    }

    public String getDomain() {
        return value.split("@")[1];
    }

    public boolean isFromDomain(String domain) {
        return getDomain().equals(domain);
    }
}
```

**C#:**

```csharp
public sealed record Email
{
    public Email(string value)
    {
        if (string.IsNullOrWhiteSpace(value) || !value.Contains('@'))
        {
            throw new InvalidEmailException(value);
        }
        Value = value;
    }

    public string Value { get; }

    public string Domain => Value.Split('@')[1];

    public bool IsFromDomain(string domain) => Domain.Equals(domain, StringComparison.OrdinalIgnoreCase);

    public override string ToString() => Value;
}
```

**Rust:**

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email {
    value: String,
}

impl Email {
    pub fn new(value: &str) -> Result<Self, InvalidEmailError> {
        if !Self::is_valid_email(value) {
            return Err(InvalidEmailError::new(value));
        }
        Ok(Self {
            value: value.to_lowercase(),
        })
    }

    pub fn value(&self) -> &str {
        &self.value
    }

    pub fn domain(&self) -> &str {
        self.value.split('@').nth(1).unwrap()
    }

    pub fn local_part(&self) -> &str {
        self.value.split('@').next().unwrap()
    }

    fn is_valid_email(value: &str) -> bool {
        let email_regex = regex::Regex::new(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
            .unwrap();
        email_regex.is_match(value)
    }
}

impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.value)
    }
}
```

**Go:**

```go
type Email struct {
    value string
}

func NewEmail(value string) (Email, error) {
    if !strings.Contains(value, "@") {
        return Email{}, errors.New("invalid email format")
    }
    return Email{value: strings.ToLower(value)}, nil
}

func (e Email) Value() string {
    return e.value
}

func (e Email) Domain() string {
    parts := strings.Split(e.value, "@")
    if len(parts) != 2 {
        return ""
    }
    return parts[1]
}

func (e Email) IsFromDomain(domain string) bool {
    return e.Domain() == domain
}

func (e Email) Validate() error {
    if !strings.Contains(e.value, "@") {
        return errors.New("invalid email format")
    }
    return nil
}

func (e Email) Equals(other Email) bool {
    return e.value == other.value
}

func (e Email) String() string {
    return e.value
}
```

### 3. Aggregate Rules

Aggregates are clusters of domain objects that are treated as a single unit. Ensure that all changes to the domain model are done through aggregates. This means that Entities are not directly modified, but rather through the Aggregate Root.

- Aggregates MUST have a single Aggregate Root (an Entity)
- Only the Aggregate Root should be directly accessible from outside
- Internal entities within an aggregate should be accessed only through the root
- Aggregate boundaries should align with transaction boundaries
- Use factory methods on aggregates for complex creation logic
- Aggregates should be small and focused
- The root Entity has global identity and is ultimately responsible for checking invariants
- Root Entities have global identity. Entities inside the boundary have local identity, unique only within the Aggregate
- Nothing outside the Aggregate boundary can hold a reference to anything inside, except to the root Entity
- Only Aggregate Roots can be obtained directly with database queries. Everything else must be done through traversal
- Objects within the Aggregate can hold references to other Aggregate roots
- A delete operation must remove everything within the Aggregate boundary all at once
- When a change to any object within the Aggregate boundary is committed, all invariants of the whole Aggregate must be satisfied
- Hide Internal State: Keep the internal state of the aggregate private and provide methods to interact with the state safely
- Encapsulate Collections: Use first class collection encapsulation

#### Examples

**Python:**

```python
@dataclass
class Order:  # Aggregate Root
    id: OrderId
    customer_id: CustomerId
    _line_items: list[OrderLineItem] = field(default_factory=list, init=False)
    status: OrderStatus = field(default=OrderStatus.PENDING, init=False)

    def add_line_item(self, product_id: ProductId, quantity: int, unit_price: Money) -> None:
        # Business rules and validation
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot add items to non-pending order")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        line_item = OrderLineItem(product_id, quantity, unit_price)
        self._line_items.append(line_item)

    def confirm(self) -> None:
        if not self._line_items:
            raise ValueError("Cannot confirm empty order")
        self.status = OrderStatus.CONFIRMED

    @property
    def line_items(self) -> tuple[OrderLineItem, ...]:
        return tuple(self._line_items)  # Return immutable view

    def total(self) -> Money:
        return sum((item.subtotal() for item in self._line_items), Money.zero())
```

**TypeScript:**

```typescript
class Order extends Entity<OrderId> {
  // Aggregate Root
  private readonly _customerId: CustomerId;
  private readonly _lineItems: OrderLineItem[] = [];
  private _status: OrderStatus = OrderStatus.PENDING;

  constructor(id: OrderId, customerId: CustomerId) {
    super(id);
    this._customerId = customerId;
  }

  addLineItem(productId: ProductId, quantity: number, unitPrice: Money): void {
    // Business rules and validation
    if (this._status !== OrderStatus.PENDING) {
      throw new Error('Cannot add items to non-pending order');
    }

    if (quantity <= 0) {
      throw new Error('Quantity must be positive');
    }

    const lineItem = new OrderLineItem(productId, quantity, unitPrice);
    this._lineItems.push(lineItem);
  }

  confirm(): void {
    if (this._lineItems.length === 0) {
      throw new Error('Cannot confirm empty order');
    }
    this._status = OrderStatus.CONFIRMED;
  }

  get lineItems(): readonly OrderLineItem[] {
    return Object.freeze([...this._lineItems]); // Return immutable view
  }

  get customerId(): CustomerId {
    return this._customerId;
  }

  get status(): OrderStatus {
    return this._status;
  }
}
```

**Java:**

```java
public class Order extends Entity<OrderId> {
    // Aggregate Root
    private final CustomerId customerId;
    private final List<OrderLineItem> lineItems = new ArrayList<>();
    private OrderStatus status = OrderStatus.PENDING;

    protected Order() {
        // For JPA/Hibernate
    }

    public Order(OrderId id, CustomerId customerId) {
        super(id);
        this.customerId = Objects.requireNonNull(customerId, "Customer ID cannot be null");
    }

    public static Order create(CustomerId customerId) {
        return new Order(OrderId.generate(), customerId);
    }

    public void addLineItem(ProductId productId, int quantity, Money unitPrice) {
        // Business rules and validation
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("Cannot add items to non-pending order");
        }

        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }

        OrderLineItem lineItem = new OrderLineItem(productId, quantity, unitPrice);
        lineItems.add(lineItem);
    }

    public void confirm() {
        if (lineItems.isEmpty()) {
            throw new IllegalStateException("Cannot confirm empty order");
        }
        status = OrderStatus.CONFIRMED;
    }

    public List<OrderLineItem> getLineItems() {
        return Collections.unmodifiableList(lineItems); // Return immutable view
    }

    public CustomerId getCustomerId() {
        return customerId;
    }

    public OrderStatus getStatus() {
        return status;
    }
}
```

**C#:**

```csharp
public class Order : Entity<OrderId>
{
    // Aggregate Root
    private readonly CustomerId _customerId;
    private readonly List<OrderLineItem> _lineItems = new();
    private OrderStatus _status = OrderStatus.Pending;

    public Order(OrderId id, CustomerId customerId) : base(id)
    {
        _customerId = customerId;
    }

    public void AddLineItem(ProductId productId, int quantity, Money unitPrice)
    {
        // Business rules and validation
        if (_status != OrderStatus.Pending)
        {
            throw new InvalidOperationException("Cannot add items to non-pending order");
        }

        if (quantity <= 0)
        {
            throw new ArgumentException("Quantity must be positive");
        }

        var lineItem = new OrderLineItem(productId, quantity, unitPrice);
        _lineItems.Add(lineItem);
    }

    public void Confirm()
    {
        if (_lineItems.Count == 0)
        {
            throw new InvalidOperationException("Cannot confirm empty order");
        }
        _status = OrderStatus.Confirmed;
    }

    public IReadOnlyList<OrderLineItem> LineItems => _lineItems.AsReadOnly();
    public CustomerId CustomerId => _customerId;
    public OrderStatus Status => _status;
}
```

**Rust:**

```rust
#[derive(Debug, Clone)]
pub struct Order {
    // Aggregate Root
    id: OrderId,
    customer_id: CustomerId,
    line_items: Vec<OrderLineItem>,
    status: OrderStatus,
}

impl Order {
    pub fn new(id: OrderId, customer_id: CustomerId) -> Self {
        Self {
            id,
            customer_id,
            line_items: Vec::new(),
            status: OrderStatus::Pending,
        }
    }

    pub fn add_line_item(&mut self, product_id: ProductId, quantity: u32, unit_price: Money) -> Result<(), DomainError> {
        // Business rules and validation
        if self.status != OrderStatus::Pending {
            return Err(DomainError::Validation("Cannot add items to non-pending order".to_string()));
        }

        if quantity == 0 {
            return Err(DomainError::Validation("Quantity must be positive".to_string()));
        }

        let line_item = OrderLineItem::new(product_id, quantity, unit_price)?;
        self.line_items.push(line_item);
        Ok(())
    }

    pub fn confirm(&mut self) -> Result<(), DomainError> {
        if self.line_items.is_empty() {
            return Err(DomainError::Validation("Cannot confirm empty order".to_string()));
        }
        self.status = OrderStatus::Confirmed;
        Ok(())
    }

    pub fn line_items(&self) -> &[OrderLineItem] {
        &self.line_items
    }

    pub fn id(&self) -> &OrderId { &self.id }
    pub fn customer_id(&self) -> &CustomerId { &self.customer_id }
    pub fn status(&self) -> OrderStatus { self.status }
}
```

**Go:**

```go
// Order is the Aggregate Root
type Order struct {
    id         OrderID
    customerID CustomerID
    lineItems  []*OrderLineItem
    status     OrderStatus
}

func NewOrder(id OrderID, customerID CustomerID) *Order {
    return &Order{
        id:         id,
        customerID: customerID,
        lineItems:  make([]*OrderLineItem, 0),
        status:     OrderStatusPending,
    }
}

func CreateOrder(customerID CustomerID) *Order {
    return NewOrder(GenerateOrderID(), customerID)
}

// Business logic through the aggregate root
func (o *Order) AddLineItem(productID ProductID, quantity int, unitPrice Money) error {
    // Business rules and validation
    if o.status != OrderStatusPending {
        return errors.New("cannot add items to non-pending order")
    }

    if quantity <= 0 {
        return errors.New("quantity must be positive")
    }

    lineItem, err := NewOrderLineItem(productID, quantity, unitPrice)
    if err != nil {
        return fmt.Errorf("failed to create line item: %w", err)
    }

    o.lineItems = append(o.lineItems, lineItem)
    return nil
}

func (o *Order) Confirm() error {
    if len(o.lineItems) == 0 {
        return errors.New("cannot confirm empty order")
    }
    o.status = OrderStatusConfirmed
    return nil
}

// Return immutable view of line items
func (o *Order) LineItems() []*OrderLineItem {
    items := make([]*OrderLineItem, len(o.lineItems))
    copy(items, o.lineItems)
    return items
}

func (o *Order) ID() OrderID { return o.id }
func (o *Order) CustomerID() CustomerID { return o.customerID }
func (o *Order) Status() OrderStatus { return o.status }
```

### 4. Domain Service Rules

Handles business logic that spans multiple entities (e.g., transferring money between two accounts)

- Create domain services ONLY when business logic doesn't naturally fit in entities or value objects
- Domain services should be stateless
- Use dependency injection for external dependencies
- Should operate on domain objects, not primitives
- Should not use Driven ports/adapters
- Name services with domain language (not technical terms)

#### Domain Service Rules - Examples

**Python:**

```python
class PricingService:
    def __init__(self, discount_repository: DiscountRepository):
        self._discount_repository = discount_repository

    def calculate_order_total(self, order: Order, customer: Customer) -> Money:
        # Complex pricing logic that spans multiple aggregates
        base_total = order.total()

        applicable_discounts = self._discount_repository.find_applicable_discounts(
            customer.id, order.line_items
        )

        total_discount = sum(
            discount.calculate_discount(base_total)
            for discount in applicable_discounts
        )

        return base_total - total_discount
```

**TypeScript:**

```typescript
class PricingService {
  constructor(private readonly discountRepository: DiscountRepository) {}

  calculateOrderTotal(order: Order, customer: Customer): Money {
    // Complex pricing logic that spans multiple aggregates
    const baseTotal = order.getTotal();

    const applicableDiscounts = this.discountRepository.findApplicableDiscounts(
      customer.getId(),
      order.getLineItems()
    );

    const totalDiscount = applicableDiscounts
      .map((discount) => discount.calculateDiscount(baseTotal))
      .reduce((acc, discount) => acc.add(discount), Money.zero());

    return baseTotal.subtract(totalDiscount);
  }
}
```

**Java:**

```java
@Component
public class PricingService {
    private final DiscountRepository discountRepository;

    public PricingService(DiscountRepository discountRepository) {
        this.discountRepository = discountRepository;
    }

    public Money calculateOrderTotal(Order order, Customer customer) {
        // Complex pricing logic that spans multiple aggregates
        Money baseTotal = order.getTotalAmount();

        // Apply customer-specific discounts
        List<Discount> applicableDiscounts = discountRepository
            .findApplicableDiscounts(customer.getId(), order.getLineItems());

        Money totalDiscount = applicableDiscounts.stream()
            .map(discount -> discount.calculateDiscount(baseTotal))
            .reduce(Money.ZERO, Money::add);

        return baseTotal.subtract(totalDiscount);
    }

    public boolean isEligibleForPremiumPricing(Customer customer) {
        // Domain logic for premium pricing eligibility
        return customer.getTotalOrdersAmount().getAmount()
            .compareTo(new BigDecimal("10000")) >= 0;
    }
}
```

**C#:**

```csharp
public class PricingService
{
    private readonly IDiscountRepository _discountRepository;

    public PricingService(IDiscountRepository discountRepository)
    {
        _discountRepository = discountRepository;
    }

    public Money CalculateOrderTotal(Order order, Customer customer)
    {
        // Complex pricing logic that spans multiple aggregates
        var baseTotal = order.GetTotal();

        var applicableDiscounts = _discountRepository
            .FindApplicableDiscounts(customer.Id, order.LineItems);

        var totalDiscount = applicableDiscounts
            .Sum(discount => discount.CalculateDiscount(baseTotal));

        return baseTotal.Subtract(totalDiscount);
    }

    public bool IsEligibleForPremiumPricing(Customer customer)
    {
        return customer.TotalOrdersAmount.Amount >= 10000m;
    }
}
```

**Rust:**

```rust
pub struct PricingService {
    discount_repository: Arc<dyn DiscountRepository>,
}

impl PricingService {
    pub fn new(discount_repository: Arc<dyn DiscountRepository>) -> Self {
        Self {
            discount_repository,
        }
    }

    pub async fn calculate_order_total(
        &self,
        order: &Order,
        customer: &Customer,
    ) -> Result<Money, DomainError> {
        // Complex pricing logic that spans multiple aggregates
        let base_total = order.total()?;

        let discounts = self.discount_repository
            .find_applicable_discounts(customer.id(), &base_total)
            .await?;

        let total_discount = discounts.iter()
            .try_fold(Money::zero(), |acc, discount| {
                Ok(acc.add(&discount.apply(&base_total)?)?)
            })?;

        base_total.subtract(&total_discount)
    }
}
```

**Go:**

```go
type PricingService struct {
    discountRepo DiscountRepository
}

func NewPricingService(discountRepo DiscountRepository) *PricingService {
    return &PricingService{
        discountRepo: discountRepo,
    }
}

func (ps *PricingService) CalculateOrderTotal(ctx context.Context, order *Order, customer *Customer) (Money, error) {
    baseTotal, err := order.Total()
    if err != nil {
        return Money{}, err
    }

    discount, err := ps.discountRepo.FindApplicableDiscount(ctx, customer.ID(), baseTotal)
    if err != nil {
        return Money{}, err
    }

    if discount == nil {
        return baseTotal, nil
    }

    return discount.Apply(baseTotal)
}

type MoneyTransferService struct{}

func NewMoneyTransferService() *MoneyTransferService {
    return &MoneyTransferService{}
}

func (mts *MoneyTransferService) Transfer(fromAccount *Account, toAccount *Account, amount Money) error {
    if !fromAccount.CanWithdraw(amount) {
        return errors.New("insufficient funds")
    }

    if err := fromAccount.Withdraw(amount); err != nil {
        return err
    }

    if err := toAccount.Deposit(amount); err != nil {
        // Rollback withdrawal
        fromAccount.Deposit(amount)
        return err
    }

    return nil
}
```

## Repository Pattern Rules

### 5. Repository Interface Rules

- Define repository interfaces in the domain layer using abstractions - they represent domain concepts
- Repositories should work with Aggregate Roots only
- Use domain-specific query methods, not generic CRUD
- Return domain objects, never DTOs or database models
- Input should be Aggregates not entities, value objects or DTOs
- Should throw domain exceptions, not infrastructure exceptions

#### Repository Interface Rules - Examples

**Python:**

```python
# Domain Layer - domain/repositories/user_repository.py
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        pass

    @abstractmethod
    def save(self, user: User) -> None:
        pass

    @abstractmethod
    def find_active_users_in_department(self, department_id: DepartmentId) -> list[User]:
        pass

    @abstractmethod
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        pass
```

**TypeScript:**

```typescript
// Domain Layer - domain/repositories/UserRepository.ts
interface UserRepository {
  findByEmail(email: Email): Promise<User | null>;
  save(user: User): Promise<void>;
  findActiveUsersInDepartment(departmentId: DepartmentId): Promise<User[]>;
  findById(userId: UserId): Promise<User | null>;
}
```

**Java:**

```java
// Domain Layer - domain/repositories/UserRepository.java
public interface UserRepository {
    CompletableFuture<Optional<User>> findByEmail(Email email);
    CompletableFuture<Void> save(User user);
    CompletableFuture<List<User>> findActiveUsersInDepartment(DepartmentId departmentId);
    CompletableFuture<Optional<User>> findById(UserId userId);
    CompletableFuture<Boolean> existsByEmail(Email email);
    CompletableFuture<Void> delete(User user);
}
```

**C#:**

```csharp
// Domain Layer - Domain/Repositories/IUserRepository.cs
public interface IUserRepository
{
    Task<User?> FindByEmailAsync(Email email, CancellationToken cancellationToken = default);
    Task SaveAsync(User user, CancellationToken cancellationToken = default);
    Task<IReadOnlyList<User>> FindActiveUsersInDepartmentAsync(DepartmentId departmentId, CancellationToken cancellationToken = default);
    Task<User?> FindByIdAsync(UserId userId, CancellationToken cancellationToken = default);
}
```

**Rust:**

```rust
// Domain Layer - domain/repositories/user_repository.rs
use async_trait::async_trait;

#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_email(&self, email: &Email) -> Result<Option<User>, DomainError>;
    async fn save(&self, user: &User) -> Result<(), DomainError>;
    async fn find_active_users_in_department(&self, department_id: &DepartmentId) -> Result<Vec<User>, DomainError>;
    async fn find_by_id(&self, user_id: &UserId) -> Result<Option<User>, DomainError>;
}
```

**Go:**

```go
// Domain Layer - domain/repositories/user_repository.go
package repositories

import "context"

type UserRepository interface {
    Save(ctx context.Context, user *User) error
    FindByID(ctx context.Context, userID UserID) (*User, error)
    FindByEmail(ctx context.Context, email Email) (*User, error)
    FindActiveUsersInDepartment(ctx context.Context, departmentID DepartmentID) ([]*User, error)
    Delete(ctx context.Context, userID UserID) error
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
- Events should be raised by aggregates, not external code

#### Domain Event Rules - Examples

**Python:**

```python
@dataclass(frozen=True)
class UserEmailChanged:
    user_id: UserId
    old_email: Email
    new_email: Email
    occurred_at: datetime
```

**TypeScript:**

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

**Java:**

```java
public record UserEmailChanged(
    UserId userId,
    Email oldEmail,
    Email newEmail,
    Instant occurredAt
) implements DomainEvent {
    public UserEmailChanged {
        Objects.requireNonNull(userId, "User ID cannot be null");
        Objects.requireNonNull(oldEmail, "Old email cannot be null");
        Objects.requireNonNull(newEmail, "New email cannot be null");
        Objects.requireNonNull(occurredAt, "Occurred at cannot be null");
    }
}
```

**C#:**

```csharp
public sealed record UserEmailChanged(
    UserId UserId,
    Email OldEmail,
    Email NewEmail,
    DateTime OccurredAt);
```

**Rust:**

```rust
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UserEmailChanged {
    pub user_id: UserId,
    pub old_email: Email,
    pub new_email: Email,
    pub occurred_at: DateTime<Utc>,
}

impl UserEmailChanged {
    pub fn new(user_id: UserId, old_email: Email, new_email: Email) -> Self {
        Self {
            user_id,
            old_email,
            new_email,
            occurred_at: Utc::now(),
        }
    }
}

impl DomainEvent for UserEmailChanged {
    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "user_email_changed"
    }
}
```

**Go:**

```go
type UserEmailChanged struct {
    userID     UserID
    oldEmail   Email
    newEmail   Email
    occurredAt time.Time
}

func NewUserEmailChanged(userID UserID, oldEmail, newEmail Email) *UserEmailChanged {
    return &UserEmailChanged{
        userID:     userID,
        oldEmail:   oldEmail,
        newEmail:   newEmail,
        occurredAt: time.Now(),
    }
}

func (e *UserEmailChanged) UserID() UserID { return e.userID }
func (e *UserEmailChanged) OldEmail() Email { return e.oldEmail }
func (e *UserEmailChanged) NewEmail() Email { return e.newEmail }
func (e *UserEmailChanged) OccurredAt() time.Time { return e.occurredAt }
func (e *UserEmailChanged) EventType() string { return "UserEmailChanged" }
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

#### Use Case Rules - Examples

**Python:**

```python
class CreateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher
    ):
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work
        self._event_publisher = event_publisher

    def execute(self, command: CreateUserCommand) -> CreateUserResponse:
        with self._unit_of_work:
            # Orchestration logic only
            email = Email(command.email)
            user = User.create(email, command.name)
            self._user_repository.save(user)
            self._event_publisher.publish(UserCreated(user.id, email))
            return CreateUserResponse(user.id.value)
```

**TypeScript:**

```typescript
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
```

**Java:**

```java
@Service
@Transactional
public class CreateUserUseCase implements CreateUserPort {
    private final UserRepository userRepository;
    private final ApplicationEventPublisher eventPublisher;
    private final TimeProviderPort timeProvider;

    public CreateUserUseCase(
        UserRepository userRepository,
        ApplicationEventPublisher eventPublisher,
        TimeProviderPort timeProvider
    ) {
        this.userRepository = userRepository;
        this.eventPublisher = eventPublisher;
        this.timeProvider = timeProvider;
    }

    @Override
    public CompletableFuture<CreateUserResponse> execute(CreateUserCommand command) {
        return CompletableFuture.supplyAsync(() -> {
            // Orchestration logic only
            Email email = new Email(command.getEmail());

            boolean userExists = userRepository.existsByEmail(email).join();
            if (userExists) {
                throw new UserAlreadyExistsException(email);
            }

            User user = User.create(email, command.getName());
            userRepository.save(user).join();

            UserCreated event = new UserCreated(
                user.getId(),
                user.getEmail(),
                user.getName(),
                timeProvider.now()
            );
            eventPublisher.publishEvent(event);

            return new CreateUserResponse(user.getId().value());
        });
    }
}
```

**C#:**

```csharp
public class CreateUserUseCase
{
    private readonly IUserRepository _userRepository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IEventPublisherPort _eventPublisher;

    public CreateUserUseCase(
        IUserRepository userRepository,
        IUnitOfWork unitOfWork,
        IEventPublisherPort eventPublisher)
    {
        _userRepository = userRepository;
        _unitOfWork = unitOfWork;
        _eventPublisher = eventPublisher;
    }

    public async Task<CreateUserResponse> ExecuteAsync(CreateUserCommand command, CancellationToken cancellationToken = default)
    {
        return await _unitOfWork.ExecuteAsync(async () =>
        {
            // Orchestration logic only
            var email = new Email(command.Email);
            var user = User.Create(email, command.Name);
            await _userRepository.SaveAsync(user, cancellationToken);
            await _eventPublisher.PublishAsync(new UserCreated(user.Id, email), cancellationToken);
            return new CreateUserResponse(user.Id.Value);
        }, cancellationToken);
    }
}
```

**Rust:**

```rust
pub struct CreateUserUseCase {
    user_repository: Arc<dyn UserRepository>,
    unit_of_work: Arc<dyn UnitOfWork>,
    event_publisher: Arc<dyn EventPublisherPort>,
}

impl CreateUserUseCase {
    pub fn new(
        user_repository: Arc<dyn UserRepository>,
        unit_of_work: Arc<dyn UnitOfWork>,
        event_publisher: Arc<dyn EventPublisherPort>,
    ) -> Self {
        Self {
            user_repository,
            unit_of_work,
            event_publisher,
        }
    }
}

#[async_trait]
impl CreateUserPort for CreateUserUseCase {
    async fn execute(&self, command: CreateUserCommand) -> Result<CreateUserResponse, UseCaseError> {
        let result = self.unit_of_work.execute(|| async {
            // Orchestration logic only
            let email = Email::new(&command.email)
                .map_err(|e| UseCaseError::InvalidInput(e.to_string()))?;

            let user = User::create(email.clone(), command.name)
                .map_err(|e| UseCaseError::DomainError(e.to_string()))?;

            self.user_repository.save(&user)
                .await
                .map_err(UseCaseError::Repository)?;

            let event = UserCreated::new(user.id().clone(), email, user.name().to_string());
            self.event_publisher.publish(Box::new(event))
                .await
                .map_err(UseCaseError::EventPublisher)?;

            Ok(CreateUserResponse {
                user_id: user.id().value().to_string(),
            })
        }).await;

        result
    }
}
```

**Go:**

```go
type CreateUserUseCase struct {
    userRepo      UserRepository
    unitOfWork    UnitOfWork
    eventPublisher EventPublisherPort
}

func NewCreateUserUseCase(
    userRepo UserRepository,
    unitOfWork UnitOfWork,
    eventPublisher EventPublisherPort,
) *CreateUserUseCase {
    return &CreateUserUseCase{
        userRepo:       userRepo,
        unitOfWork:     unitOfWork,
        eventPublisher: eventPublisher,
    }
}

func (uc *CreateUserUseCase) Execute(ctx context.Context, cmd CreateUserCommand) (*CreateUserResponse, error) {
    return uc.unitOfWork.Execute(ctx, func(ctx context.Context) (*CreateUserResponse, error) {
        // Validation and orchestration logic only
        email, err := NewEmail(cmd.Email)
        if err != nil {
            return nil, err
        }

        // Check if user already exists
        existingUser, err := uc.userRepo.FindByEmail(ctx, email)
        if err != nil {
            return nil, err
        }
        if existingUser != nil {
            return nil, NewUserAlreadyExistsError(email)
        }

        user, err := CreateUser(email, cmd.Name)
        if err != nil {
            return nil, err
        }

        if err := uc.userRepo.Save(ctx, user); err != nil {
            return nil, err
        }

        event := NewUserCreated(user.ID(), user.Email(), user.Name())
        if err := uc.eventPublisher.Publish(ctx, event); err != nil {
            return nil, err
        }

        return &CreateUserResponse{UserID: user.ID().Value()}, nil
    })
}
```

### 10. Event Integration Rules

- Domain events should be published through infrastructure ports
- Event handlers can be implemented as separate use cases
- Use event-driven architecture for cross-bounded context communication
- Events enable loose coupling between adapters and domain logic
- Consider eventual consistency for distributed operations

### 11. Validation and Error Handling Rules

- Domain validation should happen in domain objects (entities, value objects)
- Use domain exceptions that extend a base domain exception
- Validation should be explicit and fail fast
- Input validation in application services should be minimal
- Use factory methods for complex validation scenarios

### 12. Naming Convention Rules

- Use domain language (Ubiquitous Language) for all class and method names
- Avoid technical terms in domain layer (no "Manager", "Helper", "Util")
- Use intention-revealing names for methods
- Value objects should be named after the concept they represent
- Repository methods should reflect business queries
- **Port Naming**: End driving ports with "Port", driven ports with "Port"
- **Adapter Naming**: Include the technology/framework in driven adapter names
- **Clear Port vs Adapter distinction**: Ports define interfaces, Adapters implement them

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

## Ports & Adapters (Hexagonal Architecture) Rules

### 1. Port Definition Rules

- Ports define interfaces between layers and external systems
- **Driving ports** (primary/left-side) define application use cases - belong in application layer
- **Domain-driven driven ports** (repositories, domain services) - belong in domain layer
- **Infrastructure driven ports** (email, messaging, external APIs) - belong in application layer
- Port interfaces should use domain language, not technical terms
- Ports should be focused and follow Single Responsibility Principle

### 2. Driving Adapter Rules

- Driving adapters are the entry points (web controllers, CLI, message consumers)
- Should translate external requests to domain commands/queries
- Must not contain business logic - only translation and validation
- Should handle framework-specific concerns (HTTP status codes, serialization)
- Should be thin and delegate to use cases through driving ports

### 3. Driven Adapter Rules

- Driven adapters implement driven ports defined in domain/application layers
- Organize driven adapters by technology for shared infrastructure and easier maintenance
- Should handle all external system complexities (database mapping, API calls, etc.)
- Must translate between domain objects and external representations
- Should not expose external system details to the domain
- Include error handling and retry logic when appropriate
- Keep technology-specific models/schemas within their adapter implementations

### 4. Adapter Configuration Rules

- Use Dependency Injection container to wire adapters to ports
- Configuration should happen at application startup in a composition root
- Adapters should be configurable through environment variables or config files
- Use factory patterns for complex adapter creation
- Keep configuration separate from business logic

### 5. Integration Flow Rules

- Driving adapters call driving ports (use cases)
- Use cases orchestrate domain objects and use driven ports for external systems
- Driven adapters implement driven ports and handle external complexities
- Domain objects should never directly depend on adapters
- Use events for loose coupling between bounded contexts

### 6. Repository as Driven Port Rules

- Repository interfaces are domain ports (interfaces in domain layer)
- Repository implementations are driven adapters (in infrastructure layer)
- Repositories should work with Aggregate Roots and use domain language
- Repository adapters handle ORM mapping and database specifics
- Keep repository interfaces focused on domain needs, not database capabilities

### 7. Time Abstraction Adapter Rules

- Abstract system time through driven ports to enable testing and deterministic behavior
- Time ports should be infrastructure concerns, not domain concerns
- Use domain-appropriate time concepts (business hours, deadlines, schedules)
- Enable easy mocking and testing of time-dependent business logic

### 8. File System Adapter Rules

- Abstract file system operations through driven ports for testability
- Handle different storage backends (local, cloud, network) through adapters
- Use domain-specific file operations rather than generic file I/O
- Include proper error handling for file operations

### 9. External API Adapter Rules

- Abstract external service calls through driven ports
- Handle authentication, rate limiting, and retry logic in adapters
- Map external API models to domain concepts
- Provide fallback mechanisms and circuit breakers
- Include comprehensive error handling for network issues

### 10. Random Number Generation Adapter Rules

- Abstract random number generation through driven ports for deterministic testing
- Provide both cryptographically secure and pseudo-random implementations
- Enable seeded randomness for reproducible test scenarios
- Use domain-appropriate random operations rather than raw random numbers

### 11. ID Generation Adapter Rules

- Abstract ID generation through driven ports for consistent and testable ID creation
- Support different ID formats (UUID, sequential, custom formats)
- Enable deterministic ID generation for testing scenarios
- Ensure ID uniqueness and appropriate format for domain needs

### 12. Use Case as Driving Port Implementation Rules

- Use cases implement driving ports and orchestrate domain objects
- They use both domain ports (repositories) and infrastructure ports (email, messaging)
- Should not contain business logic - delegate to domain objects
- Handle cross-cutting concerns like transactions and event publishing
- Serve as the application's use case boundary
- Each use case should represent exactly one business workflow

## Testing Strategy

The testing strategy combines DDD and Ports & Adapters patterns to ensure comprehensive coverage:

### London School of TDD

#### Pedro's Algorithm: Test-Driven User Story Implementation

```text
Write an acceptance test focused on behaviour // failing for the right reason (behaviour not implemented)
Create interfaces for infrastructure as needed
// Acceptance test should be RED (failing) -> Definition off DONE for behaviour being implemented
// Don’t chase the acceptance test (don´t try to make it pass)

While the acceptance test is failing {
  Write a unit test focused on behaviour // failing for the right reason (behaviour not implemented)
  While the unit test is failing {
    Implement behaviour to pass the unit test
    Create interfaces for infrastructure as needed
    Commit on green
  }
}

Commit // acceptance test should be green at this point -> may need to adjust the acceptance test due to design decision changes

Write integration tests for driven adapter interfaces // repositories, proxies, message publishers ...
Implement behaviour to pass integration tests // convert from/to infrastructure from/to domain
Commit on green

Write contract tests for drive adapters // HTTP controllers, Message Handlers, ...
Implement behaviour to pass contract tests // convert from/to transport from/to domain
Commit on green

Optionally write End to End tests // Use the transport layer and infrastructure layer on the test (HTTP controllers, queue handlers, ...)
// Probably only need to add configuration to pass
Commit on green

Push
```

```txt
USER STORY: "As a user, I want to register with my email so that I can access the system"

DEPENDENCY FLOW: External → Driving Adapter → Use Case → Domain Objects → Driven Ports → Driven Adapters

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           TDD IMPLEMENTATION FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────────────┘

STEP 1: ACCEPTANCE TEST (OUTSIDE-IN) - Choose Your Starting Point
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ RED: Write acceptance test focused on behaviour (FAILING)                           │
│                                                                                     │
│ OPTION 1: Start from Controller Layer (Pragmatic approach)                          │
│    If the app will only use HTTP as an entrypoint you can choose this approach      │
│    Risk if in the future other entry points are added mnay need to refactor         │
│    these acceptance tests                                                           │
│                                                                                     │
│    test("user can register with email via controller") {                            │
│      const mockRepo = mock(UserRepository)                                          │
│      const mockEvents = mock(EventPublisher)                                        │
│      const controller = new UserController(mockRepo, mockEvents)                    │
│                                                                                     │
│      const result = await controller.register({                                     │
│        email: "user@example.com"                                                    │
│      })                                                                             │
│                                                                                     │
│      expect(result.status).toBe(201)                                                │
│      expect(result.body.email).toBe("user@example.com")                             │
│      verify(mockRepo.save).calledWith(instanceOf(User))                             │
│    }                                                                                │
│                                                                                     │
│ OPTION 2: Start from Use Case Layer (App-Focused)                                   │
│    test("user can register with email via use case") {                              │
│      const mockRepo = mock(UserRepository)                                          │
│      const mockEvents = mock(EventPublisher)                                        │
│      const useCase = new RegisterUser(mockRepo, mockEvents)                         │
│                                                                                     │
│      const result = await useCase.execute({                                         │
│        email: "user@example.com"                                                    │
│      })                                                                             │
│                                                                                     │
│      expect(result.userId).toBeDefined()                                            │
│      expect(result.email).toBe("user@example.com")                                  │
│      verify(mockRepo.save).calledWith(instanceOf(User))                             │
│      verify(mockEvents.publish).calledWith(instanceOf(UserRegistered))              │
│    }                                                                                │
│                                                                                     │
│ Create interfaces for infrastructure as needed:                                     │
│    - UserRepository (driven port)                                                   │
│    - EventPublisher (driven port)                                                   │
│                                                                                     │
│ DEFINITION OF DONE: Acceptance test MUST remain RED until behaviour complete        │
│                                                                                     │
│ CHOOSE YOUR STRATEGY:                                                               │
│    • Option 1: Controller focus, medium feedback, transport concerns                │
│    • Option 2: Use case focus, fast feedback, pure business logic                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        UNIT TEST CYCLE (INSIDE-OUT)                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
WHILE (acceptance test is RED) {
    STEP 2: UNIT TEST - Use Case Layer
    ┌───────────────────────────────────────────────────────────────────────────────┐
    │ RED: Write unit test for use case orchestration                               │
    │                                                                               │
    │    test("RegisterUser use case creates and saves user") {                     │
    │      const mockRepo = mock(UserRepository)                                    │
    │      const mockEvents = mock(EventPublisher)                                  │
    │      const useCase = new RegisterUser(mockRepo, mockEvents)                   │
    │                                                                               │
    │      await useCase.execute({ email: "user@example.com" })                     │
    │                                                                               │
    │      verify(mockRepo.save).calledWith(instanceOf(User))                       │
    │      verify(mockEvents.publish).calledWith(instanceOf(UserRegistered))        │
    │    }                                                                          │
    │                                                                               │
    │ GREEN: Implement RegisterUser use case                                        │
    │ REFACTOR: Extract command object                                              │
    │ COMMIT: "Add RegisterUser use case with event publishing"                     │
    └───────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
    STEP 3: UNIT TEST - Domain Layer First
    ┌───────────────────────────────────────────────────────────────────────────────┐
    │ RED: Write unit test for domain behaviour                                     │
    │                                                                               │
    │    test("User can be created with valid email") {                             │
    │      const email = new Email("user@example.com")                              │
    │      const user = User.create(userId, email)                                  │
    │      expect(user.email).toEqual(email)                                        │
    │      expect(user.domainEvents).toContain(UserRegistered)                      │
    │    }                                                                          │
    │                                                                               │
    │ GREEN: Implement User aggregate, Email value object                           │
    │ REFACTOR: Clean up code                                                       │
    │ COMMIT: "Add User aggregate with email validation"                            │
    └───────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
    REPEAT: Domain Events, Validation, etc.
    ┌───────────────────────────────────────────────────────────────────────────────┐
    │ RED: More unit tests as needed                                                │
    │ GREEN: Implement remaining domain logic                                       │
    │ REFACTOR: Clean up                                                            │
    │ COMMIT: On each green                                                         │
    └───────────────────────────────────────────────────────────────────────────────┘
} // END WHILE - Acceptance test should now be GREEN

COMMIT: "Complete user registration behaviour"
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          INTEGRATION TESTS (DRIVEN ADAPTERS)                        │
└─────────────────────────────────────────────────────────────────────────────────────┘
STEP 4: DRIVEN ADAPTER INTEGRATION TESTS
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ RED: Test driven adapter interfaces (repositories, external services)               │
│                                                                                     │
│    test("PostgresUserRepository saves and retrieves users") {                       │
│      const repo = new PostgresUserRepository(testDatabase)                          │
│      const user = UserMother.create()                                               │
│                                                                                     │
│      await repo.save(user)                                                          │
│      const retrieved = await repo.findById(user.id)                                 │
│                                                                                     │
│      expect(retrieved).toEqual(user)                                                │
│    }                                                                                │
│                                                                                     │
│ GREEN: Implement PostgresUserRepository                                             │
│          - Convert from/to database schema to/from domain objects                   │
│          - Handle database connections, transactions                                │
│                                                                                     │
│ REFACTOR: Extract mapping logic                                                     │
│ COMMIT: "Add PostgreSQL user repository implementation"                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          CONTRACT TESTS (DRIVING ADAPTERS)                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
STEP 5: DRIVING ADAPTER CONTRACT TESTS
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ RED: Test driving adapters (HTTP controllers, message handlers)                     │
│                                                                                     │
│    test("POST /api/users creates user and returns 201") {                           │
│      const mockUseCase = mock(RegisterUser)                                         │
│      const controller = new UserController(mockUseCase)                             │
│                                                                                     │
│      const response = await request(app)                                            │
│        .post('/api/users')                                                          │
│        .send({ email: 'user@example.com' })                                         │
│                                                                                     │
│      expect(response.status).toBe(201)                                              │
│      expect(response.body.email).toBe('user@example.com')                           │
│      verify(mockUseCase.execute).calledWith({ email: 'user@example.com' })          │
│    }                                                                                │
│                                                                                     │
│ GREEN: Implement UserController                                                     │
│          - Convert from/to HTTP request/response to/from domain commands            │
│          - Handle HTTP status codes, error responses                                │
│                                                                                     │
│ REFACTOR: Extract request validation                                                │
│ COMMIT: "Add HTTP controller for user registration"                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               END-TO-END TESTS (OPTIONAL)                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
STEP 6: END-TO-END TESTS (OPTIONAL)
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ RED: Test complete user journey through real transport and infrastructure           │
│                                                                                     │
│    test("User registration E2E") {                                                  │
│      // Uses real HTTP server + real database                                       │
│        const response = await fetch('/api/users', {                                 │
│        method: 'POST',                                                              │
│        body: JSON.stringify({ email: 'user@example.com' })                          │
│      })                                                                             │
│                                                                                     │
│      expect(response.status).toBe(201)                                              │
│      // Verify user exists in database                                              │
│      const user = await database.users.findByEmail('user@example.com')              │
│      expect(user).toBeDefined()                                                     │
│    }                                                                                │
│                                                                                     │
│ GREEN: Add configuration to wire everything together                                │
│          - Dependency injection setup                                               │
│          - Database migrations                                                      │
│          - Application startup                                                      │
│                                                                                     │
│ COMMIT: "Add end-to-end user registration test"                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

🚀 PUSH: Complete user story implementation
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   SUMMARY                                       │
│                                                                                 │
│ User Story: COMPLETE                                                            │
│ Acceptance Test: GREEN (behaviour implemented)                                  │
│ Unit Tests: GREEN (domain logic tested)                                         │
│ Integration Tests: GREEN (adapters tested)                                      │
│ Contract Tests: GREEN (API contracts verified)                                  │
│ E2E Tests: GREEN (full journey works)                                           │
│                                                                                 │
│ Architecture: Clean separation maintained                                       │
│ Dependencies: Flow respected (External → Adapter → Use Case → Domain)           │
│ Coverage: All layers tested appropriately                                       │
│ Process: TDD cycle followed throughout                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Testing Principles in the Flow

1. **Outside-In**: Start with acceptance test (user perspective)
2. **Inside-Out**: Build domain logic first, then orchestration
3. **Test Isolation**: Mock driven ports, test adapters separately
4. **Behaviour Focus**: Test what the system does, not how
5. **Red-Green-Refactor**: Maintain TDD discipline throughout
6. **Commit Frequently**: Each green test gets a commit
7. **Layer Separation**: Test each architectural layer appropriately

### Testing Rules

- Write unit tests for domain logic without mocking domain objects
- **Test Ports in Isolation**: Mock driven ports when testing use cases
- **Test Adapters Separately**: Test each adapter implementation independently
- **Integration Testing**: Use in-memory adapters for full workflow testing
- Test domain events are raised correctly
- Integration tests should test aggregate boundaries
- Use builders or factories for test data creation
- **Contract Testing**: Ensure all adapter implementations satisfy their port contracts
- **Use Case Testing**: Test each use case independently with mocked dependencies

### Test Boundaries and Responsibilities

```txt
                        TEST BOUNDARIES AND REPONSABILITIES
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           E2E TESTS                                     │
    │  Boundary: HTTP → Database                                              │
    │  Responsibility: User journey validation                                │
    │  Mocks: Nothing (real HTTP server, real database)                       │
    │  Purpose: Verify complete system behavior                               │
    └─────────────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                       CONTRACT TESTS                                    │
    │  Boundary: HTTP → Use Case                                              │
    │  Responsibility: API contract validation                                │
    │  Mocks: Nothing (real HTTP server, real database)                       │
    │  Purpose: Verify driving adapter contracts                              │
    └─────────────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      ACCEPTANCE TESTS                                   │
    │  Boundary: Controller → Domain OR Use Case → Domain                     │
    │  Responsibility: Whole Feature behavior validation                      │
    │  Mocks: Infrastructure (repositories, external services)                │
    │  Purpose: Define and verify business requirements                       │
    └─────────────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      INTEGRATION TESTS                                  │
    │  Boundary: Adapter → External System                                    │
    │  Responsibility: External system integration validation                 │
    │  Mocks: Nothing in boundary (real databases, real APIs)                 │
    │  Purpose: Verify driven adapter implementations                         │
    └─────────────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         UNIT TESTS                                      │
    │  Boundary: Single class/module                                          │
    │  Responsibility: Feature units validation                               │
    │  Mocks: Dependencies (ports, other domain objects if needed)            │
    │  Purpose: Verify domain behavior and use case orchestration             │
    └─────────────────────────────────────────────────────────────────────────┘
```

#### Unit Test examples

**Boundary**: Single class or module
**What it tests**: Pure business logic and behavior
**What it mocks**: Dependencies (ports, complex collaborators)
**What it uses real**: Value objects, simple domain objects
**Responsibility**:

- Domain object behavior (entities, value objects, aggregates)
- Use case orchestration logic
- Business rule enforcement
- Domain event emission

```typescript
// Domain Unit Test
test("User aggregate enforces email uniqueness") {
  const existingEmail = new Email("existing@example.com")
  const user = User.create(userId, existingEmail)

  expect(() => user.changeEmail(existingEmail))
    .toThrow(EmailAlreadyInUse)
}

// Use Case Unit Test
test("RegisterUser orchestrates domain and infrastructure") {
  const mockRepo = mock(UserRepository)
  const mockEvents = mock(EventPublisher)
  const useCase = new RegisterUser(mockRepo, mockEvents)

  await useCase.execute({ email: "user@example.com" })

  verify(mockRepo.save).calledWith(instanceOf(User))
  verify(mockEvents.publish).calledWith(instanceOf(UserRegistered))
}
```

#### Integration Test examples

**Boundary**: Adapter to external system
**What it tests**: Data transformation and external system interaction
**What it mocks**: Nothing within the boundary
**What it uses real**: Database, external APIs, file system
**Responsibility**:

- Database schema mapping
- External API communication
- Error handling with real systems
- Transaction management

```typescript
test("PostgresUserRepository saves and retrieves users correctly") {
  const repo = new PostgresUserRepository(realTestDatabase)
  const user = UserMother.withEmail("test@example.com")

  await repo.save(user)
  const retrieved = await repo.findById(user.id)

  expect(retrieved.email.value).toBe("test@example.com")
  expect(retrieved.id.equals(user.id)).toBe(true)
}
```

#### Acceptance Test examples

**Boundary**: Controller to domain OR Use case to domain
**What it tests**: Complete feature behavior
**What it mocks**: Infrastructure concerns (repositories, external services)
**What it uses real**: Domain objects, use cases, controllers
**Responsibility**:

- Feature completeness
- Business requirement satisfaction
- User story validation
- Cross-cutting concerns

```typescript
test("User can register with valid email") {
  const mockRepo = mock(UserRepository)
  const mockEvents = mock(EventPublisher)
  const useCase = new RegisterUser(mockRepo, mockEvents)

  const result = await useCase.execute({
    email: "user@example.com"
  })

  expect(result.success).toBe(true)
  expect(result.userId).toBeDefined()
  verify(mockRepo.save).calledWith(instanceOf(User))
}
```

#### Contract Tests examples

**Boundary**: HTTP → Use Case
**What it tests**: API contracts and transport concerns
**What it mocks**: Nothing (real HTTP server, real database)
**What it uses real**: Everything (HTTP server, database, external services)
**Responsibility**:

- API contract validation
- HTTP status codes
- Request/response format
- Request/response headers
- Input validation
- Error response format
- Authentication/authorization
- Pagination
- Filtering
- Sorting
- Content negotiation

```typescript
test("POST /users returns 201 with valid user data") {
  // Uses real HTTP server and real database
  const response = await request(app)
    .post('/users')
    .send({ email: 'test@example.com' })

  expect(response.status).toBe(201)
  expect(response.body.email).toBe('test@example.com')
  expect(response.body.id).toBeDefined()
  expect(response.headers['content-type']).toContain('application/json')
}
```

#### End-to-End Tests

**Boundary**: HTTP to database
**What it tests**: Complete user journeys
**What it mocks**: Nothing (full system)
**What it uses real**: Everything (HTTP server, database, external services)
**Responsibility**:

- User workflow validation
- System integration verification
- Performance under realistic conditions
- Configuration validation

```typescript
test("Complete user registration journey") {
  // Real HTTP call to real server with real database
  const response = await fetch('http://localhost:3000/users', {
    method: 'POST',
    body: JSON.stringify({ email: 'test@example.com' }),
    headers: { 'Content-Type': 'application/json' }
  })

  expect(response.status).toBe(201)

  // Verify in real database
  const savedUser = await testDatabase.query(
    'SELECT * FROM users WHERE email = $1',
    ['test@example.com']
  )
  expect(savedUser.rows).toHaveLength(1)
}
```

### Key Principles

1. **Test Pyramid**: More unit tests, fewer E2E tests
2. **Boundary Clarity**: Each test type has a clear scope
3. **Mock Strategy**: Mock external dependencies, use real domain objects
4. **Fast Feedback**: Unit and acceptance tests should be fast
5. **Realistic Validation**: Integration and E2E tests use real systems
6. **Contract Verification**: Contract tests ensure API consistency
7. **Responsibility Separation**: Each test type validates different concerns

## Project Structure

We decided to use a "real" world scenario to ilustrate how to create the project structure.
In this example we will explore how a typical folder structure for a project should look like.

## Aggregate Information

- **Name**: Naive Bank Account
- **Description**: An aggregate modeling in a very naive way a personal bank account. The account once it's opened will aggregate all transactions until it's closed (possibly years later).
- **Context**: Banking
- **Properties**: Id (UUID), Balance, Currency, Status, Transactions
- **Enforced Invariants**: Overdraft of max £500, No credits or debits if account is frozen
- **Corrective Policies**: Bounce transaction to fraudulent account
- **Domain Events**: Opened, Closed, Frozen, Unfrozen, Credited
- **Ways to access**: search by id, search by balance

## Complete Folder Structure

```text
src/
└── contexts/
    └── banking/
        └── naive-bank-accounts/
            ├── domain/
            │   ├── NaiveBankAccount.ts                    # Aggregate root
            │   ├── NaiveBankAccountOpened.ts              # Domain event
            │   ├── NaiveBankAccountClosed.ts              # Domain event
            │   ├── NaiveBankAccountFrozen.ts              # Domain event
            │   ├── NaiveBankAccountUnfrozen.ts            # Domain event
            │   ├── NaiveBankAccountCredited.ts            # Domain event
            │   ├── OverdraftLimitExceeded.ts              # Domain error
            │   ├── AccountFrozenOperation.ts              # Domain error
            │   └── NaiveBankAccountRepository.ts          # Repository interface
            ├── application/
            │   ├── open/
            │   │   └── NaiveBankAccountOpener.ts          # Use case
            │   ├── close/
            │   │   └── NaiveBankAccountCloser.ts          # Use case
            │   ├── freeze/
            │   │   └── NaiveBankAccountFreezer.ts         # Use case
            │   ├── unfreeze/
            │   │   └── NaiveBankAccountUnfreezer.ts       # Use case
            │   ├── credit/
            │   │   └── NaiveBankAccountCreditor.ts        # Use case
            │   ├── search-by-id/
            │   │   └── NaiveBankAccountByIdSearcher.ts    # Use case
            │   └── search-by-balance/
            │       └── NaiveBankAccountByBalanceSearcher.ts # Use case
            └── infrastructure/
                └── PostgresNaiveBankAccountRepository.ts  # Repository implementation

tests/
└── contexts/
    └── banking/
        └── naive-bank-accounts/
            ├── domain/
            │   ├── NaiveBankAccountMother.ts              # Object Mother
            │   ├── NaiveBankAccountIdMother.ts            # Object Mother
            │   ├── BalanceMother.ts                       # Object Mother
            │   ├── CurrencyMother.ts                      # Object Mother
            │   ├── AccountStatusMother.ts                 # Object Mother
            │   └── TransactionMother.ts                   # Object Mother
            ├── application/
            │   ├── NaiveBankAccountOpener.test.ts         # Use case test
            │   ├── NaiveBankAccountCloser.test.ts         # Use case test
            │   ├── NaiveBankAccountFreezer.test.ts        # Use case test
            │   ├── NaiveBankAccountUnfreezer.test.ts      # Use case test
            │   ├── NaiveBankAccountCreditor.test.ts       # Use case test
            │   ├── NaiveBankAccountByIdSearcher.test.ts   # Use case test
            │   └── NaiveBankAccountByBalanceSearcher.test.ts # Use case test
            └── infrastructure/
                └── PostgresNaiveBankAccountRepository.test.ts # Repository test
```

## File Structure Explanation

### Domain Layer (`src/contexts/banking/naive-bank-accounts/domain/`)

1. **NaiveBankAccount.ts** - Main aggregate root containing:

   - Properties: id, balance, currency, status, transactions
   - Invariants: overdraft limit validation, frozen account validation
   - Corrective policies: transaction bouncing logic
   - Methods to emit domain events

2. **Domain Events** (one file per event):

   - **NaiveBankAccountOpened.ts** - Emitted when account is opened
   - **NaiveBankAccountClosed.ts** - Emitted when account is closed
   - **NaiveBankAccountFrozen.ts** - Emitted when account is frozen
   - **NaiveBankAccountUnfrozen.ts** - Emitted when account is unfrozen
   - **NaiveBankAccountCredited.ts** - Emitted when account is credited

3. **Domain Errors** (one file per invariant):

   - **OverdraftLimitExceeded.ts** - Error for overdraft limit violation
   - **AccountFrozenOperation.ts** - Error for operations on frozen accounts

4. **NaiveBankAccountRepository.ts** - Repository interface with methods:
   - `save(account: NaiveBankAccount): Promise<void>`
   - `findById(id: NaiveBankAccountId): Promise<NaiveBankAccount | null>`
   - `findByBalance(balance: Balance): Promise<NaiveBankAccount[]>`

### Application Layer (`src/contexts/banking/naive-bank-accounts/application/`)

Each use case in its own folder with kebab-case naming:

1. **open/NaiveBankAccountOpener.ts** - Opens a new account
2. **close/NaiveBankAccountCloser.ts** - Closes an existing account
3. **freeze/NaiveBankAccountFreezer.ts** - Freezes an account
4. **unfreeze/NaiveBankAccountUnfreezer.ts** - Unfreezes an account
5. **credit/NaiveBankAccountCreditor.ts** - Credits money to account
6. **search-by-id/NaiveBankAccountByIdSearcher.ts** - Finds account by ID
7. **search-by-balance/NaiveBankAccountByBalanceSearcher.ts** - Finds accounts by balance

### Infrastructure Layer (`src/contexts/banking/naive-bank-accounts/infrastructure/`)

1. **PostgresNaiveBankAccountRepository.ts** - PostgreSQL implementation of the repository interface

### Test Structure (`tests/contexts/banking/naive-bank-accounts/`)

1. **Domain Object Mothers** (`domain/`):

   - **NaiveBankAccountMother.ts** - Creates test instances of NaiveBankAccount
   - **NaiveBankAccountIdMother.ts** - Creates test UUIDs
   - **BalanceMother.ts** - Creates test balance values
   - **CurrencyMother.ts** - Creates test currency values
   - **AccountStatusMother.ts** - Creates test account statuses
   - **TransactionMother.ts** - Creates test transactions

2. **Use Case Tests** (`application/`):

   - One test file per use case following the naming pattern: `[UseCase].test.ts`

3. **Infrastructure Tests** (`infrastructure/`):
   - **PostgresNaiveBankAccountRepository.test.ts** - Tests the repository implementation

## Key Naming Conventions

- **Folders**: kebab-case (e.g., `naive-bank-accounts`)
- **Files**: PascalCase with `.ts` extension (e.g., `NaiveBankAccount.ts`)
- **Use Cases**: Service-style naming (e.g., `NaiveBankAccountOpener`)
- **Domain Events**: Past tense (e.g., `NaiveBankAccountOpened`)
- **Domain Errors**: Descriptive (e.g., `OverdraftLimitExceeded`)
- **Repository**: `[Aggregate]Repository` (e.g., `NaiveBankAccountRepository`)
- **Implementation**: `[Technology][Aggregate]Repository` (e.g., `PostgresNaiveBankAccountRepository`)

This unified ruleset ensures consistent implementation of Domain Driven Design with Ports & Adapters architecture across all supported programming languages, providing clean separation of concerns, testability, and flexibility while maintaining domain focus and proper dependency management.

## CQRS - Command Query Responsibility Segregation

### What is CQRS?

- **CQRS = Command Query Responsibility Segregation**
- CQRS separates your application operations into two distinct models:
  - **Commands**: Change state (writes) - e.g., `TransferMoneyCommand`, `RegisterUserCommand`
  - **Queries**: Read state (reads) - e.g., `GetAccountBalanceQuery`, `FindUserByEmailQuery`

### The Key Insight: Different Paths for Reads and Writes

```txt
                     HEXAGONAL ARCHITECTURE + CQRS

    ┌─────────────────┐                               ┌─────────────────┐
    │   HTTP Client   │                               │   HTTP Client   │
    │  (POST/PUT)     │                               │     (GET)       │
    └─────────────────┘                               └─────────────────┘
            │                                                    │
            │ Commands (Writes)                                  │ Queries (Reads)
            ▼                                                    ▼
    ┌─────────────────┐                               ┌─────────────────┐
    │ Command Handler │                               │  Query Handler  │
    │   (Use Case)    │                               │   (Direct DB)   │
    └─────────────────┘                               └─────────────────┘
            │                                                    │
            │ Goes THROUGH Domain                                │ BYPASSES Domain
            ▼                                                    ▼
    ┌───────────────────────────┐                     ┌─────────────────┐
    │           DOMAIN LAYER    │                     │   Read Model    │
    │  ┌─────────────────┐      │                     │  (Projections)  │
    │  │   Aggregates    │      │                     │                 │
    │  │   Entities      │      │                     │  Optimized for  │
    │  │   Value Objects │      │                     │  UI needs       │
    │  │   Domain Events │      │                     │                 │
    │  └─────────────────┘      │                     └─────────────────┘
    └───────────────────────────┘                              │
                    │                                          │
                    │ Persists to                              │ Reads from
                    ▼                                          ▼
    ┌─────────────────┐                               ┌─────────────────┐
    │   Write Model   │ ────── Events ──────────────► │   Read Model    │
    │   Database      │    Sync or just write to      │   Database      │
    └─────────────────┘    table and read from view   └─────────────────┘
```

### How CQRS Works with Hexagonal Architecture

#### Commands (Writes) - Through the Domain

- **Path**: HTTP → Driving Adapter → Command Use Case → Domain → Repository → Write DB
- **Purpose**: Ensure business rules and invariants are enforced
- **Example**: Registering a user must validate email uniqueness and create domain events

```typescript
// Command side - goes through domain
class RegisterUserUseCase {
  async execute(command: RegisterUserCommand) {
    // Business logic through domain
    const email = new Email(command.email);
    const user = User.create(email, command.name); // Domain validation
    await this.userRepository.save(user); // Write model
    await this.eventPublisher.publish(new UserRegistered(user.id));
  }
}
```

#### Queries (Reads) - Around the Domain

- **Path**: HTTP → Driving Adapter → Query Handler → Repository → DTO
- **Purpose**: Optimized data retrieval without domain overhead
- **Example**: Getting user list for admin dashboard with pagination and filtering

```typescript
// Query side - bypasses domain (but still uses repository adapter)
class GetUsersQuery {
  constructor(private readonly userProjectionRepository: UserProjectionRepository) {}

  async execute(query: GetUsersQuery): Promise<UserListDto[]> {
    // Goes through repository but bypasses domain objects
    return await this.userProjectionRepository.findUsersByStatus(
      query.status,
      query.limit,
      query.offset
    );
  }
}

// Read-side repository - optimized for queries, no domain objects
class UserProjectionRepository {
  async findUsersByStatus(status: string, limit: number, offset: number): Promise<UserListDto[]> {
    return await this.readDatabase.query(
      `
      SELECT id, email, name, created_at, status
      FROM user_projections
      WHERE status = $1
      ORDER BY created_at DESC
      LIMIT $2 OFFSET $3
    `,
      [status, limit, offset]
    );
  }
}
```

### Key Benefits

#### 1. **Separation of Concerns**

- **Writes**: Complex business logic, validation, invariants
- **Reads**: Simple data retrieval, formatting, performance optimization

#### 2. **No More Bloated Entities**

- Entities don't need getters for every possible UI scenario
- Domain objects focused purely on business behavior
- Read models shaped exactly for UI needs

#### 3. **Independent Optimization**

- **Write Side**: Optimized for business logic integrity
- **Read Side**: Optimized for query performance, caching, denormalization

#### 4. **Perfect Hexagonal Integration**

- **Commands**: Use hexagonal use cases (domain-driven)
- **Queries**: Use direct database projections (infrastructure-driven)
- Same driving adapters handle both, but route differently

### Example: Banking Account

```typescript
// COMMAND - Transfer Money (through domain)
class TransferMoneyUseCase {
  async execute(cmd: TransferMoneyCommand) {
    const fromAccount = await this.accountRepo.findById(cmd.fromAccountId);
    const toAccount = await this.accountRepo.findById(cmd.toAccountId);

    // Domain logic and business rules
    fromAccount.withdraw(cmd.amount); // Validates overdraft limits
    toAccount.deposit(cmd.amount); // Domain behavior

    await this.accountRepo.save(fromAccount);
    await this.accountRepo.save(toAccount);
  }
}

// QUERY - Get Account Balance (around domain, but through repository adapter)
class GetAccountBalanceQuery {
  constructor(private readonly accountProjectionRepository: AccountProjectionRepository) {}

  async execute(query: GetAccountBalanceQuery): Promise<AccountBalanceDto> {
    // Goes through repository but bypasses domain objects
    return await this.accountProjectionRepository.getAccountBalance(query.accountId);
  }
}

// Read-side repository - optimized for account queries
class AccountProjectionRepository {
  async getAccountBalance(accountId: string): Promise<AccountBalanceDto> {
    return await this.readDatabase.query(
      `
      SELECT account_id, balance, currency, last_transaction_date
      FROM account_balances_view
      WHERE account_id = $1
    `,
      [accountId]
    );
  }
}
```

### When to Use CQRS

✅ **Use CQRS when:**

- Read and write requirements are very different
- You need optimized reads (reporting, dashboards, complex queries)
- You want to avoid polluting domain with read concerns
- You need independent scaling of reads vs writes

❌ **Don't use CQRS when:**

- Simple CRUD applications
- Read and write models are very similar
- Team lacks experience with eventual consistency
- Over-engineering for simple scenarios

CQRS perfectly complements Hexagonal Architecture by providing clear boundaries between business logic (commands through domain) and data access (queries around domain).

## References

The initial ruleset was entirely taken from: <https://github.com/bardiakhosravi/agent-context-kit/tree/main>

### Other sourcees of materials

- Codely: <https://codely.com/en/blog/how-to-implement-ddd-code-using-ai>
- Los Techies: <https://lostechies.com/jimmybogard/2008/05/21/entities-value-objects-aggregates-and-roots/>
- Hugo Graça: <https://herbertograca.com/2017/07/03/the-software-architecture-chronicles//>
