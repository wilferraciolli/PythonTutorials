from datetime import datetime
import csv
import itertools

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


def find_high_price_days_old_school(filename: str, threshold: int = 150) -> list[tuple[datetime, float]]:
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

# Generated expression in python to allow lazy loading - GENERATOR EXPRESSIONS
def find_high_price_days_new_way(filename: str, threshold: int = 150):
    with open(filename) as f:
        # skip headers
        next(f)

        # 1 strip whitespace form lines
        lines = (line.strip() for line in f)
        # 2 chain another to split each attribute per line by comma Eg [date, price, volume] so we can get by index
        parsed = (line.split(',') for line in lines)
        # 3 chain for rows where price is high
        high_price = (row for row in parsed if float(row[1]) > threshold)
        # 4 chain a final one to extract just the date and price
        date_price = ((row[0], float(row[1])) for row in high_price)

        yield from date_price

# 4 Count how many there were - OLD SCHOOL
result: list[tuple[datetime, float]] = find_high_price_days_old_school(FILE_NAME)
print(f'found {sum(1 for _ in result)} days with price > $150')


# BEST SOLUtION FOR MEMORY MANAGEMENT ***********************************************************************************
# efficient way to call the generated function to lazily evaluate, the main take away of doing this way is that the whole file will never ever be loaded to memory at once
count = sum(1 for _ in find_high_price_days_new_way(FILE_NAME))
print(f'Days with price > $150: {count}')

print('\n')

# now call with a generated expression so it will only evaluate what it needs to
print('First 5 high-price days:')
results = list(itertools.islice(find_high_price_days_new_way(FILE_NAME), 5))
for date, price in results:
    print(f'{date}: ${price:.2f}')



