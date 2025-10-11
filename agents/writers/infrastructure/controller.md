# Driving Adapter Implementer Agent

Implement driving adapters (HTTP controllers, CLI) that translate external requests to commands/queries.

## Template

```python
@router.post("/api/[resource]")
def [endpoint_name](request: [RequestDTO]) -> [ResponseDTO]:
    # Translate to command
    command = [Command](
        [id]=[generate_externally],
        [params]=request.[fields]
    )

    # Execute use case
    response = [use_case].execute(command)

    # Return HTTP response
    return Response(
        status_code=201,
        content=response
    )
```

Thin layer, framework-specific, no business logic. Follow RULES.md Section 2.
