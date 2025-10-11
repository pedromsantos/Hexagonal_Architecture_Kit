# Command Handler Implementer Agent (CQRS Write)

Implement use cases handling commands (write operations) that go THROUGH domain layer for business rule enforcement.

## Template

```python
class [CommandName]UseCase:
    def __init__(self, [repositories], [external_ports]):
        self._[repo] = [repo]
        self._[port] = [port]

    def execute(self, command: [CommandName]Command) -> [ResponseDTO]:
        # Load aggregate
        aggregate = self._[repo].find_by_id(command.[id])

        # Execute domain method
        event = aggregate.[business_method](command.[params])

        # Save
        self._[repo].save(aggregate)

        # Publish event
        self._event_publisher.publish(event)

        # Return DTO (not domain object!)
        return [ResponseDTO](aggregate.id, aggregate.[fields])
```

CQRS Write: Commands go THROUGH domain. Follow RULES.md Section 9.
