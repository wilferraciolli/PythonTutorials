file_name = 'README.md'

# read file line by line
with open(file_name) as file:
    line_number = 1
    for line in file:
        print(line_number, line.rstrip('\n'))
        line_number += 1


# note that writing to a file will replace the content of it, so we want to ideally append
# with open(file_name, mode='wt') as file:
    # file.write("Hello World")
    # file.write("\n")