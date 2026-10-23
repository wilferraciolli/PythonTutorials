# Python types

name: str = 'Wil'
age: int = 41
married: bool = True
wealth: float = 100
print(name, age, married, wealth)


# Lists
scores: list[int] = [100, 200, 300, 400, 500]
print(type(scores), scores)

# list of floats
scores2: list[float] = [100.0, 200.5, 30.0]
print(type(scores2), scores2)

names: list[str] | None = None
print(type(names), names)

names2: list[str] | None = ['Wil', 'George']
print(type(names), names)


# Tuples
user_record: tuple[str, int, bool] = ('Wil', 41, False)
print(type(user_record), user_record)

coordination: tuple[int, ...] = (10, 20, 30)
print(type(coordination), coordination)


# Sets
unique_tags: set[str] = {'Python', 'Java', 'Ruby'}
print(type(unique_tags), unique_tags)


# Dictionary
item_counts: dict[str, int] = {'Python': 3, 'Java': 2, 'Ruby': 1}
print(type(item_counts), item_counts)
