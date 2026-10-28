# loops

word = 'Test'
word_is_valid = True


found_letters = ['a', 'e', 'i', 'o', 'u']
invalid_letters = ['x']

index = 0
for letter in word:
    if found_letters[index] != '_' and found_letters[index] != letter:
        word_is_valid = False

    if letter in invalid_letters:
        word_is_valid = False

    index += 1

print(word_is_valid)


# using enumerated and zip
word_is_valid = True

for letter, found in zip(word, found_letters):
    if found != '_' and found != letter:
        word_is_valid = False

    if letter in invalid_letters:
        word_is_valid = False

print(word_is_valid)
