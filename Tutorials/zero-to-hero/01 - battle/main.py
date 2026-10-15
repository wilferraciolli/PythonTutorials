from classes.game import Person, bcolors

magic = [
    {"name": "Fire", "cost": 10, "dmg": 60},
    {"name": "Thunder", "cost": 10, "dmg": 80},
    {"name": "Blizzard", "cost": 10, "dmg": 60}
]
player: Person = Person(460, 65, 60, 34, magic)

print(player.generate_damage())
print(player.generate_speed(0))
print(player.generate_speed(1))
print(player.generate_speed(2))
