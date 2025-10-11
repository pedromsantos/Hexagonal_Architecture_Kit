# External Service Adapter Implementer Agent

Implement adapters for external APIs/services with authentication, retries, and error handling.

## Template

```python
class [Technology][Service]Service([ServicePort]):
    def __init__(self, config: [Config]):
        self._client = [HttpClient](config)

    def [operation](self, [domain_params]) -> [domain_result]:
        try:
            # Map domain → external
            external_request = self._to_external([domain_params])

            # Call external system
            response = self._client.post([url], data=external_request)

            # Map external → domain
            return self._to_domain(response)

        except [ExternalError] as e:
            # Handle errors, retry logic
            raise [DomainError](f"Failed to [operation]: {e}")
```

Technology-specific, handles complexity. Follow RULES.md Section 3, 9.
