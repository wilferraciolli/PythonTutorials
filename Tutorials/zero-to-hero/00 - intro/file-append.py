from datetime import date

# program to take notes and write to a file

print('Take note')
note = input('Enter your note: ')

today = str(date.today())
note_line = today + ': ' + note
notes_path = 'notes.txt'

# Open in append mode ('a').
# If 'notes.txt' doesn't exist, Python creates it automatically!
with open(notes_path, 'a', encoding='utf-8') as note_file:
    note_file.write(note_line + '\n')
