from datetime import datetime
import csv

# ******************************** Exercises ***************************************************
# Create memory efficient solution to :
# 1 - Read the stock data file stock-data.csv
# 2 - Find all days where the price was greater than $150
# 3 - Extract just the date and price for those days
# 4 - Count how many high price days there are (more than average)
#

FILE_NAME: str = 'stock-data.csv'
HEADER_DATE: str = 'Date'
HEADER_PRICE: str = 'Price'
HEADER_VOLUME: str = 'Volume'


def find_high_price_days(filename: str, threshold: int = 150) -> list[tuple[datetime, float]]:
    matching_values: list[tuple[datetime, float]] = []

    # 1 open the file with context manager for lazy loading, memory management and auto close
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # csv parses everything onto Strings, so convert to float
            current_price = float(row[HEADER_PRICE])

            # 2 get all dates and prices if over threshold
            if current_price > threshold:
                current_date = datetime.strptime(row[HEADER_DATE], '%Y-%m-%d')
                # print(f'Found {current_date} at {current_price}')

                matching_values.append((current_date, current_price))

    return matching_values

# 4 Count how many there wree
result: list[tuple[datetime, float]] = find_high_price_days(FILE_NAME)
print(f'found {sum(1 for _ in result)} days with price > $150')

