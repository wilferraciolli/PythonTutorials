import random
from dataclasses import dataclass

class Greeter(object):
    def __init__(self, name):
        self.name = name

    def greet(self):
        print('Welcome to Greeter!', self.name)

    def greet_again(self):
        print('Welcome to Greeter again!', self.name)


g = Greeter('Wil')
g.greet()
g.greet_again()

class Die(object):
    def __init__(self, sides):
        self.sides = sides

    def roll(self):
        return random.randint(1, self.sides)


six_sided_die: Die = Die(6)
eight_sided_die: Die = Die(8)

print(six_sided_die.roll())
print(eight_sided_die.roll())

@dataclass()
class User(object):
    first_name: str
    last_name: str
    age: int

user = User(first_name='John', last_name='Doe', age=20)
print(user.first_name)
print(user.last_name)
print(user.age)