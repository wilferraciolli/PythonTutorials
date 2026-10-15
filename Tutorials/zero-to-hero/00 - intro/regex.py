import re

string = "'I AM NOT YELLING', she said. Though we knew it to not be true from 9-5"

print(string)

 # no capital
print( re.sub('[A-Z]', '', string))
 # no lower
print( re.sub('[a-z]', '', string))
# no numbers
print( re.sub('[0-9]', '', string))
# anything but numbers
print( re.sub('[^0-9]', '', string))
