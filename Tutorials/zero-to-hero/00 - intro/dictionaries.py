# dictionaries

ice_creams = {
    'Wil': 'Strawberry',
    'George': 'Strawberry',
    'Maria': 'Chocolat',
    'Olivia': 'vanila'
}

print(type(ice_creams))
print(ice_creams)
print('Get for key: ', ice_creams['Wil'])

print(ice_creams.get('George'))
ice_creams.pop('Wil')
print(ice_creams)

print('Lists')
print(ice_creams.items())
print(ice_creams.keys())
print(ice_creams.values())
