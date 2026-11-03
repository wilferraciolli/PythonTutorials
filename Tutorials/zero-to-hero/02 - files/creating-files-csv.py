# Create a csv file with stock data, it will have the date, price and volume as headers

import csv
import random
from datetime import datetime, timedelta

NUM_ROWS: int = 500_000
FILE_NAME: str = 'stock-data.csv'
HEADERS: list[str] = ['Date', 'Price', 'Volume']

print(f'Generating {NUM_ROWS}:, rows of data into {FILE_NAME}')

current_date: datetime = datetime(2020, 1, 1)
current_price: float = 100.0


# open file for streaming output
with open(FILE_NAME, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # 1 writing headers
    writer.writerow(HEADERS)

    # 2 populate data
    for _ in range(NUM_ROWS):
        current_price = max(1.0, round(current_price + random.uniform(-3.0, 3.1), 2))
        volume = random.randint(1_000_000, 99_999_999)

        writer.writerow([
            current_date.strftime('%Y-%m-%d'),
            current_price,
            volume
        ])

        current_date += timedelta(days=1)

print(f'Done! successfullyu created {FILE_NAME} with {NUM_ROWS:,} lines.')
