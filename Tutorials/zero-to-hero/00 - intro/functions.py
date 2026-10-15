

def my_function(name: str = 'Wiliam', age: int = 41) -> None:
    print(name, 'you are', age, 'years old')


# not adding optional parameters
my_function()

# with name
my_function('Wil')

# with parameter named so order does not matter
my_function(age = 30)

def print_people(*people) -> None:
    for person in people:
        print('this person is', person)

print_people('Wil', 'George', 'Maria')
