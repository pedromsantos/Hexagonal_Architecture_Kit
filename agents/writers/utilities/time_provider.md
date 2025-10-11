# Time Provider Adapter Agent

Abstract system time for testability.

## Template

```python
class SystemTimeProvider(TimeProviderPort):
    def now(self) -> datetime:
        return datetime.now()

class FixedTimeProvider(TimeProviderPort):
    def __init__(self, fixed_time: datetime):
        self._time = fixed_time

    def now(self) -> datetime:
        return self._time
```

Mockable time for testing. Follow RULES.md Section 7 (Time Abstraction).
