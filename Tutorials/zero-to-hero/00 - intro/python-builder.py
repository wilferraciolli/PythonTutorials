from datetime import datetime
import csv
import itertools
from dataclasses import dataclass, field
from typing import ClassVar, Generator


@dataclass
class Query:
    # class variable
    MAX_LIMIT: ClassVar[int] = 100

    # instance variables (processed by @dataclass)
    table: str = ''
    select_fields: list[str] = field(default_factory=list)
    where_clause: str = ''
    limit_val: int = 0


class QueryBuilder:
    def __init__(self):
        self._query = Query()

    def select(self, fields: list[str]):
        self._query.select_fields = fields
        return self  # Returning 'self' allows method chaining!

    def from_table(self, table_name: str):
        self._query.table = f'{table_name}-data.csv'
        return self

    def where(self, condition: str):
        self._query.where_clause = condition
        return self

    def limit(self, count: int):
        self._query.limit_val = min(count, Query.MAX_LIMIT)
        return self

    def build(self) -> Query:
        # You could add validation here before returning!
        if not self._query.table:
            raise ValueError("Table name is required!")
        return self._query



# instantiating an object using builder
query: Query = (QueryBuilder()
                .from_table('stock')
                .select(['data', 'price'])
                .where('price > 150')
                .limit(1_000)
                .build()
                )
print(f'Query created from builder {query}')
