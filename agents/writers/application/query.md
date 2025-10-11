# Query Handler Implementer Agent (CQRS Read)

Implement query handlers that BYPASS domain layer for optimized read performance.

## Template

```python
class [QueryName]QueryHandler:
    def __init__(self, projection_repository: [ProjectionRepository]):
        self._projection_repo = projection_repository

    def execute(self, query: [QueryName]Query) -> [QueryDTO]:
        # Direct projection query - NO domain objects
        return self._projection_repo.[query_method](
            query.[params]
        )
```

CQRS Read: Queries bypass domain, return DTOs directly. Follow RULES.md CQRS patterns.
