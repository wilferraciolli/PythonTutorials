# Lists

fruits: list[str] = ['Banana', 'Apple', 'Watermelon', 'Pineapple']
print(fruits)


# using enumerate to convert list items onto tuples, give start 1 to mimic index+1
for item in enumerate(fruits, start=1):
    print(item)

print('\n')
# getting tuple pair and unpacking it
for item in enumerate(fruits, start=1):
    n , fruit = item
    print(n, fruit)

print('\n')
# unpacking as it is being declared and assigned
for n, fruit in enumerate(fruits, start=1):
    print(n, fruit)
