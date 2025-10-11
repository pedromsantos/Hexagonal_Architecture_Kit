# Repository Interface Designer Agent

Design repository interfaces in domain layer: one per aggregate root, domain language, returns domain objects.

## Template

```python
# domain/repositories/[aggregate]_repository.py
from abc import ABC, abstractmethod

class [Aggregate]Repository(ABC):
    @abstractmethod
    def save(self, [aggregate]: [Aggregate]) -> None:
        pass

    @abstractmethod
    def find_by_id(self, [id]: [AggregateId]) -> [Aggregate] | None:
        pass

    @abstractmethod
    def [domain_specific_query](self, [params]) -> list[[Aggregate]]:
        pass
```

One repository per aggregate root. Domain language methods. Follow RULES.md Section 5-6.
