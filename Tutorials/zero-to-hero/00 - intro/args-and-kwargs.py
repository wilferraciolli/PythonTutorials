# Return values and optional parameter to functions

# if we assigna a default value to an argument, then it becomes optional
def to_celsius(fahrenheit = 212):
    celsius = (fahrenheit - 32) * 5 / 9
    print(celsius)
    return celsius

to_celsius(212)
to_celsius()
to_celsius(fahrenheit = 50)


# *args
def sum_all(*args):
    total = 0

    for number in args:
        total += number

    return total

print('\n')
print(sum_all(1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
print(sum_all(1, 2, 3))
print('\n')

# *args and **kwargs
def style_html(*args, **kwargs):
    styles = []

    for key, value in kwargs.items():
        styles.append(f'{key}: {value}')

    style_string = '; '.join(styles)

    output = []

    for one_sentence in args:
        output.append(f'<p {style_string}>{one_sentence}</p>')

    return '\n'.join(output)


html_text = style_html('Hello there', 'how r u', 'this is a test', weight='bold', b=2, c=3)

print(html_text)
