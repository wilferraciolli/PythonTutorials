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

    # define a function to generate the query to get the data form the file


def execute_query(query: Query) -> Generator[tuple[datetime, float], None, None]:
    """ Lazily reads the file and applies filters based on the query object """

    # Simple parser
    threshold = 150.0
    if '>' in query.where_clause:
        threshold = float(query.where_clause.split('>')[1].strip())

    with open(query.table, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)

        # get headers and map
        header = next(reader)
        header_map = {col.strip().lower(): idx for idx, col in enumerate(header)}

        # find user column selection
        selected_indices = [header_map[field.strip().lower()] for field in query.select_fields]

        # asusme price index is always there to match on the where condition
        price_idx = header_map['price']
        date_idx = header_map['date']

        # stream rows lazily via generator expressions
        high_price_rows = (row for row in reader if float(row[price_idx]) > threshold)

        # extract *only* the requested columns dynamically based on query
        def process_row(row):
            extracted = []
            for idx in selected_indices:
                val = row[idx]

                # If the column is Date, parse it into a datetime object automatically
                if idx == date_idx:
                    extracted.append(datetime.strptime(val, '%Y-%m-%d'))
                # If it's Price or Volume, convert to float/int
                elif idx == price_idx or 'price' in header[idx].lower():
                    extracted.append(float(val))
                else:
                    extracted.append(val)

            return tuple(extracted)

        mapped_rows = (process_row(row) for row in high_price_rows)

        # # apply the limit dynamically using itertools.islice
        if query.limit_val > 0:
            yield from itertools.islice(mapped_rows, query.limit_val)
        else:
            yield from mapped_rows


# instantiating an object using builder
my_query: Query = (QueryBuilder()
                   .from_table('stock')
                   .select(['Date', 'Price', 'Volume'])
                   .where('price > 150')
                   .limit(5)
                   .build()
                   )

print(f"Executing query on table: {my_query.table} selecting {my_query.select_fields}\n")

for row_data in execute_query(my_query):
    # Unpack dynamically based on what was selected
    print(row_data)
