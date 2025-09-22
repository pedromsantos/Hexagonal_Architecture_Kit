# Folder Structure Guidance

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

## Implementation Protocol Summary

1. **Start with TDD approach**: Create test first, then implementation
2. **Use case by use case**: Implement one complete use case at a time
3. **Create Object Mothers**: For all domain objects and value objects
4. **Domain objects**: Create aggregate, events, errors, and repository interface
5. **Application layer**: Create use cases one by one
6. **Infrastructure**: Create repository implementation with its test
7. **Verify**: Ensure all tests pass

## Key Naming Conventions

- **Folders**: kebab-case (e.g., `naive-bank-accounts`)
- **Files**: PascalCase with `.ts` extension (e.g., `NaiveBankAccount.ts`)
- **Use Cases**: Service-style naming (e.g., `NaiveBankAccountOpener`)
- **Domain Events**: Past tense (e.g., `NaiveBankAccountOpened`)
- **Domain Errors**: Descriptive (e.g., `OverdraftLimitExceeded`)
- **Repository**: `[Aggregate]Repository` (e.g., `NaiveBankAccountRepository`)
- **Implementation**: `[Technology][Aggregate]Repository` (e.g., `PostgresNaiveBankAccountRepository`)
