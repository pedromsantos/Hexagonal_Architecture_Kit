# Database Migration Writer Agent

Create database migration scripts for schema and data changes.

## Template

```sql
-- Migration: [description]
-- Date: [date]

-- UP Migration
CREATE TABLE [table_name] (
    id UUID PRIMARY KEY,
    [columns]
);

CREATE INDEX idx_[table]_[column] ON [table]([column]);

-- DOWN Migration (Rollback)
DROP INDEX IF EXISTS idx_[table]_[column];
DROP TABLE IF EXISTS [table_name];
```

Schema changes, data migrations, rollback scripts.
