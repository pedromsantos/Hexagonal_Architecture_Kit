# DTO Generator Agent

Generate Data Transfer Objects for commands, queries, and responses.

## Command DTO Template

```python
@dataclass
class [Command]Command:
    [id]: str  # Generated externally
    [params]: [Type]
```

## Response DTO Template

```python
@dataclass
class [Command]Response:
    [id]: str
    [minimal_data]: [Type]
```

## Query DTO Template

```python
@dataclass
class [Query]QueryResult:
    [fields_optimized_for_ui]: [Type]
```

DTOs are simple data structures for transport. Not domain objects!
