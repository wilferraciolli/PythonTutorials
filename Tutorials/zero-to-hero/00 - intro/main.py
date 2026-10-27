from datetime import date
from pathlib import Path


# program to take notes and write to a file, this path can be on a configured path,
# note it depends on the OS and the home path is the users home directory

print('Take note')
note = input('Enter your note: ')

today = str(date.today())
note_line = today + ': ' + note
notes_path = Path.home() / 'notes.txt'

notes = notes_path.read_text()
notes_path.write_text(notes + note_line)
