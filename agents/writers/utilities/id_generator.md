# ID Generator Adapter Agent

IDs/SIDs generated OUTSIDE application, not by domain. This adapter provides external ID generation.

## Template

```python
class [Technology]IdGenerator([IdGeneratorPort]):
    def generate(self) -> str:
        return str(uuid.uuid4())
```

IDs generated externally, passed to domain. Follow External ID Generation Principle from CLAUDE.md.
