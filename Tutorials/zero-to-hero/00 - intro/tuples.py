# tuple unpacking
user: tuple[str, int, bool] = ('wil', 41, True)
print(type(user), user)

# unpacking it
name: str
age: int
married: bool

name, age, married = user
print(name, age, married)

# or get the tuple by index
another_name: str = user[0]
another_age: int = user[1]
another_married: int = user[2]
print(another_name, another_age, another_married)
