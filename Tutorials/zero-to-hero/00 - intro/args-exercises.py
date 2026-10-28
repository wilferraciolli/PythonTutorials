# Exercises


# 1 - smallest_and_largest this is a function to take any number of ints and returns a tuple with smaller and largest element.
# Assumes there is at least 1 argument
def smallest_and_largest(*args) -> tuple[int, int]:
    print(f'{args=}')
    smallest = args[0]
    largest = args[0]

    for number in args:
        if number < smallest:
            smallest = number

        if number > largest:
            largest = number

    return (smallest, largest)


print(smallest_and_largest(10, 1, 2, 3, 7, 4, 5, 6))
print(smallest_and_largest(1))
print('\n')


# 2 -apply_functions this is a function that takes one regular arg and then any number of keyword args which have functions as values,
# each function is applied to that value, then return a new dictionary back as the return value
def apply_functions(value, **kwargs) -> dict:
    print(f'{value=} {kwargs=}')
    output = {}

    for key, function in kwargs.items():
        output[key] = function(value)

    return output


print(apply_functions('aBcD', lower=str.lower, upper=str.upper, len=len))
print('\n')


# 3 -apply_functions_hard this is a function that takes one regular arg and then any number of keyword args which have functions as values,
# each function is applied to that value, then return a new dictionary back as the return value
def apply_functions_hard(value, **kwargs) -> dict:
    return {key: func(value)
            for key, func in kwargs.items()}


print(apply_functions_hard('aBcD', lower=str.lower, upper=str.upper, len=len))
