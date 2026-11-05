from dataclasses import dataclass

# instance attributes
# those are instantiated when a new instance of a class is created, and they are assigned with the constructor __init__(name)

# class attributes
# those are defined on the class level, they are used to hold state and are shared within every instance of the class, they can be changed and will continue to share their value

class Dog:
    # class attributes
    species: str = 'Canis familiaris'

    def __init__(self, name: str, age: int):
        # instance attributes
        self.name = name
        self.age = age






# @classmethod takes the cls as its first argument, not the self. It is used to modify class state or as an alternative to the constructor
# @staticmethod takes neither self or cls. It is essentialy a regular function that does not need to know about classes or instances (ideally this should only live on utils/helpers)

class MathOperations:
    # class attribute
    factor: int = 10

    @classmethod
    def update_factor(cls, new_factor: int) -> None:
        # can access and modify class attributes by using the cls
        cls.factor = new_factor

    @staticmethod
    def add(a: int, b: int) -> int:
        # Does not touch class or instance state, just a util function
        return a + b


MathOperations.update_factor(20)
print(MathOperations.add(5, 5))




# @property - this decorates allows to define a methods, but access it like a regular attribute (without the parenthesis) - more or less like a getter and setter
class Rectangle:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        # computed on the fly, but accessed like a variable
        return self.width * self.height


rectangle = Rectangle(4,5)
print(f'The area of the rectangle is: {rectangle.area}')




# @dataclass - used to specify config or record classes, it is just a shorthand to avoid boiler plate (__init__, __repr__, __eq__)

@dataclass
class User:
    username: str
    email: str
    active: bool = True

# Python automatically creates the boilerplate __init__
user1 = User(username='Wil', email='wil@wil.com')
print(user1)



