# for loop enumerated and zip
titles: list[str] = ['Daylight', 'Coastline', 'Paper Planes', 'Open Road']
durations: list[str] = ['3:12', '4:05', '2:58', '3:47']

bonus_titles: list[str] = ['Reprise', 'Hidden Gem', 'Encore']
bonus_durations: list[str] = ['2:12', '3:05', '4:58']

print('Main tracks')
# use enumarate to get the index on the list, then use zip to use both collections together, then since we will have an enumarate and a tuple, we unpack them with the syntax below
for number, (title, duration) in enumerate(zip(titles, durations), start=1):
    print(f'{number}. {title}: {duration}')

print('\nBonus tracks')
for number, (title, duration) in enumerate(zip(bonus_titles, bonus_durations), start=5):
    print(f'{number}. {title}: {duration}')

