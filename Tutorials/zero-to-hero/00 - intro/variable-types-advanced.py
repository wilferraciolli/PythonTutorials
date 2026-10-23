# Python advanced types
from typing import TypedDict, Any, Literal, TypeVar
from collections.abc import Sequence, Callable


# TypedDict is used to enforce type check
class User(TypedDict):
    name: str
    age: int
    is_active: bool


user: User = {
    'name': 'wil',
    'age': 100,
    'is_active': True
}
print(user)

# Immutable Sequence (Frozen and sequence)
allowed_roles: frozenset[str] = frozenset[str]({'Standard', 'Admin'})
print(allowed_roles)


# Generic collection - Sequence accepts any iterable
def process_items(items: Sequence[str]) -> None:
    for item in items:
        print(item)


my_list = ["apple", "banana", "cherry"]
process_items(my_list)
my_tuple = ("dog", "cat", "bird")
process_items(my_tuple)

# Union and Optional
id_number: int | str = 'A-123'
print(type(id_number), id_number)
id_number = 123
print(type(id_number), id_number)

middle_name: str | None = None
print(type(middle_name), middle_name)

# use Any if you dont want to check a type
data: Any = {'anything': 123, 'goes': [True, 'here']}
print(type(data), data)


# Literals
def set_mode(mode: Literal['read', 'write', 'append']) -> None:
    pass


set_mode('read')  # allowed
set_mode('delete')  # not allowed, will run but compliter should tell it is not allowed


# Callable
# Afunction that takes two ints and return an int can be passed here
def compute(func: Callable[[int, int], int], x: int, y: int) -> int:
    return func(x, y)

# 1. Define a function matching the signature
def add(a: int, b: int) -> int:
    return a + b

# 2. Pass the function reference (without parentheses!) into compute
result = compute(add, 5, 3)
print(result)  # Output: 8

# 3 Pass a lambda that multiplies two numbers
result = compute(lambda a, b: a * b, 4, 5)
print(result)  # Output: 20


# Generics
T = TypeVar('T')

def get_first_item(items: list[T]) -> T:
    return items[0]

print(get_first_item([1, 2, 3]))
print(get_first_item(['a', 'b', 'c']))
