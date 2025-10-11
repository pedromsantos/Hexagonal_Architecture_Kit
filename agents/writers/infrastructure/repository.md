# Repository Implementer Agent

Implement database-specific repositories that handle ORM mapping and persistence.

## Template

```python
class [Technology][Aggregate]Repository([Aggregate]Repository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, [aggregate]: [Aggregate]) -> None:
        orm_model = self._to_orm([aggregate])
        self._session.merge(orm_model)
        self._session.commit()

    def find_by_id(self, [id]: [AggregateId]) -> [Aggregate] | None:
        orm_model = self._session.query([OrmModel]).filter_by(id=[id].value).first()
        return self._to_domain(orm_model) if orm_model else None

    def _to_orm(self, [aggregate]: [Aggregate]) -> [OrmModel]:
        # Domain → ORM mapping
        pass

    def _to_domain(self, orm: [OrmModel]) -> [Aggregate]:
        # ORM → Domain mapping
        pass
```

Technology-specific names, handle mapping. Follow RULES.md Section 6.
