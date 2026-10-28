# Lists

videos: list[str] = ['Modules', 'Sequences', 'Tuple unpacking']
print(videos)

# copying a list
copied_videos: list[str] = [video for video in videos]
print(copied_videos)

# filtering and copying a list
formatted_videos: list[str] = [name.lower().replace(' ', '-') for name in videos]
print(formatted_videos)

single_word_names: list[str] = [name for name in videos if ' ' not in name]
print(single_word_names)

# Exercises to manipulate lists **************************************************************************************
values: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# double each number on a list if their values is bigger than 5
new_values = [n * 2 for n in values if n > 5]
print(new_values)

# numbers above 1, twice: the filtered list concatenated with a copy of itself (really just filter above one and concatenate with itself)
concatenated_values: list[int] = [n for n in values * 2 if n > 1]
print(concatenated_values)

# each number above one twice, each filtered number occurs twice is a row
twice_in_a_row: list[int] = [n for n in values if n > 1 for i in range(2)]
print(twice_in_a_row)

# A boolean for each non-zero number, stating whether the number is above one
above_one: list[int] = [n > 1 for n in values if n * 2]
print(above_one)
